"""Container-scoped submit click for the receipt-gated send path. Exists because the ranked
interactives listing caps at 60 rows and a composer's own submit can fall off it (X's compose
modal: covered feed rows behind the overlay ate the cap, so no "Post" row ever reached the index
picker, measured live 0/2 deliveries). Scope = the dialog/form ancestor of the editable holding
the payload when there is one, else a bounded nearest-scope-first upward walk, so a page-level
opener with the same label can never be chosen. A wrong resolution still fails the send receipt
downstream, never a false delivery claim."""

import json
import re
from typing import Any, Dict, Optional

# BROAD submit vocabulary shared by the index picker (browser_agent) and the JS below, one source
# so the two tiers can never drift apart.
SEND_LABELS = frozenset({
    "send", "send now", "send message",              # LinkedIn / Gmail / DMs
    "post", "post all", "tweet", "reply",            # X / Threads compose + reply
    "publish", "comment", "share",                   # articles / YouTube+FB comments / shares
})

# Gmail names its Send button 'Send ‪(⌘Enter)‬': a shortcut suffix wrapped in bidi
# isolates that defeats exact matching. Strip control chars + any parenthesized tail before compare.
P_NAME_NOISE_RE = re.compile(r"[‪‬‎‏⁦-⁩]|\([^)]*\)")


def clean_button_name(name: str) -> str:
    return P_NAME_NOISE_RE.sub("", name or "").strip().lower()

# Resolves the submit and returns its viewport center; the caller clicks it through the REAL
# input path (BrowserClickPoint). Synthetic el.click() is ignored by web-component sites
# (shreddit live), and a real click lands on whatever is topmost, so overlays can't be fooled.
P_CONTAINER_SUBMIT_JS = r"""(() => {
  const PAYLOAD = %s;
  const LABELS = new Set(%s);
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const vis = (el) => !!el && el.getClientRects().length > 0;
  const enabled = (el) => !el.disabled && el.getAttribute('aria-disabled') !== 'true';
  // Same cleaning as clean_button_name: Gmail's Send is 'Send (⌘Enter)' in bidi isolates.
  const clean = (s) => norm((s || '').replace(/[‪‬‎‏⁦-⁩]|\([^)]*\)/g, ''));
  const labelOf = (el) => clean(el.getAttribute('aria-label') || el.textContent || '');
  const holds = (el) => ((el.value || el.textContent || '').indexOf(PAYLOAD) !== -1);
  // Shadow piercing both ways: reddit's composer AND its submit live in shreddit shadow roots.
  const deep = (root, sel, out, depth) => {
    if (depth > 10 || out.length > 4000) return out;
    let hits; try { hits = root.querySelectorAll(sel); } catch (e) { hits = []; }
    for (const el of hits) out.push(el);
    let all; try { all = root.querySelectorAll('*'); } catch (e) { return out; }
    for (const el of all) { if (el.shadowRoot) deep(el.shadowRoot, sel, out, depth + 1); }
    return out;
  };
  const up = (el) => el.parentElement || (el.getRootNode() && el.getRootNode().host) || null;
  const ed = deep(document, '[contenteditable="true"],textarea,input', [], 0)
    .find((e) => vis(e) && holds(e));
  if (!ed) return { ok: false, why: 'no editable holding the payload' };
  // Ranked, not exact-match. A closed label set resolves X's "Post" and little else: live, reddit
  // labels its submit "Post to r/test" and it scored ZERO, so the send fell through to blind-tapping
  // a coordinate. Exact match still outranks everything, so every site that resolves today resolves
  // the identical button; the weaker tiers only ever answer where the strong one found nothing.
  const VERB = /^(send|post|repl(?:y|ies)|comment|tweet|publish|share|submit)\b/;
  const rank = (b) => {
    const l = labelOf(b);
    if (LABELS.has(l)) return 3;                                       // exact: today's behaviour
    if ((b.getAttribute('type') || '').toLowerCase() === 'submit') return 2;   // the form's own submit
    if (l.length <= 40 && VERB.test(l)) return 1;                      // "post to r/test", "reply all"
    return 0;
  };
  // A DISABLED submit is not a missing one, and collapsing the two is what made this whole path
  // lie. Live on reddit: the button is right there, labelled "post", and greyed out because the
  // form still wants a title. We reported "no submit control", guessed a coordinate, and announced
  // a delivery. Keeping the blocked candidate lets the caller say the true thing instead.
  let blocked = null;
  const submitIn = (root) => {
    let best = null, bestRank = 0;
    for (const b of deep(root, 'button,[role="button"],input[type="submit"]', [], 0)) {
      if (!vis(b)) continue;
      const r = rank(b);
      if (!r) continue;
      if (!enabled(b)) { if (!blocked || r > rank(blocked)) blocked = b; continue; }
      if (r > bestRank) { bestRank = r; best = b; }
    }
    return best;
  };
  const isScope = (el) => { try { return el.matches('[role="dialog"],[role="alertdialog"],form'); } catch (e) { return false; } };
  let scope = null;
  for (let node = ed; node; node = up(node)) { if (isScope(node)) { scope = node; break; } }
  let btn = scope ? submitIn(scope) : null;
  if (!btn) {
    // Nearest-scope-first walk: X's inline submit shares an ancestor 20 hops above the Draft.js
    // editable while foreign tweets' buttons only enter at 28 (measured live), so 24 finds the
    // composer's own submit and stops before any wider scope could.
    //
    // Also the fallback when a scope WAS found and held no submit. Reddit puts its composer in a
    // <form> and its submit in a sticky action bar OUTSIDE that form, so scoping alone answered
    // "no submit control" and the whole write path degraded to a coordinate guess. Walking after a
    // barren scope cannot reach wider than the walk would have reached anyway.
    let node = up(ed);
    for (let hop = 0; node && node !== document.body && hop < 24; hop++, node = up(node)) {
      btn = submitIn(node);
      if (btn) break;
    }
  }
  if (!btn) return blocked
    ? { ok: false, disabled: true, name: labelOf(blocked),
        why: 'the submit control is present but DISABLED, so the form is not complete yet '
             + '(a required field such as a title is still empty, or the editor never registered the text)' }
    : { ok: false, why: 'no submit control in the composer container' };
  const r0 = btn.getBoundingClientRect();
  if (r0.top < 0 || r0.bottom > window.innerHeight) btn.scrollIntoView({ block: 'center' });
  const r = btn.getBoundingClientRect();
  return { ok: true, name: labelOf(btn), rank: rank(btn),
           xPct: (r.left + r.width / 2) / window.innerWidth * 100,
           yPct: (r.top + r.height / 2) / window.innerHeight * 100 };
})()"""


