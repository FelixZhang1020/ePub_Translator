"""Variable management for prompt templates.

This module provides a centralized variable context builder that aggregates:
- Project variables (book title, author, etc.)
- Content variables (source text, target text - stage aware)
- Context variables (previous/next paragraphs for continuity)
- Pipeline variables (analysis result, suggestions, etc.)
- Derived variables (extracted from analysis: writing_style, tone, etc.)
- Meta variables (computed at runtime: word count, indices)
- User-defined variables (custom key-value pairs)
- Macros (composite templates for reuse)

Variable Naming Convention:
- Use canonical names: content.source, content.target
- Legacy aliases are handled by loader.py for backward compatibility
"""

from typing import Any, Dict, List, Literal, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.project import Project
from app.models.database.book_analysis import BookAnalysis
from app.core.prompts.loader import PromptLoader
from app.utils.text import safe_truncate


# =============================================================================
# Stage Types
# =============================================================================
StageType = Literal["analysis", "translation", "optimization", "proofreading"]


# =============================================================================
# Dynamic Derived Variable Mappings
# =============================================================================
# These mappings define how to extract derived variables from analysis results.
# Format: (source_path, target_key, transform_function_name)
DERIVED_MAPPINGS: List[tuple] = [
    # Direct field mappings
    ("author_name", "author_name", None),
    ("author_biography", "author_biography", None),
    ("writing_style", "writing_style", None),
    ("tone", "tone", None),
    ("target_audience", "target_audience", None),
    ("genre_conventions", "genre_conventions", None),

    # Nested field mappings with transforms
    ("key_terminology", "key_terminology", None),
    ("key_terminology", "terminology_table", "format_terminology"),

    # Translation principles
    ("translation_principles.priority_order", "priority_order", None),
    ("translation_principles.faithfulness_boundary", "faithfulness_boundary", None),
    ("translation_principles.permissible_adaptation", "permissible_adaptation", None),
    ("translation_principles.style_constraints", "style_constraints", None),
    ("translation_principles.red_lines", "red_lines", None),

    # Custom guidelines
    ("custom_guidelines", "custom_guidelines", None),
]


class VariableContext:
    """Complete variable context for prompt rendering.

    Organized into logical namespaces:
    - project: Static metadata from EPUB/project settings
    - content: Current paragraph source/target (stage-aware)
    - context: Surrounding paragraphs for continuity
    - pipeline: Output from previous processing steps
    - derived: Values extracted from analysis
    - meta: Runtime computed values (word count, indices)
    - user: Custom user-defined variables
    - macros: Reusable template fragments
    """

    def __init__(self):
        """Initialize empty variable context."""
        self.project: Dict[str, Any] = {}
        self.content: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}  # NEW: for previous/next paragraphs
        self.pipeline: Dict[str, Any] = {}
        self.derived: Dict[str, Any] = {}
        self.meta: Dict[str, Any] = {}  # NEW: for computed values
        self.user: Dict[str, Any] = {}
        self.macros: Dict[str, str] = {}  # NEW: for template macros

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to a flat dictionary with namespaced keys.

        Returns:
            Dictionary with keys like 'project.title', 'derived.writing_style', etc.
        """
        result: Dict[str, Any] = {}

        for key, value in self.project.items():
            result[f"project.{key}"] = value

        for key, value in self.content.items():
            result[f"content.{key}"] = value

        for key, value in self.context.items():
            result[f"context.{key}"] = value

        for key, value in self.pipeline.items():
            result[f"pipeline.{key}"] = value

        for key, value in self.derived.items():
            result[f"derived.{key}"] = value

        for key, value in self.meta.items():
            result[f"meta.{key}"] = value

        for key, value in self.user.items():
            result[f"user.{key}"] = value

        return result

    def to_nested_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to nested dictionary structure.

        Returns:
            Dictionary with namespaces as top-level keys.
        """
        return {
            "project": self.project,
            "content": self.content,
            "context": self.context,
            "pipeline": self.pipeline,
            "derived": self.derived,
            "meta": self.meta,
            "user": self.user,
        }

    def get_macros(self) -> Dict[str, str]:
        """Get macro definitions for template rendering.

        Returns:
            Dictionary of macro name to template string
        """
        return self.macros


