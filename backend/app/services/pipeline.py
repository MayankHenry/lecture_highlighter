import logging
import os

from cloudinary.exceptions import AuthorizationRequired, RateLimited

from app.db import SessionLocal
from app.models import Chapter, Lecture
from app.services.chaptering import make_chapters
from app.services.cloudinary_svc import clip_url, upload_video
from app.services.transcribe import transcribe

logger = logging.getLogger(__name__)


def _user_error_message(stage: str, error: Exception) -> str:
    if isinstance(error, AuthorizationRequired):
        return (
            "Cloudinary rejected its credentials. Check the cloud name, API key, "
            "and API secret in backend/.env."
        )
    if isinstance(error, RateLimited):
        return "Cloudinary's upload limit was reached. Check your plan or try again later."
    if stage == "uploading":
        return (
            "We couldn't upload this lecture. Check your Cloudinary settings and "
            "internet connection, then try again with a smaller file."
        )
    if stage == "transcribing":
        return (
            "We couldn't transcribe this lecture. Check that the file contains "
            "clear audio and isn't damaged, then try another recording."
        )
    if stage == "chaptering":
        return (
            "We couldn't create chapters for this lecture. Check your LLM settings "
            "and internet connection, then try again."
        )
    return (
        "Something went wrong while processing this lecture. Please try again. "
        "If the problem continues, check the backend logs."
    )


def process_lecture(lecture_id: int, path: str) -> None:
    db = SessionLocal()
    stage = "queued"
    try:
        lec = db.get(Lecture, lecture_id)

        stage = "uploading"
        lec.status = "uploading"
        db.commit()
        public_id, url = upload_video(path)

        stage = "transcribing"
        lec.public_id, lec.video_url, lec.status = public_id, url, "transcribing"
        db.commit()

        segments, duration = transcribe(path)

        stage = "chaptering"
        lec.duration, lec.transcript, lec.status = duration, segments, "chaptering"
        db.commit()

        for i, ch in enumerate(make_chapters(segments, duration)):
            db.add(
                Chapter(
                    lecture_id=lec.id,
                    idx=i,
                    title=ch["title"],
                    summary=ch["summary"],
                    notes=ch["notes"],
                    start=ch["start"],
                    end=ch["end"],
                    clip_url=clip_url(public_id, ch["start"], ch["end"]),
                )
            )
        lec.status = "ready"
        db.commit()
    except Exception as e:
        logger.exception("Lecture %s failed during %s", lecture_id, stage)
        db.rollback()
        lec = db.get(Lecture, lecture_id)
        lec.status, lec.error = "failed", _user_error_message(stage, e)
        db.commit()
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)