def container_submit_expression(payload: str) -> str:
    """The container-scoped submit click for a composer holding `payload` (prefix-matched, same
    24-char truncation the fill verifier uses)."""
    return P_CONTAINER_SUBMIT_JS % (json.dumps((payload or "")[:24]), json.dumps(sorted(SEND_LABELS)))


def parse_eval_value(res: object) -> Optional[Dict[str, Any]]:
    """The dict a BrowserEvaluate returned, or None. Unreadable shapes are None (honest miss)."""
    val: object = None
    if isinstance(res, dict) and "error" not in res:
        val = res.get("value")
        if val is None and isinstance(res.get("text"), str):
            try:
                val = json.loads(res["text"])
            except (json.JSONDecodeError, ValueError):
                val = None
    return val if isinstance(val, dict) else None


# The browser tool's own words when an index no longer resolves. Anchored on the stable half of the
# sentence ("not in the cached element map"), not the whole string, so a reworded tail doesn't
# silently turn the retry off and take the fast write path down with it.
P_STALE_INDEX_RE = re.compile(r"not in the cached element map|refresh the index", re.I)


def is_stale_index_error(res: object) -> bool:
    """Did this tool result fail because the element index went stale?

    Distinct from every other failure: a stale index means the element was THERE and the page
    re-rendered underneath us, so re-listing and retrying is correct. A genuine miss (no such
    control, refused input) must not retry, because retrying a real failure is how you double-post.
    """
    if not isinstance(res, dict):
        return False
    return bool(P_STALE_INDEX_RE.search(str(res.get("error") or "")))
