"""Docker container lifecycle actions (Kali / Metasploit / MobSF / pull)."""
import asyncio

from core import logger as log


async def _do_start_kali():
    from tools import kali_runner
    log.tool_call("start_kali", {})
    ok, msg = await kali_runner.ensure_running()
    result = (
        f"Kali container ready at {kali_runner.KALI_API} ({msg})"
        if ok else f"Failed to start Kali container: {msg}"
    )
    log.tool_result("start_kali", result)
    return result


async def _do_stop_kali():
    from tools import kali_runner
    log.tool_call("stop_kali", {})
    result = await kali_runner.stop()
    log.tool_result("stop_kali", result)
    return result


async def _do_start_metasploit():
    from tools import metasploit_runner
    log.tool_call("start_metasploit", {})
    ok, msg = await metasploit_runner.ensure_running()
    result = (
        f"Metasploit container ready at {metasploit_runner.MSF_API} ({msg})"
        if ok else f"Failed to start Metasploit container: {msg}"
    )
    log.tool_result("start_metasploit", result)
    return result


async def _do_stop_metasploit():
    from tools import metasploit_runner
    log.tool_call("stop_metasploit", {})
    result = await metasploit_runner.stop()
    log.tool_result("stop_metasploit", result)
    return result


async def _do_start_mobsf():
    from tools import mobsf_runner
    log.tool_call("start_mobsf", {})
    ok, msg = await mobsf_runner.ensure_running()
    result = (
        f"MobSF container ready at {mobsf_runner.MOBSF_API} ({msg}) — "
        f"run scan(tool='mobsf', target='/path/app.apk')."
        if ok else f"Failed to start MobSF container: {msg}"
    )
    log.tool_result("start_mobsf", result)
    return result


async def _do_stop_mobsf():
    from tools import mobsf_runner
    log.tool_call("stop_mobsf", {})
    result = await mobsf_runner.stop()
    log.tool_result("stop_mobsf", result)
    return result


async def _do_pull_images():
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'mcp_server/session_tools/containers.py','step':'_do_pull_images','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
