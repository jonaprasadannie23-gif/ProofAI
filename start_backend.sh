#!/usr/bin/env zsh
# start_backend.sh — create venv, install deps, and launch the FastAPI server.
# Run from the ProofAI/ directory:  zsh start_backend.sh

set -e

SCRIPT_DIR="${0:A:h}"        # absolute path to the directory containing this script
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$SCRIPT_DIR/.venv_backend"

# ── 1. Locate Python 3.13 ──────────────────────────────────────────────────
PYTHON=$(command -v python3.13 2>/dev/null || command -v python3 2>/dev/null)
if [[ -z "$PYTHON" ]]; then
  echo "ERROR: python3 not found. Install Python 3.13 first." >&2
  exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print('%d.%d' % sys.version_info[:2])")
echo "Using Python $PYVER at $PYTHON"

# ── 2. Create virtual environment ─────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment at $VENV_DIR …"
  "$PYTHON" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ── 3. Install / sync dependencies ────────────────────────────────────────
echo "Installing dependencies …"
pip install --upgrade pip --quiet
pip install -r "$BACKEND_DIR/requirements.txt"

# ── 4. Bootstrap .env if missing ──────────────────────────────────────────
if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  echo "No .env found — copying from .env.example"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "⚠  Set GEMINI_API_KEY in backend/.env before using the /analyze endpoint."
fi

# ── 5. Start the server ───────────────────────────────────────────────────
echo ""
echo "Starting FastAPI on http://127.0.0.1:8000 …"
echo "  Swagger UI : http://127.0.0.1:8000/docs"
echo "  Health     : http://127.0.0.1:8000/health"
echo ""
cd "$BACKEND_DIR"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
