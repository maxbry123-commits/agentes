from __future__ import annotations

from dataclasses import dataclass

from scripts.eval.locomo_loader import LoCoMoConversation


@dataclass
class Chunk:
    text: str
    session_num: int
    conversation_id: str
    dia_ids: list[str]


def chunk_conversation(
    conv: LoCoMoConversation,
    max_chunk_chars: int = 1024,
) -> list[Chunk]:
    """Split one conversation into chunk list by session then turn boundaries."""
    chunks: list[Chunk] = []

    for session in conv.sessions:
        header = f"[{session.date_time}]\n" if session.date_time else ""

        current_lines: list[str] = []
        current_dia_ids: list[str] = []
        current_len = len(header)

        def flush() -> None:
            nonlocal current_lines, current_dia_ids, current_len
            if not current_lines:
                return
            body = "\n".join(current_lines)
            text = f"{header}{body}" if header else body
            chunks.append(
                Chunk(
                    text=text,
                    session_num=session.session_num,
                    conversation_id=conv.sample_id,
                    dia_ids=list(current_dia_ids),
                )
            )
            current_lines = []
            current_dia_ids = []
            current_len = len(header)

        for turn in session.turns:
            line = f"{turn.speaker}: {turn.text}".strip()
            # +1 for the newline that will be inserted when joining lines.
            addition = len(line) + (1 if current_lines else 0)

            if current_lines and (current_len + addition > max_chunk_chars):
                flush()

            # If one single turn is extremely long, keep it intact in one chunk
            # instead of splitting inside the turn.
            current_lines.append(line)
            current_dia_ids.append(turn.dia_id)
            current_len += len(line) + (1 if len(current_lines) > 1 else 0)

        flush()

    return chunks


if __name__ == "__main__":
    import argparse

    from scripts.eval.locomo_loader import load_locomo

    parser = argparse.ArgumentParser(description="Quick LoCoMo chunker sanity check.")
    parser.add_argument("path", type=str, help="Path to locomo10.json")
    parser.add_argument("--max-chars", type=int, default=1024)
    args = parser.parse_args()

    conversations, _ = load_locomo(args.path)
    if not conversations:
        raise SystemExit("No conversations found.")
    chunks = chunk_conversation(conversations[0], max_chunk_chars=args.max_chars)
    print(f"conversation={conversations[0].sample_id} chunks={len(chunks)}")
    if chunks:
        print("first chunk preview:")
        print(chunks[0].text[:300])
