from __future__ import annotations

import asyncio
import os

from tools.docker_cli import docker_executable

DEFAULT_TIMEOUT = 600
PULL_TIMEOUT = 300  # 5 min max for pulling a single image

_pulled_images: set[str] = set()


async def image_exists(image: str) -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/docker_runner.py','step':'image_exists','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _ensure_image(image: str) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/docker_runner.py','step':'_ensure_image','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def run_container(
    image: str,
    args: list[str],
    timeout: int = DEFAULT_TIMEOUT,
    mount_path: str | None = None,
    extra_volumes: list[tuple[str, str]] | None = None,
    env_vars: dict[str, str] | None = None,
    network: str = "host",
    cap_add: list[str] | None = None,
) -> tuple[str, str, int]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/docker_runner.py','step':'run_container','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
