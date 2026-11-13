#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request

import websearch_engine as ws

SCHEMA = "yaiwes.research.prepass.v1"
BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_REGISTRY = BASE_DIR / "source_registry.json"
DEFAULT_OUTPUT_ROOT = pathlib.Path(
    os.getenv(
        "RESEARCH_OUTPUT_ROOT",
        "/data/research-prepass" if pathlib.Path("/data").exists() else "./research-prepass-results",
    )
)

STOPWORDS = {
    "a","al","algo","como","con","contra","cual","cuando","de","del","desde","donde","el","ella","ellos",
    "en","entre","es","esta","este","esto","hacer","hacia","la","las","lo","los","mas","me","mi","no","o",
    "para","pero","por","porque","que","se","ser","si","sin","sobre","su","sus","te","tiene","tu","un","una",
    "uno","usar","y","ya","the","and","for","from","into","of","on","or","to","with","without","this","that",
    "what","when","where","which","how","use","using","make","create","agent","agente","task","tarea","plan",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/+\-]{1,79}")
QUOTE_RE = re.compile(r'["\'\x60]([^"\'\x60]{3,100})["\'\x60]')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def compact(text: str, limit: int = 700) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def read_input(file_value: str, env_name: str) -> tuple[str, str]:
    if file_value:
        p = pathlib.Path(file_value).expanduser()
        if not p.is_file():
            raise RuntimeError(f"{env_name}_FILE_NOT_FOUND:{p}")
        return p.read_text(encoding="utf-8"), str(p)
    raw = os.getenv(env_name, "")
    if raw:
        return raw, f"env:{env_name}"
    return "", ""


