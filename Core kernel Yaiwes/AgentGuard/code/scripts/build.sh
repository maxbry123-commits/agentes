#!/bin/bash
set -e

echo "🔨 Building AgentGuard..."

# Compile TypeScript with verbose output
echo "📝 Running TypeScript compilation..."
npx tsc --listFiles | grep -E "(bin/|error|Error)" || true

# Check if bin files were created
echo "📁 Checking bin files after tsc..."
ls -la dist/bin/ 2>/dev/null || echo "dist/bin not found"

# Make executables executable if they exist
if [ -d "dist/bin" ]; then
    find dist/bin -name "*.js" -exec chmod +x {} \; 2>/dev/null || true
fi

# Copy wrapper scripts if they exist
mkdir -p dist/bin/wrappers
if [ -d "src/bin/wrappers" ] && [ "$(ls -A src/bin/wrappers 2>/dev/null)" ]; then
    cp src/bin/wrappers/* dist/bin/wrappers/ 2>/dev/null || true
    chmod +x dist/bin/wrappers/* 2>/dev/null || true
fi

echo "✅ Build complete"
