"""连接测试脚本 — 验证 LLM / SSH / MCP 服务是否可用。

    python test_llm.py                     测试全部
    python test_llm.py --timeout 10        自定义超时（秒）
    python test_llm.py --skip-ssh          跳过 SSH 连接测试
    python test_llm.py --skip-mcp         跳过 MCP 服务测试
"""

import json
import sys
import time
import argparse

try:
    import litellm
except ImportError:
    print("[FAIL] litellm 未安装，请运行: pip install litellm")
    sys.exit(1)

CONFIG_PATH = "config.json"
TEST_PROMPT = "回复 'OK'，只回复这两个字母，不要回复其他内容。"


#

def load_full_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[FAIL] 找不到配置文件: {CONFIG_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[FAIL] 配置文件 JSON 解析错误: {e}")
        sys.exit(1)


def test_completion(name: str, cfg: dict, timeout: int) -> bool:
    model = cfg.get("model", "unknown")
    api_base = cfg.get("api_base", "")
    api_key = cfg.get("api_key", "")

    if not api_key:
        print(f"  [SKIP] {name} ({model}) — 未配置 api_key")
        return True

    try:
        start = time.time()
        response = litellm.completion(
            model=model,
            api_key=api_key,
            api_base=api_base,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            timeout=timeout,
            max_tokens=5,
        )
        elapsed = time.time() - start
        content = response.choices[0].message.content.strip()
        print(f"  [PASS] {name} ({model}) — {elapsed:.1f}s, 响应: {content}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name} ({model}) — {e}")
        return False


def test_embedding(name: str, cfg: dict, timeout: int) -> bool:
    model = cfg.get("model", "unknown")
    api_base = cfg.get("api_base", "")
    api_key = cfg.get("api_key", "")

    if not api_key:
        print(f"  [SKIP] {name} ({model}) — 未配置 api_key")
        return True

    try:
        start = time.time()
        response = litellm.embedding(
            model=model,
            api_key=api_key,
            api_base=api_base,
            input=["connection test"],
            timeout=timeout,
        )
        elapsed = time.time() - start
        dim = len(response.data[0]["embedding"]) if response.data else "?"
        print(f"  [PASS] {name} ({model}) — {elapsed:.1f}s, 维度: {dim}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name} ({model}) — {e}")
        return False



def test_ssh(config: dict, timeout: int) -> bool:
    ssh_cfg = config.get("tool_config", {}).get("ssh_shell", {})
    if not ssh_cfg:
        print("  [SKIP] 未配置 ssh_shell")
        return True

    host = ssh_cfg.get("host", "127.0.0.1")
    port = ssh_cfg.get("port", 22)
    username = ssh_cfg.get("username", "")
    password = ssh_cfg.get("password", "")

    if not username:
        print("  [SKIP] SSH 未配置 username")
        return True

    print(f"  [TEST] SSH {username}@{host}:{port} ...")

    try:
        import paramiko
    except ImportError:
        print("  [FAIL] paramiko 未安装，请运行: pip install paramiko")
        return False

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=min(timeout, 10),
            allow_agent=False,
            look_for_keys=False,
        )
        _, stdout, stderr = client.exec_command("echo OK", timeout=5)
        output = stdout.read().decode("utf-8", errors="replace").strip()
        if output == "OK":
            print(f"  [PASS] SSH 连接成功 — {username}@{host}:{port}")
            return True
        else:
            print(f"  [FAIL] SSH echo 测试异常 — 输出: {output}")
            return False
    except Exception as e:
        print(f"  [FAIL] SSH 连接失败 — {username}@{host}:{port}: {e}")
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass



def test_mcp(config: dict, timeout: int) -> bool:
    mcp_servers = config.get("mcp_server", {})
    if not mcp_servers:
        print("  [SKIP] 未配置 mcp_server")
        return True

    all_ok = True
    for server_name, server_cfg in mcp_servers.items():
        comm_mode = server_cfg.get("type", "http")
        print(f"  [TEST] MCP [{server_name}] mode={comm_mode} ...")

        if comm_mode == "http":
            ok = _test_mcp_http(server_name, server_cfg, timeout)
        elif comm_mode == "stdio":
            ok = _test_mcp_stdio(server_name, server_cfg, timeout)
        else:
            print(f"  [WARN] MCP [{server_name}] 不支持的通信模式: {comm_mode}")
            ok = True

        if not ok:
            all_ok = False

    return all_ok


def _test_mcp_http(name: str, cfg: dict, timeout: int) -> bool:
    url = cfg.get("url", "")
    if not url:
        print(f"  [FAIL] MCP [{name}] 缺少 url 配置")
        return False

    auth_token = cfg.get("auth_token", "")
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        import requests
    except ImportError:
        print("  [FAIL] requests 未安装，请运行: pip install requests")
        return False

    try:
        # 1) 列出工具
        resp = requests.get(
            f"{url}/tools",
            headers=headers,
            timeout=min(timeout, 10),
        )
        resp.raise_for_status()
        tools_data = resp.json()
        tools = tools_data if isinstance(tools_data, list) else []
        tool_count = len(tools)

        # 2) 冒烟测试：实际调用一个安全工具
        safe_tool = _pick_safe_tool(tools)
        invoked_name = ""
        invoke_ok = True
        invoke_detail = ""
        if safe_tool:
            invoked_name = _tool_name(safe_tool)
            try:
                call_resp = requests.post(
                    f"{url}/tools/{invoked_name}",
                    json={},
                    headers=headers,
                    timeout=min(timeout, 10),
                )
                if call_resp.status_code < 500:
                    invoke_detail = str(call_resp.json() if call_resp.text else "(空)")[:80]
                else:
                    invoke_ok = False
                    invoke_detail = f"HTTP {call_resp.status_code}"
            except Exception as exc:
                invoke_ok = False
                invoke_detail = str(exc)[:80]

        if invoked_name:
            if invoke_ok:
                print(f"  [PASS] MCP [{name}] HTTP 连接成功 — {url}, {tool_count} 工具, 冒烟 [{invoked_name}] → {invoke_detail}")
            else:
                print(f"  [PASS] MCP [{name}] HTTP 连接成功 — {url}, {tool_count} 工具")
                print(f"  [WARN] MCP [{name}] 工具列表可用，但调用 [{invoked_name}] 失败: {invoke_detail}")
                return False
        else:
            print(f"  [PASS] MCP [{name}] HTTP 连接成功 — {url}, {tool_count} 工具 (无工具可冒烟测试)")
        return True
    except Exception as e:
        print(f"  [FAIL] MCP [{name}] HTTP 连接失败 — {url}: {e}")
        return False


