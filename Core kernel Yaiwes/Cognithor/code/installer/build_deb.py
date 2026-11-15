"""Build Cognithor Linux .deb Package.

Creates a Debian package with:
  - Python venv with cognithor[all] installed
  - Ollama binary (optional, downloaded if not present)
  - Flutter Command Center web build (optional)
  - systemd service file
  - Desktop entry + icon
  - Launcher script (/usr/bin/cognithor)

Usage:
    python installer/build_deb.py          # Build .deb
    python installer/build_deb.py --skip-ollama   # Without bundled Ollama
    python installer/build_deb.py --clean          # Clean build dir first

Prerequisites:
    - Linux (or WSL) with dpkg-deb
    - Python 3.12+ with pip
    - Internet connection (pip install, optional Ollama download)

Output:
    installer/dist/cognithor_<version>_amd64.deb
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import textwrap
import urllib.request
from pathlib import Path

# --- Config ---
OLLAMA_INSTALL_SCRIPT = "https://ollama.com/install.sh"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / "installer" / "build_deb"
DIST_DIR = PROJECT_ROOT / "installer" / "dist"
INSTALL_PREFIX = "/opt/cognithor"


def read_version() -> str:
    """Read version from pyproject.toml."""
    toml = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for line in toml.splitlines():
        if line.strip().startswith("version"):
            return line.split("=")[1].strip().strip('"')
    raise RuntimeError("Could not read version from pyproject.toml")


def download(url: str, dest: Path, desc: str = "") -> None:
    """Download a file with progress."""
    print(f"  Downloading {desc or url}...")
    if dest.exists():
        print(f"  [SKIP] Already exists: {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f"  [OK] {dest.name} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")


def step_venv(pkg_root: Path) -> Path:
    """Step 1: Create Python venv with cognithor installed."""
    print("\n=== Step 1: Python Virtual Environment ===")

    venv_dir = pkg_root / INSTALL_PREFIX.lstrip("/") / "venv"
    if venv_dir.exists():
        print("  [SKIP] venv/ already built")
        return venv_dir

    venv_dir.parent.mkdir(parents=True, exist_ok=True)

    # Create venv
    print("  Creating venv...")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
    )

    venv_python = venv_dir / "bin" / "python"

    # Upgrade pip
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=True,
        capture_output=True,
    )
    print("  [OK] pip upgraded")

    # Build wheel
    print("  Building cognithor wheel...")
    wheel_dir = BUILD_DIR / "wheel"
    wheel_dir.mkdir(exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(PROJECT_ROOT),
            "--wheel-dir",
            str(wheel_dir),
            "--no-deps",
        ],
        check=True,
    )

    # Install cognithor[all]
    print("  Installing cognithor[all] into venv...")
    wheels = sorted(wheel_dir.glob("cognithor-*.whl"))
    if not wheels:
        raise RuntimeError("No cognithor wheel found")

    # Install core extras (without torch/sentence-transformers to keep size <2GB).
    # Users can install GPU extras later: pip install cognithor[identity,arc-gpu]
    _extras = "memory,mcp,telegram,web,search,cron,documents,desktop,encryption"
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            f"{wheels[-1]}[{_extras}]",
            "--no-warn-script-location",
        ],
        check=True,
    )
    print(f"  [OK] cognithor[{_extras}] installed")

    return venv_dir


def step_ollama_install_script(pkg_root: Path) -> None:
    """Step 2: Bundle Ollama install script (not the 1.9GB binary).

    Ollama releases are now .tar.zst (~1.9 GB) which is too large to bundle.
    Instead, we ship the official install script and run it in postinst.
    """
    print("\n=== Step 2: Ollama Install Script ===")

    scripts_dir = pkg_root / INSTALL_PREFIX.lstrip("/") / "scripts"
    install_sh = scripts_dir / "install_ollama.sh"
    if install_sh.exists():
        print("  [SKIP] install_ollama.sh already exists")
        return

    scripts_dir.mkdir(parents=True, exist_ok=True)
    download(OLLAMA_INSTALL_SCRIPT, install_sh, "Ollama install script")
    install_sh.chmod(0o755)
    print("  [OK] Ollama install script bundled")


def step_flutter_ui(pkg_root: Path) -> Path | None:
    """Step 3: Copy Flutter web build."""
    print("\n=== Step 3: Flutter UI ===")

    web_build = PROJECT_ROOT / "flutter_app" / "build" / "web"
    dest = pkg_root / INSTALL_PREFIX.lstrip("/") / "web"

    if dest.exists():
        print("  [SKIP] web/ already in package")
        return dest

    if web_build.exists() and (web_build / "index.html").exists():
        shutil.copytree(web_build, dest)
        print(f"  [OK] Flutter web copied ({sum(1 for _ in dest.rglob('*'))} files)")
        return dest

    print("  [SKIP] No pre-built Flutter web found (flutter_app/build/web/)")
    return None


def step_launcher(pkg_root: Path, version: str) -> None:
    """Step 4: Create launcher script."""
    print("\n=== Step 4: Launcher Script ===")

    bin_dir = pkg_root / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    launcher = bin_dir / "cognithor"
    launcher.write_text(
        textwrap.dedent(f"""\
        #!/bin/bash
        # Cognithor v{version} — Agent OS
        # Installed to {INSTALL_PREFIX}

        export COGNITHOR_HOME="${{COGNITHOR_HOME:-$HOME/.jarvis}}"

        exec "{INSTALL_PREFIX}/venv/bin/python" -m cognithor "$@"
    """)
    )
    launcher.chmod(0o755)

    # Also create 'jarvis' symlink
    jarvis_link = bin_dir / "jarvis"
    if not jarvis_link.exists():
        jarvis_link.symlink_to("cognithor")

    print("  [OK] /usr/bin/cognithor + /usr/bin/jarvis")


def step_systemd(pkg_root: Path) -> None:
    """Step 5: Create systemd service file."""
    print("\n=== Step 5: Systemd Service ===")

    svc_dir = pkg_root / "etc" / "systemd" / "system"
    svc_dir.mkdir(parents=True, exist_ok=True)

    (svc_dir / "cognithor.service").write_text(
        textwrap.dedent("""\
        [Unit]
        Description=Cognithor Agent OS
        After=network-online.target ollama.service
        Wants=network-online.target

        [Service]
        Type=simple
        User=%i
        ExecStart=/usr/bin/cognithor --no-cli --api-host 0.0.0.0
        Restart=on-failure
        RestartSec=5
        Environment=COGNITHOR_HOME=/home/%i/.jarvis

        [Install]
        WantedBy=multi-user.target
    """)
    )
    print("  [OK] cognithor.service")


def step_desktop_entry(pkg_root: Path, version: str) -> None:
    """Step 6: Create desktop entry."""
    print("\n=== Step 6: Desktop Entry ===")

    apps_dir = pkg_root / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    (apps_dir / "cognithor.desktop").write_text(
        textwrap.dedent(f"""\
        [Desktop Entry]
        Name=Cognithor
        Comment=Agent OS — Local-first autonomous agent operating system
        Exec=/usr/bin/cognithor
        Terminal=true
        Type=Application
        Categories=Development;Utility;
        Version={version}
    """)
    )
    print("  [OK] cognithor.desktop")


def step_debian_control(pkg_root: Path, version: str) -> None:
    """Step 7: Create DEBIAN control files."""
    print("\n=== Step 7: DEBIAN Control ===")

    debian_dir = pkg_root / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)

    # Compute installed size (KB)
    total_size = sum(f.stat().st_size for f in pkg_root.rglob("*") if f.is_file()) // 1024

    (debian_dir / "control").write_text(
        textwrap.dedent(f"""\
        Package: cognithor
        Version: {version}
        Section: utils
        Priority: optional
        Architecture: amd64
        Depends: python3 (>= 3.12), libsqlite3-0
        Recommends: ollama
        Suggests: flutter
        Installed-Size: {total_size}
        Maintainer: Alexander Soellner <alex@cognithor.dev>
        Homepage: https://github.com/Alex8791-cyber/cognithor
        Description: Cognithor Agent OS — Local-first autonomous agent operating system
         PGE-Trinity architecture (Planner-Gatekeeper-Executor) with 122 MCP tools,
         18 communication channels, 6-tier memory system, and Flutter Command Center.
         .
         Features:
          - Local LLM via Ollama (qwen3, llama, etc.)
          - 12 MCP tool modules (filesystem, shell, web, media, memory, vault, etc.)
          - Telegram, Discord, Slack, WhatsApp, Signal, Matrix, and more
          - ARC-AGI-3 benchmark integration
          - Community Skill Marketplace
    """)
    )

    # postinst: first-run setup
    postinst = debian_dir / "postinst"
    postinst.write_text(
        textwrap.dedent("""\
        #!/bin/bash
        set -e

        # Install Ollama if not present
        if ! command -v ollama &>/dev/null; then
            echo "  Installing Ollama..."
            if [ -x "/opt/cognithor/scripts/install_ollama.sh" ]; then
                bash /opt/cognithor/scripts/install_ollama.sh || true
            else
                curl -fsSL https://ollama.com/install.sh | sh || true
            fi
        fi

        # Create default config directory for installing user
        if [ -n "$SUDO_USER" ]; then
            REAL_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
            JARVIS_HOME="$REAL_HOME/.cognithor"
            if [ ! -d "$JARVIS_HOME" ]; then
                su - "$SUDO_USER" -c "/usr/bin/cognithor --init-only" || true
            fi
        fi

        echo ""
        echo "  Cognithor installed successfully!"
        echo ""
        echo "  Quick start:"
        echo "    cognithor              # Start interactive CLI"
        echo "    cognithor --init-only  # Create config only"
        echo "    cognithor --lite       # Low-VRAM mode (8B models)"
        echo ""
        echo "  Config: ~/.cognithor/config.yaml"
        echo "  Docs:   https://github.com/Alex8791-cyber/cognithor"
        echo ""
    """)
    )
    postinst.chmod(0o755)

    # prerm: cleanup
    prerm = debian_dir / "prerm"
    prerm.write_text(
        textwrap.dedent("""\
        #!/bin/bash
        set -e

        # Stop systemd service if running
        if systemctl is-active --quiet cognithor@* 2>/dev/null; then
            systemctl stop cognithor@* || true
        fi
    """)
    )
    prerm.chmod(0o755)

    print(f"  [OK] DEBIAN/control (installed size: {total_size} KB)")


def build_deb(pkg_root: Path, version: str) -> Path:
    """Step 8: Build the .deb package."""
    print("\n=== Step 8: Build .deb ===")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    deb_name = f"cognithor_{version}_amd64.deb"
    deb_path = DIST_DIR / deb_name

    # Check for dpkg-deb
    if shutil.which("dpkg-deb"):
        subprocess.run(
            ["dpkg-deb", "--build", "--root-owner-group", str(pkg_root), str(deb_path)],
            check=True,
        )
    elif shutil.which("fakeroot") and shutil.which("dpkg-deb"):
        subprocess.run(
            ["fakeroot", "dpkg-deb", "--build", str(pkg_root), str(deb_path)],
            check=True,
        )
    else:
        # Fallback: create .deb manually using ar + tar
        print("  [WARN] dpkg-deb not found, creating .deb via ar+tar fallback")
        _build_deb_manual(pkg_root, deb_path)

    size_mb = deb_path.stat().st_size / 1024 / 1024
    print(f"\n  [OK] {deb_path} ({size_mb:.1f} MB)")
    return deb_path


def _build_deb_manual(pkg_root: Path, deb_path: Path) -> None:
    """Build .deb without dpkg-deb (ar + tar fallback)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # debian-binary
        (tmpdir / "debian-binary").write_text("2.0\n")

        # control.tar.gz
        debian_dir = pkg_root / "DEBIAN"
        with tarfile.open(tmpdir / "control.tar.gz", "w:gz") as tf:
            for f in debian_dir.iterdir():
                tf.add(f, arcname=f"./{f.name}")

        # data.tar.gz
        with tarfile.open(tmpdir / "data.tar.gz", "w:gz") as tf:
            for entry in sorted(pkg_root.iterdir()):
                if entry.name == "DEBIAN":
                    continue
                tf.add(entry, arcname=f"./{entry.name}")

        # Assemble with ar
        if shutil.which("ar"):
            subprocess.run(
                [
                    "ar",
                    "rcs",
                    str(deb_path),
                    str(tmpdir / "debian-binary"),
                    str(tmpdir / "control.tar.gz"),
                    str(tmpdir / "data.tar.gz"),
                ],
                check=True,
            )
        else:
            raise RuntimeError(
                "Neither dpkg-deb nor ar found. Install dpkg or binutils.\n"
                "On Ubuntu/Debian: sudo apt install dpkg-dev\n"
                "On WSL: sudo apt install dpkg-dev"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Cognithor .deb package")
    parser.add_argument("--skip-ollama", action="store_true", help="Don't bundle Ollama")
    parser.add_argument("--clean", action="store_true", help="Clean build directory first")
    args = parser.parse_args()

    version = read_version()
    print(f"Building Cognithor {version} .deb package")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Build dir:    {BUILD_DIR}")

    if args.clean and BUILD_DIR.exists():
        print("  Cleaning build directory...")
        shutil.rmtree(BUILD_DIR)

    # Package root = fake filesystem that becomes the .deb content
    pkg_root = BUILD_DIR / "pkg"
    pkg_root.mkdir(parents=True, exist_ok=True)

    # Build steps
    step_venv(pkg_root)
    step_ollama_install_script(pkg_root)
    step_flutter_ui(pkg_root)
    step_launcher(pkg_root, version)
    step_systemd(pkg_root)
    step_desktop_entry(pkg_root, version)
    step_debian_control(pkg_root, version)
    deb_path = build_deb(pkg_root, version)

    print(f"\n{'=' * 60}")
    print(f"  .deb package ready: {deb_path}")
    print(f"  Install: sudo dpkg -i {deb_path.name}")
    print("  Remove:  sudo dpkg -r cognithor")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
