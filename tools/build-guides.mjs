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
 */
import { readFile, writeFile, readdir, mkdir } from 'node:fs/promises';
import { CONFIG } from '../assets/js/config.js';
import { esc, legalLine, footerOfficeLine } from '../assets/js/render.js';

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
  return {
    ...meta,
    published: meta.published || meta.updated,
    reviews: list(meta.reviews),
    related: list(meta.related),
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

/** Splits the body into blocks and renders them; "## Questions" is collected separately. */
function renderBody(md) {
  const blocks = md.trim().split(/\n\s*\n/);
  const html = [];
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
      if (!inQuestions) html.push(`<h2 id="${slugify(heading)}">${inline(heading)}</h2>`);
      // A heading may be followed directly by text in the same block.
      const rest = lines.slice(1).join('\n').trim();
      if (rest) {
        if (inQuestions) throw new Error('Put a blank line after "## Questions"');
        html.push(renderBlock(rest));
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

    html.push(renderBlock(block));
  }
  return { html: html.join('\n'), faqs };
}

function renderBlock(block) {
  const lines = block.split('\n');
  if (/^### /.test(block)) {
    return `<h3>${inline(lines[0].slice(4))}</h3>` + (lines.length > 1 ? `\n${renderBlock(lines.slice(1).join('\n'))}` : '');
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

/* ──────────────────────────────── pages ──────────────────────────────── */

function guidePage(g, all, testimonials) {
  const prefix = '../';
  const url = `${CONFIG.siteUrl}guides/${g.slug}.html`;
  const { html: bodyHTML, faqs } = renderBody(g.body);
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
        image: `${CONFIG.siteUrl}assets/img/social-card.jpg`,
        author: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        publisher: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        ...(g.place && { about: { '@type': 'Place', name: g.place } }),
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
        <p class="guide-cta__title">Questions about ${esc(g.place ? g.place.replace(/, Pennsylvania$/, '') : 'your move')}?</p>
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

export async function buildGuides(root) {
  const guides = await loadGuides(root);
  const testimonials = JSON.parse(await readFile(`${root}assets/data/testimonials.json`, 'utf8'));
  await mkdir(`${root}guides`, { recursive: true });
  for (const g of guides) {
    await writeFile(`${root}guides/${g.slug}.html`, guidePage(g, guides, testimonials));
  }
  await writeFile(`${root}guides/index.html`, indexPage(guides));
  return guides;
}
