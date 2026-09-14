# Evolution Engine Phase 1: Hardware-Aware System Profile

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Comprehensive hardware/software detection at startup (GPU via nvidia-smi, CPU, RAM, disk, network, Ollama, LM Studio) with structured SystemProfile, mode recommendation, REST API, and Flutter visualization page.

**Architecture:** New `src/jarvis/system/` module with `SystemDetector` class that runs 8 detection targets. Results stored as `SystemProfile` dataclass, cached to `~/.cognithor/system_profile.json`, exposed via `GET /api/v1/system/profile`. Flutter shows hardware details with color-coded status badges. Existing `HardwareDetector` in `installer.py` is NOT modified — SystemDetector is a clean replacement used at runtime.

**Tech Stack:** Python 3.12+ (psutil, subprocess, platform, shutil, urllib), pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/system/__init__.py` | Package exports |
| Create | `src/jarvis/system/detector.py` | SystemDetector + 8 detect_* methods + SystemProfile |
| Modify | `src/jarvis/gateway/gateway.py` | Run quick_scan on startup, store profile |
| Modify | `src/jarvis/channels/config_routes.py` | GET /api/v1/system/profile endpoint |
| Create | `flutter_app/lib/screens/config/system_profile_page.dart` | Hardware profile visualization |
| Modify | `flutter_app/lib/screens/config_screen.dart` | Register system_profile page |
| Create | `tests/unit/test_system_detector.py` | 15+ tests |

---

### Task 1: DetectionResult + SystemProfile Data Models

**Files:**
- Create: `src/jarvis/system/__init__.py`
- Create: `src/jarvis/system/detector.py` (data models only)
- Create: `tests/unit/test_system_detector.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_system_detector.py`:

```python
"""Tests for SystemDetector — hardware/software detection."""

import json
import pytest
from pathlib import Path


class TestDetectionResult:
    def test_create_ok_result(self):
        from jarvis.system.detector import DetectionResult
        r = DetectionResult(key="cpu", value="AMD Ryzen 9", status="ok", raw_data={"cores": 16})
        assert r.key == "cpu"
        assert r.status == "ok"
        assert r.raw_data["cores"] == 16

    def test_create_fail_result(self):
        from jarvis.system.detector import DetectionResult
        r = DetectionResult(key="gpu", value="No GPU found", status="fail", raw_data={})
        assert r.status == "fail"

    def test_to_dict(self):
        from jarvis.system.detector import DetectionResult
        r = DetectionResult(key="ram", value="32 GB", status="ok", raw_data={"total_gb": 32})
        d = r.to_dict()
        assert d["key"] == "ram"
        assert d["raw_data"]["total_gb"] == 32


