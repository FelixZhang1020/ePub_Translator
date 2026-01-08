"""Database model mixins for shared functionality."""


class ProgressTrackingMixin:
    """Mixin for models that track progress of a task.

    Requires the model to have these attributes:
    - completed_paragraphs: int
    - total_paragraphs: int
    - progress: float
    """

    completed_paragraphs: int
    total_paragraphs: int
    progress: float

    def update_progress(self) -> None:
        """Update progress percentage based on completed paragraphs."""
        if self.total_paragraphs > 0:
            self.progress = self.completed_paragraphs / self.total_paragraphs
