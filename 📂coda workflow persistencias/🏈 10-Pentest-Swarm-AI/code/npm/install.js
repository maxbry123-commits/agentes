#!/usr/bin/env node
// postinstall: fetch the prebuilt pentestswarm binary matching this package's
// version + the host platform from the GitHub release, into ./bin. The Go
// binary is the real program; this npm package is just a delivery vehicle so
// `npm i -g pentestswarm` works like any other CLI.
"use strict";
const fs = require("fs");
const path = require("path");
const https = require("https");

const REPO = "Armur-Ai/Pentest-Swarm-AI";
const version = "v" + require("./package.json").version;

// Map Node's platform/arch onto the GoReleaser artifact names
// (pentestswarm-<goos>-<goarch>).
const osMap = { darwin: "darwin", linux: "linux", win32: "windows" };
const archMap = { x64: "amd64", arm64: "arm64" };
const goos = osMap[process.platform];
const goarch = archMap[process.arch];

if (!goos || !goarch) {
  console.error(
    `pentestswarm: unsupported platform ${process.platform}/${process.arch}.\n` +
      `Install from https://github.com/${REPO}/releases instead.`
  );
  process.exit(0); // don't hard-fail the whole npm install
}

const ext = goos === "windows" ? ".exe" : "";
const asset = `pentestswarm-${goos}-${goarch}`;
const url = `https://github.com/${REPO}/releases/download/${version}/${asset}`;
const binDir = path.join(__dirname, "bin");
const dest = path.join(binDir, "pentestswarm" + ext);

function download(u, file, redirects) {
  if (redirects > 10) return file.destroy(new Error("too many redirects"));
  https
    .get(u, { headers: { "User-Agent": "pentestswarm-npm" } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        return download(res.headers.location, file, (redirects || 0) + 1);
      }
      if (res.statusCode !== 200) {
        return file.destroy(new Error(`HTTP ${res.statusCode} for ${u}`));
      }
      res.pipe(file);
    })
    .on("error", (e) => file.destroy(e));
}

fs.mkdirSync(binDir, { recursive: true });
const out = fs.createWriteStream(dest, { mode: 0o755 });
out.on("finish", () => {
  try {
    fs.chmodSync(dest, 0o755);
  } catch (_) {}
  console.log(`pentestswarm ${version} installed (${goos}/${goarch}).`);
});
out.on("error", (e) => {
  console.error(
    `pentestswarm: could not download the binary (${e.message}).\n` +
      `Grab it from https://github.com/${REPO}/releases or use the install script.`
  );
  // Exit 0 so a transient download hiccup doesn't break the user's whole
  // `npm install`; the bin shim reports a clear error if the binary is absent.
  process.exit(0);
});
download(url, out, 0);