class TestSystemProfile:
    def test_empty_profile(self):
        from jarvis.system.detector import SystemProfile
        p = SystemProfile()
        assert len(p.results) == 0

    def test_add_result(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["cpu"] = DetectionResult(key="cpu", value="Test", status="ok", raw_data={})
        assert "cpu" in p.results

    def test_get_tier_minimal(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["ram"] = DetectionResult(key="ram", value="4 GB", status="fail", raw_data={"total_gb": 4})
        p.results["cpu"] = DetectionResult(key="cpu", value="2 cores", status="warn", raw_data={"physical_cores": 2})
        p.results["gpu"] = DetectionResult(key="gpu", value="None", status="fail", raw_data={"vram_total_gb": 0})
        assert p.get_tier() == "minimal"

    def test_get_tier_power(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["ram"] = DetectionResult(key="ram", value="64 GB", status="ok", raw_data={"total_gb": 64})
        p.results["cpu"] = DetectionResult(key="cpu", value="16 cores", status="ok", raw_data={"physical_cores": 16})
        p.results["gpu"] = DetectionResult(key="gpu", value="RTX 4090", status="ok", raw_data={"vram_total_gb": 24})
        assert p.get_tier() in ("power", "enterprise")

    def test_get_available_modes_offline_only(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["gpu"] = DetectionResult(key="gpu", value="RTX", status="ok", raw_data={"vram_total_gb": 24})
        p.results["ollama"] = DetectionResult(key="ollama", value="Running", status="ok", raw_data={"running": True})
        p.results["network"] = DetectionResult(key="network", value="No internet", status="fail", raw_data={"internet": False})
        modes = p.get_available_modes()
        assert "offline" in modes
        assert "online" not in modes

    def test_get_recommended_mode(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["gpu"] = DetectionResult(key="gpu", value="RTX", status="ok", raw_data={"vram_total_gb": 24})
        p.results["ollama"] = DetectionResult(key="ollama", value="Running", status="ok", raw_data={"running": True, "models": ["qwen3:32b"]})
        p.results["network"] = DetectionResult(key="network", value="OK", status="ok", raw_data={"internet": True})
        mode = p.get_recommended_mode()
        assert mode in ("offline", "hybrid")

    def test_to_dict_roundtrip(self):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["cpu"] = DetectionResult(key="cpu", value="Test CPU", status="ok", raw_data={"cores": 8})
        d = p.to_dict()
        assert d["results"]["cpu"]["value"] == "Test CPU"

    def test_save_and_load(self, tmp_path):
        from jarvis.system.detector import DetectionResult, SystemProfile
        p = SystemProfile()
        p.results["ram"] = DetectionResult(key="ram", value="32 GB", status="ok", raw_data={"total_gb": 32})
        path = tmp_path / "profile.json"
        p.save(path)
        loaded = SystemProfile.load(path)
        assert loaded is not None
        assert loaded.results["ram"].raw_data["total_gb"] == 32

    def test_load_nonexistent_returns_none(self, tmp_path):
        from jarvis.system.detector import SystemProfile
        result = SystemProfile.load(tmp_path / "nonexistent.json")
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_system_detector.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement data models**

Create `src/jarvis/system/__init__.py`:
```python
"""System detection and hardware profiling."""
from jarvis.system.detector import DetectionResult, SystemDetector, SystemProfile

__all__ = ["DetectionResult", "SystemDetector", "SystemProfile"]
```

Create `src/jarvis/system/detector.py` with DetectionResult, SystemProfile (data models + save/load + get_tier + get_available_modes + get_recommended_mode). No detection methods yet.

```python
"""System Detector — comprehensive hardware and software profiling.

Detects CPU, RAM, GPU, disk, network, Ollama, LM Studio at startup.
Results cached to ~/.cognithor/system_profile.json.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["DetectionResult", "SystemDetector", "SystemProfile"]


@dataclass
class DetectionResult:
    """Result of a single detection target."""

    key: str
    value: str
    status: str  # "ok" | "warn" | "fail"
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "status": self.status, "raw_data": self.raw_data}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DetectionResult:
        return cls(key=d["key"], value=d["value"], status=d["status"], raw_data=d.get("raw_data", {}))


@dataclass
class SystemProfile:
    """Complete system profile with all detection results."""

    results: dict[str, DetectionResult] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def get_tier(self) -> str:
        ram_gb = self.results.get("ram", DetectionResult("ram", "", "fail", {})).raw_data.get("total_gb", 0)
        cores = self.results.get("cpu", DetectionResult("cpu", "", "fail", {})).raw_data.get("physical_cores", 0)
        vram = self.results.get("gpu", DetectionResult("gpu", "", "fail", {})).raw_data.get("vram_total_gb", 0)
        if ram_gb >= 64 and cores >= 16 and vram >= 48:
            return "enterprise"
        if vram >= 16 and ram_gb >= 32:
            return "power"
        if vram >= 8 and ram_gb >= 16:
            return "standard"
        return "minimal"

    def get_available_modes(self) -> list[str]:
        modes = []
        ollama = self.results.get("ollama", DetectionResult("ollama", "", "fail", {}))
        network = self.results.get("network", DetectionResult("network", "", "fail", {}))
        gpu = self.results.get("gpu", DetectionResult("gpu", "", "fail", {}))
        if ollama.raw_data.get("running") or gpu.raw_data.get("vram_total_gb", 0) >= 4:
            modes.append("offline")
        if network.raw_data.get("internet"):
            modes.append("online")
        if "offline" in modes and "online" in modes:
            modes.append("hybrid")
        if not modes:
            modes.append("offline")
        return modes

    def get_recommended_mode(self) -> str:
        modes = self.get_available_modes()
        ollama = self.results.get("ollama", DetectionResult("ollama", "", "fail", {}))
        gpu = self.results.get("gpu", DetectionResult("gpu", "", "fail", {}))
        if "offline" in modes and ollama.raw_data.get("running") and gpu.raw_data.get("vram_total_gb", 0) >= 8:
            return "offline"
        if "hybrid" in modes:
            return "hybrid"
        if "online" in modes:
            return "online"
        return "offline"

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_at": self.detected_at,
            "tier": self.get_tier(),
            "recommended_mode": self.get_recommended_mode(),
            "available_modes": self.get_available_modes(),
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SystemProfile | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            profile = cls(detected_at=data.get("detected_at", ""))
            for k, v in data.get("results", {}).items():
                profile.results[k] = DetectionResult.from_dict(v)
            return profile
        except Exception:
            return None
```

- [ ] **Step 4: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_system_detector.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/system/ tests/unit/test_system_detector.py
git commit -m "feat: DetectionResult + SystemProfile data models with tier/mode logic"
```

---

### Task 2: 8 Detection Methods (CPU, RAM, OS, GPU, Disk, Network, Ollama, LMStudio)

**Files:**
- Modify: `src/jarvis/system/detector.py` (add SystemDetector class)
- Modify: `tests/unit/test_system_detector.py` (add detection tests)

- [ ] **Step 1: Write detection tests**

Append to test file:

```python
class TestSystemDetector:
    @pytest.fixture
    def detector(self):
        from jarvis.system.detector import SystemDetector
        return SystemDetector()

    def test_detect_os(self, detector):
        r = detector.detect_os()
        assert r.key == "os"
        assert r.status == "ok"
        assert "os" in r.raw_data

    def test_detect_cpu(self, detector):
        r = detector.detect_cpu()
        assert r.key == "cpu"
        assert r.raw_data.get("physical_cores", 0) > 0

    def test_detect_ram(self, detector):
        r = detector.detect_ram()
        assert r.key == "ram"
        assert r.raw_data.get("total_gb", 0) > 0

    def test_detect_gpu(self, detector):
        r = detector.detect_gpu()
        assert r.key == "gpu"
        assert r.status in ("ok", "warn", "fail")

    def test_detect_disk(self, detector):
        r = detector.detect_disk()
        assert r.key == "disk"
        assert r.raw_data.get("free_gb", 0) >= 0

    def test_detect_network(self, detector):
        r = detector.detect_network()
        assert r.key == "network"
        assert r.status in ("ok", "warn", "fail")

    def test_detect_ollama(self, detector):
        r = detector.detect_ollama()
        assert r.key == "ollama"
        assert r.status in ("ok", "warn", "fail")

    def test_detect_lmstudio(self, detector):
        r = detector.detect_lmstudio()
        assert r.key == "lmstudio"
        assert r.status in ("ok", "warn", "fail")

    def test_run_full_scan(self, detector):
        profile = detector.run_full_scan()
        assert len(profile.results) >= 6
        assert "cpu" in profile.results
        assert "ram" in profile.results

    def test_run_quick_scan_uses_cache(self, detector, tmp_path):
        profile = detector.run_full_scan()
        cache_path = tmp_path / "profile.json"
        profile.save(cache_path)
        quick = detector.run_quick_scan(cache_path=cache_path)
        assert "cpu" in quick.results
```

- [ ] **Step 2: Implement SystemDetector class**

Add to `src/jarvis/system/detector.py`:

```python
class SystemDetector:
    """Detects hardware and software environment."""

    def detect_os(self) -> DetectionResult:
        import platform, sys
        data = {
            "os": platform.system().lower(),
            "version": platform.release(),
            "arch": platform.machine(),
            "python": platform.python_version(),
            "is_wsl": "microsoft" in platform.release().lower() if sys.platform == "linux" else False,
        }
        return DetectionResult(key="os", value=f"{platform.system()} {platform.release()}", status="ok", raw_data=data)

    def detect_cpu(self) -> DetectionResult:
        import os, platform
        cores = os.cpu_count() or 1
        physical = cores // 2 if cores > 1 else 1
        try:
            import psutil
            physical = psutil.cpu_count(logical=False) or physical
            freq = psutil.cpu_freq()
            max_freq = freq.max if freq else 0
        except ImportError:
            max_freq = 0
        name = platform.processor() or platform.machine()
        status = "ok" if physical >= 4 else "warn" if physical >= 2 else "fail"
        data = {"model": name, "physical_cores": physical, "logical_cores": cores, "max_freq_mhz": max_freq}
        return DetectionResult(key="cpu", value=f"{name} ({physical}C/{cores}T)", status=status, raw_data=data)

    def detect_ram(self) -> DetectionResult:
        total_gb = 0
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3), 1)
            available_gb = round(mem.available / (1024**3), 1)
            percent = mem.percent
        except ImportError:
            # Fallback: platform-specific
            import platform, subprocess, sys
            if sys.platform == "win32":
                try:
                    import ctypes
                    mem_kb = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem_kb))
                    total_gb = round(mem_kb.value / (1024 * 1024), 1)
                except Exception:
                    pass
            available_gb = 0
            percent = 0
        status = "ok" if total_gb >= 16 else "warn" if total_gb >= 8 else "fail"
        data = {"total_gb": total_gb, "available_gb": available_gb, "percent_used": percent}
        return DetectionResult(key="ram", value=f"{total_gb} GB", status=status, raw_data=data)

    def detect_gpu(self) -> DetectionResult:
        import subprocess, sys
        # Try nvidia-smi
        try:
            cmd = ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"]
            if sys.platform == "win32":
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) >= 4:
                    name = parts[0].strip()
                    vram_total = round(float(parts[1].strip()) / 1024, 1)
                    vram_free = round(float(parts[2].strip()) / 1024, 1)
                    driver = parts[3].strip()
                    status = "ok" if vram_total >= 8 else "warn" if vram_total >= 4 else "fail"
                    data = {"vendor": "nvidia", "model": name, "vram_total_gb": vram_total, "vram_free_gb": vram_free, "driver": driver}
                    return DetectionResult(key="gpu", value=f"{name} ({vram_total} GB)", status=status, raw_data=data)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # Check Apple Silicon
        import platform
        if platform.system() == "Darwin" and "arm" in platform.machine().lower():
            data = {"vendor": "apple", "model": "Apple Silicon", "vram_total_gb": 0, "unified_memory": True}
            return DetectionResult(key="gpu", value="Apple Silicon (unified)", status="warn", raw_data=data)
        return DetectionResult(key="gpu", value="No dedicated GPU", status="fail", raw_data={"vendor": "none", "vram_total_gb": 0})

    def detect_disk(self) -> DetectionResult:
        import shutil
        from pathlib import Path
        home = Path.home() / ".cognithor"
        usage = shutil.disk_usage(str(home.parent))
        free_gb = round(usage.free / (1024**3), 1)
        total_gb = round(usage.total / (1024**3), 1)
        status = "ok" if free_gb >= 50 else "warn" if free_gb >= 10 else "fail"
        data = {"path": str(home.parent), "total_gb": total_gb, "free_gb": free_gb}
        return DetectionResult(key="disk", value=f"{free_gb} GB free", status=status, raw_data=data)

    def detect_network(self) -> DetectionResult:
        import urllib.request
        internet = False
        try:
            urllib.request.urlopen("https://api.anthropic.com", timeout=5)
            internet = True
        except Exception:
            try:
                urllib.request.urlopen("https://api.openai.com", timeout=5)
                internet = True
            except Exception:
                pass
        status = "ok" if internet else "fail"
        data = {"internet": internet}
        return DetectionResult(key="network", value="Connected" if internet else "No internet", status=status, raw_data=data)

    def detect_ollama(self) -> DetectionResult:
        import json as json_mod, urllib.request, shutil
        # Check if running
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
                data = json_mod.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                return DetectionResult(key="ollama", value=f"Running ({len(models)} models)", status="ok",
                    raw_data={"installed": True, "running": True, "models": models, "endpoint": "http://localhost:11434"})
        except Exception:
            pass
        # Check if installed
        if shutil.which("ollama"):
            return DetectionResult(key="ollama", value="Installed (not running)", status="warn",
                raw_data={"installed": True, "running": False, "models": []})
        return DetectionResult(key="ollama", value="Not installed", status="fail",
            raw_data={"installed": False, "running": False, "models": []})

    def detect_lmstudio(self) -> DetectionResult:
        import json as json_mod, urllib.request
        try:
            with urllib.request.urlopen("http://localhost:1234/v1/models", timeout=3) as resp:
                data = json_mod.loads(resp.read())
                models = [m.get("id", "") for m in data.get("data", [])]
                return DetectionResult(key="lmstudio", value=f"Running ({len(models)} models)", status="ok",
                    raw_data={"installed": True, "running": True, "models": models})
        except Exception:
            pass
        return DetectionResult(key="lmstudio", value="Not available", status="fail",
            raw_data={"installed": False, "running": False, "models": []})

    def run_full_scan(self) -> SystemProfile:
        profile = SystemProfile()
        for detect_fn in [self.detect_os, self.detect_cpu, self.detect_ram, self.detect_gpu,
                          self.detect_disk, self.detect_network, self.detect_ollama, self.detect_lmstudio]:
            try:
                result = detect_fn()
                profile.results[result.key] = result
            except Exception as exc:
                log.debug(f"detection_failed", target=detect_fn.__name__, error=str(exc))
        return profile

    def run_quick_scan(self, cache_path: Path | None = None) -> SystemProfile:
        # Use cached results for stable items, re-scan volatile items
        cached = SystemProfile.load(cache_path) if cache_path else None
        profile = SystemProfile()
        # Stable: OS, CPU, RAM, disk — use cache if available
        for key in ("os", "cpu", "ram", "disk"):
            if cached and key in cached.results:
                profile.results[key] = cached.results[key]
            else:
                detect_fn = getattr(self, f"detect_{key}")
                profile.results[key] = detect_fn()
        # Volatile: GPU state, network, Ollama, LMStudio — always re-scan
        for key in ("gpu", "network", "ollama", "lmstudio"):
            detect_fn = getattr(self, f"detect_{key}")
            try:
                profile.results[key] = detect_fn()
            except Exception:
                pass
        return profile
