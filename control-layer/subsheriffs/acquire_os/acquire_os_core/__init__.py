"""ACQUIRE-OS v1 — motor genérico de 28 nodos, dirigido por Recipe.

Uso:
    from acquire_os_core.core import main
    ctx = main(recipe, checkout_path, work_root)

`recipe` es un dict con el schema definido en A3/A4 (source_type, pin,
toolchain, dependencies, build, install, verify). Este paquete no
contiene ningún dato específico de OpenClaw ni de ningún otro software
— eso vive exclusivamente en la Recipe que entrega Discovery (T-005).
"""
from acquire_os_core.core import main

__all__ = ["main"]
__version__ = "2.0.0"
