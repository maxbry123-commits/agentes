// Shared text-measurement heuristics for chat bubbles. These are empirical pixel values measured against the bubble styling in MessageBubble; they're used to estimate how tall a chunk of text will render (for spacer / placeholder height reservation) and how many characters make a message "oversized" enough to virtualize. They're estimates only: actual heights are measured once an element is on screen and override these everywhere.

// Fired on the scroll container after a programmatic jump (scroll-to-bottom / initial open pin) settles, so oversized messages and their blocks re-evaluate visibility synchronously instead of waiting on the async IntersectionObserver, which occasionally misses the final transition and leaves a stuck placeholder.
export const RECHECK_VISIBILITY_EVENT = 'chat-recheck-visibility';

export const BUBBLE_LINE_HEIGHT_PX = 22;      // line-height of bubble body text
export const BUBBLE_AVG_CHAR_WIDTH_PX = 7.2;  // average glyph width at the bubble font
export const BUBBLE_WIDTH_RATIO = 0.85;       // bubbles are maxWidth: 85% of the column
export const MIN_CHARS_PER_VIEWPORT = 2_000;  // floor so tiny/zero viewports still allow real-sized messages
export const OVERSIZED_VIEWPORT_MULTIPLE = 2;  // a message taller than ~2 screens gets virtualized

// Tweak on the line-based estimate. Kept at 1.0 so estimates lean accurate/under rather than over: the scroll-height lock tolerates under-estimates fine (the total just grows monotonically as things measure), but OVER-estimates inflate the lock's compensating pad into visible empty space below the chat. Prose in particular over-estimated badly at higher values.
const MARKDOWN_DENSITY_FACTOR = 1.0;

// Characters that fit on one rendered line at this width.
function charsPerLine(viewportWidth: number): number {
  const readableWidth = Math.max(280, (viewportWidth || 0) * BUBBLE_WIDTH_RATIO);
  return Math.max(36, Math.floor(readableWidth / BUBBLE_AVG_CHAR_WIDTH_PX));
}

// Rough pixel height `text` will occupy when rendered in a bubble at this width. Counts by SOURCE line (each \n-delimited line takes at least one rendered line, plus wraps for long lines) rather than total chars, so dense markdown with many short lines isn't wildly under-counted. `chromePx` is the vertical padding/ margins around the text.
export function estimateRenderedTextHeight(text: string, viewportWidth: number, chromePx = 40): number {
  const cpl = charsPerLine(viewportWidth);
  const sourceLines = text ? text.split('\n') : [''];
  let lines = 0;
  for (let i = 0; i < sourceLines.length; i++) {
    lines += Math.max(1, Math.ceil(sourceLines[i].length / cpl));
  }
  return Math.ceil(Math.max(1, lines) * BUBBLE_LINE_HEIGHT_PX * MARKDOWN_DENSITY_FACTOR) + chromePx;
}

// Character count above which an assistant message is treated as "oversized" and gets the placeholder + block-virtualization treatment: roughly two screens of text, with a floor so it never trips on short messages.
export function oversizedCharThreshold(viewportHeight: number, viewportWidth: number): number {
  const visibleLines = Math.max(1, Math.ceil(Math.max(0, viewportHeight) / BUBBLE_LINE_HEIGHT_PX));
  const charsPerViewport = Math.max(MIN_CHARS_PER_VIEWPORT, visibleLines * charsPerLine(viewportWidth));
  return charsPerViewport * OVERSIZED_VIEWPORT_MULTIPLE;
}
