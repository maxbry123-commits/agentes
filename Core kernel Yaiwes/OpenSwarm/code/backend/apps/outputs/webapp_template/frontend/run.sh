#!/bin/bash
# The comment above is shebang, DO NOT REMOVE
RUN_FRONTEND_ABSPATH="$(readlink -f "${BASH_SOURCE[0]}")"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # echo "In macOS server sed START"
    # echo "SERVER_ABSPATH: $SERVER_ABSPATH"
    sed -i '' 's/\r//g' "$RUN_FRONTEND_ABSPATH"
    # echo "In macOS server sed END"
else
    # echo "NOT in macOS server START"
    # echo "SERVER_ABSPATH: $SERVER_ABSPATH"
    sed -i 's/\r//g' "$RUN_FRONTEND_ABSPATH"
    # echo "NOT in macOS server START"
fi
chmod +x "$RUN_FRONTEND_ABSPATH"

FRONTEND_DIR_ABSPATH="$(dirname "$RUN_FRONTEND_ABSPATH")"

cd "$FRONTEND_DIR_ABSPATH"

# Put the bundled Node on PATH so `npm`, `node`, and the vite child
# processes all resolve even on a machine with no system Node. The
# packaged Electron shell exports OPENSWARM_NODE_PATH (e.g.
# .../node/x64/node.exe on Windows, .../node/<arch>/bin/node on POSIX);
# its directory holds node + the npm/npx shims. Dev leaves it unset and
# falls back to system Node on PATH.
NPM="npm"
if [[ -n "${OPENSWARM_NODE_PATH:-}" && -x "${OPENSWARM_NODE_PATH}" ]]; then
    NODE_DIR="$(dirname "$OPENSWARM_NODE_PATH")"
    export PATH="$NODE_DIR:$PATH"
    # Windows bundles npm.cmd next to node.exe; POSIX bundles an `npm` shim
    # in the same bin/ dir. Prefer the colocated one, else trust PATH.
    if [[ -f "$NODE_DIR/npm.cmd" ]]; then
        NPM="$NODE_DIR/npm.cmd"
    elif [[ -x "$NODE_DIR/npm" ]]; then
        NPM="$NODE_DIR/npm"
    fi
fi

# Fast path: the seeder usually symlinks node_modules to a shared warm
# cache (~/.openswarm/cache/webapp_template_node_modules/<hash>), so the
# dependency install has already been done once and we can skip straight
# to vite. A non-empty node_modules is NOT proof of a finished install
# (npm links .bin/* last, so a killed install leaves trees but no bin and
# vite dies with "command not found"); gate on the bin we actually launch.
if [ -e node_modules/.bin/vite ]; then
    echo "Dependencies already present - skipping install."
else
    # Incomplete tree. If node_modules is a SYMLINK to the shared warm cache,
    # never install through it: that writes into the cache every other app
    # shares (corruption) and stampedes when several apps boot at once. Drop
    # the link and install a private tree so this app heals alone while the
    # backend's background warmer rebuilds the shared cache for everyone else.
    [ -L node_modules ] && rm -f node_modules
    echo "Installing dependencies..."
    "$NPM" install --prefer-offline --no-audit --no-fund
fi

echo "Building with development mode..."
# Prefer `npm run dev` (honors package.json script + flags). But the
# packaged build ships node.exe WITHOUT npm, so on a machine with no
# system npm we fall back to invoking vite directly through the bundled
# node; node_modules is already populated (warm-cache symlink or seed),
# so vite's bin is present and this needs no package manager at all.
if command -v "$NPM" &>/dev/null || [[ "$NPM" != "npm" ]]; then
    "$NPM" run dev
elif [[ -n "${OPENSWARM_NODE_PATH:-}" && -x "${OPENSWARM_NODE_PATH}" && -f node_modules/vite/bin/vite.js ]]; then
    echo "npm not found; running vite directly via bundled node."
    "$OPENSWARM_NODE_PATH" node_modules/vite/bin/vite.js
else
    "$NPM" run dev
fi

# exit back to the dir that we were in before
cd -
