#!/bin/bash
set -euo pipefail

# Check on every apply so opting out on a server does not prevent a later install.
if [[ ${DOTFILES_INSTALL_FONTS:-1} == 0 ]]; then
  exit 0
fi

version=v0.1.0
archive_sha256=399ab416895c01ddc1d43db509d7aa7cede4ad209f597ae8639c6d0194c2b133
variants=(Thin ThinItalic ExtraLight ExtraLightItalic Light LightItalic
  Regular Italic Medium MediumItalic SemiBold SemiBoldItalic Bold BoldItalic
  ExtraBold ExtraBoldItalic)

os=$(uname -s)
case "$os" in
  Darwin) font_dir="$HOME/Library/Fonts/Jetendard" ;;
  Linux) font_dir="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/Jetendard" ;;
  *) echo "Automatic font installation supports macOS and Linux." >&2; exit 1 ;;
esac

marker="$font_dir/.dotfiles-release"
if [[ -f "$marker" && $(<"$marker") == "$version:$archive_sha256" ]]; then
  complete=true
  for variant in "${variants[@]}"; do
    if [[ ! -s "$font_dir/Jetendard-$variant.ttf" ]]; then
      complete=false
      break
    fi
  done
  if [[ "$complete" == true ]]; then
    exit 0
  fi
fi

if [[ "$os" == Linux ]] && ! command -v fc-cache >/dev/null 2>&1; then
  if [[ $(id -u) == 0 ]]; then
    apt-get update
    apt-get install -y fontconfig
  else
    sudo apt-get update
    sudo apt-get install -y fontconfig
  fi
fi

temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT
archive="$temporary_dir/Jetendard-TTF.zip"
curl -fsSL --retry 3 \
  "https://github.com/kuskhan/jetendard/releases/download/$version/Jetendard-TTF.zip" \
  -o "$archive"

if command -v sha256sum >/dev/null 2>&1; then
  actual_sha256=$(sha256sum "$archive")
else
  actual_sha256=$(shasum -a 256 "$archive")
fi
if [[ ${actual_sha256%% *} != "$archive_sha256" ]]; then
  echo "Jetendard archive checksum mismatch; fonts were not installed." >&2
  exit 1
fi

unzip -q "$archive" 'ttf/Jetendard-*.ttf' -d "$temporary_dir"
# Validate the complete family before replacing any previously installed fonts.
for variant in "${variants[@]}"; do
  if [[ ! -s "$temporary_dir/ttf/Jetendard-$variant.ttf" ]]; then
    echo "Jetendard archive is missing $variant." >&2
    exit 1
  fi
done

mkdir -p "$font_dir"
for variant in "${variants[@]}"; do
  install -m 644 "$temporary_dir/ttf/Jetendard-$variant.ttf" "$font_dir/"
done
if [[ "$os" == Linux ]]; then
  fc-cache -f "$font_dir"
fi
printf '%s\n' "$version:$archive_sha256" > "$marker"
