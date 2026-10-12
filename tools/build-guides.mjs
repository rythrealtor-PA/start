/**
 * Builds the guide pages — the library of single-question pages AI search and
 * Google draw answers from — out of plain text files, in English and Spanish:
 *
 *   content/guides/stroudsburg.md  ->  guides/stroudsburg.html
 *   content/guias/stroudsburg.md   ->  es/guias/stroudsburg.html
 *
 * Every page gets the same structure, because that structure is what makes a
 * page citable: a direct answer first, a byline and an "updated" date (who
 * says this, and how fresh it is), the reviews, questions and answers, an
 * author box, and schema data (Article, FAQPage, BreadcrumbList) describing
 * all of it. Everything is in the HTML source; nothing is added by script.
 *
 * Run through tools/prerender.mjs, which also refreshes the homepages' guide
 * links and the sitemap.
 *
 * ── Writing a guide ───────────────────────────────────────────────────────
 *
 *   ---
 *   title: Living in Stroudsburg, PA            (the page heading)
 *   seoTitle: Living in Stroudsburg, PA (2026)  (browser tab / Google, ≤ 60)
 *   description: One or two sentences, ≤ 160 characters, for Google.
 *   answer: The short, direct answer shown first on the page.
 *   category: Towns                  (Buying, Selling, Investing, Towns, Counties)
 *   ctaTitle: Questions about ...?    (the contact box's heading, optional)
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
 * ── The Spanish version ───────────────────────────────────────────────────
 *
 * A Spanish guide names the English guide it translates, and takes from it
 * everything that is not words: category, order, featured, place, map,
 * highlight, marker, mapStyle and reviews (and its photos and market
 * numbers). Its related guides are the Spanish versions of the English ones,
 * unless it lists its own by Spanish file name. The two pages link to each
 * other, for visitors and for search engines.
 *
 *   ---
 *   en: stroudsburg                  (the English guide's file name)
 *   title: Vivir en Stroudsburg, PA
 *   description: ...
 *   answer: ...
 *   updated: 2026-10-12
 *   ---
 *   ## Preguntas
 *   ### ¿Una pregunta?
 *   Su respuesta.
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
 *   mapStyle: colors                   (each municipality its own color)
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
import { COUNTIES, countyMap } from './maps.mjs';

/** Category keys, in page order, with their Spanish names. */
const CATEGORIES = {
  Buying: 'Comprar',
  Selling: 'Vender',
  Investing: 'Invertir',
  Towns: 'Pueblos y ciudades',
  Counties: 'Condados',
};
const CATEGORY_ORDER = Object.keys(CATEGORIES);

/* ────────────────────────────── languages ────────────────────────────── */

