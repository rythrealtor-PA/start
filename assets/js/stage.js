/**
 * The scroll-driven frame animation.
 *
 * A sticky full-viewport canvas renders one still from the hero sequence. Scroll
 * position picks the frame, so scrolling down plays the clip forward and
 * scrolling up plays it backward — reverse needs no special handling, it is
 * simply a decreasing index.
 *
 * three.js draws it through a shader that cover-fits the frame to any viewport,
 * grades it toward the page palette, and feathers the bottom edge so the footage
 * dissolves into the section below instead of ending at a hard line.
 */
import * as THREE from '../vendor/three.min.js';
import { FrameSequence, FRAME_COUNT } from './frames.js';
import { VideoSequence } from './video-sequence.js';

/**
 * Scroll distance the animation occupies, as a multiple of viewport height.
 * A shorter runway means the clip advances further per scroll — this is the
 * knob for how fast the video plays, not the damping below.
 *
 * Careful with the arithmetic: the sticky panel consumes the first viewport, so
 * the distance actually scrolled is (STAGE_VH - 100) * 1vh, not STAGE_VH * 1vh.
 * Speeding playback up by 30% means dividing the *scrollable* height by 1.3,
 * not the whole value — dividing 460 by 1.3 directly would overshoot to 42%.
 * The viewport height cancels out, so the ratio holds on any screen.
 *
 * History: 460 (360 scrollable) -> 377 (277) -> 313 (213) -> 252 (152) ->
 * 209 (109, another 40%), so the clip now plays 3.3x faster per scroll than
 * it first shipped. The whole 193-frame sequence takes about 1.1
 * screen-heights of scrolling.
 */
const STAGE_VH = 209;

/**
 * How far the playhead closes the gap to the scroll position each 1/60s.
 * Lower is smoother but laggier. Applied per unit of *time*, not per animation
 * frame, so a 120Hz phone or monitor eases at the same speed as a 60Hz one
 * instead of twice as fast.
 */
const DAMPING = 0.12;

/**
 * A jump bigger than this many frames (a link to a section, a page restored
 * mid-scroll) is allowed to skip ahead instead of playing every frame.
 */
const MAX_GATED_JUMP = 60;

/** Fraction of the scroll over which the title fades out. */
const TITLE_FADE = 0.12;

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;

  uniform sampler2D uTexA;  // frame floor(playhead)
  uniform sampler2D uTexB;  // the frame after it
  uniform float uMix;       // how far between the two, 0..1
  uniform vec2  uRes;       // canvas size, px
  uniform vec2  uTexSize;   // frame native size, px
  uniform vec3  uBase;      // page background, for the edge dissolve
  uniform float uScrim;     // top scrim strength, tied to title visibility

  varying vec2 vUv;

  void main() {
    // Cover-fit: fill the viewport and crop the overflow, like
    // background-size: cover, but done in UV space so no CSS hacks are needed.
    float canvasAspect = uRes.x / uRes.y;
    float texAspect    = uTexSize.x / uTexSize.y;
    vec2 uv = vUv;
    if (canvasAspect > texAspect) {
      uv.y = (uv.y - 0.5) * (texAspect / canvasAspect) + 0.5;
    } else {
      uv.x = (uv.x - 0.5) * (canvasAspect / texAspect) + 0.5;
    }
    // Frames are uploaded top row first (flipY off — decoded bitmaps ignore
    // it anyway), so flip here instead.
    uv.y = 1.0 - uv.y;

    // The clip has 193 pictures and the scroll can land between any two.
    // Blending the neighbours by the fractional position turns a sequence of
    // jumps into continuous motion; at rest the playhead sits exactly on a
    // frame, so a still image is never a blend.
    vec3 col = mix(texture2D(uTexA, uv).rgb, texture2D(uTexB, uv).rgb, uMix);
    float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));

    // Grade toward the page palette: lift the darks to slate so they read as
    // part of the page rather than as crushed black, and warm the highlights
    // a touch toward the brass accent.
    col += vec3(0.035, 0.045, 0.058) * (1.0 - smoothstep(0.0, 0.38, luma));
    col *= mix(vec3(1.0), vec3(1.045, 1.0, 0.93), smoothstep(0.42, 1.0, luma));

    // Vignette. Slightly taller than wide so it does not pinch the corners of
    // wide monitors.
    vec2 p = vUv - 0.5;
    float vig = 1.0 - smoothstep(0.36, 0.98, length(p * vec2(1.0, 1.12)));
    col *= mix(0.62, 1.0, vig);

    // Scrim while the title is up: a broad dim across the frame with extra
    // weight directly behind the type, so the headline holds up even over the
    // brightest part of the facade. Note vUv.y is 0 at the BOTTOM in GL — the
    // title sits in the upper third, which is y ~= 0.66 here. Multiplied by
    // uScrim, so it leaves exactly when the title does and never darkens the
    // footage during the scroll.
    float behindTitle =
      1.0 - smoothstep(0.10, 0.62, length((vUv - vec2(0.5, 0.66)) * vec2(1.0, 1.7)));
    col *= 1.0 - uScrim * (0.32 + 0.44 * behindTitle);

    // Dissolve the bottom edge into the page so the stage hands off to the
    // next section without a seam.
    col = mix(uBase, col, smoothstep(0.0, 0.14, vUv.y));

    // Static grain — keyed to pixel position only, never to time, so it does
    // not force the render loop to keep running once the scroll settles.
    float n = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
    col += (n - 0.5) * 0.022;

    gl_FragColor = vec4(col, 1.0);
  }
