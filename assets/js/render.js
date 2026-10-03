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
    fact('Languages', languages.join(' · ')),
  ].join('');
}

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
  ].filter(Boolean).join(' · ');
}

/* ──────────────────────────── listings, reviews ──────────────────────── */

/** One listing card, as its outer HTML. */
export function cardHTML(listing) {
  const specs = [
    { label: 'Beds', value: listing.beds },
    { label: 'Baths', value: fmtBaths(listing.baths) },
  ];
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
            <dl class="specs">${specs.map((s) => `
              <div class="specs__item">
                <dt class="specs__label">${s.label}</dt>
                <dd class="specs__value">${esc(s.value)}</dd>
              </div>`).join('')}
            </dl>
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

/** Every data-driven block, rendered from config and the two data files. */
export function renderAllBlocks(html, { config, listings, testimonials }) {
  let out = html;
  out = replaceBlock(out, 'facts', factsHTML(config));
  out = replaceBlock(out, 'social', socialHTML(config));
  out = replaceBlock(out, 'legal', esc(legalLine(config)));
  out = replaceBlock(out, 'listings', listings.map(cardHTML).join(''));
  out = replaceBlock(out, 'testimonials', testimonials.map(testimonialHTML).join(''));
  return out;
}
