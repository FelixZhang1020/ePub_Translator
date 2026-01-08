-- Migration: Add proofreading v2 fields
-- Date: 2026-01-07
-- Description: Add improvement_level and issue_types columns to proofreading_suggestions table

-- Add improvement_level column (enum-like string: none, optional, recommended, critical)
ALTER TABLE proofreading_suggestions
ADD COLUMN IF NOT EXISTS improvement_level VARCHAR(20) DEFAULT NULL;

-- Add issue_types column (JSON array: ["accuracy", "naturalness", "modern_usage", "style_consistency", "readability"])
ALTER TABLE proofreading_suggestions
ADD COLUMN IF NOT EXISTS issue_types JSON DEFAULT NULL;

-- Note: For SQLite, use this syntax instead:
-- ALTER TABLE proofreading_suggestions ADD COLUMN improvement_level VARCHAR(20);
-- ALTER TABLE proofreading_suggestions ADD COLUMN issue_types TEXT;
