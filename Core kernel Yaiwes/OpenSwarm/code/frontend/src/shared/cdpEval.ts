// Turn a CDP `Runtime.evaluate` result into the value, the way webContents.executeJavaScript
// hands it back: return the serialized value, and throw when the page code itself threw (that
// arrives as `exceptionDetails`, not as an infra error). Kept pure + separate so it's unit
// testable without the whole browser-command module and its Electron globals.

export interface CdpEvalResult {
  result?: { value?: unknown; type?: string };
  exceptionDetails?: {
    text?: string;
    exception?: { description?: string; value?: unknown };
  };
}

export function unwrapCdpEval(cdp: CdpEvalResult): unknown {
  if (cdp && cdp.exceptionDetails) {
    const ex = cdp.exceptionDetails;
    const msg = (ex.exception && (ex.exception.description || ex.exception.value)) || ex.text || 'eval error in page';
    throw new Error(String(msg));
  }
  return cdp && cdp.result ? cdp.result.value : undefined;
}
