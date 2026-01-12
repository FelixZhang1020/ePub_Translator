-- Migration: Add analysis_tasks table
-- Date: 2026-01-09
-- Description: Create analysis_tasks table for tracking analysis progress across page refreshes

-- Create analysis_tasks table
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress REAL DEFAULT 0.0,
    current_step VARCHAR(50) NOT NULL,
    step_message TEXT,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create index on project_id for faster queries
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_project_id ON analysis_tasks(project_id);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
