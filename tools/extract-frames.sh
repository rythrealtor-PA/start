#!/usr/bin/env bash
# Decode the hero clip into the still sequences the scroll stage scrubs through.
#
# Why stills and not a <video>: scrubbing video.currentTime is unreliable — seeks
# snap to keyframes, reverse playback stutters, and iOS Safari throttles it.
# With a still sequence, playing in reverse is just a decreasing array index.
#
# Three sets are produced, and a visitor downloads exactly one:
#   desktop/   1440px AVIF   wide viewports on browsers with AVIF
#   mobile/     900px AVIF   narrow viewports on browsers with AVIF
#   fallback/   900px WebP   anything without AVIF (Safari < 16.4, old Android)
#
# The fallback is deliberately the 900px set rather than a second 1440px one:
# AVIF covers ~95% of browsers, and a full-size WebP twin would have added ~15MB
# to the repo to serve a slightly sharper image to the remaining few percent —
# who are on older, slower devices anyway.
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
OUT="$(cd "$(dirname "$0")/.." && pwd)/assets/frames"

# Widths are deliberate: the canvas is cover-fit and always in motion under a
# vignette and grain, so 1440px upscaled to a 1920px viewport is indistinguishable.
DESKTOP_W=1440
MOBILE_W=900

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
    -pix_fmt yuv420p -c:v libaom-av1 -crf "$3" -cpu-used 6 -still-picture 1 \
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
build_avif_set "$DESKTOP_W" 44 "$OUT/desktop"

echo "mobile/ (${MOBILE_W}px AVIF) ..."
build_avif_set "$MOBILE_W" 46 "$OUT/mobile"

# WebP through image2 is fine — the muxer problem above is AVIF-specific.
echo "fallback/ (${MOBILE_W}px WebP) ..."
ffmpeg -hide_banner -loglevel error -i "$SRC" \
  -vf "scale=$MOBILE_W:-2:flags=lanczos" \
  -c:v libwebp -quality 40 -compression_level 6 -preset photo \
  -start_number 1 "$OUT/fallback/f_%03d.webp"

echo
for d in desktop mobile fallback; do
  printf '%-10s %4s frames  %6s\n' "$d" \
    "$(find "$OUT/$d" -type f | wc -l)" "$(du -sh "$OUT/$d" | cut -f1)"
done