const listEn = (items) =>
  (items.length < 3 ? items.join(' and ') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`);
const listEs = (items) =>
  (items.length < 3 ? items.join(' y ') : `${items.slice(0, -1).join(', ')} y ${items.at(-1)}`);

const MONTHS_ES = {
  January: 'enero', February: 'febrero', March: 'marzo', April: 'abril', May: 'mayo', June: 'junio',
  July: 'julio', August: 'agosto', September: 'septiembre', October: 'octubre', November: 'noviembre',
  December: 'diciembre',
};
/** "October 2026" -> "octubre de 2026". */
const monthYearEs = (s) => s.replace(/^(\w+) (\d{4})$/, (m, month, year) => (MONTHS_ES[month] ? `${MONTHS_ES[month]} de ${year}` : m));

/** "Monroe County" -> "el condado de Monroe". */
const countyEs = (name) => `el condado de ${name.replace(/ County$/, '')}`;
/** "de" before a name, with Spanish's "de el" -> "del". */
const de = (name) => `de ${name}`.replace(/^de el /, 'del ');
const countiesEs = () => listEs(CONFIG.serviceAreas.counties.map((c) => c.replace(/ County$/, '')));

/**
 * Everything the page templates say, per language. `dir` is where the pages
 * go; `root` leads from a guide back to the site root, `home` to that
 * language's homepage.
 */
const L = {
  en: {
    lang: 'en',
    hreflang: 'en',
    locale: 'en_US',
    inLanguage: 'en-US',
    dir: 'guides/',
    homePath: '',
    root: '../',
    home: '../',
    category: (key) => key,
    date: (iso) => new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
    }),
    skip: 'Skip to content',
    homeCrumb: 'Home',
    guidesCrumb: 'Guides',
    crumbsLabel: 'Breadcrumb',
    navLabel: 'Site',
    allGuides: '&larr; All guides',
    backHome: '&larr; Home',
    contact: 'Contact',
    switchTo: { label: 'Español', lang: 'es', title: 'Leer esta página en español' },
    by: 'By',
    updated: 'Updated',
    inShort: 'In short:',
    clientsSay: ['what-clients-say', 'What clients say'],
    questions: ['questions', 'Questions'],
    related: ['related-guides', 'Related guides'],
    ctaDefault: (places) => `Questions about ${places.length ? listEn(places) : 'your move'}?`,
    ctaText: (phone) => `Ryth answers in English or Spanish — call or text
        ${phone}, or send a message.`,
    ctaButton: 'Contact Ryth',
    aboutAuthor: 'About the author',
    writtenBy: 'Written by',
    bio: () => `Bilingual (English and Spanish) REALTOR<sup>&reg;</sup> with ${esc(CONFIG.brokerage)},
        serving ${esc(CONFIG.serviceAreas.counties.join(' and '))}. Specializes in luxury real
        estate, real estate investors, and Spanish-speaking buyers and sellers. In 2025, Ryth and his team
        at ${esc(CONFIG.team)} closed 149 transactions totaling $49&nbsp;million in sales.`,
    license: 'License',
    footerLine: 'English &amp; Español · Equal Housing Opportunity',
    footerLinks: (root) => `<a href="${root}guides/">Guides</a>
        <a href="${root}privacy.html">Privacy Policy</a>
        <a href="${root}terms.html">Terms of Use</a>
        <a href="${root}es/" hreflang="es" lang="es">Español</a>`,
    indexTitle: 'Real Estate Guides for Monroe & Northampton County, PA',
    indexDescription:
      'Local guides by Ryth Vara, REALTOR®: towns and counties, buying, selling, closing costs and investing in Monroe and Northampton County, PA.',
    indexIntro: () => `Straight answers about buying, selling and investing in
    ${esc(CONFIG.serviceAreas.counties.join(' and '))} — town by town, in plain language.`,
    tableLabel: 'Table',
    mapLabel: (county) => `Map of ${county}`,
    mapTitle: (county) => `Map of ${county}, Pennsylvania, by municipality`,
    mapCaption: (hl, county, marker) =>
      `${listEn(hl)} ${hl.length > 1 ? 'are' : 'is'} highlighted on this map of ${county}${marker ? `; the dot marks ${marker}` : ''}.`,
    mapAll: (county) => `The municipalities of ${county}, from US Census boundaries.`,
    mapKinds: [['city', 'Cities'], ['borough', 'Boroughs'], ['township', 'Townships']],
    mapKey: 'Numbers on the map:',
    mapHint: 'Swipe sideways to see the whole county.',
    strNames: { green: 'Green: easier', yellow: 'Yellow: possible, with limits', red: 'Red: very difficult' },
    strTitle: (county) => `Short-term rental rules by municipality in ${county}: green, yellow or red`,
    strLabel: (county) => `Short-term rental map of ${county}`,
    strNote: (asOf) => `Ryth's assessment as of ${asOf}. Rules change; confirm with the township before you buy.`,
    strTableLabel: 'Short-term rentals by municipality',
    strCaption: (county, asOf) => `Short-term rentals by municipality, ${county}: Ryth's assessment as of ${asOf}`,
    strHead: ['Municipality', 'Rating', 'Why'],
    asOf: (s) => s,
    countyName: (name) => name,
    why: (r) => r.why,
    market: ['Median sale price', 'Homes sold in the last 12 months', 'Average days on market', 'Source'],
    marketText: (m) => [m.scope, m.period, m.source],
    photo: (p) => ({ alt: p.alt, caption: p.caption }),
    moved: 'This guide has moved:',
  },
  es: {
    lang: 'es',
    hreflang: 'es',
    locale: 'es_LA',
    inLanguage: 'es',
    dir: 'es/guias/',
    homePath: 'es/',
    root: '../../',
    home: '../',
    category: (key) => CATEGORIES[key],
    date: (iso) => new Date(`${iso}T12:00:00Z`).toLocaleDateString('es', {
      year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
    }),
    skip: 'Saltar al contenido',
    homeCrumb: 'Inicio',
    guidesCrumb: 'Guías',
    crumbsLabel: 'Ruta de navegación',
    navLabel: 'Sitio',
    allGuides: '&larr; Todas las guías',
    backHome: '&larr; Inicio',
    contact: 'Contacto',
    switchTo: { label: 'English', lang: 'en', title: 'Read this page in English' },
    by: 'Por',
    updated: 'Actualizado el',
    inShort: 'En pocas palabras:',
    clientsSay: ['lo-que-dicen-los-clientes', 'Lo que dicen los clientes'],
    questions: ['preguntas', 'Preguntas frecuentes'],
    related: ['guias-relacionadas', 'Guías relacionadas'],
    ctaDefault: () => '¿Tiene preguntas sobre su compra o su venta?',
    ctaText: (phone) => `Ryth le atiende en español o en inglés. Llame o escriba por
        mensaje de texto al ${phone}, o envíe un mensaje.`,
    ctaButton: 'Contactar a Ryth',
    aboutAuthor: 'Sobre el autor',
    writtenBy: 'Escrito por',
    bio: () => `REALTOR<sup>&reg;</sup> bilingüe (español e inglés) con ${esc(CONFIG.brokerage)}, que atiende
        los condados de ${esc(countiesEs())}. Se especializa en bienes raíces de lujo, inversionistas
        y compradores y vendedores de habla hispana. En 2025, Ryth y su equipo en ${esc(CONFIG.team)}
        cerraron 149 transacciones por un total de $49&nbsp;millones en ventas.`,
    license: 'Licencia',
    footerLine: 'English &amp; Español · Igualdad de oportunidades en la vivienda',
    footerLinks: (root) => `<a href="${root}es/guias/">Guías</a>
        <a href="${root}privacy.html" hreflang="en">Privacidad (en inglés)</a>
        <a href="${root}terms.html" hreflang="en">Términos de uso (en inglés)</a>
        <a href="${root}" hreflang="en" lang="en">English</a>`,
    indexTitle: 'Guías de bienes raíces: condados de Monroe y Northampton, PA',
    indexDescription:
      'Guías de Ryth Vara, REALTOR®, en español: comprar, vender, costos de cierre e invertir en los condados de Monroe y Northampton, Pensilvania.',
    indexIntro: () => `Respuestas claras sobre comprar, vender e invertir en los condados de
    ${esc(countiesEs())}, pueblo por pueblo y en palabras sencillas.`,
    tableLabel: 'Tabla',
    mapLabel: (county) => `Mapa ${de(county)}`,
    mapTitle: (county) => `Mapa ${de(county)}, Pensilvania, por municipio`,
    mapCaption: (hl, county, marker) =>
      `En este mapa ${de(county)} se ${hl.length > 1 ? 'resaltan' : 'resalta'} ${listEs(hl)}${marker ? `; el punto marca ${marker}` : ''}.`,
    mapAll: (county) => `Los municipios ${de(county)}, según los límites de la Oficina del Censo de EE.&nbsp;UU.`,
    mapKinds: [['city', 'Ciudades'], ['borough', 'Boroughs'], ['township', 'Townships']],
    mapKey: 'Números en el mapa:',
    mapHint: 'Deslice hacia los lados para ver todo el condado.',
    strNames: { green: 'Verde: más fácil', yellow: 'Amarillo: posible, con límites', red: 'Rojo: muy difícil' },
    strTitle: (county) => `Reglas de alquiler a corto plazo por municipio en ${county}: verde, amarillo o rojo`,
    strLabel: (county) => `Mapa de alquileres a corto plazo ${de(county)}`,
    strNote: (asOf) => `Evaluación de Ryth a ${asOf}. Las reglas cambian; confirme con el municipio antes de comprar.`,
    strTableLabel: 'Alquileres a corto plazo por municipio',
    strCaption: (county, asOf) => `Alquileres a corto plazo por municipio en ${county}: evaluación de Ryth a ${asOf}`,
    strHead: ['Municipio', 'Calificación', 'Motivo'],
    asOf: monthYearEs,
    countyName: countyEs,
    why: (r, name) => {
      if (!r.whyEs) throw new Error(`content/str-ratings.json: "${name}" needs "whyEs" (the reason in Spanish)`);
      return r.whyEs;
    },
    market: ['Precio de venta mediano', 'Casas vendidas en los últimos 12 meses', 'Días promedio en el mercado', 'Fuente'],
    marketText: (m) => [m.scopeEs || m.scope, m.periodEs || m.period, m.sourceEs || m.source],
    photo: (p) => ({ alt: p.altEs || p.alt, caption: p.captionEs || p.caption }),
    moved: 'Esta guía cambió de dirección:',
  },
};

