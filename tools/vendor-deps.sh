#!/usr/bin/env bash
# Fetch the two runtime dependencies into the repo so the site has no external
# network dependency at all: three.js from npm, and the two OFL typefaces from
# Google Fonts. Both are committed — the site is meant to deploy with no build
# step, and public CDNs are unreachable from some networks anyway.
#
# Usage: tools/vendor-deps.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
THREE_VERSION="0.186.0"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "three.js $THREE_VERSION"
(cd "$tmp" && npm pack "three@$THREE_VERSION" --silent >/dev/null)
tar xzf "$tmp"/three-*.tgz -C "$tmp" package/build/three.module.js package/build/three.core.js package/LICENSE
mkdir -p "$ROOT/assets/vendor"
cp "$tmp/package/build/three.module.js" "$ROOT/assets/vendor/three.module.js"
cp "$tmp/package/build/three.core.js"   "$ROOT/assets/vendor/three.core.js"
cp "$tmp/package/LICENSE"               "$ROOT/assets/vendor/THREE-LICENSE.txt"

# Fraunces carries an optical-size axis, so display sizes get the chiselled,
# high-contrast cut while small sizes stay readable — one variable file covers both.
declare -A FAMILIES=(
  ["fraunces"]="Fraunces:opsz,wght@9..144,300..700"
  ["archivo"]="Archivo:wght@400..700"
)

mkdir -p "$ROOT/assets/fonts"
: > "$ROOT/assets/fonts/fonts.css"

for slug in fraunces archivo; do
  spec="${FAMILIES[$slug]}"
  echo "font: $spec"

  python3 "$ROOT/tools/fetch-font.py" "$slug" "$spec" "$ROOT/assets/fonts"
done

curl -fsS -o "$ROOT/assets/fonts/OFL.txt" \
  "https://raw.githubusercontent.com/google/fonts/main/ofl/archivo/OFL.txt" \
  || echo "note: fetch OFL.txt manually from github.com/google/fonts"

echo "done"
