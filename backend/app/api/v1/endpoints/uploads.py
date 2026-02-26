from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api import deps
from app.core.config import settings
from app.core.exceptions import NeuroGlossException
from app.features.users.models import User
from app.features.uploads.service import UploadService


router = APIRouter()


@router.post("/image")
async def upload_image(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    image: UploadFile = File(...),
) -> Any:
    if not settings.UPLOADS_ENABLED:
        raise NeuroGlossException(status_code=404, code="not_found", detail="Not Found")

    content_type = (image.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise NeuroGlossException(status_code=415, code="unsupported_media_type", detail="Only image uploads are supported")

    data = await image.read()
    if not data:
        raise NeuroGlossException(status_code=400, code="invalid_upload", detail="Empty file")

    if settings.UPLOAD_MAX_BYTES and len(data) > int(settings.UPLOAD_MAX_BYTES):
        raise NeuroGlossException(status_code=413, code="payload_too_large", detail="File too large")

    svc = UploadService()
    result = await run_in_threadpool(svc.upload_image, data=data, filename=image.filename or "image")

    return {
        "url": result.get("secure_url") or result.get("url"),
        "public_id": result.get("public_id"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
        "format": result.get("format"),
        "resource_type": result.get("resource_type"),
    }
