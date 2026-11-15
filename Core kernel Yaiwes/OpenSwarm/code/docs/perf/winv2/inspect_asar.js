// #9 item 4: inventory an app.asar without extracting it. Parses the asar header
// (a Chromium Pickle: [u32 payloadSize][u32 headerSize] then [u32 payloadSize]
// [u32 jsonLen][json...]) and reports total size, biggest top-level dirs, biggest
// individual files, and trimmable categories (source maps, etc.).
// Usage: node inspect_asar.js <path-to-app.asar>
const fs = require('fs');

const asar = process.argv[2];
if (!asar) { console.error('usage: node inspect_asar.js <app.asar>'); process.exit(1); }

const fd = fs.openSync(asar, 'r');
const head = Buffer.alloc(8);
fs.readSync(fd, head, 0, 8, 0);
const headerSize = head.readUInt32LE(4);            // size of the header pickle
const hp = Buffer.alloc(headerSize);
fs.readSync(fd, hp, 0, headerSize, 8);
const jsonLen = hp.readUInt32LE(4);                 // string length inside the pickle
const json = hp.slice(8, 8 + jsonLen).toString('utf8');
const header = JSON.parse(json);
fs.closeSync(fd);

let total = 0, fileCount = 0;
const byExt = {};
const files = [];           // {path, size}
const topDirs = {};         // top-level entry -> size

function walk(node, parts) {
  if (node.files) {
    for (const [name, child] of Object.entries(node.files)) walk(child, parts.concat(name));
  } else if (typeof node.size === 'number') {
    const p = parts.join('/');
    total += node.size; fileCount++;
    files.push({ p, size: node.size });
    const ext = (p.match(/\.[^./]+$/) || ['(none)'])[0].toLowerCase();
    byExt[ext] = (byExt[ext] || 0) + node.size;
    topDirs[parts[0]] = (topDirs[parts[0]] || 0) + node.size;
  }
}
walk(header, []);

const mb = (b) => (b / 1048576).toFixed(1) + ' MB';
const sortObj = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]);

console.log(`asar total: ${mb(total)} across ${fileCount} files\n`);
console.log('=== biggest top-level entries ===');
for (const [d, s] of sortObj(topDirs).slice(0, 15)) console.log(`  ${mb(s).padStart(10)}  ${d}`);
console.log('\n=== biggest single files ===');
for (const f of files.sort((a, b) => b.size - a.size).slice(0, 20)) console.log(`  ${mb(f.size).padStart(10)}  ${f.p}`);
console.log('\n=== by extension (top 15) ===');
for (const [e, s] of sortObj(byExt).slice(0, 15)) console.log(`  ${mb(s).padStart(10)}  ${e}`);
console.log('\n=== trimmable categories ===');
const cat = (re) => files.filter(f => re.test(f.p)).reduce((n, f) => n + f.size, 0);
console.log(`  source maps (*.map):        ${mb(cat(/\.map$/))}`);
console.log(`  .ts/.tsx sources:           ${mb(cat(/\.tsx?$/))}`);
console.log(`  markdown/license/readme:    ${mb(cat(/(\.md|license|readme|changelog)/i))}`);
console.log(`  test/spec/__tests__:        ${mb(cat(/(\/test\/|\/tests\/|__tests__|\.spec\.|\.test\.)/i))}`);
console.log(`  node_modules inside asar:   ${mb(cat(/(^|\/)node_modules\//))}`);
