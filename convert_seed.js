const fs = require('fs');
const INPUT = 'mongodb_testdaten_onlineshop.js';
const raw = fs.readFileSync(INPUT, 'utf8');
const re = /db\.([a-zA-Z_]+)\.insertMany\s*\(\s*(\[[\s\S]*?\])\s*\)\s*;?/g;
const out = {};
let totalDocs = 0, blocks = 0, m;
while ((m = re.exec(raw)) !== null) {
  const collection = m[1];
  let docs;
  try { docs = JSON.parse(m[2]); }
  catch (e) { console.error(`Parse-Fehler in Block ${blocks + 1} (${collection}):`, e.message); process.exit(1); }
  if (!out[collection]) {
    out[collection] = fs.createWriteStream(`${collection}.jsonl`);
    console.log(`-> schreibe ${collection}.jsonl`);
  }
  for (const doc of docs) { out[collection].write(JSON.stringify(doc) + '\n'); totalDocs++; }
  blocks++;
}
for (const c of Object.keys(out)) out[c].end();
console.log(`\nFertig: ${blocks} Blöcke, ${totalDocs} Dokumente.`);
