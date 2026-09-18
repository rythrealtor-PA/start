/**
 * Everything about Ryth that appears on the page lives here.
 *
 * Values marked TODO are placeholders — the site works with them in place, but
 * they are visibly wrong on purpose so they cannot be shipped by accident.
 * Search this file for "TODO" and you have the full list.
 */
export const CONFIG = {
  name: 'Ryth Vara',
  role: 'Real Estate Agent',
  state: 'Pennsylvania',

  contact: {
    email: 'ryth.realtor@gmail.com',

    // `phone` is what visitors read; `phoneHref` is what their dialler gets.
    // The href carries the +1 country code so the link works from abroad.
    phone: '929.345.6838',
    phoneHref: '+19293456838',
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

  // Shown as the service-area line. Broad by default; narrow it to the
  // counties you actually work if you would rather be specific.
  serviceArea: 'Serving buyers and sellers across Pennsylvania',

  // Tracking parameters are stripped: the ?stkn / ?_r / ?mibextid strings these
  // links arrive with are share-session tokens, not part of the profile URL.
  // Add or remove entries freely — the list renders from whatever is non-empty.
  social: {
    instagram: 'https://www.instagram.com/ryth_william',
    tiktok: 'https://www.tiktok.com/@rythvararealtor',
    facebook: 'https://www.facebook.com/share/1DZJzdaQ4v/',
    linkedin: '',
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
   */
  web3formsKey: '',
};

/** Topic options for the contact form's "Select a topic" field. */
export const TOPICS = ['Buying', 'Selling', 'Rental'];
