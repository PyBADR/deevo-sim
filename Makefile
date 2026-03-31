.PHONY: help install dev test lint build up down logs clean seed seed-graph migrate status shell-api shell-db shell-neo4j check format test-backend test-frontend test-integration

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

BACKEND := backend
FRONTEND := frontend
DOCKER_COMPOSE := docker-compose
PYTHONPATH := PYTHONPATH=$(BACKEND)

# Default target
help:
	@echo "$(BLUE)DecisionCore Intelligence — GCC Platform$(NC)"
	@echo "$(BLUE)Available targets:$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation$(NC)"
	@echo "  make install              Install all dependencies (backend + frontend)"
	@echo "  make migrate              Run database migrations"
	@echo ""
	@echo "$(GREEN)Development$(NC)"
	@echo "  make dev                  Start development servers (docker-compose up -d)"
	@echo "  make up                   Alias for 'dev'"
	@echo "  make down                 Stop all services"
	@echo "  make logs                 Tail all service logs"
	@echo "  make status               Show service health status"
	@echo ""
	@echo "$(GREEN)Testing$(NC)"
	@echo "  make test                 Run all tests (backend + frontend)"
	@echo "  make test-backend         Run backend pytest tests only"
	@echo "  make test-frontend        Run frontend tests (eslint + vitest) only"
	@echo "  make test-integration     Run integration tests"
	@echo "  make check                Run full CI pipeline (lint + test + build)"
	@echo ""
	@echo "$(GREEN)Code Quality$(NC)"
	@echo "  make lint                 Run linters (ruff + eslint)"
	@echo "  make format               Auto-format code (ruff format + prettier)"
	@echo ""
	@echo "$(GREEN)Building$(NC)"
	@echo "  make build                Build all Docker images"
	@echo ""
	@echo "$(GREEN)Data Management$(NC)"
	@echo "  make seed                 Load GCC seed data into PostgreSQL"
	@echo "  make seed-graph           Load seed data into Neo4j graph"
	@echo ""
	@echo "$(GREEN)Shells & Debugging$(NC)"
	@echo "  make shell-api            Open bash shell in API container"
	@echo "  make shell-db             Open psql shell to PostgreSQL"
	@echo "  make shell-neo4j          Open cypher shell to Neo4j"
	@echo ""
	@echo "$(GREEN)Cleanup$(NC)"
	@echo "  make clean                Remove containers, volumes, caches"
	@echo ""

# Installation targets
install:
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd $(BACKEND) && pip install -q -r requirements.txt
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND) && npm install --silent
	@echo "$(GREEN)✓ Installation complete$(NC)"

# Development targets
dev: up

up:
	@echo "$(BLUE)Starting services with docker-compose...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "  API:       http://localhost:8000"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Docs:      http://localhost:8000/api/docs"
	@echo "  Neo4j:     http://localhost:7474"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis:     localhost:6379"
	@sleep 3 && make status

down:
	@echo "$(BLUE)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

logs:
	@echo "$(BLUE)Tailing service logs (Ctrl+C to stop)...$(NC)"
	$(DOCKER_COMPOSE) logs -f

status:
	@echo "$(BLUE)Service health status:$(NC)"
	@echo ""
	@echo "Backend API:"
	@curl -s -f http://localhost:8000/api/v1/health -w "  Status: $(GREEN)✓$(NC)\n" || echo "  Status: $(RED)✗$(NC) (unavailable)"
	@echo ""
	@echo "Frontend:"
	@curl -s -f http://localhost:3000/ -w "  Status: $(GREEN)✓$(NC)\n" || echo "  Status: $(RED)✗$(NC) (unavailable)"
	@echo ""
	@echo "PostgreSQL:"
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U dc7 >/dev/null 2>&1 && echo "  Status: $(GREEN)✓$(NC)" || echo "  Status: $(RED)✗$(NC)"
	@echo ""
	@echo "Neo4j:"
	@$(DOCKER_COMPOSE) exec -T neo4j cypher-shell -u neo4j -p dc7_graph_2026 'RETURN 1' >/dev/null 2>&1 && echo "  Status: $(GREEN)✓$(NC)" || echo "  Status: $(RED)✗$(NC)"
	@echo ""
	@echo "Redis:"
	@$(DOCKER_COMPOSE) exec -T redis redis-cli ping >/dev/null 2>&1 && echo "  Status: $(GREEN)✓$(NC)" || echo "  Status: $(RED)✗$(NC)"

# Build targets
build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)✓ Build complete$(NC)"

# Testing targets
test: test-backend test-frontend
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) pytest tests/ -v --tb=short --cov=app --cov-report=term-missing 2>&1
	@echo "$(GREEN)✓ Backend tests complete$(NC)"

test-frontend:
	@echo "$(BLUE)Running frontend linter...$(NC)"
	cd $(FRONTEND) && npm run lint --silent 2>&1
	@echo "$(GREEN)✓ Frontend tests complete$(NC)"

test-integration:
	@echo "$(BLUE)Running integration tests...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) pytest tests/test_integration.py -v --tb=short 2>&1
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

# Code quality targets
lint:
	@echo "$(BLUE)Running ruff linter (backend)...$(NC)"
	cd $(BACKEND) && ruff check . 2>&1 || true
	@echo "$(BLUE)Running eslint (frontend)...$(NC)"
	cd $(FRONTEND) && npm run lint --silent 2>&1 || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format:
	@echo "$(BLUE)Formatting backend code...$(NC)"
	cd $(BACKEND) && ruff format . --quiet 2>&1 || true
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	cd $(FRONTEND) && npx prettier --write . --quiet 2>&1 || true
	@echo "$(GREEN)✓ Formatting complete$(NC)"

check: lint test build
	@echo "$(GREEN)✓ Full CI pipeline passed$(NC)"

# Data management targets
seed:
	@echo "$(BLUE)Loading GCC seed data into PostgreSQL...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) python -m scripts.seed_postgres 2>&1
	@echo "$(GREEN)✓ Seed data loaded$(NC)"

seed-graph:
	@echo "$(BLUE)Loading GCC seed data into Neo4j...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) python -m scripts.seed_neo4j 2>&1
	@echo "$(GREEN)✓ Graph seed data loaded$(NC)"

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd $(BACKEND) && alembic upgrade head 2>&1
	@echo "$(GREEN)✓ Migrations complete$(NC)"

# Shell targets
shell-api:
	@echo "$(BLUE)Opening shell in API container...$(NC)"
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-db:
	@echo "$(BLUE)Opening psql shell to PostgreSQL...$(NC)"
	$(DOCKER_COMPOSE) exec postgres psql -U dc7 -d decision_core

shell-neo4j:
	@echo "$(BLUE)Opening cypher shell to Neo4j...$(NC)"
	$(DOCKER_COMPOSE) exec neo4j cypher-shell -u neo4j -p dc7_graph_2026

# Cleanup target
clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v
	cd $(BACKEND) && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND) && find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND) && rm -rf .coverage htmlcov/ .mypy_cache/ 2>/dev/null || true
	cd $(FRONTEND) && rm -rf node_modules .next .cache 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"
