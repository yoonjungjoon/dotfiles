"""Exercise installer branches without modifying the host or using the network."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "chezmoi/.chezmoiscripts"
PACKAGES = "run_once_before_00_install_packages.sh"
GHOSTTY = "run_before_10_install_ghostty.sh"

MOCK = r'''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["MOCK_LOG"], "a") as log:
    log.write(json.dumps([name, *args]) + "\n")
if name == "uname":
    print(os.environ.get("MOCK_ARCH", "x86_64") if args == ["-m"] else os.environ.get("MOCK_OS", "Linux"))
elif name == "id":
    print(os.environ.get("MOCK_UID", "1000"))
elif name == "sudo":
    os.execvp(args[0], args)
elif name == "brew" and args[0] == "list":
    sys.exit(0 if args[-1] in os.environ.get("MOCK_INSTALLED", "").split() else 1)
elif name == "dpkg-query":
    print("install ok installed" if os.environ.get("MOCK_GHOSTTY_INSTALLED") else "unknown ok not-installed")
elif name == "apt-cache":
    sys.exit(1 if os.environ.get("MOCK_NO_GHOSTTY") else 0)
elif name == "apt-get":
    sys.exit(23 if os.environ.get("MOCK_APT_FAIL") else 0)
elif name == "curl":
    if os.environ.get("MOCK_DOWNLOAD_FAIL"):
        sys.exit(22)
    output = pathlib.Path(args[args.index("-o") + 1])
    # Simulate installer side effects in the isolated home.
    if "https://mise.run" in args:
        output.write_text('#!/bin/sh\nprintf "#!/bin/sh\\n" > "$MISE_INSTALL_PATH"\nchmod +x "$MISE_INSTALL_PATH"\n')
    elif "https://starship.rs/install.sh" in args:
        output.write_text('#!/bin/sh\nprintf "#!/bin/sh\\n" > "$HOME/.local/bin/starship"\nchmod +x "$HOME/.local/bin/starship"\n')
    else:
        output.touch()
elif name == "tar":
    dest = pathlib.Path(args[args.index("-C") + 1])
    (dest / "zellij").write_text("#!/bin/sh\n")
'''


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.log = self.root / "commands.jsonl"
        self.env = {
            "HOME": str(self.home), "PATH": str(self.bin),
            "MOCK_LOG": str(self.log), "TMPDIR": str(self.root),
        }
        for command in ("uname", "id", "sudo", "brew", "dpkg-query", "apt-cache",
                        "apt-get", "add-apt-repository", "curl", "tar"):
            target = self.bin / command
            target.write_text(f"#!{sys.executable}\n" + MOCK)
            target.chmod(0o755)
        for command in ("sh", "mkdir", "mktemp", "rm", "install", "chmod", "grep"):
            (self.bin / command).symlink_to(shutil.which(command))

    def run_script(self, script, **env):
        return subprocess.run(["/bin/bash", str(SCRIPTS / script)],
                              env={**self.env, **env}, capture_output=True, text=True)

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_linux_installs_tools_in_user_bin_and_uses_apt(self):
        self.assert_success(self.run_script(PACKAGES))
        calls = self.commands()
        self.assertIn(["apt-get", "install", "-y", "ca-certificates", "curl", "git", "unzip", "zsh", "fzf"], calls)
        self.assertFalse(any(call[0] == "brew" for call in calls))
        for tool in ("mise", "starship", "zellij"):
            self.assertTrue(os.access(self.home / ".local/bin" / tool, os.X_OK))
        self.log.unlink()
        self.assert_success(self.run_script(PACKAGES))
        self.assertFalse(any(call[0] == "curl" for call in self.commands()))

    def test_linux_arm64_downloads_correct_zellij_release(self):
        self.assert_success(self.run_script(PACKAGES, MOCK_ARCH="aarch64"))
        self.assertTrue(any("zellij-aarch64-unknown-linux-musl.tar.gz" in " ".join(call)
                            for call in self.commands()))

    def test_linux_root_does_not_use_sudo(self):
        self.assert_success(self.run_script(PACKAGES, MOCK_UID="0"))
        self.assertFalse(any(call[0] == "sudo" for call in self.commands()))

    def test_apt_failure_stops_downloads(self):
        result = self.run_script(PACKAGES, MOCK_APT_FAIL="1")
        self.assertEqual(result.returncode, 23)
        self.assertFalse(any(call[0] == "curl" for call in self.commands()))

    def test_download_failure_does_not_run_partial_installers(self):
        result = self.run_script(PACKAGES, MOCK_DOWNLOAD_FAIL="1")
        self.assertEqual(result.returncode, 22)
        self.assertFalse((self.home / ".local/bin/mise").exists())
        self.assertFalse((self.home / ".local/bin/starship").exists())

    def test_macos_only_installs_missing_formulae(self):
        self.assert_success(self.run_script(PACKAGES, MOCK_OS="Darwin", MOCK_INSTALLED="git unzip zsh zellij"))
        self.assertIn(["brew", "install", "mise", "starship", "fzf"], self.commands())
        self.assertFalse(any(call[0] in ("apt-get", "curl") for call in self.commands()))

    def test_macos_no_install_when_formulae_present(self):
        self.assert_success(self.run_script(PACKAGES, MOCK_OS="Darwin", MOCK_INSTALLED="git unzip zsh mise starship fzf zellij"))
        self.assertFalse(any(call[:2] == ["brew", "install"] for call in self.commands()))

    def test_ghostty_uses_available_apt_package(self):
        self.assert_success(self.run_script(GHOSTTY))
        self.assertIn(["apt-get", "install", "-y", "ghostty"], self.commands())
        self.assertFalse(any(call[0] in ("add-apt-repository", "curl") for call in self.commands()))

    def test_ghostty_installed_package_is_noop(self):
        self.assert_success(self.run_script(GHOSTTY, MOCK_GHOSTTY_INSTALLED="1"))
        self.assertFalse(any(call[0] == "apt-get" for call in self.commands()))

    def test_ghostty_opt_out_is_noop(self):
        self.assert_success(self.run_script(GHOSTTY, DOTFILES_INSTALL_GHOSTTY="0"))
        self.assertEqual(self.commands(), [])

    def test_ubuntu_2404_ppa_fallback(self):
        release = Path("/etc/os-release")
        if release.exists():
            values = dict(line.split("=", 1) for line in release.read_text().splitlines() if "=" in line)
            if values.get("ID", "").strip('"') != "ubuntu" or values.get("VERSION_ID", "").strip('"') != "24.04":
                self.skipTest("PPA fallback requires an Ubuntu 24.04 release fixture")
        # On macOS no /etc/os-release is sourced, so supply the Linux metadata.
        self.assert_success(self.run_script(GHOSTTY, MOCK_NO_GHOSTTY="1", ID="ubuntu", VERSION_ID="24.04"))
        self.assertIn(["add-apt-repository", "-y", "ppa:mkasberg/ghostty-ubuntu"], self.commands())
        self.assertIn(["apt-get", "install", "-y", "ghostty"], self.commands())


if __name__ == "__main__":
    unittest.main()
