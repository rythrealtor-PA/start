/**
 * The footer is the same on every page, so the pieces of it that come from
 * config.js are filled in here once, for the home page and the legal pages
 * alike.
 */
import { CONFIG } from './config.js';

/**
 * The licence line and office address are written into each page's HTML by
 * tools/prerender.mjs (from the same render.js functions), so they are already
 * there for search engines. Only the year is filled in here.
 */
export function renderFooter(root = document) {
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
