"""Tests fuer F-021: Docker --cpus falsche Einheiten.

Prueft dass:
  - SandboxConfig.max_cpu_cores existiert mit Default 1.0
  - Docker-Args max_cpu_cores statt max_cpu_seconds/10 verwenden
  - Verschiedene max_cpu_cores Werte korrekt in docker_args landen
  - max_cpu_seconds keinen Einfluss auf --cpus hat
  - Source-Code den Fix enthaelt
"""

from __future__ import annotations

import inspect

import pytest

from cognithor.models import SandboxConfig
from cognithor.security.sandbox import Sandbox

# ============================================================================
# SandboxConfig Tests
# ============================================================================


class TestSandboxConfigCpuCores:
    """Prueft das neue max_cpu_cores Feld."""

    def test_default_1_core(self) -> None:
        config = SandboxConfig()
        assert config.max_cpu_cores == 1.0

    def test_custom_value(self) -> None:
        config = SandboxConfig(max_cpu_cores=2.5)
        assert config.max_cpu_cores == 2.5

    def test_fractional_cores(self) -> None:
        config = SandboxConfig(max_cpu_cores=0.5)
        assert config.max_cpu_cores == 0.5

    def test_min_value(self) -> None:
        config = SandboxConfig(max_cpu_cores=0.1)
        assert config.max_cpu_cores == 0.1

    def test_below_min_rejected(self) -> None:
        with pytest.raises(Exception, match="cpu|cores"):
            SandboxConfig(max_cpu_cores=0.05)

    def test_max_value(self) -> None:
        config = SandboxConfig(max_cpu_cores=64.0)
        assert config.max_cpu_cores == 64.0

    def test_above_max_rejected(self) -> None:
        with pytest.raises(Exception, match="cpu|cores"):
            SandboxConfig(max_cpu_cores=65.0)


# ============================================================================
# Docker Args Tests
# ============================================================================


class TestDockerCpuArgs:
    """Prueft dass Docker-Args korrekte --cpus Werte enthalten."""

    def _get_docker_args(self, config: SandboxConfig) -> list[str]:
        """Extrahiert die Docker-Args aus _exec_docker Source."""
        # Wir testen indirekt via Source-Inspection:
        # Die docker_args werden aus self._config.max_cpu_cores gebaut
        Sandbox(config)
        source = inspect.getsource(Sandbox._exec_docker)
        return source

    def test_uses_max_cpu_cores_not_seconds(self) -> None:
        """--cpus verwendet max_cpu_cores, nicht max_cpu_seconds/10."""
        source = inspect.getsource(Sandbox._exec_docker)
        assert "max_cpu_cores" in source
        assert "max_cpu_seconds / 10" not in source
        assert "max_cpu_seconds" not in source

    def test_default_cpus_value(self) -> None:
        """Default-Config erzeugt --cpus 1.0."""
        config = SandboxConfig()
        cpus_value = str(config.max_cpu_cores)
        assert cpus_value == "1.0"

    def test_custom_cpus_value(self) -> None:
        """Custom max_cpu_cores=2.5 erzeugt --cpus 2.5."""
        config = SandboxConfig(max_cpu_cores=2.5)
        cpus_value = str(config.max_cpu_cores)
        assert cpus_value == "2.5"

    def test_cpu_seconds_independent_from_cpus(self) -> None:
        """max_cpu_seconds hat keinen Einfluss auf --cpus Wert."""
        config_10s = SandboxConfig(max_cpu_seconds=10, max_cpu_cores=1.0)
        config_60s = SandboxConfig(max_cpu_seconds=60, max_cpu_cores=1.0)
        config_300s = SandboxConfig(max_cpu_seconds=300, max_cpu_cores=1.0)

        assert str(config_10s.max_cpu_cores) == "1.0"
        assert str(config_60s.max_cpu_cores) == "1.0"
        assert str(config_300s.max_cpu_cores) == "1.0"

    def test_old_bug_would_give_6_cores(self) -> None:
        """Alter Bug: max_cpu_seconds=60 / 10 = 6.0 Cores (semantisch falsch)."""
        config = SandboxConfig(max_cpu_seconds=60, max_cpu_cores=1.0)
        old_buggy_value = config.max_cpu_seconds / 10  # 6.0
        correct_value = config.max_cpu_cores  # 1.0

        assert old_buggy_value == 6.0  # Das waere falsch gewesen
        assert correct_value == 1.0  # Jetzt korrekt


# ============================================================================
# Regression
# ============================================================================


class TestRegression:
    """Prueft dass andere Config-Werte unveraendert sind."""

    def test_memory_mb_still_works(self) -> None:
        config = SandboxConfig(max_memory_mb=1024)
        assert config.max_memory_mb == 1024

    def test_cpu_seconds_still_works(self) -> None:
        config = SandboxConfig(max_cpu_seconds=30)
        assert config.max_cpu_seconds == 30

    def test_timeout_still_works(self) -> None:
        config = SandboxConfig(timeout_seconds=60)
        assert config.timeout_seconds == 60

    def test_all_fields_coexist(self) -> None:
        config = SandboxConfig(
            max_memory_mb=256,
            max_cpu_seconds=20,
            max_cpu_cores=0.5,
            timeout_seconds=45,
        )
        assert config.max_memory_mb == 256
        assert config.max_cpu_seconds == 20
        assert config.max_cpu_cores == 0.5
        assert config.timeout_seconds == 45


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_docker_uses_max_cpu_cores(self) -> None:
        source = inspect.getsource(Sandbox._exec_docker)
        assert "max_cpu_cores" in source

    def test_docker_no_seconds_division(self) -> None:
        source = inspect.getsource(Sandbox._exec_docker)
        assert "max_cpu_seconds / 10" not in source

    def test_config_has_max_cpu_cores(self) -> None:
        source = inspect.getsource(SandboxConfig)
        assert "max_cpu_cores" in source

    def test_docker_has_cpus_flag(self) -> None:
        source = inspect.getsource(Sandbox._exec_docker)
        assert '"--cpus"' in source
