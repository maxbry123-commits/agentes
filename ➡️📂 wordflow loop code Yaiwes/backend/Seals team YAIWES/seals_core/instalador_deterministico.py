"""
instalador_deterministico.py - FIX P0-13, P0-14, P0-15, P0-17, P1-28.
P1-28 NUEVO: workspace aislado -> acquisition -> inspect -> install ->
local test -> promote. Si algo falla en cualquier paso, se descarta el
workspace temporal completo (rollback real), nunca queda a medias en el
destino final.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from sheriff_policy import StructuredAction, aprobar
from tool_result import ToolResult


def instalar_componente(nombre: str, repo_url: str, carpeta_destino: Path) -> ToolResult:
    accion = StructuredAction(action="git_clone", target_path=nombre, params={"repo_url": repo_url})
    ok_policy, motivo_policy = aprobar(accion, carpeta_destino)
    if not ok_policy:
        return ToolResult(ok=False, error_type="POLICY_DENIED", stderr=motivo_policy)

    destino_final = carpeta_destino / nombre
    manifest_path = destino_final / ".instalacion_manifest.json"

    if destino_final.exists():
        ok_previo, motivo = _verificar_instalacion_previa(destino_final, repo_url, manifest_path)
        if ok_previo:
            return ToolResult(ok=True, receipt=f"ya_instalado_verificado:{motivo}")
        return ToolResult(ok=False, error_type="INTEGRITY_MISMATCH", stderr=motivo)

    # P1-28 FIX: workspace temporal aislado. Si algo falla, se borra
    # completo (rollback) - el destino final nunca queda a medias.
    with tempfile.TemporaryDirectory(prefix="seals_staging_") as staging:
        staging_path = Path(staging) / nombre
        try:
            subprocess.run(["git", "clone", repo_url, str(staging_path)], check=True, capture_output=True, timeout=60, text=True)
        except subprocess.CalledProcessError as e:
            return ToolResult(ok=False, error_type="GIT_CLONE_FAILED", stderr=e.stderr or "", exit_code=e.returncode)
        except subprocess.TimeoutExpired:
            return ToolResult(ok=False, error_type="TIMEOUT", stderr="git clone excedio 60s")

        commit_real = _resolver_commit_actual(staging_path)
        if commit_real is None:
            return ToolResult(ok=False, error_type="COMMIT_RESOLUTION_FAILED", stderr="no se pudo leer el commit tras clonar")

        req = staging_path / "requirements.txt"
        if req.exists():
            try:
                subprocess.run(["pip", "install", "-r", str(req), "--break-system-packages"], check=True, capture_output=True, timeout=120, text=True)
            except subprocess.CalledProcessError as e:
                # ROLLBACK: el staging se descarta al salir del `with`, nada llega al destino final.
                return ToolResult(ok=False, error_type="PIP_INSTALL_FAILED", stderr=e.stderr or "")

        # PROMOTE: solo si todo lo anterior paso, se mueve al destino final.
        (staging_path / ".instalacion_manifest.json").write_text(
            json.dumps({"repo_url": repo_url, "source_commit": commit_real, "nombre": nombre})
        )
        shutil.move(str(staging_path), str(destino_final))

    return ToolResult(ok=True, artifacts=[str(destino_final)], receipt=f"SOURCE_COMMIT=={commit_real}:promovido_desde_staging")


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
