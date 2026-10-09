/**
 * Builds the guide pages — the library of single-question pages AI search and
 * Google draw answers from — out of plain text files in content/guides/.
 *
 *   content/guides/stroudsburg.md  ->  guides/stroudsburg.html
 *
 * Every page gets the same structure, because that structure is what makes a
 * page citable: a direct answer first, a byline and an "updated" date (who
 * says this, and how fresh it is), the reviews, questions and answers, an
 * author box, and schema data (Article, FAQPage, BreadcrumbList) describing
 * all of it. Everything is in the HTML source; nothing is added by script.
 *
 * Run through tools/prerender.mjs, which also refreshes the homepage's guide
 * links and the sitemap.
 *
 * ── Writing a guide ───────────────────────────────────────────────────────
 *
 *   ---
 *   title: Living in Stroudsburg, PA            (the page heading)
 *   seoTitle: Living in Stroudsburg, PA (2026)  (browser tab / Google, ≤ 60)
 *   description: One or two sentences, ≤ 160 characters, for Google.
 *   answer: The short, direct answer shown first on the page.
 *   category: Towns                  (Counties, Towns, Buying, Selling, Investing)
 *   place: Stroudsburg, Pennsylvania (area guides only)
 *   published: 2026-10-08
 *   updated: 2026-10-08
 *   reviews: Steven B., Flor B.      (names exactly as in testimonials.json)
 *   related: monroe-county, tannersville
 *   featured: yes                    (also listed on the homepage)
 *   order: 10                        (position within its category)
 *   ---
 *   ## A heading
 *   A paragraph. **Bold**, *italic* and [links](tannersville.html) work.
 *
 *   - a list item
 *
 *   ## Questions
 *   ### A question people ask?
 *   Its answer.
 *
 * "## Questions" is special: each "###" under it becomes a question.
 *
 * ── Slots ─────────────────────────────────────────────────────────────────
 *
 * A line holding only {{name}} drops in a block built from data:
 *
 *   {{photo}}      the guide's first photo        content/photos.json
 *   {{photos}}     all of the guide's photos      content/photos.json
 *   {{map}}        the county map                 front matter: map, highlight, marker
 *   {{market}}     median price, sales, days      content/market.json
 *   {{take}}       Ryth's own words               front matter: take
 *   {{str-map}}    rental rules map, by color     content/str-ratings.json
 *   {{str-table}}  the same, as a table           content/str-ratings.json
 *
 *   map: monroe                        (monroe or northampton)
 *   highlight: Pocono township         (Census names, comma separated)
 *   marker: Tannersville @ 41.0401, -75.3057
 *   aliases: old-slug                  (old addresses that redirect here)
 *
 * A slot with no data yet renders nothing, and a "##" section left empty
 * is dropped, so a page never shows an empty box. Pipe tables work too:
 *
 *   | Column | Column |
 *   | --- | --- |
 *   | cell | cell |
 */
import { readFile, writeFile, readdir, mkdir, unlink, access } from 'node:fs/promises';
import { CONFIG } from '../assets/js/config.js';
import { esc, legalLine, footerOfficeLine } from '../assets/js/render.js';
import { countyMap } from './maps.mjs';

const CATEGORY_ORDER = ['Counties', 'Towns', 'Buying', 'Selling', 'Investing'];

/* ───────────────────────────── text → HTML ───────────────────────────── */

function parseFrontMatter(text, file) {
  const m = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) throw new Error(`${file}: missing the --- front matter block`);
  const meta = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.*)$/);
    if (kv) meta[kv[1]] = kv[2].trim();
  }
  for (const key of ['title', 'description', 'answer', 'category', 'updated']) {
    if (!meta[key]) throw new Error(`${file}: front matter needs "${key}"`);
  }
  if (!CATEGORY_ORDER.includes(meta.category)) {
    throw new Error(`${file}: category must be one of ${CATEGORY_ORDER.join(', ')}`);
  }
  const list = (v) => (v ? v.split(',').map((s) => s.trim()).filter(Boolean) : []);
  let marker = null;
  if (meta.marker) {
    const mk = meta.marker.match(/^(.+?)\s*@\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)$/);
    if (!mk) throw new Error(`${file}: marker must look like "Town @ 41.04, -75.30"`);
    marker = { label: mk[1], lat: Number(mk[2]), lon: Number(mk[3]) };
  }
  return {
    ...meta,
    published: meta.published || meta.updated,
    places: meta.place ? meta.place.split(';').map((p) => p.trim()) : [],
    reviews: list(meta.reviews),
    related: list(meta.related),
    aliases: list(meta.aliases),
    highlight: list(meta.highlight),
    marker,
    featured: /^(yes|true)$/i.test(meta.featured || ''),
    order: Number(meta.order || 100),
    body: m[2],
  };
}

