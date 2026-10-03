#!/usr/bin/env node
/**
 * Writes the data-driven text into index.html — contact facts, social links,
 * the licence line, listings and testimonials — so it is in the HTML source
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
import { renderAllBlocks } from '../assets/js/render.js';

const root = fileURLToPath(new URL('..', import.meta.url));
const read = (p) => readFile(root + p, 'utf8');

const html = await read('index.html');
const out = renderAllBlocks(html, {
  config: CONFIG,
  listings: JSON.parse(await read('assets/data/listings.json')),
  testimonials: JSON.parse(await read('assets/data/testimonials.json')),
});
await writeFile(root + 'index.html', out);
console.log(out === html ? 'index.html already up to date' : 'index.html updated');