/** Where a guide is published, from the site root. */
const pagePath = (g) => `${L[g.lang].dir}${g.slug}.html`;
const urlOf = (g) => `${CONFIG.siteUrl}${pagePath(g)}`;

/** A quote in English on a page in another language is marked as English. */
const quoteLang = (t, quote) => (t.lang !== 'en' && !/[¿¡áéíóúñ]/i.test(quote) ? ' lang="en"' : '');

/* ───────────────────────────── text → HTML ───────────────────────────── */

function parseFrontMatter(text, file) {
  const m = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) throw new Error(`${file}: missing the --- front matter block`);
  const meta = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.*)$/);
    if (kv) meta[kv[1]] = kv[2].trim();
  }
  return { meta, body: m[2] };
}

/** Checks the front matter and turns lists and flags into values. */
function normalize(meta, file) {
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
  };
}

/** **bold**, *italic*, [text](url) — on already-escaped text. */
function inline(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*(?!\s)(.+?)\*/g, '$1<em>$2</em>')
    .replace(/\[(.+?)\]\((.+?)\)/g, (_, label, href) => `<a href="${href}">${label}</a>`);
}

/** Heading text -> id. Accents are dropped, so "Vivir aquí" -> "vivir-aqui". */
const slugify = (s) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

/** The heading that starts the questions: "## Questions" or "## Preguntas". */
const QUESTIONS = /^(questions|preguntas( frecuentes)?)$/i;

/**
 * Splits the body into blocks and renders them; "## Questions" is collected
 * separately. slot(name) renders a {{name}} line; a section whose blocks all
 * render empty is left out, heading and all.
 */
