#!/bin/sh

if ! command -v apt >/dev/null 2>&1; then
  exit 0
fi

sudo apt update
sudo apt install -y unzip zsh

# Dependencies for asdf
sudo apt install -y curl git
