"""Iterative translation strategy.

This module provides a multi-step translation strategy that first creates
a literal translation, then refines it for naturalness.
"""

import logging
from typing import Any, Dict

from .base import PromptStrategy
from ..models.context import TranslationContext
from ..models.prompt import Message, PromptBundle
from app.core.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)


class IterativeStrategy(PromptStrategy):
    """Multi-step iterative translation strategy.

    This strategy performs translation in multiple steps:
    1. Step 1: Create a literal, accurate translation
    2. Step 2: Refine for naturalness while preserving meaning

    Prompts are loaded from:
    - Step 1: backend/prompts/translation/system.iterative-step1.md
    - Step 2: backend/prompts/translation/system.iterative-step2.md

    Use get_step() to determine which step to build prompts for.
    """

    def __init__(self, step: int = 1):
        """Initialize strategy for specific step.

        Args:
            step: Which step to build prompts for (1 or 2)
        """
        self.step = step

    def build(self, context: TranslationContext) -> PromptBundle:
        """Build prompt bundle for the configured step.

        Args:
            context: Translation context

        Returns:
            PromptBundle for the current step
        """
        if self.step == 1:
            return self._build_step1(context)
        else:
            return self._build_step2(context)

    def get_template_variables(self, context: TranslationContext) -> Dict[str, Any]:
        """Extract template variables for iterative translation.

        Args:
            context: Translation context

        Returns:
            Dictionary with variables for the current step
        """
        variables: Dict[str, Any] = {
            "content.source": context.source.text,
            "content": {"source": context.source.text},
            "source_text": context.source.text,
            "step": self.step,
            "derived": {},
        }

        # For step 2, include literal translation
        if self.step == 2 and context.existing:
            variables["content.target"] = context.existing.text
            variables["content"]["target"] = context.existing.text
            variables["literal_translation"] = context.existing.text

        # Style information for step 2
        if context.book_analysis:
            variables["derived"].update({
                "writing_style": context.book_analysis.writing_style,
                "tone": context.book_analysis.tone,
            })

        return variables

    def _build_step1(self, context: TranslationContext) -> PromptBundle:
        """Build prompt for step 1: literal translation.

        Args:
            context: Translation context

        Returns:
            PromptBundle for literal translation
        """
        variables = self.get_template_variables(context)

        # Load prompts from .md files
        try:
            template = PromptLoader.load_template("translation", "iterative-step1")
            system_prompt = PromptLoader.render(template.system_prompt, variables)
            user_prompt = PromptLoader.render(template.user_prompt_template, variables)
        except Exception as e:
            logger.warning(f"Failed to load step1 prompts from files: {e}. Using fallback.")
            system_prompt = self._get_fallback_step1_system()
            user_prompt = self._get_fallback_step1_user(variables)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        return PromptBundle(
            messages=messages,
            temperature=0.2,  # Lower temperature for accuracy
            max_tokens=4096,
            mode="iterative_step1",
            estimated_input_tokens=self.estimate_tokens(system_prompt + user_prompt),
            template_variables=variables,
        )

    def _build_step2(self, context: TranslationContext) -> PromptBundle:
        """Build prompt for step 2: refinement.

        Args:
            context: Translation context (should include literal translation)

        Returns:
            PromptBundle for refinement

        Raises:
            ValueError: If literal translation is not available
        """
        if not context.existing:
            raise ValueError(
                "Step 2 requires literal translation from step 1 in context.existing"
            )

        variables = self.get_template_variables(context)

        # Load prompts from .md files
        try:
            template = PromptLoader.load_template("translation", "iterative-step2")
            system_prompt = PromptLoader.render(template.system_prompt, variables)
            user_prompt = PromptLoader.render(template.user_prompt_template, variables)
        except Exception as e:
            logger.warning(f"Failed to load step2 prompts from files: {e}. Using fallback.")
            system_prompt = self._get_fallback_step2_system(variables)
            user_prompt = self._get_fallback_step2_user(variables)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        return PromptBundle(
            messages=messages,
            temperature=0.4,  # Slightly higher for creativity in polishing
            max_tokens=4096,
            mode="iterative_step2",
            estimated_input_tokens=self.estimate_tokens(system_prompt + user_prompt),
            template_variables=variables,
        )

    def _get_fallback_step1_system(self) -> str:
        """Get fallback system prompt for step 1."""
        return """You are a precise translator. Create a literal translation that prioritizes accuracy.

## Translation Requirements
1. Stay as close as possible to the original sentence structure
2. Ensure every concept is accurately conveyed
3. Do not prioritize elegant Chinese at this stage
4. Translate proper nouns according to common conventions

## Output Format
Output only the literal translation, without any explanation or commentary."""

    def _get_fallback_step1_user(self, variables: Dict[str, Any]) -> str:
        """Get fallback user prompt for step 1."""
        source = variables.get("source_text", variables.get("content.source", ""))
        return f"""Please create a literal translation of the following English text:

{source}"""

    def _get_fallback_step2_system(self, variables: Dict[str, Any]) -> str:
        """Get fallback system prompt for step 2."""
        style_section = ""
        derived = variables.get("derived", {})
        if derived.get("writing_style") or derived.get("tone"):
            style_section = f"""
## Style Reference
**Writing Style**: {derived.get('writing_style', 'N/A')}
**Tone**: {derived.get('tone', 'N/A')}
"""
        return f"""You are a Chinese language polishing expert. Based on the provided literal translation, refine it into elegant and fluent Chinese.

## Polishing Requirements
1. Adjust to natural Chinese expressions while preserving the original meaning
2. Eliminate translation artifacts, use idiomatic Chinese
3. Maintain the tone and style of the original text
4. Ensure technical terms remain accurate
{style_section}
## Output Format
Output only the polished translation, without any explanation."""

    def _get_fallback_step2_user(self, variables: Dict[str, Any]) -> str:
        """Get fallback user prompt for step 2."""
        source = variables.get("source_text", variables.get("content.source", ""))
        literal = variables.get("literal_translation", variables.get("content.target", ""))
        return f"""**Original English**:
{source}

**Literal Translation**:
{literal}

Please polish into natural, fluent Chinese:"""
