#!/bin/sh

if command -v brew >/dev/null 2>&1; then
  exit 0
fi

# Install Homebrew (non-interactive to avoid prompt during automation).
NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
