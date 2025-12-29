-- Migration: Add tool_calls table for agent functionality
-- Date: 2025-12-27
-- Description: Adds table to track tool calls made by AI agent

CREATE TABLE IF NOT EXISTS tool_calls (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  message_id BIGINT UNSIGNED NOT NULL,
  tool_call_id VARCHAR(64) NOT NULL,
  tool_name VARCHAR(100) NOT NULL,
  input JSON NOT NULL,
  output TEXT,
  error TEXT,
  status ENUM('pending', 'success', 'error') NOT NULL DEFAULT 'pending',
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE INDEX idx_tool_calls_message_id ON tool_calls (message_id);
CREATE INDEX idx_tool_calls_tool_call_id ON tool_calls (tool_call_id);
