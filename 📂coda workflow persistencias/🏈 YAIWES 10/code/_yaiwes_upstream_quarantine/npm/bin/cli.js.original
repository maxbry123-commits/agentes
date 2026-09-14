#!/usr/bin/env node
// Thin shim: exec the real (Go) pentestswarm binary fetched by install.js,
// forwarding all args, stdio, and the exit code — so `pentestswarm …` behaves
// exactly like the native binary, including the interactive TUI.
"use strict";
const path = require("path");
const fs = require("fs");
const { spawnSync } = require("child_process");

const ext = process.platform === "win32" ? ".exe" : "";
const bin = path.join(__dirname, "pentestswarm" + ext);

if (!fs.existsSync(bin)) {
  console.error(
    "pentestswarm: binary not found — the postinstall download may have failed.\n" +
      "Reinstall (npm i -g @armurai/pentestswarm), or install from\n" +
      "https://github.com/Armur-Ai/Pentest-Swarm-AI/releases"
  );
  process.exit(1);
}

const res = spawnSync(bin, process.argv.slice(2), { stdio: "inherit" });
if (res.error) {
  console.error("pentestswarm:", res.error.message);
  process.exit(1);
}
process.exit(res.status === null ? 1 : res.status);
