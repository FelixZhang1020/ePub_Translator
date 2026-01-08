"""Base repository with common database operations."""

from typing import Generic, TypeVar, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self, db: AsyncSession, id: str
    ) -> Optional[ModelType]:
        """Get a record by its ID."""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> list[ModelType]:
        """Get all records with pagination."""
        result = await db.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, obj: ModelType
    ) -> ModelType:
        """Create a new record."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
        self, db: AsyncSession, obj: ModelType
    ) -> ModelType:
        """Update an existing record."""
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete(
        self, db: AsyncSession, obj: ModelType
    ) -> None:
        """Delete a record."""
        await db.delete(obj)
        await db.commit()