```

- [ ] **Step 3: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_system_detector.py -v`
Expected: All 20 tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/system/detector.py tests/unit/test_system_detector.py
git commit -m "feat: SystemDetector with 8 detection targets (CPU, RAM, GPU, disk, network, Ollama, LMStudio)"
```

---

### Task 3: Gateway Integration + REST API

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Modify: `src/jarvis/channels/config_routes.py`

- [ ] **Step 1: Initialize SystemDetector in gateway startup**

In gateway.py, near the ConversationTree initialization, add:

```python
        # System Detector (hardware profiling)
        try:
            from jarvis.system.detector import SystemDetector
            _detector = SystemDetector()
            _cache = self._config.jarvis_home / "system_profile.json"
            self._system_profile = _detector.run_quick_scan(cache_path=_cache)
            self._system_profile.save(_cache)
            log.info(
                "system_profile_detected",
                tier=self._system_profile.get_tier(),
                mode=self._system_profile.get_recommended_mode(),
                results=len(self._system_profile.results),
            )
        except Exception:
            log.debug("system_detector_failed", exc_info=True)
            self._system_profile = None
```

- [ ] **Step 2: Add REST endpoint**

In config_routes.py, near system endpoints:

```python
    @app.get("/api/v1/system/profile", dependencies=deps)
    async def get_system_profile() -> dict[str, Any]:
        """Get hardware/software system profile."""
        profile = getattr(gateway, "_system_profile", None)
        if not profile:
            return {"error": "System profile not available"}
        return profile.to_dict()

    @app.post("/api/v1/system/rescan", dependencies=deps)
    async def rescan_system() -> dict[str, Any]:
        """Force a full system re-scan."""
        try:
            from jarvis.system.detector import SystemDetector
            detector = SystemDetector()
            profile = detector.run_full_scan()
            cache = config_manager.config.jarvis_home / "system_profile.json"
            profile.save(cache)
            if gateway:
                gateway._system_profile = profile
            return profile.to_dict()
        except Exception as exc:
            return {"error": str(exc)}
