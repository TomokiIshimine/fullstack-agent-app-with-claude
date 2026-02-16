"""Seed development test users.

Standalone CLI script executed by docker-compose command before Flask startup.
NOT imported by main.py — only runs via docker-compose entrypoint.

Double guard:
  1. FLASK_ENV must be "development"
  2. SEED_TEST_USERS must be "true"

Behavior:
  - Creates test user from TEST_USER_EMAIL / TEST_USER_PASSWORD env vars
  - Skips if user already exists (idempotent)
  - Always exits with code 0 (never blocks Flask startup)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def seed_test_users() -> None:
    """Create test users for development environment."""
    # Guard 1: FLASK_ENV must be "development"
    flask_env = os.getenv("FLASK_ENV", "")
    if flask_env != "development":
        print(f"[seed_dev_users] Skipping: FLASK_ENV={flask_env!r} (requires 'development')")
        return

    # Guard 2: SEED_TEST_USERS must be "true"
    seed_enabled = os.getenv("SEED_TEST_USERS", "false").lower()
    if seed_enabled != "true":
        print(f"[seed_dev_users] Skipping: SEED_TEST_USERS={seed_enabled!r} (requires 'true')")
        return

    email = os.getenv("TEST_USER_EMAIL", "testuser@example.com")
    password = os.getenv("TEST_USER_PASSWORD", "Test123!")

    from sqlalchemy.orm import Session  # noqa: E402

    from app.config import Config  # noqa: E402
    from app.database import get_engine, init_engine  # noqa: E402
    from app.models.user import User  # noqa: E402
    from app.utils.password import hash_password  # noqa: E402

    print(f"[seed_dev_users] Seeding test user: {email}")

    init_engine(Config.SQLALCHEMY_DATABASE_URI)
    engine = get_engine()

    with Session(engine) as session:
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            print(f"[seed_dev_users] User {email} already exists (id={existing.id}). Skipping.")
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
            role="user",
            name="Test User",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"[seed_dev_users] Created test user: {email} (id={user.id})")


if __name__ == "__main__":
    try:
        seed_test_users()
    except Exception as e:
        # Never block Flask startup — log error and exit cleanly
        print(f"[seed_dev_users] Error (non-fatal): {e}", file=sys.stderr)
    sys.exit(0)
