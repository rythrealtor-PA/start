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
 * every 6 frames (see tools/encode-hero-video.sh), so any seek decodes at most
 * 6 frames — forward or backward. It is downloaded whole and played from a
 * Blob, because a seek into a range that is not buffered yet would wait on
 * the network.
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
  { type: 'video/mp4; codecs="avc1.640028"', url: 'assets/video/hero-1920.mp4' },
];

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

    const blob = await this.download(source.url);
    const video = document.createElement('video');
    video.muted = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.src = URL.createObjectURL(blob);
    await new Promise((resolve, reject) => {
      video.addEventListener('loadeddata', resolve, { once: true });
      video.addEventListener('error', () => reject(video.error), { once: true });
    });
    video.addEventListener('seeked', this.onSeeked);

    this.video = video;
    this.playable = true;
    this.seek(this.wanted);
  }

  /** Fetches the whole file, reporting progress for the hairline under the title. */
  async download(url) {
    const response = await fetch(`${url}?v=${FRAMES_VERSION}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const total = Number(response.headers.get('content-length')) || 0;
    if (!total || !response.body) return response.blob();

    const reader = response.body.getReader();
    const chunks = [];
    let received = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      this.onProgress?.(Math.min(0.99, received / total));
    }
    this.onProgress?.(1);
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
