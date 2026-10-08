/**
 * Markup for every piece of credibility text that comes from data: contact
 * facts, social links, the licence line, listings and testimonials.
 *
 * Pure string functions with no DOM access, so the same code runs in two
 * places and cannot drift:
 *   - tools/prerender.mjs writes it into index.html, so the text is in the
 *     HTML source that search engines and link previews read, not only
 *     injected by JavaScript after the page opens;
 *   - admin.js rewrites those same blocks in index.html on every Publish.
 *
 * In index.html each block sits between <!-- prerender:NAME --> and
 * <!-- /prerender:NAME --> markers; replaceBlock() swaps what is inside.
 */

/** Escapes text before it goes into HTML. */
export const esc = (value = '') =>
  String(value).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const fmtBaths = (n) => (Number.isInteger(n) ? String(n) : Number(n).toFixed(1));

/* ─────────────────────────── contact and licence ─────────────────────── */

function fact(label, value, href) {
  if (!value) return '';
  const body = href
    ? `<a class="facts__link" href="${esc(href)}">${esc(value)}</a>`
    : esc(value);
  return `
          <div class="facts__row">
            <dt class="facts__label">${label}</dt>
            <dd class="facts__value">${body}</dd>
          </div>`;
}

/**
 * Contact details beside the portrait. Deliberately just these three — the bio
 * names the brokerage and area, and the brokerage and licence number are in
 * the footer, which is what Pennsylvania's advertising rule requires.
 */
export function factsHTML(config) {
  const { contact, languages } = config;
  return [
    fact('Email', contact.email, `mailto:${contact.email}`),
    fact('Phone', contact.phone, contact.phoneHref ? `tel:${contact.phoneHref}` : null),
    fact('Office', officeLine(config), mapsUrl(config)),
    fact('Hours', config.hours),
    fact('Languages', languages.join(' · ')),
  ].join('');
}

/**
 * The footer's office line: address, hours and the area served — the three
 * things local search looks for in a footer.
 */
export function footerOfficeLine(config) {
  return [
    officeLine(config),
    config.hours,
    `Serving ${config.serviceAreas.counties.join(' & ')}`,
  ].filter(Boolean).join(' · ');
}

/** "1636 US 209, Suite 106, Brodheadsville, PA 18322" — or '' if unset. */
export function officeLine(config) {
  const o = config.office;
  if (!o?.street) return '';
  return `${o.street}, ${o.city}, ${o.region} ${o.postalCode}`.trim();
}

