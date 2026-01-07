#!/bin/sh

brew_bin=""
if command -v brew >/dev/null 2>&1; then
  brew_bin="$(command -v brew)"
elif [ -x /opt/homebrew/bin/brew ]; then
  brew_bin="/opt/homebrew/bin/brew"
elif [ -x /usr/local/bin/brew ]; then
  brew_bin="/usr/local/bin/brew"
fi

if [ -z "$brew_bin" ]; then
  exit 0
fi

packages=""
for pkg in git unzip; do
  if ! command -v "$pkg" >/dev/null 2>&1; then
    packages="$packages $pkg"
  fi
done

if [ -n "$packages" ]; then
  HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" install $packages
fi