function renderBody(md, slot, t) {
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
      inQuestions = QUESTIONS.test(heading);
      current = null;
      if (!inQuestions) sections.push({ heading, html: [] });
      // A heading may be followed directly by text in the same block.
      const rest = lines.slice(1).join('\n').trim();
      if (rest) {
        if (inQuestions) throw new Error(`Put a blank line after "## ${heading}"`);
        sections.at(-1).html.push(renderBlock(rest, slot, t));
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

    sections.at(-1).html.push(renderBlock(block, slot, t));
  }

  const html = sections
    .filter((sec) => sec.html.some(Boolean))
    .map((sec) => [sec.heading && `<h2 id="${slugify(sec.heading)}">${inline(sec.heading)}</h2>`, ...sec.html.filter(Boolean)]
      .filter(Boolean).join('\n'))
    .join('\n');
  return { html, faqs };
}

function renderTable(lines, t) {
  const cells = (l) => l.replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
  const [head, , ...rows] = lines;
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="${t.tableLabel}: ${esc(cells(head).join(', '))}"><table>
  <thead><tr>${cells(head).map((c) => `<th scope="col">${inline(c)}</th>`).join('')}</tr></thead>
  <tbody>
${rows.map((r) => `    <tr>${cells(r).map((c, i) => (i === 0 ? `<th scope="row">${inline(c)}</th>` : `<td>${inline(c)}</td>`)).join('')}</tr>`).join('\n')}
  </tbody>
</table></div>`;
}

function renderBlock(block, slot, t) {
  const lines = block.split('\n');
  const slotMatch = block.match(/^\{\{([\w-]+)\}\}$/);
  if (slotMatch) return slot(slotMatch[1]);
  if (/^### /.test(block)) {
    return `<h3>${inline(lines[0].slice(4))}</h3>` + (lines.length > 1 ? `\n${renderBlock(lines.slice(1).join('\n'), slot, t)}` : '');
  }
  if (lines.length > 2 && lines.every((l) => /^\|.*\|$/.test(l)) && /^\|[\s:|-]+\|$/.test(lines[1])) {
    return renderTable(lines, t);
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

const jsonLd = (data) =>
  `<script type="application/ld+json">\n${JSON.stringify(data, null, 2).replace(/</g, '\\u003c')}\n</script>`;

/**
 * `alternates` is [[hreflang, url], …] for the page in each language; the
 * English one doubles as x-default, the version for everyone else.
 */
function head({ t, title, description, canonical, type = 'article', schema, alternates = [] }) {
  const prefix = t.root;
  const other = alternates.find(([lang]) => lang !== t.hreflang);
  const en = alternates.find(([lang]) => lang === 'en');
  return `<!doctype html>
<html lang="${t.lang}">
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
${alternates.map(([lang, href]) => `<link rel="alternate" hreflang="${lang}" href="${href}">\n`).join('')}${en ? `<link rel="alternate" hreflang="x-default" href="${en[1]}">\n` : ''}<meta property="og:site_name" content="Ryth Vara Real Estate">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:type" content="${type}">
<meta property="og:locale" content="${t.locale}">
${other ? `<meta property="og:locale:alternate" content="${L[other[0]].locale}">\n` : ''}<meta property="og:url" content="${canonical}">
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
<a class="skip-link" href="#main">${t.skip}</a>
`;
}

/** The link to the same page in the other language, or '' if there is none. */
function switchLink(t, href) {
  if (!href) return '';
  const s = t.switchTo;
  return `\n      <a class="page-header__back page-header__lang" href="${href}" hreflang="${s.lang}" lang="${s.lang}" title="${s.title}">${s.label}</a>`;
}

function header(t, backHref, backLabel, otherHref) {
  return `
<header class="page-header">
  <div class="wrap">
    <a class="page-header__name" href="${t.home}">Ryth Vara</a>
    <nav class="page-header__nav" aria-label="${t.navLabel}">
      <a class="page-header__back" href="${backHref}">${backLabel}</a>
      <a class="page-header__back" href="${t.home}#contact">${t.contact}</a>${switchLink(t, otherHref)}
    </nav>
  </div>
</header>
`;
}

function footer(t) {
  const prefix = t.root;
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
      <p class="footer__office">${esc(footerOfficeLine(CONFIG, t.lang))}</p>
      <p data-footer-legal>${esc(legalLine(CONFIG, t.lang))}</p>
      <p>&copy; <span data-year>${new Date().getUTCFullYear()}</span> · ${t.footerLine}</p>
      <p class="footer__links">
        ${t.footerLinks(prefix)}
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
          <span class="guide-card__kicker">${esc(L[g.lang].category(g.category))}</span>
          <span class="guide-card__title">${esc(g.title)}</span>
          <span class="guide-card__text">${esc(g.description)}</span>
        </a>`;
}

function authorBox(t) {
  return `
    <aside class="guide-author" aria-label="${t.aboutAuthor}">
      <img class="guide-author__photo" src="${t.root}${CONFIG.portrait}" alt="${esc(CONFIG.name)}"
           width="96" height="120" loading="lazy">
      <div>
        <p class="guide-author__name">${t.writtenBy} ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup></p>
        <p>${t.bio()}</p>
        <p><a href="tel:${CONFIG.contact.phoneHref}">${esc(CONFIG.contact.phone)}</a> ·
        <a href="mailto:${CONFIG.contact.email}">${esc(CONFIG.contact.email)}</a> ·
        ${t.license} ${esc(CONFIG.license)}</p>
      </div>
    </aside>`;
}

