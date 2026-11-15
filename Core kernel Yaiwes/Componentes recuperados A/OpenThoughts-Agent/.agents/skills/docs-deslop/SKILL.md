---
name: docs-deslop
description: >-
  Condense and clarify an operational/research doc (SKILL.md, ops.md, tracker, README,
  agent_log) OR the COMMENTS of a launch/config YAML (.yaml/.yml) by an editor-subagent
  dispatched with fresh context and a list of file paths to review. The editor MOVES
  information to a concept-ordered taxonomy with functional subsections, then cuts
  paragraph-by-paragraph: stale gotchas + their corrections, deprecated features,
  rationalizations/justifications for actions (docs say WHAT to do, not WHY),
  partially-redundant sections, and flowery language. For YAML files: edit ONLY the `#`
  comment lines — every key, value, flag, list element, and the structural whitespace must
  stay byte-identical (the config is re-parsed as-is at launch). CONDENSE AND CLARIFY ONLY
  — never add or elaborate. Backs up every doc to ~/Documents/slop_docs/ before editing
  (dated + original filename), then leans toward OVER-condensing (backups exist). Returns
  a per-doc percent-shortened count + a brief overview of what was compressed for the
  supervisor to review. Use when docs have grown bloated/stale/repetitive, when a sweep
  flags doc bloat, or when the supervisor says "deslop these docs".
---

# docs-deslop

Condense and reorganize listed documents without adding content. Move, merge, tighten, or
cut existing material only; flag gaps for the supervisor.

## Inputs

From the dispatching supervisor you receive:

| Input | Required | Notes |
|---|---|---|
| **List of doc paths** to edit | yes | absolute or repo-relative; one or many |
| Scope constraints (optional) | no | e.g. "only the Guardrails section", "leave the worked example" — if none given, the whole doc is in scope |

Accepted file types: `.md`/`.txt` (free-form docs — edit the body), and `.yaml`/`.yml`
(config/launch files — edit ONLY the `#` comments, never the keys/values; see §2). If a
path does not exist or is none of these, report it back unchanged with a note — do not
guess or create files.

---

## 0. Back up the original (FIRST, before any edit)

**Before touching a doc, save a dated copy of the verbatim original** to
`/Users/benjaminfeuer/Documents/slop_docs/`. This is non-negotiable — the whole skill
licenses aggressive cuts on the basis that the original is recoverable.

Naming: **`<YYYY-MM-DD_HHMM>_<original-filename>`** — date+time prefix, original filename
preserved (including extension). Example: editing `ops/leonardo/ops.md` on 2026-07-08 at
14:32 → `/Users/benjaminfeuer/Documents/slop_docs/2026-07-08_1432_ops.md`.

```bash
STAMP=$(date +%Y-%m-%d_%H%M)
cp "<doc-path>" "/Users/benjaminfeuer/Documents/slop_docs/${STAMP}_$(basename "<doc-path>")"
```

Do this **once per doc**, before the first edit. If two docs share a basename, the date
prefix disambiguates them. Confirm the backup landed (the `cp` above either succeeds or
errors loudly — no silent skip).

---

## 1. First pass — reorganize (move, don't write)

Read the whole doc first, then move existing material into a concept-ordered structure.

> **For YAML files this pass is mostly a no-op:** a YAML's section order is fixed by the
> SkyRL/Hydra schema, so you cannot reorder keys/blocks. Skip to §2 (condense). The one
> reorganize action available is **promoting** a buried load-bearing comment up to sit
> next to the key it governs (e.g. a divisibility note hoisted to the top of a comment
> block above its `fsdp_size:` line).

**Order by concept, not chronology.** Preserve chronology for inherently sequential
runbooks, bring-up ladders, and retry/restart flows.

**Organize into well-organized subsections with a natural taxonomy by function.** Group
related material under a heading that names the *function* of the material (access,
invocation, gotchas, guardrails, worked examples), not the *incidents* that produced it.
Use the taxonomy already present in the repo's best docs as a template:
`When to use` → `What it does`/`Resources` → `How to invoke`/numbered procedure →
`Gotchas`/`Guardrails` → `Worked example`. Merge scattered discussions of the same topic
into one place; a reader should never have to assemble an answer from three sections.

- Move paragraphs and sections to their functional home; merge duplicate sections; promote
  buried essential facts. Do not write new connective prose.

---

## 2. Second pass — condense and clean (paragraph by paragraph)

Go through the reorganized doc **paragraph by paragraph** and cut. This is where the bulk
of the reduction happens. Lean toward **over-condensing** — the backup in `slop_docs/`
exists precisely so you can be aggressive; a doc that comes back too tight is a quick
un-edit, while one that comes back too loose wastes the whole pass.

**Candidates for removal or tightening:**

