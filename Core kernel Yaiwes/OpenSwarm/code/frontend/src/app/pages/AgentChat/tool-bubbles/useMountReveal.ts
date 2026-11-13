import { useEffect, useState } from 'react';

/**
 * Reliable mount-reveal for elements that should slide+fade in once when they
 * first appear. Returns an sx fragment to spread onto the element.
 *
 * Why this instead of a CSS `@keyframes ... animation`: a mount-time keyframe
 * fires at most once and silently no-ops in several real cases here (Emotion
 * injects the keyframe in the same pass the element mounts; the tool bubble
 * briefly exists as its streaming twin first; a same-frame re-render with the
 * same animation-name won't restart it). That's why tool bubbles read as
 * "appears out of nowhere" while the JS-driven streamed text feels smooth.
 *
 * This is the same robustness class as the text reveal: render hidden, then on
 * the NEXT frame flip to shown with a CSS *transition*. A transition always
 * runs when the property value changes, and the rAF flip guarantees a change
 * after the first paint, so the reveal can't be skipped. Transform+opacity only,
 * so it rides the compositor and never nudges layout or scroll.
 */
export function useMountReveal(durationMs = 280, travelPx = 10) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const r = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(r);
  }, []);
  // No willChange: transform/opacity already composite in Chromium, and a permanent willChange would pin every tool bubble to its own layer for the life of a long transcript. The one-frame promotion hitch is imperceptible for a mount fade.
  return {
    opacity: shown ? 1 : 0,
    transform: shown ? 'translateY(0)' : `translateY(${travelPx}px)`,
    transition: `opacity ${durationMs}ms cubic-bezier(0.22, 1, 0.36, 1), transform ${durationMs}ms cubic-bezier(0.22, 1, 0.36, 1)`,
  } as const;
}
