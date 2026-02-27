.PHONY: help install install-frontend install-backend setup up down \
        lint lint-frontend lint-backend \
        format format-frontend format-backend format-check format-check-frontend format-check-backend \
        test test-frontend test-backend test-fast test-coverage test-parallel \
        test-frontend-ci test-backend-ci lint-ci format-check-ci \
        security ci pre-commit-install pre-commit-run pre-commit-update \
        db-init db-create-user db-reset doctor health

# ==============================================================================
# Variables
# ==============================================================================
PNPM        ?= pnpm --dir frontend
POETRY      ?= poetry -C backend
COMPOSE     ?= docker compose -f infra/docker-compose.yml --env-file infra/.env.development

# Quiet mode variables (use consistently for suppressed output)
PNPM_QUIET   = $(PNPM) --silent
POETRY_QUIET = $(POETRY) --quiet

# Prettier file patterns
PRETTIER_PATTERNS = "src/**/*.{ts,tsx,js,jsx,json,css,scss,md,html,yaml,yml,cjs,mjs}"

# ==============================================================================
# Help
# ==============================================================================
help:
	@printf 'Usage: make [target]\n\n'
	@printf 'Development:\n'
	@printf '  install              Install all dependencies\n'
	@printf '  install-frontend     Install frontend dependencies only\n'
	@printf '  install-backend      Install backend dependencies only\n'
	@printf '  setup                Install dependencies and setup environment\n'
	@printf '  up                   Start all services\n'
	@printf '  down                 Stop all services\n'
	@printf '\n'
	@printf 'Code Quality:\n'
	@printf '  lint                 Run all linters (frontend + backend)\n'
	@printf '  lint-frontend        Run frontend linters (ESLint, TypeScript)\n'
	@printf '  lint-backend         Run backend linters (flake8, mypy)\n'
	@printf '  format               Format all code\n'
	@printf '  format-frontend      Format frontend code (Prettier)\n'
	@printf '  format-backend       Format backend code (Black, isort)\n'
	@printf '  format-check         Check formatting without changes\n'
	@printf '  format-check-frontend Check frontend formatting\n'
	@printf '  format-check-backend Check backend formatting\n'
	@printf '\n'
	@printf 'Testing:\n'
	@printf '  test                 Run all tests with coverage\n'
	@printf '  test-frontend        Run frontend tests\n'
	@printf '  test-backend         Run backend tests with coverage\n'
	@printf '  test-fast            Run all tests without coverage\n'
	@printf '  test-coverage        Run tests and generate coverage report\n'
	@printf '  test-parallel        Run tests in parallel\n'
	@printf '\n'
	@printf 'CI:\n'
	@printf '  ci                   Run lint, format-check, and test\n'
	@printf '  lint-ci              Run linters (CI mode, no progress output)\n'
	@printf '  format-check-ci      Check formatting (CI mode)\n'
	@printf '  test-frontend-ci     Run frontend tests (CI mode)\n'
	@printf '  test-backend-ci      Run backend tests (CI mode)\n'
	@printf '\n'
	@printf 'Security:\n'
	@printf '  security             Run security audit\n'
	@printf '\n'
	@printf 'Pre-commit:\n'
	@printf '  pre-commit-install   Install pre-commit hooks\n'
	@printf '  pre-commit-run       Run pre-commit on all files\n'
	@printf '  pre-commit-update    Update pre-commit hooks\n'
	@printf '\n'
	@printf 'Database:\n'
	@printf '  db-init              Create database tables\n'
	@printf '  db-create-user       Create a user (EMAIL=... PASSWORD=...)\n'
	@printf '  db-reset             Reset database (destructive)\n'
	@printf '\n'
	@printf 'Diagnostics:\n'
	@printf '  doctor               Check development environment\n'
	@printf '  health               Check service health\n'

# ==============================================================================
# Development
# ==============================================================================
install: install-frontend install-backend
	@printf '✅ All dependencies installed\n'

install-frontend:
	@printf '📦 Installing frontend dependencies...\n'
	@CI=true $(PNPM_QUIET) install --config.allow-scripts=true
	@printf '✅ Frontend dependencies installed\n'

install-backend:
	@printf '📦 Installing backend dependencies...\n'
	@$(POETRY_QUIET) install
	@printf '✅ Backend dependencies installed\n'

