.PHONY: help setup run test test-offline docker-build docker-run clean

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest
PORT ?= 8080

help:
	@echo "=================================================================="
	@echo "  🍽️  TABLEKEEPER (STAGE 1) MAKEFILE TARGETS                      "
	@echo "=================================================================="
	@echo "  make setup         - Create isolated .venv & install dependencies"
	@echo "  make run           - Launch service locally on port $(PORT)"
	@echo "  make test          - Run concurrency & contract test suite in .venv"
	@echo "  make test-offline  - Verify clean Docker container with --network none"
	@echo "  make docker-build  - Build production Docker image"
	@echo "  make docker-run    - Run container on port $(PORT)"
	@echo "  make clean         - Remove .venv, caches, and test databases"
	@echo "=================================================================="

$(VENV):
	@echo "⚙️ Creating isolated virtual environment in $(VENV)..."
	@python3 -m venv $(VENV)
	@echo "✓ Virtual environment created."

setup: $(VENV)
	@echo "📦 Installing dependencies into isolated environment..."
	@if command -v uv > /dev/null 2>&1; then \
		uv pip install -r requirements.txt; \
	else \
		$(PIP) install --upgrade pip --quiet && $(PIP) install -r requirements.txt --quiet; \
	fi
	@echo "✓ Environment ready at $(VENV)"

run: setup
	@echo "🚀 Starting TableKeeper on http://localhost:$(PORT)"
	@$(UVICORN) src.main:app --host 0.0.0.0 --port $(PORT) --reload

test: setup
	@echo "🧪 Running Concurrency & Contract Test Suite..."
	@$(PYTEST) tests/test_concurrency.py -v

test-offline:
	@chmod +x run_offline_test.sh
	@./run_offline_test.sh

docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t tablekeeper-stage1:latest .

docker-run:
	@echo "🐳 Running container on http://localhost:$(PORT)..."
	@docker run --rm -it -p $(PORT):8080 tablekeeper-stage1:latest

clean:
	@echo "🧹 Cleaning up isolated environment and temporary artifacts..."
	@rm -rf $(VENV) .pytest_cache data/ *.sqlite3
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete."
