"""状态检查路由 — 环境探测 + LLM 连接验证。"""
import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/status", tags=["status"])
logger = logging.getLogger(__name__)

# 缓存最近一次探测结果（进程级，会话间复用）
_cached_probe: Optional[dict] = None
_cached_llm_test: Optional[dict] = None


@router.get("/env")
async def get_env_status():
    """获取 Kali 环境探测结果（已缓存则直接返回）。"""
    global _cached_probe
    if _cached_probe is not None:
        return _cached_probe

    try:
        from utils.env_probe import probe_environment
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, probe_environment)
        if result:
            _cached_probe = {
                "status": "ok",
                "tools_found": result.get("tools_found", []),
                "tools_missing": result.get("tools_missing", []),
                "py_modules_found": result.get("py_modules_found", []),
                "py_modules_missing": result.get("py_modules_missing", []),
                "network": result.get("network", {}),
                "os_info": result.get("os_info", "").strip(),
            }
        else:
            _cached_probe = {"status": "unavailable", "detail": "SSH 未配置或无法连接"}
        return _cached_probe
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/env/refresh")
async def refresh_env():
    """强制重新探测环境。"""
    global _cached_probe
    _cached_probe = None
    return await get_env_status()


@router.post("/llm")
async def test_llm():
    """测试所有 LLM 端点连通性。结果缓存 60s。"""
    global _cached_llm_test
    if _cached_llm_test and (time.time() - _cached_llm_test.get("_ts", 0) < 60):
        return _cached_llm_test

    try:
        import litellm
    except ImportError:
        return {"status": "error", "detail": "litellm 未安装"}

    from config import Config
    cfg = Config.load_config()
    llm_configs = cfg.get("llm", {})

    results = {}
    prompt = "Reply 'OK' only, nothing else."
    timeout_sec = 10

    for name, llm_cfg in llm_configs.items():
        model = llm_cfg.get("model", "?")
        api_key = llm_cfg.get("api_key", "")
        api_base = llm_cfg.get("api_base", "")

        if not api_key:
            results[name] = {"model": model, "status": "skip", "detail": "未配置 api_key"}
            continue

        try:
            if name == "embedding":
                loop = asyncio.get_event_loop()
                start = time.time()

                def _test_embed():
                    return litellm.embedding(
                        model=model, api_key=api_key, api_base=api_base,
                        input=["test"], timeout=timeout_sec,
                    )

                await loop.run_in_executor(None, _test_embed)
                elapsed = time.time() - start
                results[name] = {"model": model, "status": "pass", "elapsed_s": round(elapsed, 2)}
            else:
                loop = asyncio.get_event_loop()
                start = time.time()

                def _test_completion():
                    return litellm.completion(
                        model=model, api_key=api_key, api_base=api_base,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=timeout_sec, max_tokens=5,
                    )

                await loop.run_in_executor(None, _test_completion)
                elapsed = time.time() - start
                results[name] = {"model": model, "status": "pass", "elapsed_s": round(elapsed, 2)}
        except Exception as e:
            results[name] = {"model": model, "status": "fail", "detail": str(e)[:200]}

    _cached_llm_test = {"_ts": time.time(), "results": results}
    return _cached_llm_test


@router.get("/mcp")
async def get_mcp_status():
    """获取 MCP 服务连接状态。"""
    from config import Config
    cfg = Config.load_config()
    mcp_servers = cfg.get("mcp_server", {})
    if not mcp_servers:
        return {"servers": [], "total": 0}

    results = []
    for name, svc_cfg in mcp_servers.items():
        results.append({
            "name": name,
            "type": svc_cfg.get("type", "?"),
            "lazy": svc_cfg.get("lazy", False),
            "command": (svc_cfg.get("command", "") + " " + " ".join(svc_cfg.get("args", [])))[:120],
            "auto_activate": svc_cfg.get("auto_activate_for", []),
            "status": "configured",
        })
    return {"servers": results, "total": len(results)}
