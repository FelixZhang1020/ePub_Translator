-- Migration: Remove prompt content from database
-- Date: 2026-01-07
-- Description: Remove system_prompt, default_user_prompt, variables columns from prompt_templates
--              Add template_name column to reference file-based templates
--              Prompt content is now stored in backend/prompts/{category}/system.{template_name}.md

-- SQLite doesn't support DROP COLUMN, so we need to recreate the table

-- Step 1: Create new table with updated schema
CREATE TABLE prompt_templates_new (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    template_name VARCHAR(100) NOT NULL DEFAULT 'default',
    is_builtin BOOLEAN NOT NULL DEFAULT 0,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Step 2: Migrate data with template_name inference
-- For existing templates, infer template_name from the name field
INSERT INTO prompt_templates_new (id, name, description, category, template_name, is_builtin, is_default, created_at, updated_at)
SELECT
    id,
    name,
    description,
    category,
    CASE
        WHEN name LIKE '%Reformed%' OR name LIKE '%改革宗%' THEN 'reformed-theology'
        ELSE 'default'
    END as template_name,
    is_builtin,
    is_default,
    created_at,
    updated_at
FROM prompt_templates;

-- Step 3: Drop old table
DROP TABLE prompt_templates;

-- Step 4: Rename new table
ALTER TABLE prompt_templates_new RENAME TO prompt_templates;

-- Step 5: Verify migration
-- SELECT * FROM prompt_templates;
