#!/usr/bin/env node
/**
 * Writes the data-driven text — contact facts, office address, social links,
 * the licence line, listings, testimonials and the schema data search engines
 * read — into both homepages (index.html, and es/index.html in Spanish), so it
 * is in the HTML source that search engines and link previews read, not only
 * injected by JavaScript. Also builds the guide pages and the sitemap.
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
import { buildGuides, homepageGuidesHTML, llmsTxt, sitemapXML } from './build-guides.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const read = (p) => readFile(root + p, 'utf8');

// The guide pages first: the homepages link to them and the sitemap lists them.
const guides = await buildGuides(root);
console.log(`guides/: ${guides.en.length} guides + index built`);
console.log(`es/guias/: ${guides.es.length} guides + index built`);
await writeFile(root + 'sitemap.xml', sitemapXML(guides));
await writeFile(root + 'llms.txt', llmsTxt(guides));

// The two homepages: English at the root, Spanish in es/.
const data = {
  config: CONFIG,
  listings: JSON.parse(await read('assets/data/listings.json')),
  testimonials: JSON.parse(await read('assets/data/testimonials.json')),
};
for (const page of [
  { file: 'index.html', lang: 'en', root: '', guides: guides.en, prefix: 'guides/' },
  { file: 'es/index.html', lang: 'es', root: '../', guides: guides.es, prefix: 'guias/' },
]) {
  const html = await read(page.file);
  let out = renderAllBlocks(html, data, page);
  out = replaceBlock(out, 'guides', homepageGuidesHTML(page.guides, page.prefix));
  await writeFile(root + page.file, out);
  console.log(out === html ? `${page.file} already up to date` : `${page.file} updated`);
}

// Every absolute URL — canonical links, link-preview tags, sitemap, robots —
// follows config.siteUrl, so connecting the domain later is a one-line change.
const HOSTS = ['https://rythvara.com/', 'https://rythrealtor-pa.github.io/start/'];
for (const file of ['index.html', 'es/index.html', 'privacy.html', 'terms.html', 'preview.html', 'robots.txt']) {
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
