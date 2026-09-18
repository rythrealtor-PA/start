/**
 * Wires the page together: fills the config-driven contact details, boots the
 * scroll stage, the listings carousel, and the contact form.
 */
import { CONFIG, TOPICS } from './config.js';
import { Stage } from './stage.js';
import { initCarousel } from './carousel.js';
import { initContact } from './contact.js';

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

function renderFacts(root) {
  const { contact, brokerage, license, languages, serviceArea, yearsExperience } =
    CONFIG;

  root.innerHTML = [
    fact('Email', contact.email, `mailto:${contact.email}`),
    fact(
      'Phone',
      contact.phone,
      contact.phoneHref ? `tel:${contact.phoneHref}` : null,
    ),
    fact('Languages', languages.join(' · ')),
    fact('Licensed in', CONFIG.state),
    fact('Brokerage', brokerage),
    fact('License', license),
    fact('Experience', yearsExperience ? `${yearsExperience} years` : ''),
    fact('Area', serviceArea),
  ].join('');
}

function renderSocial(root) {
  const links = Object.entries(CONFIG.social).filter(([, url]) => url);
  if (!links.length) {
    root.remove();
    return;
  }
  root.innerHTML = links
    .map(
      ([name, url]) =>
        `<li><a class="social__link" href="${url}" rel="me noopener">${
          name[0].toUpperCase() + name.slice(1)
        }</a></li>`,
    )
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

  initCarousel(document.querySelector('[data-carousel]'));
  initContact(document.querySelector('[data-contact-form]'));

  document.querySelector('[data-year]').textContent = new Date().getFullYear();

  const stage = new Stage({
    section: document.querySelector('[data-stage]'),
    canvas: document.querySelector('[data-stage-canvas]'),
    title: document.querySelector('[data-stage-title]'),
    cue: document.querySelector('[data-stage-cue]'),
    progressBar: document.querySelector('[data-stage-progress]'),
  });
  stage.init();

  // Exposed so the scroll animation can be driven and inspected from a test
  // harness (and from the console when tuning the pacing).
  window.__stage = stage;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
