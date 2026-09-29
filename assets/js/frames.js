/**
 * Loads the hero still sequence and hands the stage a frame for any index.
 *
 * The clip ships as numbered stills rather than as a <video> because scrubbing
 * video.currentTime is unreliable — seeks snap to keyframes, reverse playback
 * stutters, and iOS Safari throttles it. With stills, playing backwards is just
 * a decreasing index.
 *
 * All 145 frames are kept compressed (as <img>, ~16MB). Only a small window
 * around the playhead is kept decoded, as ImageBitmaps — decoding all of them
 * would take ~960MB of memory. See warm().
 */

/** Must match the number of files tools/extract-frames.sh produced. */
export const FRAME_COUNT = 145;

/** How many frames to have in flight at once. */
const CONCURRENCY = 6;

/**
 * A 1x1 AVIF. If the browser decodes it, the AVIF sets are safe to use;
 * otherwise we fall back to WebP. Roughly 5% of browsers still need this
 * (Safari below 16.4, older Android).
 */
const AVIF_PROBE =
  'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIABoAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEDQgMgkQAAAAB8dSLfI9pAw=';

let avifSupport = null;

/** Resolves true when the browser can decode AVIF. Probed once, then cached. */
function supportsAvif() {
  if (avifSupport) return avifSupport;
  avifSupport = new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img.width === 1);
    img.onerror = () => resolve(false);
    img.src = AVIF_PROBE;
  });
  return avifSupport;
}

/**
 * Picks a frame set. Narrow viewports get the 900px set; anything without AVIF
 * gets the WebP fallback, which is also 900px — a softer image on browsers that
 * are old enough to be on slower hardware anyway.
 */
async function chooseSet() {
  const wide = window.matchMedia('(min-width: 768px)').matches;
  if (!(await supportsAvif())) return { dir: 'fallback', ext: 'webp' };
  return wide ? { dir: 'desktop', ext: 'avif' } : { dir: 'mobile', ext: 'avif' };
}

const pad = (n) => String(n).padStart(3, '0');

/**
 * Frames kept decoded around the current position. A downloaded AVIF is still
 * compressed; drawing it for the first time makes the browser decode it on the
 * spot, on the main thread, mid-scroll — 10-30ms that shows up as a hitch.
 * Decoding the next few frames ahead of time means every frame is ready before
 * it is needed. It has to be decoded from the downloaded file (a Blob), not
 * from the <img>: measured in Chromium, createImageBitmap(img) blocks the main
 * thread ~75ms per frame, while createImageBitmap(blob) runs on a background
 * thread and costs the page nothing.
 *
 * More room ahead than behind, because that is where the scroll is going.
 * Memory is the ceiling: one decoded desktop frame is ~6.6MB, so this window
 * holds ~100MB on desktop and ~45MB on a phone, and frames leaving it are
 * released straight away.
 */
const AHEAD = 10;
const BEHIND = 4;
/**
 * When the exact frame is not decoded yet, a decoded neighbour up to this many
 * frames away is shown instead of stalling to decode the exact one — at scroll
 * speed a frame or two of difference is invisible, a hitch is not.
 */
const STAND_IN_REACH = 3;
/** Decodes in flight at once, so the nearest frames are never queued behind far ones. */
const MAX_DECODING = 4;
const CAN_PREDECODE = typeof createImageBitmap === 'function';

export class FrameSequence {
  constructor() {
    this.images = new Array(FRAME_COUNT);
    this.loadedCount = 0;
    this.width = 0;
    this.height = 0;
    /** Called with (0..1) as loading progresses. */
    this.onProgress = null;
    /** Called once the first frame is ready to draw. */
    this.onFirstFrame = null;

    /** The downloaded files, which is what decoding works from. */
    this.blobs = new Array(FRAME_COUNT);
    /** Called when a frame arrives or finishes decoding. */
    this.onReady = null;
    /** index -> decoded ImageBitmap, for the window around the playhead. */
    this.decoded = new Map();
    this.decoding = new Set();
    this.windowLo = 0;
    this.windowHi = AHEAD;
  }

  /** True once every frame has landed. */
  get complete() {
    return this.loadedCount === FRAME_COUNT;
  }