```

- [ ] **Step 3: Verify**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.gateway.gateway import Gateway; print('OK')"`
Run: `python -m pytest tests/unit/ -q --tb=short` — Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/gateway/gateway.py src/jarvis/channels/config_routes.py
git commit -m "feat: SystemDetector runs on gateway startup + GET /api/v1/system/profile endpoint"
```

---

### Task 4: Flutter System Profile Page

**Files:**
- Create: `flutter_app/lib/screens/config/system_profile_page.dart`
- Modify: `flutter_app/lib/screens/config_screen.dart`
- Modify: `flutter_app/lib/l10n/app_en.arb`

- [ ] **Step 1: Add i18n keys**

In `app_en.arb`:
```json
"configPageSystemProfile": "Hardware",
"@configPageSystemProfile": {},
"systemTier": "System Tier",
"@systemTier": {},
"systemRecommendedMode": "Recommended Mode",
"@systemRecommendedMode": {},
"systemRescan": "Rescan Hardware",
"@systemRescan": {}
```

- [ ] **Step 2: Create system_profile_page.dart**

A page that calls `GET /api/v1/system/profile` and displays:
- Tier badge (minimal/standard/power/enterprise) with color
- Recommended mode
- For each detection result: key, value, status badge (green/yellow/red), expandable raw_data
- Rescan button

- [ ] **Step 3: Register in config_screen.dart**

Add to System category: `'system_profile'` with `Icons.memory` icon.

- [ ] **Step 4: Build + Analyze**

Run: `flutter gen-l10n && flutter analyze && flutter build web --release --no-tree-shake-icons`

- [ ] **Step 5: Commit**

```bash
git add flutter_app/
git commit -m "feat: Flutter System Profile page with hardware details and tier visualization"
```

---

### Task 5: Full Test Suite + Regression

- [ ] **Step 1: Run all new tests**

Run: `python -m pytest tests/unit/test_system_detector.py -v`
Expected: All 20 PASS

- [ ] **Step 2: Run all unit tests**

Run: `python -m pytest tests/unit/ -q --tb=short`
Expected: 90+ passed

- [ ] **Step 3: Ruff check**

Run: `python -m ruff check src/jarvis/system/ --select=F401,F811,F821,E501 --no-fix`

- [ ] **Step 4: Commit any fixes**

```bash
git add -A && git commit -m "fix: test adjustments for system detector"
```
