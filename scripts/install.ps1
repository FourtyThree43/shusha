# ==============================================================================
# Shusha 2 — Universal One-Liner Installer & Updater for Windows PowerShell
# Usage:
#   irm https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "=== Shusha 2 — Universal Download Platform Installer (Windows) ===" -ForegroundColor Cyan

# 1. Check for Astral uv toolchain
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Astral 'uv' package manager not found. Installing uv..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$HOME\.local\bin;$HOME\AppData\Local\bin;$env:Path"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Failed to locate 'uv' in PATH. Please restart your PowerShell and re-run." -ForegroundColor Red
    exit 1
}

Write-Host "✔ Astral uv toolchain ready." -ForegroundColor Green

# 2. Install / Upgrade Shusha Tool
$RepoUrl = "git+https://github.com/FourtyThree43/shusha.git"
Write-Host "Installing/Upgrading Shusha from $RepoUrl..." -ForegroundColor Cyan
uv tool install --force $RepoUrl

# 3. Check for reference execution engines (aria2c, yt-dlp)
Write-Host "`nChecking execution backends:" -ForegroundColor Cyan
if (Get-Command aria2c -ErrorAction SilentlyContinue) {
    Write-Host "✔ aria2c available." -ForegroundColor Green
} else {
    Write-Host "▲ aria2c not found. Install via winget ('winget install aria2.aria2') or scoop ('scoop install aria2')." -ForegroundColor Yellow
}

if (Get-Command yt-dlp -ErrorAction SilentlyContinue) {
    Write-Host "✔ yt-dlp available." -ForegroundColor Green
} else {
    Write-Host "▲ Installing yt-dlp via uv..." -ForegroundColor Yellow
    uv tool install yt-dlp
}

# 4. Register Browser Bridge
Write-Host "`nRegistering browser native messaging bridge:" -ForegroundColor Cyan
shusha install-host

Write-Host "`n✔ Shusha 2 successfully installed!" -ForegroundColor Green
Write-Host "Run the terminal interface:    shusha" -ForegroundColor White
Write-Host "Run the desktop GUI:           shusha --gui" -ForegroundColor White
Write-Host "Run system health check:       shusha doctor" -ForegroundColor White
