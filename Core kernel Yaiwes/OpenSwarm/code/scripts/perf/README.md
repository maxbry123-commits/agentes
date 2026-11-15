# Boot + size instrumentation (Phase 0 baseline)

Tooling to measure two things we used to guess at: how long a cold launch takes,
and how many files we make the OS (and Defender) scan. These numbers are the
baseline that Phase 6 (slimming) and Phase 7 (Squirrel vs NSIS) are judged against.

## Boot timing

`electron/main.js` emits four ordered milestones to `backend.log`, one line each:

```
[perf] app-launch t=<ms>
[perf] first-paint t=<ms>
[perf] backend-http-ready t=<ms>
[perf] first-agent-response t=<ms>
```

`t` is milliseconds since process start. `first-agent-response` is fired by the
renderer (`WebSocketManager.dispatchDelta`) on the first streamed agent token.

Read and assert them after launching a packaged build:

```
node scripts/perf/parse-timing.js          # human table, exits 1 if missing/unordered
node scripts/perf/parse-timing.js --json    # machine-readable
node scripts/perf/parse-timing.js --log <path-to-backend.log>
```

backend.log lives next to `auth.token`:
- macOS:   `~/Library/Application Support/OpenSwarm/data/backend.log`
- Windows: `%APPDATA%\OpenSwarm\data\backend.log`
- Linux:   `~/.local/share/OpenSwarm/data/backend.log`

## File count / size

```
node scripts/perf/file-count.js                       # auto-detects packaged tree
node scripts/perf/file-count.js --root <resources-dir> # explicit
node scripts/perf/file-count.js --json
```

### Recorded baseline (Windows, win-unpacked/resources)

| dir         | files  | size    |
|-------------|--------|---------|
| python-env  | 8421   | 373.6 MB |
| router      | 2651   | 35.9 MB |
| backend     | 86     | 8.2 MB  |
| frontend    | 11     | 232.3 MB |
| debugger    | 75     | 1.2 MB  |
| other       | 3      | 621.3 MB |
| **TOTAL**   | 11247  | 1.2 GB  |

`python-env` is by far the largest file count, so it dominates Defender's
per-file scan cost on first launch. That is the Phase 6a target.

## Tests

`node scripts/perf/test-perf.js` builds throwaway fixtures with known counts and
known timing logs, runs both tools against them, and asserts exact numbers plus
that the failure paths fail. Hermetic; needs no packaged build. 17 assertions.
