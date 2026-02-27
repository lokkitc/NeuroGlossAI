from __future__ import annotations

import mimetypes
import os
import uuid
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions import ServiceException


class UploadService:
    def __init__(self) -> None:
        if not settings.UPLOADS_ENABLED:
            raise ServiceException("Uploads are disabled")

        self._provider = (settings.UPLOAD_PROVIDER or "").strip().lower() or "cloudinary"
        if self._provider not in {"cloudinary", "s3"}:
            raise ServiceException("Unsupported upload provider")

        if self._provider == "cloudinary":
            if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
                raise ServiceException("Cloudinary is not configured")

            import cloudinary  # type: ignore

            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )

        if self._provider == "s3":
            if not settings.S3_ENDPOINT_URL:
                raise ServiceException("S3 is not configured")
            if not settings.S3_BUCKET_NAME:
                raise ServiceException("S3 is not configured")
            if not settings.S3_ACCESS_KEY_ID or not settings.S3_SECRET_ACCESS_KEY:
                raise ServiceException("S3 is not configured")

    def upload_image(self, *, data: bytes, filename: str, folder: str = "neuroglossai") -> dict:
        if self._provider == "cloudinary":
            try:
                import cloudinary.uploader  # type: ignore

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

        if self._provider == "s3":
            return self._upload_image_s3(data=data, filename=filename, folder=folder)

        raise ServiceException("Upload failed")

    def _upload_image_s3(self, *, data: bytes, filename: str, folder: str) -> dict:
        try:
            endpoint_url = settings.S3_ENDPOINT_URL
            bucket = settings.S3_BUCKET_NAME

            ext = os.path.splitext(filename)[1].lower()
            if not ext:
                guessed_ext = mimetypes.guess_extension(mimetypes.guess_type(filename)[0] or "")
                ext = (guessed_ext or "").lower()

            key = f"{folder.strip('/')}/{uuid.uuid4().hex}{ext}" if folder else f"{uuid.uuid4().hex}{ext}"

            cfg = Config(
                s3={
                    "addressing_style": "virtual" if settings.S3_USE_VIRTUAL_HOSTED_STYLE else "path",
                }
            )
            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                config=cfg,
            )

            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL="public-read",
            )

            public_url = self._build_public_url(bucket=bucket, key=key)

            return {
                "url": public_url,
                "secure_url": public_url,
                "public_id": key,
                "bytes": len(data),
                "format": (ext[1:] if ext.startswith(".") else ext) or None,
                "resource_type": "image",
            }
        except Exception as e:
            raise ServiceException(f"Upload failed: {str(e)}")

    def _build_public_url(self, *, bucket: str, key: str) -> str:
        base = (settings.S3_PUBLIC_BASE_URL or "").strip().rstrip("/")
        if base:
            return f"{base}/{key}"

        parsed = urlparse(settings.S3_ENDPOINT_URL or "")
        host = parsed.netloc
        scheme = parsed.scheme or "https"
        if settings.S3_USE_VIRTUAL_HOSTED_STYLE:
            return f"{scheme}://{bucket}.{host}/{key}"
        return f"{scheme}://{host}/{bucket}/{key}"

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
