#!/usr/bin/env node
/* ============================================================================
   Inlines config + CSS + JS into two self-contained HTML files in dist/.
   Use these when pasting into a page builder (GoHighLevel custom code, etc.)
   that will not reliably serve sibling asset files.

   Hosting the repo as static files? You don't need this — deploy as-is.

     node build.js
   ========================================================================== */

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const DIST = path.join(ROOT, 'dist');

const read = f => fs.readFileSync(path.join(ROOT, f), 'utf8');

// Neutralise any accidental </script> inside inlined JS/CSS, which would
// otherwise close the wrapping tag early and break the page.
const safe = s => s.replace(/<\/script>/gi, '<\\/script>');

function inline(htmlFile, outFile) {
  let html = read(htmlFile);

  // <link rel="stylesheet" href="assets/*.css">  ->  <style>…</style>
  html = html.replace(
    /<link[^>]+href="(assets\/[^"]+\.css)"[^>]*>/g,
    (_, href) => '<style>\n' + read(href) + '\n</style>'
  );

  // <script src="…"></script>  ->  <script>…</script>
  html = html.replace(
    /<script src="((?:assets\/)?[^"]+\.js)"><\/script>/g,
    (_, src) => '<script>\n' + safe(read(src)) + '\n</script>'
  );

  const leftover = html.match(/(?:src|href)="(?:\.\/)?(?:assets\/)?[^"]+\.(?:js|css)"/g);
  if (leftover) {
    console.warn('  ! not inlined: ' + leftover.join(', '));
  }

  fs.writeFileSync(path.join(DIST, outFile), html);
  const kb = (Buffer.byteLength(html) / 1024).toFixed(1);
  console.log(`  ${outFile.padEnd(12)} ${kb} KB`);
}

fs.mkdirSync(DIST, { recursive: true });
console.log('Building self-contained pages into dist/');
inline('lp.html', 'lp.html');
inline('quiz.html', 'quiz.html');
console.log('\nPaste each file into its page builder as raw HTML.');
console.log('Rebuild after every config.js change — dist/ is a snapshot, not a link.');
