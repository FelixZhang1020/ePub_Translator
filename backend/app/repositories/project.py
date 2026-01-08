"""Project repository for project-related database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database.project import Project
from app.models.database.chapter import Chapter
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations."""

    def __init__(self):
        super().__init__(Project)

    async def get_with_chapters(
        self, db: AsyncSession, project_id: str
    ) -> Optional[Project]:
        """Get a project with all its chapters loaded."""
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.chapters))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_with_analysis(
        self, db: AsyncSession, project_id: str
    ) -> Optional[Project]:
        """Get a project with its book analysis loaded."""
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.book_analysis))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_with_all_relations(
        self, db: AsyncSession, project_id: str
    ) -> Optional[Project]:
        """Get a project with all relations loaded."""
        result = await db.execute(
            select(Project)
            .options(
                selectinload(Project.chapters).selectinload(Chapter.paragraphs),
                selectinload(Project.book_analysis),
                selectinload(Project.tasks),
            )
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()


# Global instance for convenience
project_repository = ProjectRepository()
