# @armurai/pentestswarm

One-command install of [Pentest Swarm AI](https://github.com/Armur-Ai/Pentest-Swarm-AI):

```bash
npm install -g @armurai/pentestswarm
pentestswarm run
```

The package is scoped to the `@armurai` org, but the installed command is just
`pentestswarm`.

This package is a thin delivery wrapper: on install it downloads the prebuilt
Go binary for your platform from the matching GitHub release (`vX.Y.Z`), and
the `pentestswarm` command execs it directly. The real program is the Go
binary — see the main repo for docs.

## Publishing (maintainers)

The package `version` MUST match a published GitHub release tag (the
postinstall downloads `pentestswarm-<os>-<arch>` from
`releases/download/v<version>/`). To cut a release:

1. Tag + push (`git tag vX.Y.Z && git push origin vX.Y.Z`) → GoReleaser builds
   the per-platform binaries and publishes the GitHub release.
2. Bump `npm/package.json` `version` to `X.Y.Z`.
3. `cd npm && npm publish` — `publishConfig.access` is already `public`, so the
   scoped package publishes publicly without the `--access public` flag. Needs
   `npm login` to the `@armurai` org (member with publish rights).

To let the `@armurai:<team>` team manage the package after the first publish:

```bash
npm access grant read-write armurai:<team> @armurai/pentestswarm
```

A CI step can automate 2–3 on release via an npm **automation** token stored as
the `NPM_TOKEN` GitHub Actions secret. Consider migrating to per-platform
`optionalDependencies` packages (esbuild-style) later to avoid a postinstall
network fetch.
