#!/usr/bin/env python3
"""
Build Sphinx documentation locally for testing.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    print("🔨 Building ISEK documentation...")

    # Change to docs directory
    os.chdir(docs_dir)

    try:
        # Clean previous build
        print("🧹 Cleaning previous build...")
        subprocess.run(["make", "clean"], check=True, capture_output=True)

        # Build HTML documentation
        print("📚 Building HTML documentation...")
        result = subprocess.run(
            ["make", "html"], check=True, capture_output=True, text=True
        )

        print("✅ Documentation built successfully!")
        print(f"📁 Output directory: {docs_dir / 'build' / 'html'}")
        print("🌐 Open index.html in your browser to view the documentation")

        # Check if there were any warnings
        if "warning" in result.stdout.lower() or "warning" in result.stderr.lower():
            print("⚠️  Warnings detected during build. Check the output above.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error building documentation: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
