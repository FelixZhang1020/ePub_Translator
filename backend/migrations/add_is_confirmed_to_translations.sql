-- Add is_confirmed column to translations table
-- This marks translations that should not be changed during re-translation

ALTER TABLE translations ADD COLUMN is_confirmed BOOLEAN DEFAULT 0;
