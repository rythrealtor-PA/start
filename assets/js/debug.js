/**
 * Add ?debug to the address to see, in the corner, how the hero is really
 * playing on this machine — so tuning works from measurements on the actual
 * device rather than guesses. Inert without the flag.
 *
 *   screen   how many times per second the canvas was redrawn
 *   pictures how many different video pictures reached the screen per second
 *   mode     video (GPU video engine) or stills (CPU-decoded frames)
 */
export function initDebug(stage) {
  if (!new URLSearchParams(location.search).has('debug')) return;
  const box = document.createElement('pre');
  box.setAttribute('aria-hidden', 'true');
  box.style.cssText =
    'position:fixed;left:8px;top:8px;z-index:99;margin:0;padding:8px 10px;' +
    'font:12px/1.4 ui-monospace,monospace;color:#f2eee7;' +
    'background:rgba(0,0,0,.72);pointer-events:none;white-space:pre';
  document.body.append(box);

  let last = { ...stage.stats, t: performance.now() };
  const peak = { screen: 0, pictures: 0 };
  setInterval(() => {
    const now = performance.now();
    const dt = (now - last.t) / 1000;
    const screen = Math.round((stage.stats.renders - last.renders) / dt);
    const pictures = Math.round((stage.stats.newFrames - last.newFrames) / dt);
    peak.screen = Math.max(peak.screen, screen);
    peak.pictures = Math.max(peak.pictures, pictures);
    last = { ...stage.stats, t: now };
    box.textContent =
      `mode      ${stage.frames.isVideo ? 'video' : 'stills'}\n` +
      `screen    ${screen}/s   (best ${peak.screen})\n` +
      `pictures  ${pictures}/s   (best ${peak.pictures})\n` +
      `frame     ${Math.round(stage.currentIndex)} / ${Math.round(stage.targetIndex)}`;
  }, 500);
}
