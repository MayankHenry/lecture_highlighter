from functools import lru_cache

from faster_whisper import WhisperModel

from app import config


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    return WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")


def transcribe(path: str) -> tuple[list[dict], float]:
    """Returns ([{start, end, text}], duration_seconds). Works on video files directly."""
    segments, info = _model().transcribe(path, vad_filter=True, beam_size=1)
    out = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    return out, float(info.duration)
