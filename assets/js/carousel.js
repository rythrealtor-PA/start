/**
 * The LISTINGS carousel: two cards visible at a time on desktop, one on mobile,
 * paged by the arrow buttons.
 *
 * Paging is native scrolling with CSS scroll-snap underneath, so touch swipe,
 * trackpad, and keyboard all work without being reimplemented, and the track
 * stays a usable scroller if this script never runs.
 */
const fmtBaths = (n) => (Number.isInteger(n) ? n : n.toFixed(1));

/**
 * One listing card. Exported so the admin page previews a listing with exactly
 * the markup the real site uses, rather than an approximation that can drift.
 */
export function card(listing) {
  const el = document.createElement('article');
  el.className = 'listing';

  const specs = [
    { label: 'Beds', value: listing.beds },
    { label: 'Baths', value: fmtBaths(listing.baths) },
  ];
  if (listing.sqft) {
    specs.push({ label: 'Sq ft', value: listing.sqft.toLocaleString('en-US') });
  }

  el.innerHTML = `
    <div class="listing__frame">
      <img class="listing__photo" src="${listing.photo}"
           alt="${listing.address}, ${listing.city}" loading="lazy" decoding="async">
      ${listing.status ? `<span class="listing__status">${listing.status}</span>` : ''}
    </div>
    <div class="listing__body">
      <h3 class="listing__address">${listing.address}</h3>
      <p class="listing__city">${listing.city}</p>
      <p class="listing__price">${listing.price}</p>
      <dl class="specs">
        ${specs
          .map(
            (s) => `
          <div class="specs__item">
            <dt class="specs__label">${s.label}</dt>
            <dd class="specs__value">${s.value}</dd>
          </div>`,
          )
          .join('')}
      </dl>
    </div>`;
  return el;
}

export function initCarousel(root, listings) {
  const track = root.querySelector('[data-track]');
  const prev = root.querySelector('[data-prev]');
  const next = root.querySelector('[data-next]');
  const status = root.querySelector('[data-carousel-status]');

  listings.forEach((l) => track.append(card(l)));

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
    const total = Math.max(1, Math.ceil(listings.length / perPage));
    status.textContent = `Page ${Math.min(current, total)} of ${total}`;
  };

  const cardWidth = () => {
    const first = track.querySelector('.listing');
    return first ? first.getBoundingClientRect().width : track.clientWidth;
  };

  prev.addEventListener('click', () => page(-1));
  next.addEventListener('click', () => page(1));
  track.addEventListener('scroll', sync, { passive: true });
  window.addEventListener('resize', sync, { passive: true });
  sync();
}