/** **bold**, *italic*, [text](url) — on already-escaped text. */
function inline(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*(?!\s)(.+?)\*/g, '$1<em>$2</em>')
    .replace(/\[(.+?)\]\((.+?)\)/g, (_, label, href) => `<a href="${href}">${label}</a>`);
}

const slugify = (s) => s.toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

/**
 * Splits the body into blocks and renders them; "## Questions" is collected
 * separately. slot(name) renders a {{name}} line; a section whose blocks all
 * render empty is left out, heading and all.
 */
function renderBody(md, slot) {
  const blocks = md.trim().split(/\n\s*\n/);
  const sections = [{ heading: null, html: [] }];
  const faqs = [];
  let inQuestions = false;
  let current = null; // the FAQ being filled

  for (const raw of blocks) {
    const block = raw.trim();
    const lines = block.split('\n');

    if (/^## /.test(block)) {
      const heading = lines[0].slice(3).trim();
      inQuestions = /^questions$/i.test(heading);
      current = null;
      if (!inQuestions) sections.push({ heading, html: [] });
      // A heading may be followed directly by text in the same block.
      const rest = lines.slice(1).join('\n').trim();
      if (rest) {
        if (inQuestions) throw new Error('Put a blank line after "## Questions"');
        sections.at(-1).html.push(renderBlock(rest, slot));
      }
      continue;
    }

    if (inQuestions) {
      if (/^### /.test(block)) {
        current = { q: lines[0].slice(4).trim(), a: [] };
        faqs.push(current);
        const rest = lines.slice(1).join(' ').trim();
        if (rest) current.a.push(rest);
      } else if (current) {
        current.a.push(lines.join(' '));
      }
      continue;
    }

    sections.at(-1).html.push(renderBlock(block, slot));
  }

  const html = sections
    .filter((sec) => sec.html.some(Boolean))
    .map((sec) => [sec.heading && `<h2 id="${slugify(sec.heading)}">${inline(sec.heading)}</h2>`, ...sec.html.filter(Boolean)]
      .filter(Boolean).join('\n'))
    .join('\n');
  return { html, faqs };
}

function renderTable(lines) {
  const cells = (l) => l.replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
  const [head, , ...rows] = lines;
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="Table: ${esc(cells(head).join(', '))}"><table>
  <thead><tr>${cells(head).map((c) => `<th scope="col">${inline(c)}</th>`).join('')}</tr></thead>
  <tbody>
${rows.map((r) => `    <tr>${cells(r).map((c, i) => (i === 0 ? `<th scope="row">${inline(c)}</th>` : `<td>${inline(c)}</td>`)).join('')}</tr>`).join('\n')}
  </tbody>
</table></div>`;
}

function renderBlock(block, slot) {
  const lines = block.split('\n');
  const slotMatch = block.match(/^\{\{([\w-]+)\}\}$/);
  if (slotMatch) return slot(slotMatch[1]);
  if (/^### /.test(block)) {
    return `<h3>${inline(lines[0].slice(4))}</h3>` + (lines.length > 1 ? `\n${renderBlock(lines.slice(1).join('\n'), slot)}` : '');
  }
  if (lines.length > 2 && lines.every((l) => /^\|.*\|$/.test(l)) && /^\|[\s:|-]+\|$/.test(lines[1])) {
    return renderTable(lines);
  }
  if (lines.every((l) => /^- /.test(l))) {
    return `<ul>\n${lines.map((l) => `  <li>${inline(l.slice(2))}</li>`).join('\n')}\n</ul>`;
  }
  if (lines.every((l) => /^\d+\. /.test(l))) {
    return `<ol>\n${lines.map((l) => `  <li>${inline(l.replace(/^\d+\. /, ''))}</li>`).join('\n')}\n</ol>`;
  }
  return `<p>${inline(lines.join(' '))}</p>`;
}

/* ─────────────────────────────── pieces ──────────────────────────────── */

const longDate = (iso) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
  });

const jsonLd = (data) =>
  `<script type="application/ld+json">\n${JSON.stringify(data, null, 2).replace(/</g, '\\u003c')}\n</script>`;

function head({ title, description, canonical, prefix, type = 'article', schema }) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="theme-color" content="#12171C">
<link rel="icon" href="${prefix}favicon.ico" sizes="32x32">
<link rel="icon" href="${prefix}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="${prefix}apple-touch-icon.png">
<link rel="canonical" href="${canonical}">
<meta property="og:site_name" content="Ryth Vara Real Estate">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:type" content="${type}">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="${canonical}">
<meta property="og:image" content="${CONFIG.siteUrl}assets/img/social-card.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${CONFIG.siteUrl}assets/img/social-card.jpg">
${jsonLd(schema)}
<link rel="stylesheet" href="${prefix}assets/fonts/fonts.css">
<link rel="stylesheet" href="${prefix}assets/css/styles.css">
<script type="module" src="${prefix}assets/js/page.js"></script>
</head>

<body>
<a class="skip-link" href="#main">Skip to content</a>
`;
}

