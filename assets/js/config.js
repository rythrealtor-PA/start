/**
 * Everything about Ryth that appears on the page lives here.
 *
 * Values marked TODO are placeholders — the site works with them in place, but
 * they are visibly wrong on purpose so they cannot be shipped by accident.
 * Search this file for "TODO" and you have the full list.
 */
export const CONFIG = {
  name: 'Ryth Vara',
  // The name on the licence and the MLS ("Ryth Vara Verastegui"). Given to
  // search engines as an alternate name so MLS listings, Realtor.com and this
  // site are recognised as the same person.
  legalName: 'Ryth Vara Verastegui',
  role: 'Real Estate Agent',
  state: 'Pennsylvania',

  contact: {
    email: 'ryth.realtor@gmail.com',

    // `phone` is what visitors read; `phoneHref` is what their dialler gets.
    // The href carries the +1 country code so the link works from abroad.
    phone: '929.345.6838',
    phoneHref: '+19293456838',

    // The brokerage office line, shown beside the brokerage name in the
    // footer (Pennsylvania advertising rules expect the broker's number).
    officePhone: '570.801.7441',
    officePhoneHref: '+15708017441',
  },

  // Pennsylvania requires advertising to identify the broker, so `brokerage`
  // and `license` are rendered in both the bio and the footer rather than
  // being optional decoration.
  brokerage: 'Real of Pennsylvania',
  license: 'RS380174',

  // The team Ryth works under; its mark sits beside the brokerage's in the footer.
  team: 'HS Group',

  // TODO: optional — omitted from the page entirely while empty.
  yearsExperience: '',

  languages: ['English', 'Español'],

  /**
   * The public address of the site. Every absolute URL — link previews
   * (og:image), canonical links, the sitemap and the schema data — is built
   * from this. Switch it to 'https://rythvara.com/' the day that domain is
   * registered and connected, then run `node tools/prerender.mjs`.
   */
  siteUrl: 'https://rythrealtor-pa.github.io/start/',

  /**
   * Office address. Shown beside the contact details and in the footer, and
   * given to search engines as the business address. Keep it character for
   * character the same as on Google Business Profile, Zillow and Realtor.com —
   * consistent name/address/phone across listings is what local search trusts.
   */
  office: {
    street: '1636 US 209, Suite 106',
    city: 'Brodheadsville',
    region: 'PA',
    postalCode: '18322',
    country: 'US',
  },

  /** Hours, as shown on Google Business Profile. */
  hours: 'Open 24/7',
  open24h: true,

  /** What Ryth specialises in — shown to search engines as his expertise. */
  specialties: ['Luxury real estate', 'Real estate investors', 'Spanish-speaking families'],

  /**
   * Other profiles that describe Ryth (beyond the social links): search
   * engines use them to confirm this site, the MLS and these are one person.
   */
  profiles: [
    'https://www.realtor.com/realestateagents/694acaadf16e5b22934e2f8a',
  ],

  /** Counties and towns served — the schema's areaServed, in this order. */
  serviceAreas: {
    counties: ['Monroe County', 'Northampton County'],
    towns: ['Stroudsburg', 'East Stroudsburg', 'Tannersville', 'Pocono Pines',
            'Saylorsburg', 'Bethlehem', 'Nazareth', 'Easton', 'Bath'],
  },

  // Tracking parameters are stripped: the ?stkn / ?_r / ?mibextid strings these
  // links arrive with are share-session tokens, not part of the profile URL.
  // Add or remove entries freely — the list renders from whatever is non-empty.
  social: {
    instagram: 'https://www.instagram.com/ryth_william',
    tiktok: 'https://www.tiktok.com/@rythvararealtor',
    facebook: 'https://www.facebook.com/share/1DZJzdaQ4v/',
    linkedin: 'https://www.linkedin.com/in/ryth-vara-a6b87b3a2/',
  },

  portrait: 'assets/img/ryth-vara.jpg',

  /**
   * Web3Forms access key (free, no backend, no account server to run).
   * Get one at https://web3forms.com — you enter your email, they mail you a
   * key, and submissions arrive in your inbox.
   *
   * While this is empty the form still works: it falls back to opening the
   * visitor's email app with everything they typed prefilled, so no enquiry
   * is ever lost.
   *
   * This key is public by design — it lives in the page source, as every
   * Web3Forms key must, and all it can do is deliver mail to the address it
   * was registered with. It is not a password and does not need hiding. If it
   * ever attracts spam, generate a new one at web3forms.com and replace it
   * here; the honeypot field in the form handles the routine bots.
   */
  web3formsKey: '66dfc7aa-3620-4ee2-a874-faa4bdf31bf2',

  /**
   * Visitor statistics, via Cloudflare Web Analytics (free). It uses no
   * cookies and stores nothing on the visitor's device, so no cookie banner is
   * needed. To switch it on: dash.cloudflare.com → Analytics & Logs → Web
   * Analytics → Add a site → rythvara.com → copy the token from the snippet it
   * shows (the value after "token":) and paste it here. Empty = off.
   */
  analytics: {
    cloudflareToken: '',
  },
};

/** Topic options for the contact form's "Select a topic" field. */
export const TOPICS = ['Buying', 'Selling', 'Rental'];
