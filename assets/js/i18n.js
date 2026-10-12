/**
 * The site has an English and a Spanish version (es/). Each page says which
 * it is with <html lang>, and the scripts take their visible text from here,
 * so the same scripts serve both.
 *
 * Text that is written into the HTML at build time (contact facts, listing
 * cards, the footer line) lives in render.js instead, because that file also
 * runs in Node, where there is no document to read the language from.
 */

/** 'es' on the Spanish pages, 'en' everywhere else. */
export const LANG = document.documentElement.lang.startsWith('es') ? 'es' : 'en';

/**
 * The site root as an absolute URL, worked out from where this file lives
 * (assets/js/), so assets load the same from / and from /es/.
 */
export const SITE_ROOT = new URL('../../', import.meta.url).href;

const STRINGS = {
  en: {
    topics: ['Buying', 'Selling', 'Rental'],
    chooseTopic: 'Please choose a topic.',
    enterField: (label) => `Please enter your ${label.toLowerCase()}.`,
    badEmail: 'That email address looks incomplete.',
    fixFields: 'Please fix the highlighted fields.',
    openingEmail: 'Opening your email app…',
    sending: 'Sending…',
    sent: (first) => `Thank you — your message is on its way. ${first} will be in touch shortly.`,
    failed: 'Something went wrong sending that.',
    sendByEmail: 'Send it by email instead',
    subject: (topic, name) => `${topic} enquiry from ${name}`,
    mailLabels: { name: 'Name', email: 'Email', phone: 'Phone', topic: 'Topic' },
    page: (n, total) => `Page ${n} of ${total}`,
    listingsDown: 'Listings are unavailable right now.',
    testimonialsDown: 'Testimonials are unavailable right now.',
    portraitAlt: (name) => `${name}, Real Estate Agent in Pennsylvania`,
  },
  es: {
    topics: ['Comprar', 'Vender', 'Alquilar'],
    chooseTopic: 'Elija un tema.',
    enterField: (label) => `Escriba su ${label.toLowerCase()}.`,
    badEmail: 'Ese correo electrónico parece incompleto.',
    fixFields: 'Revise los campos marcados.',
    openingEmail: 'Abriendo su aplicación de correo…',
    sending: 'Enviando…',
    sent: (first) => `Gracias, su mensaje fue enviado. ${first} le responderá pronto.`,
    failed: 'No se pudo enviar el mensaje.',
    sendByEmail: 'Envíelo por correo electrónico',
    subject: (topic, name) => `Consulta (${topic}) de ${name}, desde el sitio en español`,
    mailLabels: { name: 'Nombre', email: 'Correo', phone: 'Teléfono', topic: 'Tema' },
    page: (n, total) => `Página ${n} de ${total}`,
    listingsDown: 'Las propiedades no están disponibles en este momento.',
    testimonialsDown: 'Los testimonios no están disponibles en este momento.',
    portraitAlt: (name) => `${name}, agente de bienes raíces en Pensilvania`,
  },
};

export const T = STRINGS[LANG];