/* ──────────────────────────────── slots ──────────────────────────────── */

/** "Numbers on the map: 1 Delaware Water Gap Borough, ..." */
function mapKey(items, t) {
  const nums = items.filter((i) => i.num).sort((a, b) => a.num - b.num);
  return nums.length ? ` ${t.mapKey} ${nums.map((i) => `${i.num} ${esc(i.full)}`).join(', ')}.` : '';
}

const hint = (t) => ` <span class="cmap__hint">${t.mapHint}</span>`;

function mapSlot(g, t) {
  if (!g.map) return '';
  const county = esc(t.countyName(COUNTIES[g.map].name));
  const m = countyMap(g.map, {
    highlight: g.highlight,
    marker: g.marker,
    colors: /^colou?rs$/i.test(g.mapStyle || ''),
    idPrefix: `map-${g.slug}`,
    title: t.mapTitle(t.countyName(COUNTIES[g.map].name)),
  });
  const hl = m.items.filter((i) => i.hl).map((i) => esc(i.full));
  const caption = g.mapCaption
    ? esc(g.mapCaption)
    : hl.length
      ? t.mapCaption(hl, county, g.marker && esc(g.marker.label))
      : t.mapAll(county);
  // A county page lists every municipality under the map, in text.
  const list = hl.length ? '' : `\n<div class="cmap__list">${t.mapKinds
    .map(([kind, label]) => {
      const of = m.items.filter((i) => i.kind === kind);
      return of.length ? `<p>${label} (${of.length}): ${of.map((i) => `${esc(i.base)}${i.num ? ` (${i.num})` : ''}`).join(', ')}.</p>` : '';
    }).join('')}</div>`;
  return `<figure class="cmap">
  <div class="cmap__scroll" tabindex="0" role="region" aria-label="${t.mapLabel(county)}">${m.svg}</div>
  <figcaption>${caption}${mapKey(m.items, t)}${hint(t)}</figcaption>
</figure>${list}`;
}

const STR_ORDER = ['green', 'yellow', 'red'];

function strMapSlot(data, t) {
  if (!data) return '';
  const ratings = Object.fromEntries(Object.entries(data.ratings).map(([name, r]) => [name, r.color]));
  const county = t.countyName(COUNTIES[data.county].name);
  const m = countyMap(data.county, { ratings, idPrefix: 'map-str', title: t.strTitle(county) });
  return `<figure class="cmap">
  <div class="cmap__scroll" tabindex="0" role="region" aria-label="${esc(t.strLabel(county))}">${m.svg}</div>
  <figcaption>
    <ul class="str-legend">${STR_ORDER.map((c) => `<li><span class="str-swatch str-swatch--${c}" aria-hidden="true"></span>${t.strNames[c]}</li>`).join('')}</ul>
    ${esc(t.strNote(t.asOf(data.asOf)))}${mapKey(m.items, t)}${hint(t)}
  </figcaption>
</figure>`;
}

