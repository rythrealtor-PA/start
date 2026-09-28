/**
 * The footer is the same on every page, so the pieces of it that come from
 * config.js are filled in here once, for the home page and the legal pages
 * alike.
 */
import { CONFIG } from './config.js';

/**
 * The footer's identification line. Pennsylvania requires advertising to name
 * the broker, so the brokerage and licence number are built from config rather
 * than typed into the markup where they could drift out of sync with the bio.
 */
export function renderFooter(root = document) {
  const legal = root.querySelector('[data-footer-legal]');
  if (legal) {
    legal.textContent = [
      `${CONFIG.name} — ${CONFIG.role}, ${CONFIG.state}`,
      CONFIG.license ? `License ${CONFIG.license}` : '',
      CONFIG.brokerage ? `Brokered by ${CONFIG.brokerage}` : '',
    ].filter(Boolean).join(' · ');
  }
  const year = root.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();
}

/**
 * Cloudflare Web Analytics: counts visits without cookies, without storing
 * anything on the visitor's device and without fingerprinting, which is why
 * the site needs no cookie banner. Inert until a token is set in config.js.
 */
export function loadAnalytics() {
  const token = CONFIG.analytics?.cloudflareToken;
  if (!token) return;
  const s = document.createElement('script');
  s.defer = true;
  s.src = 'https://static.cloudflareinsights.com/beacon.min.js';
  s.dataset.cfBeacon = JSON.stringify({ token });
  document.head.append(s);
}
