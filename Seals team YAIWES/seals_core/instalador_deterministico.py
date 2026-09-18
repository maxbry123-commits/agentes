"""
instalador_deterministico.py - FIX P0-13, P0-14, P0-15, P0-17 (auditoria 5x).
P0-13: se resuelve y registra el commit exacto tras el clone.
P0-14: directorio existente ya NO equivale a instalado - se verifica
       source_commit registrado + integridad.
P0-15: pasa por sheriff_policy.aprobar() ANTES de tocar el filesystem.
P0-17: devuelve ToolResult tipado, nunca un bool plano que oculte el error.
"""
import json
import subprocess
from pathlib import Path

from sheriff_policy import StructuredAction, aprobar
from tool_result import ToolResult


def instalar_componente(nombre: str, repo_url: str, carpeta_destino: Path) -> ToolResult:
    accion = StructuredAction(action="git_clone", target_path=nombre, params={"repo_url": repo_url})
    ok_policy, motivo_policy = aprobar(accion, carpeta_destino)
    if not ok_policy:
        return ToolResult(ok=False, error_type="POLICY_DENIED", stderr=motivo_policy)

    destino = carpeta_destino / nombre
    manifest_path = destino / ".instalacion_manifest.json"

    if destino.exists():
        ok_previo, motivo = _verificar_instalacion_previa(destino, repo_url, manifest_path)
        if ok_previo:
            return ToolResult(ok=True, receipt=f"ya_instalado_verificado:{motivo}")
        return ToolResult(ok=False, error_type="INTEGRITY_MISMATCH", stderr=motivo)

    try:
        subprocess.run(["git", "clone", repo_url, str(destino)], check=True, capture_output=True, timeout=60, text=True)
    except subprocess.CalledProcessError as e:
        return ToolResult(ok=False, error_type="GIT_CLONE_FAILED", stderr=e.stderr or "", exit_code=e.returncode)
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, error_type="TIMEOUT", stderr="git clone excedio 60s")

    commit_real = _resolver_commit_actual(destino)
    if commit_real is None:
        return ToolResult(ok=False, error_type="COMMIT_RESOLUTION_FAILED", stderr="no se pudo leer el commit tras clonar")

    manifest = {"repo_url": repo_url, "source_commit": commit_real, "nombre": nombre}
    manifest_path.write_text(json.dumps(manifest))

    req = destino / "requirements.txt"
    if req.exists():
        try:
            subprocess.run(["pip", "install", "-r", str(req), "--break-system-packages"], check=True, capture_output=True, timeout=120, text=True)
        except subprocess.CalledProcessError as e:
            return ToolResult(ok=False, error_type="PIP_INSTALL_FAILED", stderr=e.stderr or "", artifacts=[str(destino)])

    return ToolResult(ok=True, artifacts=[str(destino)], receipt=f"SOURCE_COMMIT=={commit_real}")


def _resolver_commit_actual(destino: Path) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(destino), "rev-parse", "HEAD"], check=True, capture_output=True, timeout=15, text=True)
        return proc.stdout.strip()
    except Exception:
        return None


def _verificar_instalacion_previa(destino: Path, repo_url: str, manifest_path: Path) -> tuple[bool, str]:
    if not manifest_path.exists():
        return False, "SIN_MANIFEST_DIRECTORIO_SOSPECHOSO"
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception:
        return False, "MANIFEST_CORRUPTO"
    if manifest.get("repo_url") != repo_url:
        return False, f"REPO_DISTINTO_AL_ESPERADO:{manifest.get('repo_url')}"
    commit_actual = _resolver_commit_actual(destino)
    if commit_actual is None:
        return False, "NO_SE_PUDO_VERIFICAR_COMMIT_ACTUAL"
    if commit_actual != manifest.get("source_commit"):
        return False, f"COMMIT_DIVERGIO:esperado={manifest.get('source_commit')}:actual={commit_actual}"
    return True, f"source_commit={commit_actual}"


def verificar_existencia(nombre: str, carpeta_raiz: Path) -> ToolResult:
    existe = (carpeta_raiz / nombre).exists()
    if not existe:
        return ToolResult(ok=False, error_type="NOT_FOUND", stderr=f"{nombre} no existe")
    return ToolResult(ok=True, artifacts=[str(carpeta_raiz / nombre)])