| Cut | What it looks like | Why |
|---|---|---|
| **Stale gotchas + their corrections** | "NOTE: X used to break, but the fix in commit Y…"; a whole paragraph about a bug that's long fixed and whose fix is now the normal behavior | If the corrected behavior is now the default/only path, the history is dead weight. Keep the *current* rule, drop the story of the bug. |
| **Deprecated features** | Steps/flags/paths that no longer exist or are explicitly superseded; "legacy" paths called out as legacy | If it's deprecated, describing how to use it is actively harmful. Remove unless the doc's job is a migration guide. |
| **Rationalizations + justifications** | "We do X *because*…", "the reason for this is…", paragraphs of *why* a step exists | **Docs say WHAT to do, not WHY.** Cut the rationale, keep the instruction. (The rare exception: a non-obvious rule that a reader will *violate* without understanding it — there, one clause of "why," not a paragraph.) |
| **Partially redundant sections** | Two sections that restate the same rule; a procedure that repeats a caveat already stated once globally; a worked example whose lesson already appears as a guardrail | Keep the single strongest statement; cut the rest. |
| **Flowery language** | Hedging ("it might be worth considering whether…"), throat-clearing intros/conclusions, emphatic adverbs, metaphor, rhetorical questions | Replace with the direct statement. The reader wants the rule, not the mood. |

**Condensing rules:**
- **For YAML files: edit ONLY the `#` comment lines.** Every key name, value, flag, list
  item, inline value, and the indentation/structural whitespace must remain byte-identical
  to the backup — the config is re-parsed verbatim at launch. You cut/tighten prose in
  comments; you never touch the YAML data. (This is the YAML-specific license: it lets you
  be aggressive on comments with zero risk to the experiment.) Keep any comment that is
  load-bearing — a non-obvious flag rationale a reader will violate, a divisibility/memory
  check that justifies a value, a gotcha naming a real failure mode and its fix — and cut
  the rest (history, reverted experiments, dead job numbers, "we do X because" essays).
- **Preserve every load-bearing technical fact:** exact commands, flag names, paths,
  thresholds, IDs, version numbers, the literal strings to grep for. These are the point
  of the doc. Condense the prose *around* them, never the facts themselves.
- **Preserve the doc's frontmatter** (the `---` YAML block) and top-level structure
  conventions — edit the body, not the metadata.
- **Keep code blocks and tables** unless their content is fully redundant with prose
  elsewhere (then cut the weaker of the two — usually the prose restating the table).
- **A bullet is tighter than a paragraph.** A list of conditions reads faster than the
  same conditions in sentences. Convert where it loses nothing.
- **When in doubt, cut and let the supervisor restore.** Asymmetry: an over-cut paragraph
  is a 30-second restore from the backup; an under-cut doc is a wasted dispatch.

---

## 3. Return — percent shortened + overview

For **each** doc you edited, report back to the supervisor in this shape:

```
DOCS-DESLOP — <doc-path>

Reduction: <X%> shorter   (before: <B> words/lines → after: <A>)
Backup:    /Users/benjaminfeuer/Documents/slop_docs/<stamp>_<filename>

Reorganized:
  - <1-line: what moved where, e.g. "merged three scattered 'Gotchas' mentions into one §Gotchas">
  - <1-line: concept reorders, e.g. "moved 'When to use' above 'What it does'">

Condensed / removed:
  - <1-line per category of cut, e.g. "dropped the fixed-bug history in §3 (now default behavior)">
  - "removed rationale paragraphs from the launch procedure (kept the steps)"
  - "tightened flowery intros in §1, §4"

Flagged (NOT edited — for supervisor decision):
  - <any gap you noticed but did NOT author, e.g. "§Eval references a flag --foo not defined anywhere; may need authoring">
```

The **percent-shortened** is the headline number (compute it as
`round((before − after) / before × 100)` on whichever unit — words or lines — is cleaner;
state which). The **overview** is a short list of *what categories of slop were removed*
and *what was reorganized* — enough for the supervisor to spot-check one or two cuts
against the backup without re-reading the whole doc.

If a doc came back **little changed** (< ~10% shorter), say so explicitly — that doc was
already tight, and the supervisor should know the pass found little to cut rather than
assume it was thorough. If a doc came back **much shorter** (> ~50%), flag it for closer
review — aggressive cuts warrant a second look.

---

## Guardrails

- **CONDENSE AND CLARIFY ONLY. Never add or elaborate.** This is the whole license and the
  whole constraint. You move, merge, tighten, and cut. You do not write new content. When
  you spot a genuine gap, put it in the "Flagged" section of your return — do not fill it.
- **The backup is mandatory and first.** No edit before the dated `slop_docs/` copy lands.
  The aggressive condensing in §2 is only safe because §0 ran.
- **Order by concept, not chronology** — unless the doc is inherently chronological (a
  runbook, a sequence, a ladder). When in doubt, the reader's lookup task wins over the
  author's narrative.
- **Preserve load-bearing facts.** Commands, flags, paths, thresholds, IDs, literal grep
  strings, version pins — these are non-negotiable. Condense prose, never facts.
- **For YAML: comments only, config byte-identical.** Edit `#` comment lines; never change
  a key, value, flag, list element, or structural whitespace. The parsed config must match
  the backup exactly. Verify by re-parsing both after the edit (e.g. `python -c "import
  yaml,sys; yaml.safe_load(open(sys.argv[1]))"` on each) and by diffing the keys/values.
- **One doc at a time.** Back up → reorganize → condense → report, then move to the next.
  Don't batch edits across docs (a half-edited doc is hard to reason about).
- **Don't touch frontmatter or the repo's structural conventions** (`---` YAML, `# <name>`
  H1, the `When to use` / `Gotchas` / `Guardrails` taxonomy). Edit the body within the
  existing skeleton; restructure subsections, not the doc type.
- **Over-condense, don't under-condense.** The asymmetry is deliberate: the backup makes
  over-cuts cheap to reverse; under-cuts waste the dispatch.
