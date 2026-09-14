# diff

The diff pane as a plugin: `/diff` opens the session's uncommitted changes
beside the transcript, one row per changed file and the selected file's
hunks beneath, and closes it again. The pane refreshes as Claude edits,
runs shell commands and finishes turns, and while it is open it polls the
repository's HEAD so a commit or checkout made elsewhere shows too. The
first successful edit of a session opens the pane by itself where the
terminal is wide enough (144 columns when the person never chose, 110 when
they kept it open before; a person who closed it is left alone). On a
terminal under 110 columns `/diff` answers with the built-in's line asking
for a wider terminal and opens nothing; a pane opened wider that the surface
then seats inline shows only that line. A file's
ask button arms that file: its hunks ride the next prompt as context, once.

The pane compares the working tree against HEAD, split at the session's
start (the default), against HEAD plainly, or against the merge-base with
the default branch; the choice is kept per repository in the plugin's
store. A second picker shows one earlier turn's edits instead of the
working tree, read from the session's messages. Files that changed before
the session started, and noise (lockfiles, generated and test files), are
listed apart and folded until asked for. Outside a git repository `/diff`
says so and does nothing else.

`hooks/register.ts` is the module; everything under `hooks/` is its parts.

## What it hooks

| event | what the hook does |
| --- | --- |
| `session.start` | Binds the engine once, registers `/diff` (a session where another `/diff` is listed leaves the plugin idle), and pins the repository. |
| `ui.render` of `PromptHint` | Reads the terminal's width, which decides whether the first edit opens the pane. |
| `ui.render` of `Pane` | Draws the pane: header, the file list, the toggles, the base and source pickers, and the selected file's hunks. |
| `command.run` of `diff` | Opens or closes the pane and remembers the choice. |
| `command.run` of `clear`, `resume` | Closes the pane and forgets the session's state. |
| `tool.call` of `Edit`, `Write`, `NotebookEdit` | After the edit, refreshes an open pane; the session's first successful edit opens it. |
| `tool.call` of `Bash`, `PowerShell` | After the command, refreshes an open pane. |
| `turn.complete` | Refreshes an open pane. |
| `prompt.submit` | Adds the armed file's hunks to the prompt's context and disarms. |

## What it calls on `$`

`clock.after`, `clock.every`, `clock.now`, `clock.sleep`, `command.register`,
`fs.list`, `fs.read`, `fs.stat`, `process.run` (git, read-only), `session.messages`,
`store.get`, `store.set`, `telemetry.log`, `telemetry.mark`, `ui.close`,
`ui.invalidate`, `ui.log`, `ui.open`, `ui.resolve`, `ui.status`.

`$.telemetry` is the telemetry plugin's noun; where it is absent the rows
are dropped and nothing else changes.

## Try it

```sh
claude --plugin-dir /path/to/diff
```

then `/diff` inside a git repository with a modified file.
