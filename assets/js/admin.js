/**
 * The listings editor at /admin.html.
 *
 * The site is static — there is no server to log in to — so publishing works by
 * committing straight to the GitHub repository the site is served from, using a
 * fine-grained access token the owner pastes in once.
 *
 * On access: the token lives in this browser's localStorage and is never part
 * of the deployed site, so a visitor who finds this page sees a setup screen and
 * can do nothing. The token is the credential; the page is just a form. Anyone
 * with the token can write to the repository, so it is scoped to Contents on a
 * single repo, and Sign out clears it from the device — worth doing on a shared
 * or borrowed computer.
 *
 * Photos are resized in the browser before upload — a 12MP phone photo becomes
 * a ~200KB web image, so the repository does not fill up with originals.
 */
import { card, testimonial } from './carousel.js';

const API = 'https://api.github.com';
const STORE_KEY = 'ryth-admin-settings';
const PHOTO_DIR = 'assets/img/listings';

/**
 * The two things this page edits. Each is a JSON array in the repo with its own
 * form, its own list and its own unsaved state; everything else — the token,
 * the GitHub calls, the Publish button — is shared.
 */
const COLLECTIONS = {
  listings: { path: 'assets/data/listings.json', render: card, hasPhoto: true },
  testimonials: { path: 'assets/data/testimonials.json', render: testimonial, hasPhoto: false },
};

/** Photos are cover-fitted into a 4:3 card, so this is ample on any screen. */
const MAX_PHOTO_EDGE = 1400;
const PHOTO_QUALITY = 0.82;

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  token: '',
  owner: '',
  repo: '',
  branch: 'main',
  /** Which collection the forms are currently editing. */
  tab: 'listings',
  /** Per collection: { items, sha, dirty, editingIndex }. */
  data: {
    listings: { items: [], sha: null, dirty: false, editingIndex: null },
    testimonials: { items: [], sha: null, dirty: false, editingIndex: null },
  },
  /** Photos chosen but not yet uploaded, keyed by their target path. */
  pending: new Map(),
  formPhoto: null,
};

/** Shorthand for the collection being edited right now. */
const current = () => state.data[state.tab];

/* ─────────────────────────────── settings ─────────────────────────────── */

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) Object.assign(state, JSON.parse(raw));
  } catch {
    // Private browsing, or storage disabled. The setup screen handles it.
  }
}

function saveSettings() {
  try {
    localStorage.setItem(
      STORE_KEY,
      JSON.stringify({
        token: state.token,
        owner: state.owner,
        repo: state.repo,
        branch: state.branch,
      }),
    );
  } catch {
    setStatus('Could not save the key on this device — you will need to paste it again next time.');
  }
}

/* ──────────────────────────────── GitHub ──────────────────────────────── */

async function gh(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${state.token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const hint =
      response.status === 401 ? 'The access key was rejected. It may be wrong or expired.'
      : response.status === 403 ? 'That key does not have permission to write to this repository.'
      : response.status === 404 ? 'Repository or file not found — check the owner/repo and branch.'
      : response.status === 409 ? 'The file changed on GitHub since this page loaded. Reload and try again.'
      : body.message || `GitHub returned ${response.status}.`;
    throw new Error(hint);
  }
  return response.status === 204 ? null : response.json();
}

/** Reads one collection from the repo, capturing its SHA so it can be updated. */
async function fetchCollection(name) {
  const slot = state.data[name];
  try {
    const file = await gh(
      `/repos/${state.owner}/${state.repo}/contents/${COLLECTIONS[name].path}?ref=${state.branch}`,
    );
    slot.sha = file.sha;
    // atob gives Latin-1; this round-trip recovers the original UTF-8 so that
    // accented names and Spanish testimonials survive.
    const text = new TextDecoder().decode(
      Uint8Array.from(atob(file.content.replace(/\s/g, '')), (c) => c.charCodeAt(0)),
    );
    slot.items = JSON.parse(text);
  } catch (error) {
    if (!/not found/i.test(error.message)) throw error;
    slot.sha = null;
    slot.items = [];
  }
}

function toBase64(bytes) {
  let binary = '';
  // Chunked: spreading a multi-megabyte array into apply() blows the stack.
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

async function putFile(path, base64, message) {
  let sha;
  try {
    const existing = await gh(
      `/repos/${state.owner}/${state.repo}/contents/${path}?ref=${state.branch}`,
    );
    sha = existing.sha;
  } catch {
    sha = undefined; // new file
  }
  return gh(`/repos/${state.owner}/${state.repo}/contents/${path}`, {
    method: 'PUT',
    body: JSON.stringify({
      message,
      content: base64,
      branch: state.branch,
      ...(sha ? { sha } : {}),
    }),
  });
}

/* ───────────────────────────────  photos  ─────────────────────────────── */

/** Scales a chosen photo down and re-encodes it as a modest JPEG. */
function processPhoto(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      const scale = Math.min(1, MAX_PHOTO_EDGE / Math.max(img.width, img.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      const ctx = canvas.getContext('2d');
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error('Could not process that image.'))),
        'image/jpeg',
        PHOTO_QUALITY,
      );
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('That file does not look like an image.'));
    };
    img.src = url;
  });
}

