#!/usr/bin/env bash
# Decode the hero clip into the still sequences the scroll stage scrubs through.
#
# Why stills and not a <video>: scrubbing video.currentTime is unreliable — seeks
# snap to keyframes, reverse playback stutters, and iOS Safari throttles it.
# With a still sequence, playing in reverse is just a decreasing array index.
#
# Three sets are produced, and a visitor downloads exactly one:
#   desktop/   1920px AVIF   wide viewports on browsers with AVIF
#   mobile/    1170px AVIF   narrow viewports on browsers with AVIF
#   fallback/  1000px WebP   anything without AVIF (Safari < 16.4, old Android)
#
# The fallback is deliberately smaller than the desktop set: AVIF covers ~95%
# of browsers, and a full-size WebP twin would add ~30MB to the repo to serve a
# slightly sharper image to the remaining few percent — who are on older,
# slower devices anyway.
#
# TWO ENCODER GOTCHAS, both found the hard way by loading the output in Chrome:
#
#   1. AVIF must go through `-f avif`, one file per call. Writing a numbered
#      sequence with `-f image2` produces files that `file` and ffprobe happily
#      call AVIF but that Chromium refuses to decode. Hence the PNG intermediate
#      and the per-frame encode loop below.
#   2. Without an explicit `-pix_fmt yuv420p`, libaom picks gbrp (planar RGB),
#      which decodes but is roughly twice the size for no visible gain.
#
# Usage: tools/extract-frames.sh path/to/source.mp4
set -euo pipefail

SRC="${1:?usage: extract-frames.sh <source.mp4>}"
# OUT can be overridden to encode into a staging folder and compare first.
OUT="${OUT:-$(cd "$(dirname "$0")/.." && pwd)/assets/frames}"

# Widths are deliberate. A 390px phone at 3x is 1170 real pixels, so that is the
# phone set's native size; 1920px is a full-HD screen 1:1 and a 1440px laptop
# at 1.33x. Wider was measured and not worth it: 2048px bought +0.16dB for 7%
# more bytes, and every decoded frame held in memory grows with the square.
DESKTOP_W=1920
MOBILE_W=1170
FALLBACK_W=1000

# Quality settings were measured on a 13-frame sample of the 4K source, against
# the source scaled to the same width (so this is compression loss only):
#   desktop 1920px crf 30 -> SSIM 0.972, 38.9 dB, ~150KB/frame
#   mobile  1170px crf 34 -> SSIM 0.959, 36.1 dB,  ~65KB/frame
# -cpu-used 3 (slower, more careful) gains ~0.4dB over 6 at the same size.
#
# Frame count is NOT reducible here. Consecutive frames measure ~18 dB PSNR
# apart, which is substantial motion — dropping every other frame judders.
# If you swap the video, update FRAME_COUNT in assets/js/frames.js to match.

JOBS="$(nproc 2>/dev/null || echo 4)"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

for d in desktop mobile fallback; do
  rm -rf "${OUT:?}/$d"
  mkdir -p "$OUT/$d"
done

# One AVIF encode. Exported so the xargs workers below can call it.
encode_one() {
  ffmpeg -hide_banner -loglevel error -i "$1" \
    -pix_fmt yuv420p -c:v libaom-av1 -crf "$3" -cpu-used 3 -still-picture 1 \
    -f avif -y "$2"
}
export -f encode_one

# <width> <crf> <outdir> — decode to PNG once, then encode frames in parallel.
build_avif_set() {
  local width="$1" crf="$2" dest="$3"
  local stills="$tmp/png_$width"
  mkdir -p "$stills"
  ffmpeg -hide_banner -loglevel error -i "$SRC" \
    -vf "scale=$width:-2:flags=lanczos" -start_number 1 "$stills/f_%03d.png"

  find "$stills" -name '*.png' -print0 \
    | xargs -0 -P "$JOBS" -I{} bash -c \
        'encode_one "$1" "$2/$(basename "${1%.png}").avif" "$3"' _ {} "$dest" "$crf"
}

echo "desktop/ (${DESKTOP_W}px AVIF, ${JOBS} jobs) ..."
build_avif_set "$DESKTOP_W" 30 "$OUT/desktop"

echo "mobile/ (${MOBILE_W}px AVIF) ..."
build_avif_set "$MOBILE_W" 34 "$OUT/mobile"

# WebP through image2 is fine — the muxer problem above is AVIF-specific.
# WebP is far less efficient than AVIF at this content, so the fallback is
# improved but not matched — it serves a few percent of visitors, on older
# devices, and a 16MB WebP set would cost them more than the sharpness is worth.
echo "fallback/ (${FALLBACK_W}px WebP) ..."
ffmpeg -hide_banner -loglevel error -i "$SRC" \
  -vf "scale=$FALLBACK_W:-2:flags=lanczos" \
  -c:v libwebp -quality 55 -compression_level 6 -preset photo \
  -start_number 1 "$OUT/fallback/f_%03d.webp"

echo
for d in desktop mobile fallback; do
  printf '%-10s %4s frames  %6s\n' "$d" \
    "$(find "$OUT/$d" -type f | wc -l)" "$(du -sh "$OUT/$d" | cut -f1)"
done
