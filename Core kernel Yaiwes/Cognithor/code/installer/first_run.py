"""Cognithor First-Run Setup.

Called automatically on first launch when ~/.cognithor/.cognithor_initialized is missing.
Downloads community skills from GitHub registry, installs default agent configs,
and runs an interactive setup wizard (hardware detection, model recommendation).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any

REGISTRY_URL = "https://raw.githubusercontent.com/Alex8791-cyber/skill-registry/main/registry.json"
SKILL_BASE_URL = "https://raw.githubusercontent.com/Alex8791-cyber/skill-registry/main/skills"

JARVIS_HOME = Path(os.environ.get("JARVIS_HOME", Path.home() / ".cognithor"))
INSTALL_DIR = Path(sys.executable).resolve().parent.parent  # e.g. D:\Cognithor


def setup_agents() -> int:
    """Copy default agents.yaml to ~/.cognithor/ if missing."""
    agents_dest = JARVIS_HOME / "agents.yaml"
    if agents_dest.exists():
        print("  [SKIP] agents.yaml already exists")
        return 0

    # Look for default agents in installer dir
    agents_source = INSTALL_DIR / "agents.yaml.default"
    if not agents_source.exists():
        # Try next to this script
        agents_source = Path(__file__).parent / "agents.yaml.default"

    if agents_source.exists():
        shutil.copy2(agents_source, agents_dest)
        print("  [OK] 6 default agents installed")
        return 6
    else:
        print("  [WARN] No agents.yaml.default found")
        return 0


def _update_agents_language(lang: str) -> None:
    """Rewrite ``agents.yaml`` so every agent uses the user's chosen language.

    Issue #109: The default agents.yaml ships with ``language: de`` hardcoded.
    When the user picks a different language in the setup wizard, we post-process
    the file to replace those lines.
    """
    if not lang or lang == "de":
        return
    agents_path = JARVIS_HOME / "agents.yaml"
    if not agents_path.exists():
        return
    try:
        text = agents_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"  [WARN] Could not read agents.yaml: {exc}")
        return

    new_lines: list[str] = []
    replaced = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "language: de" or stripped.startswith("language: de "):
            indent = line[: len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}language: {lang}")
            replaced += 1
        else:
            new_lines.append(line)
    if replaced == 0:
        return
    try:
        agents_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"  [OK] Updated {replaced} agent language entries to '{lang}'")
    except Exception as exc:
        print(f"  [WARN] Could not update agents.yaml language: {exc}")


def setup_skills() -> int:
    """Download community skills from GitHub registry."""
    skills_dir = JARVIS_HOME / "skills" / "generated"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Download registry
    try:
        resp = urllib.request.urlopen(REGISTRY_URL, timeout=15)
        registry = json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] Could not fetch skill registry: {e}")
        return 0

    skills = registry.get("skills", [])
    installed = 0

    for skill in skills:
        name = skill.get("name", "")
        if not name:
            continue

        dest = skills_dir / f"{name}.md"
        if dest.exists():
            continue

        url = f"{SKILL_BASE_URL}/{name}/skill.md"
        try:
            urllib.request.urlretrieve(url, dest)
            installed += 1
        except Exception:
            pass  # silently skip failed downloads

    print(f"  [OK] {installed} community skills installed ({len(skills)} available)")
    return installed


def setup_encryption() -> bool:
    """Set up database encryption with auto-generated key in OS keyring."""
    try:
        import secrets

        import keyring
    except ImportError:
        print("  [SKIP] keyring not available, encryption disabled")
        return False

    # Check if key already exists
    existing = keyring.get_password("cognithor", "db_encryption_key")
    if existing:
        print("  [OK] Encryption key already in OS keyring")
        return True

    # Generate 32-byte hex key and store in OS keyring
    key = secrets.token_hex(32)
    try:
        keyring.set_password("cognithor", "db_encryption_key", key)
        print("  [OK] Encryption key generated and stored in OS keyring")
        return True
    except Exception as e:
        print(f"  [WARN] Could not store encryption key: {e}")
        return False


def setup_directories() -> None:
    """Create standard directory structure."""
    dirs = [
        JARVIS_HOME / "config",
        JARVIS_HOME / "skills" / "generated",
        JARVIS_HOME / "vault",
        JARVIS_HOME / "memory",
        JARVIS_HOME / "logs",
        JARVIS_HOME / "workspace",
        JARVIS_HOME / "cache",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def run_setup_wizard(encryption_ok: bool = False) -> dict | None:
    """Run interactive setup wizard: detect hardware, recommend model, write config."""
    try:
        # Import from installed cognithor package
        from cognithor.core.installer import (
            PRESETS,
            HardwareDetector,
            ModelRecommender,
            PresetLevel,
        )
    except ImportError:
        print("  [WARN] Could not import setup wizard (cognithor not installed?)")
        return None

    print()
    print("  --- System Configuration ---")
    print()

    # Step 1: Hardware detection
    print("  Detecting hardware...")
    detector = HardwareDetector()
    hw = detector.detect()
    print(f"  CPU:  {hw.cpu_name} ({hw.cpu_cores} cores)")
    print(f"  RAM:  {hw.ram_gb} GB")
    if hw.gpu.vram_gb > 0:
        print(f"  GPU:  {hw.gpu.name} ({hw.gpu.vram_gb} GB VRAM)")
    else:
        print("  GPU:  None detected (CPU-only mode)")
    print(f"  Disk: {hw.disk_free_gb} GB free")
    print(f"  Tier: {hw.tier.upper()}")
    print()

    # Step 2: LLM provider choice
    print("  How would you like to run LLMs?")
    print()
    print("    [1] Ollama (local, private, no internet needed)")
    print("    [2] External API (OpenAI, Anthropic, etc.)")
    print("    [3] Both (Ollama + API fallback)")
    print()

    provider_choice = _ask_choice("  Your choice [1/2/3]", ["1", "2", "3"], default="1")

    use_ollama = provider_choice in ("1", "3")
    use_api = provider_choice in ("2", "3")

    config: dict[str, Any] = {}

    # Step 3: Model selection (Ollama)
    if use_ollama:
        print()
        print("  --- Model Recommendation ---")
        recommender = ModelRecommender()
        recs = recommender.recommend(hw, top_n=5)

        if recs:
            print()
            for i, rec in enumerate(recs, 1):
                stars = "*" * rec.quality_score
                print(
                    f"    [{i}] {rec.model_name:<25} Quality: {stars:<10}"
                    f"  Speed: {rec.speed_score}/10  ({rec.use_case})"
                )
            print()

            model_choice = _ask_choice(
                f"  Select model [1-{len(recs)}]",
                [str(i) for i in range(1, len(recs) + 1)],
                default="1",
            )
            selected_model = recs[int(model_choice) - 1].model_name
        else:
            selected_model = "qwen3.5:3b"

        print(f"  [OK] Selected: {selected_model}")
        config["models"] = {
            "planner": {"name": selected_model},
            "executor": {"name": selected_model},
        }

    # Step 4: External API config
    if use_api:
        print()
        print("  --- External API Configuration ---")
        print()
        print("    [1] OpenAI (GPT-4o, GPT-4)")
        print("    [2] Anthropic (Claude)")
        print("    [3] Google (Gemini)")
        print("    [4] Other / Configure later")
        print()

        api_choice = _ask_choice("  API provider [1/2/3/4]", ["1", "2", "3", "4"], default="4")

        api_providers = {"1": "openai", "2": "anthropic", "3": "google", "4": "custom"}
        api_env_keys = {"1": "OPENAI_API_KEY", "2": "ANTHROPIC_API_KEY", "3": "GOOGLE_API_KEY"}
        backend_map = {"1": "openai", "2": "anthropic", "3": "gemini"}

        _ = api_providers[api_choice]  # validates choice; value unused
        if api_choice in backend_map:
            config["llm_backend_type"] = backend_map[api_choice]

        if api_choice in ("1", "2", "3"):
            env_key = api_env_keys[api_choice]
            existing = os.environ.get(env_key, "")
            if existing:
                print(f"  [OK] {env_key} already set in environment")
            else:
                print("  Enter your API key (or press Enter to configure later):")
                api_key = input("  > ").strip()
                if api_key:
                    # Save to .env file in cognithor home
                    env_file = JARVIS_HOME / ".env"
                    with open(env_file, "a", encoding="utf-8") as f:
                        f.write(f"{env_key}={api_key}\n")
                    print(f"  [OK] API key saved to {env_file}")
                else:
                    print(f"  [SKIP] Set {env_key} environment variable later")

        if not use_ollama:
            api_model = (
                "gpt-4o"
                if api_choice == "1"
                else "claude-sonnet-4-20250514"
                if api_choice == "2"
                else "gemini-2.0-flash"
                if api_choice == "3"
                else ""
            )
            if api_model:
                config["models"] = {
                    "planner": {"name": api_model},
                    "executor": {"name": api_model},
                }

    # Step 5: Apply preset based on hardware tier
    tier_map = {
        "minimal": PresetLevel.MINIMAL,
        "standard": PresetLevel.STANDARD,
        "power": PresetLevel.POWER,
        "enterprise": PresetLevel.ENTERPRISE,
    }
    preset_level = tier_map.get(hw.tier, PresetLevel.STANDARD)
    preset = PRESETS[preset_level]

    config["max_agents"] = preset.max_agents
    config["max_concurrent"] = preset.max_concurrent
    config["memory_limit_mb"] = preset.memory_limit_mb
    if hasattr(preset, "enable_rag"):
        config["rag"] = {"enabled": preset.enable_rag}
    config["database"] = {"encryption_enabled": encryption_ok}

    # Step 6: Language
    # Issue #114: honor the installer's language choice via the marker file
    # written by Inno Setup's CurStepChanged(ssPostInstall). If present, we
    # skip the interactive question so the user isn't asked twice.
    lang_map = {"1": "en", "2": "de", "3": "zh"}
    rev_lang_map = {v: k for k, v in lang_map.items()}
    marker_path = JARVIS_HOME / "install_language.txt"
    installer_lang: str | None = None
    if marker_path.exists():
        try:
            raw = marker_path.read_text(encoding="utf-8").strip().lower()[:2]
            if raw in lang_map.values():
                installer_lang = raw
        except Exception:
            installer_lang = None

    if installer_lang:
        config["language"] = installer_lang
        print()
        print(f"  --- Language: {installer_lang} (from installer) ---")
        # Clean up the marker so a later re-run falls through to the wizard.
        import contextlib as _ctx

        with _ctx.suppress(Exception):
            marker_path.unlink()
    else:
        print()
        print("  --- Language ---")
        print()
        print("    [1] English")
        print("    [2] Deutsch")
        print("    [3] Chinese")
        print()
        lang_choice = _ask_choice(
            "  Language [1/2/3]",
            ["1", "2", "3"],
            default=rev_lang_map.get("en", "1"),
        )
        config["language"] = lang_map[lang_choice]

    # Write config.yaml (load_config reads from ~/.cognithor/config.yaml)
    config_path = JARVIS_HOME / "config.yaml"
    if not config_path.exists():
        _write_yaml(config, config_path)
        print(f"\n  [OK] Configuration saved to {config_path}")
    else:
        print("\n  [SKIP] config.yaml already exists")

    return config


def _ask_choice(prompt: str, options: list[str], default: str = "") -> str:
    """Ask user for a choice with default fallback."""
    while True:
        try:
            answer = input(f"{prompt} (default={default}): ").strip()
            if not answer:
                return default
            if answer in options:
                return answer
            print(f"  Please enter one of: {', '.join(options)}")
        except (EOFError, KeyboardInterrupt):
            print()
            return default


def _write_yaml(data: dict, path: Path) -> None:
    """Write a simple YAML config file (no pyyaml dependency needed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Cognithor Configuration (auto-generated by first-run setup)\n"]

    def _format_value(val: object) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, str):
            return f'"{val}"'
        return str(val)

    def _write_dict(d: dict, indent: int = 0) -> None:
        prefix = "  " * indent
        for key, val in d.items():
            if isinstance(val, dict):
                lines.append(f"{prefix}{key}:")
                _write_dict(val, indent + 1)
            else:
                lines.append(f"{prefix}{key}: {_format_value(val)}")

    _write_dict(data)
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def mark_initialized() -> None:
    """Create marker file so first-run doesn't run again."""
    try:
        from jarvis import __version__ as ver
    except ImportError:
        ver = "0.80.1"
    marker = JARVIS_HOME / ".cognithor_initialized"
    marker.write_text(
        json.dumps(
            {
                "version": ver,
                "first_run": True,
            }
        )
    )


def main() -> None:
    print()
    print("=" * 50)
    print("  Cognithor First-Run Setup")
    print("=" * 50)
    print()

    # Check if already initialized
    marker = JARVIS_HOME / ".cognithor_initialized"
    if marker.exists():
        print("  Already initialized. Skipping.")
        return

    print("  Setting up directories...")
    setup_directories()

    print("  Setting up encryption...")
    encryption_ok = setup_encryption()

    print("  Installing default agents...")
    setup_agents()

    print("  Downloading community skills...")
    setup_skills()

    # Interactive setup wizard
    wizard_config = run_setup_wizard(encryption_ok=encryption_ok)

    # Issue #109: Apply chosen language to agents.yaml (which defaults to German)
    if wizard_config and isinstance(wizard_config, dict):
        chosen_lang = wizard_config.get("language", "de")
        if chosen_lang and chosen_lang != "de":
            _update_agents_language(chosen_lang)

    mark_initialized()

    print()
    print("  Setup complete!")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
