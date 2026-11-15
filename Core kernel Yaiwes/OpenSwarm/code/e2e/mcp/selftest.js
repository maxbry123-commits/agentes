#!/usr/bin/env node
// Proves the openswarm-gui MCP server works: spawn over stdio, list tools, then (unless --no-launch) launch the app, screenshot, assert the renderer painted, and close.

'use strict';
const path = require('path');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

const NO_LAUNCH = process.argv.includes('--no-launch');

async function main() {
  const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(__dirname, 'electron-mcp.js')] });
  const client = new Client({ name: 'mcp-selftest', version: '0.1.0' }, { capabilities: {} });
  await client.connect(transport);

  const { tools } = await client.listTools();
  const names = tools.map((t) => t.name);
  process.stdout.write(`tools (${names.length}): ${names.join(', ')}\n`);
  for (const required of ['app_launch', 'click', 'fill', 'screenshot', 'snapshot', 'eval', 'read_log', 'app_close']) {
    if (!names.includes(required)) throw new Error(`missing tool: ${required}`);
  }

  if (NO_LAUNCH) {
    process.stdout.write('\nMCP SELFTEST PASS (handshake + tools only; --no-launch).\n');
    await client.close();
    process.exit(0);
  }

  const launch = await client.callTool({ name: 'app_launch', arguments: {} });
  if (launch.isError) throw new Error(`app_launch: ${launch.content?.[0]?.text}`);
  process.stdout.write(`app_launch -> ${launch.content?.[0]?.text}\n`);

  const shot = await client.callTool({ name: 'screenshot', arguments: {} });
  const isImage = shot.content?.[0]?.type === 'image' && (shot.content[0].data || '').length > 1000;
  if (!isImage) throw new Error('screenshot did not return a PNG');
  process.stdout.write(`screenshot -> ${shot.content[0].data.length} base64 bytes\n`);

  // A PNG of the right size could still be a blank window, so prove the renderer painted: assert #root mounted children.
  const root = await client.callTool({ name: 'eval', arguments: { expression: "document.getElementById('root').childElementCount" } });
  const childCount = Number(root.content?.[0]?.text);
  if (!(childCount > 0)) throw new Error(`renderer #root has ${root.content?.[0]?.text} children (blank window, not a real paint)`);
  process.stdout.write(`render check -> #root has ${childCount} children\n`);

  const log = await client.callTool({ name: 'read_log', arguments: { tailLines: 5 } });
  process.stdout.write(`read_log tail:\n${log.content?.[0]?.text}\n`);

  await client.callTool({ name: 'app_close', arguments: {} });
  await client.close();
  process.stdout.write('\nMCP SELFTEST PASS: server launched, drove, screenshotted, and read the app.\n');
  process.exit(0);
}

main().catch((e) => { process.stderr.write(`\nMCP SELFTEST FAIL: ${e && e.message || e}\n`); process.exit(1); });
