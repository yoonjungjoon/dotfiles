{{- if and (eq .chezmoi.os "linux") (eq .chezmoi.osRelease.id "ubuntu") -}}
#!/bin/bash

# Install/upgrade asdf
if [[ ! $(command -v asdf) ]]; then
  git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
  source $HOME/.asdf/asdf.sh
else
  asdf update
fi
{{ end -}}
