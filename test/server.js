/* ============================================================================
   Test harness: static file server + webhook capture.

   Serves the funnel from the repo root, but patches config.js in flight so the
   webhook and calendar point at this harness. config.js on disk stays in its
   shippable state — the test never mutates it.
   ========================================================================== */

const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const PORT = process.env.PORT || 8099;
const HITS = [];

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };

/* Test-only config overrides, applied to the served copy of config.js. */
function patchConfig(src) {
  return src
    .replace(/webhooks:\s*\[[^\]]*\]/, "webhooks: ['http://localhost:" + PORT + "/hook']")
    .replace(/calendarUrl:\s*''/, "calendarUrl: 'https://api.leadconnectorhq.com/widget/bookings/test-cal'");
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');

  if (req.method === 'POST' && u.pathname === '/hook') {
    let body = '';
    req.on('data', c => (body += c));
    req.on('end', () => {
      try { HITS.push(JSON.parse(body)); } catch (e) { HITS.push({ parseError: body }); }
      res.writeHead(200, { 'Access-Control-Allow-Origin': '*' });
      res.end('{"ok":true}');
    });
    return;
  }

  if (u.pathname === '/__reset') { HITS.length = 0; res.writeHead(200); return res.end('reset'); }

  if (u.pathname === '/__hits') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(HITS, null, 2));
  }

  const p = path.join(ROOT, u.pathname === '/' ? '/lp.html' : u.pathname);
  if (!p.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }

  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    let out = data;
    if (path.basename(p) === 'config.js') out = Buffer.from(patchConfig(data.toString('utf8')));
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(out);
  });
});

server.listen(PORT, () => console.log('test server on http://localhost:' + PORT));

module.exports = server;
