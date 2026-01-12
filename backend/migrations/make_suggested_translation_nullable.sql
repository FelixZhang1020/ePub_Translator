-- Migration: Make suggested_translation nullable in proofreading_suggestions table
-- This allows comment-only proofreading workflow where LLM provides feedback without suggesting replacement text

-- For SQLite, we need to recreate the table as ALTER COLUMN is limited
-- Backup existing data
CREATE TABLE proofreading_suggestions_backup AS SELECT * FROM proofreading_suggestions;

-- Drop old table
DROP TABLE proofreading_suggestions;

-- Recreate table with nullable suggested_translation
CREATE TABLE proofreading_suggestions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    paragraph_id TEXT NOT NULL,
    original_translation TEXT NOT NULL,
    suggested_translation TEXT,  -- Now nullable
    explanation TEXT,
    improvement_level TEXT,
    issue_types TEXT,  -- JSON stored as TEXT in SQLite
    status TEXT NOT NULL DEFAULT 'pending',
    user_modified_text TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (session_id) REFERENCES proofreading_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (paragraph_id) REFERENCES paragraphs(id) ON DELETE CASCADE
);

-- Restore data
INSERT INTO proofreading_suggestions
SELECT * FROM proofreading_suggestions_backup;

-- Clean up
DROP TABLE proofreading_suggestions_backup;
