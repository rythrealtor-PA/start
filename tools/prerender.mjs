#!/usr/bin/env node
/**
 * Writes the data-driven text into index.html — contact facts, office
 * address, social links, the licence line, listings, testimonials and the
 * schema data search engines read — so it is in the HTML source
 * that search engines and link previews read, not only injected by JavaScript.
 *
 * Run after editing assets/js/config.js or the files in assets/data/ by hand:
 *
 *   node tools/prerender.mjs
 *
 * Publishing from admin.html does the same for listings and testimonials
 * automatically. Uses the very functions the browser uses (assets/js/render.js).
 */
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { CONFIG } from '../assets/js/config.js';
import { renderAllBlocks, renderFooterBlocks, replaceBlock } from '../assets/js/render.js';
import { buildGuides, homepageGuidesHTML, sitemapXML } from './build-guides.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const read = (p) => readFile(root + p, 'utf8');

// The guide pages first: the homepage links to them and the sitemap lists them.
const guides = await buildGuides(root);
console.log(`guides/: ${guides.length} guides + index built`);
await writeFile(root + 'sitemap.xml', sitemapXML(guides));

const html = await read('index.html');
let out = renderAllBlocks(html, {
  config: CONFIG,
  listings: JSON.parse(await read('assets/data/listings.json')),
  testimonials: JSON.parse(await read('assets/data/testimonials.json')),
});
out = replaceBlock(out, 'guides', homepageGuidesHTML(guides));
await writeFile(root + 'index.html', out);
console.log(out === html ? 'index.html already up to date' : 'index.html updated');

// Every absolute URL — canonical links, link-preview tags, sitemap, robots —
// follows config.siteUrl, so connecting the domain later is a one-line change.
const HOSTS = ['https://rythvara.com/', 'https://rythrealtor-pa.github.io/start/'];
for (const file of ['index.html', 'privacy.html', 'terms.html', 'preview.html', 'robots.txt']) {
  const before = await read(file);
  let after = before;
  for (const host of HOSTS) if (host !== CONFIG.siteUrl) after = after.split(host).join(CONFIG.siteUrl);
  if (after !== before) {
    await writeFile(root + file, after);
    console.log(`${file}: addresses now point at ${CONFIG.siteUrl}`);
  }
}

// The other pages share the footer: licence line and office address.
for (const page of ['privacy.html', 'terms.html', '404.html']) {
  const before = await read(page);
  const after = renderFooterBlocks(before, CONFIG);
  await writeFile(root + page, after);
  console.log(after === before ? `${page} already up to date` : `${page} updated`);
}
