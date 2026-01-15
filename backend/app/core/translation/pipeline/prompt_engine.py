"""Prompt engine with strategy pattern.

This module provides the PromptEngine class that routes to appropriate
prompt strategies based on translation mode.
"""

from typing import Any, Dict, Type

from ..models.context import TranslationContext, TranslationMode
from ..models.prompt import Message, PromptBundle
from ..strategies import (
    PromptStrategy,
    DirectTranslationStrategy,
    AuthorAwareStrategy,
    OptimizationStrategy,
)
from app.utils.text import safe_truncate
from app.core.prompts.loader import PromptLoader


class PromptEngine:
    """Factory and router for prompt strategies.

    The PromptEngine is responsible for:
    1. Selecting the appropriate strategy based on translation mode
    2. Building prompts using the selected strategy
    3. Handling custom prompt overrides
    4. Providing preview functionality
    """

    # Strategy registry: mode -> strategy class
    _strategies: Dict[TranslationMode, Type[PromptStrategy]] = {
        TranslationMode.DIRECT: DirectTranslationStrategy,
        TranslationMode.AUTHOR_AWARE: AuthorAwareStrategy,
        TranslationMode.OPTIMIZATION: OptimizationStrategy,
    }

    @classmethod
    def register_strategy(
        cls, mode: TranslationMode, strategy_class: Type[PromptStrategy]
    ) -> None:
        """Register a custom strategy for a mode.

        Args:
            mode: Translation mode
            strategy_class: Strategy class to use for this mode
        """
        cls._strategies[mode] = strategy_class

    @classmethod
    def get_strategy(cls, mode: TranslationMode) -> PromptStrategy:
        """Get strategy instance for a mode.

        Args:
            mode: Translation mode

        Returns:
            Strategy instance

        Raises:
            ValueError: If no strategy is registered for the mode
        """
        strategy_class = cls._strategies.get(mode)
        if not strategy_class:
            raise ValueError(f"No strategy registered for mode: {mode}")
        return strategy_class()

    @classmethod
    def build(cls, context: TranslationContext) -> PromptBundle:
        """Build prompt bundle for the given context.

        Args:
            context: Translation context

        Returns:
            PromptBundle ready for LLM call
        """
        # Handle custom prompt overrides
        if context.custom_system_prompt or context.custom_user_prompt:
            return cls._build_custom(context)

        # Get strategy for mode and build
        strategy = cls.get_strategy(context.mode)
        return strategy.build(context)

    @classmethod
    def preview(cls, context: TranslationContext) -> Dict[str, Any]:
        """Generate a preview of prompts without making LLM call.

        This is useful for displaying prompts to users before execution.

        Args:
            context: Translation context

        Returns:
            Dictionary with preview information including:
            - system_prompt: Rendered system prompt
            - user_prompt: Rendered user prompt
            - variables: Template variables used
            - mode: Translation mode
            - estimated_tokens: Estimated token count
        """
        bundle = cls.build(context)
        return bundle.to_preview_dict()

    @classmethod
    def preview_with_highlights(cls, context: TranslationContext) -> Dict[str, Any]:
        """Generate a preview with variable positions highlighted.

        This is useful for showing users which parts of the prompt
        came from which variables.

        Args:
            context: Translation context

        Returns:
            Dictionary with preview and variable mapping
        """
        bundle = cls.build(context)
        variables = bundle.template_variables

        # Build a mapping of variable name to its value and usage
        variable_info = {}
        for name, value in variables.items():
            if value is not None and value != "":
                str_value = str(value)
                variable_info[name] = {
                    "value": safe_truncate(str_value, 200) if len(str_value) > 200 else str_value,
                    "type": type(value).__name__,
                    "used_in": [],
                }

                # Check where variable is used
                system = bundle.system_prompt or ""
                user = bundle.user_prompt or ""

                if str(value) in system:
                    variable_info[name]["used_in"].append("system_prompt")
                if str(value) in user:
                    variable_info[name]["used_in"].append("user_prompt")

        return {
            "system_prompt": bundle.system_prompt,
            "user_prompt": bundle.user_prompt,
            "variables": variable_info,
            "mode": bundle.mode,
            "estimated_tokens": bundle.estimated_input_tokens,
            "temperature": bundle.temperature,
            "max_tokens": bundle.max_tokens,
        }

    @classmethod
    def _build_custom(cls, context: TranslationContext) -> PromptBundle:
        """Build prompt with custom overrides.

        Args:
            context: Translation context with custom prompts

        Returns:
            PromptBundle with custom prompts
        """
        messages = []
        variables: Dict[str, Any] = {
            "source_text": context.source.text,
        }

        # Use custom system prompt or fall back to a simple default
        if context.custom_system_prompt:
            system_content = context.custom_system_prompt
            # Replace common placeholders
            system_content = cls._replace_placeholders(system_content, context)
            messages.append(Message(role="system", content=system_content))
            variables["custom_system_prompt"] = context.custom_system_prompt
        else:
            # Minimal default system prompt
            messages.append(
                Message(
                    role="system",
                    content="You are a professional translator. Translate the text accurately and naturally.",
                )
            )

        # Use custom user prompt or default
        if context.custom_user_prompt:
            user_content = context.custom_user_prompt
            user_content = cls._replace_placeholders(user_content, context)
            variables["custom_user_prompt"] = context.custom_user_prompt
        else:
            user_content = context.source.text

        messages.append(Message(role="user", content=user_content))

        return PromptBundle(
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
            mode="custom",
            template_variables=variables,
        )

    @classmethod
    def _replace_placeholders(cls, template: str, context: TranslationContext) -> str:
        """Replace placeholders in custom prompts using full variable system.

        Supports all template variables including:
        - content.source, content.target
        - project.title, project.author, project.source_language, project.target_language
        - context.previous_source, context.previous_target, context.next_source
        - derived.* variables from book analysis
        - Legacy placeholders for backward compatibility

        Args:
            template: Template string with placeholders
            context: Translation context

        Returns:
            String with placeholders replaced
        """
        # Build comprehensive variable dictionary
        variables: Dict[str, Any] = {
            # Content namespace
            "content.source": context.source.text,
            "content.source_text": context.source.text,  # Legacy alias
            "source_text": context.source.text,  # Legacy alias

            # Project namespace
            "project.title": context.project.title if context.project else "",
            "project.author": context.project.author if context.project else "",
            "project.source_language": context.project.source_language if context.project else "en",
            "project.target_language": context.target_language,
            "target_language": context.target_language,  # Legacy alias

            # Meta namespace
            "meta.word_count": context.source.word_count,
            "meta.paragraph_index": context.source.paragraph_index or 0,
            "meta.chapter_index": context.source.chapter_index or 0,
        }

        # Add existing translation if available
        if context.existing:
            variables["content.target"] = context.existing.text
            variables["existing_translation"] = context.existing.text

        # Add context (previous/next paragraphs) if available
        if context.adjacent:
            if context.adjacent.previous_original:
                variables["context.previous_source"] = context.adjacent.previous_original
            if context.adjacent.previous_translation:
                variables["context.previous_target"] = context.adjacent.previous_translation
            if context.adjacent.next_original:
                variables["context.next_source"] = context.adjacent.next_original

        # Add book analysis derived variables if available
        if context.book_analysis:
            analysis = context.book_analysis
            if analysis.writing_style:
                variables["derived.writing_style"] = analysis.writing_style
                variables["derived.has_writing_style"] = True
            if analysis.tone:
                variables["derived.tone"] = analysis.tone
            if analysis.target_audience:
                variables["derived.target_audience"] = analysis.target_audience
            if analysis.author_biography:
                variables["derived.author_biography"] = analysis.author_biography
                variables["derived.has_author_biography"] = True
            if analysis.key_terminology:
                # Format terminology as table from Dict[str, str]
                terms = analysis.key_terminology
                if terms:
                    table_rows = ["| Term | Translation |", "|------|-------------|"]
                    for src, tgt in list(terms.items())[:20]:  # Limit to 20 terms
                        table_rows.append(f"| {src} | {tgt} |")
                    variables["derived.terminology_table"] = "\n".join(table_rows)
                    variables["derived.has_terminology"] = True

            # Translation principles
            if analysis.translation_principles:
                principles = analysis.translation_principles
                if principles.priority_order:
                    variables["derived.priority_order"] = ", ".join(principles.priority_order)
                if principles.faithfulness_boundary:
                    variables["derived.faithfulness_boundary"] = principles.faithfulness_boundary
                if principles.permissible_adaptation:
                    variables["derived.permissible_adaptation"] = principles.permissible_adaptation
                if principles.style_constraints:
                    variables["derived.style_constraints"] = principles.style_constraints
                if principles.red_lines:
                    variables["derived.red_lines"] = principles.red_lines
                variables["derived.has_translation_principles"] = True

        # Use PromptLoader.render() for proper template variable substitution
        return PromptLoader.render(template, variables)

