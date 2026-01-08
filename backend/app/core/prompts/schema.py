"""
Shared Variable Schema Loader

Loads the shared variable schema from the shared directory.
This ensures frontend and backend use the same variable definitions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Path to the shared schema
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent.parent / "shared" / "variable-schema.json"


class VariableSchema:
    """Loader for the shared variable schema."""

    _instance: Optional["VariableSchema"] = None
    _schema: Optional[Dict[str, Any]] = None

    def __new__(cls) -> "VariableSchema":
        """Singleton pattern to avoid reloading schema."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Load schema if not already loaded."""
        if self._schema is None:
            self._load_schema()

    def _load_schema(self) -> None:
        """Load the schema from the JSON file."""
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        else:
            # Fallback to empty schema if file not found
            self._schema = {
                "variables": [],
                "categories": {},
                "aliases": {},
                "stages": [],
            }

    @property
    def schema(self) -> Dict[str, Any]:
        """Get the full schema."""
        return self._schema or {}

    @property
    def variables(self) -> List[Dict[str, Any]]:
        """Get all variable definitions."""
        return self.schema.get("variables", [])

    @property
    def categories(self) -> Dict[str, Any]:
        """Get category definitions."""
        return self.schema.get("categories", {})

    @property
    def aliases(self) -> Dict[str, str]:
        """Get variable aliases mapping."""
        return self.schema.get("aliases", {})

    @property
    def stages(self) -> List[str]:
        """Get available stages."""
        return self.schema.get("stages", [])

    @property
    def default_macros(self) -> Dict[str, str]:
        """Get default macro definitions."""
        return self.schema.get("defaultMacros", {})

    @property
    def template_syntax(self) -> Dict[str, str]:
        """Get template syntax reference."""
        return self.schema.get("templateSyntax", {})

    def get_variable(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get a variable definition by full name.

        Args:
            full_name: Variable full name (e.g., 'project.title')

        Returns:
            Variable definition dict or None if not found
        """
        for var in self.variables:
            if var.get("fullName") == full_name:
                return var
        return None

    def get_variables_for_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get variables available for a specific stage.

        Args:
            stage: Stage name (analysis, translation, optimization, proofreading)

        Returns:
            List of variable definitions available in that stage
        """
        return [
            var for var in self.variables
            if stage in var.get("stages", [])
        ]

    def get_variables_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get variables in a specific category.

        Args:
            category: Category name (project, content, derived, etc.)

        Returns:
            List of variable definitions in that category
        """
        return [
            var for var in self.variables
            if var.get("category") == category
        ]

    def get_canonical_name(self, var_name: str) -> str:
        """Resolve a variable name to its canonical form.

        Args:
            var_name: Variable name (may be an alias)

        Returns:
            Canonical variable name
        """
        # Check if it's an alias
        if var_name in self.aliases:
            return self.aliases[var_name]

        # Check if any variable has this as a legacy alias
        for var in self.variables:
            if var.get("isLegacy") and var.get("fullName") == var_name:
                canonical = var.get("canonicalName")
                if canonical:
                    return canonical

        return var_name

    def is_variable_valid_for_stage(self, var_name: str, stage: str) -> bool:
        """Check if a variable is valid for a specific stage.

        Args:
            var_name: Variable full name
            stage: Stage name

        Returns:
            True if variable is available in the stage
        """
        var = self.get_variable(var_name)
        if var:
            return stage in var.get("stages", [])
        return False

    def get_legacy_variables(self) -> List[Dict[str, Any]]:
        """Get all legacy/deprecated variables.

        Returns:
            List of variable definitions marked as legacy
        """
        return [
            var for var in self.variables
            if var.get("isLegacy", False)
        ]


# Global instance for easy access
variable_schema = VariableSchema()
