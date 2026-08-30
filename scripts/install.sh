#!/usr/bin/env bash
# ==============================================================================
# Shusha 2 — Universal One-Liner Installer & Updater for Linux & macOS
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.sh | bash
# ==============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}=== Shusha 2 — Universal Download Platform Installer ===${NC}"

# 1. Detect OS & Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"
echo -e "Detected Platform: ${BOLD}${OS} (${ARCH})${NC}"

# 2. Check for Astral uv toolchain
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${YELLOW}Astral 'uv' package manager not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}Failed to locate 'uv' in PATH. Please add ~/.local/bin to your PATH and re-run.${NC}"
    exit 1
fi
echo -e "${GREEN}✔ Astral uv toolchain ready: $(uv --version)${NC}"

# 3. Install / Upgrade Shusha Tool
REPO_URL="git+https://github.com/FourtyThree43/shusha.git"
echo -e "Installing/Upgrading Shusha from ${BOLD}${REPO_URL}${NC}..."
uv tool install --force --python 3.14 "${REPO_URL}" || uv tool install --force "${REPO_URL}"

# 4. Check for reference execution engines (aria2c, yt-dlp)
echo -e "\n${BOLD}Checking execution backends:${NC}"
if command -v aria2c >/dev/null 2>&1; then
    echo -e "${GREEN}✔ aria2c available: $(command -v aria2c)${NC}"
else
    echo -e "${YELLOW}▲ aria2c not found. Multi-source & BitTorrent acceleration recommended:${NC}"
    if [ "${OS}" = "Linux" ]; then
        echo -e "  Install via your package manager (e.g., 'sudo apt install aria2' or 'sudo pacman -S aria2')"
    elif [ "${OS}" = "Darwin" ]; then
        echo -e "  Install via Homebrew: 'brew install aria2'"
    fi
fi

if command -v yt-dlp >/dev/null 2>&1; then
    echo -e "${GREEN}✔ yt-dlp available: $(command -v yt-dlp)${NC}"
else
    echo -e "${YELLOW}▲ yt-dlp not found. Media stream extraction recommended:${NC}"
    echo -e "  Installing yt-dlp via uv tool..."
    uv tool install yt-dlp || true
fi

# 5. Register Browser Bridge & Desktop Launchers
echo -e "\n${BOLD}Configuring OS integrations:${NC}"
if command -v shusha >/dev/null 2>&1; then
    shusha install-host || true
    if [ "${OS}" = "Linux" ]; then
        shusha install-desktop || true
    fi
fi

echo -e "\n${BOLD}${GREEN}✔ Shusha 2 successfully installed!${NC}"
echo -e "Run the terminal interface:    ${BOLD}shusha${NC} (or ${BOLD}shusha tui${NC})"
echo -e "Run the desktop GUI:           ${BOLD}shusha --gui${NC} (or ${BOLD}shusha-gui${NC})"
echo -e "Run system health check:       ${BOLD}shusha doctor${NC}"
echo -e "View available CLI commands:   ${BOLD}shusha --help${NC}"
