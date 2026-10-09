/**
 * County maps for the guide pages: every township, borough and city, drawn as
 * inline SVG from US Census boundaries (tools/data/municipalities.geojson).
 *
 * Inline, so a page needs no extra image request, and the same map serves
 * every page: the county pages show it plain, a town page highlights its
 * municipality and marks the town, and the investing page colors each
 * municipality by how hard short-term rentals are there.
 *
 * Names are written on the map where they fit; the rest get a number, listed
 * under the map. The map never shrinks below a readable width: on a phone it
 * scrolls sideways in its own box, starting at the highlighted town. The list under the map is also what AI
 * search reads: a picture of a map carries no text.
 */
import { readFileSync } from 'node:fs';
import { esc } from '../assets/js/render.js';

export const COUNTIES = {
  monroe: { fips: '089', name: 'Monroe County' },
  northampton: { fips: '095', name: 'Northampton County' },
};

const W = 800;          // map width, in map units
const PAD = 14;
const FONT = 16;        // label size, in map units; names are fitted at this size
const FONT_SM = 13.5;   // for names that only fit smaller
const LINE = 1.12;      // line height, in em
const CHAR = 0.58;      // average character width, in em (Archivo, mixed case)
const NUM_R = 12;       // radius of a number marker
const DOT_R = 6;        // the town dot
const MARK_FONT = 19;   // the town's name next to its dot

const geo = JSON.parse(readFileSync(new URL('./data/municipalities.geojson', import.meta.url), 'utf8'));

/* ───────────────────────────── geometry ───────────────────────────── */

const polysOf = (g) => (g.type === 'Polygon' ? [g.coordinates] : g.coordinates);

function inRing(x, y, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Even-odd test across every ring, so holes count as outside. */
const inside = (x, y, rings) => rings.reduce((n, r) => n + (inRing(x, y, r) ? 1 : 0), 0) % 2 === 1;

function segDist(px, py, [ax, ay], [bx, by]) {
  const dx = bx - ax;
  const dy = by - ay;
  const t = dx || dy ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) : 0;
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}

function edgeDist(x, y, rings) {
  let d = Infinity;
  for (const r of rings) for (let i = 0, j = r.length - 1; i < r.length; j = i++) d = Math.min(d, segDist(x, y, r[i], r[j]));
  return d;
}

