#!/usr/bin/env python3
"""
Version management script for ISEK.
Helps with version updates and release preparation.
"""

import re
import sys
from pathlib import Path
from typing import Tuple


def read_current_version() -> str:
    """Read current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")

    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def update_version(new_version: str) -> None:
    """Update version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Update version
    content = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']', f'version = "{new_version}"', content
    )

    pyproject_path.write_text(content)
    print(f"✅ Updated version to {new_version}")


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into components"""
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Version must have 3 parts: {version}")

    return (int(parts[0]), int(parts[1]), int(parts[2]))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version components into string"""
    return f"{major}.{minor}.{patch}"


def suggest_next_version(current_version: str, release_type: str = "patch") -> str:
    """Suggest next version based on release type"""
    major, minor, patch = parse_version(current_version)

    if release_type == "major":
        return format_version(major + 1, 0, 0)
    elif release_type == "minor":
        return format_version(major, minor + 1, 0)
    elif release_type == "patch":
        return format_version(major, minor, patch + 1)
    else:
        raise ValueError(f"Unknown release type: {release_type}")


def create_release_notes(version: str) -> str:
    """Create a template for release notes"""
    return f"""# Release {version}

## What's New
- 

## Bug Fixes
- 

## Breaking Changes
- 

## Installation
```bash
pip install isek=={version}
```

## Quick Start
```bash
pip install isek
isek setup
```

## Documentation
- [Installation Guide](INSTALL.md)
- [User Guide](docs/source/user_guide/)
- [API Documentation](docs/source/api/)
"""


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python scripts/version.py current                    # Show current version"
        )
        print(
            "  python scripts/version.py next [major|minor|patch]  # Suggest next version"
        )
        print(
            "  python scripts/version.py update <version>          # Update to specific version"
        )
        print(
            "  python scripts/version.py bump [major|minor|patch]  # Bump and update version"
        )
        print(
            "  python scripts/version.py notes [version]           # Generate release notes template"
        )
        return

    command = sys.argv[1]

    try:
        if command == "current":
            version = read_current_version()
            print(f"Current version: {version}")

        elif command == "next":
            release_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
            current_version = read_current_version()
            next_version = suggest_next_version(current_version, release_type)
            print(f"Current version: {current_version}")
            print(f"Suggested next version ({release_type}): {next_version}")

        elif command == "update":
            if len(sys.argv) < 3:
                print("Error: Please provide a version number")
                return
            new_version = sys.argv[2]
            update_version(new_version)

        elif command == "bump":
            release_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
            current_version = read_current_version()
            next_version = suggest_next_version(current_version, release_type)
            update_version(next_version)
            print(f"Bumped version from {current_version} to {next_version}")

        elif command == "notes":
            version = sys.argv[2] if len(sys.argv) > 2 else read_current_version()
            notes = create_release_notes(version)
            print("Release notes template:")
            print("=" * 50)
            print(notes)

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