function strTableSlot(data, t) {
  if (!data) return '';
  const full = (name) => name.replace(/^(.*) (township|borough)$/, (_, b, k) => `${b} ${k === 'township' ? 'Township' : 'Borough'}`);
  const rows = Object.entries(data.ratings)
    .sort(([a, ra], [b, rb]) => STR_ORDER.indexOf(ra.color) - STR_ORDER.indexOf(rb.color) || a.localeCompare(b));
  const county = t.countyName(COUNTIES[data.county].name);
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="${t.strTableLabel}"><table class="str-table">
  <caption>${esc(t.strCaption(county, t.asOf(data.asOf)))}</caption>
  <thead><tr>${t.strHead.map((h) => `<th scope="col">${h}</th>`).join('')}</tr></thead>
  <tbody>
${rows.map(([name, r]) => `    <tr><th scope="row">${esc(full(name))}</th><td><span class="str-swatch str-swatch--${r.color}" aria-hidden="true"></span>${t.strNames[r.color]}</td><td>${inline(t.why(r, name))}</td></tr>`).join('\n')}
  </tbody>
</table></div>`;
}

function marketSlot(m, t) {
  if (!m) return '';
  const n = (v) => Number(v).toLocaleString('en-US');
  const [scope, period, source] = t.marketText(m);
  return `<div class="stats">
  <p class="stat"><span class="stat__value">$${n(m.median)}</span><span class="stat__label">${t.market[0]}</span></p>
  <p class="stat"><span class="stat__value">${n(m.sold)}</span><span class="stat__label">${t.market[1]}</span></p>
  <p class="stat"><span class="stat__value">${n(m.dom)}</span><span class="stat__label">${t.market[2]}</span></p>
</div>
<p class="stats__note">${esc(scope)}, ${esc(period)}. ${t.market[3]}: ${esc(source)}.</p>`;
}

function photoFigure(p, eager, t) {
  const { alt, caption: text } = t.photo(p);
  const caption = [text && esc(text), p.credit && `<span class="guide-photo__credit">${inline(p.credit)}</span>`]
    .filter(Boolean).join(' ');
  return `<figure class="guide-photo">
  <img src="${t.root}${esc(p.src)}" alt="${esc(alt)}" width="${p.width}" height="${p.height}" loading="${eager ? 'eager' : 'lazy'}" decoding="async">${caption ? `
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

/** [[hreflang, url], …] for a guide and its translation, English first. */
function alternatesOf(g) {
  if (!g.pair) return [];
  const [en, es] = g.lang === 'en' ? [g, g.pair] : [g.pair, g];
  return [[L.en.hreflang, urlOf(en)], [L.es.hreflang, urlOf(es)]];
}

function guidePage(g, all, testimonials, data, { drafts = false } = {}) {
  const t = L[g.lang];
  const url = urlOf(g);
  // Photos and market numbers are listed under the English guide's name.
  const key = g.lang === 'en' ? g.slug : g.en;
  const photos = data.photos[key] || [];
  const slots = {
    photo: () => (photos[0] ? photoFigure(photos[0], true, t) : ''),
    photos: () => (photos.length ? `<div class="guide-photos">\n${photos.map((p) => photoFigure(p, false, t)).join('\n')}\n</div>` : ''),
    map: () => mapSlot(g, t),
    market: () => marketSlot(data.market[key], t),
    take: () => takeSlot(g.take),
    'str-map': () => strMapSlot(data.str, t),
    'str-table': () => strTableSlot(data.str, t),
  };
  const slot = (name) => {
    if (!slots[name]) throw new Error(`${g.slug}: unknown slot {{${name}}}`);
    const html = slots[name]();
    return html || (drafts && PENDING[name]
      ? `<p style="border:1px dashed #b08d57;padding:1.25rem;color:#d4b483">Pending: ${esc(PENDING[name])}</p>`
      : '');
  };
  const { html: bodyHTML, faqs } = renderBody(g.body, slot, t);
  const agentId = `${CONFIG.siteUrl}#agent`;

  const reviews = g.reviews.map((name) => {
    const r = testimonials.find((x) => x.name === name);
    if (!r) throw new Error(`${g.slug}: no testimonial named "${name}"`);
    return r;
  });
  const related = g.related.map((slug) => {
    const r = all.find((x) => x.slug === slug);
    if (!r) throw new Error(`${pagePath(g)}: related guide "${slug}" does not exist`);
    return r;
  });

  const schema = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        headline: g.title,
        description: g.description,
        inLanguage: t.inLanguage,
        datePublished: g.published,
        dateModified: g.updated,
        mainEntityOfPage: url,
        image: `${CONFIG.siteUrl}${photos[0] ? photos[0].src : 'assets/img/social-card.jpg'}`,
        author: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        publisher: { '@type': 'RealEstateAgent', '@id': agentId, name: CONFIG.name, url: CONFIG.siteUrl },
        ...(g.pair && { [g.lang === 'en' ? 'workTranslation' : 'translationOfWork']: { '@type': 'Article', url: urlOf(g.pair) } }),
        ...(g.places.length && {
          about: g.places.length === 1
            ? { '@type': 'Place', name: g.places[0] }
            : g.places.map((name) => ({ '@type': 'Place', name })),
        }),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: t.homeCrumb, item: `${CONFIG.siteUrl}${t.homePath}` },
          { '@type': 'ListItem', position: 2, name: t.guidesCrumb, item: `${CONFIG.siteUrl}${t.dir}` },
          { '@type': 'ListItem', position: 3, name: g.title, item: url },
        ],
      },
      ...(faqs.length
        ? [{
          '@type': 'FAQPage',
          inLanguage: t.inLanguage,
          mainEntity: faqs.map((f) => ({
            '@type': 'Question',
            name: f.q,
            acceptedAnswer: { '@type': 'Answer', text: f.a.join(' ').replace(/\*\*|\*|\[|\]\(.*?\)/g, '') },
          })),
        }]
        : []),
    ],
  };

  const ctaTitle = g.ctaTitle || t.ctaDefault(g.places.map((p) => p.replace(/, Pennsylvania$/, '')));
  const phoneLink = `<a href="tel:${CONFIG.contact.phoneHref}">${esc(CONFIG.contact.phone)}</a>`;

  return head({
    t,
    title: g.seoTitle || `${g.title} | Ryth Vara, REALTOR®`,
    description: g.description,
    canonical: url,
    schema,
    alternates: alternatesOf(g),
  }) + header(t, './', t.allGuides, g.pair && `${t.root}${pagePath(g.pair)}`) + `
<main id="main" class="doc guide">
  <div class="wrap">
    <nav class="crumbs" aria-label="${t.crumbsLabel}">
      <a href="${t.home}">${t.homeCrumb}</a> <span aria-hidden="true">/</span>
      <a href="./">${t.guidesCrumb}</a> <span aria-hidden="true">/</span>
      <span aria-current="page">${esc(g.title)}</span>
    </nav>

    <h1 class="section__title">${esc(g.title)}</h1>
    <p class="doc__meta">${t.by} ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup> · ${esc(CONFIG.brokerage)} ·
      ${t.updated} <time datetime="${g.updated}">${t.date(g.updated)}</time></p>

    <div class="doc__body">
      <p class="guide__answer"><strong>${t.inShort}</strong> ${inline(g.answer)}</p>

${bodyHTML.split('\n').map((l) => `      ${l}`).join('\n')}
${reviews.length ? `
      <h2 id="${t.clientsSay[0]}">${t.clientsSay[1]}</h2>
