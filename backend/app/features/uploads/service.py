from __future__ import annotations

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions import ServiceException


class UploadService:
    def __init__(self) -> None:
        if not settings.UPLOADS_ENABLED:
            raise ServiceException("Uploads are disabled")

        if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
            raise ServiceException("Cloudinary is not configured")

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def upload_image(self, *, data: bytes, filename: str, folder: str = "neuroglossai") -> dict:
        try:
            return cloudinary.uploader.upload(
                data,
                resource_type="image",
                folder=folder,
                public_id=None,
                filename_override=filename,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        except Exception as e:
            raise ServiceException(f"Upload failed: {str(e)}")

    async def upload_image_file(self, *, image: UploadFile, folder: str = "neuroglossai") -> dict:
        content_type = (getattr(image, "content_type", None) or "").lower()
        if not content_type.startswith("image/"):
            raise ServiceException("Only image uploads are supported")

        data = await image.read()
        if not data:
            raise ServiceException("Empty file")

        if settings.UPLOAD_MAX_BYTES and len(data) > int(settings.UPLOAD_MAX_BYTES):
            raise ServiceException("File too large")

        filename = getattr(image, "filename", None) or "image"
        return await run_in_threadpool(self.upload_image, data=data, filename=filename, folder=folder)
