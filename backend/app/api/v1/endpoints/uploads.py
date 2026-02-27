from typing import Any

import logging
from fastapi import APIRouter, Depends, UploadFile, File

from app.api import deps
from app.core.exceptions import NeuroGlossException
from app.features.users.models import User
from app.features.uploads.service import UploadService


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/image")
async def upload_image(
    current_user: User = Depends(deps.get_current_user),
    image: UploadFile = File(...),
) -> Any:
    try:
        svc = UploadService()
        result = await svc.upload_image_file(image=image)
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
        raise NeuroGlossException(status_code=500, code="upload_failed", detail=msg)

    return {
        "url": result.get("secure_url") or result.get("url"),
        "public_id": result.get("public_id"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
        "format": result.get("format"),
        "resource_type": result.get("resource_type"),
    }
