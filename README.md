# Ryth Vara — Pennsylvania Real Estate

A one-page site for Ryth Vara, a bilingual real estate agent working across
Pennsylvania. The hero is a scroll-driven frame animation: an aerial clip of a
house whose walls turn transparent to reveal the interiors, playing forward as
you scroll down and backward as you scroll up.

Plain static files. No build step, no framework, no CDN — open `index.html`
through any web server and it runs.

---

## Before going live

Everything personal lives in **`assets/js/config.js`**.

| What | Status |
|---|---|
| Phone | done — 929.345.6838 |
| Email | done — `ryth.realtor@gmail.com` |
| Brokerage | done — Real of Pennsylvania |
| PA license | done — RS380174 |
| Instagram / TikTok / Facebook | done |
| Headshot | done — `assets/img/ryth-vara.jpg` |
| Contact form | done — delivering to the email above |
| **Listings** | **still placeholders — see below** |
| Testimonials | done — four real client quotes |
| Years of experience | empty (optional) |
| Privacy Policy / Terms of Use | drafted — `privacy.html`, `terms.html`; have your broker review |
| FAQ | drafted in `index.html` — check the buyer-agreement answer with your broker |
| Visitor analytics | off until a Cloudflare Web Analytics token is set in `config.js` |
| Custom domain | **not connected — see below** |

Live at **https://rythrealtor-pa.github.io/start/** (GitHub Pages from `main`).

**Custom domain — not connected yet.** On 2026-09-28 the .com registry had no
record of `rythvara.com` (DNS answered NXDOMAIN and the Verisign RDAP lookup
returned 404) — the registration had not gone through, whether unpaid, still
processing, or bought under a different spelling. The `CNAME` file was
removed because with it in place GitHub redirected every visitor to a domain
that does not exist, taking the whole site offline. Once the domain shows as
active in Namecheap:

1. Namecheap → Domain List → rythvara.com → Advanced DNS. Add four **A**
   records on host `@`: `185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153`; and a **CNAME** on host `www` pointing
   to `rythrealtor-pa.github.io.` Delete Namecheap's default parking records.
2. Put a file named `CNAME` containing the single line `rythvara.com` back at
   the repo root (or type the domain into Settings → Pages → Custom domain,
   which writes the same file).
3. When the DNS check turns green, tick **Enforce HTTPS** in Settings → Pages.

The canonical URLs, sitemap, robots.txt and social-share tags already point at
`https://rythvara.com`, so nothing else needs to change on the day.

Any field left empty is left off the page rather than rendered blank, so
partial answers are safe to ship.

### Advertising compliance

Pennsylvania requires advertising to identify the broker, so the brokerage name
and licence number are **not** optional decoration here — they render in two
places, both built from `config.js` so they cannot drift apart:

- the facts list in the bio section
- the footer line, beside the brokerage and team logos

If your broker has specific requirements about wording, logo size, or the
placement of the Equal Housing Opportunity mark, those are the two places to
adjust. The footer currently carries "Equal Housing Opportunity" as text — if
your broker expects the official HUD logo artwork, drop it in `assets/img/` and
add it beside the other marks in the footer.

### Logos

`assets/img/real-of-pennsylvania.png` is a **reversed** (white-on-transparent)
version, generated from the black-on-white original so it reads on the dark
page. The artwork is unchanged — only its colour is flipped, which is what a
reversed logo is. If Real's brand portal provides an official reversed asset,
prefer that file and drop it in at the same path.

### Contact form

