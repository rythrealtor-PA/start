/**
 * The paged carousels — LISTINGS and TESTIMONIALS — showing two cards at a
 * time on desktop, one on mobile, paged by the arrow buttons.
 *
 * Paging is native scrolling with CSS scroll-snap underneath, so touch swipe,
 * trackpad, and keyboard all work without being reimplemented, and the track
 * stays a usable scroller if this script never runs.
 */
import { cardHTML, testimonialHTML } from './render.js';

/** Builds an element from one of render.js's HTML strings. */
const fromHTML = (html) => {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
};

/**
 * One listing card. Exported so the admin page previews a listing with exactly
 * the markup the real site uses — the same render.js function that writes the
 * card into index.html — rather than an approximation that can drift.
 */
export const card = (listing) => fromHTML(cardHTML(listing));

/** One testimonial. Same carousel machinery as the listing cards. */
export const testimonial = (item) => fromHTML(testimonialHTML(item));

/**
 * Wires up a carousel. The cards are normally already in the HTML (written by
 * tools/prerender.mjs or by Publish); `items`, when given, are appended —
 * the fallback for a page whose HTML has not been regenerated yet.
 */
export function initCarousel(root, items, renderItem = card) {
  const track = root.querySelector('[data-track]');
  const prev = root.querySelector('[data-prev]');
  const next = root.querySelector('[data-next]');
  const status = root.querySelector('[data-carousel-status]');

  (items ?? []).forEach((item) => track.append(renderItem(item)));
  const count = track.querySelectorAll('[data-carousel-item]').length;

  /** Scroll by exactly one visible page, whatever the breakpoint is showing. */
  const page = (dir) => {
    track.scrollBy({ left: dir * track.clientWidth, behavior: 'smooth' });
  };

  const sync = () => {
    const max = track.scrollWidth - track.clientWidth;
    // A pixel of slack: fractional scroll offsets otherwise leave the button
    // enabled at the very end.
    prev.disabled = track.scrollLeft <= 1;
    next.disabled = track.scrollLeft >= max - 1;

    const perPage = Math.max(1, Math.round(track.clientWidth / cardWidth()));
    const current = Math.round(track.scrollLeft / track.clientWidth) + 1;
    const total = Math.max(1, Math.ceil(count / perPage));
    status.textContent = `Page ${Math.min(current, total)} of ${total}`;
  };

  const cardWidth = () => {
    const first = track.querySelector('[data-carousel-item]');
    return first ? first.getBoundingClientRect().width : track.clientWidth;
  };

  prev.addEventListener('click', () => page(-1));
  next.addEventListener('click', () => page(1));
  track.addEventListener('scroll', sync, { passive: true });
  window.addEventListener('resize', sync, { passive: true });
  sync();
}
