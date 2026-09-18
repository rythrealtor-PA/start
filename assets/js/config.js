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

  // TODO: fill these in. Any left empty is simply omitted from the page
  // rather than rendered blank, so partial answers are fine.
  brokerage: '',
  license: '',
  yearsExperience: '',

  languages: ['English', 'Español'],

  // Shown as the service-area line. Broad by default; narrow it to the
  // counties you actually work if you would rather be specific.
  serviceArea: 'Serving buyers and sellers across Pennsylvania',

  // TODO: add any you want linked. Omitted entirely when empty.
  social: {
    instagram: '',
    facebook: '',
    linkedin: '',
  },

  // TODO: drop a headshot in assets/img/ and point this at it.
  // Falls back to the placeholder portrait when empty.
  portrait: '',

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
