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

# Enable PyO3 stable ABI forward-compatibility as a safeguard
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

echo "=================================================================="
echo "  🍽️  TABLEKEEPER: ONE-CLICK LAUNCHER (ISOLATED ENVIRONMENT)     "
echo "=================================================================="

# 1. Detect best stable Python interpreter (< 3.14 to ensure pre-built wheels exist)
CHOSEN_PYTHON=""
for py in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$py" &> /dev/null; then
        VER=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" = "3" ] && [ "$MINOR" -lt 14 ]; then
            CHOSEN_PYTHON="$py"
            break
        fi
    fi
done

CHOSEN_PYTHON="${CHOSEN_PYTHON:-python3}"
echo "✓ Selected stable Python interpreter: $CHOSEN_PYTHON ($($CHOSEN_PYTHON --version 2>&1))"

# 2. Verify or create isolated virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️  Creating dedicated isolated virtual environment in '$VENV_DIR'..."
    "$CHOSEN_PYTHON" -m venv "$VENV_DIR"
    echo "✓ Virtual environment created successfully."
    NEEDS_INSTALL=1
else
    # Check if existing venv is using Python >= 3.14
    EXISTING_VER=$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
    EXISTING_MINOR=$(echo "$EXISTING_VER" | cut -d. -f2)
    if [ "$EXISTING_MINOR" -ge 14 ]; then
        echo "⚠️  Existing .venv is using Python $EXISTING_VER (which has no binary wheels for PyO3/pydantic)."
        echo "🔄 Recreating .venv with stable $CHOSEN_PYTHON..."
        rm -rf "$VENV_DIR"
        "$CHOSEN_PYTHON" -m venv "$VENV_DIR"
        echo "✓ Virtual environment recreated."
        NEEDS_INSTALL=1
    else
        echo "✓ Found existing isolated environment in '$VENV_DIR' ($($VENV_DIR/bin/python --version))."
        NEEDS_INSTALL=0
    fi
fi

# 3. Locate virtual environment binaries
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# 4. Check & Install dependencies into isolated .venv
STAMP_FILE="$VENV_DIR/.requirements.stamp"
if [ $NEEDS_INSTALL -eq 1 ] || [ ! -f "$STAMP_FILE" ] || [ requirements.txt -nt "$STAMP_FILE" ]; then
    echo "📦 Synchronizing dependencies into isolated environment..."
    "$PIP_BIN" install --upgrade pip --quiet
    "$PIP_BIN" install -r requirements.txt
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
