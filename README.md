# Ryth Vara — Pennsylvania Real Estate

A one-page site for Ryth Vara, a bilingual real estate agent working across
Pennsylvania. The hero is a scroll-driven frame animation: an aerial clip of a
house whose walls turn transparent to reveal the interiors, playing forward as
you scroll down and backward as you scroll up.

Plain static files. No build step, no framework, no CDN — open `index.html`
through any web server and it runs.

---

## Fill these in before going live

Everything personal lives in **`assets/js/config.js`**. Search it for `TODO`:

| What | Status |
|---|---|
| **Phone number** | done — 929.345.6838 |
| **Email** | done — `ryth.realtor@gmail.com` |
| Brokerage name | empty |
| PA license number | empty |
| Years of experience | empty |
| Instagram / Facebook / LinkedIn | empty |
| Headshot | using a placeholder — see below |

Any field left empty is simply left off the page rather than rendered blank, so
partial answers are safe to ship.

### Headshot

Drop the image in `assets/img/` and point `portrait` at it, e.g.
`portrait: 'assets/img/ryth.jpg'`. Portrait orientation, roughly 4:5. Until
then a generated placeholder stands in at the right size, so adding the real
photo will not shift the layout.

### Contact form

The form posts to [Web3Forms](https://web3forms.com) — free, and no server to
run. Sign up with your email, they send you an access key, paste it into
`web3formsKey` in `config.js`. Submissions then arrive in your inbox.

**Until you add a key the form still works**: it opens the visitor's email app
with everything they typed already filled in. No enquiry is lost either way.

### Listings

Edit **`assets/js/listings.js`**. Each listing is one object:

```js
{
  photo:   'assets/img/listings/my-listing.jpg',
  address: '412 Chestnut Ridge Road',
  city:    'Doylestown, PA',
  price:   '$685,000',
  beds:    4,
  baths:   2.5,          // halves are fine
  sqft:    2840,         // optional — the slot is skipped if omitted
  status:  'For sale',   // optional: For sale | Pending | Sold | For rent
}
```

Put photos in `assets/img/listings/`, landscape, ideally 4:3 and at least
1200px wide. One photo per listing — that is the design.

The six shipped listings are placeholders with generated artwork. Delete them
as you add real ones.

---

## Running it locally

It must be served over HTTP, not opened as a `file://` path — the code uses ES
modules, which browsers block on `file://`.

```bash
python3 -m http.server 8000
# then open http://127.0.0.1:8000
```

## Deploying

Any static host works, with no build configuration:

- **GitHub Pages** — Settings → Pages → deploy from branch, root folder
- **Netlify / Vercel** — connect the repo, leave the build command empty and
  the publish directory as the repo root

---

## How the hero animation works

The clip is **not** a `<video>` element. Scrubbing `video.currentTime` is
unreliable — seeks snap to keyframes, reverse playback stutters, and iOS Safari
throttles it. Instead the video is decoded ahead of time into 145 still frames,
and scroll position picks one. Playing in reverse is then just a decreasing
array index, which is why scrolling up is as smooth as scrolling down.

- **`assets/js/frames.js`** — loads the sequence and picks a set per visitor
- **`assets/js/stage.js`** — the three.js scene, shader, and scroll driver

A tall section acts as the scroll runway while a sticky canvas inside it stays
on screen. Scroll progress maps to a frame index, eased each animation frame so
fast scrolling reads as motion rather than as a slideshow. The render loop stops
itself once the frame catches up with the scroll, so an idle page uses no GPU.

three.js draws the frame through a shader that cover-fits it to any viewport,
grades it toward the page palette, adds a vignette and grain, and feathers the
bottom edge so the footage dissolves into the section below.

The title is ordinary DOM text over the canvas, not burned into the video, so
it stays selectable and readable by screen readers — and it fades back in when
you scroll up.

**Fallbacks:** no WebGL falls back to a plain 2D canvas with the scrub intact;
`prefers-reduced-motion` holds a single frame and collapses the runway so the
page reads as an ordinary site.

### Frame sets

A visitor downloads exactly one:

| Set | Size | Served to |
|---|---|---|
| `assets/frames/desktop/` | 1440px AVIF | wide viewports with AVIF support |
| `assets/frames/mobile/` | 900px AVIF | narrow viewports with AVIF support |
| `assets/frames/fallback/` | 900px WebP | anything without AVIF (Safari < 16.4, older Android) |

### Replacing the video

```bash
tools/extract-frames.sh path/to/new-video.mp4
```

Requires `ffmpeg` with `libaom-av1` and `libwebp`. Then set `FRAME_COUNT` in
`assets/js/frames.js` to the number of frames it reports.

Two encoder gotchas are documented in the script, both found by loading the
output in a real browser: AVIF has to be written one file per `ffmpeg -f avif`
call (a numbered `-f image2` sequence produces files that tools call valid but
Chromium refuses to decode), and `-pix_fmt yuv420p` must be explicit or libaom
picks planar RGB and doubles the file size for no visible gain.

---

## Regenerating assets

```bash
tools/vendor-deps.sh        # three.js + the two typefaces, into the repo
tools/make-placeholders.py  # placeholder listing and portrait artwork
```

Both are committed already; you only need these if you are changing versions.

## Design

The palette comes from Pennsylvania building materials rather than the usual
luxury-realtor kit — bluestone, slate roofs, fieldstone, and the aged brass on
old front doors. The dark page is what lets the footage act as the light source.

```
slate     #12171C     bluestone  #2C3E4A
brass     #B08D57     ivory      #F2EEE7
```

Type is **Fraunces** for display and **Archivo** for everything else, both
self-hosted under the SIL Open Font License (see `assets/fonts/OFL.txt`).
Fraunces carries an optical-size axis, so headings get a chiselled, high-contrast
cut while small text stays readable — from a single file.