function header(prefix, backHref, backLabel) {
  return `
<header class="page-header">
  <div class="wrap">
    <a class="page-header__name" href="${prefix}./">Ryth Vara</a>
    <nav class="page-header__nav" aria-label="Site">
      <a class="page-header__back" href="${backHref}">${backLabel}</a>
      <a class="page-header__back" href="${prefix}./#contact">Contact</a>
    </nav>
  </div>
</header>
`;
}

function footer(prefix) {
  return `
<footer class="footer">
  <div class="wrap footer__inner">
    <div class="footer__brands">
      <span class="footer__brand">
        <img class="footer__mark footer__mark--team" src="${prefix}assets/img/hs-group.png"
             alt="HS Group" width="440" height="378" loading="lazy">
      </span>
      <span class="footer__divider" aria-hidden="true"></span>
      <span class="footer__brand">
        <img class="footer__mark footer__mark--broker" src="${prefix}assets/img/real-of-pennsylvania.png"
             alt="Real of Pennsylvania" width="900" height="460" loading="lazy">
      </span>
    </div>

    <div class="footer__legal">
      <p class="footer__office">${esc(footerOfficeLine(CONFIG))}</p>
      <p data-footer-legal>${esc(legalLine(CONFIG))}</p>
      <p>&copy; <span data-year>${new Date().getUTCFullYear()}</span> · English &amp; Español · Equal Housing Opportunity</p>
      <p class="footer__links">
        <a href="${prefix}guides/">Guides</a>
        <a href="${prefix}privacy.html">Privacy Policy</a>
        <a href="${prefix}terms.html">Terms of Use</a>
      </p>
    </div>
  </div>
</footer>
</body>
</html>
`;
}

function card(g, prefix) {
  return `
        <a class="guide-card" href="${prefix}${g.slug}.html">
          <span class="guide-card__kicker">${esc(g.category)}</span>
          <span class="guide-card__title">${esc(g.title)}</span>
          <span class="guide-card__text">${esc(g.description)}</span>
        </a>`;
}

function authorBox(prefix) {
  return `
    <aside class="guide-author" aria-label="About the author">
      <img class="guide-author__photo" src="${prefix}${CONFIG.portrait}" alt="${esc(CONFIG.name)}"
           width="96" height="120" loading="lazy">
      <div>
        <p class="guide-author__name">Written by ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup></p>
        <p>Bilingual (English and Spanish) REALTOR<sup>&reg;</sup> with ${esc(CONFIG.brokerage)},
        serving ${esc(CONFIG.serviceAreas.counties.join(' and '))}. Specializes in luxury real
        estate, real estate investors, and Spanish-speaking families. In 2025, Ryth and his team
        at ${esc(CONFIG.team)} closed 149 transactions totaling $49&nbsp;million in sales.</p>
        <p><a href="tel:${CONFIG.contact.phoneHref}">${esc(CONFIG.contact.phone)}</a> ·
        <a href="mailto:${CONFIG.contact.email}">${esc(CONFIG.contact.email)}</a> ·
        License ${esc(CONFIG.license)}</p>
      </div>
    </aside>`;
}

/* ──────────────────────────────── slots ──────────────────────────────── */