${reviews.map((r) => `      <figure class="guide-quote">
        <blockquote${quoteLang(t, r.quote)}>${esc(r.quote)}</blockquote>
        <figcaption>${esc(r.name)}</figcaption>
      </figure>`).join('\n')}` : ''}
${faqs.length ? `
      <h2 id="${t.questions[0]}">${t.questions[1]}</h2>
      <div class="faq__list">
${faqs.map((f) => `        <details class="faq__item">
          <summary class="faq__q">${inline(f.q)}</summary>
          <div class="faq__a">${f.a.map((p) => `<p>${inline(p)}</p>`).join('')}</div>
        </details>`).join('\n')}
      </div>` : ''}

      <div class="guide-cta">
        <p class="guide-cta__title">${esc(ctaTitle)}</p>
        <p>${t.ctaText(phoneLink)}</p>
        <a class="button button--primary" href="${t.home}#contact">${t.ctaButton}</a>
      </div>
${related.length ? `
      <h2 id="${t.related[0]}">${t.related[1]}</h2>
      <div class="guide-grid">${related.map((r) => card(r, '')).join('')}
      </div>` : ''}
${authorBox(t)}
    </div>
  </div>
</main>
` + footer(t);
}

function indexPage(guides, lang) {
  const t = L[lang];
  const other = L[lang === 'en' ? 'es' : 'en'];
  const url = `${CONFIG.siteUrl}${t.dir}`;
  const { indexTitle: title, indexDescription: description } = t;
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: title,
    description,
    url,
    inLanguage: t.inLanguage,
    author: { '@type': 'RealEstateAgent', '@id': `${CONFIG.siteUrl}#agent`, name: CONFIG.name },
    hasPart: guides.map((g) => ({ '@type': 'Article', headline: g.title, url: urlOf(g) })),
  };
  const groups = CATEGORY_ORDER
    .map((c) => [c, guides.filter((g) => g.category === c)])
    .filter(([, list]) => list.length);
  const alternates = [[L.en.hreflang, `${CONFIG.siteUrl}${L.en.dir}`], [L.es.hreflang, `${CONFIG.siteUrl}${L.es.dir}`]];

  return head({ t, title, description, canonical: url, type: 'website', schema, alternates })
    + header(t, t.home, t.backHome, `${t.root}${other.dir}`) + `
<main id="main" class="doc guide">
  <div class="wrap">
    <nav class="crumbs" aria-label="${t.crumbsLabel}">
      <a href="${t.home}">${t.homeCrumb}</a> <span aria-hidden="true">/</span>
      <span aria-current="page">${t.guidesCrumb}</span>
    </nav>
    <h1 class="section__title">${esc(title)}</h1>
    <p class="doc__meta">${t.by} ${esc(CONFIG.name)}, REALTOR<sup>&reg;</sup> · ${esc(CONFIG.brokerage)}</p>
    <p class="guides__intro">${t.indexIntro()}</p>
${groups.map(([c, list]) => `
    <h2 class="guides__group">${esc(t.category(c))}</h2>
    <div class="guide-grid">${list.map((g) => card(g, '')).join('')}
    </div>`).join('\n')}
${authorBox(t)}
  </div>
</main>
` + footer(t);
}

/* ───────────────────────────────── build ─────────────────────────────── */

const sortGuides = (list) => list.sort((a, b) =>
  CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category)
  || a.order - b.order || a.title.localeCompare(b.title));

async function readSources(dir) {
  const files = (await readdir(dir).catch(() => [])).filter((f) => f.endsWith('.md')).sort();
  return Promise.all(files.map(async (f) => ({
    file: f,
    slug: f.replace(/\.md$/, ''),
    ...parseFrontMatter(await readFile(dir + f, 'utf8'), f),
  })));
}

/** What a Spanish guide takes from the English one it translates. */
const INHERITED = ['category', 'order', 'featured', 'place', 'map', 'highlight', 'marker', 'mapStyle', 'reviews'];

/** The front matter text a normalized field came from, for inheriting. */
function rawOf(g, key) {
  switch (key) {
    case 'featured': return g.featured ? 'yes' : '';
    case 'order': return String(g.order);
    case 'place': return g.places.join('; ');
    case 'reviews': case 'highlight': return g[key].join(', ');
    case 'marker': return g.marker ? `${g.marker.label} @ ${g.marker.lat}, ${g.marker.lon}` : '';
    default: return g[key];
  }
}

/**
 * Both languages, each sorted for display. Every Spanish guide is linked to
 * its English original (and back) through `pair`.
 */
