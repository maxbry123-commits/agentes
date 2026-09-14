from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CATEGORY_NAMES: dict[int, str] = {
    1: "multi_hop",
    2: "temporal",
    3: "open_domain",
    4: "single_hop",
    5: "adversarial",
}

_SESSION_KEY_RE = re.compile(r"^session_(\d+)$")


@dataclass
class Turn:
    speaker: str
    dia_id: str
    text: str


@dataclass
class Session:
    session_num: int
    date_time: str
    turns: list[Turn] = field(default_factory=list)


@dataclass
class LoCoMoConversation:
    sample_id: str
    speaker_a: str
    speaker_b: str
    sessions: list[Session] = field(default_factory=list)


@dataclass
class QAPair:
    question: str
    answer: str
    category: int
    evidence: list[str]
    conversation_id: str
    qa_index: int


def load_locomo(path: str | Path) -> tuple[list[LoCoMoConversation], list[QAPair]]:
    """Load LoCoMo JSON and return conversations + QA pairs."""
    data_path = Path(path)
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            samples = payload["data"]
        elif isinstance(payload.get("samples"), list):
            samples = payload["samples"]
        else:
            raise ValueError("Unsupported LoCoMo JSON object format.")
    elif isinstance(payload, list):
        samples = payload
    else:
        raise ValueError("LoCoMo file must be a JSON list or object.")

    conversations: list[LoCoMoConversation] = []
    qa_pairs: list[QAPair] = []

    for sample_idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            continue

        sample_id = str(
            sample.get("sample_id")
            or sample.get("id")
            or f"conversation_{sample_idx}"
        )
        conv_raw = sample.get("conversation", {})
        conv = _parse_conversation(sample_id, conv_raw)
        conversations.append(conv)

        qa_raw = sample.get("qa", [])
        if not isinstance(qa_raw, list):
            qa_raw = []
        for qa_idx, qa in enumerate(qa_raw):
            parsed = _parse_qa(qa, sample_id=sample_id, qa_index=qa_idx)
            if parsed is not None:
                qa_pairs.append(parsed)

    return conversations, qa_pairs


def group_qa_by_conversation(qa_pairs: list[QAPair]) -> dict[str, list[QAPair]]:
    grouped: dict[str, list[QAPair]] = {}
    for qa in qa_pairs:
        grouped.setdefault(qa.conversation_id, []).append(qa)
    return grouped


def category_name(category: int) -> str:
    return CATEGORY_NAMES.get(category, f"unknown_{category}")


def _parse_conversation(sample_id: str, conv_raw: Any) -> LoCoMoConversation:
    if not isinstance(conv_raw, dict):
        return LoCoMoConversation(sample_id=sample_id, speaker_a="", speaker_b="", sessions=[])

    speaker_a = str(conv_raw.get("speaker_a", "")).strip()
    speaker_b = str(conv_raw.get("speaker_b", "")).strip()

    session_nums: list[int] = []
    for key in conv_raw.keys():
        m = _SESSION_KEY_RE.match(str(key))
        if m:
            session_nums.append(int(m.group(1)))
    session_nums.sort()

    sessions: list[Session] = []
    for session_num in session_nums:
        turns_raw = conv_raw.get(f"session_{session_num}", [])
        date_time = str(conv_raw.get(f"session_{session_num}_date_time", "")).strip()

        turns: list[Turn] = []
        if isinstance(turns_raw, list):
            for turn_idx, turn in enumerate(turns_raw):
                if not isinstance(turn, dict):
                    continue
                speaker = str(turn.get("speaker", "")).strip()
                dia_id = str(turn.get("dia_id", f"s{session_num}_t{turn_idx}")).strip()
                text = str(turn.get("text", "")).strip()
                if not text:
                    continue
                turns.append(Turn(speaker=speaker, dia_id=dia_id, text=text))

        sessions.append(
            Session(
                session_num=session_num,
                date_time=date_time,
                turns=turns,
            )
        )

    return LoCoMoConversation(
        sample_id=sample_id,
        speaker_a=speaker_a,
        speaker_b=speaker_b,
        sessions=sessions,
    )


def _parse_qa(qa_raw: Any, sample_id: str, qa_index: int) -> QAPair | None:
    if not isinstance(qa_raw, dict):
        return None
    question = str(qa_raw.get("question", "")).strip()
    answer = str(qa_raw.get("answer", "")).strip()
    if not question:
        return None

    category = qa_raw.get("category", 0)
    try:
        category_int = int(category)
    except Exception:
        category_int = 0

    evidence_raw = qa_raw.get("evidence", [])
    evidence: list[str] = []
    if isinstance(evidence_raw, list):
        for item in evidence_raw:
            s = str(item).strip()
            if s:
                evidence.append(s)

    return QAPair(
        question=question,
        answer=answer,
        category=category_int,
        evidence=evidence,
        conversation_id=sample_id,
        qa_index=qa_index,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick LoCoMo loader sanity check.")
    parser.add_argument("path", type=str, help="Path to locomo10.json")
    args = parser.parse_args()

    conversations, qa_pairs = load_locomo(args.path)
    print(f"conversations={len(conversations)} qa_pairs={len(qa_pairs)}")
    if conversations:
        first = conversations[0]
        print(
            f"first_conversation={first.sample_id} "
            f"sessions={len(first.sessions)} "
            f"first_session_turns={len(first.sessions[0].turns) if first.sessions else 0}"
        )
