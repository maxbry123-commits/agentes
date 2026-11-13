// Onboarding is a playground, not homework: every roadmap step is freely explorable in any order. A linear FEATURE_CHAIN used to gate each step on finishing the one above it (the 🔒 "Finish the step above" teasers); that read as a chore, so the gating is gone and nothing is locked. The exported shapes are kept so the panel/roadmap callers don't change.

import { useMemo } from 'react';
import type { RootState } from '@/shared/state/store';
import { useAppSelector } from '@/shared/hooks';
import { STEPS } from './index';

export function isStepUnlocked(_stepId: string, _s: RootState): boolean {
  return true;
}

export function unlockHintFor(_stepId: string): string | null {
  return null;
}

/** Set of currently-unlocked step ids: every step, always. Selector form kept
 *  so callers' memoization is unchanged. */
export function useUnlockedStepIds(): Set<string> {
  const key = useAppSelector(() => STEPS.map((st) => st.id).join('|'));
  return useMemo(() => new Set(key ? key.split('|') : []), [key]);
}
