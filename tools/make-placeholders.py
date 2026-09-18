#!/usr/bin/env python3
"""Generate the placeholder artwork used until real photos are dropped in.

These are SVG rather than fetched stock images: the site has no external
dependencies, and a generated placeholder is unmistakably a placeholder — it
cannot be shipped by accident thinking it is a real photo.

Each listing gets a different roofline so the six cards read as six properties
while the layout is being reviewed.

Usage: tools/make-placeholders.py
"""
import os

SLATE, SLATE_2, BLUESTONE, BRASS, IVORY = (
    "#12171C", "#191F26", "#2C3E4A", "#B08D57", "#F2EEE7",
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LISTINGS_DIR = os.path.join(ROOT, "assets", "img", "listings")

# (roof outline, extra detail) per listing — varied silhouettes so the cards
# do not look like six copies of one card.
HOUSES = [
    # gable with dormer
    ("M60,190 L60,120 L160,55 L260,120 L260,190 Z",
     "M120,105 L120,78 L146,58 L172,78 L172,105 Z"),
    # broad hip roof
    ("M50,190 L50,128 L160,62 L270,128 L270,190 Z",
     "M104,190 L104,140 L216,140 L216,190 Z"),
    # rowhouse / flat front
    ("M78,190 L78,72 L242,72 L242,190 Z",
     "M78,72 L160,44 L242,72"),
    # farmhouse with wing
    ("M70,190 L70,112 L154,56 L238,112 L238,190 Z",
     "M238,190 L238,140 L286,140 L286,190 Z"),
    # steep A-frame
    ("M66,190 L160,48 L254,190 Z",
     "M126,190 L126,142 L194,142 L194,190 Z"),
    # duplex / twin
    ("M46,190 L46,118 L116,66 L186,118 L186,190 Z",
     "M186,190 L186,118 L246,74 L296,118 L296,190 Z"),
]


def svg(index: int, roof: str, detail: str) -> str:
    gid = f"g{index}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240"
     width="320" height="240" role="img"
     aria-label="Placeholder image for listing {index}">
  <defs>
    <linearGradient id="{gid}" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{BLUESTONE}"/>
      <stop offset="1" stop-color="{SLATE}"/>
    </linearGradient>
  </defs>
  <rect width="320" height="240" fill="url(#{gid})"/>
  <!-- horizon -->
  <path d="M0,190 H320" stroke="{BRASS}" stroke-opacity="0.35" stroke-width="1"/>
  <!-- house silhouette -->
  <path d="{roof}" fill="{SLATE_2}" fill-opacity="0.75"
        stroke="{BRASS}" stroke-opacity="0.5" stroke-width="1.5"
        stroke-linejoin="round"/>
  <path d="{detail}" fill="none"
        stroke="{BRASS}" stroke-opacity="0.4" stroke-width="1.25"
        stroke-linejoin="round"/>
  <text x="160" y="222" text-anchor="middle"
        font-family="Archivo, system-ui, sans-serif" font-size="9"
        letter-spacing="2.4" fill="{IVORY}" fill-opacity="0.42">
    PLACEHOLDER — ADD PHOTO
  </text>
</svg>
"""


def portrait() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 400"
     width="320" height="400" role="img" aria-label="Placeholder portrait">
  <defs>
    <linearGradient id="p" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0" stop-color="{BLUESTONE}"/>
      <stop offset="1" stop-color="{SLATE}"/>
    </linearGradient>
  </defs>
  <rect width="320" height="400" fill="url(#p)"/>
  <circle cx="160" cy="158" r="52" fill="none"
          stroke="{BRASS}" stroke-opacity="0.45" stroke-width="1.5"/>
  <path d="M74,320 c0,-52 38,-88 86,-88 c48,0 86,36 86,88" fill="none"
        stroke="{BRASS}" stroke-opacity="0.45" stroke-width="1.5"/>
  <text x="160" y="372" text-anchor="middle"
        font-family="Archivo, system-ui, sans-serif" font-size="10"
        letter-spacing="2.6" fill="{IVORY}" fill-opacity="0.42">
    PLACEHOLDER — ADD HEADSHOT
  </text>
</svg>
"""


def main() -> None:
    os.makedirs(LISTINGS_DIR, exist_ok=True)
    for i, (roof, detail) in enumerate(HOUSES, start=1):
        path = os.path.join(LISTINGS_DIR, f"placeholder-{i}.svg")
        with open(path, "w") as f:
            f.write(svg(i, roof, detail))
        print(f"  {os.path.relpath(path, ROOT)}")

    path = os.path.join(ROOT, "assets", "img", "portrait-placeholder.svg")
    with open(path, "w") as f:
        f.write(portrait())
    print(f"  {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