/** A stable, collision-free filename derived from the address. */
function photoPath(address) {
  const slug = address
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 48) || 'listing';
  return `${PHOTO_DIR}/${slug}-${Date.now().toString(36)}.jpg`;
}

/* ─────────────────────────────── rendering ────────────────────────────── */

function setStatus(message, tone = '') {
  const el = $('[data-status]');
  el.textContent = message;
  el.dataset.tone = tone;
}

function markDirty(dirty = true, name = state.tab) {
  state.data[name].dirty = dirty;
  const anyDirty = Object.values(state.data).some((d) => d.dirty);
  $('[data-publish]').disabled = !anyDirty;
  $('[data-unsaved]').hidden = !current().dirty;
}

/** Object URLs for pending photos, so previews work before anything uploads. */
const previewUrls = new Map();
function previewSrc(listing) {
  const pendingBlob = state.pending.get(listing.photo);
  if (!pendingBlob) return listing.photo;
  if (!previewUrls.has(listing.photo)) {
    previewUrls.set(listing.photo, URL.createObjectURL(pendingBlob));
  }
  return previewUrls.get(listing.photo);
}

function renderList() {
  const { items } = current();
  const { render, hasPhoto } = COLLECTIONS[state.tab];
  const list = $('[data-list]');
  list.innerHTML = '';
  $('[data-empty]').hidden = items.length > 0;

  items.forEach((listing, index) => {
    const item = document.createElement('li');
    item.className = 'admin__item';

    // The real card component, so this preview cannot drift from the site.
    const preview = render(hasPhoto ? { ...listing, photo: previewSrc(listing) } : listing);
    preview.classList.add('admin__card');

    const label = listing.address || listing.name || `item ${index + 1}`;
    const controls = document.createElement('div');
    controls.className = 'admin__controls';
    controls.innerHTML = `
      <button class="admin__ctl" type="button" data-up ${index === 0 ? 'disabled' : ''}
        aria-label="Move ${label} earlier">↑</button>
      <button class="admin__ctl" type="button" data-down
        ${index === items.length - 1 ? 'disabled' : ''}
        aria-label="Move ${label} later">↓</button>
      <button class="admin__ctl" type="button" data-edit
        aria-label="Edit ${label}">Edit</button>
      <button class="admin__ctl admin__ctl--danger" type="button" data-delete
        aria-label="Remove ${label}">Remove</button>`;

    $('[data-up]', controls).onclick = () => move(index, -1);
    $('[data-down]', controls).onclick = () => move(index, 1);
    $('[data-edit]', controls).onclick = () => startEdit(index);
    $('[data-delete]', controls).onclick = () => remove(index);

    item.append(preview, controls);
    list.append(item);
  });
}

function move(index, delta) {
  const { items } = current();
  const target = index + delta;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  markDirty();
  renderList();
}

function remove(index) {
  const { items } = current();
  const label = items[index].address || items[index].name || 'this entry';
  if (!window.confirm(`Remove ${label}? This cannot be undone once published.`)) return;
  items.splice(index, 1);
  markDirty();
  renderList();
}

/* ──────────────────────────────── the form ────────────────────────────── */

const form = () => $('[data-listing-form]');

function showError(name, message) {
  const el = $(`[data-error="${name}"]`);
  if (el) el.textContent = message;
}

function clearErrors() {
  $$('[data-error]').forEach((el) => { el.textContent = ''; });
}

const NOUN = { listings: 'listing', testimonials: 'testimonial' };

function resetForm() {
  form().reset();
  clearErrors();
  current().editingIndex = null;
  state.formPhoto = null;
  $('[data-photo-preview]').hidden = true;
  $('[data-photo-preview]').removeAttribute('src');
  $('[data-photo-prompt]').hidden = false;
  $('[data-form-heading]').textContent = `Add a ${NOUN[state.tab]}`;
  $('[data-submit]').textContent = `Add ${NOUN[state.tab]}`;
  $('[data-cancel]').hidden = true;
}

