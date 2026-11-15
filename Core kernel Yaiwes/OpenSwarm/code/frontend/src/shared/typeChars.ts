// Type a string into the already-focused box as real, trusted key events over CDP.
//
// This file exists because the Electron sendInputEvent path it replaces was abandoned once
// already, in handlePressKey, for one reason: it delivers to whatever the OS thinks has focus
// rather than to this webview, and it is fire-and-forget, so a read-back races the text it is
// checking for. Both fill paths kept using it anyway, and the "via keystrokes" success line has
// never once appeared in a log.
//
// Multi-line text is refused rather than typed: Enter in a chat composer sends the message, and a
// fill tier that can post half a draft is worse than one that admits it gave up.

/** One CDP command against the frame that owns the box being filled. */
export type CdpDispatch = (method: string, params: Record<string, unknown>) => Promise<unknown>;

export interface TypedKeys {
  /** True only when every character was dispatched. */
  dispatched: boolean;
  /** Why nothing was dispatched. Empty exactly when dispatched is true. */
  skipped: '' | 'empty' | 'multiline';
}

const NEWLINE: RegExp = /[\r\n]/;

function codeFor(ch: string): string {
  if (/[a-zA-Z]/.test(ch)) return `Key${ch.toUpperCase()}`;
  if (/[0-9]/.test(ch)) return `Digit${ch}`;
  return ch === ' ' ? 'Space' : '';
}

export async function typeChars(dispatch: CdpDispatch, text: string): Promise<TypedKeys> {
  if (!text) return { dispatched: false, skipped: 'empty' };
  if (NEWLINE.test(text)) return { dispatched: false, skipped: 'multiline' };
  for (const ch of text) {
    const vk: number = ch.toUpperCase().charCodeAt(0);
    const code: string = codeFor(ch);
    // text on the DOWN event is what actually inserts the character; keyUp carrying it too would
    // type everything twice.
    const down: Record<string, unknown> = {
      type: 'keyDown', key: ch, text: ch, unmodifiedText: ch,
      windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk,
    };
    const up: Record<string, unknown> = {
      type: 'keyUp', key: ch, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk,
    };
    if (code) { down.code = code; up.code = code; }
    await dispatch('Input.dispatchKeyEvent', down);
    await dispatch('Input.dispatchKeyEvent', up);
  }
  return { dispatched: true, skipped: '' };
}
