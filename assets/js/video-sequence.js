/**
 * The hero clip as a real video, scrubbed by seeking, for wide screens.
 *
 * Why: the still-frame sequence (frames.js) has to decode a 1920px AVIF on
 * the CPU for every frame shown — ~47ms each, measured. A laptop that manages
 * only a few of those per second plays the scrub at ~8fps however smooth the
 * scroll is. A <video> is decoded by the GPU's video engine instead, which
 * every laptop has and which turns out a 1080p H.264 frame in a few ms.
 *
 * The file is encoded for scrubbing, not playback: no B-frames and a keyframe
 * every 3 frames (see tools/encode-hero-video.sh), so any seek decodes at most
 * 3 frames — forward or backward. It is downloaded whole and played from a
 * Blob, because a seek into a range that is not buffered yet would wait on
 * the network.
 *
 * Two copies, so it moves almost at once: a light 960px one (2.9MB) is
 * fetched first and scrubs within about a second, then the sharp 1920px one
 * (23MB) downloads behind it and is swapped in on the frame already showing.
 * Both are hardware-decoded, so the scrub is equally fluid on either; only the
 * detail changes, and only once.
 *
 * Same interface as FrameSequence, so Stage drives either one. Until the
 * video has arrived, the first still frame stands in so the hero is never
 * blank; if the video cannot play at all, start() rejects and Stage falls
 * back to the stills.
 */
import { FRAME_COUNT, FRAMES_VERSION } from './frames.js';

const FPS = 24;

/**
 * H.264, because it is hardware-decoded on effectively every laptop and
 * desktop. A browser that cannot play it (some Linux Chromium builds) gets the
 * still frames instead, which is why there is no second format here.
 */
const SOURCES = [
  {
    type: 'video/mp4; codecs="avc1.640028"',
    quick: 'assets/video/hero-960.mp4',
    full: 'assets/video/hero-1920.mp4',
  },
];

/** Share of the loading hairline given to the light copy. */
const QUICK_SHARE = 0.15;

export class VideoSequence {
  constructor() {
    this.isVideo = true;
    this.width = 0;
    this.height = 0;
    this.onProgress = null;
    this.onFirstFrame = null;
    this.onReady = null;

    this.video = null;
    this.poster = null;
    this.playable = false;
    /** The frame the video element is showing right now, or -1. */
    this.shown = -1;
    /** The frame Stage wants. */
    this.wanted = 0;
    this.seeking = false;
    /** Bumped on every completed seek, so Stage knows to re-upload. */
    this.version = 0;
  }

  get complete() {
    return this.playable;
  }

  /** Which source this browser can play, or null. */
  static pickSource() {
    const probe = document.createElement('video');
    return SOURCES.find((s) => probe.canPlayType(s.type) === 'probably') ?? null;
  }

  async start() {
    const source = VideoSequence.pickSource();
    if (!source) throw new Error('no playable video codec');

    // The first still, for the instant before the video arrives. Same URL as
    // the preload in the page, so it costs no extra request.
    await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.poster = img;
        this.width = img.naturalWidth;
        this.height = img.naturalHeight;
        this.onFirstFrame?.();
        resolve();
      };
      img.onerror = reject;
      img.src = `assets/frames/desktop/f_001.avif?v=${FRAMES_VERSION}`;
    });

    const video = await this.makeVideo(await this.download(source.quick, 0, QUICK_SHARE));
    video.addEventListener('seeked', this.onSeeked);
    this.video = video;
    this.playable = true;
    this.seek(this.wanted);

    // Not awaited: the scrub already works; this only sharpens it.
    this.upgrade(source.full);
  }

  async makeVideo(blob) {
    const video = document.createElement('video');
    video.muted = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.src = URL.createObjectURL(blob);
    await new Promise((resolve, reject) => {
      video.addEventListener('loadeddata', resolve, { once: true });
      video.addEventListener('error', () => reject(video.error), { once: true });
    });
    // three.js sizes a texture from an element's width/height properties,
    // which on a <video> are the (unset, so zero) attributes, not the
    // picture's size. Without these a fresh texture is allocated 0x0.
    video.width = video.videoWidth;
    video.height = video.videoHeight;
    return video;
  }

  /**
   * Swaps in the sharp copy. It is first brought to the frame on screen, so
   * the only visible change is the extra detail. If it fails to arrive, the
   * light copy simply stays.
   */
  async upgrade(url) {
    try {
      const sharp = await this.makeVideo(await this.download(url, QUICK_SHARE, 1));
      const frame = this.wanted;
      await new Promise((resolve) => {
        sharp.addEventListener('seeked', resolve, { once: true });
        sharp.currentTime = (frame + 0.5) / FPS;
      });
      const light = this.video;
      light.removeEventListener('seeked', this.onSeeked);
      sharp.addEventListener('seeked', this.onSeeked);
      this.video = sharp;
      this.seeking = false;
      this.shown = frame;
      this.version += 1;
      URL.revokeObjectURL(light.src);
      light.removeAttribute('src');
      light.load();
      if (this.wanted !== this.shown) this.seek(this.wanted);
      this.onReady?.();
    } catch (error) {
      this.onProgress?.(1);
      console.warn('[video] sharp copy unavailable, keeping the light one:', error);
    }
  }

  /**
   * Fetches a whole file, reporting progress for the hairline under the title
   * as the span `from`..`to` of the full bar.
   */
  async download(url, from = 0, to = 1) {
    const report = (p) => this.onProgress?.(from + (to - from) * p);
    const response = await fetch(`${url}?v=${FRAMES_VERSION}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const total = Number(response.headers.get('content-length')) || 0;
    if (!total || !response.body) {
      const blob = await response.blob();
      report(1);
      return blob;
    }

    const reader = response.body.getReader();
    const chunks = [];
    let received = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      report(Math.min(0.99, received / total));
    }
    report(1);
    return new Blob(chunks, { type: response.headers.get('content-type') || '' });
  }

  /** Frame i is on screen from i/FPS; aim for the middle of it. */
  seek(i) {
    this.seeking = true;
    this.seekingTo = i;
    this.video.currentTime = (i + 0.5) / FPS;
  }

  onSeeked = () => {
    this.seeking = false;
    this.shown = this.seekingTo;
    this.version += 1;
    // Only ever one seek in flight; if the playhead moved meanwhile, chase it.
    if (this.wanted !== this.shown) this.seek(this.wanted);
    this.onReady?.();
  };

  /**
   * What to draw for frame `index`. Asks the video for that frame and returns
   * the video element itself — whatever frame it holds right now — or the
   * first still until the video has arrived.
   */
  pick(index) {
    const i = Math.max(0, Math.min(FRAME_COUNT - 1, Math.round(index)));
    this.wanted = i;
    if (!this.playable) return { image: this.poster, exact: i === 0 };
    if (!this.seeking && this.shown !== i) this.seek(i);
    return { image: this.video, exact: this.shown === i };
  }

  /** Nothing to pre-decode: the video engine is fast enough to seek on demand. */
  warm() {}

  /** Never hold the playhead: seeks chase it instead. */
  readyEdge(from, dir) {
    return dir > 0 ? FRAME_COUNT - 1 : 0;
  }
}
