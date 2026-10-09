# Dotfiles

Chezmoi-managed Zsh configuration for macOS and Ubuntu.

## Install

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- \
  init --apply yoonjungjoon
```

Network access and package-manager privileges are required. macOS installs Homebrew
if needed. Ubuntu uses **apt, never Snap**. Ghostty uses the configured apt
repositories on Ubuntu 26.04+; on Ubuntu 24.04, if no package is available, the
installer adds the community [mkasberg/ghostty-ubuntu PPA](https://github.com/mkasberg/ghostty-ubuntu).
The PPA is third-party packaging linked by the [Ghostty installation documentation](https://ghostty.org/docs/install/binary).
Other Ubuntu/Debian versions need an existing Ghostty apt package or the server option below.

For an existing chezmoi checkout, commit or stash local changes first:

```sh
chezmoi git -- fetch origin
chezmoi git -- switch main
chezmoi git -- pull --ff-only origin main
chezmoi diff
chezmoi apply
```

Open a new terminal after applying so the old asdf/direnv environment is not inherited.
Ghostty starts Zsh; other terminals still use the account's configured login shell.

On a headless server, skip the graphical terminal and local font installation:

```sh
DOTFILES_INSTALL_GHOSTTY=0 DOTFILES_INSTALL_FONTS=0 chezmoi apply
```

Set these variables on each apply on that server. Both installers check on every
apply, so a later apply without the variables can install them. Fonts are needed
on the machine running your terminal, including when connecting to a remote shell.

## Managed components

| Component | Purpose / installation |
| --- | --- |
| Zsh + Oh My Zsh | Shell, Git aliases; Oh My Zsh fetched by chezmoi |
| Starship | Catppuccin Powerline prompt, Mocha palette; Homebrew / official installer |
| mise | Runtime versions and directory environment changes; Homebrew / official installer |
| fzf + fzf-tab | Tab completion selection; fzf from Homebrew / apt, plugin from chezmoi |
| zsh-completions | Extra completion definitions, registered before Oh My Zsh runs `compinit` |
| zsh-autosuggestions | History-based suggestions, loaded after fzf-tab |
| zsh-syntax-highlighting | The only highlighter, loaded last in `.zshrc` |
| Ghostty | Terminal with Catppuccin Mocha and Jetendard; Homebrew cask / apt |
| Jetendard | Hangul + Nerd Font icons; pinned upstream TTF release, SHA-256 verified |
| Zellij | Session and pane management; Homebrew / official Linux release binary |

Chezmoi refreshes Oh My Zsh and plugin archives weekly when applying. Oh My Zsh's
own updater is disabled because these are archives, not Git checkouts. Linux
installs mise, Starship and Zellij into `~/.local/bin`; `.zshrc` adds it to `PATH`.
The package installer runs once per script revision and stops on errors.

## Runtime versions and project environments

`~/.tool-versions` remains the managed version file and is read by mise directly:

- Python 3.12.15
- Node.js 20.15.0
- Go 1.22.5

Node.js and Go retain their previous versions. Python moves from 3.12.4 to 3.12.15
within the same minor series: the old prebuilt artifact lacks the attestation
required by current mise. Artifact verification stays enabled.
Chezmoi installs these versions after applying files and repeats that
step when this version file changes. mise manages its own runtime installations;
existing asdf installations are not reused or removed.

For project-specific versions or environment variables, add `mise.toml` to the
project, for example:

```toml
[tools]
node = "20.15.0"

[env]
APP_ENV = "development"
# Load a project's .env if needed:
# _.file = ".env"
```

Review the file, then run `mise trust` and `mise install` in the project. The
`mise activate zsh` hook switches tools and variables on directory changes.
The previous home `.envrc` only contained `use asdf`, so no separate direnv hook
is needed. Project `.envrc` shell logic must be migrated separately; mise does not
execute it automatically.

## Prompt and terminal settings

The prompt uses Starship's [Catppuccin Powerline preset](https://starship.rs/presets/catppuccin-powerline)
with `palette = 'catppuccin_mocha'`. It keeps a separate command input line and
shows command durations after two seconds, without desktop notifications. Edit
`chezmoi/dot_config/starship.toml` to customize it; chezmoi deploys the preset as
configuration, so no separate theme installation command is needed.

Both local and SSH sessions show `user@hostname` in the first Powerline segment.
The hostname comes from the system running the shell (up to the first dot), not
the client's SSH alias. Apply these dotfiles on the SSH server to enable this
prompt there.

Ghostty uses `font-family = Jetendard` and its built-in `Catppuccin Mocha` theme.
Edit `chezmoi/dot_config/ghostty/config.tmpl` for terminal settings. The background
is fully opaque (`background-opacity = 1.0`). The previous 13-point size, padding
and editing shortcuts, including Shift+Enter, are retained. The OS-specific line
editing shortcuts use Command on macOS and
Control on Linux. Restart Ghostty after applying to pick up the font and theme.

[Jetendard](https://github.com/kuskhan/jetendard) combines JetBrains Mono Nerd Font
Mono with Pretendard Hangul. Chezmoi installs all 16 TTF styles from the pinned
`v0.1.0` release after verifying its SHA-256 checksum:

- macOS: `~/Library/Fonts/Jetendard`
- Linux: `$XDG_DATA_HOME/fonts/Jetendard`, defaulting to `~/.local/share/fonts/Jetendard`

Linux installs `fontconfig` through apt if necessary and refreshes the font cache.
The installer skips a complete installation of the same release and repairs
missing font files on a later apply. Set `DOTFILES_INSTALL_FONTS=0` to opt out.
The font release and checksum are pinned in
`chezmoi/.chezmoiscripts/run_before_15_install_jetendard.sh`; upgrades are explicit.

Alacritty, Powerlevel10k, asdf, asdf-direnv, fast-syntax-highlighting and
zsh-autocomplete are no longer installed or loaded by this configuration.
Existing applications/runtime directories are left on disk. Previously deployed
`~/.envrc`, `~/.p10k.zsh`, `~/.config/asdf-direnv`, `~/.config/direnv/lib/use_asdf.sh`
and Alacritty configuration may also remain; review any personal changes before
removing them. Neovim and Zellij configuration are unchanged.

## Validation

```sh
python3 -m unittest discover -s tests -v
zsh -n chezmoi/dot_zshrc
```

Installer tests use temporary homes and mocked package managers/downloads; they do
not install software on the test host. Actual template rendering and plugin
startup can be checked with chezmoi against a separate destination, excluding
scripts. A real Ubuntu GUI session is still needed to assess rendering and key feel.
