/**
 * Loads the hero still sequence and hands the stage a frame for any index.
 *
 * The clip ships as numbered stills rather than as a <video> because scrubbing
 * video.currentTime is unreliable — seeks snap to keyframes, reverse playback
 * stutters, and iOS Safari throttles it. With stills, playing backwards is just
 * a decreasing index.
 *
 * Frames are kept as HTMLImageElements, not ImageBitmaps. Decoded bitmaps for
 * 145 frames at 1440x800 would be ~660MB of RAM; as <img> the browser holds
 * them compressed and manages its own decode cache.
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
  }

  /** True once every frame has landed. */
  get complete() {
    return this.loadedCount === FRAME_COUNT;
  }

  load(index) {
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
        resolve(img);
      };
      // A missing frame must not stall the sequence — nearest() will simply
      // reach past the gap.
      img.onerror = () => {
        this.loadedCount += 1;
        this.onProgress?.(this.loadedCount / FRAME_COUNT);
        resolve(null);
      };
      img.src = `${this.basePath}/f_${pad(index + 1)}.${this.ext}`;
    });
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
