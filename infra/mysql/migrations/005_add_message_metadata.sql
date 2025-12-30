-- Migration: Add metadata columns to messages table
-- Date: 2025-12-30
-- Description: Adds token usage, model, response time, and cost tracking to messages
--
-- IMPORTANT: This migration is for EXISTING databases only.
-- New installations should use infra/mysql/init/001_init.sql instead.
--
-- Usage:
--   poetry -C backend run python scripts/apply_sql_migrations.py

-- Step 1: Add input_tokens column
ALTER TABLE messages ADD COLUMN input_tokens INT UNSIGNED NULL COMMENT 'Number of input tokens used';

-- Step 2: Add output_tokens column
ALTER TABLE messages ADD COLUMN output_tokens INT UNSIGNED NULL COMMENT 'Number of output tokens generated';

-- Step 3: Add model column
ALTER TABLE messages ADD COLUMN model VARCHAR(255) NULL COMMENT 'Model name used for generation';

-- Step 4: Add response_time_ms column
ALTER TABLE messages ADD COLUMN response_time_ms INT UNSIGNED NULL COMMENT 'Response time in milliseconds';

-- Step 5: Add cost_usd column
ALTER TABLE messages ADD COLUMN cost_usd FLOAT NULL COMMENT 'Cost in USD for this message';
