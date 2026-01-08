"""Repository pattern implementation for database access.

Repositories provide a clean abstraction layer between business logic
and database operations, making code more testable and maintainable.
"""

from .base import BaseRepository
from .project import ProjectRepository
from .translation import TranslationTaskRepository

__all__ = [
    "BaseRepository",
    "ProjectRepository",
    "TranslationTaskRepository",
]
