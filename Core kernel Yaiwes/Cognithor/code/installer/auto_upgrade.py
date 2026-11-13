r"""Auto-upgrade Cognithor if a source tree with a newer version is found.

Checked locations (in order):
  1. COGNITHOR_DEV environment variable
  2. %USERPROFILE%\Cognithor
  3. D:\Cognithor
  4. %USERPROFILE%\Jarvis\jarvis complete v20 (legacy)
  5. D:\Jarvis\jarvis complete v20 (legacy)

If src/cognithor/ with a higher version is found, copies the package
directly into site-packages (no pip/build tools needed).
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path


def _read_version_from_toml(toml_path: Path) -> str | None:
    """Extract version = 'X.Y.Z' from pyproject.toml."""
    try:
        for line in toml_path.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*version\s*=\s*"([^"]+)"', line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def _installed_version() -> str | None:
    """Get the currently installed cognithor version."""
    try:
        from cognithor import __version__

        return __version__
    except Exception:
        pass
    # Fallback: try legacy package name
    try:
        from jarvis import __version__

        return __version__
    except Exception:
        pass
    return None


def _compare_versions(a: str, b: str) -> int:
    """Compare two version strings. Returns >0 if a > b."""

    def parts(v: str) -> list[int]:
        return [int(x) for x in re.findall(r"\d+", v)]

    pa, pb = parts(a), parts(b)
    for x, y in zip(pa, pb, strict=False):
        if x != y:
            return x - y
    return len(pa) - len(pb)


def _find_site_packages() -> Path | None:
    """Find the site-packages directory for the current Python."""
    for p in sys.path:
        pp = Path(p)
        if pp.name == "site-packages" and pp.is_dir():
            return pp
    return None


def main() -> None:
    candidates = []

    # 1. COGNITHOR_DEV env var
    dev = os.environ.get("COGNITHOR_DEV", "")
    if dev:
        candidates.append(Path(dev))

    # 2-5. Common locations (new + legacy)
    home = Path.home()
    candidates.extend(
        [
            home / "Cognithor",
            Path("D:/Cognithor"),
            home / "cognithor",
            home / "Jarvis" / "jarvis complete v20",  # legacy
            Path("D:/Jarvis/jarvis complete v20"),  # legacy
        ]
    )

    cur = _installed_version()
    if not cur:
        return

    for candidate in candidates:
        toml = candidate / "pyproject.toml"
        # Try both new and legacy source directory names
        src_pkg = candidate / "src" / "cognithor"
        if not src_pkg.is_dir():
            src_pkg = candidate / "src" / "jarvis"  # legacy layout
        if not toml.exists() or not src_pkg.is_dir():
            continue

        dev_ver = _read_version_from_toml(toml)
        if not dev_ver:
            continue

        if _compare_versions(dev_ver, cur) > 0:
            print(f"  [UPGRADE] Source v{dev_ver} found at {candidate}")
            print(f"            Installed v{cur} -- upgrading...")

            site_packages = _find_site_packages()
            if site_packages is None:
                print("  [WARN] Could not find site-packages directory")
                print(f"         Continuing with v{cur}")
                return

            # Determine target package name from source
            pkg_name = src_pkg.name  # "cognithor" or "jarvis"
            dest = site_packages / pkg_name
            try:
                # Remove old packages (both names)
                for old_name in ("cognithor", "jarvis"):
                    old_dest = site_packages / old_name
                    if old_dest.exists():
                        shutil.rmtree(old_dest)
                # Copy new source
                shutil.copytree(src_pkg, dest)
                # Copy data/procedures to ~/.cognithor/data/procedures
                src_data = candidate / "data" / "procedures"
                cognithor_home = Path.home() / ".cognithor"
                if not cognithor_home.exists():
                    cognithor_home = Path.home() / ".jarvis"  # fallback
                dest_data = cognithor_home / "data" / "procedures"
                if src_data.is_dir():
                    dest_data.mkdir(parents=True, exist_ok=True)
                    for f in src_data.glob("*.md"):
                        shutil.copy2(f, dest_data / f.name)
                # Sync Flutter web UI if a build exists
                src_web = candidate / "flutter_app" / "build" / "web"
                install_dir = Path(sys.executable).parent.parent
                dest_web = install_dir / "flutter_app" / "web"
                if src_web.is_dir() and (src_web / "index.html").exists():
                    if dest_web.exists():
                        shutil.rmtree(dest_web)
                    dest_web.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src_web, dest_web)
                    print("  [OK] Flutter UI synced")
                print(f"  [OK] Upgraded to v{dev_ver}")
            except Exception as exc:
                print(f"  [WARN] Upgrade failed: {exc}")
                print(f"         Continuing with v{cur}")
            return  # Only upgrade once

    # No upgrade needed -- silent return


if __name__ == "__main__":
    main()
