/** Entry point for the secondary pages: privacy, terms, the guides and the 404. */
import { renderFooter, loadAnalytics } from './footer.js';

renderFooter();
loadAnalytics();

// A county map wider than the phone scrolls sideways in its own box: start it
// on the highlighted town (or the middle of the county) instead of the edge.
for (const box of document.querySelectorAll('.cmap__scroll')) {
  if (box.scrollWidth <= box.clientWidth) continue;
  const target = box.querySelector('.cmap__mark circle, .cmap__area.is-hl');
  const boxRect = box.getBoundingClientRect();
  const center = target
    ? target.getBoundingClientRect().left + target.getBoundingClientRect().width / 2 - boxRect.left
    : box.scrollWidth / 2;
  box.scrollLeft = Math.max(0, center - box.clientWidth / 2);
}