/** Interior points, best first (farthest from the edge): label candidates. */
function interiorPoints(rings) {
  const xs = rings.flat().map((p) => p[0]);
  const ys = rings.flat().map((p) => p[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const step = Math.max(2, Math.max(x1 - x0, y1 - y0) / 40);
  const pts = [];
  for (let x = x0 + step / 2; x < x1; x += step) {
    for (let y = y0 + step / 2; y < y1; y += step) {
      if (inside(x, y, rings)) pts.push({ x, y, d: edgeDist(x, y, rings) });
    }
  }
  // Refine around the best point, so even a sliver gets a sensible center.
  pts.sort((a, b) => b.d - a.d);
  if (pts.length) {
    let best = pts[0];
    for (let s = step / 4; s > 0.3; s /= 4) {
      for (let dx = -4; dx <= 4; dx++) {
        for (let dy = -4; dy <= 4; dy++) {
          const x = best.x + dx * s;
          const y = best.y + dy * s;
          if (!inside(x, y, rings)) continue;
          const d = edgeDist(x, y, rings);
          if (d > best.d) best = { x, y, d };
        }
      }
    }
    pts.unshift(best);
  }
  return pts;
}

/** True when a w×h box centered at (x, y) sits inside the shape, clear of its edges. */
function boxFits(x, y, w, h, rings) {
  const n = 6;
  for (let i = 0; i <= n; i++) {
    for (const [px, py] of [
      [x - w / 2 + (w * i) / n, y - h / 2], [x - w / 2 + (w * i) / n, y + h / 2],
      [x - w / 2, y - h / 2 + (h * i) / n], [x + w / 2, y - h / 2 + (h * i) / n],
    ]) {
      if (!inside(px, py, rings) || edgeDist(px, py, rings) < 3) return false;
    }
  }
  return true;
}

const overlaps = (a, b, gap = 4) =>
  a.x - a.w / 2 - gap < b.x + b.w / 2 && b.x - b.w / 2 - gap < a.x + a.w / 2
  && a.y - a.h / 2 - gap < b.y + b.h / 2 && b.y - b.h / 2 - gap < a.y + a.h / 2;

/* ───────────────────────────── names ───────────────────────────── */

function describe(f, all) {
  const m = f.properties.NAME.match(/^(.*) (township|borough|city)$/);
  const [, base, kind] = m;
  const twin = all.some((o) => o !== f && o.properties.NAME.startsWith(`${base} `));
  return {
    name: f.properties.NAME,
    base,
    kind,
    full: kind === 'city' ? `City of ${base}` : `${base} ${kind === 'township' ? 'Township' : 'Borough'}`,
    // Bethlehem (city) and Bethlehem Township share a base name: say which is which.
    label: twin && kind === 'township' ? `${base} Township` : base,
  };
}

/** Ways to break a label into lines: one line, two, or one word per line. */
function layouts(text) {
  const words = text.split(' ');
  const out = [[text]];
  for (let i = 1; i < words.length; i++) out.push([words.slice(0, i).join(' '), words.slice(i).join(' ')]);
  if (words.length > 2) out.push(words);
  return out;
}

const textBox = (lines, size) => ({
  w: Math.max(...lines.map((l) => l.length)) * CHAR * size + 6,
  h: lines.length * LINE * size,
});

/* ─────────────────────────────── map ─────────────────────────────── */

/**
 * countyMap('monroe', { highlight: ['Pocono township'], marker: {label, lat, lon},
 *                       ratings: { 'Barrett township': 'green', ... }, idPrefix })
 * → { svg, items } where items lists every municipality with its number, if any.
 */
export function countyMap(key, opts = {}) {
  const county = COUNTIES[key];
  if (!county) throw new Error(`Unknown county map "${key}"`);
  const feats = geo.features.filter((f) => f.properties.COUNTY === county.fips);
  const highlight = new Set(opts.highlight || []);
  for (const h of highlight) {
    if (!feats.some((f) => f.properties.NAME === h)) throw new Error(`Map ${key}: no municipality named "${h}"`);
  }
  if (opts.ratings) {
    for (const f of feats) {
      if (!opts.ratings[f.properties.NAME]) throw new Error(`Map ${key}: no rating for "${f.properties.NAME}"`);
    }
  }

  // Projection: equirectangular, scaled for the county's latitude.
  const coords = feats.flatMap((f) => polysOf(f.geometry).flat(2));
  const lons = coords.map((c) => c[0]);
  const lats = coords.map((c) => c[1]);
  const [lon0, lon1, lat0, lat1] = [Math.min(...lons), Math.max(...lons), Math.min(...lats), Math.max(...lats)];
  const kx = Math.cos((((lat0 + lat1) / 2) * Math.PI) / 180);
  const s = (W - 2 * PAD) / ((lon1 - lon0) * kx);
  const H = Math.round((lat1 - lat0) * s + 2 * PAD);
  const proj = ([lon, lat]) => [PAD + (lon - lon0) * kx * s, PAD + (lat1 - lat) * s];

  const items = feats.map((f) => {
    const rings = polysOf(f.geometry).flatMap((poly) => poly.map((ring) => ring.map(proj)));
    return { ...describe(f, feats), rings, hl: highlight.has(f.properties.NAME) };
  }).sort((a, b) => a.full.localeCompare(b.full));

  // 1. Names that fit inside their own shape: full size if they can, a size
  //    smaller if they must (a slanted township has less room than it seems).
  const boxes = [];
  for (const it of items) {
    it.points = interiorPoints(it.rings);
    it.anchor = it.points[0];
    fit: for (const small of [false, true]) {
      for (const lines of layouts(it.label)) {
        const { w, h } = textBox(lines, small ? FONT_SM : FONT);
        const spot = it.points.find((p) => boxFits(p.x, p.y, w, h, it.rings));
        if (spot) {
          it.text = { lines, x: spot.x, y: spot.y, w, h, small };
          boxes.push(it.text);
          break fit;
        }
      }
    }
  }

  // 2. The town: a dot and its name, placed clear of the other names.
  let mark = null;
  if (opts.marker) {
    const [x, y] = proj([opts.marker.lon, opts.marker.lat]);
    const { w, h } = textBox([opts.marker.label], MARK_FONT);
    const gap = DOT_R + 8;
    const spots = [
      { x: x + gap + w / 2, y, anchor: 'start' }, { x: x - gap - w / 2, y, anchor: 'end' },
      { x, y: y - gap - h / 2, anchor: 'middle' }, { x, y: y + gap + h / 2, anchor: 'middle' },
      { x: x + gap + w / 2, y: y - h, anchor: 'start' }, { x: x - gap - w / 2, y: y - h, anchor: 'end' },
      { x: x + gap + w / 2, y: y + h, anchor: 'start' }, { x: x - gap - w / 2, y: y + h, anchor: 'end' },
    ].map((p) => ({ ...p, w, h }));
    const inBounds = (b) => b.x - b.w / 2 > 2 && b.x + b.w / 2 < W - 2 && b.y - b.h / 2 > 2 && b.y + b.h / 2 < H - 2;
    const spot = spots.find((b) => inBounds(b) && !boxes.some((o) => overlaps(b, o)))
      || spots.find(inBounds) || spots[0];
    mark = { x, y, label: { ...spot } };
    boxes.push(spot, { x, y, w: DOT_R * 2, h: DOT_R * 2 });
  }

  // 3. Numbers for the rest (not for highlighted places: the town's own
  //    label covers those), nudged off any name they would cover.
  const numbered = items.filter((it) => !it.text && !it.hl);
  numbered.forEach((it, i) => { it.num = i + 1; });
  const placed = [];
  const lit = items.filter((it) => it.hl);
  const onLit = (c) => lit.some((h) => inside(c.x, c.y, h.rings) || edgeDist(c.x, c.y, h.rings) < NUM_R);
  for (const it of numbered) {
    const { x, y } = it.anchor;
    let spot = null;
    for (const r of [0, 2.3, 3.4, 4.6, 6].map((k) => k * NUM_R)) {
      for (let a = 0; a < 12 && !spot; a++) {
        const c = { x: x + r * Math.cos((a * Math.PI) / 6), y: y + r * Math.sin((a * Math.PI) / 6), w: NUM_R * 2, h: NUM_R * 2 };
        const ok = c.x > NUM_R + 2 && c.x < W - NUM_R - 2 && c.y > NUM_R + 2 && c.y < H - NUM_R - 2
          && !boxes.some((o) => overlaps(c, o, 3))
          && !onLit(c)
          && !placed.some((o) => Math.hypot(o.x - c.x, o.y - c.y) < NUM_R * 2 + 4);
        if (ok) spot = c;
        if (r === 0) break;
      }
      if (spot) break;
    }
    spot = spot || { x, y };
    it.marker = { x: spot.x, y: spot.y, from: Math.hypot(spot.x - x, spot.y - y) > NUM_R ? { x, y } : null };
    placed.push(it.marker);
  }

  /* ── SVG ── */
  const f1 = (n) => n.toFixed(1);
  const id = opts.idPrefix || `map-${key}`;
  const areaClass = (it) => [
    'cmap__area',
    it.hl && 'is-hl',
    opts.ratings && `str-${opts.ratings[it.name]}`,
  ].filter(Boolean).join(' ');

  const areas = items.map((it) => {
    const d = it.rings.map((r) => `M${r.map(([x, y]) => `${f1(x)} ${f1(y)}`).join('L')}Z`).join('');
    return `<path class="${areaClass(it)}" d="${d}"><title>${esc(it.full)}</title></path>`;
  }).join('');

  const labels = items.filter((it) => it.text).map((it) => {
    const n = it.text.lines.length;
    const tspans = it.text.lines.map((l, i) =>
      `<tspan x="${f1(it.text.x)}" dy="${i === 0 ? `${(0.35 - ((n - 1) * LINE) / 2).toFixed(2)}em` : `${LINE}em`}">${esc(l)}</tspan>`).join('');
    return `<text class="cmap__label${it.text.small ? ' cmap__label--sm' : ''}${it.hl ? ' is-hl' : ''}" x="${f1(it.text.x)}" y="${f1(it.text.y)}" aria-hidden="true">${tspans}</text>`;
  }).join('');

  const numbers = numbered.map((it) => {
    const m = it.marker;
    const leader = m.from ? `<line class="cmap__leader" x1="${f1(m.from.x)}" y1="${f1(m.from.y)}" x2="${f1(m.x)}" y2="${f1(m.y)}"/>` : '';
    const pin = m.from ? `<circle class="cmap__pin" cx="${f1(m.from.x)}" cy="${f1(m.from.y)}" r="3"/>` : '';
    return `${leader}${pin}<g transform="translate(${f1(m.x)} ${f1(m.y)})"><g class="cmap__num"><circle r="${NUM_R}"/><text dy="0.35em">${it.num}</text></g></g>`;
  }).join('');

  const marker = mark
    ? `<g class="cmap__mark"><circle cx="${f1(mark.x)}" cy="${f1(mark.y)}" r="${DOT_R}"/>`
      + `<text class="cmap__mlabel" x="${f1(mark.label.anchor === 'start' ? mark.label.x - mark.label.w / 2 : mark.label.anchor === 'end' ? mark.label.x + mark.label.w / 2 : mark.label.x)}" `
      + `y="${f1(mark.label.y)}" dy="0.35em" text-anchor="${mark.label.anchor}">${esc(opts.marker.label)}</text></g>`
    : '';

  const svg = `<svg class="cmap__svg${opts.ratings ? ' cmap__svg--str' : ''}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${id}-title">`
    + `<title id="${id}-title">${esc(opts.title || `Map of ${county.name}, Pennsylvania, by municipality`)}</title>`
    + `<g class="cmap__areas">${areas}</g><g>${labels}</g><g>${numbers}</g>${marker}</svg>`;

  return {
    svg,
    county: county.name,
    items: items.map(({ name, base, kind, full, num, hl }) => ({ name, base, kind, full, num, hl })),
  };
}
