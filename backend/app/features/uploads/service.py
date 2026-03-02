from __future__ import annotations

import mimetypes
import os
import re
import uuid
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
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

    def _s3_client_candidates(self):
        endpoint_url = settings.S3_ENDPOINT_URL
        addressing_styles = [
            "virtual" if settings.S3_USE_VIRTUAL_HOSTED_STYLE else "path",
            "path" if settings.S3_USE_VIRTUAL_HOSTED_STYLE else "virtual",
        ]
        regions = [settings.S3_REGION, "us-east-1"] if settings.S3_REGION != "us-east-1" else [settings.S3_REGION]

        for region_name in regions:
            for addressing_style in addressing_styles:
                cfg = Config(
                    signature_version="s3v4",
                    s3={
                        "addressing_style": addressing_style,
                    },
                )
                client = boto3.client(
                    "s3",
                    endpoint_url=endpoint_url,
                    region_name=region_name,
                    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                    config=cfg,
                )
                yield client, region_name, addressing_style

    def presign_get_url(self, *, public_id: str) -> str:
        if self._provider != "s3":
            raise ServiceException("Presign is only supported for S3 provider")

        key = (public_id or "").strip().lstrip("/")
        if not key:
            raise ServiceException("Invalid public_id")

        # Best-effort validation to reduce abuse. Keys are generated as:
        # {folder}/{uuid4hex}{ext}
        if not re.fullmatch(r"[a-z0-9_\-/]{1,200}\.(png|jpg|jpeg|gif|webp)", key, flags=re.IGNORECASE):
            raise ServiceException("Invalid public_id")

        bucket = settings.S3_BUCKET_NAME
        expires = int(getattr(settings, "S3_PRESIGNED_URL_EXPIRES_SECONDS", 3600) or 3600)
        last_error: Exception | None = None
        last_attempt: tuple[str, str] | None = None

        for client, region_name, addressing_style in self._s3_client_candidates():
            last_attempt = (region_name, addressing_style)
            try:
                return client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=max(1, expires),
                )
            except Exception as e:
                last_error = e
                continue

        region_name, addressing_style = last_attempt or ("?", "?")
        raise ServiceException(f"Presign failed: {str(last_error)} region={region_name} addressing_style={addressing_style}")

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

            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            addressing_styles = [
                "virtual" if settings.S3_USE_VIRTUAL_HOSTED_STYLE else "path",
                "path" if settings.S3_USE_VIRTUAL_HOSTED_STYLE else "virtual",
            ]
            regions = [settings.S3_REGION, "us-east-1"] if settings.S3_REGION != "us-east-1" else [settings.S3_REGION]

            object_acl = (getattr(settings, "S3_OBJECT_ACL", None) or "").strip() or None
            last_error: Exception | None = None
            last_attempt: tuple[str, str] | None = None
            success_attempt: tuple[str, str] | None = None
            success_client = None
            for region_name in regions:
                for addressing_style in addressing_styles:
                    last_attempt = (region_name, addressing_style)
                    cfg = Config(
                        signature_version="s3v4",
                        s3={
                            "addressing_style": addressing_style,
                        },
                    )
                    client = boto3.client(
                        "s3",
                        endpoint_url=endpoint_url,
                        region_name=region_name,
                        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                        config=cfg,
                    )

                    try:
                        put_kwargs = {
                            "Bucket": bucket,
                            "Key": key,
                            "Body": data,
                            "ContentType": content_type,
                        }
                        if object_acl is not None:
                            put_kwargs["ACL"] = object_acl

                        client.put_object(
                            **put_kwargs,
                        )
                        last_error = None
                        success_attempt = (region_name, addressing_style)
                        success_client = client
                        break
                    except ClientError as e:
                        last_error = e
                        code = (e.response.get("Error") or {}).get("Code")
                        msg = (e.response.get("Error") or {}).get("Message")

                        acl_not_supported = (
                            (code or "").lower() in {"accesscontrollistnotsupported", "invalidrequest"}
                            or "acl" in (msg or "").lower()
                        )
                        if not acl_not_supported:
                            continue

                        try:
                            client.put_object(
                                Bucket=bucket,
                                Key=key,
                                Body=data,
                                ContentType=content_type,
                            )
                            last_error = None
                            success_attempt = (region_name, addressing_style)
                            success_client = client
                            break
                        except ClientError as e2:
                            last_error = e2
                            continue
                    except Exception as e:
                        last_error = e
                        continue

                if last_error is None:
                    break

            if last_error is not None:
                if isinstance(last_error, ClientError):
                    err = last_error.response.get("Error") or {}
                    code = err.get("Code")
                    msg = err.get("Message")
                    req_id = last_error.response.get("ResponseMetadata", {}).get("RequestId")
                    region_name, addressing_style = last_attempt or ("?", "?")
                    raise ServiceException(
                        f"Upload failed: S3 ClientError code={code} message={msg} request_id={req_id} region={region_name} addressing_style={addressing_style}"
                    )

                region_name, addressing_style = last_attempt or ("?", "?")
                raise ServiceException(
                    f"Upload failed: {str(last_error)} region={region_name} addressing_style={addressing_style}"
                )

            _, addressing_style = success_attempt or last_attempt or ("?", "path")

            # If object is public, return its public URL. Otherwise, return a presigned URL (short-lived)
            # while keeping public_id as the stable identifier.
            is_public = object_acl == "public-read"
            url_value = None
            if is_public:
                url_value = self._build_public_url(bucket=bucket, key=key, addressing_style=addressing_style)
            else:
                if bool(getattr(settings, "S3_RETURN_PRESIGNED_URL", True)) and success_client is not None:
                    expires = int(getattr(settings, "S3_PRESIGNED_URL_EXPIRES_SECONDS", 3600) or 3600)
                    url_value = success_client.generate_presigned_url(
                        ClientMethod="get_object",
                        Params={"Bucket": bucket, "Key": key},
                        ExpiresIn=max(1, expires),
                    )

            return {
                "url": url_value,
                "secure_url": url_value,
                "public_id": key,
                "bytes": len(data),
                "format": (ext[1:] if ext.startswith(".") else ext) or None,
                "resource_type": "image",
            }
        except Exception as e:
            raise ServiceException(f"Upload failed: {str(e)}")

    def _build_public_url(self, *, bucket: str, key: str, addressing_style: str = "path") -> str:
        base = (settings.S3_PUBLIC_BASE_URL or "").strip().rstrip("/")
        if base:
            return f"{base}/{key}"

        parsed = urlparse(settings.S3_ENDPOINT_URL or "")
        host = parsed.netloc
        scheme = parsed.scheme or "https"

        # Some S3-compatible providers (including t3.storageapi.dev) commonly expose public objects via path-style URLs.
        # If you have a dedicated public CDN/domain, set S3_PUBLIC_BASE_URL.
        if host.endswith("storageapi.dev"):
            base_host = host
            if base_host.startswith(f"{bucket}."):
                base_host = base_host[len(f"{bucket}.") :]
            return f"{scheme}://{base_host}/{bucket}/{key}"

        if addressing_style == "virtual":
            return f"{scheme}://{bucket}.{host}/{key}"
        return f"{scheme}://{host}/{bucket}/{key}"

    async def upload_image_file(self, *, image: UploadFile, folder: str = "neuroglossai") -> dict:
        content_type = (getattr(image, "content_type", None) or "").lower()
        allowed_mime = {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/gif",
            "image/webp",
        }
        if content_type not in allowed_mime:
            raise ServiceException("Only image uploads are supported")

        data = await image.read()
        if not data:
            raise ServiceException("Empty file")

        if settings.UPLOAD_MAX_BYTES and len(data) > int(settings.UPLOAD_MAX_BYTES):
            raise ServiceException("File too large")

        def _looks_like_image_bytes(b: bytes) -> bool:
            # PNG
            if b.startswith(b"\x89PNG\r\n\x1a\n"):
                return True
            # JPEG
            if len(b) >= 3 and b[0:3] == b"\xff\xd8\xff":
                return True
            # GIF
            if b.startswith(b"GIF87a") or b.startswith(b"GIF89a"):
                return True
            # WEBP (RIFF....WEBP)
            if len(b) >= 12 and b[0:4] == b"RIFF" and b[8:12] == b"WEBP":
                return True
            return False

        if not _looks_like_image_bytes(data):
            raise ServiceException("Only image uploads are supported")

        filename = getattr(image, "filename", None) or "image"
        return await run_in_threadpool(self.upload_image, data=data, filename=filename, folder=folder)
