# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

AI chat application powered by Claude API. Users can have real-time streaming conversations with an AI assistant, with conversation history management and user authentication.

## Repository Overview

Full-stack monorepo: React + TypeScript frontend, Flask + SQLAlchemy backend, MySQL database. Docker Compose for local development.

**Detailed guides:**
- [backend/CLAUDE.md](backend/CLAUDE.md) - Backend architecture, patterns, logging
- [frontend/CLAUDE.md](frontend/CLAUDE.md) - Frontend architecture, UI components, patterns
- [docs/](docs/) - Comprehensive documentation (start with `00_development.md`)
- [docs/10_troubleshooting.md](docs/10_troubleshooting.md) - Common issues and solutions

## Architecture

### Clean Architecture

Dependencies flow inward: Routes → Services → Repositories → Models. Keep infrastructure code at the edges.

### Data Flow

```
Frontend (React)                    Backend (Flask)
     │                                   │
     ├─ pages/         ──HTTP/JSON──►   routes/        ─► Blueprints, request validation
     ├─ components/                      services/      ─► Business logic
     ├─ hooks/                           repositories/  ─► Data access (SQLAlchemy)
     ├─ contexts/                        models/        ─► ORM models
     └─ lib/api/                         schemas/       ─► Pydantic validation
```

### Key Technologies

| Layer | Frontend | Backend |
|-------|----------|---------|
| Framework | React 18 + Vite | Flask 3.x |
| Language | TypeScript | Python 3.12 |
| Styling | Tailwind CSS | - |
| State | React Context | - |
| Validation | - | Pydantic v2 |
| ORM | - | SQLAlchemy 2.x |
| Database | - | MySQL 8.0 |
| Auth | JWT (httpOnly Cookie) | JWT (httpOnly Cookie) |

## Commands

Run `make help` to see all available commands.

### Development
```bash
make install              # Install all dependencies
make install-frontend     # Install frontend dependencies only
make install-backend      # Install backend dependencies only
make up                   # Start all services (frontend :5174, backend :5000, MySQL, Redis)
make down                 # Stop all services
make doctor               # Check development environment (Node, Python, Docker, etc.)
make health               # Check if all services are running and healthy
```

### Testing
```bash
make test                 # Run all tests with coverage
make test-frontend        # Run frontend tests only
make test-backend         # Run backend tests only
make test-fast            # Run tests without coverage (faster)
make test-coverage        # Run tests and generate HTML coverage report

# Individual tests
pnpm --dir frontend run test src/lib/api/auth.test.ts
poetry -C backend run pytest backend/tests/routes/test_auth_routes.py::test_login_success
```

### Code Quality
```bash
make lint                 # Run all linters (frontend + backend)
make lint-frontend        # Run frontend linters (ESLint, TypeScript)
make lint-backend         # Run backend linters (flake8, mypy)
make format               # Format all code
make format-frontend      # Format frontend code (Prettier)
make format-backend       # Format backend code (Black, isort)
make format-check         # Check formatting without changes
```

### Database
```bash
make db-init              # Create/recreate all tables
make db-create-user EMAIL=user@example.com PASSWORD=password123
make db-reset             # ⚠️ Drop and recreate database
```

### Pre-commit
```bash
make pre-commit-install   # Install hooks (run once after clone)
make pre-commit-run       # Run pre-commit on all files
make pre-commit-update    # Update pre-commit hooks
```

### CI
```bash
make ci                   # Run lint, format-check, and test (full CI pipeline)
```

## Browser Testing with Playwright MCP

Use **mcp__playwright** tools for UI verification:

1. `make up` to start the application
2. `mcp__playwright__browser_navigate` to `http://localhost:5174`
3. `mcp__playwright__browser_snapshot` to capture page state
4. `mcp__playwright__browser_click`, `mcp__playwright__browser_type` to interact
5. `mcp__playwright__browser_take_screenshot` to verify

**Note:** Always use `Test123!` as the password when testing.

## Key Patterns

### Backend: Adding a Feature

1. **Model** (`app/models/`) - SQLAlchemy ORM with `Mapped` types
2. **Schema** (`app/schemas/`) - Pydantic v2 for request/response validation
3. **Repository** (`app/repositories/`) - Data access layer
4. **Service** (`app/services/`) - Business logic
5. **Route** (`app/routes/`) - Flask Blueprint, `@require_auth` decorator
6. **Tests** (`backend/tests/`) - pytest with SQLite in-memory

### Frontend: Adding a Feature

1. **Types** (`src/types/`) - TypeScript interfaces
2. **API** (`src/lib/api/`) - Fetch functions with `credentials: 'include'`
3. **Hook** (`src/hooks/`) - Custom hook for state management
4. **Components** (`src/components/`) - React components using `@/components/ui`
5. **Page** (`src/pages/`) - Page component with routing
6. **Tests** (`src/**/*.test.tsx`) - Vitest + Testing Library

### API Conventions

- All routes under `/api` prefix
- JSON request/response bodies
- JWT auth via httpOnly cookies (automatic with `credentials: 'include'`)
- Rate limiting via Flask-Limiter + Redis

### Commit Messages

[Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <subject>`

Examples: `feat(chat): add streaming support`, `fix(auth): handle expired tokens`

## Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=mysql+pymysql://user:password@db:3306/app_db
JWT_SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-...  # For AI chat feature
LLM_PROVIDER=anthropic        # LLM provider (default: anthropic)
LLM_MODEL=claude-sonnet-4-5-20250929  # Claude model to use
```

### Frontend (`frontend/.env`)
```env
VITE_API_PROXY=http://localhost:5000
```

## Docker Services

- `frontend` - Node 20, port 5174
- `backend` - Python 3.12, port 5000
- `db` - MySQL 8.0, port 3306
- `redis` - Redis 7, port 6379 (rate limiting)
