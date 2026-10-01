#!/usr/bin/env bash
set -e

# ==============================================================================
# TableKeeper Stage 1: One-Click Environment Setup & Launcher
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

echo "=================================================================="
echo "  🍽️  TABLEKEEPER: ONE-CLICK LAUNCHER (ISOLATED ENVIRONMENT)     "
echo "=================================================================="

# 1. Detect environment manager (prefer uv if executable, fallback to python3 venv)
USE_UV=0
if command -v uv &> /dev/null && uv --version &> /dev/null; then
    USE_UV=1
    echo "✓ Detected high-speed package manager: uv ($(uv --version))"
else
    echo "ℹ Using standard Python 3 venv for environment isolation."
fi

# 2. Verify or create isolated virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️  Creating dedicated isolated virtual environment in '$VENV_DIR'..."
    if [ $USE_UV -eq 1 ]; then
        uv venv "$VENV_DIR" --python 3.11 2>/dev/null || uv venv "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
    echo "✓ Virtual environment created successfully."
    NEEDS_INSTALL=1
else
    echo "✓ Found existing isolated environment in '$VENV_DIR'."
    NEEDS_INSTALL=0
fi

# 3. Activate the virtual environment
source "$VENV_DIR/bin/activate"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

echo "✓ Active Python runtime: $($PYTHON_BIN --version) [$PYTHON_BIN]"

# 4. Check & Install dependencies into isolated .venv
STAMP_FILE="$VENV_DIR/.requirements.stamp"
if [ ! -f "$STAMP_FILE" ] || [ requirements.txt -nt "$STAMP_FILE" ]; then
    echo "📦 Synchronizing dependencies into isolated environment..."
    if [ $USE_UV -eq 1 ]; then
        uv pip install -r requirements.txt
    else
        "$PIP_BIN" install --upgrade pip --quiet
        "$PIP_BIN" install -r requirements.txt --quiet
    fi
    cp requirements.txt "$STAMP_FILE"
    echo "✓ All dependencies installed into isolated .venv (zero global pollution)."
else
    echo "✓ Dependencies are up to date."
fi

# 5. Launch the service
echo ""
echo "=================================================================="
echo "  🚀 Starting TableKeeper Service on http://localhost:$PORT       "
echo "  Press Ctrl+C to stop the server                                 "
echo "=================================================================="
echo ""

# Try opening the browser automatically on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 1 && open "http://localhost:$PORT") &
fi

exec "$VENV_DIR/bin/uvicorn" src.main:app --host "$HOST" --port "$PORT" --reload
