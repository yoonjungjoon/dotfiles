"""Test font installation with real ZIP extraction and checksum verification."""
import hashlib
import re
import shutil
import zipfile

from test_installers import InstallerHarness, SCRIPTS

VARIANTS = ("Thin", "ThinItalic", "ExtraLight", "ExtraLightItalic", "Light",
            "LightItalic", "Regular", "Italic", "Medium", "MediumItalic",
            "SemiBold", "SemiBoldItalic", "Bold", "BoldItalic", "ExtraBold",
            "ExtraBoldItalic")


class FontInstallerTests(InstallerHarness):
    def setUp(self):
        super().setUp()
        self.archive = self.root / "font-fixture.zip"
        self.script = self.root / "install-fonts.sh"
        self.env["MOCK_FONT_ARCHIVE"] = str(self.archive)
        for command in ("unzip", "shasum", "sha256sum"):
            executable = shutil.which(command)
            if executable:
                (self.bin / command).symlink_to(executable)
        self.make_archive()

    def make_archive(self, variants=VARIANTS):
        with zipfile.ZipFile(self.archive, "w") as archive:
            for variant in variants:
                archive.writestr(f"ttf/Jetendard-{variant}.ttf", f"font fixture: {variant}")
            archive.writestr("__MACOSX/ttf/._Jetendard-Regular.ttf", "metadata")
        # Pin the test fixture digest while exercising the real verifier.
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        source = (SCRIPTS / "run_before_15_install_jetendard.sh").read_text()
        source = re.sub(r"^archive_sha256=[0-9a-f]+$", f"archive_sha256={digest}",
                        source, flags=re.MULTILINE)
        self.script.write_text(source)

    @property
    def linux_fonts(self):
        return self.home / ".local/share/fonts/Jetendard"

    def test_linux_install_is_idempotent_and_repairs_missing_fonts(self):
        self.assert_success(self.run_script(self.script))
        self.assertEqual(len(list(self.linux_fonts.glob("*.ttf"))), 16)
        self.assertIn(["fc-cache", "-f", str(self.linux_fonts)], self.commands())
        self.assertTrue((self.linux_fonts / ".dotfiles-release").is_file())
        self.assertFalse(any(self.home.rglob("__MACOSX")))
        self.log.unlink()
        self.assert_success(self.run_script(self.script))
        self.assertEqual(self.commands(), [["uname", "-s"]])
        (self.linux_fonts / "Jetendard-Bold.ttf").unlink()
        self.assert_success(self.run_script(self.script))
        self.assertTrue((self.linux_fonts / "Jetendard-Bold.ttf").is_file())

    def test_macos_uses_user_fonts_without_package_manager_or_cache(self):
        # Exercise the macOS shasum fallback even on Linux CI.
        (self.bin / "sha256sum").unlink(missing_ok=True)
        self.assert_success(self.run_script(self.script, MOCK_OS="Darwin"))
        fonts = self.home / "Library/Fonts/Jetendard"
        self.assertEqual(len(list(fonts.glob("*.ttf"))), 16)
        self.assertFalse(any(call[0] in ("fc-cache", "apt-get", "brew", "sudo")
                             for call in self.commands()))

    def test_linux_honors_xdg_data_home_with_spaces(self):
        data = self.home / "custom data"
        self.assert_success(self.run_script(self.script, XDG_DATA_HOME=str(data)))
        self.assertTrue((data / "fonts/Jetendard/Jetendard-Regular.ttf").exists())
        self.assertFalse(self.linux_fonts.exists())

    def test_linux_installs_missing_fontconfig_with_apt(self):
        (self.bin / "fc-cache").unlink()
        self.assert_success(self.run_script(self.script))
        self.assertIn(["sudo", "apt-get", "install", "-y", "fontconfig"], self.commands())
        self.assertIn(["fc-cache", "-f", str(self.linux_fonts)], self.commands())

    def test_linux_root_installs_fontconfig_without_sudo(self):
        (self.bin / "fc-cache").unlink()
        self.assert_success(self.run_script(self.script, MOCK_UID="0"))
        self.assertIn(["apt-get", "install", "-y", "fontconfig"], self.commands())
        self.assertFalse(any(call[0] == "sudo" for call in self.commands()))

    def test_checksum_failure_preserves_existing_fonts(self):
        self.assert_success(self.run_script(self.script))
        original = (self.linux_fonts / "Jetendard-Regular.ttf").read_bytes()
        marker = self.linux_fonts / ".dotfiles-release"
        marker.unlink()
        self.archive.write_bytes(b"corrupted download")
        result = self.run_script(self.script)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertEqual((self.linux_fonts / "Jetendard-Regular.ttf").read_bytes(), original)
        self.assertFalse(marker.exists())

    def test_incomplete_archive_does_not_install_partial_family(self):
        self.make_archive(variants=("Regular",))
        result = self.run_script(self.script)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive is missing", result.stderr)
        self.assertFalse(self.linux_fonts.exists())

    def test_download_failure_does_not_install_fonts(self):
        result = self.run_script(self.script, MOCK_DOWNLOAD_FAIL="1")
        self.assertEqual(result.returncode, 22)
        self.assertFalse(self.linux_fonts.exists())

    def test_cache_failure_is_retried_on_next_apply(self):
        result = self.run_script(self.script, MOCK_FONT_CACHE_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.linux_fonts / ".dotfiles-release").exists())
        self.assert_success(self.run_script(self.script))
        self.assertTrue((self.linux_fonts / ".dotfiles-release").is_file())

    def test_font_opt_out_is_noop_and_can_install_later(self):
        self.assert_success(self.run_script(self.script, DOTFILES_INSTALL_FONTS="0"))
        self.assertEqual(self.commands(), [])
        self.assert_success(self.run_script(self.script))
