/**
 * The floating "Contact Ryth" button.
 *
 * It stays out of the way while the hero is on screen — the video is meant to
 * play with nothing over it — and again once the contact form or the footer
 * is in view, where it would only point at what the visitor is already
 * looking at. Everywhere in between, one tap reaches Ryth.
 */
export function initCta(cta) {
  if (!cta || !('IntersectionObserver' in window)) return;

  const hiders = [
    document.querySelector('[data-stage]'),
    document.querySelector('#contact'),
    document.querySelector('.footer'),
  ].filter(Boolean);
  const visible = new Set();

  cta.inert = true;
  cta.hidden = false;
  // The bottom margin means the contact form and footer only hide the button
  // once they are properly in view, not the moment their top edge peeks in.
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => (e.isIntersecting ? visible.add(e.target) : visible.delete(e.target)));
    const show = visible.size === 0;
    cta.classList.toggle('is-shown', show);
    // Out of the tab order and the accessibility tree while it is hidden.
    cta.inert = !show;
  }, { threshold: 0, rootMargin: '0px 0px -35% 0px' });

  // The stage counts as on screen for its whole scroll runway, so the button
  // arrives only once the video has handed off to the page below.
  hiders.forEach((el) => io.observe(el));
}
