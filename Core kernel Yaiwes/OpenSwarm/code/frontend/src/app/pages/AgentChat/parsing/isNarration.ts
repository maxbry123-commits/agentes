// Is this assistant message throwaway narration, or is it the answer?
//
// The transcript folds narration that sits between two tool runs into the grey tool group, which is
// right for "Let me check that" and catastrophic for a 1,060-word memo: the deliverable vanishes
// from the card entirely, and expanding the group renders it as raw markdown source in tertiary
// grey inside a row labelled with whatever file the agent happened to read. Observed live on a real
// run, with the answer streaming in and then disappearing the instant the run completed.
//
// The two mistakes are not symmetric. Showing one redundant sentence inline costs a line of noise.
// Hiding the answer costs the user the entire run, silently, while it is marked done and billed.
// So this is deliberately biased toward "that is the answer, show it".

/** Past this, it is not a passing remark. Real narration in practice is a short sentence or two. */
const NARRATION_MAX_CHARS = 240;

// Structure means someone is presenting, not muttering: a heading, a list, a table, a code fence, a
// quote, or a horizontal rule. Any of these makes the message a deliverable regardless of length.
const STRUCTURE = /(^|\n)\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>\s|\||```|---)/;

export function isNarration(content: unknown): boolean {
  if (typeof content !== 'string') return true;
  const text = content.trim();
  if (text.length === 0) return true;
  if (text.length > NARRATION_MAX_CHARS) return false;
  return !STRUCTURE.test(text);
}
