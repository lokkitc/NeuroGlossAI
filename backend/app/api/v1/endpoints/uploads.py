from typing import Any

import logging
from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.exceptions import NeuroGlossException
from app.core.rate_limit import limiter
from app.features.users.models import User
from app.features.uploads.service import UploadService
from app.features.uploads.models import Upload
from app.features.uploads.repository import UploadRepository
from app.features.common.db import begin_if_needed


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/image")
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    image: UploadFile = File(...),
) -> Any:
    try:
        svc = UploadService()
        # Namespace uploads by user id to simplify ownership enforcement without a DB table.
        result = await svc.upload_image_file(image=image, folder=f"neuroglossai/{current_user.id}")
    except Exception as e:
        logger.exception("Upload failed")
        msg = str(e)
        lowered = msg.lower()
        if "disabled" in lowered:
            raise NeuroGlossException(status_code=404, code="not_found", detail="Not Found")
        if "only image" in lowered:
            raise NeuroGlossException(status_code=415, code="unsupported_media_type", detail="Only image uploads are supported")
        if "empty file" in lowered:
            raise NeuroGlossException(status_code=400, code="invalid_upload", detail="Empty file")
        if "too large" in lowered:
            raise NeuroGlossException(status_code=413, code="payload_too_large", detail="File too large")
        raise NeuroGlossException(status_code=500, code="upload_failed", detail="Upload failed")

    public_id = result.get("public_id")
    if public_id:
        row = Upload(
            owner_user_id=current_user.id,
            public_id=str(public_id),
            provider=(getattr(svc, "_provider", "") or ""),
            bytes=int(result.get("bytes") or 0),
            mime=(getattr(image, "content_type", None) or None),
        )
        try:
            async with begin_if_needed(db):
                await UploadRepository(db).create(row)
        except Exception:
            # Best-effort persistence: do not fail upload if metadata insert fails.
            logger.exception("Failed to persist upload metadata")

    return {
        "url": result.get("secure_url") or result.get("url"),
        "public_id": public_id,
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
        "format": result.get("format"),
        "resource_type": result.get("resource_type"),
    }


@router.get("/presign")
@limiter.limit("60/minute")
async def presign_upload_get_url(
    request: Request,
    public_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    try:
        pid = (public_id or "").strip().lstrip("/")
        repo = UploadRepository(db)
        row = await repo.get_by_public_id(public_id=pid)
        if row is None or row.owner_user_id != current_user.id:
            raise NeuroGlossException(status_code=404, code="not_found", detail="Not Found")
        async with begin_if_needed(db):
            await repo.mark_accessed(row=row)
        svc = UploadService()
        url = svc.presign_get_url(public_id=pid)
        return {"url": url}
    except Exception as e:
        logger.exception("Presign failed")
        raise NeuroGlossException(status_code=400, code="invalid_public_id", detail="Invalid public_id")
