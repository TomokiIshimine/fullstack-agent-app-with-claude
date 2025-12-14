-- Migration: Create conversations and messages tables
-- Date: 2025-12-14
-- Description: Adds tables for AI chat functionality
--
-- IMPORTANT: This migration is for EXISTING databases only.
-- New installations should use infra/mysql/init/001_init.sql instead.
--
-- Usage:
--   poetry -C backend run python scripts/apply_sql_migrations.py

-- Step 1: Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid VARCHAR(36) NOT NULL UNIQUE,
  user_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Step 2: Create indexes for conversations
CREATE INDEX idx_conversations_user_id ON conversations (user_id);
CREATE INDEX idx_conversations_updated_at ON conversations (updated_at);

-- Step 3: Create messages table
CREATE TABLE IF NOT EXISTS messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  conversation_id BIGINT UNSIGNED NOT NULL,
  role ENUM('user', 'assistant') NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Step 4: Create indexes for messages
CREATE INDEX idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX idx_messages_created_at ON messages (created_at);
