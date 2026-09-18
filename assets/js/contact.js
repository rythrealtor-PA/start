/**
 * The GET IN TOUCH form.
 *
 * Posts to Web3Forms when a key is configured. With no key it falls back to
 * opening the visitor's email app with everything prefilled — so the form is
 * never a dead end, even on a fresh clone.
 */
import { CONFIG } from './config.js';

const ENDPOINT = 'https://api.web3forms.com/submit';

/** Native validity messages are terse; these say what to actually do. */
function errorFor(field) {
  if (field.validity.valueMissing) {
    return field.type === 'select-one'
      ? 'Please choose a topic.'
      : `Please enter your ${field.dataset.label.toLowerCase()}.`;
  }
  if (field.validity.typeMismatch && field.type === 'email') {
    return 'That email address looks incomplete.';
  }
  return field.validationMessage;
}

function showError(field, message) {
  const slot = document.getElementById(`${field.id}-error`);
  if (slot) slot.textContent = message;
  field.setAttribute('aria-invalid', message ? 'true' : 'false');
}

/** Builds the mailto: used when no Web3Forms key is set. */
function mailtoFallback(data) {
  const body = [
    `Name:  ${data.name}`,
    `Email: ${data.email}`,
    `Phone: ${data.phone || '—'}`,
    `Topic: ${data.topic}`,
    '',
    data.message,
  ].join('\n');
  return `mailto:${CONFIG.contact.email}?subject=${encodeURIComponent(
    `${data.topic} enquiry from ${data.name}`,
  )}&body=${encodeURIComponent(body)}`;
}

export function initContact(form) {
  const result = form.querySelector('[data-result]');
  const submit = form.querySelector('[type="submit"]');
  const fields = [...form.querySelectorAll('[data-label]')];

  // Validate on blur rather than on input: flagging an email as malformed
  // while it is still being typed is just nagging.
  fields.forEach((field) => {
    field.addEventListener('blur', () => {
      showError(field, field.checkValidity() ? '' : errorFor(field));
    });
    field.addEventListener('input', () => {
      if (field.getAttribute('aria-invalid') === 'true' && field.checkValidity()) {
        showError(field, '');
      }
    });
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    let firstInvalid = null;
    fields.forEach((field) => {
      const ok = field.checkValidity();
      showError(field, ok ? '' : errorFor(field));
      if (!ok && !firstInvalid) firstInvalid = field;
    });
    if (firstInvalid) {
      firstInvalid.focus();
      result.textContent = 'Please fix the highlighted fields.';
      result.dataset.state = 'error';
      return;
    }

    const data = Object.fromEntries(new FormData(form).entries());

    if (!CONFIG.web3formsKey) {
      result.textContent = 'Opening your email app…';
      result.dataset.state = 'pending';
      window.location.href = mailtoFallback(data);
      return;
    }

    submit.disabled = true;
    result.textContent = 'Sending…';
    result.dataset.state = 'pending';

    try {
      const response = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          access_key: CONFIG.web3formsKey,
          subject: `${data.topic} enquiry from ${data.name}`,
          from_name: data.name,
          ...data,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      form.reset();
      result.textContent = `Thank you — your message is on its way. ${CONFIG.name.split(' ')[0]} will be in touch shortly.`;
      result.dataset.state = 'success';
    } catch {
      // Never strand the enquiry: hand them the prefilled email instead.
      result.innerHTML =
        `Something went wrong sending that. ` +
        `<a href="${mailtoFallback(data)}">Send it by email instead</a>.`;
      result.dataset.state = 'error';
    } finally {
      submit.disabled = false;
    }
  });
}
