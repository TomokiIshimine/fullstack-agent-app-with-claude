-- Migration: Create user_settings table
-- Date: 2026-02-16
-- Description: Adds user_settings table for per-user preferences (send shortcut key setting)
--
-- Usage:
--   poetry -C backend run python scripts/apply_sql_migrations.py

CREATE TABLE IF NOT EXISTS user_settings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL UNIQUE,
  send_shortcut ENUM('enter', 'ctrl_enter') NOT NULL DEFAULT 'enter',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