const mapsUrl = (config) =>
  officeLine(config)
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(officeLine(config))}`
    : null;

/** Capitalisation these brands actually use — "Tiktok" would be wrong. */
const SOCIAL_LABELS = {
  instagram: 'Instagram',
  tiktok: 'TikTok',
  facebook: 'Facebook',
  linkedin: 'LinkedIn',
};

export function socialHTML(config) {
  return Object.entries(config.social)
    .filter(([, url]) => url)
    .map(([name, url]) => `
          <li><a class="social__link" href="${esc(url)}" rel="me noopener" target="_blank">${esc(SOCIAL_LABELS[name] ?? name)}</a></li>`)
    .join('');
}

/**
 * The footer's identification line. Pennsylvania requires advertising to name
 * the broker, so it is built from config.js rather than typed by hand.
 */
export function legalLine(config) {
  return [
    `${config.name} — ${config.role}, ${config.state}`,
    config.license ? `License ${config.license}` : '',
    config.brokerage ? `Brokered by ${config.brokerage}` : '',
    config.contact.officePhone ? `Office ${config.contact.officePhone}` : '',
  ].filter(Boolean).join(' · ');
}

/* ──────────────────────────── listings, reviews ──────────────────────── */

/** One listing card, as its outer HTML. */
export function cardHTML(listing) {
  // Zero beds and baths means land (a lot): say nothing rather than "0 Beds".
  const specs = [];
  if (Number(listing.beds) > 0) specs.push({ label: 'Beds', value: listing.beds });
  if (Number(listing.baths) > 0) specs.push({ label: 'Baths', value: fmtBaths(Number(listing.baths)) });
  if (listing.sqft) {
    specs.push({ label: 'Sq ft', value: Number(listing.sqft).toLocaleString('en-US') });
  }
  const where = [listing.address, listing.city].filter(Boolean).join(', ');
  return `
        <article class="listing" data-carousel-item>
          <div class="listing__frame">
            <img class="listing__photo" src="${esc(listing.photo)}"
                 alt="${esc(where)}" loading="lazy" decoding="async">
            ${listing.status ? `<span class="listing__status">${esc(listing.status)}</span>` : ''}
          </div>
          <div class="listing__body">
            <h3 class="listing__address">${esc(listing.address)}</h3>
            ${listing.city ? `<p class="listing__city">${esc(listing.city)}</p>` : ''}
            ${listing.price ? `<p class="listing__price">${esc(listing.price)}</p>` : ''}
            ${specs.length ? `<dl class="specs">${specs.map((s) => `
              <div class="specs__item">
                <dt class="specs__label">${s.label}</dt>
                <dd class="specs__value">${esc(s.value)}</dd>
              </div>`).join('')}
            </dl>` : ''}
          </div>
        </article>`;
}

/** One testimonial, as its outer HTML. */
export function testimonialHTML(item) {
  return `
        <figure class="quote" data-carousel-item>
          <blockquote class="quote__text">${esc(item.quote)}</blockquote>
          <figcaption class="quote__by">
            <span class="quote__name">${esc(item.name)}</span>
            ${item.detail ? `<span class="quote__detail">${esc(item.detail)}</span>` : ''}
          </figcaption>
        </figure>`;
}

/* ─────────────────────────────── schema ──────────────────────────────── */

/** "Luxury real estate" -> "luxury real estate"; "Spanish-…" stays capitalised. */
const sentenceCase = (x) => (/^(Spanish|English)/.test(x) ? x : x[0].toLowerCase() + x.slice(1));
/** ["a", "b", "c"] -> "a, b, and c". */
const listSentence = (xs) => (xs.length < 3 ? xs.join(' and ') : `${xs.slice(0, -1).join(', ')}, and ${xs.at(-1)}`);

/**
 * The structured data search engines read: who Ryth is (a RealEstateAgent),
 * licence, brokerage, team, office address, languages, the areas served,
 * social profiles, and every testimonial as a Review — all built from the same
 * config and data as the visible page, so the two can never disagree.
 *
 * No star rating is given: the testimonials do not carry one, and inventing
 * one would be both false and against Google's review guidelines.
 */
export function schemaJSON(config, testimonials) {
  const site = config.siteUrl;
  const o = config.office;
  const social = [...Object.values(config.social), ...(config.profiles ?? [])].filter(Boolean);
  const data = {
    '@context': 'https://schema.org',
    '@type': 'RealEstateAgent',
    '@id': `${site}#agent`,
    name: config.name,
    ...(config.legalName && { alternateName: config.legalName }),
    description:
      `Bilingual (English and Spanish) REALTOR® with ${config.brokerage}, serving ` +
      `${config.serviceAreas.counties.join(' and ')}, Pennsylvania. ` +
      `Specializes in ${listSentence(config.specialties.map(sentenceCase))}.`,
    knowsAbout: config.specialties,
    url: site,
    image: `${site}${config.portrait}`,
    telephone: `+1-${config.contact.phoneHref.replace(/^\+1/, '').replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3')}`,
    email: config.contact.email,
    knowsLanguage: ['en', 'es'],
    ...(config.open24h && {
      openingHoursSpecification: {
        '@type': 'OpeningHoursSpecification',
        dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        opens: '00:00',
        closes: '23:59',
      },
    }),
    ...(o?.street && {
      address: {
        '@type': 'PostalAddress',
        streetAddress: o.street,
        addressLocality: o.city,
        addressRegion: o.region,
        postalCode: o.postalCode,
        addressCountry: o.country,
      },
    }),
    areaServed: [
      ...config.serviceAreas.counties.map((c) => ({ '@type': 'AdministrativeArea', name: `${c}, Pennsylvania` })),
      ...config.serviceAreas.towns.map((t) => ({ '@type': 'City', name: `${t}, PA` })),
    ],
    ...(config.license && {
      hasCredential: {
        '@type': 'EducationalOccupationalCredential',
        credentialCategory: 'license',
        name: 'Pennsylvania Real Estate Salesperson License',
        identifier: config.license,
        recognizedBy: {
          '@type': 'GovernmentOrganization',
          name: 'Pennsylvania State Real Estate Commission',
        },
      },
    }),
    ...(config.brokerage && {
      parentOrganization: {
        '@type': 'RealEstateAgent',
        name: config.brokerage,
        ...(config.contact.officePhoneHref && {
          telephone: `+1-${config.contact.officePhoneHref.replace(/^\+1/, '').replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3')}`,
        }),
      },
    }),
    ...(config.team && { memberOf: { '@type': 'Organization', name: config.team } }),
    ...(social.length && { sameAs: social }),
    ...(testimonials.length && {
      review: testimonials.map((t) => ({
        '@type': 'Review',
        author: { '@type': 'Person', name: t.name },
        reviewBody: t.quote,
        itemReviewed: { '@id': `${site}#agent` },
      })),
    }),
  };
  return data;
}

/** The schema as a <script> tag. "<" is escaped so no text can close it early. */
export function schemaHTML(config, testimonials) {
  const json = JSON.stringify(schemaJSON(config, testimonials), null, 2).replace(/</g, '\\u003c');
  return `\n<script type="application/ld+json">\n${json}\n</script>`;
}

/* ──────────────────────────────── blocks ─────────────────────────────── */

/**
 * Replaces the contents of <!-- prerender:NAME --> … <!-- /prerender:NAME -->
 * in `html`. Throws if the markers are missing, so a mistake is loud rather
 * than a silently stale page.
 */
export function replaceBlock(html, name, inner) {
  const open = `<!-- prerender:${name} -->`;
  const close = `<!-- /prerender:${name} -->`;
  const start = html.indexOf(open);
  const end = html.indexOf(close);
  if (start < 0 || end < start) throw new Error(`index.html is missing the ${name} markers`);
  return html.slice(0, start + open.length) + inner + '\n        ' + html.slice(end);
}

/**
 * The footer blocks every page shares — the licence line and the office
 * address. Unlike renderAllBlocks, missing markers are skipped, since not
 * every page has every block.
 */
export function renderFooterBlocks(html, config) {
  let out = html;
  for (const [name, inner] of [['legal', esc(legalLine(config))], ['office', esc(footerOfficeLine(config))]]) {
    if (out.includes(`<!-- prerender:${name} -->`)) out = replaceBlock(out, name, inner);
  }
  return out;
}

/** Every data-driven block, rendered from config and the two data files. */
export function renderAllBlocks(html, { config, listings, testimonials }) {
  let out = html;
  out = replaceBlock(out, 'schema', schemaHTML(config, testimonials));
  out = replaceBlock(out, 'office', esc(footerOfficeLine(config)));
  out = replaceBlock(out, 'facts', factsHTML(config));
  out = replaceBlock(out, 'social', socialHTML(config));
  out = replaceBlock(out, 'legal', esc(legalLine(config)));
  out = replaceBlock(out, 'listings', listings.map(cardHTML).join(''));
  out = replaceBlock(out, 'testimonials', testimonials.map(testimonialHTML).join(''));
  return out;
}
