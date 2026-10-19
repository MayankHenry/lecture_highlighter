import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from app import config

cloudinary.config(
    cloud_name=config.CLOUD_NAME,
    api_key=config.API_KEY,
    api_secret=config.API_SECRET,
    secure=True,
)


def upload_video(path: str) -> tuple[str, str]:
    """Upload the lecture to Cloudinary. Returns (public_id, secure_url)."""
    res = cloudinary.uploader.upload_large(
        path, resource_type="video", folder="lecture-highlighter", chunk_size=6_000_000
    )
    return res["public_id"], res["secure_url"]


def clip_url(public_id: str, start: float, end: float) -> str:
    """Cloudinary cuts the clip on the fly using start/end offsets (seconds)."""
    url, _ = cloudinary_url(
        public_id,
        resource_type="video",
        format="mp4",
        transformation=[{"start_offset": round(start, 2), "end_offset": round(end, 2)}],
    )
    return url
