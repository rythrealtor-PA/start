/**
 * The listings shown in the LISTINGS carousel.
 *
 * To add one: copy a block, change the values, drop its photo in
 * assets/img/listings/ and point `photo` at it. Order here is display order.
 *
 * Fields:
 *   photo   one image per listing (the carousel shows a single photo per card)
 *   address street line — the card's heading
 *   city    city / township, shown under the address
 *   price   free text, so "Coming soon" or "Contact for price" also work
 *   beds    number
 *   baths   number — halves are fine (2.5)
 *   sqft    optional; the slot is skipped when omitted
 *   status  optional badge: 'For sale' | 'Pending' | 'Sold' | 'For rent'
 *
 * The six below are PLACEHOLDERS with generated artwork, here so the layout is
 * real and reviewable. Replace them with your own before going live.
 */
export const LISTINGS = [
  {
    photo: 'assets/img/listings/placeholder-1.svg',
    address: '412 Chestnut Ridge Road',
    city: 'Doylestown, PA',
    price: '$685,000',
    beds: 4,
    baths: 2.5,
    sqft: 2840,
    status: 'For sale',
  },
  {
    photo: 'assets/img/listings/placeholder-2.svg',
    address: '78 Bluestone Lane',
    city: 'Lower Merion, PA',
    price: '$1,240,000',
    beds: 5,
    baths: 4,
    sqft: 4100,
    status: 'For sale',
  },
  {
    photo: 'assets/img/listings/placeholder-3.svg',
    address: '1905 Fairmount Avenue',
    city: 'Philadelphia, PA',
    price: '$525,000',
    beds: 3,
    baths: 2,
    sqft: 1960,
    status: 'Pending',
  },
  {
    photo: 'assets/img/listings/placeholder-4.svg',
    address: '233 Millrace Court',
    city: 'Lancaster, PA',
    price: '$398,000',
    beds: 3,
    baths: 2,
    sqft: 1740,
    status: 'For sale',
  },
  {
    photo: 'assets/img/listings/placeholder-5.svg',
    address: '60 Slate Hollow Drive',
    city: 'Bethlehem, PA',
    price: '$742,500',
    beds: 4,
    baths: 3.5,
    sqft: 3120,
    status: 'For sale',
  },
  {
    photo: 'assets/img/listings/placeholder-6.svg',
    address: '14 Orchard Row',
    city: 'West Chester, PA',
    price: '$2,850 / mo',
    beds: 2,
    baths: 1,
    sqft: 1180,
    status: 'For rent',
  },
];
