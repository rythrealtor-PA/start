#!/usr/bin/env python3
"""Download one Google Fonts family for self-hosting, and append its @font-face
rules — rewritten to local paths — to assets/fonts/fonts.css.

Only the latin and latin-ext subsets are kept. Emitting rules for the subsets we
do not download (cyrillic, greek, vietnamese) would leave 404s in the stylesheet.
latin-ext is not optional: the site is bilingual and Spanish needs the accented
forms.

Usage: fetch-font.py <slug> <family-spec> <out-dir>
       fetch-font.py archivo 'Archivo:wght@400..700' assets/fonts
"""
import os
import re
import sys
import urllib.request

KEEP = ("latin", "latin-ext")

# Google Fonts serves woff2 only to user agents it knows support it.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main() -> int:
    slug, spec, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)

    css = get(f"https://fonts.googleapis.com/css2?family={spec}&display=swap").decode()
    blocks = re.findall(r"/\* (\S+) \*/\s*(@font-face \{.*?\})", css, re.S)
    if not blocks:
        print(f"  no @font-face blocks parsed for {spec}", file=sys.stderr)
        return 1

    rules = []
    for subset, block in blocks:
        if subset not in KEEP:
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        name = f"{slug}-{subset}.woff2"
        path = os.path.join(outdir, name)
        with open(path, "wb") as f:
            f.write(get(url))
        print(f"  {name} ({os.path.getsize(path)} bytes)", file=sys.stderr)
        rules.append(re.sub(r"url\(https://[^)]+\)", f"url('./{name}')", block))

    with open(os.path.join(outdir, "fonts.css"), "a") as f:
        f.write("\n".join(rules) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
