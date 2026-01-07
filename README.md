### tl;dr

- to setup these chezmoi dotfiles including my settings, do following command from your ubuntu terminal
- `sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply yoonjungjoon`


- macOS: run the same command from Terminal (Homebrew will be installed if missing)
- oh-my-zsh and plugins are fetched via chezmoi externals during apply (network required)
- macOS: chezmoi will install Homebrew if missing and install git/unzip via brew
