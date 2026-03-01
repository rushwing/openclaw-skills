#!/usr/bin/env bash
# setup_env.sh — Bootstrap the Python venv for everything_openclaw skills.
#
# Managed by: uv  (https://github.com/astral-sh/uv)
# Venv path:  ~/.tutor-venv  (existing skills expect this exact path)
# Target:     Raspberry Pi OS Bookworm / arm64, Python 3.11+
#
# Usage:
#   bash setup_env.sh
#
# Override venv path:
#   OPENCLAW_VENV=~/my-venv bash setup_env.sh
#
# After this script:
#   Python packages (edge-tts, requests, beautifulsoup4) will be ready.
#   System deps (manim, ffmpeg, LaTeX, CJK fonts) are advisory-only here;
#   see skills/tutor/DEPENDENCIES.md for full installation instructions.

set -euo pipefail

VENV_PATH="${OPENCLAW_VENV:-$HOME/.tutor-venv}"
PYTHON_VERSION="3.11"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✅  $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️   $*${NC}"; }
fail() { echo -e "${RED}  ❌  $*${NC}"; }
header() { echo -e "\n${BOLD}── $* ${NC}"; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════╗"
echo "║    everything_openclaw — environment setup       ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "  Venv   : $VENV_PATH"
echo "  Project: $PROJECT_ROOT"
echo "  Python : $PYTHON_VERSION"

# ── Step 1: uv ────────────────────────────────────────────────────────────────
header "Step 1: uv"
if ! command -v uv &>/dev/null; then
    echo "  uv not found — downloading installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # uv installs to ~/.local/bin on Linux
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &>/dev/null; then
        fail "uv still not found after install. Add ~/.local/bin to your PATH and re-run."
        exit 1
    fi
fi
ok "uv $(uv --version)"

# ── Step 2: Python venv ───────────────────────────────────────────────────────
header "Step 2: Python venv"
if [ -d "$VENV_PATH" ]; then
    echo "  Venv already exists — reusing."
    ok "$("$VENV_PATH/bin/python" --version)"
else
    echo "  Creating venv at $VENV_PATH ..."
    # uv will download Python $PYTHON_VERSION if not found on system
    uv venv "$VENV_PATH" --python "$PYTHON_VERSION"
    ok "Venv created ($("$VENV_PATH/bin/python" --version))"
fi
VENV_PYTHON="$VENV_PATH/bin/python"

# ── Step 3: Python packages ───────────────────────────────────────────────────
header "Step 3: Python packages (from pyproject.toml)"
# -e installs this project's declared [project.dependencies] into the venv.
# No Python source is installed (tool.setuptools.packages = []).
uv pip install --python "$VENV_PYTHON" -e "$PROJECT_ROOT" --quiet
ok "Packages installed"

# ── Step 4: Verify Python packages ───────────────────────────────────────────
header "Step 4: Verify Python packages"
PASS=true
verify_py() {
    local label="$1" module="$2"
    if "$VENV_PYTHON" -c "import $module" 2>/dev/null; then
        ok "$label"
    else
        fail "$label — import failed"
        PASS=false
    fi
}
verify_py "edge-tts       (TTS narration + english_partner)" "edge_tts"
verify_py "requests       (OJ problem fetch)"                "requests"
verify_py "beautifulsoup4 (OJ HTML parsing)"                 "bs4"

# ── Step 5: System deps (advisory) ───────────────────────────────────────────
header "Step 5: System deps (advisory — not managed by uv)"
check_bin() {
    local label="$1" cmd="$2" hint="$3"
    if command -v "$cmd" &>/dev/null; then
        ok "$label  →  $(command -v "$cmd")"
    else
        warn "$label — not found.  $hint"
    fi
}
check_bin "manim"  "manim"  "brew install manim"
check_bin "ffmpeg" "ffmpeg" "installed with manim via brew"
check_bin "latex"  "latex"  "sudo apt install texlive-latex-base texlive-latex-extra dvipng cm-super"
check_bin "dvipng" "dvipng" "sudo apt install dvipng"

if fc-list 2>/dev/null | grep -q "Noto Sans CJK SC"; then
    ok "Noto Sans CJK SC font"
else
    warn "Noto Sans CJK SC font — see skills/tutor/DEPENDENCIES.md §3"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
if $PASS; then
    echo -e "${GREEN}${BOLD}✅  Python venv ready.${NC}"
    echo ""
    echo "  Interpreter : $VENV_PYTHON"
    echo "  Quick check : $VENV_PYTHON -c \"import edge_tts, requests, bs4; print('OK')\""
    echo ""
    echo "  For system deps (manim, LaTeX, fonts), see:"
    echo "  skills/tutor/DEPENDENCIES.md"
else
    echo -e "${RED}${BOLD}❌  Setup incomplete — fix errors above and re-run.${NC}"
    exit 1
fi
