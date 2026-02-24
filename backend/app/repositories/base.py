from typing import Generic, TypeVar, Type, Optional, List, Any, Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: ModelType, commit: bool = True) -> ModelType:
        self.db.add(obj_in)
        if commit:
            await self.db.commit()
            await self.db.refresh(obj_in)
        else:
            await self.db.flush()
        return obj_in
    
    async def update(self, db_obj: ModelType, obj_in: dict | Any, commit: bool = True) -> ModelType:
        # Если obj_in - это словарь, обновить атрибуты
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        self.db.add(db_obj)
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        else:
            await self.db.flush()
        return db_obj

    async def delete(self, id: Any, commit: bool = True) -> Optional[ModelType]:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            if commit:
                await self.db.commit()
        return obj
