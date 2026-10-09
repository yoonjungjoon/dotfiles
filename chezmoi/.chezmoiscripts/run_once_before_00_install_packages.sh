#!/bin/bash
set -euo pipefail

as_root() {
  if [[ $(id -u) == 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

case "$(uname -s)" in
  Darwin)
    # A newly installed Homebrew may not be on PATH yet.
    if ! command -v brew >/dev/null 2>&1; then
      if [[ -x /opt/homebrew/bin/brew ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
      elif [[ -x /usr/local/bin/brew ]]; then
        export PATH="/usr/local/bin:$PATH"
      else
        installer=$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)
        NONINTERACTIVE=1 /bin/bash -c "$installer"
        if [[ -x /opt/homebrew/bin/brew ]]; then
          export PATH="/opt/homebrew/bin:$PATH"
        else
          export PATH="/usr/local/bin:$PATH"
        fi
      fi
    fi
    packages=()
    for package in git unzip zsh mise starship fzf zellij; do
      if ! brew list --formula "$package" >/dev/null 2>&1; then
        packages+=("$package")
      fi
    done
    if (( ${#packages[@]} )); then
      HOMEBREW_NO_AUTO_UPDATE=1 brew install "${packages[@]}"
    fi
    ;;
  Linux)
    if ! command -v apt-get >/dev/null 2>&1; then
      echo "Automatic Linux installation requires Ubuntu/Debian (apt-get)." >&2
      exit 1
    fi
    as_root apt-get update
    as_root apt-get install -y ca-certificates curl git unzip zsh fzf

    export PATH="$HOME/.local/bin:$PATH"
    mkdir -p "$HOME/.local/bin"
    temporary_dir=$(mktemp -d)
    trap 'rm -rf "$temporary_dir"' EXIT

    if ! command -v mise >/dev/null 2>&1; then
      curl -fsSL https://mise.run -o "$temporary_dir/mise-install.sh"
      MISE_INSTALL_PATH="$HOME/.local/bin/mise" sh "$temporary_dir/mise-install.sh"
    fi
    if ! command -v starship >/dev/null 2>&1; then
      curl -fsSL https://starship.rs/install.sh -o "$temporary_dir/starship-install.sh"
      sh "$temporary_dir/starship-install.sh" --yes --bin-dir "$HOME/.local/bin"
    fi
    if ! command -v zellij >/dev/null 2>&1; then
      case "$(uname -m)" in
        x86_64) architecture=x86_64 ;;
        aarch64|arm64) architecture=aarch64 ;;
        *) echo "Unsupported Zellij architecture: $(uname -m)" >&2; exit 1 ;;
      esac
      curl -fsSL "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${architecture}-unknown-linux-musl.tar.gz" \
        -o "$temporary_dir/zellij.tar.gz"
      tar -xzf "$temporary_dir/zellij.tar.gz" -C "$temporary_dir" zellij
      install -m 755 "$temporary_dir/zellij" "$HOME/.local/bin/zellij"
    fi
    ;;
  *)
    echo "Automatic installation supports macOS and Ubuntu/Debian." >&2
    exit 1
    ;;
esac
