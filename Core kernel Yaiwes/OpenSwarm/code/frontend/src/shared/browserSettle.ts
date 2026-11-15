// Renderer-side mirror of the backend's smart-wait (browser_wait.py): a `wait` that returns the instant the page is READY instead of blind-sleeping. A top-level BrowserWait gets this on the backend, but a `wait` INSIDE a BrowserBatch runs entirely here, so without this it would fall back to a dumb sleep. Two readiness signals plus a target: settle when the agent's `until` target is present (no waiting blind), else when the page goes quiet by EITHER the network OR the DOM settling (beacon-heavy SPAs never idle the network but their DOM does).

export const SETTLE_FLOOR_MS = 250; // never settle before this unless the target is already there
export const SETTLE_QUIET_MS = 400; // network OR DOM must be quiet this long to count as settled
export const SETTLE_POLL_MS = 150;

// Probe built per wait so it can also look for the agent's target. Returns ready + quiet (network-idle ms) + elems (element count; the caller watches it stop changing = DOM settle) + found (the `until` target is present + visible). `until` is JSON- encoded into a string literal, so it is data, never executable.
export function settleProbeJs(until: string): string {
  const spec = JSON.stringify(until || '');
  return (
    '(()=>{const n=performance.now();' +
    "const es=performance.getEntriesByType('resource');let last=0;" +
    'for(const e of es){const t=Math.max(e.responseEnd||0,e.startTime||0);if(t>last)last=t;}' +
    'let found=false;const spec=' + spec + ';' +
    'if(spec){try{const low=spec.toLowerCase();' +
    "let el=[...document.querySelectorAll('button,a,[role],input,textarea,[contenteditable],[aria-label],h1,h2')]" +
    ".find(e=>((e.innerText||e.value||e.getAttribute('aria-label')||'')+'').toLowerCase().includes(low));" +
    'if(!el){try{el=document.querySelector(spec);}catch(_){}}' +
    'if(el){const r=el.getBoundingClientRect();found=r.width>0&&r.height>0;}}catch(_){}}' +
    "return JSON.stringify({ready:document.readyState==='complete'," +
    'quiet:Math.round(n-last),elems:document.getElementsByTagName(\'*\').length,found});})()'
  );
}

// Pure decision. Stop the instant the target is present; otherwise, past the floor and once the document is complete, stop as soon as it's quiet by EITHER network OR DOM.
export function shouldStopWaiting(
  ready: boolean,
  quietMs: number,
  domStableMs: number,
  found: boolean,
  elapsedMs: number,
  floorMs = SETTLE_FLOOR_MS,
  windowMs = SETTLE_QUIET_MS,
): boolean {
  if (found) return true;
  if (elapsedMs < floorMs) return false;
  if (!ready) return false;
  return (quietMs || 0) >= windowMs || (domStableMs || 0) >= windowMs;
}
