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
import { card } from './carousel.js';
import { LISTINGS_URL } from './listings.js';

const API = 'https://api.github.com';
const STORE_KEY = 'ryth-admin-settings';
const DATA_PATH = 'assets/data/listings.json';
const PHOTO_DIR = 'assets/img/listings';

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
  listings: [],
  /** Blob SHA of listings.json, needed to update rather than clobber it. */
  sha: null,
  /** Photos chosen but not yet uploaded, keyed by their target path. */
  pending: new Map(),
  editingIndex: null,
  dirty: false,
};

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

/** Reads listings.json from the repo, capturing its SHA so it can be updated. */
async function fetchListings() {
  try {
    const file = await gh(
      `/repos/${state.owner}/${state.repo}/contents/${DATA_PATH}?ref=${state.branch}`,
    );
    state.sha = file.sha;
    // atob gives Latin-1; this round-trip recovers the original UTF-8 so that
    // accented place names survive.
    const text = new TextDecoder().decode(
      Uint8Array.from(atob(file.content.replace(/\s/g, '')), (c) => c.charCodeAt(0)),
    );
    state.listings = JSON.parse(text);
  } catch (error) {
    if (!/not found/i.test(error.message)) throw error;
    state.sha = null;
    state.listings = [];
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

function markDirty(dirty = true) {
  state.dirty = dirty;
  $('[data-publish]').disabled = !dirty;
  $('[data-unsaved]').hidden = !dirty;
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
  const list = $('[data-list]');
  list.innerHTML = '';
  $('[data-empty]').hidden = state.listings.length > 0;

  state.listings.forEach((listing, index) => {
    const item = document.createElement('li');
    item.className = 'admin__item';

    // The real card component, so this preview cannot drift from the site.
    const preview = card({ ...listing, photo: previewSrc(listing) });
    preview.classList.add('admin__card');

    const controls = document.createElement('div');
    controls.className = 'admin__controls';
    controls.innerHTML = `
      <button class="admin__ctl" type="button" data-up ${index === 0 ? 'disabled' : ''}
        aria-label="Move ${listing.address} earlier">↑</button>
      <button class="admin__ctl" type="button" data-down
        ${index === state.listings.length - 1 ? 'disabled' : ''}
        aria-label="Move ${listing.address} later">↓</button>
      <button class="admin__ctl" type="button" data-edit
        aria-label="Edit ${listing.address}">Edit</button>
      <button class="admin__ctl admin__ctl--danger" type="button" data-delete
        aria-label="Remove ${listing.address}">Remove</button>`;

    $('[data-up]', controls).onclick = () => move(index, -1);
    $('[data-down]', controls).onclick = () => move(index, 1);
    $('[data-edit]', controls).onclick = () => startEdit(index);
    $('[data-delete]', controls).onclick = () => remove(index);

    item.append(preview, controls);
    list.append(item);
  });
}

function move(index, delta) {
  const target = index + delta;
  if (target < 0 || target >= state.listings.length) return;
  [state.listings[index], state.listings[target]] =
    [state.listings[target], state.listings[index]];
  markDirty();
  renderList();
}

function remove(index) {
  const listing = state.listings[index];
  if (!window.confirm(`Remove ${listing.address}? This cannot be undone once published.`)) return;
  state.listings.splice(index, 1);
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

function resetForm() {
  form().reset();
  clearErrors();
  state.editingIndex = null;
  state.formPhoto = null;
  $('[data-photo-preview]').hidden = true;
  $('[data-photo-preview]').removeAttribute('src');
  $('[data-photo-prompt]').hidden = false;
  $('[data-form-heading]').textContent = 'Add a listing';
  $('[data-submit]').textContent = 'Add listing';
  $('[data-cancel]').hidden = true;
}

function startEdit(index) {
  const listing = state.listings[index];
  state.editingIndex = index;
  state.formPhoto = null; // keep the existing photo unless a new one is chosen

  const f = form();
  f.address.value = listing.address ?? '';
  f.city.value = listing.city ?? '';
  f.price.value = listing.price ?? '';
  f.beds.value = listing.beds ?? '';
  f.baths.value = listing.baths ?? '';
  f.sqft.value = listing.sqft ?? '';
  f.status.value = listing.status ?? '';

  const preview = $('[data-photo-preview]');
  preview.src = previewSrc(listing);
  preview.hidden = false;
  $('[data-photo-prompt]').hidden = true;

  $('[data-form-heading]').textContent = 'Edit listing';
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

function onSubmit(event) {
  event.preventDefault();
  clearErrors();

  const f = form();
  const address = f.address.value.trim();
  const beds = f.beds.value;
  const baths = f.baths.value;
  const editing = state.editingIndex !== null;

  let ok = true;
  if (!address) { showError('address', 'An address is required.'); ok = false; }
  if (beds === '') { showError('beds', 'How many bedrooms?'); ok = false; }
  if (baths === '') { showError('baths', 'How many bathrooms?'); ok = false; }
  if (!state.formPhoto && !editing) { showError('photo', 'Please choose a photo.'); ok = false; }
  if (!ok) return;

  const listing = {
    photo: editing ? state.listings[state.editingIndex].photo : '',
    address,
    city: f.city.value.trim(),
    price: f.price.value.trim(),
    beds: Number(beds),
    baths: Number(baths),
  };
  if (f.sqft.value) listing.sqft = Number(f.sqft.value);
  if (f.status.value) listing.status = f.status.value;

  if (state.formPhoto) {
    const path = photoPath(address);
    state.pending.set(path, state.formPhoto);
    listing.photo = path;
  }

  if (editing) state.listings[state.editingIndex] = listing;
  else state.listings.push(listing);

  resetForm();
  markDirty();
  renderList();
  setStatus(editing ? 'Listing updated — press Publish to put it live.'
                    : 'Listing added — press Publish to put it live.');
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

    setStatus('Saving listings…');
    const json = `${JSON.stringify(state.listings, null, 2)}\n`;
    const encoded = toBase64(new TextEncoder().encode(json));
    const result = await gh(`/repos/${state.owner}/${state.repo}/contents/${DATA_PATH}`, {
      method: 'PUT',
      body: JSON.stringify({
        message: `Update listings (${state.listings.length})`,
        content: encoded,
        branch: state.branch,
        ...(state.sha ? { sha: state.sha } : {}),
      }),
    });
    state.sha = result.content.sha;

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
  await fetchListings();
  $('[data-setup]').hidden = true;
  $('[data-editor]').hidden = false;
  $('[data-signout]').hidden = false;
  markDirty(false);
  renderList();
  setStatus(`Connected to ${state.owner}/${state.repo}`, 'ok');
}

function showSetup(message = '') {
  $('[data-setup]').hidden = false;
  $('[data-editor]').hidden = true;
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
    if (state.dirty &&
        !window.confirm('There are unpublished changes. Sign out and lose them?')) return;
    try { localStorage.removeItem(STORE_KEY); } catch { /* nothing to clear */ }
    location.reload();
  };

  form().addEventListener('submit', onSubmit);
  $('[data-cancel]').onclick = resetForm;
  $('[data-publish]').onclick = publish;

  window.addEventListener('beforeunload', (e) => {
    if (state.dirty) e.preventDefault();
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

// The live site reads the same file this page writes.
export { LISTINGS_URL };
