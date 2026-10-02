/**
 * Wires the page together: fills the config-driven contact details, boots the
 * scroll stage, the listings carousel, and the contact form.
 */
import { CONFIG, TOPICS } from './config.js';
import { Stage } from './stage.js';
import { VideoSequence } from './video-sequence.js';
import { initDebug } from './debug.js';
import { initCarousel, card, testimonial } from './carousel.js';
import { loadListings, loadTestimonials } from './listings.js';
import { initContact } from './contact.js';
import { renderFooter, loadAnalytics } from './footer.js';
import { initCta } from './cta.js';

/** Renders a definition-list row, or nothing at all when the value is empty. */
function fact(label, value, href) {
  if (!value) return '';
  const body = href
    ? `<a class="facts__link" href="${href}">${value}</a>`
    : value;
  return `
    <div class="facts__row">
      <dt class="facts__label">${label}</dt>
      <dd class="facts__value">${body}</dd>
    </div>`;
}

/**
 * Contact details beside the portrait. Deliberately just these three — the
 * bio copy already names the brokerage and the service area, and the brokerage
 * and licence number appear in the footer, which is what Pennsylvania's
 * advertising rule requires.
 */
function renderFacts(root) {
  const { contact, languages } = CONFIG;

  root.innerHTML = [
    fact('Email', contact.email, `mailto:${contact.email}`),
    fact(
      'Phone',
      contact.phone,
      contact.phoneHref ? `tel:${contact.phoneHref}` : null,
    ),
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

function renderSocial(root) {
  const links = Object.entries(CONFIG.social).filter(([, url]) => url);
  if (!links.length) {
    root.remove();
    return;
  }
  root.innerHTML = links
    .map(([name, url]) => {
      const label = SOCIAL_LABELS[name] ?? name;
      return `<li><a class="social__link" href="${url}"
        rel="me noopener" target="_blank">${label}</a></li>`;
    })
    .join('');
}

function renderTopics(select) {
  select.append(
    ...TOPICS.map((topic) => new Option(topic, topic)),
  );
}

function renderPortrait(img) {
  if (CONFIG.portrait) img.src = CONFIG.portrait;
  img.alt = `${CONFIG.name}, ${CONFIG.role} in ${CONFIG.state}`;
}

function renderBrandMarks() {
  const team = document.querySelector('[data-team-mark]');
  const broker = document.querySelector('[data-broker-mark]');
  if (CONFIG.team) team.alt = CONFIG.team; else team.closest('.footer__brand').remove();
  if (CONFIG.brokerage) broker.alt = CONFIG.brokerage;
  else broker.closest('.footer__brand').remove();
}

function renderContactLinks() {
  document.querySelectorAll('[data-email-link]').forEach((el) => {
    el.href = `mailto:${CONFIG.contact.email}`;
    el.textContent = CONFIG.contact.email;
  });
  document.querySelectorAll('[data-phone-link]').forEach((el) => {
    el.textContent = CONFIG.contact.phone;
    if (CONFIG.contact.phoneHref) {
      el.href = `tel:${CONFIG.contact.phoneHref}`;
    } else {
      // No number yet — keep the text visible but do not offer a dead link.
      el.removeAttribute('href');
    }
  });
  // Icon-only links (the floating call button) keep their contents.
  document.querySelectorAll('[data-phone-href]').forEach((el) => {
    if (CONFIG.contact.phoneHref) el.href = `tel:${CONFIG.contact.phoneHref}`;
    else el.remove();
  });
}

/** Fills one carousel from its data file, or says so in place if it cannot. */
function hydrate(name, load, renderItem, failureMessage) {
  const root = document.querySelector(`[data-carousel="${name}"]`);
  load()
    .then((items) => {
      // Nothing to show (e.g. between listings): drop the whole section rather
      // than leave a heading over an empty row.
      if (!items.length) {
        root.hidden = true;
        return;
      }
      initCarousel(root, items, renderItem);
    })
    .catch((error) => {
      console.error(`[${name}]`, error);
      root.querySelector('[data-carousel-status]').textContent = failureMessage;
    });
}

function boot() {
  document.querySelectorAll('[data-name]').forEach((el) => {
    el.textContent = CONFIG.name;
  });
  document.documentElement.classList.remove('no-js');

  renderFacts(document.querySelector('[data-facts]'));
  renderSocial(document.querySelector('[data-social]'));
  renderTopics(document.querySelector('#topic'));
  renderPortrait(document.querySelector('[data-portrait]'));
  renderContactLinks();
  renderBrandMarks();
  renderFooter();

  // Both carousels read their data over the network, so they fill in a moment
  // after the rest of the page. Everything else is already rendered. They load
  // independently, so one failing does not take the other down.
  hydrate('listings', loadListings, card, 'Listings are unavailable right now.');
  hydrate('testimonials', loadTestimonials, testimonial,
          'Testimonials are unavailable right now.');
  initContact(document.querySelector('[data-contact-form]'));

  initCta(document.querySelector('[data-cta]'));
  loadAnalytics();

  const stage = new Stage({
    section: document.querySelector('[data-stage]'),
    canvas: document.querySelector('[data-stage-canvas]'),
    title: document.querySelector('[data-stage-title]'),
    cue: document.querySelector('[data-stage-cue]'),
    progressBar: document.querySelector('[data-stage-progress]'),
    // Laptops and desktops scrub a real video; phones keep the stills. Only on
    // pages that opt in (preview.html) until it has been tried on real
    // hardware.
    useVideo:
      document.documentElement.dataset.hero === 'video' &&
      window.matchMedia('(min-width: 768px)').matches &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches &&
      VideoSequence.pickSource() !== null,
  });
  stage.init();

  // Exposed so the scroll animation can be driven and inspected from a test
  // harness (and from the console when tuning the pacing).
  window.__stage = stage;
  initDebug(stage);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
