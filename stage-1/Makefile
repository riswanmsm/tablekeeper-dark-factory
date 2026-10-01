.PHONY: help setup run test test-offline docker-build docker-run clean

# Auto-detect best stable Python interpreter (< 3.14 to ensure pre-built wheels exist for PyO3/pydantic)
PYTHON_STABLE := $(shell for py in python3.12 python3.13 python3.11 python3.10 python3; do \
	if command -v $$py > /dev/null 2>&1; then \
		ver=$$($$py -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null); \
		major=$$(echo $$ver | cut -d. -f1); \
		minor=$$(echo $$ver | cut -d. -f2); \
		if [ "$$major" = "3" ] && [ "$$minor" -lt 14 ]; then \
			echo $$py; \
			break; \
		fi; \
	fi; \
done)
PYTHON_STABLE := $(if $(PYTHON_STABLE),$(PYTHON_STABLE),python3)

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest
PORT ?= 8080

# Forward compatibility flag in case a native build is attempted
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY = 1

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
	@echo "⚙️ Creating isolated virtual environment using $(PYTHON_STABLE)..."
	@$(PYTHON_STABLE) -m venv $(VENV)
	@echo "✓ Virtual environment created ($$($(PYTHON) --version))."

setup: $(VENV)
	@echo "📦 Installing dependencies into isolated environment..."
	@$(PIP) install --upgrade pip --quiet
	@$(PIP) install -r requirements.txt
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
