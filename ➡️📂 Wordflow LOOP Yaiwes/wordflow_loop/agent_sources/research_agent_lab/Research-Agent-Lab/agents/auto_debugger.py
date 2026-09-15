from __future__ import annotations
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.auto_debug_record import AutoDebugRecord
from tools.llm_budget import llm_budget_allows, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRouter


_TRACEBACK_PATTERN = re.compile(
    r'File\s+"([^"]+)",\s+line\s+(\d+)', re.IGNORECASE
)


class AutoDebuggerAgent(Agent):
    name = "auto_debugger"

    def __init__(self):
        super().__init__()
        self.llm_client = OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        results = state.values.get("experiment_results") or []
        failed = [r for r in results if isinstance(r, dict) and r.get("status") in ("error", "failed")]
        if not failed:
            return AgentResult(notes=["auto_debugger: no failed results to debug"])

        failed_result = failed[-1]
        experiment_id = failed_result.get("experiment_id", "unknown")
        attempt = failed_result.get("attempt", 0)
        patch_id = failed_result.get("patch_id", "")

        max_attempts = int(context.settings.get("max_debug_attempts", 3))
        if attempt >= max_attempts:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="max debug attempts reached",
                fix_description="",
            )
            return self._persist(record, state, context, experiment_id)

        enable_llm = bool(context.settings.get("enable_llm"))
        if not enable_llm:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="skipped: LLM disabled",
                fix_description="auto-debug requires --enable-llm",
            )
            return self._persist(record, state, context, experiment_id)

        patches = state.values.get("code_patches_by_experiment_id", {})
        code_patch = patches.get(experiment_id, {})
        if not code_patch:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="error: no CodePatch for experiment",
                fix_description="",
            )
            return self._persist(record, state, context, experiment_id)

        plans = state.values.get("experiment_plans", []) or []
        plan = plans[0] if plans else {}

        work_dir = Path(code_patch.get("work_dir", ""))
        error_text = failed_result.get("error_message", "")
        log_tail = failed_result.get("log_tail", "")
        combined_log = f"{error_text}\n{log_tail}"

        traceback_info, ignored_paths = self._parse_traceback(combined_log, work_dir)
        state.values["ignored_traceback_paths"] = ignored_paths

        # --- LLM path ---

        # Collect candidate files
        plan_files = plan.get("files_to_change", [])
        patch_files = [f.get("relative_path", "") for f in code_patch.get("changed_files", [])]
        traceback_files = list(traceback_info.keys()) if traceback_info else []
        candidates = list(dict.fromkeys(traceback_files + plan_files + patch_files))  # dedup, preserve order

        contexts, read_only = self._read_file_contexts(candidates, work_dir, traceback_info or {})

        # Look up route early (used by both budget and LLM call branches)
        route = ModelRouter(state.topic).route_for("paper_triage")

        # Check budget
        allowed, budget_reason = llm_budget_allows(state, context.settings)
        if not allowed:
            call_id = self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": budget_reason,
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": {},
                "error": budget_reason,
            })
            record = AutoDebugRecord(
                experiment_id=experiment_id,
                result_id=failed_result.get("result_id", ""),
                patch_id=patch_id,
                attempt_number=attempt,
                error_summary=f"skipped: {budget_reason}",
                fix_description="",
                fix_file_contents={},
                llm_call_id=call_id,
            )
            return self._persist(record, state, context, experiment_id)

        # Check route enabled (provider=offline/local/rule_based OR API key missing)
        if route.provider in {"offline", "local", "rule_based"} or not route.enabled:
            call_id = self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": "skipped_route_disabled",
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": {},
                "error": "",
            })
            record = AutoDebugRecord(experiment_id=experiment_id,
                result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="skipped: LLM route not enabled",
                fix_description="",
                fix_file_contents={},
                llm_call_id=call_id,
            )
            return self._persist(record, state, context, experiment_id)

        # No usable context (includes case of no traceback and no plan files)
        if not contexts:
            call_id = self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": "skipped_no_context",
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": {},
                "error": "",
            })
            record = AutoDebugRecord(experiment_id=experiment_id,
                result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary=error_text[:500] if error_text else "no error message",
                fix_description="no usable file context for LLM; manual review needed",
                fix_file_contents={},
                llm_call_id=call_id,
            )
            return self._persist(record, state, context, experiment_id)

        # Build prompt and call LLM
        prompt = self._build_debug_prompt(experiment_id, attempt, plan, failed_result, code_patch, contexts, read_only)
        response = self.llm_client.chat(route, prompt, temperature=0.1, max_tokens=3000)

        call_id = self._new_llm_call_id()
        fix_description = ""
        fix_file_contents: dict[str, str] = {}

        if not response.ok:
            self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": "error",
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": response.usage,
                "error": response.error,
            }, call_id)
            record = AutoDebugRecord(
                experiment_id=experiment_id,
                result_id=failed_result.get("result_id", ""),
                patch_id=patch_id,
                attempt_number=attempt,
                error_summary=f"LLM API error: {response.error}",
                fix_description="",
                fix_file_contents={},
                llm_call_id=call_id,
            )
            return self._persist(record, state, context, experiment_id)

        # API call succeeded — record usage
        record_llm_usage(state, response.usage)

        # Parse and validate LLM response
        payload = extract_json_object(response.text)
        if payload is not None:
            fix_description = str(payload.get("fix_description", ""))
            raw_fixes = payload.get("fix_file_contents")
            if isinstance(raw_fixes, dict):
                for fpath, fcontent in raw_fixes.items():
                    if not isinstance(fpath, str) or not isinstance(fcontent, str):
                        continue
                    if fpath in read_only:
                        continue  # reject overwrite of read_only_context files
                    if fpath not in candidates:
                        continue  # reject paths outside candidate list
                    if Path(fpath).is_absolute() or ".." in Path(fpath).parts:
                        continue
                    fix_file_contents[fpath] = fcontent
            self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": "ok",
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": response.usage,
                "error": "",
            }, call_id)
        else:
            self._write_llm_call_artifact(state, context.artifact_store, {
                "agent": "auto_debugger",
                "experiment_id": experiment_id,
                "result_id": failed_result.get("result_id", ""),
                "patch_id": patch_id,
                "status": "invalid_json",
                "transport_ok": True,
                "provider": route.provider,
                "model": route.model,
                "route_enabled": route.enabled,
                "usage": response.usage,
                "error": "JSON parse failed",
            }, call_id)

        record = AutoDebugRecord(
            experiment_id=experiment_id,
            result_id=failed_result.get("result_id", ""),
            patch_id=patch_id,
            attempt_number=attempt,
            error_summary=error_text[:500] if error_text else "no error message",
            fix_description=fix_description or (
                f"traceback parsed: {traceback_info}" if traceback_info
                else "no traceback found; manual review needed"
            ),
            fix_file_contents=fix_file_contents,
            llm_call_id=call_id,
        )
        return self._persist(record, state, context, experiment_id)

    def _parse_traceback(self, text: str, work_dir: Path) -> tuple[dict[str, int] | None, list[str]]:
        matches = _TRACEBACK_PATTERN.findall(text)
        if not matches:
            return None, []
        result: dict[str, int] = {}
        ignored: list[str] = []
        work_resolved = work_dir.resolve()
        for filepath, line_num in matches:
            try:
                resolved = Path(filepath).resolve()
                rel = str(resolved.relative_to(work_resolved))
                result[rel] = int(line_num)
            except ValueError:
                ignored.append(filepath)
        return (result if result else None, ignored)

    _MAX_FULL_FILE_LINES = 800
    _TRUNCATION_CONTEXT_LINES = 100

    def _read_file_contexts(self, candidates: list[str], work_dir: Path, traceback_lines: dict[str, int] | None = None) -> tuple[dict[str, str], set[str]]:
        """Read candidate files. Returns (contexts, read_only_paths).
        Files > _MAX_FULL_FILE_LINES lines are truncated around error lines
        and marked as read_only_context.
        """
        contexts: dict[str, str] = {}
        read_only: set[str] = set()
        work_resolved = work_dir.resolve()
        for rel_path in candidates:
            # Path safety validation — mirrors CodeWriter._validate_paths() inline:
            # Reject empty/whitespace paths, absolute/drive-letter paths,
            # parent traversal (..), and paths resolving outside work_dir.
            if not rel_path or rel_path != rel_path.strip():
                continue
            if Path(rel_path).is_absolute() or rel_path.startswith("/") or (len(rel_path) >= 3 and rel_path[1] == ":"):
                continue
            if ".." in Path(rel_path).parts:
                continue
            try:
                resolved = (work_dir / rel_path).resolve()
                resolved.relative_to(work_resolved)
            except ValueError:
                continue

            target = work_dir / rel_path
            if not target.exists() or not target.is_file():
                continue
            lines = target.read_text(encoding="utf-8").splitlines()
            if len(lines) <= self._MAX_FULL_FILE_LINES:
                contexts[rel_path] = "\n".join(lines)
            else:
                read_only.add(rel_path)
                err_line = (traceback_lines or {}).get(rel_path, 1)
                start = max(0, err_line - self._TRUNCATION_CONTEXT_LINES - 1)
                end = min(len(lines), err_line + self._TRUNCATION_CONTEXT_LINES)
                snippet = lines[start:end]
                contexts[rel_path] = (
                    f"[... {start} lines truncated ...]\n"
                    + "\n".join(snippet)
                    + f"\n[... {len(lines) - end} lines truncated ...]"
                )
        return contexts, read_only

    def _build_debug_prompt(
        self, experiment_id: str, attempt: int,
        plan: dict, failed: dict, patch: dict,
        contexts: dict[str, str],
        read_only: set[str],
    ) -> list[dict[str, str]]:
        topic_keywords = ", ".join(
            plan.get("files_to_change", [])[:10]
        )
        context_parts = []
        for path, content in contexts.items():
            if path in read_only:
                context_parts.append(f"--- [READ_ONLY] {path} ---\n{content}")
            else:
                context_parts.append(f"--- {path} ---\n{content}")
        context_text = "\n\n".join(context_parts)
        patch_id = patch.get("patch_id", "")
        changed_files = patch.get("changed_files", [])
        changed_summary = ", ".join(f.get("relative_path", "") for f in changed_files)
        return [
            {"role": "system", "content": (
                "You are debugging a failed experiment. Your job is to analyze the error "
                "and propose a minimal, safe fix that preserves the experiment's intent. "
                "Return exactly one JSON object with 'fix_description' (string) and "
                "'fix_file_contents' (dict mapping relative path to complete corrected file content). "
                "Only return files among the provided file contexts. "
                "If a file is marked as read_only_context in the prompt, do NOT include it "
                "in fix_file_contents — set its value to null instead. "
                "Keep fixes minimal: change only what's needed to resolve the error."
            )},
            {"role": "user", "content": (
                f"Experiment: {experiment_id} (attempt {attempt})\n"
                f"Hypothesis: {plan.get('hypothesis', 'unknown')}\n"
                f"Modification: {plan.get('modification', 'unknown')}\n"
                f"Files to change: {', '.join(plan.get('files_to_change', []))}\n"
                f"Keywords: {topic_keywords}\n"
                f"Patch: {patch_id}\n"
                f"Changed files: {changed_summary}\n\n"
                f"Error: {failed.get('error_message', '')}\n"
                f"Status: {failed.get('status', '')}\n"
                f"Command: {failed.get('run_command', '')}\n"
                f"Log tail:\n{failed.get('log_tail', '')}\n\n"
                f"File contexts:\n{context_text}"
            )},
        ]

    def _new_llm_call_id(self) -> str:
        import uuid
        return f"llm_call_{uuid.uuid4().hex[:12]}"

    def _write_llm_call_artifact(self, state, artifact_store, call_data: dict, call_id: str | None = None) -> str:
        if call_id is None:
            call_id = self._new_llm_call_id()
        artifact_store.save_json(state.run_id, "llm_calls", call_id, call_data)
        return call_id

    def _persist(self, record: AutoDebugRecord, state: ResearchState, context: AgentContext, experiment_id: str) -> AgentResult:
        record_dict = asdict(record)
        records = state.values.setdefault("last_debug_records_by_experiment_id", {})
        records[experiment_id] = record_dict
        state.values["last_debug_record"] = record_dict
        context.artifact_store.save_json(state.run_id, "auto_debug_records", record.record_id, record_dict)
        note = f"auto_debugger: experiment={experiment_id} attempt={record.attempt_number}"
        if record.error_summary:
            note = f"auto_debugger: {record.error_summary}"
        return AgentResult(
            notes=[note],
            artifacts={"auto_debug_records": [record.record_id]},
            values={
                "last_debug_record": record_dict,
                "last_debug_records_by_experiment_id": records,
            },
        )
