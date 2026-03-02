from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.features.common.db import BaseRepository
from app.features.uploads.models import Upload


class UploadRepository(BaseRepository[Upload]):
    def __init__(self, db: AsyncSession):
        super().__init__(Upload, db)

    async def get_by_public_id(self, *, public_id: str) -> Upload | None:
        q = select(Upload).where(Upload.public_id == public_id)
        res = await self.db.execute(q)
        return res.scalars().first()

    async def mark_accessed(self, *, row: Upload) -> None:
        row.access_count = int(getattr(row, "access_count", 0) or 0) + 1
        row.last_accessed_at = datetime.utcnow()
        self.db.add(row)
        await self.db.flush()