setup: install
	@printf '✅ Environment setup complete. Run "make up" to start the stack.\n'

up:
	@if [ ! -f infra/.env.development ]; then \
		printf '📋 Creating infra/.env.development from .env.example...\n'; \
		cp infra/.env.example infra/.env.development; \
		printf '   ✅ Created. Edit infra/.env.development to set ANTHROPIC_API_KEY.\n'; \
	fi
	@printf '🚀 Starting services...\n'
	@$(COMPOSE) up -d --quiet-pull 2>/dev/null || $(COMPOSE) up -d
	@printf '✅ Services started (frontend :5174, backend :5001)\n'

down:
	@printf '🛑 Stopping services...\n'
	@$(COMPOSE) down --remove-orphans 2>/dev/null || true
	@printf '✅ Services stopped\n'

# ==============================================================================
# Linting (static analysis, no formatting)
# ==============================================================================
lint: lint-frontend lint-backend
	@printf '✅ All lint checks passed\n'

lint-frontend:
	@printf '🔍 Linting frontend...\n'
	@$(PNPM_QUIET) run lint
	@$(PNPM_QUIET) exec tsc --noEmit
	@printf '✅ Frontend lint passed\n'

lint-backend:
	@printf '🔍 Linting backend...\n'
	@$(POETRY_QUIET) run flake8 app tests
	@$(POETRY_QUIET) run mypy app
	@printf '✅ Backend lint passed\n'

# ==============================================================================
# Formatting
# ==============================================================================
format: format-frontend format-backend
	@printf '✅ All code formatted\n'

format-frontend:
	@printf '✨ Formatting frontend...\n'
	@$(PNPM_QUIET) exec prettier --ignore-unknown --write --log-level warn .
	@printf '✅ Frontend formatted\n'

format-backend:
	@printf '✨ Formatting backend...\n'
	@$(POETRY_QUIET) run isort app tests
	@$(POETRY_QUIET) run black app tests
	@printf '✅ Backend formatted\n'

format-check: format-check-frontend format-check-backend
	@printf '✅ All format checks passed\n'

format-check-frontend:
	@printf '🔍 Checking frontend format...\n'
	@$(PNPM_QUIET) exec prettier --check --log-level warn $(PRETTIER_PATTERNS)
	@printf '✅ Frontend format check passed\n'

format-check-backend:
	@printf '🔍 Checking backend format...\n'
	@$(POETRY_QUIET) run isort --check-only app tests
	@$(POETRY_QUIET) run black --check app tests
	@printf '✅ Backend format check passed\n'

# ==============================================================================
# Testing
# ==============================================================================
test: test-frontend test-backend
	@printf '✅ All tests passed\n'

test-frontend:
	@printf '🧪 Running frontend tests...\n'
	@$(PNPM_QUIET) run test:coverage
	@printf '✅ Frontend tests passed\n'

test-backend:
	@printf '🧪 Running backend tests...\n'
	@$(POETRY_QUIET) run pytest --cov=app --cov-report=term-missing -q
	@printf '✅ Backend tests passed\n'

test-fast:
	@printf '🧪 Running tests (no coverage)...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@$(POETRY_QUIET) run pytest --no-cov -q
	@printf '✅ All tests passed\n'

test-coverage:
	@printf '🧪 Running tests with coverage...\n'
	@$(PNPM_QUIET) run test:coverage
	@$(POETRY_QUIET) run pytest --cov=app --cov-report=term-missing --cov-report=html -q
	@printf '✅ Coverage report generated in backend/htmlcov/index.html\n'

test-parallel:
	@printf '🧪 Running tests in parallel...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@$(POETRY_QUIET) run pytest -n auto --cov=app --cov-report=term-missing -q
	@printf '✅ All tests passed\n'

# ==============================================================================
# CI Targets (minimal output, for automated pipelines)
# ==============================================================================
ci: lint-ci format-check-ci test-frontend-ci test-backend-ci
	@printf '✅ CI pipeline passed\n'

lint-ci:
	@$(PNPM_QUIET) run lint
	@$(PNPM_QUIET) exec tsc --noEmit
	@$(POETRY_QUIET) run flake8 app tests
	@$(POETRY_QUIET) run mypy app