const listSentence = (items) =>
  (items.length < 3 ? items.join(' and ') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`);

/** "Numbers on the map: 1 Delaware Water Gap Borough, ..." */
function mapKey(items) {
  const nums = items.filter((i) => i.num).sort((a, b) => a.num - b.num);
  return nums.length ? ` Numbers on the map: ${nums.map((i) => `${i.num} ${esc(i.full)}`).join(', ')}.` : '';
}

const HINT = ' <span class="cmap__hint">Swipe sideways to see the whole county.</span>';

function mapSlot(g) {
  if (!g.map) return '';
  const m = countyMap(g.map, { highlight: g.highlight, marker: g.marker, idPrefix: `map-${g.slug}` });
  const hl = m.items.filter((i) => i.hl).map((i) => i.full);
  const caption = g.mapCaption
    ? esc(g.mapCaption)
    : hl.length
      ? `${esc(listSentence(hl))} ${hl.length > 1 ? 'are' : 'is'} highlighted on this map of ${esc(m.county)}${g.marker ? `; the dot marks ${esc(g.marker.label)}` : ''}.`
      : `The municipalities of ${esc(m.county)}, from US Census boundaries.`;
  // A county page lists every municipality under the map, in text.
  const list = hl.length ? '' : `\n<div class="cmap__list">${[['city', 'Cities'], ['borough', 'Boroughs'], ['township', 'Townships']]
    .map(([kind, label]) => {
      const of = m.items.filter((i) => i.kind === kind);
      return of.length ? `<p>${label} (${of.length}): ${of.map((i) => `${esc(i.base)}${i.num ? ` (${i.num})` : ''}`).join(', ')}.</p>` : '';
    }).join('')}</div>`;
  return `<figure class="cmap">
  <div class="cmap__scroll" tabindex="0" role="region" aria-label="Map of ${esc(m.county)}">${m.svg}</div>
  <figcaption>${caption}${mapKey(m.items)}${HINT}</figcaption>
</figure>${list}`;
}

const STR = {
  green: 'Easier',
  yellow: 'Possible, with limits',
  red: 'Very difficult',
};
const STR_ORDER = Object.keys(STR);

function strMapSlot(data) {
  if (!data) return '';
  const ratings = Object.fromEntries(Object.entries(data.ratings).map(([name, r]) => [name, r.color]));
  const m = countyMap(data.county, {
    ratings,
    idPrefix: 'map-str',
    title: `Short-term rental rules by municipality in ${data.county === 'monroe' ? 'Monroe County' : 'Northampton County'}: green, yellow or red`,
  });
  return `<figure class="cmap">
  <div class="cmap__scroll" tabindex="0" role="region" aria-label="Short-term rental map of ${esc(m.county)}">${m.svg}</div>
  <figcaption>
    <ul class="str-legend">${STR_ORDER.map((c) => `<li><span class="str-swatch str-swatch--${c}" aria-hidden="true"></span>${c[0].toUpperCase()}${c.slice(1)}: ${STR[c].toLowerCase()}</li>`).join('')}</ul>
    Ryth's assessment as of ${esc(data.asOf)}. Rules change; confirm with the township before you buy.${mapKey(m.items)}${HINT}
  </figcaption>
</figure>`;
}

function strTableSlot(data) {
  if (!data) return '';
  const full = (name) => name.replace(/^(.*) (township|borough)$/, (_, b, k) => `${b} ${k === 'township' ? 'Township' : 'Borough'}`);
  const rows = Object.entries(data.ratings)
    .sort(([a, ra], [b, rb]) => STR_ORDER.indexOf(ra.color) - STR_ORDER.indexOf(rb.color) || a.localeCompare(b));
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="Short-term rentals by municipality"><table class="str-table">
  <caption>Short-term rentals by municipality, ${data.county === 'monroe' ? 'Monroe County' : 'Northampton County'}: Ryth's assessment as of ${esc(data.asOf)}</caption>
  <thead><tr><th scope="col">Municipality</th><th scope="col">Rating</th><th scope="col">Why</th></tr></thead>
  <tbody>
${rows.map(([name, r]) => `    <tr><th scope="row">${esc(full(name))}</th><td><span class="str-swatch str-swatch--${r.color}" aria-hidden="true"></span>${r.color[0].toUpperCase()}${r.color.slice(1)}: ${STR[r.color].toLowerCase()}</td><td>${inline(r.why)}</td></tr>`).join('\n')}
  </tbody>
</table></div>`;
}

