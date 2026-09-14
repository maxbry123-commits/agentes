/**
 * Product knowledge for the Help panel. The backend assembles it from facts that ship with the
 * build plus live facts about this install, so it can't drift the way a hardcoded prompt does.
 *
 * Two consumers, one fetch: the Ask box searches topics locally (instant, no model, works with no
 * provider connected) and the help chat gets the assembled system prompt.
 */
import { API_BASE } from '@/shared/config';
import type { HelpKnowledge } from './helpSearch';

// If the backend can't answer, the chat still has to know it is a help chat and still has to refuse
// to guess. Deliberately thin: the real facts live in the build, and claiming them from memory here
// is exactly the staleness this feature exists to kill.
export const FALLBACK_HELP_PROMPT = [
  "You are OpenSwarm's help assistant, a support chat inside the app.",
  'Your product knowledge feed is unavailable right now, so you are working without verified facts',
  'about this build. Do not guess where things are, do not invent buttons, menus, or shortcuts, and',
  'do not claim anything about known bugs.',
  'Say plainly what you cannot verify, then point the user at the Help pill (top right) for Docs and',
  'shortcuts, Talk to the team, or Report a bug. Keep answers to a couple of sentences.',
].join('\n');

let cached: HelpKnowledge | null = null;
let inFlight: Promise<HelpKnowledge | null> | null = null;

export async function loadHelpKnowledge(): Promise<HelpKnowledge | null> {
  if (cached) return cached;
  if (inFlight) return inFlight;
  inFlight = (async () => {
    try {
      const res = await fetch(`${API_BASE}/help/knowledge`);
      if (!res.ok) return null;
      cached = (await res.json()) as HelpKnowledge;
      return cached;
    } catch {
      return null;
    } finally {
      inFlight = null;
    }
  })();
  return inFlight;
}