  /**
   * Frame 1 comes in through an <img>, so it can use the preload in
   * index.html. The rest are fetched as files, so they can be decoded off the
   * main thread later; each also gets an <img> as a fallback drawable.
   */
  load(index) {
    const url = `${this.basePath}/f_${pad(index + 1)}.${this.ext}`;
    if (index === 0 || !CAN_PREDECODE) return this.loadImage(index, url);
    return fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        this.blobs[index] = blob;
        return this.loadImage(index, URL.createObjectURL(blob));
      })
      .catch(() => this.failed());
  }

  loadImage(index, src) {
    return new Promise((resolve) => {
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        this.images[index] = img;
        this.loadedCount += 1;
        // Announce readiness on the first frame that genuinely decoded, not
        // merely on the first request that settled. If frame 1 were to fail,
        // keying off it would hand the stage a zero-sized buffer and the
        // canvas would render nothing, silently.
        if (!this.width) {
          this.width = img.naturalWidth;
          this.height = img.naturalHeight;
          this.onFirstFrame?.();
        }
        this.onProgress?.(this.loadedCount / FRAME_COUNT);
        this.onReady?.();
        resolve(img);
      };
      // A missing frame must not stall the sequence — nearest() will simply
      // reach past the gap.
      img.onerror = () => resolve(this.failed());
      img.src = src;
    });
  }

  failed() {
    this.loadedCount += 1;
    this.onProgress?.(this.loadedCount / FRAME_COUNT);
    return null;
  }

  async start() {
    const { dir, ext } = await chooseSet();
    this.basePath = `assets/frames/${dir}`;
    this.ext = ext;

    // Frame 1 first and alone: it is the static hero behind the title, so it
    // decides how soon the page stops looking empty.
    await this.load(0);

    // Then the rest in order, a few at a time. Sequential order matters —
    // it matches the order a visitor scrolls through them.
    let next = 1;
    const worker = async () => {
      while (next < FRAME_COUNT) {
        const i = next;
        next += 1;
        await this.load(i);
      }
    };
    await Promise.all(
      Array.from({ length: CONCURRENCY }, worker),
    );

    if (!this.width) {
      console.warn(
        `[frames] no frame decoded from ${this.basePath} — the stage will ` +
        'stay on its gradient. Check the sequence exists and the format is ' +
        'one this browser can decode.',
      );
    }
  }

  /**
   * What to draw for frame `index`, as { image, exact }. In order of
   * preference: its decoded bitmap; a decoded neighbour within
   * STAND_IN_REACH (no stall, and invisible at scroll speed); the frame's own
   * <img>, which the browser decodes on the spot; or, while the sequence is
   * still downloading, the nearest frame that has arrived.
   */
  pick(index) {
    const own = this.decoded.get(index);
    if (own) return { image: own, exact: true };
    for (let d = 1; d <= STAND_IN_REACH; d += 1) {
      const near = this.decoded.get(index - d) ?? this.decoded.get(index + d);
      if (near) return { image: near, exact: false };
    }
    return { image: this.nearest(index), exact: !!this.images[index] };
  }

  /**
   * Keeps the frames around `center` decoded, weighted toward `direction`
   * (+1 scrolling down, -1 up), and releases everything outside that window.
   * Cheap enough to call every animation frame.
   */
  warm(center, direction = 1) {
    if (!CAN_PREDECODE) return;
    const c = Math.round(center);
    const lo = Math.max(0, c - (direction >= 0 ? BEHIND : AHEAD));
    const hi = Math.min(FRAME_COUNT - 1, c + (direction >= 0 ? AHEAD : BEHIND));
    this.windowLo = lo;
    this.windowHi = hi;

    for (const [i, bitmap] of this.decoded) {
      // Frame 1 stays decoded for good: it is the resting hero image, and it
      // is the one frame that only exists as an <img> (see load()).
      if (i !== 0 && (i < lo || i > hi)) {
        bitmap.close();
        this.decoded.delete(i);
      }
    }

    // Nearest first, alternating ahead and behind.
    const sign = direction >= 0 ? 1 : -1;
    for (let d = 0; d <= AHEAD && this.decoding.size < MAX_DECODING; d += 1) {
      for (const i of d === 0 ? [c] : [c + d * sign, c - d * sign]) {
        if (i < lo || i > hi) continue;
        if (this.decoded.has(i) || this.decoding.has(i) || !this.images[i]) continue;
        if (this.decoding.size >= MAX_DECODING) break;
        this.decode(i);
      }
    }
  }

  decode(i) {
    this.decoding.add(i);
    createImageBitmap(this.blobs[i] ?? this.images[i])
      .then((bitmap) => {
        // The playhead may have moved on while this was decoding.
        if (i === 0 || (i >= this.windowLo && i <= this.windowHi)) {
          this.decoded.set(i, bitmap);
          this.onReady?.();
        } else {
          bitmap.close();
        }
      })
      .catch(() => {}) // the plain image still works; this was only a head start
      .finally(() => this.decoding.delete(i));
  }

  /**
   * The loaded frame closest to `index`. While loading is still in progress
   * this lets the stage draw *something* for every scroll position instead of
   * blanking, so scrolling never has to wait.
   */
  nearest(index) {
    const i = Math.max(0, Math.min(FRAME_COUNT - 1, Math.round(index)));
    if (this.images[i]) return this.images[i];
    for (let d = 1; d < FRAME_COUNT; d += 1) {
      if (this.images[i - d]) return this.images[i - d];
      if (this.images[i + d]) return this.images[i + d];
    }
    return null;
  }
}
