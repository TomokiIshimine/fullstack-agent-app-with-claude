.PHONY: install setup up down lint lint-frontend lint-backend format format-check test test-frontend test-backend test-fast test-cov test-parallel test-frontend-ci test-backend-ci security ci pre-commit-install pre-commit-run pre-commit-update db-init db-create-user db-reset doctor health

PNPM ?= pnpm --dir frontend
POETRY ?= poetry -C backend
COMPOSE ?= docker compose -f infra/docker-compose.yml --env-file infra/.env.development

# Suppress command echo and add quiet flags where appropriate
PNPM_QUIET = $(PNPM) --silent
POETRY_QUIET = $(POETRY) --quiet

install:
	@printf '📦 Installing frontend dependencies...\n'
	@CI=true $(PNPM_QUIET) install --config.allow-scripts=true
	@printf '📦 Installing backend dependencies...\n'
	@$(POETRY_QUIET) install
	@printf '✅ Dependencies installed\n'

setup: install
	@printf '✅ Environment setup complete. You can now run `make up` to start the stack.\n'

up:
	@printf '🚀 Starting services...\n'
	@$(COMPOSE) up -d --quiet-pull 2>/dev/null || $(COMPOSE) up -d
	@printf '✅ Services started (frontend :5174, backend :5000)\n'

down:
	@$(COMPOSE) down --remove-orphans 2>/dev/null
	@printf '✅ Services stopped\n'

lint:
	@printf '🔍 Linting frontend...\n'
	@$(PNPM_QUIET) run lint
	@$(PNPM) exec tsc --noEmit
	@printf '🔍 Linting backend...\n'
	@$(POETRY) run flake8 app tests --quiet || $(POETRY) run flake8 app tests
	@$(POETRY) run mypy app --no-error-summary 2>/dev/null || $(POETRY) run mypy app
	@printf '✅ Lint passed\n'

lint-frontend:
	@printf '🔍 Linting frontend...\n'
	@$(PNPM_QUIET) run lint
	@$(PNPM) exec tsc --noEmit
	@$(PNPM) exec prettier --check --log-level warn "src/**/*.{ts,tsx,js,jsx,json,css,scss,md,html,yaml,yml,cjs,mjs}"
	@printf '✅ Frontend lint passed\n'

lint-backend:
	@printf '🔍 Linting backend...\n'
	@$(POETRY) run flake8 app tests --quiet || $(POETRY) run flake8 app tests
	@$(POETRY) run mypy app --no-error-summary 2>/dev/null || $(POETRY) run mypy app
	@$(POETRY) run isort --check-only --quiet app tests
	@$(POETRY) run black --check --quiet app tests
	@printf '✅ Backend lint passed\n'

test:
	@printf '🧪 Running frontend tests...\n'
	@$(PNPM_QUIET) run test:coverage
	@printf '🧪 Running backend tests...\n'
	@$(POETRY) run pytest --cov=app --cov-report=term-missing --cov-report=html -q
	@printf '✅ All tests passed\n'

test-frontend:
	@printf '🧪 Running frontend tests...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@printf '✅ Frontend tests passed\n'

test-backend:
	@printf '🧪 Running backend tests...\n'
	@$(POETRY) run pytest --cov=app --cov-report=term-missing -q
	@printf '✅ Backend tests passed\n'

test-fast:
	@printf '🧪 Running tests (no coverage)...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@$(POETRY) run pytest --no-cov -q
	@printf '✅ All tests passed\n'

test-cov:
	@printf '🧪 Running tests with coverage...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@$(POETRY) run pytest --cov=app --cov-report=term-missing --cov-report=html -q
	@printf '\n✅ Coverage report generated in backend/htmlcov/index.html\n'

test-parallel:
	@printf '🧪 Running tests in parallel...\n'
	@$(PNPM_QUIET) run test -- --runInBand
	@$(POETRY) run pytest -n auto --cov=app --cov-report=term-missing -q
	@printf '✅ All tests passed\n'

test-frontend-ci:
	@$(PNPM_QUIET) run test:coverage

test-backend-ci:
	@$(POETRY) run pytest --cov=app --cov-report=term-missing --cov-report=html -q

format:
	@printf '✨ Formatting code...\n'
	@$(PNPM) exec prettier --ignore-unknown --write --log-level warn .
	@$(POETRY) run isort app tests --quiet
	@$(POETRY) run black app tests --quiet
	@printf '✅ Code formatted\n'

format-check:
	@printf '🔍 Checking format...\n'
	@$(PNPM) exec prettier --check --log-level warn "src/**/*.{ts,tsx,js,jsx,json,css,scss,md,html,yaml,yml,cjs,mjs}"
	@$(POETRY) run isort --check-only --quiet app tests
	@$(POETRY) run black --check --quiet app tests
	@printf '✅ Format check passed\n'

security:
	@printf '🔒 Running security audit...\n'
	@EXIT_CODE=0; \
	$(PNPM) audit --audit-level=moderate || EXIT_CODE=$$?; \
	$(POETRY_QUIET) check || EXIT_CODE=$$?; \
	$(POETRY) run pip-audit || EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then printf '✅ Security audit passed\n'; fi; \
	exit $$EXIT_CODE

ci: lint format-check test

pre-commit-install:
	@$(POETRY) run pre-commit install >/dev/null
	@$(POETRY) run pre-commit install --hook-type pre-push >/dev/null
	@printf '✅ Pre-commit and pre-push hooks installed\n'

pre-commit-run:
	@printf '🔍 Running pre-commit hooks...\n'
	@$(POETRY) run pre-commit run --all-files

pre-commit-update:
	@$(POETRY) run pre-commit autoupdate
	@printf '✅ Pre-commit hooks updated\n'

# Database management targets
db-init:
	@printf '🗄️  Creating database tables...\n'
	@$(POETRY) run python scripts/create_tables.py 2>/dev/null || $(POETRY) run python scripts/create_tables.py
	@printf '✅ Database tables created\n'

db-create-user:
	@if [ -z "$(EMAIL)" ] || [ -z "$(PASSWORD)" ]; then \
		printf 'Usage: make db-create-user EMAIL=user@example.com PASSWORD=password123\n'; \
		exit 1; \
	fi
	@$(POETRY) run python scripts/create_user.py $(EMAIL) $(PASSWORD)

db-reset:
	@printf '⚠️  This will reset the database. Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]
	@$(COMPOSE) down -v 2>/dev/null
	@printf '🗄️  Starting database...\n'
	@$(COMPOSE) up -d db --quiet-pull 2>/dev/null || $(COMPOSE) up -d db
	@printf 'Waiting for database to be ready...\n'
	@sleep 5
	@printf '✅ Database reset complete\n'

# Environment validation
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
		printf '✅ Environment is ready! Run `make install` to install dependencies.\n'; \
	else \
		printf '❌ Some issues found. Please fix them before continuing.\n'; \
		printf '   See docs/10_troubleshooting.md for help.\n'; \
		exit 1; \
	fi

# Service health check
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
		printf '❌ Some services are not healthy. Try `make down && make up`.\n'; \
		printf '   See docs/10_troubleshooting.md for help.\n'; \
	fi
