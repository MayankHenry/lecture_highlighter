import os
import shutil
import tempfile

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lecture
from app.schemas import LectureOut
from app.services.pipeline import process_lecture

router = APIRouter(prefix="/api/lectures", tags=["lectures"])

ALLOWED = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".mp3", ".wav", ".m4a")


@router.post("", response_model=LectureOut)
def create_lecture(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type. Use one of: {', '.join(ALLOWED)}")

    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as out:
        shutil.copyfileobj(file.file, out)

    lec = Lecture(title=(title or file.filename or "Untitled lecture")[:200], status="queued")
    db.add(lec)
    db.commit()
    db.refresh(lec)
    background.add_task(process_lecture, lec.id, path)
    return lec


@router.get("", response_model=list[LectureOut])
def list_lectures(db: Session = Depends(get_db)):
    rows = db.scalars(select(Lecture).order_by(Lecture.created_at.desc())).all()
    return rows


@router.get("/{lecture_id}", response_model=LectureOut)
def get_lecture(lecture_id: int, db: Session = Depends(get_db)):
    lec = db.get(Lecture, lecture_id)
    if not lec:
        raise HTTPException(404, "Lecture not found")
    return lec
