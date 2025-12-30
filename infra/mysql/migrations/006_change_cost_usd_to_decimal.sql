-- Migration: Change cost_usd from FLOAT to DECIMAL
-- Date: 2025-12-30
-- Description: Changes cost_usd column type from FLOAT to DECIMAL(10, 6) for better precision
--
-- IMPORTANT: This migration is for databases that already applied 005_add_message_metadata.sql
-- with the FLOAT type. New installations using the updated 005 migration or init script
-- already have DECIMAL(10, 6).
--
-- Usage:
--   poetry -C backend run python scripts/apply_sql_migrations.py
--
-- Note: This is safe to run even if the column is already DECIMAL(10, 6).
-- MySQL will simply change the column to the same type without data loss.

ALTER TABLE messages MODIFY COLUMN cost_usd DECIMAL(10, 6) NULL COMMENT 'Cost in USD for this message';