The form posts to [Web3Forms](https://web3forms.com) — free, and no server to
run. The access key is set in `config.js` and submissions arrive in the inbox it
was registered with.

That key is **public by design**. Every Web3Forms key sits in the page source
where anyone can read it, and all it can do is deliver mail to the address it
was registered with — it is not a password. If it ever starts attracting spam,
generate a new one and replace it. A hidden `botcheck` honeypot field in the
form already turns away the routine bots.

**If the key is ever removed the form still works**: it falls back to opening
the visitor's email app with everything they typed prefilled, so no enquiry is
lost either way.

### Listings and testimonials — the editor at /admin.html

Open **`yoursite.com/admin.html`** to add, edit, reorder and remove both
**listings** and **testimonials** — the two tabs at the top switch between them.
Fill in the form and press **Publish**; the live site updates about a minute
later. Only the section you actually changed is written, so editing
testimonials never touches listings.

It is a form, not a file. Photos are shrunk to a sensible web size in the
browser before they upload, so a photo straight off a phone is fine.

**One-time setup.** The site is static — there is no server to log into — so
publishing works by committing straight to this repository with a GitHub access
token you create once:

1. Go to [fine-grained access tokens](https://github.com/settings/personal-access-tokens/new).
2. **Repository access** → *Only select repositories* → this one.
3. **Repository permissions** → **Contents** → *Read and write*. Nothing else.
4. Generate, copy, and paste it into `/admin.html`.

The token is stored only in that browser on that device. It is never part of the
published site, so a visitor who finds `/admin.html` sees the setup screen and
can do nothing. Anyone holding the token can write to this repository, which is
why it is scoped to one repo and to Contents alone — and why **Sign out** is
there for a shared or borrowed computer. If a token ever leaks, revoke it on the
same GitHub page and generate a new one.

Both live in **`assets/data/`** as plain JSON rather than JavaScript, precisely
so the editor can rewrite them without a stray comma taking the page down.
Editing by hand still works — `listings.json`:

```json
{
  "photo":   "assets/img/listings/my-listing.jpg",
  "address": "412 Chestnut Ridge Road",
  "city":    "Doylestown, PA",
  "price":   "$685,000",
  "beds":    4,
  "baths":   2.5,
  "sqft":    2840,
  "status":  "For sale"
}
```

`sqft` and `status` are optional. `status` is one of *For sale*, *Pending*,
*Sold*, *For rent*.

And `testimonials.json`:

```json
{
  "quote":  "Ryth sold our place faster than we thought possible.",
  "name":   "Danielle R.",
  "detail": "Seller, Stroudsburg"
}
```

`detail` is optional. Quotes in Spanish are fine — the fonts carry the accents.

The six shipped listings are placeholders with invented addresses and generated
artwork. **Replace them before sharing the site** — they are the one thing on
the page that is not real.

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
throttles it. Instead the video is decoded ahead of time into 193 still frames,
and scroll position picks one. Playing in reverse is then just a decreasing
array index, which is why scrolling up is as smooth as scrolling down.

- **`assets/js/video-sequence.js`** — laptops and desktops: scrubs
  `assets/video/hero-1920.mp4` (H.264, decoded by the GPU's video engine).
  Rebuild it with `tools/encode-hero-video.sh`. Falls back to the stills if
  the browser cannot play it.
- **`assets/js/frames.js`** — phones (and the fallback): loads the still
  sequence and picks a set per visitor
- **`assets/js/stage.js`** — the three.js scene, shader, and scroll driver

A tall section acts as the scroll runway while a sticky canvas inside it stays
on screen. Scroll progress maps to a frame index, eased over time so fast
scrolling reads as motion rather than as a slideshow. The render loop stops
itself once the frame catches up with the scroll, so an idle page uses no GPU.

Three things keep it fluid with 193 frames (the source is 8s at 24fps):

- **Blending.** The playhead is fractional; the shader crossfades the two
  frames either side of it, so the picture moves continuously instead of
  holding and jumping. At rest it always lands exactly on one frame, so a
  paused image is never a blend.
- **Decoding ahead.** Frames from the playhead toward where the scroll is
  heading (a flick moves the target ~20 frames at once) are decoded in advance,
  several in parallel on background threads, from the downloaded file rather
  than the `<img>`. Decoded frames are capped at ~160MB and released as soon as
  they fall out of that window.
- **Never skipping.** The playhead is not allowed to pass a frame that is
  downloaded but not yet decoded. A flick that outruns the device therefore
  plays through every frame a moment late instead of jumping to a stand-in —
  on a phone-sized test that took wrong-frame displays from 11 per flick
  sequence to 0.
- **Time-based easing,** so 60Hz, 90Hz and 120Hz screens all feel the same.

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
| `assets/frames/desktop/` | 1728px AVIF, ~17MB | wide viewports with AVIF support |
| `assets/frames/mobile/` | 1170px AVIF, ~7MB | narrow viewports with AVIF support |
| `assets/frames/fallback/` | 1000px WebP, ~10MB | anything without AVIF (Safari < 16.4, older Android) |

### A note on the quality settings

These were measured against the source frame rather than guessed, because the
first pass shipped visibly soft:

| | PSNR vs source |
|---|---|
| Downscaling 1928px → 1440px, no compression | 40.2 dB — invisible |
| Compressing at crf 44, no downscale | 30.3 dB — the real loss |
| What shipped first (1440px, crf 44) | 28.7 dB — smeared stone and foliage |
| What ships now (1728px, crf 30) | 34.1 dB — near-indistinguishable at 1:1 |

The lesson: for this footage **resolution is cheap and compression is
expensive**. If the sequence ever needs to shrink, take pixels off the width
before taking quality off the encoder.

The first source video was 1928×1072, so 34 dB was close to its ceiling. It
has since been replaced by a 4K version of the clip (3856×2148, 8 seconds, 193
frames), which is the better source that note called for: scaled down to
1920px it carries visibly crisper stone, siding and shingles, and the extra
two seconds give 33% more real frames over the same scroll distance. Measured
on a 13-frame sample, against the 4K source scaled to the same width:

| Set | Setting | SSIM | PSNR |
|---|---|---|---|
| desktop | 1920px, crf 30 | 0.972 | 38.9 dB |
| mobile | 1170px, crf 34 | 0.959 | 36.1 dB |

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

Add `?debug` to the address to see the real redraw and picture rates on any
machine.

## Launch plumbing

| File | What it is for |
|---|---|
| `robots.txt` | lets search engines crawl everything and points them to the sitemap |
| `sitemap.xml` | the three public pages; bump `<lastmod>` when a page changes materially |
| `404.html` | GitHub Pages serves it for any missing address, on either host |
| `favicon.ico`, `favicon.svg`, `apple-touch-icon.png` | browser tab, bookmarks, iPhone home screen |
| JSON-LD in `index.html` | tells Google this is a real estate agent: phone, area, languages. Keep in step with `config.js` |

**No cookie banner, on purpose.** The site sets no cookies and stores nothing in
the visitor's browser; fonts are self-hosted, social links are plain links, and
Cloudflare Web Analytics is cookieless. A banner would be asking consent for
nothing. If you ever add Google Analytics, a Facebook pixel, or an embedded map
or video, that changes — add consent at the same time.

## Regenerating assets

```bash
tools/vendor-deps.sh        # three.js (tree-shaken, minified) + the two typefaces
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