def _pick_safe_tool(tools) -> dict | None:
    """从工具列表中选一个只读类工具用于冒烟测试，避免副作用"""
    safe_keywords = ["list", "status", "check", "get", "info", "read", "ping", "health"]
    for tool in tools:
        name = tool.name if hasattr(tool, "name") else tool.get("name", "")
        if any(kw in name.lower() for kw in safe_keywords):
            return tool
    return tools[0] if tools else None


def _tool_name(tool) -> str:
    return tool.name if hasattr(tool, "name") else tool.get("name", "unknown")


def _test_mcp_stdio(name: str, cfg: dict, timeout: int) -> bool:
    command = cfg.get("command", "")
    if not command:
        print(f"  [FAIL] MCP [{name}] 缺少 command 配置")
        return False

    args = cfg.get("args", [])
    print(f"  [INFO] MCP [{name}] 启动: {command} {' '.join(args)}")

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import asyncio
    except ImportError:
        print("  [FAIL] mcp 库未安装，请运行: pip install mcp")
        return False

    async def _try_stdio_connect():
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_resp = await session.list_tools()
                tools = tools_resp.tools
                tool_count = len(tools)

                # 冒烟测试：实际调用一个安全工具验证端到端可用
                safe_tool = _pick_safe_tool(tools)
                invoke_result = None
                if safe_tool:
                    try:
                        invoke_result = await session.call_tool(
                            _tool_name(safe_tool), arguments={}
                        )
                    except Exception as exc:
                        invoke_result = f"调用失败: {exc}"

                return tool_count, _tool_name(safe_tool) if safe_tool else None, invoke_result

    try:
        tool_count, invoked_name, invoke_result = asyncio.run(asyncio.wait_for(
            _try_stdio_connect(), timeout=min(timeout, 15)
        ))
        status = f"  [PASS] MCP [{name}] stdio 连接成功 — {tool_count} 个工具"
        if invoked_name:
            if isinstance(invoke_result, str) and invoke_result.startswith("调用失败"):
                # 连接/列表 OK，但实际调用失败
                print(status)
                print(f"  [WARN] MCP [{name}] 工具列表可用，但调用 [{invoked_name}] 失败: {invoke_result}")
                return False
            else:
                # 截短输出用于显示
                result_preview = str(invoke_result)[:80] if invoke_result else "(空)"
                print(f"{status}, 冒烟 [{invoked_name}] → {result_preview}")
        else:
            print(f"{status} (无工具可冒烟测试)")
        return True
    except asyncio.TimeoutError:
        print(f"  [FAIL] MCP [{name}] stdio 连接超时")
        return False
    except Exception as e:
        print(f"  [FAIL] MCP [{name}] stdio 连接失败 — {e}")
        return False



def main():
    parser = argparse.ArgumentParser(description="CTF Agent 连接测试")
    parser.add_argument("--timeout", type=int, default=15,
                        help="单次请求超时秒数 (默认 15)")
    parser.add_argument("--skip-ssh", action="store_true",
                        help="跳过 SSH 连接测试")
    parser.add_argument("--skip-mcp", action="store_true",
                        help="跳过 MCP 服务测试")
    args = parser.parse_args()

    config = load_full_config()
    llm_configs = config.get("llm", {})

    if not llm_configs:
        print("[FAIL] config.json 中未配置 llm 字段")
        sys.exit(1)

    results: dict[str, bool] = {}
    embedding_keys = {"embedding"}

    # ── 第 1 组: LLM 端点 ──
    print(f"====== LLM 端点测试 ({len(llm_configs)} 个, 超时 {args.timeout}s) ======\n")
    for name, cfg in llm_configs.items():
        if name in embedding_keys:
            results[f"LLM:{name}"] = test_embedding(name, cfg, args.timeout)
        else:
            results[f"LLM:{name}"] = test_completion(name, cfg, args.timeout)

    # ── 第 2 组: SSH ──
    if not args.skip_ssh:
        print(f"\n====== SSH 连接测试 ======\n")
        results["SSH"] = test_ssh(config, args.timeout)

    # ── 第 3 组: MCP ──
    if not args.skip_mcp:
        mcp_servers = config.get("mcp_server", {})
        if mcp_servers:
            print(f"\n====== MCP 服务测试 ({len(mcp_servers)} 个) ======\n")
        results["MCP"] = test_mcp(config, args.timeout)

    # ── 汇总 ──
    print()
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    all_ok = all(results.values())

    if all_ok:
        print(f"全部通过 ({passed}/{total}) — 可以启动项目")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"通过 {passed}/{total}，失败: {', '.join(failed)}")
        print("请检查相关服务的配置是否正确、网络是否可达。")
        sys.exit(1)


if __name__ == "__main__":
    main()
