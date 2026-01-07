#!/bin/sh

brew_bin=""
if command -v brew >/dev/null 2>&1; then
  brew_bin="$(command -v brew)"
elif [ -x /opt/homebrew/bin/brew ]; then
  brew_bin="/opt/homebrew/bin/brew"
elif [ -x /usr/local/bin/brew ]; then
  brew_bin="/usr/local/bin/brew"
elif [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
  brew_bin="/home/linuxbrew/.linuxbrew/bin/brew"
fi

if [ -z "$brew_bin" ]; then
  exit 0
fi

if [ "$(uname -s)" = "Darwin" ]; then
  if [ -d "/Applications/Alacritty.app" ] || [ -d "$HOME/Applications/Alacritty.app" ]; then
    exit 0
  fi
  if ! "$brew_bin" list --cask alacritty >/dev/null 2>&1; then
    HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" install --cask alacritty
  fi
else
  if ! "$brew_bin" list --formula alacritty >/dev/null 2>&1; then
    HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" install alacritty
  fi
fi