function marketSlot(m) {
  if (!m) return '';
  const n = (v) => Number(v).toLocaleString('en-US');
  return `<div class="stats">
  <p class="stat"><span class="stat__value">$${n(m.median)}</span><span class="stat__label">Median sale price</span></p>
  <p class="stat"><span class="stat__value">${n(m.sold)}</span><span class="stat__label">Homes sold in the last 12 months</span></p>
  <p class="stat"><span class="stat__value">${n(m.dom)}</span><span class="stat__label">Average days on market</span></p>
</div>
<p class="stats__note">${esc(m.scope)}, ${esc(m.period)}. Source: ${esc(m.source)}.</p>`;
}

function photoFigure(p, eager) {
  const caption = [p.caption && esc(p.caption), p.credit && `<span class="guide-photo__credit">${esc(p.credit)}</span>`]
    .filter(Boolean).join(' ');
  return `<figure class="guide-photo">
  <img src="../${esc(p.src)}" alt="${esc(p.alt)}" width="${p.width}" height="${p.height}" loading="${eager ? 'eager' : 'lazy'}" decoding="async">${caption ? `
  <figcaption>${caption}</figcaption>` : ''}
</figure>`;
}

function takeSlot(text) {
  if (!text) return '';
  return `<figure class="guide-take">
  <blockquote><p>${inline(text)}</p></blockquote>
  <figcaption>${esc(CONFIG.name)}, REALTOR&reg;</figcaption>
</figure>`;
}

/** What each slot needs, for the placeholders in a draft build. */
const PENDING = {
  photo: "Ryth's photo of the town",
  photos: 'Three photos (Lake Harmony, Lake Naomi, Emerald Lakes)',
  market: 'Market numbers from the MLS: median sale price, homes sold in the last 12 months, average days on market',
  take: "Ryth's take, in his own words",
};

/* ──────────────────────────────── pages ──────────────────────────────── */

function guidePage(g, all, testimonials, data, { drafts = false } = {}) {
  const prefix = '../';
  const url = `${CONFIG.siteUrl}guides/${g.slug}.html`;
  const photos = data.photos[g.slug] || [];
  const slots = {
    photo: () => (photos[0] ? photoFigure(photos[0], true) : ''),
    photos: () => (photos.length ? `<div class="guide-photos">\n${photos.map((p) => photoFigure(p, false)).join('\n')}\n</div>` : ''),
    map: () => mapSlot(g),
    market: () => marketSlot(data.market[g.slug]),
    take: () => takeSlot(g.take),
    'str-map': () => strMapSlot(data.str),
    'str-table': () => strTableSlot(data.str),
  };
  const slot = (name) => {
    if (!slots[name]) throw new Error(`${g.slug}: unknown slot {{${name}}}`);
    const html = slots[name]();
    return html || (drafts && PENDING[name]
      ? `<p style="border:1px dashed #b08d57;padding:1.25rem;color:#d4b483">Pending: ${esc(PENDING[name])}</p>`
      : '');
  };
  const { html: bodyHTML, faqs } = renderBody(g.body, slot);
  const agentId = `${CONFIG.siteUrl}#agent`;

  const reviews = g.reviews.map((name) => {
    const t = testimonials.find((x) => x.name === name);
    if (!t) throw new Error(`${g.slug}: no testimonial named "${name}"`);
    return t;
  });
  const related = g.related.map((slug) => {
    const r = all.find((x) => x.slug === slug);
    if (!r) throw new Error(`${g.slug}: related guide "${slug}" does not exist`);
    return r;
  });

  const schema = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        headline: g.title,
        description: g.description,
        inLanguage: 'en-US',
        datePublished: g.published,
        dateModified: g.updated,
        mainEntityOfPage: url,
        image: `${CONFIG.siteUrl}${photos[0] ? photos[0].src : 'assets/img/social-card.jpg'}`,
        author: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        publisher: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        ...(g.places.length && {
          about: g.places.length === 1
            ? { '@type': 'Place', name: g.places[0] }
            : g.places.map((name) => ({ '@type': 'Place', name })),
        }),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: CONFIG.siteUrl },
          { '@type': 'ListItem', position: 2, name: 'Guides', item: `${CONFIG.siteUrl}guides/` },
          { '@type': 'ListItem', position: 3, name: g.title, item: url },
        ],
      },
      ...(faqs.length
        ? [{
          '@type': 'FAQPage',
          mainEntity: faqs.map((f) => ({
            '@type': 'Question',
            name: f.q,
            acceptedAnswer: { '@type': 'Answer', text: f.a.join(' ').replace(/\*\*|\*|\[|\]\(.*?\)/g, '') },
          })),
        }]
        : []),
    ],
  };

  return head({
    title: g.seoTitle || `${g.title} | Ryth Vara, REALTOR®`,
    description: g.description,
    canonical: url,
    prefix,
    schema,
  }) + header(prefix, './', '&larr; All guides') + `
<main id="main" class="doc guide">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="${prefix}./">Home</a> <span aria-hidden="true">/</span>
      <a href="./">Guides</a> <span aria-hidden="true">/</span>
      <span aria-current="page">${esc(g.title)}</span>
    </nav>

    <h1 class="section__title">${esc(g.title)}</h1>
    <p class="doc__meta">By ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup> · ${esc(CONFIG.brokerage)} ·
      Updated <time datetime="${g.updated}">${longDate(g.updated)}</time></p>

    <div class="doc__body">
      <p class="guide__answer"><strong>In short:</strong> ${inline(g.answer)}</p>

${bodyHTML.split('\n').map((l) => `      ${l}`).join('\n')}
${reviews.length ? `
      <h2 id="what-clients-say">What clients say</h2>
