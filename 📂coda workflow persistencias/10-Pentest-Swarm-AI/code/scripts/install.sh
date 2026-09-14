#!/bin/sh
# Pentest Swarm AI — one-line installer.
#
#   curl -fsSL https://raw.githubusercontent.com/Armur-Ai/Pentest-Swarm-AI/main/scripts/install.sh | sh
#
# Downloads the right prebuilt binary for your OS/arch from the latest GitHub
# release and installs it onto your PATH. Override the version with
# PENTESTSWARM_VERSION=v0.1.0, or the install dir with PENTESTSWARM_BIN_DIR.
set -e

REPO="Armur-Ai/Pentest-Swarm-AI"
BIN="pentestswarm"

say()  { printf '  %s\n' "$1"; }
die()  { printf '  error: %s\n' "$1" >&2; exit 1; }

# --- detect platform (matches the GoReleaser artifact names) ---
os=$(uname -s | tr '[:upper:]' '[:lower:]')
case "$os" in
  linux|darwin) ;;
  *) die "unsupported OS '$os' — on Windows, grab the .exe from the Releases page or use scoop." ;;
esac
arch=$(uname -m)
case "$arch" in
  x86_64|amd64)   arch=amd64 ;;
  arm64|aarch64)  arch=arm64 ;;
  *) die "unsupported architecture '$arch'." ;;
esac
asset="pentestswarm-${os}-${arch}"

# --- resolve the version to install ---
version="${PENTESTSWARM_VERSION:-}"
if [ -z "$version" ]; then
  version=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
    | grep '"tag_name"' | head -1 | cut -d'"' -f4)
fi
[ -n "$version" ] || die "could not resolve the latest release (set PENTESTSWARM_VERSION to pin one)."

url="https://github.com/${REPO}/releases/download/${version}/${asset}"
say "Installing ${BIN} ${version} (${os}/${arch})…"

tmp=$(mktemp)
curl -fsSL "$url" -o "$tmp" || die "download failed: ${url}"
chmod +x "$tmp"

# --- pick an install dir on PATH; use sudo only if needed ---
dir="${PENTESTSWARM_BIN_DIR:-/usr/local/bin}"
sudo=""
if [ ! -d "$dir" ] || [ ! -w "$dir" ]; then
  if command -v sudo >/dev/null 2>&1 && [ "$dir" = "/usr/local/bin" ]; then
    sudo="sudo"
  else
    dir="${HOME}/.local/bin"
    mkdir -p "$dir"
  fi
fi
$sudo mv "$tmp" "${dir}/${BIN}"
say "Installed → ${dir}/${BIN}"

# --- PATH hint ---
case ":$PATH:" in
  *":$dir:"*) ;;
  *) say ""; say "Add it to your PATH (then restart your shell):"; say "  export PATH=\"${dir}:\$PATH\"" ;;
esac

say ""
say "Get started:  ${BIN} run       (interactive)"
say "Check setup:  ${BIN} doctor"
