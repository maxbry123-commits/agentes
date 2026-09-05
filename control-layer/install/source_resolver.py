"""Instalación determinista — investigar y descargar source.
SOURCE: ley no-from-scratch · FROMTED · UOOS · CAPA DE CONTROL.
Sin source materializado → solo descarga. Nunca inventar código desde 0.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import hashlib
import json
import urllib.request

Mode = Literal["full", "sparse", "file"]


@dataclass(frozen=True)
class SourceSpec:
    url: str
    mode: Mode = "sparse"
    paths: tuple[str, ...] = ()
    expected_sha256: str | None = None
    dest: str = "sources/"
    ref: str | None = None  # branch/tag/commit


@dataclass(frozen=True)
class SourceResult:
    ok: bool
    dest_path: str
    sha256: str | None
    error: str | None = None
    manifest: dict | None = None


class SourceResolver:
    """Resuelve y descarga source de forma determinista."""

    def resolve(self, spec: SourceSpec) -> SourceResult:
        dest = Path(spec.dest)
        dest.mkdir(parents=True, exist_ok=True)

        if not spec.url:
            return SourceResult(False, str(dest), None, "missing url")

        if spec.mode == "file":
            return self._download_file(spec, dest)

        # full/sparse: escribe manifest para que el runtime haga git clone/sparse
        manifest = {
            "url": spec.url,
            "mode": spec.mode,
            "paths": list(spec.paths),
            "ref": spec.ref,
            "dest": str(dest),
        }
        man_path = dest / "source_manifest.json"
        man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return SourceResult(True, str(dest), None, None, manifest)

    def _download_file(self, spec: SourceSpec, dest: Path) -> SourceResult:
        try:
            name = spec.paths[0] if spec.paths else Path(spec.url).name
            target = dest / name
            urllib.request.urlretrieve(spec.url, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if spec.expected_sha256 and digest != spec.expected_sha256:
                return SourceResult(False, str(target), digest, "sha256 mismatch")
            return SourceResult(True, str(target), digest)
        except Exception as e:
            return SourceResult(False, str(dest), None, str(e))
