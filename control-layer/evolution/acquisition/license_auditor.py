"""S27 · License Auditor · 100% determinista."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ALLOWED = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0", "Unlicense", "0BSD"}
COPYLEFT_DIRECTOR = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0"}
SPDX_HINTS = {"mit": "MIT", "apache": "Apache-2.0", "bsd-3": "BSD-3-Clause", "bsd-2": "BSD-2-Clause", "isc": "ISC", "mpl": "MPL-2.0", "gpl-3": "GPL-3.0", "gpl-2": "GPL-2.0", "agpl": "AGPL-3.0"}

@dataclass
class LicenseVerdict:
    spdx: str
    veredicto: str
    evidence_path: str
    raw_snippet: str = ""
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class LicenseAuditor:
    def audit(self, root: str | Path) -> LicenseVerdict:
        root_p = Path(root)
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE"):
            c = root_p / name
            if c.exists():
                text = c.read_text(encoding="utf-8", errors="ignore")[:4000]
                return self._classify(text, str(c))
        for name in ("pyproject.toml", "package.json", "setup.py"):
            p = root_p / name
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="ignore")[:3000]
                if "license" in text.lower():
                    return self._classify(text, str(p))
        return LicenseVerdict("UNKNOWN", "STOP", "", "no_license_file")

    def _classify(self, text: str, path: str) -> LicenseVerdict:
        low = text.lower()
        spdx = "UNKNOWN"
        for hint, val in SPDX_HINTS.items():
            if hint in low:
                spdx = val
                break
        if "permission is hereby granted" in low and "mit" in low:
            spdx = "MIT"
        if "apache license" in low:
            spdx = "Apache-2.0"
        if spdx in ALLOWED:
            return LicenseVerdict(spdx, "PASS", path, text[:120])
        if spdx in COPYLEFT_DIRECTOR:
            return LicenseVerdict(spdx, "DIRECTOR", path, text[:120])
        return LicenseVerdict(spdx, "STOP" if spdx == "UNKNOWN" else "DIRECTOR", path, text[:120])
