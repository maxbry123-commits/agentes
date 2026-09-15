"""Entry point for a new isolated YAIWES programming LOOP run.

Input can be a literal instruction or a JSON manifest with 1..100 uploaded text
files. The launcher only builds/persists run-scoped planning artifacts. It does not
execute generated code, deploy, or alter global CODE_GRAPH state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .project_intake_pipeline import InputFile, analyze_project
    from .auto_loop_builder import build_loop_documents, persist_run_documents
except ImportError:
    from project_intake_pipeline import InputFile, analyze_project  # type: ignore
    from auto_loop_builder import build_loop_documents, persist_run_documents  # type: ignore


class RunLauncherError(ValueError):
    pass


def _manifest_files(payload: Mapping[str, Any]) -> tuple[InputFile, ...]:
    raw=payload.get("files")
    if not isinstance(raw,list):
        raise RunLauncherError("MANIFEST_FILES_LIST_REQUIRED")
    files=[]
    for index,row in enumerate(raw,1):
        if not isinstance(row,Mapping):
            raise RunLauncherError("MANIFEST_FILE_MAPPING_REQUIRED")
        files.append(InputFile(
            source_id=str(row.get("source_id") or f"upload-{index:03d}"),
            filename=str(row.get("filename", "")),
            content=str(row.get("content", "")),
            provenance=str(row.get("provenance") or f"manifest:{index}"),
        ))
    return tuple(files)


def launch_run(
    *,
    instruction: str,
    project_id: str,
    profile: str,
    run_id: str,
    authorized_root: Path,
    manifest: Mapping[str, Any] | None = None,
    mutation_authorized: bool = False,
) -> Path:
    instruction=instruction.strip()
    if not instruction:
        raise RunLauncherError("INSTRUCTION_REQUIRED")
    if manifest is None:
        if not project_id.strip():
            raise RunLauncherError("PROJECT_ID_REQUIRED_FOR_LITERAL_INPUT")
        files=(InputFile(
            source_id="literal-instruction-001",
            filename="instructions.md",
            content=f"# {project_id.strip()}\n\n{instruction}\n",
            provenance="literal-user-instruction",
        ),)
    else:
        files=_manifest_files(manifest)
        if not project_id.strip():
            project_id=str(manifest.get("project_id", "")).strip()
        if profile == "general" and str(manifest.get("profile", "")).strip():
            profile=str(manifest.get("profile")).strip().lower()

    intake=analyze_project(files,profile=profile,project_hint=project_id)
    documents=build_loop_documents(intake=intake,instruction=instruction,run_id=run_id)
    return persist_run_documents(
        authorized_root=authorized_root,
        run_id=run_id,
        documents=documents,
        mutation_authorized=mutation_authorized,
    )


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--project-id", default="")
    parser.add_argument("--profile", choices=("backend","frontend","general"), default="general")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--authorized-root", required=True)
    parser.add_argument("--manifest", default="")
    parser.add_argument("--mutation-authorized", action="store_true")
    args=parser.parse_args()
    manifest=None
    if args.manifest:
        value=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        if not isinstance(value,Mapping):
            raise RunLauncherError("MANIFEST_OBJECT_REQUIRED")
        manifest=value
    out=launch_run(
        instruction=args.instruction,
        project_id=args.project_id,
        profile=args.profile,
        run_id=args.run_id,
        authorized_root=Path(args.authorized_root),
        manifest=manifest,
        mutation_authorized=args.mutation_authorized,
    )
    print("YAIWES_RUN_READY="+str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
