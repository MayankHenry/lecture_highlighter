from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idx: int
    title: str
    summary: str
    notes: list[str]
    start: float
    end: float
    clip_url: str


class LectureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    error: str | None = None
    video_url: str | None = None
    duration: float | None = None
    created_at: datetime
    chapters: list[ChapterOut] = []
