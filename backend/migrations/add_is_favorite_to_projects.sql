-- Migration: Add is_favorite field to projects
-- Date: 2026-01-08
-- Description: Add is_favorite column to projects table for starring/favoriting projects

-- Add is_favorite column (boolean, defaults to false)
-- SQLite syntax:
ALTER TABLE projects ADD COLUMN is_favorite BOOLEAN DEFAULT 0;