/** Shows the fields that belong to the collection being edited. */
function applyTab() {
  $$('[data-tab]').forEach((b) => {
    const on = b.dataset.tab === state.tab;
    b.classList.toggle('is-active', on);
    b.setAttribute('aria-selected', String(on));
  });
  $$('[data-for]').forEach((el) => {
    el.hidden = el.dataset.for !== state.tab;
  });
  $('[data-list-heading]').textContent =
    state.tab === 'listings' ? 'Your listings' : 'Your testimonials';
  resetForm();
  markDirty(current().dirty);
  renderList();
}

function startEdit(index) {
  const item = current().items[index];
  current().editingIndex = index;
  state.formPhoto = null; // keep the existing photo unless a new one is chosen

  const f = form();
  if (state.tab === 'listings') {
    f.address.value = item.address ?? '';
    f.city.value = item.city ?? '';
    f.price.value = item.price ?? '';
    f.beds.value = item.beds ?? '';
    f.baths.value = item.baths ?? '';
    f.sqft.value = item.sqft ?? '';
    f.status.value = item.status ?? '';

    const preview = $('[data-photo-preview]');
    preview.src = previewSrc(item);
    preview.hidden = false;
    $('[data-photo-prompt]').hidden = true;
  } else {
    f.quote.value = item.quote ?? '';
    f.person.value = item.name ?? '';
    f.detail.value = item.detail ?? '';
  }

  $('[data-form-heading]').textContent = `Edit ${NOUN[state.tab]}`;
  $('[data-submit]').textContent = 'Save changes';
  $('[data-cancel]').hidden = false;
  clearErrors();
  $('.admin__panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function onPhotoChosen(file) {
  if (!file) return;
  showError('photo', '');
  try {
    const blob = await processPhoto(file);
    state.formPhoto = blob;
    const preview = $('[data-photo-preview]');
    preview.src = URL.createObjectURL(blob);
    preview.hidden = false;
    $('[data-photo-prompt]').hidden = true;
    setStatus(`Photo ready (${Math.round(blob.size / 1024)} KB)`);
  } catch (error) {
    showError('photo', error.message);
  }
}

function buildListing(f, editing, index) {
  const address = f.address.value.trim();
  let ok = true;
  if (!address) { showError('address', 'An address is required.'); ok = false; }
  if (f.beds.value === '') { showError('beds', 'How many bedrooms?'); ok = false; }
  if (f.baths.value === '') { showError('baths', 'How many bathrooms?'); ok = false; }
  if (!state.formPhoto && !editing) { showError('photo', 'Please choose a photo.'); ok = false; }
  if (!ok) return null;

  const listing = {
    photo: editing ? current().items[index].photo : '',
    address,
    city: f.city.value.trim(),
    price: f.price.value.trim(),
    beds: Number(f.beds.value),
    baths: Number(f.baths.value),
  };
  if (f.sqft.value) listing.sqft = Number(f.sqft.value);
  if (f.status.value) listing.status = f.status.value;

  if (state.formPhoto) {
    const path = photoPath(address);
    state.pending.set(path, state.formPhoto);
    listing.photo = path;
  }
  return listing;
}

function buildTestimonial(f) {
  const quote = f.quote.value.trim();
  const name = f.person.value.trim();
  let ok = true;
  if (!quote) { showError('quote', 'Paste what the client said.'); ok = false; }
  if (!name) { showError('person', 'Whose words are these?'); ok = false; }
  if (!ok) return null;

  const item = { quote, name };
  const detail = f.detail.value.trim();
  if (detail) item.detail = detail;
  return item;
}

function onSubmit(event) {
  event.preventDefault();
  clearErrors();

  const f = form();
  const slot = current();
  const editing = slot.editingIndex !== null;
  const item = state.tab === 'listings'
    ? buildListing(f, editing, slot.editingIndex)
    : buildTestimonial(f);
  if (!item) return;

  if (editing) slot.items[slot.editingIndex] = item;
  else slot.items.push(item);

  const noun = NOUN[state.tab];
  resetForm();
  markDirty();
  renderList();
  setStatus(`${noun[0].toUpperCase()}${noun.slice(1)} ` +
            `${editing ? 'updated' : 'added'} — press Publish to put it live.`);
}

/* ─────────────────────────────── publishing ───────────────────────────── */

async function publish() {
  const button = $('[data-publish]');
  button.disabled = true;

  try {
    // Photos first, so listings.json never points at a file that is not there
    // yet — if this fails halfway, the live site is still consistent.
    let n = 0;
    for (const [path, blob] of state.pending) {
      n += 1;
      setStatus(`Uploading photo ${n} of ${state.pending.size}…`);
      const bytes = new Uint8Array(await blob.arrayBuffer());
      await putFile(path, toBase64(bytes), `Add listing photo ${path.split('/').pop()}`);
    }

    // Then each changed data file. Anything untouched is left alone, so two
    // people editing different sections never overwrite each other.
    for (const [name, slot] of Object.entries(state.data)) {
      if (!slot.dirty) continue;
      setStatus(`Saving ${name}…`);
      const json = `${JSON.stringify(slot.items, null, 2)}\n`;
      const result = await gh(
        `/repos/${state.owner}/${state.repo}/contents/${COLLECTIONS[name].path}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            message: `Update ${name} (${slot.items.length})`,
            content: toBase64(new TextEncoder().encode(json)),
            branch: state.branch,
            ...(slot.sha ? { sha: slot.sha } : {}),
          }),
        },
      );
      slot.sha = result.content.sha;
      slot.dirty = false;
    }

    state.pending.clear();
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    previewUrls.clear();
    markDirty(false);
    renderList();
    setStatus('Published. The live site updates in about a minute.', 'ok');
  } catch (error) {
    setStatus(error.message, 'error');
    button.disabled = false;
  }
}

/* ──────────────────────────────── startup ─────────────────────────────── */

async function connect() {
  setStatus('Connecting…');
  await fetchCollection('listings');
  await fetchCollection('testimonials');
  $('[data-setup]').hidden = true;
  $('[data-editor]').hidden = false;
  $('[data-editor-tabs]').hidden = false;
  $('[data-signout]').hidden = false;
  applyTab();
  setStatus(`Connected to ${state.owner}/${state.repo}`, 'ok');
}

function showSetup(message = '') {
  $('[data-setup]').hidden = false;
  $('[data-editor]').hidden = true;
  $('[data-editor-tabs]').hidden = true;
  $('[data-signout]').hidden = true;
  $('#token').value = state.token ?? '';
  $('#repo').value = state.owner && state.repo ? `${state.owner}/${state.repo}` : '';
  $('#branch').value = state.branch || 'main';
  $('[data-setup-error]').textContent = message;
}

async function init() {
  loadSettings();

  $('[data-save-token]').onclick = async () => {
    const [owner, repo] = ($('#repo').value.trim().split('/'));
    if (!owner || !repo) {
      $('[data-setup-error]').textContent = 'Repository should look like owner/repo.';
      return;
    }
    state.token = $('#token').value.trim();
    state.owner = owner;
    state.repo = repo;
    state.branch = $('#branch').value.trim() || 'main';
    if (!state.token) {
      $('[data-setup-error]').textContent = 'Paste the access key first.';
      return;
    }
    try {
      await connect();
      saveSettings();
    } catch (error) {
      showSetup(error.message);
    }
  };

  // Photo input: click, drop, and paste all land in the same place.
  const zone = $('[data-dropzone]');
  const input = $('[data-photo]');
  input.onchange = () => onPhotoChosen(input.files[0]);
  zone.onkeydown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
  };
  ['dragenter', 'dragover'].forEach((type) =>
    zone.addEventListener(type, (e) => {
      e.preventDefault();
      zone.classList.add('is-over');
    }));
  ['dragleave', 'drop'].forEach((type) =>
    zone.addEventListener(type, () => zone.classList.remove('is-over')));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    onPhotoChosen(e.dataTransfer.files[0]);
  });

  $('[data-signout]').onclick = () => {
    if (Object.values(state.data).some((d) => d.dirty) &&
        !window.confirm('There are unpublished changes. Sign out and lose them?')) return;
    try { localStorage.removeItem(STORE_KEY); } catch { /* nothing to clear */ }
    location.reload();
  };

  $$('[data-tab]').forEach((button) => {
    button.onclick = () => {
      if (state.tab === button.dataset.tab) return;
      state.tab = button.dataset.tab;
      applyTab();
    };
  });

  form().addEventListener('submit', onSubmit);
  $('[data-cancel]').onclick = resetForm;
  $('[data-publish]').onclick = publish;

  window.addEventListener('beforeunload', (e) => {
    if (Object.values(state.data).some((d) => d.dirty)) e.preventDefault();
  });

  if (state.token && state.owner && state.repo) {
    try {
      await connect();
      return;
    } catch (error) {
      showSetup(error.message);
      return;
    }
  }

  // First run: guess the repository from the GitHub Pages URL so there is one
  // less thing to type. owner.github.io/repo → owner/repo.
  const host = location.hostname.match(/^([^.]+)\.github\.io$/);
  if (host && !state.owner) {
    state.owner = host[1];
    state.repo = location.pathname.split('/').filter(Boolean)[0] || `${host[1]}.github.io`;
  }
  showSetup();
}

init().catch((error) => {
  console.error(error);
  showSetup(error.message);
});
