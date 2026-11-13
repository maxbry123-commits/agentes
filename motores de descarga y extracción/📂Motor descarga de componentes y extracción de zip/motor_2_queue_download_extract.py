#!/usr/bin/env python3
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time

SCHEMA = "yaiwes.frontend.download-extract-queue.v1"
QUEUE_FILE = pathlib.Path(os.getenv("QUEUE_FILE", "queue.json")).expanduser()
STATE_FILE = pathlib.Path(os.getenv("STATE_FILE", ".motor2-queue-state.json")).expanduser()
ENGINE_PATH = pathlib.Path(os.getenv("ENGINE_PATH", str(pathlib.Path(__file__).resolve().parent / "download_extract_engine.py"))).expanduser()
INDEX_PATH_RAW = os.getenv("INDEX_PATH", "").strip()
INDEX_PATH = pathlib.Path(INDEX_PATH_RAW).expanduser() if INDEX_PATH_RAW else None
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
LOOP_SLEEP_SECONDS = float(os.getenv("LOOP_SLEEP_SECONDS", "0"))
ITEM_DELAY_SECONDS = float(os.getenv("ITEM_DELAY_SECONDS", "2"))
RATE_LIMIT_COOLDOWN_SECONDS = float(os.getenv("RATE_LIMIT_COOLDOWN_SECONDS", "120"))
MAX_ITEMS_PER_RUN = int(os.getenv("MAX_ITEMS_PER_RUN", "0"))


def load_queue():
    data = json.loads(QUEUE_FILE.read_text())
    if isinstance(data, dict): data = data.get("queue", [])
    if not isinstance(data, list): raise RuntimeError("QUEUE_FORMAT_INVALID")
    out = []
    for i, row in enumerate(data):
        if not isinstance(row, dict) or not row.get("source_repo"):
            raise RuntimeError(f"QUEUE_ITEM_INVALID:{i}")
        item = dict(row); item.setdefault("source_ref", "HEAD"); item.setdefault("slug", item["source_repo"].rstrip("/").removesuffix(".git").split("/")[-1]); item.setdefault("publish", False)
        item["id"] = item.get("id") or f"{i+1:04d}:{item['slug']}"
        out.append(item)
    return out


def load_state(queue):
    if STATE_FILE.exists(): return json.loads(STATE_FILE.read_text())
    return {"schema": SCHEMA, "created_at": int(time.time()), "items": {x["id"]: {"status": "PENDING", "attempts": 0, "slug": x["slug"], "source_repo": x["source_repo"]} for x in queue}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, STATE_FILE)


def run_item(item):
    env = dict(os.environ)
    env.update({
        "SOURCE_REPO": item["source_repo"], "SOURCE_REF": str(item.get("source_ref", "HEAD")), "SLUG": item["slug"],
        "DEST_REPO": item.get("dest_repo", env.get("DEST_REPO", "")),
        "DEST_BRANCH": item.get("dest_branch", env.get("DEST_BRANCH", "main")),
        "DEST_ROOT": item.get("dest_root", env.get("DEST_ROOT", "")),
        "PUBLISH": "1" if item.get("publish") else "0",
    })
    p = subprocess.run([sys.executable, str(ENGINE_PATH)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = [x.strip() for x in p.stdout.splitlines() if x.strip()]
    payload = None
    for line in reversed(lines):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict): payload = obj; break
        except json.JSONDecodeError: pass
    if p.returncode != 0 or not payload:
        raise RuntimeError((p.stdout or "ENGINE_NO_JSON_OUTPUT")[-3000:])
    if payload.get("verdict") != "VERIFIED_CLOSED":
        raise RuntimeError("ENGINE_NOT_CLOSED:" + json.dumps(payload, ensure_ascii=False)[-2000:])
    return payload


def balance(state):
    rows = list(state["items"].values()); total = len(rows)
    success = [r for r in rows if r.get("status") == "VERIFIED_CLOSED"]
    download_ok = sum(1 for r in success if r.get("result", {}).get("source_commit"))
    extract_ok = sum(1 for r in success if r.get("result", {}).get("extraction_verified") is True)
    publish_ok = sum(1 for r in success if r.get("result", {}).get("publish", {}).get("verdict") == "PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED")
    failed = sum(1 for r in rows if r.get("status") == "FAILED")
    pending = total - len(success) - failed
    return {"total": total, "download_verified": download_ok, "extraction_verified": extract_ok, "published_readback_verified": publish_ok, "failed": failed, "pending": pending}


def write_index(state):
    if INDEX_PATH is None:
        return
    rows = []
    for item_id, row in sorted(state["items"].items()):
        result = row.get("result", {}); repo = row.get("source_repo", ""); slug = row.get("slug", item_id)
        source_url = repo if repo.startswith("http") else ("https://github.com/" + repo if repo else "")
        rows.append((slug, source_url, row.get("status", "PENDING"), result.get("source_commit", "")))
    text = ["# Índice de componentes open source", "", "Generado automáticamente por Motor 2 — cola descarga + extracción persistente.", "", "| Componente | Repositorio fuente | Estado | Commit fuente |", "|---|---|---|---|"]
    for slug, url, status, commit in rows:
        link = f"[{url}]({url})" if url else "—"; text.append(f"| {slug} | {link} | {status} | `{commit}` |")
    text += ["", "## Balance", "", "```json", json.dumps(balance(state), indent=2, sort_keys=True), "```", ""]
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True); INDEX_PATH.write_text("\n".join(text))


def main():
    if not QUEUE_FILE.exists() or not ENGINE_PATH.exists():
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "QUEUE_FILE or ENGINE_PATH missing"}))
    queue = load_queue(); state = load_state(queue); by_id = {x["id"]: x for x in queue}
    processed = 0
    progress = True
    while progress:
        progress = False
        for item_id, item in by_id.items():
            row = state["items"].setdefault(item_id, {"status": "PENDING", "attempts": 0, "slug": item["slug"], "source_repo": item["source_repo"]})
            if row.get("status") == "VERIFIED_CLOSED" or row.get("attempts", 0) >= MAX_RETRIES: continue
            if row.get("cooldown_until", 0) > time.time(): continue
            progress = True; row["attempts"] = row.get("attempts", 0) + 1; row["status"] = "RUNNING"; save_state(state)
            try:
                result = run_item(item); row["result"] = result; row["status"] = "VERIFIED_CLOSED"; row.pop("error", None)
            except Exception as e:
                row["error"] = str(e); row["status"] = "FAILED" if row["attempts"] >= MAX_RETRIES else "RETRY_PENDING"
                err = str(e).lower()
                if any(k in err for k in ("rate_limit", "rate limit", "secondary rate", "429")):
                    row["cooldown_until"] = int(time.time() + RATE_LIMIT_COOLDOWN_SECONDS)
                    time.sleep(RATE_LIMIT_COOLDOWN_SECONDS)
                elif row["status"] == "RETRY_PENDING":
                    time.sleep(min(5 * row["attempts"], 60))
            save_state(state); write_index(state)
            processed += 1
            if MAX_ITEMS_PER_RUN and processed >= MAX_ITEMS_PER_RUN: progress = False; break
            time.sleep(ITEM_DELAY_SECONDS + LOOP_SLEEP_SECONDS)
    b = balance(state); write_index(state)
    verdict = "VERIFIED_CLOSED" if b["pending"] == 0 and b["failed"] == 0 else "GAPS_PENDING"
    print(json.dumps({"schema": SCHEMA, "balance": b, "state_file": str(STATE_FILE), "index_path": str(INDEX_PATH) if INDEX_PATH else "", "verdict": verdict}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