format-check-ci:
	@$(PNPM_QUIET) exec prettier --check --log-level error $(PRETTIER_PATTERNS)
	@$(POETRY_QUIET) run isort --check-only app tests
	@$(POETRY_QUIET) run black --check app tests

test-frontend-ci:
	@$(PNPM_QUIET) run test:coverage

test-backend-ci:
	@$(POETRY_QUIET) run pytest --cov=app --cov-report=term-missing --cov-report=html -q

# ==============================================================================
# Security
# ==============================================================================
security:
	@printf '🔒 Running security audit...\n'
	@EXIT_CODE=0; \
	$(PNPM_QUIET) audit --audit-level=moderate || EXIT_CODE=$$?; \
	$(POETRY_QUIET) check || EXIT_CODE=$$?; \
	$(POETRY_QUIET) run pip-audit || EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then printf '✅ Security audit passed\n'; fi; \
	exit $$EXIT_CODE

# ==============================================================================
# Pre-commit
# ==============================================================================
pre-commit-install:
	@printf '🔧 Installing pre-commit hooks...\n'
	@$(POETRY_QUIET) run pre-commit install
	@$(POETRY_QUIET) run pre-commit install --hook-type pre-push
	@printf '✅ Pre-commit and pre-push hooks installed\n'

pre-commit-run:
	@printf '🔍 Running pre-commit hooks...\n'
	@$(POETRY_QUIET) run pre-commit run --all-files
	@printf '✅ Pre-commit hooks passed\n'

pre-commit-update:
	@printf '🔄 Updating pre-commit hooks...\n'
	@$(POETRY_QUIET) run pre-commit autoupdate
	@printf '✅ Pre-commit hooks updated\n'

# ==============================================================================
# Database
# ==============================================================================
db-init:
	@printf '🗄️  Creating database tables...\n'
	@$(POETRY_QUIET) run python scripts/create_tables.py 2>/dev/null || $(POETRY_QUIET) run python scripts/create_tables.py
	@printf '✅ Database tables created\n'

db-create-user:
	@if [ -z "$(EMAIL)" ] || [ -z "$(PASSWORD)" ]; then \
		printf 'Usage: make db-create-user EMAIL=user@example.com PASSWORD=password123\n'; \
		exit 1; \
	fi
	@printf '👤 Creating user...\n'
	@$(POETRY_QUIET) run python scripts/create_user.py $(EMAIL) $(PASSWORD)
	@printf '✅ User created\n'

db-reset:
	@printf '⚠️  This will reset the database. Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]
	@printf '🗄️  Resetting database...\n'
	@$(COMPOSE) down -v 2>/dev/null || true
	@printf '🗄️  Starting database...\n'
	@$(COMPOSE) up -d db --quiet-pull 2>/dev/null || $(COMPOSE) up -d db
	@printf '⏳ Waiting for database to be ready...\n'
	@sleep 5
	@printf '✅ Database reset complete\n'

