"""Translation repository for translation-related database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database.translation import TranslationTask, Translation
from app.models.database.enums import TaskStatus
from app.repositories.base import BaseRepository


class TranslationTaskRepository(BaseRepository[TranslationTask]):
    """Repository for TranslationTask model operations."""

    def __init__(self):
        super().__init__(TranslationTask)

    async def get_active_task(
        self, db: AsyncSession, project_id: str
    ) -> Optional[TranslationTask]:
        """Get the active (processing or paused) task for a project."""
        result = await db.execute(
            select(TranslationTask)
            .where(
                TranslationTask.project_id == project_id,
                TranslationTask.status.in_([
                    TaskStatus.PROCESSING.value,
                    TaskStatus.PAUSED.value,
                ])
            )
            .order_by(TranslationTask.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_task(
        self, db: AsyncSession, project_id: str
    ) -> Optional[TranslationTask]:
        """Get the most recent task for a project."""
        result = await db.execute(
            select(TranslationTask)
            .where(TranslationTask.project_id == project_id)
            .order_by(TranslationTask.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_with_project(
        self, db: AsyncSession, task_id: str
    ) -> Optional[TranslationTask]:
        """Get a task with its project loaded."""
        result = await db.execute(
            select(TranslationTask)
            .options(selectinload(TranslationTask.project))
            .where(TranslationTask.id == task_id)
        )
        return result.scalar_one_or_none()


class TranslationRepository(BaseRepository[Translation]):
    """Repository for Translation model operations."""

    def __init__(self):
        super().__init__(Translation)

    async def get_by_paragraph_id(
        self, db: AsyncSession, paragraph_id: str
    ) -> Optional[Translation]:
        """Get translation for a specific paragraph."""
        result = await db.execute(
            select(Translation)
            .where(Translation.paragraph_id == paragraph_id)
        )
        return result.scalar_one_or_none()


# Global instances for convenience
translation_task_repository = TranslationTaskRepository()
translation_repository = TranslationRepository()