`;

const clamp01 = (v) => Math.max(0, Math.min(1, v));

export class Stage {
  constructor({ section, canvas, title, cue, progressBar, useVideo = false }) {
    this.section = section;
    this.canvas = canvas;
    this.title = title;
    this.cue = cue;
    this.progressBar = progressBar;

    // Wide screens can scrub a real video (decoded by the GPU's video engine);
    // everything else, and any browser where the video fails, uses stills.
    this.frames = useVideo ? new VideoSequence() : new FrameSequence();
    /** Counters for the ?debug overlay. */
    this.stats = { renders: 0, newFrames: 0 };
    this.currentIndex = 0;
    this.targetIndex = 0;
    this.lastTime = 0;
    this.titleOpacity = 1;
    this.dirty = true;
    this.running = false;

    this.reducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches;

    // Only used without WebGL: frames are composited here and the canvas is
    // shown directly. With WebGL, frames go straight to two GPU textures —
    // two, not 193, which is the difference between ~16MB and ~1.6GB.
    this.buffer = document.createElement('canvas');
    this.bufferCtx = this.buffer.getContext('2d', { alpha: false });
  }

  async init() {
    this.section.style.setProperty(
      '--stage-vh',
      this.reducedMotion ? '100' : String(STAGE_VH),
    );

    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onResize, { passive: true });

    this.wire(this.frames);
    try {
      await this.frames.start();
    } catch (error) {
      if (!this.frames.isVideo) throw error;
      // The video could not load or play here. The stills always can.
      console.warn('[stage] video unavailable, using stills:', error);
      this.frames = new FrameSequence();
      this.wire(this.frames);
      this.shownIndex = NaN;
      await this.frames.start();
    }
  }

  wire(frames) {
    frames.onProgress = (p) => {
      if (this.progressBar) this.progressBar.style.transform = `scaleX(${p})`;
      if (p >= 1) this.progressBar?.classList.add('is-complete');
    };
    // The frame on screen was a stand-in for one still downloading, decoding
    // or seeking: redraw once it is ready.
    frames.onReady = () => {
      if (this.pendingExact && !this.running && !this.reducedMotion) {
        this.shownIndex = NaN;
        this.startLoop();
      }
    };
    frames.onFirstFrame = () => {
      if (!this.rendererReady) this.setupRenderer();
      this.showFrame(this.currentIndex);
      this.canvas.classList.add('is-ready');
      if (!this.reducedMotion) this.startLoop();
    };
  }

  setupRenderer() {
    this.rendererReady = true;
    this.buffer.width = this.frames.width;
    this.buffer.height = this.frames.height;

    try {
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: false,
        alpha: false,
        powerPreference: 'high-performance',
      });
    } catch {
      this.renderer = null; // handled by render()'s 2D path
    }

    if (!this.renderer) {
      // Without the shader there is no cover-fit and no scrim, so CSS has to
      // supply both. See the .no-webgl rules in styles.css.
      document.documentElement.classList.add('no-webgl');
      return;
    }

    this.renderer.setClearColor(0x12171c, 1);
    this.scene = new THREE.Scene();
    // A full-screen quad. The vertex shader writes clip space directly, so the
    // camera is a formality kept for readability.
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const makeTexture = () => {
      const t = new THREE.Texture(this.frames.pick(0).image);
      t.colorSpace = THREE.SRGBColorSpace;
      t.minFilter = THREE.LinearFilter;
      t.magFilter = THREE.LinearFilter;
      t.generateMipmaps = false;
      t.flipY = false;
      return t;
    };
    this.texA = makeTexture();
    this.texB = makeTexture();

    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTexA: { value: this.texA },
        uTexB: { value: this.texB },
        uMix: { value: 0 },
        uRes: { value: new THREE.Vector2(1, 1) },
        uTexSize: {
          value: new THREE.Vector2(this.frames.width, this.frames.height),
        },
        uBase: { value: new THREE.Color(0x12171c) },
        uScrim: { value: 1 },
      },
    });

    this.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.material));
    this.resize();
  }

  resize() {
    if (!this.renderer) return;
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    // Capping DPR at 2 keeps 4K and high-DPI phones from rendering four times
    // the pixels for detail nobody can see on moving footage.
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h, false);
    this.material.uniforms.uRes.value.set(w, h);
    this.dirty = true;
  }

  onResize = () => {
    this.resize();
    this.render();
  };

  onScroll = () => {
    if (this.reducedMotion) return;
    if (!this.running) this.startLoop();
  };

  /** Where the visitor is through the stage, 0 to 1. */
  progress() {
    const rect = this.section.getBoundingClientRect();
    const scrollable = rect.height - window.innerHeight;
    if (scrollable <= 0) return 0;
    return clamp01(-rect.top / scrollable);
  }

  /**
   * Puts the playhead at `position` (fractional frame index): frame
   * floor(position) in one texture, the next frame in the other, blended by
   * the remainder. Moving forward one frame reuses the texture that already
   * holds it, so a step costs one upload, not two.
   */
  showFrame(position) {
    const last = FRAME_COUNT - 1;
    const p = Math.max(0, Math.min(last, position));
    const a = Math.floor(p);
    const b = Math.min(a + 1, last);
    const mix = b === a ? 0 : p - a;

    if (this.frames.isVideo) {
      this.showVideoFrame(p);
      return;
    }

    if (!this.renderer) {
      this.draw2D(a, b, mix);
      return;
    }

    const held = (t) => t.userData.index;
    if (held(this.texA) !== a && (held(this.texB) === a || held(this.texA) === b)) {
      [this.texA, this.texB] = [this.texB, this.texA];
      this.material.uniforms.uTexA.value = this.texA;
      this.material.uniforms.uTexB.value = this.texB;
    }
    this.pendingExact = false;
    this.upload(this.texA, a);
    // Skip the second frame while it would be invisible anyway.
    if (mix > 0.001) this.upload(this.texB, b);
    this.material.uniforms.uMix.value = mix > 0.001 ? mix : 0;
    this.dirty = true;
  }

  /**
   * Video mode: one frame at a time (a video element holds one), so no blend —
   * the seek rate is high enough not to need it. Re-uploads only when a seek
   * has actually landed a new frame.
   */
  showVideoFrame(position) {
    const { image, exact } = this.frames.pick(position);
    this.pendingExact = !exact;
    if (!image) return;
    const key = `${this.frames.version}:${image === this.frames.video}`;
    if (!this.renderer) {
      if (key !== this.videoKey) {
        this.videoKey = key;
        this.bufferCtx.drawImage(image, 0, 0, this.buffer.width, this.buffer.height);
        this.stats.newFrames += 1;
      }
      this.dirty = true;
      return;
    }
    const held = this.texA.userData;
    if (held.key !== key) {
      held.key = key;
      this.texA.image = image;
      this.texA.needsUpdate = true;
      this.stats.newFrames += 1;
    }
    this.material.uniforms.uMix.value = 0;
    this.dirty = true;
  }

  /** Uploads frame `index` into `texture` unless it already holds it. */
  upload(texture, index) {
    const { image, exact } = this.frames.pick(index);
    const held = texture.userData;
    if (!exact) this.pendingExact = true;
    // Already there — or already showing this same stand-in.
    if (held.index === index && (held.exact || held.image === image)) return;
    texture.image = image;
    texture.needsUpdate = true;
    this.stats.newFrames += 1;
    held.index = index;
    held.exact = exact;
    held.image = image;
  }

  /** The same blend without WebGL, composited on the 2D buffer. */
  draw2D(a, b, mix) {
    const ctx = this.bufferCtx;
    const { width, height } = this.buffer;
    const first = this.frames.pick(a).image;
    if (!first) return;
    ctx.globalAlpha = 1;
    ctx.drawImage(first, 0, 0, width, height);
    if (mix > 0.001) {
      const second = this.frames.pick(b).image;
      if (second) {
        ctx.globalAlpha = mix;
        ctx.drawImage(second, 0, 0, width, height);
        ctx.globalAlpha = 1;
      }
    }
    this.dirty = true;
  }

  render() {
    if (!this.dirty) return;
    this.stats.renders += 1;
    if (this.renderer) {
      this.material.uniforms.uScrim.value = this.titleOpacity;
      this.renderer.render(this.scene, this.camera);
    } else if (this.canvas !== this.buffer) {
      // No WebGL: show the buffer directly. The grade and vignette are lost
      // but the scroll animation itself still works. Once swapped, this.canvas
      // *is* the buffer — guarding it stops a replaceWith(self) every frame.
      this.buffer.className = this.canvas.className;
      this.canvas.replaceWith(this.buffer);
      this.canvas = this.buffer;
    }
    this.dirty = false;
  }

  tick = (now) => {
    // The target is always a whole frame. The playhead glides between frames
    // on the way there (that is what the blend is for) but always comes to
    // rest exactly on one, so a paused image is as sharp as the source.
    const target = Math.round(this.progress() * (FRAME_COUNT - 1));
    this.targetIndex = target;

    // Frame-rate independent easing: the same fraction of the gap per 1/60s
    // whether the display runs at 60Hz, 90Hz or 120Hz. dt is capped so a tab
    // coming back from the background does not leap.
    const dt = this.lastTime ? Math.min(now - this.lastTime, 64) : 16.67;
    this.lastTime = now;
    const ease = 1 - Math.pow(1 - DAMPING, dt / 16.67);

    const delta = this.targetIndex - this.currentIndex;
    const settled = Math.abs(delta) < 0.01;
    let next = settled ? this.targetIndex : this.currentIndex + delta * ease;
    // Never run ahead of the decoder: play every frame, a moment late if need
    // be, rather than skip. See FrameSequence.readyEdge().
    if (!settled && Math.abs(delta) < MAX_GATED_JUMP) {
      const edge = this.frames.readyEdge(this.currentIndex, Math.sign(delta));
      next = delta > 0 ? Math.min(next, edge) : Math.max(next, edge);
    }
    this.currentIndex = next;

    this.frames.warm(this.currentIndex, this.targetIndex);
    if (this.currentIndex !== this.shownIndex) {
      this.shownIndex = this.currentIndex;
      this.showFrame(this.currentIndex);
    }

    this.updateTitle();
    this.render();

    // Stop once the frame has caught up with the scroll, so an idle page uses
    // no GPU at all. A scroll event restarts the loop.
    if (settled) {
      this.running = false;
      this.lastTime = 0;
      return;
    }
    requestAnimationFrame(this.tick);
  };

  updateTitle() {
    const p = this.progress();
    const opacity = clamp01(1 - p / TITLE_FADE);
    if (Math.abs(opacity - this.titleOpacity) < 0.001) return;
    this.titleOpacity = opacity;
    // Published for the .no-webgl scrim, which stands in for the shader's.
    this.section.style.setProperty('--title-opacity', String(opacity));
    this.title.style.opacity = String(opacity);
    // A small rise as it goes, and it comes back on the way up.
    this.title.style.transform = `translateY(${(1 - opacity) * -2.2}rem)`;
    // The cue says "Scroll" — it is meaningless once they have, so it leaves
    // with the title rather than riding along to the final frame.
    if (this.cue) this.cue.style.opacity = String(opacity);
    this.title.setAttribute('aria-hidden', opacity < 0.05 ? 'true' : 'false');
    this.dirty = true;
  }

  startLoop() {
    if (this.running) return;
    this.running = true;
    requestAnimationFrame(this.tick);
  }
}
