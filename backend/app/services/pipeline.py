import os

from app.db import SessionLocal
from app.models import Chapter, Lecture
from app.services.chaptering import make_chapters
from app.services.cloudinary_svc import clip_url, upload_video
from app.services.transcribe import transcribe


def process_lecture(lecture_id: int, path: str) -> None:
    db = SessionLocal()
    try:
        lec = db.get(Lecture, lecture_id)

        lec.status = "uploading"
        db.commit()
        public_id, url = upload_video(path)
        lec.public_id, lec.video_url, lec.status = public_id, url, "transcribing"
        db.commit()

        segments, duration = transcribe(path)
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
        db.rollback()
        lec = db.get(Lecture, lecture_id)
        lec.status, lec.error = "failed", str(e)[:500]
        db.commit()
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)