${reviews.map((t) => `      <figure class="guide-quote">
        <blockquote>${esc(t.quote)}</blockquote>
        <figcaption>${esc(t.name)}</figcaption>
      </figure>`).join('\n')}` : ''}
${faqs.length ? `
      <h2 id="questions">Questions</h2>
      <div class="faq__list">
${faqs.map((f) => `        <details class="faq__item">
          <summary class="faq__q">${inline(f.q)}</summary>
          <div class="faq__a">${f.a.map((p) => `<p>${inline(p)}</p>`).join('')}</div>
        </details>`).join('\n')}
      </div>` : ''}

      <div class="guide-cta">
        <p class="guide-cta__title">Questions about ${esc(g.places.length ? listSentence(g.places.map((p) => p.replace(/, Pennsylvania$/, ''))) : 'your move')}?</p>
        <p>Ryth answers in English or Spanish — call or text
        <a href="tel:${CONFIG.contact.phoneHref}">${esc(CONFIG.contact.phone)}</a>, or send a message.</p>
        <a class="button button--primary" href="${prefix}./#contact">Contact Ryth</a>
      </div>
${related.length ? `
      <h2 id="related-guides">Related guides</h2>
      <div class="guide-grid">${related.map((r) => card(r, '')).join('')}
      </div>` : ''}
${authorBox(prefix)}
    </div>
  </div>
</main>
` + footer(prefix);
}

function indexPage(guides) {
  const prefix = '../';
  const url = `${CONFIG.siteUrl}guides/`;
  const title = 'Real Estate Guides for Monroe & Northampton County, PA';
  const description =
    'Local guides by Ryth Vara, REALTOR®: towns and counties, buying, selling, closing costs and investing in Monroe and Northampton County, PA.';
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: title,
    description,
    url,
    inLanguage: 'en-US',
    author: { '@type': 'RealEstateAgent', '@id': `${CONFIG.siteUrl}#agent`, name: CONFIG.name },
    hasPart: guides.map((g) => ({ '@type': 'Article', headline: g.title, url: `${url}${g.slug}.html` })),
  };
  const groups = CATEGORY_ORDER
    .map((c) => [c, guides.filter((g) => g.category === c)])
    .filter(([, list]) => list.length);

  return head({ title, description, canonical: url, prefix, type: 'website', schema })
    + header(prefix, prefix, '&larr; Home') + `
<main id="main" class="doc guide">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="${prefix}./">Home</a> <span aria-hidden="true">/</span>
      <span aria-current="page">Guides</span>
    </nav>
    <h1 class="section__title">${esc(title)}</h1>
    <p class="doc__meta">By ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup> · ${esc(CONFIG.brokerage)}</p>
    <p class="guides__intro">Straight answers about buying, selling and investing in
    ${esc(CONFIG.serviceAreas.counties.join(' and '))} — town by town, in plain language.</p>
${groups.map(([c, list]) => `
    <h2 class="guides__group">${esc(c)}</h2>
    <div class="guide-grid">${list.map((g) => card(g, '')).join('')}
    </div>`).join('\n')}
${authorBox(prefix)}
  </div>
</main>
` + footer(prefix);
}

