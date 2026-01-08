"""Centralized enum definitions for database models.

All status and type enums should be defined here for consistency.
"""

from enum import Enum


# =============================================================================
# Translation Enums
# =============================================================================


class TranslationMode(str, Enum):
    """Translation mode enum."""

    AUTHOR_BASED = "author_based"
    OPTIMIZATION = "optimization"


class TaskStatus(str, Enum):
    """Translation task status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Proofreading Enums
# =============================================================================


class ProofreadingStatus(str, Enum):
    """Proofreading session status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SuggestionStatus(str, Enum):
    """Suggestion status enum."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ImprovementLevel(str, Enum):
    """Improvement level enum for proofreading suggestions."""

    NONE = "none"  # No improvement needed
    OPTIONAL = "optional"  # Minor style improvements, not necessary
    RECOMMENDED = "recommended"  # Noticeable improvements, but original is acceptable
    CRITICAL = "critical"  # Must fix - errors or serious issues


# =============================================================================
# Prompt Template Enums
# =============================================================================


class PromptCategory(str, Enum):
    """Categories of prompts."""

    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    PROOFREADING = "proofreading"
    OPTIMIZATION = "optimization"


class VariableType(str, Enum):
    """Types of variable values."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"  # For arrays or objects
