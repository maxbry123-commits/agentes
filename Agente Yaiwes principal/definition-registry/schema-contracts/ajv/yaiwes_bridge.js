"use strict";
const fs=require("node:fs"),path=require("node:path");
function fail(m){process.stderr.write(String(m)+"\n");process.exit(2)}
try{const r=JSON.parse(fs.readFileSync(0,"utf8"));if(!r||typeof r!=="object"||Array.isArray(r))fail("request must be a JSON object");if(!r.schema||typeof r.schema!=="object"||Array.isArray(r.schema))fail("schema must be a JSON object");const M=require(path.join(__dirname,"dist","ajv.js")),Ajv=M.default||M,o=r.options&&typeof r.options==="object"&&!Array.isArray(r.options)?r.options:{},ajv=new Ajv(o),v=ajv.compile(r.schema),valid=Boolean(v(r.data));process.stdout.write(JSON.stringify({valid,errors:v.errors||[]}))}catch(e){fail(e&&e.stack?e.stack:e)}