export async function loadGuides(root) {
  const en = (await readSources(`${root}content/guides/`))
    .map((s) => ({ lang: 'en', slug: s.slug, body: s.body, ...normalize(s.meta, `content/guides/${s.file}`) }));
  const es = [];
  for (const s of await readSources(`${root}content/guias/`)) {
    const file = `content/guias/${s.file}`;
    const original = en.find((g) => g.slug === s.meta.en);
    if (!original) throw new Error(`${file}: "en: ${s.meta.en ?? ''}" must name a guide in content/guides/`);
    if (original.pair) throw new Error(`${file}: ${original.slug} already has a Spanish version`);
    const meta = { ...s.meta };
    for (const key of INHERITED) if (!(key in meta) && original[key] !== undefined) meta[key] = rawOf(original, key);
    const g = { lang: 'es', slug: s.slug, en: original.slug, body: s.body, ...normalize(meta, file) };
    g.ownRelated = Boolean(s.meta.related);
    g.pair = original;
    original.pair = g;
    es.push(g);
  }
  // Unless a Spanish guide lists its own, its related guides are the Spanish
  // versions of the English guide's (any not yet translated are skipped).
  for (const g of es) {
    if (!g.ownRelated) g.related = g.pair.related.map((r) => es.find((x) => x.en === r)?.slug).filter(Boolean);
  }
  return { en: sortGuides(en), es: sortGuides(es) };
}

/** Homepage block: the featured guides, linked from the front page. */
export function homepageGuidesHTML(guides, prefix = 'guides/') {
  return guides.filter((g) => g.featured).map((g) => card(g, prefix)).join('');
}

/**
 * sitemap.xml for every public page. A page that exists in both languages
 * lists both, which is how search engines learn they are one page.
 */
export function sitemapXML({ en, es }) {
  const latest = (list) => list.reduce((d, g) => (g.updated > d ? g.updated : d), '2026-10-08');
  const site = CONFIG.siteUrl;
  const pair = (enPath, esPath) => [['en', site + enPath], ['es', site + esPath], ['x-default', site + enPath]];
  const guideAlts = (g) => (g.pair ? [...alternatesOf(g), ['x-default', alternatesOf(g)[0][1]]] : []);
  const urls = [
    ['', latest(en), pair('', 'es/')],
    ['es/', latest(es), pair('', 'es/')],
    ['guides/', latest(en), pair('guides/', 'es/guias/')],
    ['es/guias/', latest(es), pair('guides/', 'es/guias/')],
    ...[...en, ...es].map((g) => [pagePath(g), g.updated, guideAlts(g)]),
    ['privacy.html', '2026-09-28', []],
    ['terms.html', '2026-09-28', []],
  ];
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.map(([p, d, alts]) => `  <url>
    <loc>${site}${p}</loc>
    <lastmod>${d}</lastmod>
${alts.map(([lang, href]) => `    <xhtml:link rel="alternate" hreflang="${lang}" href="${href}"/>\n`).join('')}  </url>`).join('\n')}
</urlset>
`;
}

/** An old address that moved: send people (and search engines) to the new one. */
function redirectPage(g) {
  const t = L[g.lang];
  return `<!doctype html>
<html lang="${t.lang}">
<head>
<meta charset="utf-8">
<title>${esc(g.title)}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="${urlOf(g)}">
<meta http-equiv="refresh" content="0; url=${g.slug}.html">
</head>
<body>
<p>${t.moved} <a href="${g.slug}.html">${esc(g.title)}</a>.</p>
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

/** Writes one language's pages into its folder and clears out stale ones. */
async function writeLanguage(root, lang, guides, testimonials, data, opts) {
  const dir = `${root}${L[lang].dir}`;
  await mkdir(dir, { recursive: true });
  const written = new Set(['index.html']);
  for (const g of guides) {
    await writeFile(`${dir}${g.slug}.html`, guidePage(g, guides, testimonials, data, opts));
    written.add(`${g.slug}.html`);
    for (const alias of g.aliases) {
      if (written.has(`${alias}.html`) || guides.some((o) => o.slug === alias)) {
        throw new Error(`${g.slug}: alias "${alias}" is already a page`);
      }
      await writeFile(`${dir}${alias}.html`, redirectPage(g));
      written.add(`${alias}.html`);
    }
  }
  await writeFile(`${dir}index.html`, indexPage(guides, lang));
  // The folder holds only built pages: remove any left from a guide since deleted.
  for (const f of await readdir(dir)) {
    if (f.endsWith('.html') && !written.has(f)) await unlink(`${dir}${f}`);
  }
}

/** Builds every guide page in both languages; returns { en, es }. */
export async function buildGuides(root, { drafts = false } = {}) {
  const guides = await loadGuides(root);
  const testimonials = JSON.parse(await readFile(`${root}assets/data/testimonials.json`, 'utf8'));
  const data = await loadData(root);
  await writeLanguage(root, 'en', guides.en, testimonials, data, { drafts });
  await writeLanguage(root, 'es', guides.es, testimonials, data, { drafts });
  return guides;
}
