"""
instalador_deterministico.py - 100% deterministico. Cero llamadas a LLM.
Adaptado del patron entregado en DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md
"""
import subprocess
from pathlib import Path


def instalar_componente(nombre: str, repo_url: str, carpeta_destino: Path) -> bool:
    destino = carpeta_destino / nombre
    if destino.exists():
        return True  # ya existe, no repetir (COPY-FIRST)
    try:
        subprocess.run(
            ["git", "clone", repo_url, str(destino)],
            check=True, capture_output=True, timeout=60,
        )
        req = destino / "requirements.txt"
        if req.exists():
            subprocess.run(
                ["pip", "install", "-r", str(req)],
                check=True, capture_output=True, timeout=120,
            )
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False


def verificar_existencia(nombre: str, carpeta_raiz: Path) -> bool:
    return (carpeta_raiz / nombre).exists()