/* ───────────────────────────────── build ─────────────────────────────── */

export async function loadGuides(root) {
  const dir = `${root}content/guides/`;
  const files = (await readdir(dir)).filter((f) => f.endsWith('.md')).sort();
  const guides = [];
  for (const f of files) {
    guides.push({ slug: f.replace(/\.md$/, ''), ...parseFrontMatter(await readFile(dir + f, 'utf8'), f) });
  }
  return guides.sort((a, b) =>
    CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category)
    || a.order - b.order || a.title.localeCompare(b.title));
}

/** Homepage block: the featured guides, linked from the front page. */
export function homepageGuidesHTML(guides) {
  return guides.filter((g) => g.featured).map((g) => card(g, 'guides/')).join('');
}

/** sitemap.xml for every public page. */
export function sitemapXML(guides) {
  const latest = guides.reduce((d, g) => (g.updated > d ? g.updated : d), '2026-10-08');
  const urls = [
    ['', latest],
    ['guides/', latest],
    ...guides.map((g) => [`guides/${g.slug}.html`, g.updated]),
    ['privacy.html', '2026-09-28'],
    ['terms.html', '2026-09-28'],
  ];
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(([p, d]) => `  <url>
    <loc>${CONFIG.siteUrl}${p}</loc>
    <lastmod>${d}</lastmod>
  </url>`).join('\n')}
</urlset>
`;
}

/** An old address that moved: send people (and search engines) to the new one. */
function redirectPage(alias, g) {
  const url = `${CONFIG.siteUrl}guides/${g.slug}.html`;
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${esc(g.title)}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="${url}">
<meta http-equiv="refresh" content="0; url=${g.slug}.html">
</head>
<body>
<p>This guide has moved: <a href="${g.slug}.html">${esc(g.title)}</a>.</p>
</body>
</html>
`;
}

const readJSON = async (path, fallback) => {
  try {
    return JSON.parse(await readFile(path, 'utf8'));
  } catch (e) {
    if (e.code === 'ENOENT') return fallback;
    throw new Error(`${path}: ${e.message}`);
  }
};

/** Loads the data the slots draw from, and checks every photo file exists. */
async function loadData(root) {
  const data = {
    photos: await readJSON(`${root}content/photos.json`, {}),
    market: await readJSON(`${root}content/market.json`, {}),
    str: await readJSON(`${root}content/str-ratings.json`, null),
  };
  delete data.photos._about;
  delete data.market._about;
  for (const [slug, list] of Object.entries(data.photos)) {
    for (const p of list) {
      for (const key of ['src', 'alt', 'width', 'height']) {
        if (!p[key]) throw new Error(`content/photos.json: ${slug} photo needs "${key}"`);
      }
      await access(`${root}${p.src}`).catch(() => { throw new Error(`content/photos.json: ${p.src} not found`); });
    }
  }
  return data;
}

export async function buildGuides(root, { drafts = false } = {}) {
  const guides = await loadGuides(root);
  const testimonials = JSON.parse(await readFile(`${root}assets/data/testimonials.json`, 'utf8'));
  const data = await loadData(root);
  await mkdir(`${root}guides`, { recursive: true });
  const written = new Set(['index.html']);
  for (const g of guides) {
    await writeFile(`${root}guides/${g.slug}.html`, guidePage(g, guides, testimonials, data, { drafts }));
    written.add(`${g.slug}.html`);
    for (const alias of g.aliases) {
      if (written.has(`${alias}.html`) || guides.some((o) => o.slug === alias)) {
        throw new Error(`${g.slug}: alias "${alias}" is already a page`);
      }
      await writeFile(`${root}guides/${alias}.html`, redirectPage(alias, g));
      written.add(`${alias}.html`);
    }
  }
  await writeFile(`${root}guides/index.html`, indexPage(guides));
  // guides/ holds only built pages: remove any left from a guide since deleted.
  for (const f of await readdir(`${root}guides`)) {
    if (f.endsWith('.html') && !written.has(f)) await unlink(`${root}guides/${f}`);
  }
  return guides;
}
