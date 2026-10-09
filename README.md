# Dotfiles

Chezmoi-managed Zsh configuration for macOS and Ubuntu.

## Install the candidate branch

```sh
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- \
  init --apply --branch feat/candidate-2026-01 yoonjungjoon
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
chezmoi git -- switch --track origin/feat/candidate-2026-01
chezmoi diff
chezmoi apply
```

If the branch already exists locally, use `chezmoi git -- switch feat/candidate-2026-01`.
Open a new terminal after applying so the old asdf/direnv environment is not inherited.
Ghostty starts Zsh; other terminals still use the account's configured login shell.

On a headless server, skip the graphical terminal installation:

```sh
DOTFILES_INSTALL_GHOSTTY=0 chezmoi apply
```

Set this variable on each apply on that server. The Ghostty installer checks on
every apply, so a later apply without the variable can install it.

## Managed components

| Component | Purpose / installation |
| --- | --- |
| Zsh + Oh My Zsh | Shell, Git aliases; Oh My Zsh fetched by chezmoi |
| Starship | Prompt; Homebrew on macOS, official installer on Linux |
| mise | Runtime versions and directory environment changes; Homebrew / official installer |
| fzf + fzf-tab | Tab completion selection; fzf from Homebrew / apt, plugin from chezmoi |
| zsh-completions | Extra completion definitions, registered before Oh My Zsh runs `compinit` |
| zsh-autosuggestions | History-based suggestions, loaded after fzf-tab |
| zsh-syntax-highlighting | The only highlighter, loaded last in `.zshrc` |
| Ghostty | Terminal; Homebrew cask / apt |
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

Edit `chezmoi/dot_config/starship.toml` for the prompt and
`chezmoi/dot_config/ghostty/config.tmpl` for the terminal. Ghostty preserves the
previous 13-point font, 0.8 opacity, padding and editing shortcuts, including
Shift+Enter. Install `JetBrainsMonoHangul Nerd Font Mono` separately for the
preferred font; Ghostty uses its bundled fallback when that font is unavailable.
The OS-specific line editing shortcuts use Command on macOS and Control on Linux.

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
