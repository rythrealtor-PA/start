#!/usr/bin/env bash
# Encode the hero clip as a video built for scroll-scrubbing (laptops and
# desktops; phones use the still frames from extract-frames.sh).
#
# Encoded for seeking, not for playback:
#   -bf 0   no B-frames, so every frame decodes from the ones before it only
#   -g 3    a keyframe every 3 frames, so any seek — forward or backward —
#           decodes at most 3 frames (2 on average). Measured at crf 22:
#             -g 6  17.2MB  SSIM 0.980   (3.5 frames decoded per seek)
#             -g 3  23.1MB  SSIM 0.981   (2)
#             -g 1  26.5MB  SSIM 0.954   (1, but x264 starves intra-only)
#           Seek cost is what limits the scrub's frame rate, so -g 3 it is.
# Profile High, level 4.0 = the "avc1.640028" that video-sequence.js asks the
# browser about; keep the two in step.
# H.264 because it is hardware-decoded on effectively every laptop and desktop
# (Chrome, Edge, Safari and Firefox alike). Browsers that cannot play it fall
# back to the still frames automatically.
#
# Usage: tools/encode-hero-video.sh path/to/source.mp4 [crf]
set -euo pipefail

SRC="${1:?usage: encode-hero-video.sh <source.mp4> [crf]}"
CRF="${2:-22}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/assets/video"
mkdir -p "$OUT"

# Same width as the desktop stills, so the first still (shown while the video
# downloads) and the video line up exactly.
ffmpeg -hide_banner -loglevel error -y -i "$SRC" \
  -vf "scale=1920:-2:flags=lanczos" \
  -c:v libx264 -preset slow -crf "$CRF" -g 3 -bf 0 \
  -profile:v high -level:v 4.0 -pix_fmt yuv420p -movflags +faststart -an \
  "$OUT/hero-1920.mp4"

ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=width,height,nb_read_frames -of csv=p=0 "$OUT/hero-1920.mp4"
du -h "$OUT/hero-1920.mp4"
echo "If the frame count changed, update FRAME_COUNT in assets/js/frames.js."
