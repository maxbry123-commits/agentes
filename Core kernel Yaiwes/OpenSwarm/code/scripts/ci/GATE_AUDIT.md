# Gate audit: is this a real gate or smoke and mirrors?

A test only counts if breaking the thing it guards turns it RED. This is the
red-team of our own gate: for each check, the claim, the fault we injected, the
result, and an honest note on what it still does NOT cover. Re-run the evidence
with `node scripts/ci/selftest-gate.js` (pure, mutation tests) plus the live
fault-injections noted below.

## Verdict: it has teeth (with one gap found + fixed)

| Check | Claim | Fault injected | Result | Real? |
| --- | --- | --- | --- | --- |
| boot: provenance | the running app is the build at HEAD | built at an older sha, ran against HEAD | **RED** ("provenance sha X != git HEAD Y"), seen live | yes |
| boot: provenance/marks | a good log passes; broken logs don't | missing `[provenance]`, sha mismatch, missing mark, out-of-order, all-zero | **RED on each**, good log green (selftest-gate.js) | yes |
| boot: health | backend actually serves | port not serving | **RED** (health != 200) | yes |
| signature: reject | unsigned bits can't ship | `--require-signed` on the unsigned local build | **RED** (exit 1) | yes |
| signature: recognize | a real signature is seen as valid | `--require-signed` on `node.exe` (OpenJS-signed) | **GREEN, signed=Valid** (not "always unsigned") | yes |
| resilience: locked-port | survives a taken preferred port | held 8324-8333 | app served on **:8334** (behavior changed vs default :8324) | yes |
| resilience: multi-instance | 2nd launch exits, 1st keeps serving | launched a 2nd instance | 2nd **exited code 0**, 1st still 200 | yes |
| network: auth | the bearer is validated, not just present | no-token / **wrong-token** / real-token | **401 / 401 / 200** | yes (after fix) |
| network: 9router | the bundled router is up | TCP probe :20128 | open when up, RED when down | yes |
| agent turn | a real model reply on the user's creds | fresh session, tool-free prompt | **completed, tokens.output > 0** (can't be faked: a fresh session starts at 0) | yes |
| gui hand | a CC instance can drive the real GUI | launched + screenshotted + read log | works; render gate asserts `#root` has children (not a blank window) | yes |
| verify-all | one failure fails the whole gate | bogus app path | **3 sub-checks RED -> exit 1** (not silently green) | yes |

## The gap we found and closed

`verify-network` originally tested only no-token (401) vs real-token (200). A
backend that accepted ANY `Authorization` header would have passed both while auth
was actually broken. Added a **wrong-token probe** that must also get 401; the 200
now means "validated", not "a header was present". Proven live: `401 / 401 / 200`.

## What this gate still does NOT cover (honest residuals)

- **macOS signing path is unverified locally** (no Mac here). The `codesign` +
  `spctl` + staple logic is written but only CI on a Mac runner proves it.
- **Full port-range exhaustion** isn't exercised; we hold the bottom of the range
  (common real case). All-101-taken relies on get-port's own ephemeral fallback.
- **Agent-turn content** isn't asserted (models vary); we assert real output
  tokens were produced, not that the words are correct.
- **Perf marks are emitted by product code**; the gate trusts the app isn't lying
  about its own lifecycle. `first-paint` only exists if the renderer painted, so a
  no-paint boot is still caught.
- **The gate proves boot/serve/resilience/auth, not feature correctness.** That is
  the CC-instance apex layer's job (drive the GUI, judge "does it actually work").
