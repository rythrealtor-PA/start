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
import * as THREE from '../vendor/three.module.js';
import { FrameSequence, FRAME_COUNT } from './frames.js';

/**
 * Scroll distance the animation occupies, as a multiple of viewport height.
 * A shorter runway means the clip advances further per scroll — this is the
 * knob for how fast the video plays, not the damping below.
 *
 * Careful with the arithmetic: the sticky panel consumes the first viewport, so
 * the distance actually scrolled is (STAGE_VH - 100) * 1vh, not STAGE_VH * 1vh.
 * Speeding playback up by 30% therefore means 360 / 1.3 = 277 of *scrollable*
 * height, i.e. 377 here — dividing 460 by 1.3 directly would overshoot to 42%.
 * The viewport height cancels out, so the ratio holds on any screen.
 */
const STAGE_VH = 377;

/** Frame index easing per rAF tick. Lower is smoother but laggier. */
const DAMPING = 0.12;

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

  uniform sampler2D uTex;
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

    vec3 col = texture2D(uTex, uv).rgb;
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
  constructor({ section, canvas, title, cue, progressBar }) {
    this.section = section;
    this.canvas = canvas;
    this.title = title;
    this.cue = cue;
    this.progressBar = progressBar;

    this.frames = new FrameSequence();
    this.currentIndex = 0;
    this.targetIndex = 0;
    this.titleOpacity = 1;
    this.dirty = true;
    this.running = false;

    this.reducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches;

    // Frames are drawn here first, then uploaded as a single texture. Holding
    // one texture instead of 145 is the difference between ~5MB and ~660MB of
    // GPU memory.
    this.buffer = document.createElement('canvas');
    this.bufferCtx = this.buffer.getContext('2d', { alpha: false });
  }

  async init() {
    this.section.style.setProperty(
      '--stage-vh',
      this.reducedMotion ? '100' : String(STAGE_VH),
    );

    this.frames.onProgress = (p) => {
      if (this.progressBar) this.progressBar.style.transform = `scaleX(${p})`;
      if (p >= 1) this.progressBar?.classList.add('is-complete');
    };
    this.frames.onFirstFrame = () => {
      this.setupRenderer();
      this.drawFrame(0);
      this.canvas.classList.add('is-ready');
      if (!this.reducedMotion) this.startLoop();
    };

    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onResize, { passive: true });

    await this.frames.start();
  }

  setupRenderer() {
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

    this.texture = new THREE.CanvasTexture(this.buffer);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.minFilter = THREE.LinearFilter;
    this.texture.magFilter = THREE.LinearFilter;
    this.texture.generateMipmaps = false;

    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTex: { value: this.texture },
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

  drawFrame(index) {
    const img = this.frames.nearest(index);
    if (!img) return;
    this.bufferCtx.drawImage(img, 0, 0, this.buffer.width, this.buffer.height);
    if (this.texture) this.texture.needsUpdate = true;
    this.dirty = true;
  }

  render() {
    if (!this.dirty) return;
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

  tick = () => {
    this.targetIndex = this.progress() * (FRAME_COUNT - 1);

    // Ease toward the target rather than snapping to it. This is what makes
    // fast scrolling read as motion instead of as a slideshow, and it costs
    // nothing in reverse.
    const delta = this.targetIndex - this.currentIndex;
    this.currentIndex += delta * DAMPING;

    if (Math.round(this.currentIndex) !== this.lastDrawn) {
      this.lastDrawn = Math.round(this.currentIndex);
      this.drawFrame(this.currentIndex);
    }

    this.updateTitle();
    this.render();

    // Stop once the frame has caught up with the scroll, so an idle page uses
    // no GPU at all. A scroll event restarts the loop.
    if (Math.abs(delta) < 0.01) {
      this.running = false;
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
