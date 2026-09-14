#!/bin/bash
# Build whisper.cpp's whisper-server for one arch and stage it where electron-builder's
# extraResources picks it up (build-staging/whisper/<arch>). The packaged app resolves it at
# resources/whisper/whisper-server (electron/voice/whisperService.js resolveBinary); the model
# stays a first-run download (ships +0MB, whisperService owns the fetch + progress UI).
# The brew binary can't be bundled: it links homebrew dylibs that don't exist on user machines.
set -euo pipefail

ARCH="${1:?usage: build-whisper.sh <arm64|x64>}"

WHISPER_VERSION="v1.7.6"
HERE="$(cd "$(dirname "$0")/.." && pwd)"   # electron/
OUT="$HERE/build-staging/whisper/$ARCH"
SRC="$HERE/build-staging/whisper-src"

# Idempotent across publish reruns: a staged binary from the same pinned version is reused.
if [[ -f "$OUT/whisper-server" && -f "$OUT/.version" && "$(cat "$OUT/.version")" == "$WHISPER_VERSION" ]]; then
    echo "[whisper] $ARCH already staged at $WHISPER_VERSION, skipping"
    exit 0
fi

if [[ ! -d "$SRC/.git" ]]; then
    git clone --depth 1 --branch "$WHISPER_VERSION" https://github.com/ggml-org/whisper.cpp "$SRC"
else
    CUR="$(git -C "$SRC" describe --tags --exact-match 2>/dev/null || echo none)"
    if [[ "$CUR" != "$WHISPER_VERSION" ]]; then
        git -C "$SRC" fetch --depth 1 origin tag "$WHISPER_VERSION"
        git -C "$SRC" checkout -f "$WHISPER_VERSION"
    fi
fi

case "$ARCH" in
    arm64) OSX_ARCH="arm64";  EXTRA=(-DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON) ;;
    # Intel slice: CPU + Accelerate only. Metal shaders target Apple Silicon, and GGML_NATIVE
    # would bake this arm64 build host's flags into a cross build.
    x64)   OSX_ARCH="x86_64"; EXTRA=(-DGGML_METAL=OFF -DGGML_NATIVE=OFF) ;;
    *) echo "unknown arch: $ARCH"; exit 1 ;;
esac

BUILD_DIR="$SRC/build-$ARCH"
echo "[whisper] building whisper-server $WHISPER_VERSION for $ARCH..."
cmake -S "$SRC" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES="$OSX_ARCH" \
    -DBUILD_SHARED_LIBS=OFF \
    -DWHISPER_BUILD_TESTS=OFF \
    "${EXTRA[@]}" > /dev/null
cmake --build "$BUILD_DIR" --target whisper-server -j "$(sysctl -n hw.ncpu)" > /dev/null

BIN="$BUILD_DIR/bin/whisper-server"
[[ -f "$BIN" ]] || { echo "[whisper] build produced no whisper-server"; exit 1; }

mkdir -p "$OUT"
cp "$BIN" "$OUT/whisper-server"
echo "$WHISPER_VERSION" > "$OUT/.version"
echo "[whisper] staged -> $OUT/whisper-server"
file "$OUT/whisper-server"
# A binary that links anything outside the OS is a launch crash on user machines; fail loud here.
if otool -L "$OUT/whisper-server" | grep -qE "/opt/homebrew|/usr/local"; then
    echo "[whisper] ERROR: binary links non-system libraries"; otool -L "$OUT/whisper-server"; exit 1
fi