def terms_from(text: str, max_terms: int = 24) -> list[str]:
    seen = set()
    ranked = []

    def add(token: str, priority: int, pos: int):
        t = token.strip(".,;:()[]{}<>").strip()
        low = t.lower()
        if len(t) < 3 or low in STOPWORDS or low in seen:
            return
        if t.startswith(("http://", "https://")):
            try:
                u = urllib.parse.urlsplit(t)
                t = (u.hostname or "") + (u.path or "")
                low = t.lower()
            except Exception:
                pass
        if len(t) > 80:
            t = t[:80]
            low = t.lower()
        seen.add(low)
        ranked.append((priority, pos, t))

    pos = 0
    for m in QUOTE_RE.finditer(text):
        add(compact(m.group(1), 0, pos)
        pos += 1

    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        code_like = any(ch in tok for ch in "._/+:-") or any(ch.isdigit() for ch in tok)
        camel = any(ch.isupper() for ch in tok[1:]) and any(ch.islower() for ch in tok)
        add(tok, 1 if code_like else 2 if camel else 3, pos)
        pos += 1

    ranked.sort(key=lambda x: (x[0], x[1], x[2].lower()))
    return [x[2] for x in ranked[:max_terms]]


def build_query(input_text: str, plan_text: str = "") -> tuple[str, list[str]]:
    terms = terms_from(input_text, 20)
    existing = {x.lower() for x in terms}
    for t in terms_from(plan_text, 12):
        if t.lower() not in existing:
            terms.append(t)
            existing.add(t.lower())
        if len(terms) >= 24:
            break
    if not terms:
        normalized = compact(input_text or plan_text, 220)
        if not normalized:
            raise RuntimeError("INPUT_BLOCK_EMPTY")
        return normalized, [normalized]
    query = " ".join(terms)
    if len(query) > 280:
        query = query[:280].rsplit(" ", 1)[0]
    return query, terms


def load_registry(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "yaiwes.research.source-registry.v1":
        raise RuntimeError("SOURCE_REGISTRY_SCHEMA_INVALID")
    if len(data.get("web_sources", [])) != 10:
        raise RuntimeError("SOURCE_REGISTRY_REQUIRES_10_WEB_SOURCES")
    ids = [x.get("id") for x in data.get("web_sources", []) + data.get("direct_sources", [])]
    if len(ids) != len(set(ids)):
        raise RuntimeError("SOURCE_REGISTRY_DUPLICATE_ID")
    return data


def api_json(url: str, token: str = ""):
    headers = {"Accept": "application/json", "User-Agent": "YaiwesResearchPrepass/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=float(os.getenv("RESEARCH_TIMEOUT_SECONDS", "18"))) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def hostname_matches(url: str, domain: str, path_prefix: str = "") -> bool:
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or "").lower()
    domain = domain.lower()
    if not (host == domain or host.endswith("." + domain)):
        return False
    if path_prefix and not (p.path or "/").startswith(path_prefix):
        return False
    return True


def make_record(source: dict, title: str, url: str, snippet: str, rank: int, provider: str) -> dict:
    return {
        "source_id": source["id"],
        "source_kind": source.get("kind", ""),
        "source_weight": float(source.get("weight", 0.5)),
        "title": compact(title, 220),
        "url": ws.canon(url),
        "snippet": compact(snippet, 700),
        "rank": int(rank),
        "provider": provider,
    }


def search_web_source(source: dict, query: str, limit: int) -> list[dict]:
    scoped = f"site:{source['domain']} {query}"
    rows = ws.ddgs(scoped, max(limit * 2, limit))
    out = []
    for row in rows:
        if hostname_matches(row.url, source["domain"], source.get("path_prefix", "")):
            out.append(make_record(source, row.title, row.url, row.snippet, len(out) + 1, "ddgs"))
            if len(out) >= limit:
                break
    return out


def github_search(source: dict, query: str, limit: int) -> list[dict]:
    token = os.getenv("GITHUB_TOKEN", "").strip() or os.getenv("GH_TOKEN", "").strip()
    out = []
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={min(limit,10)}"
    data = api_json(url, token)
    for i, x in enumerate(data.get("items", [])[:limit], 1):
        snippet = f"{x.get('description') or ''} stars={x.get('stargazers_count',0)} language={x.get('language') or ''} updated={x.get('updated_at') or ''}"
        out.append(make_record(source, x.get("full_name", ""), x.get("html_url", ""), snippet, i, "github_api"))

    if token and len(out) < limit:
        remaining = limit - len(out)
        code_url = f"https://api.github.com/search/code?q={q}&per_page={min(remaining,10)}"
        try:
            code = api_json(code_url, token)
            for x in code.get("items", [])[:remaining]:
                repo = (x.get("repository") or {}).get("full_name", "")
                title = f"{repo}/{x.get('path','')}".strip("/")
                out.append(make_record(source, title, x.get("html_url", ""), "GitHub code search match", len(out) + 1, "github_code_api"))
        except Exception:
            pass
    return out[:limit]


def hf_search(source: dict, query: str, limit: int) -> list[dict]:
    token = os.getenv("HF_TOKEN", "").strip() or os.getenv("HUGGINGFACE_TOKEN", "").strip()
    out = []
    endpoints = [
        ("model", "models", "https://huggingface.co/"),
        ("dataset", "datasets", "https://huggingface.co/datasets/"),
        ("space", "spaces", "https://huggingface.co/spaces/"),
    ]
    per_kind = max(1, min(4, limit))
    for kind, endpoint, base in endpoints:
        url = "https://huggingface.co/api/" + endpoint + "?" + urllib.parse.urlencode({"search": query, "limit": per_kind})
        try:
            rows = api_json(url, token)
        except Exception:
            continue
        for x in rows[:per_kind]:
            item_id = x.get("modelId") or x.get("id") or ""
            if not item_id:
                continue
            snippet = f"{kind} downloads={x.get('downloads',0)} likes={x.get('likes',0)} updated={x.get('lastModified') or ''} pipeline={x.get('pipeline_tag') or ''}"
            out.append(make_record(source, item_id, base + item_id, snippet, len(out) + 1, "huggingface_api"))
            if len(out) >= limit:
                return out
    return out[:limit]


def overlap_score(terms: list[str], row: dict) -> int:
    hay = (row.get("title", "") + " " + row.get("snippet", "")).lower()
    return sum(1 for t in terms if len(t) >= 3 and t.lower() in hay)


def rank_records(rows: list[dict], terms: list[str]) -> list[dict]:
    merged = {}
    for row in rows:
        url = row.get("url", "")
        if not url:
            continue
        score = (
            float(row.get("source_weight", 0.5)) * 100.0
            + max(0, 14 - int(row.get("rank", 99)))
            + 2.0 * overlap_score(terms, row)
        )
        item = dict(row)
        item["score"] = round(score, 4)
        prev = merged.get(url)
        if prev is None or item["score"] > prev["score"]:
            merged[url] = item
    return sorted(merged.values(), key=lambda x: (-x["score"], x["source_id"], x["url"]))


def select_budget(rows: list[dict], budget_tokens: int, max_per_source: int):
    selected = []
    counts = {}
    used = 0
    truncated = False
    for row in rows:
        sid = row["source_id"]
        if counts.get(sid, 0) >= max_per_source:
            truncated = True
            continue
        cost = max(1, (len(row.get("title", "")) + len(row.get("url", "")) + len(row.get("snippet", "")) + 3) // 4)
        if used + cost > budget_tokens:
            truncated = True
            continue
        item = dict(row)
        item["estimated_tokens"] = cost
        selected.append(item)
        counts[sid] = counts.get(sid, 0) + 1
        used += cost
    return selected, used, truncated


def render_context(packet: dict) -> str:
    lines = [
        "# YAIWES Research Context Packet",
        "",
        f"- Input SHA256: {packet['input']['sha256']}",
        f"- Query: {packet['derived_query']}",
        "- LLM usado para investigar: no",
        f"- Context tokens estimados: {packet['estimated_context_tokens']} / {packet['budget_tokens']}",
        f"- Verdict: {packet['verdict']}",
        "",
        "## Evidencia seleccionada",
    ]
    for i, x in enumerate(packet["records"], 1):
        lines += [
            "",
            f"### {i}. [{x['source_id']}] {x['title'] or x['url']}",
            f"- URL: {x['url']}",
            f"- Provider: {x['provider']}",
            f"- Score determinista: {x['score']}",
        ]
        if x.get("snippet"):
            lines.append(f"- Evidencia: {x['snippet']}")
    lines += ["", "## Estado de fuentes", "", json.dumps(packet["source_status"], indent=2, ensure_ascii=False, sort_keys=True), ""]
    return "\n".join(lines)


def cache_valid(packet_path: pathlib.Path, input_sha: str, registry_sha: str, ttl: int) -> bool:
    if ttl <= 0 or not packet_path.is_file():
        return False
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if packet.get("input", {}).get("sha256") != input_sha:
        return False
    if packet.get("source_registry_sha256") != registry_sha:
        return False
    return (time.time() - packet_path.stat().st_mtime) <= ttl


def run(
    input_text: str,
    input_origin: str,
    plan_text: str,
    plan_origin: str,
    registry_path: pathlib.Path,
    output_root: pathlib.Path,
    limit: int,
    budget_tokens: int,
    max_per_source: int,
    cache_ttl: int,
    force: bool = False,
) -> dict:
    raw_bytes = input_text.encode("utf-8")
    input_sha = sha256_bytes(raw_bytes)
    registry = load_registry(registry_path)
    registry_sha = sha256_file(registry_path)
    query, terms = build_query(input_text, plan_text)
    plan_sha = sha256_bytes(plan_text.encode("utf-8")) if plan_text else None
    cache_key = sha256_bytes((input_sha + "|" + (plan_sha or "") + "|" + registry_sha).encode())[:20]
    run_id = "rp-" + cache_key
    out = output_root / run_id
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / "context_packet.json"

    if not force and cache_valid(packet_path, input_sha, registry_sha, cache_ttl):
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        packet["cache_state"] = "HIT"
        packet["context_packet"] = str(packet_path)
        packet["context_md"] = str(out / "context.md")
        return packet

    (out / "input_verbatim.txt").write_bytes(raw_bytes)
    if plan_text:
        (out / "plan_verbatim.txt").write_text(plan_text, encoding="utf-8")

    all_rows = []
    status = {}

    for source in registry["direct_sources"]:
        try:
            if source["adapter"] == "github_api":
                got = github_search(source, query, limit)
            elif source["adapter"] == "huggingface_hub_api":
                got = hf_search(source, query, limit)
            else:
                raise RuntimeError("UNKNOWN_DIRECT_ADAPTER")
            all_rows.extend(got)
            status[source["id"]] = {"state": "PASS" if got else "NO_RESULTS", "results": len(got)}
        except Exception as e:
            status[source["id"]] = {"state": "GAP", "detail": compact(f"{type(e).__name__}:{e}", 300)}

    for source in registry["web_sources"]:
        try:
            got = search_web_source(source, query, limit)
            all_rows.extend(got)
            status[source["id"]] = {"state": "PASS" if got else "NO_RESULTS", "results": len(got)}
        except Exception as e:
            status[source["id"]] = {"state": "GAP", "detail": compact(f"{type(e).__name__}:{e}", 300)}

    ranked = rank_records(all_rows, terms)
    selected, used, truncated = select_budget(ranked, budget_tokens, max_per_source)
    verdict = "VERIFIED_CLOSED" if selected else "NO_NEW_EVIDENCE"

    packet = {
        "schema": SCHEMA,
        "run_id": run_id,
        "cache_state": "MISS",
        "llm_used": False,
        "input": {
            "origin": input_origin,
            "path": str(out / "input_verbatim.txt"),
            "sha256": input_sha,
            "bytes": len(raw_bytes),
            "verbatim_preserved": (out / "input_verbatim.txt").read_bytes() == raw_bytes,
        },
        "plan": {
            "origin": plan_origin or None,
            "path": str(out / "plan_verbatim.txt") if plan_text else None,
            "sha256": plan_sha,
        },
        "source_registry": str(registry_path),
        "source_registry_sha256": registry_sha,
        "derived_query": query,
        "derived_terms": terms,
        "sources_requested": [x["id"] for x in registry["direct_sources"] + registry["web_sources"]],
        "source_status": status,
        "result_count_raw": len(all_rows),
        "result_count_ranked": len(ranked),
        "records": selected,
        "budget_tokens": budget_tokens,
        "estimated_context_tokens": used,
        "truncated": truncated,
        "verdict": verdict,
    }

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    context_path = out / "context.md"
    context_path.write_text(render_context(packet), encoding="utf-8")

    check = json.loads(packet_path.read_text(encoding="utf-8"))
    if check["input"]["sha256"] != input_sha or not check["input"]["verbatim_preserved"]:
        raise RuntimeError("CONTEXT_PACKET_READBACK_MISMATCH")

    packet["context_packet"] = str(packet_path)
    packet["context_md"] = str(context_path)
    return packet


def main():
    p = argparse.ArgumentParser(description="YAIWES deterministic research prepass")
    p.add_argument("--input-file", default=os.getenv("INPUT_BLOCK_FILE", ""))
    p.add_argument("--plan-file", default=os.getenv("EXECUTION_PLAN_FILE", ""))
    p.add_argument("--registry", default=os.getenv("SOURCE_REGISTRY", str(DEFAULT_REGISTRY)))
    p.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    p.add_argument("--limit", type=int, default=int(os.getenv("RESEARCH_RESULTS_PER_SOURCE", "4")))
    p.add_argument("--budget-tokens", type=int, default=int(os.getenv("CONTEXT_BUDGET_TOKENS", "5000")))
    p.add_argument("--max-per-source", type=int, default=int(os.getenv("CONTEXT_MAX_PER_SOURCE", "3")))
    p.add_argument("--cache-ttl", type=int, default=int(os.getenv("RESEARCH_CACHE_TTL_SECONDS", "21600")))
    p.add_argument("--force", action="store_true")
    a = p.parse_args()

    input_text, input_origin = read_input(a.input_file, "INPUT_BLOCK")
    if a.plan_file or os.getenv("EXECUTION_PLAN"):
        plan_text, plan_origin = read_input(a.plan_file, "EXECUTION_PLAN")
    else:
        plan_text, plan_origin = "", ""

    if not input_text:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "INPUT_BLOCK or INPUT_BLOCK_FILE required"}))
    if a.budget_tokens <= 0 or a.limit <= 0 or a.max_per_source <= 0:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "positive limit/budget/max-per-source required"}))

    try:
        result = run(
            input_text=input_text,
            input_origin=input_origin,
            plan_text=plan_text,
            plan_origin=plan_origin,
            registry_path=pathlib.Path(a.registry),
            output_root=pathlib.Path(a.output_root),
            limit=min(a.limit, 10),
            budget_tokens=a.budget_tokens,
            max_per_source=a.max_per_source,
            cache_ttl=a.cache_ttl,
            force=a.force,
        )
        print(json.dumps({
            "schema": SCHEMA,
            "run_id": result["run_id"],
            "cache_state": result["cache_state"],
            "verdict": result["verdict"],
            "context_packet": result.get("context_packet"),
            "context_md": result.get("context_md"),
            "records": len(result["records"]),
            "estimated_context_tokens": result["estimated_context_tokens"],
            "llm_used": False,
        }, ensure_ascii=False, sort_keys=True))
    except Exception as e:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "GAP", "detail": compact(f"{type(e).__name__}:{e}", 500)}))


if __name__ == "__main__":
    main()
