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

# three.js ships ~2.1MB of unminified ES modules, of which the hero uses eleven
# classes. esbuild bundles just those (tree-shaken, minified) into one ~520KB file
# — about 130KB over the wire once the host gzips it. If stage.js starts using
# another THREE class, add it to the export list below and re-run.
echo "three.js $THREE_VERSION (tree-shaken)"
(cd "$tmp" && npm init -y >/dev/null && npm install --silent "three@$THREE_VERSION" "esbuild@0.24.2")
cat > "$tmp/entry.js" <<'JS'
export {
  Color, LinearFilter, Mesh, OrthographicCamera, PlaneGeometry,
  SRGBColorSpace, Scene, ShaderMaterial, Texture, Vector2, WebGLRenderer,
} from 'three';
JS
mkdir -p "$ROOT/assets/vendor"
(cd "$tmp" && npx esbuild entry.js --bundle --minify --format=esm \
  --legal-comments=inline --outfile="$ROOT/assets/vendor/three.min.js" --log-level=warning)
cp "$tmp/node_modules/three/LICENSE" "$ROOT/assets/vendor/THREE-LICENSE.txt"

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
