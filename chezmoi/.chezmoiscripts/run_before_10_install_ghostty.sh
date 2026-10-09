#!/bin/bash
set -euo pipefail

# Servers can opt out without marking a run_once script as permanently complete.
if [[ ${DOTFILES_INSTALL_GHOSTTY:-1} == 0 ]]; then
  exit 0
fi

as_root() {
  if [[ $(id -u) == 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

case "$(uname -s)" in
  Darwin)
    if [[ -d /Applications/Ghostty.app || -d "$HOME/Applications/Ghostty.app" ]]; then
      exit 0
    fi
    if ! command -v brew >/dev/null 2>&1; then
      if [[ -x /opt/homebrew/bin/brew ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
      elif [[ -x /usr/local/bin/brew ]]; then
        export PATH="/usr/local/bin:$PATH"
      fi
    fi
    if ! brew list --cask ghostty >/dev/null 2>&1; then
      HOMEBREW_NO_AUTO_UPDATE=1 brew install --cask ghostty
    fi
    ;;
  Linux)
    if dpkg-query -W -f='${Status}' ghostty 2>/dev/null | grep -q '^install ok installed$'; then
      exit 0
    fi
    as_root apt-get update
    if ! apt-cache show ghostty >/dev/null 2>&1; then
      # Ubuntu 26.04+ provides Ghostty. Ubuntu 24.04 uses the community PPA
      # maintained by the packager linked from Ghostty's installation docs.
      if [[ -r /etc/os-release ]]; then
        . /etc/os-release
      fi
      if [[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04 ]]; then
        as_root apt-get install -y software-properties-common
        as_root add-apt-repository -y ppa:mkasberg/ghostty-ubuntu
        as_root apt-get update
      else
        echo "No Ghostty apt package is available for this distribution." >&2
        echo "Use Ubuntu 24.04/26.04+, or set DOTFILES_INSTALL_GHOSTTY=0 on servers." >&2
        exit 1
      fi
    fi
    as_root apt-get install -y ghostty
    ;;
  *)
    echo "Automatic Ghostty installation supports macOS and Ubuntu." >&2
    exit 1
    ;;
esac
