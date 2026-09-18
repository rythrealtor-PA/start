/**
 * Loads the listings shown in the LISTINGS carousel.
 *
 * The data lives in assets/data/listings.json — plain JSON, not JavaScript,
 * so the admin page can rewrite it safely. A stray comma in a .js file breaks
 * the whole page; a stray comma in JSON is caught before anything is published.
 *
 * To edit listings, open /admin.html on the site. To edit them by hand, edit the
 * JSON file directly — the shape of one entry is:
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
 */
export const LISTINGS_URL = 'assets/data/listings.json';

export async function loadListings() {
  // no-store so a freshly published listing shows up on the next reload
  // instead of waiting for a cached copy to expire.
  const response = await fetch(LISTINGS_URL, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Could not load listings (HTTP ${response.status})`);
  }
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error('listings.json must be an array');
  return data;
}