# ==============================================================================
# Diagnostics
# ==============================================================================
doctor:
	@printf '🩺 Checking development environment...\n\n'
	@ERRORS=0; \
	printf '  Node.js:   '; \
	if command -v node >/dev/null 2>&1; then \
		NODE_VER=$$(node --version | sed 's/v//'); \
		NODE_MAJOR=$$(echo $$NODE_VER | cut -d. -f1); \
		if [ $$NODE_MAJOR -ge 20 ]; then \
			printf '✅ v%s\n' "$$NODE_VER"; \
		else \
			printf '⚠️  v%s (v20+ recommended)\n' "$$NODE_VER"; \
		fi; \
	else \
		printf '❌ Not installed\n'; ERRORS=1; \
	fi; \
	printf '  Python:    '; \
	if command -v python3 >/dev/null 2>&1; then \
		PY_VER=$$(python3 --version | cut -d' ' -f2); \
		PY_MAJOR=$$(echo $$PY_VER | cut -d. -f1); \
		PY_MINOR=$$(echo $$PY_VER | cut -d. -f2); \
		if [ $$PY_MAJOR -ge 3 ] && [ $$PY_MINOR -ge 12 ]; then \
			printf '✅ v%s\n' "$$PY_VER"; \
		else \
			printf '⚠️  v%s (v3.12+ recommended)\n' "$$PY_VER"; \
		fi; \
	else \
		printf '❌ Not installed\n'; ERRORS=1; \
	fi; \
	printf '  Docker:    '; \
	if command -v docker >/dev/null 2>&1; then \
		if docker info >/dev/null 2>&1; then \
			DOCKER_VER=$$(docker --version | sed 's/Docker version \([^,]*\).*/\1/'); \
			printf '✅ v%s (running)\n' "$$DOCKER_VER"; \
		else \
			printf '⚠️  Installed but not running\n'; ERRORS=1; \
		fi; \
	else \
		printf '❌ Not installed\n'; ERRORS=1; \
	fi; \
	printf '  pnpm:      '; \
	if command -v pnpm >/dev/null 2>&1; then \
		PNPM_VER=$$(pnpm --version); \
		printf '✅ v%s\n' "$$PNPM_VER"; \
	else \
		printf '❌ Not installed (run: npm install -g pnpm)\n'; ERRORS=1; \
	fi; \
	printf '  Poetry:    '; \
	if command -v poetry >/dev/null 2>&1; then \
		POETRY_VER=$$(poetry --version | sed 's/Poetry (version \(.*\))/\1/'); \
		printf '✅ v%s\n' "$$POETRY_VER"; \
	else \
		printf '❌ Not installed (see: https://python-poetry.org/docs/#installation)\n'; ERRORS=1; \
	fi; \
	printf '\n  Environment files:\n'; \
	printf '    infra/.env.development: '; \
	if [ -f infra/.env.development ]; then \
		printf '✅ exists\n'; \
	else \
		printf '❌ missing (copy from infra/.env.example)\n'; ERRORS=1; \
	fi; \
	printf '    backend/.env:           '; \
	if [ -f backend/.env ]; then \
		printf '✅ exists\n'; \
	else \
		printf '⚠️  missing (optional, uses defaults)\n'; \
	fi; \
	printf '\n'; \
	if [ $$ERRORS -eq 0 ]; then \
		printf '✅ Environment is ready! Run "make install" to install dependencies.\n'; \
	else \
		printf '❌ Some issues found. Please fix them before continuing.\n'; \
		printf '   See docs/10_troubleshooting.md for help.\n'; \
		exit 1; \
	fi

health:
	@printf '🏥 Checking service health...\n\n'
	@ERRORS=0; \
	printf '  Docker services:\n'; \
	for SERVICE in frontend backend db redis; do \
		printf '    %s: ' "$$SERVICE"; \
		STATUS=$$($(COMPOSE) ps --format '{{.Status}}' $$SERVICE 2>/dev/null | head -1); \
		if echo "$$STATUS" | grep -q "Up"; then \
			if echo "$$STATUS" | grep -q "healthy"; then \
				printf '✅ Running (healthy)\n'; \
			elif echo "$$STATUS" | grep -q "starting"; then \
				printf '⏳ Starting...\n'; \
			else \
				printf '✅ Running\n'; \
			fi; \
		else \
			printf '❌ Not running\n'; ERRORS=1; \
		fi; \
	done; \
	printf '\n  HTTP endpoints:\n'; \
	printf '    Frontend (http://localhost:5174): '; \
	if curl -sf http://localhost:5174 >/dev/null 2>&1; then \
		printf '✅ Accessible\n'; \
	else \
		printf '❌ Not accessible\n'; ERRORS=1; \
	fi; \
	printf '    Backend  (http://localhost:5001/api/health): '; \
	HEALTH_RESP=$$(curl -sf http://localhost:5001/api/health 2>/dev/null); \
	if [ $$? -eq 0 ]; then \
		DB_STATUS=$$(echo "$$HEALTH_RESP" | grep -o '"database":"[^"]*"' | cut -d'"' -f4); \
		if [ "$$DB_STATUS" = "connected" ]; then \
			printf '✅ Healthy (DB connected)\n'; \
		else \
			printf '⚠️  Running (DB: %s)\n' "$$DB_STATUS"; \
		fi; \
	else \
		printf '❌ Not accessible\n'; ERRORS=1; \
	fi; \
	printf '\n'; \
	if [ $$ERRORS -eq 0 ]; then \
		printf '✅ All services are healthy!\n'; \
	else \
		printf '❌ Some services are not healthy. Try "make down && make up".\n'; \
		printf '   See docs/10_troubleshooting.md for help.\n'; \
	fi