class VariableService:
    """Service for building and managing variable contexts.

    Provides stage-aware variable population and dynamic derived extraction.
    """

    # Default macros available in all templates
    # Note: Use English labels here; Chinese text should be in prompt templates
    DEFAULT_MACROS: Dict[str, str] = {
        "book_info": "{{project.title}} by {{project.author}}",
        "style_guide": (
            "{{#if derived.writing_style}}"
            "**Style**: {{derived.writing_style}}\n"
            "{{/if}}"
            "{{#if derived.tone}}"
            "**Tone**: {{derived.tone}}"
            "{{/if}}"
        ),
        "terminology_section": (
            "{{#if derived.has_terminology}}"
            "### Terminology\n{{derived.terminology_table}}"
            "{{/if}}"
        ),
    }

    @classmethod
    async def build_context(
        cls,
        db: AsyncSession,
        project_id: str,
        stage: Optional[StageType] = None,
        source_text: Optional[str] = None,
        target_text: Optional[str] = None,
        paragraph_index: Optional[int] = None,
        chapter_index: Optional[int] = None,
        chapter_title: Optional[str] = None,
        # Context for continuity
        previous_source: Optional[str] = None,
        previous_target: Optional[str] = None,
        next_source: Optional[str] = None,
        # Pipeline outputs
        reference_translation: Optional[str] = None,
        suggested_changes: Optional[str] = None,
        sample_paragraphs: Optional[str] = None,
        # Legacy aliases (for backward compatibility)
        existing_translation: Optional[str] = None,
        previous_original: Optional[str] = None,
        previous_translation: Optional[str] = None,
    ) -> VariableContext:
        """Build a complete variable context for prompt rendering.

        Stage-aware population:
        - analysis: Uses sample_paragraphs
        - translation: Uses source_text, populates content.source
        - optimization: Uses source_text + target_text, populates both
        - proofreading: Uses source_text + target_text, populates both

        Args:
            db: Database session
            project_id: Project ID
            stage: Current processing stage (affects variable mapping)
            source_text: Source text to translate
            target_text: Current translation (canonical name)
            paragraph_index: Current paragraph index
            chapter_index: Current chapter index
            chapter_title: Current chapter title
            previous_source: Previous paragraph source
            previous_target: Previous paragraph translation
            next_source: Next paragraph source
            reference_translation: Reference translation if available
            suggested_changes: Suggested edits for optimization
            sample_paragraphs: Sample paragraphs for analysis stage
            existing_translation: Legacy alias for target_text
            previous_original: Legacy alias for previous_source
            previous_translation: Legacy alias for previous_target

        Returns:
            Complete VariableContext instance
        """
        context = VariableContext()

        # Handle legacy aliases
        if existing_translation and not target_text:
            target_text = existing_translation
        if previous_original and not previous_source:
            previous_source = previous_original
        if previous_translation and not previous_target:
            previous_target = previous_translation

        # Load project data
        project = await cls._load_project(db, project_id)
        if project:
            context.project = cls._extract_project_vars(project)

        # Load analysis and extract derived variables
        analysis = await cls._load_analysis(db, project_id)
        if analysis and analysis.raw_analysis:
            context.derived = cls._extract_derived_vars(analysis.raw_analysis)

        # Load user-defined variables and macros
        user_vars = await cls._load_user_variables(db, project_id)
        context.user = user_vars

        # Set up macros (default + user-defined)
        context.macros = cls.DEFAULT_MACROS.copy()
        if "macros" in user_vars and isinstance(user_vars["macros"], dict):
            context.macros.update(user_vars["macros"])

        # =================================================================
        # Stage-aware content variable population
        # =================================================================
        # Use canonical names: content.source, content.target
        if source_text:
            context.content["source"] = source_text
            # Also populate legacy names for backward compatibility
            context.content["source_text"] = source_text
            context.content["original_text"] = source_text

        if target_text:
            context.content["target"] = target_text
            # Legacy names
            context.content["translated_text"] = target_text
            context.content["current_translation"] = target_text
            context.content["existing_translation"] = target_text

        if chapter_title:
            context.content["chapter_title"] = chapter_title

        # Analysis stage special handling
        if sample_paragraphs:
            context.content["sample_paragraphs"] = sample_paragraphs

        # =================================================================
        # Context variables (for continuity)
        # =================================================================
        if previous_source:
            context.context["previous_source"] = previous_source
        if previous_target:
            context.context["previous_target"] = previous_target
        if next_source:
            context.context["next_source"] = next_source

        # =================================================================
        # Meta variables (computed at runtime)
        # =================================================================
        if source_text:
            context.meta["word_count"] = len(source_text.split())
            context.meta["char_count"] = len(source_text)
        if paragraph_index is not None:
            context.meta["paragraph_index"] = paragraph_index
        if chapter_index is not None:
            context.meta["chapter_index"] = chapter_index
        if stage:
            context.meta["stage"] = stage

        # =================================================================
        # Pipeline variables
        # =================================================================
        if reference_translation:
            context.pipeline["reference_translation"] = reference_translation
        if suggested_changes:
            context.pipeline["suggested_changes"] = suggested_changes

        return context

    @classmethod
    async def _load_project(
        cls, db: AsyncSession, project_id: str
    ) -> Optional[Project]:
        """Load project from database."""
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def _load_analysis(
        cls, db: AsyncSession, project_id: str
    ) -> Optional[BookAnalysis]:
        """Load book analysis from database."""
        result = await db.execute(
            select(BookAnalysis).where(BookAnalysis.project_id == project_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def _load_user_variables(
        cls, db: AsyncSession, project_id: str
    ) -> Dict[str, Any]:
        """Load user-defined variables from file.

        Variables are stored in: projects/{project_id}/variables.json

        Returns:
            Dictionary mapping variable names to their values.
        """
        # Load from file-based storage (not database)
        return PromptLoader.load_project_variables(project_id)

    # Default target language (used when not configured in project)
    DEFAULT_TARGET_LANGUAGE = "zh"

    @classmethod
    def _extract_project_vars(cls, project: Project) -> Dict[str, Any]:
        """Extract project-level variables.

        Args:
            project: Project database model

        Returns:
            Dictionary with project variables
        """
        # Try to get target_language from project config
        target_language = cls.DEFAULT_TARGET_LANGUAGE
        config = PromptLoader.load_project_config(project.id)
        if config and "target_language" in config:
            target_language = config["target_language"]

        return {
            "title": project.epub_title or project.name or "",
            "author": project.epub_author or "",
            "author_background": project.author_background or "",
            "name": project.name or "",
            "source_language": project.epub_language or "en",
            "target_language": target_language,
            "total_chapters": project.total_chapters or 0,
            "total_paragraphs": project.total_paragraphs or 0,
        }

    @classmethod
    def _extract_derived_vars(cls, raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract derived variables from analysis result.

        Uses DERIVED_MAPPINGS configuration for dynamic extraction.

        Args:
            raw_analysis: Raw analysis dictionary from BookAnalysis.raw_analysis

        Returns:
            Dictionary with derived variables
        """
        # Default scaffold so templates always have defined keys
        derived: Dict[str, Any] = {
            "author_name": "",
            "author_biography": "",
            "writing_style": "",
            "tone": "",
            "target_audience": "",
            "genre_conventions": "",
            "key_terminology": {},
            "translation_principles": {},
            "terminology_table": "",
            "priority_order": [],
            "faithfulness_boundary": "",
            "permissible_adaptation": "",
            "style_constraints": "",
            "red_lines": "",
            "custom_guidelines": [],
        }

        # Process dynamic mappings
        for source_path, target_key, transform in DERIVED_MAPPINGS:
            value = cls._get_nested_value(raw_analysis, source_path)
            if value is not None:
                if transform:
                    value = cls._apply_transform(value, transform)
                derived[target_key] = value

        # Add has_* flags for conditional blocks (auto-generate from derived)
        derived["has_analysis"] = bool(raw_analysis)
        derived["has_writing_style"] = bool(derived.get("writing_style"))
        derived["has_tone"] = bool(derived.get("tone"))
        derived["has_terminology"] = bool(derived.get("key_terminology"))
        derived["has_target_audience"] = bool(derived.get("target_audience"))
        derived["has_genre_conventions"] = bool(derived.get("genre_conventions"))
        derived["has_translation_principles"] = bool(derived.get("priority_order"))
        derived["has_custom_guidelines"] = bool(derived.get("custom_guidelines"))
        derived["has_style_constraints"] = bool(derived.get("style_constraints"))

        return derived

    @classmethod
    def _get_nested_value(cls, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value using dot notation path.

        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., "translation_principles.priority_order")

        Returns:
            Value at path, or None if not found
        """
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @classmethod
    def _apply_transform(cls, value: Any, transform: str) -> Any:
        """Apply a transform function to a value.

        Supported transforms:
        - format_terminology: Convert terminology dict/list to markdown list
        - format_list: Convert list to bullet points
        - join_comma: Join list with commas

        Args:
            value: Value to transform
            transform: Transform function name

        Returns:
            Transformed value
        """
        if transform == "format_terminology":
            return cls._format_terminology(value)
        elif transform == "format_list":
            if isinstance(value, list):
                return "\n".join(f"- {item}" for item in value)
            return str(value)
        elif transform == "join_comma":
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            return str(value)
        return value

    @classmethod
    def _format_terminology(cls, terms: Any) -> str:
        """Format terminology as markdown list.

        Args:
            terms: Dict or list of terminology entries

        Returns:
            Markdown formatted string
        """
        if isinstance(terms, dict):
            return "\n".join(f"- {en}: {zh}" for en, zh in terms.items())
        elif isinstance(terms, list):
            lines = []
            for term in terms:
                if isinstance(term, dict):
                    en = term.get("english_term") or term.get("english", "")
                    zh = term.get("chinese_translation") or term.get("chinese", "")
                    notes = term.get("notes", "")
                    if en and zh:
                        line = f"- {en}: {zh}"
                        if notes:
                            line += f" ({notes})"
                        lines.append(line)
                else:
                    lines.append(f"- {term}")
            return "\n".join(lines)
        return str(terms)

    @classmethod
    def _parse_variable_value(cls, value: str, value_type: str) -> Any:
        """Parse variable value based on its type.

        Args:
            value: String value from database
            value_type: Type of the variable

        Returns:
            Parsed value of appropriate type
        """
        if value_type == "number":
            try:
                return float(value) if "." in value else int(value)
            except (ValueError, TypeError):
                return 0
        elif value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            import json
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            return value

    @classmethod
    def is_value_effective(cls, value: Any) -> bool:
        """Check if a value is considered 'effective' (non-empty).

        Args:
            value: Value to check

        Returns:
            True if value is non-empty/non-null, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, str):
            return len(value.strip()) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True  # Booleans are always effective
        return True  # Numbers, etc.

    @classmethod
    async def get_available_variables(
        cls,
        db: AsyncSession,
        project_id: str,
        stage: Optional[StageType] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get list of available variables for a project.

        Args:
            db: Database session
            project_id: Project ID
            stage: Optional stage filter (analysis, translation, etc.)

        Returns:
            Dictionary with variable categories and their variables
        """
        # Build context to get actual values
        context = await cls.build_context(db, project_id, stage=stage)

        result: Dict[str, List[Dict[str, Any]]] = {
            "project": [],
            "content": [],
            "context": [],
            "pipeline": [],
            "derived": [],
            "meta": [],
            "user": [],
            "macros": [],
        }

        # Project variables (always available)
        project_var_info = [
            ("title", "Book title from EPUB metadata"),
            ("author", "Author name from EPUB metadata"),
            ("author_background", "Custom author background info"),
            ("name", "Project name"),
            ("source_language", "Source language code"),
            ("target_language", "Target language code"),
            ("total_chapters", "Total number of chapters"),
            ("total_paragraphs", "Total number of paragraphs"),
        ]
        for key, desc in project_var_info:
            result["project"].append({
                "name": f"project.{key}",
                "description": desc,
                "current_value": context.project.get(key),
                "type": "string" if isinstance(context.project.get(key), str) else "number",
                "stages": ["analysis", "translation", "optimization", "proofreading"],
            })

        # Content variables with canonical names
        content_vars = [
            ("source", "Source text (canonical)", ["translation", "optimization", "proofreading"]),
            ("target", "Current translation (canonical)", ["optimization", "proofreading"]),
            ("source_text", "Source text (legacy alias)", ["translation", "optimization"]),
            ("original_text", "Original text (legacy alias)", ["proofreading"]),
            ("translated_text", "Translated text (legacy alias)", ["optimization", "proofreading"]),
            ("chapter_title", "Current chapter title", ["translation", "optimization", "proofreading"]),
            ("sample_paragraphs", "Sample paragraphs for analysis", ["analysis"]),
        ]
        for name, desc, stages in content_vars:
            if stage is None or stage in stages:
                result["content"].append({
                    "name": f"content.{name}",
                    "description": desc,
                    "current_value": context.content.get(name),
                    "stages": stages,
                })

        # Context variables (surrounding paragraphs)
        context_vars = [
            ("previous_source", "Previous paragraph source text", ["translation"]),
            ("previous_target", "Previous paragraph translation", ["translation"]),
            ("next_source", "Next paragraph source text", ["translation"]),
        ]
        for name, desc, stages in context_vars:
            if stage is None or stage in stages:
                result["context"].append({
                    "name": f"context.{name}",
                    "description": desc,
                    "current_value": context.context.get(name),
                    "stages": stages,
                })

        # Pipeline variables
        pipeline_vars = [
            ("reference_translation", "Matched reference translation", ["translation"]),
            ("suggested_changes", "User-provided suggestions", ["optimization"]),
        ]
        for name, desc, stages in pipeline_vars:
            if stage is None or stage in stages:
                result["pipeline"].append({
                    "name": f"pipeline.{name}",
                    "description": desc,
                    "current_value": context.pipeline.get(name),
                    "stages": stages,
                })

        # Meta variables (computed at runtime)
        meta_vars = [
            ("word_count", "Word count of source text", ["translation", "optimization"]),
            ("char_count", "Character count of source text", ["translation", "optimization"]),
            ("paragraph_index", "Current paragraph index", ["translation", "proofreading"]),
            ("chapter_index", "Current chapter index", ["translation", "proofreading"]),
            ("stage", "Current processing stage", ["analysis", "translation", "optimization", "proofreading"]),
        ]
        for name, desc, stages in meta_vars:
            if stage is None or stage in stages:
                result["meta"].append({
                    "name": f"meta.{name}",
                    "description": desc,
                    "current_value": context.meta.get(name),
                    "stages": stages,
                })

        # Derived variables (from analysis)
        derived_var_info = [
            ("writing_style", "Writing style from analysis"),
            ("tone", "Tone from analysis"),
            ("target_audience", "Target audience"),
            ("genre_conventions", "Genre conventions"),
            ("terminology_table", "Formatted terminology list"),
            ("priority_order", "Translation priority order"),
            ("faithfulness_boundary", "Strict faithfulness requirements"),
            ("permissible_adaptation", "Allowed adaptations"),
            ("style_constraints", "Style constraints"),
            ("red_lines", "Prohibited actions"),
            ("custom_guidelines", "Custom translation guidelines"),
            # Boolean flags
            ("has_analysis", "Whether analysis exists"),
            ("has_writing_style", "Whether writing style is defined"),
            ("has_tone", "Whether tone is defined"),
            ("has_terminology", "Whether terminology is defined"),
            ("has_custom_guidelines", "Whether custom guidelines exist"),
            ("has_style_constraints", "Whether style constraints exist"),
        ]
        for key, desc in derived_var_info:
            value = context.derived.get(key)
            result["derived"].append({
                "name": f"derived.{key}",
                "description": desc,
                "current_value": value if not isinstance(value, (dict, list)) else safe_truncate(str(value), 100),
                "type": "boolean" if key.startswith("has_") else (
                    "object" if isinstance(value, (dict, list)) else "string"
                ),
                "stages": ["translation", "optimization", "proofreading"],
            })

        # User variables
        for key, value in context.user.items():
            if key != "macros":  # Macros are listed separately
                result["user"].append({
                    "name": f"user.{key}",
                    "description": "User-defined variable",
                    "current_value": value if not isinstance(value, (dict, list)) else safe_truncate(str(value), 100),
                    "editable": True,
                    "stages": ["analysis", "translation", "optimization", "proofreading"],
                })

        # Macros
        for name, template in context.macros.items():
            result["macros"].append({
                "name": f"@{name}",
                "description": f"Macro: expands to template",
                "template": safe_truncate(template, 100) if len(template) > 100 else template,
                "stages": ["analysis", "translation", "optimization", "proofreading"],
            })

        return result
