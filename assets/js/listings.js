/**
 * Loads the data behind the LISTINGS and TESTIMONIALS carousels.
 *
 * The data lives in assets/data/listings.json — plain JSON, not JavaScript,
 * so the admin page can rewrite it safely. A stray comma in a .js file breaks
 * the whole page; a stray comma in JSON is caught before anything is published.
 *
 * To edit either, open /admin.html on the site. To edit them by hand, edit the
 * JSON files directly. A listing entry looks like:
 *
 *   {
 *     "photo":   "assets/img/listings/my-listing.jpg",
 *     "address": "412 Chestnut Ridge Road",
 *     "city":    "Doylestown, PA",
 *     "price":   "$685,000",
 *     "beds":    4,
 *     "baths":   2.5,          // halves are fine
 *     "sqft":    2840,         // optional — the slot is skipped if omitted
 *     "status":  "For sale"    // optional: For sale | Pending | Sold | For rent
 *   }
 *
 * and a testimonial:
 *
 *   {
 *     "quote":  "Ryth sold our place faster than we thought possible.",
 *     "name":   "Danielle R.",
 *     "detail": "Seller, Stroudsburg"   // optional
 *   }
 */
export const LISTINGS_URL = 'assets/data/listings.json';
export const TESTIMONIALS_URL = 'assets/data/testimonials.json';

/**
 * Both carousels read their data the same way.
 *
 * no-store matters: without it a freshly published listing waits for a cached
 * copy to expire before anyone sees it.
 */
export async function loadCollection(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Could not load ${url} (HTTP ${response.status})`);
  }
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error(`${url} must be an array`);
  return data;
}

export const loadListings = () => loadCollection(LISTINGS_URL);
export const loadTestimonials = () => loadCollection(TESTIMONIALS_URL);
