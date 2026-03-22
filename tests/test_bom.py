"""Bill of Materials tests for ClawTasker CEO Console v1.2.0.

These tests verify that every critical file exists and key content is correct.
Run with: python -m pytest tests/test_bom.py -v
"""
import unittest
from pathlib import Path

import server


class BillOfMaterialsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(server.__file__).resolve().parent
        self.version = (self.root / 'VERSION').read_text(encoding='utf-8').strip()
        self.ui_dist = self.root / 'ui' / 'dist'
        self.assets = self.ui_dist / 'assets'

    # ------------------------------------------------------------------
    # Version consistency
    # ------------------------------------------------------------------

    def test_version_file_matches_server_constant(self):
        """VERSION file and server.APP_VERSION must be identical."""
        self.assertEqual(self.version, server.APP_VERSION)

    def test_version_is_1_2_0(self):
        """This release is v1.2.0."""
        self.assertEqual(self.version, '1.2.0')

    # ------------------------------------------------------------------
    # Server configuration
    # ------------------------------------------------------------------

    def test_web_dir_points_to_ui_dist(self):
        """WEB_DIR must point to ui/dist/, NOT web/."""
        expected = self.root / 'ui' / 'dist'
        self.assertEqual(server.WEB_DIR, expected,
                         f"WEB_DIR is {server.WEB_DIR}, expected {expected}")

    # ------------------------------------------------------------------
    # Critical path files
    # ------------------------------------------------------------------

    def test_index_html_exists(self):
        """ui/dist/index.html must exist."""
        self.assertTrue((self.ui_dist / 'index.html').exists())

    def test_index_html_is_substantial(self):
        """ui/dist/index.html must be > 1000 lines (not the gutted 466-line shell)."""
        content = (self.ui_dist / 'index.html').read_text(encoding='utf-8')
        line_count = len(content.splitlines())
        self.assertGreater(line_count, 1000,
                           f"index.html is only {line_count} lines — likely the gutted shell, not the full monolith")

    def test_styles_css_exists(self):
        """ui/dist/assets/styles.css must exist."""
        self.assertTrue((self.assets / 'styles.css').exists())

    def test_logo_svg_exists(self):
        """ui/dist/logo.svg must exist."""
        self.assertTrue((self.ui_dist / 'logo.svg').exists())

    def test_version_file_exists(self):
        """VERSION file must exist."""
        self.assertTrue((self.root / 'VERSION').exists())

    # ------------------------------------------------------------------
    # CSS content checks
    # ------------------------------------------------------------------

    def test_styles_css_has_sprite_avatar_frame(self):
        """styles.css must contain .sprite-avatar-frame class."""
        css = (self.assets / 'styles.css').read_text(encoding='utf-8')
        self.assertIn('sprite-avatar-frame', css)

    def test_styles_css_has_sprite_url_variable(self):
        """styles.css must contain --sprite-url CSS variable."""
        css = (self.assets / 'styles.css').read_text(encoding='utf-8')
        self.assertIn('--sprite-url', css)

    # ------------------------------------------------------------------
    # Portrait assets (14 agents)
    # ------------------------------------------------------------------

    AGENT_NAMES = [
        'ceo', 'charlie', 'codex', 'echo', 'iris', 'ledger',
        'mercury', 'orion', 'pixel', 'quill', 'ralph', 'scout',
        'shield', 'violet'
    ]

    def test_all_portraits_exist(self):
        """All 14 agent portrait PNGs must exist in ui/dist/assets/portraits/."""
        portraits_dir = self.assets / 'portraits'
        for name in self.AGENT_NAMES:
            path = portraits_dir / f'{name}.png'
            self.assertTrue(path.exists(), f"Missing portrait: {path}")

    def test_all_sprites_exist(self):
        """All 14 agent sprite PNGs must exist in ui/dist/assets/sprites/."""
        sprites_dir = self.assets / 'sprites'
        for name in self.AGENT_NAMES:
            path = sprites_dir / f'{name}.png'
            self.assertTrue(path.exists(), f"Missing sprite: {path}")

    # ------------------------------------------------------------------
    # Texture assets
    # ------------------------------------------------------------------

    TEXTURE_NAMES = [
        'board_tile', 'bookshelf', 'chair_front', 'chair_side', 'chair_side_2',
        'leaf_tile', 'office_map_16bit', 'office_map_16bit_thumb', 'office_map_32bit',
        'office_map_day_32bit', 'office_map_night_32bit',
        'office_overlay_32bit', 'office_overlay_day_32bit', 'office_overlay_night_32bit',
        'path_tile', 'rug_green', 'rug_red', 'stone_tile', 'table_round', 'torch',
        'wood_bottom', 'wood_left', 'wood_right'
    ]

    def test_all_textures_exist(self):
        """All texture PNGs must exist in ui/dist/assets/textures/."""
        textures_dir = self.assets / 'textures'
        for name in self.TEXTURE_NAMES:
            path = textures_dir / f'{name}.png'
            self.assertTrue(path.exists(), f"Missing texture: {path}")

    # ------------------------------------------------------------------
    # JavaScript modules
    # ------------------------------------------------------------------

    def test_legacy_bootstrap_exists(self):
        """legacy/bootstrap.js must exist (contains officeSceneMarkup)."""
        path = self.assets / 'legacy' / 'bootstrap.js'
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_bootstrap_has_officeSceneMarkup(self):
        """bootstrap.js must contain officeSceneMarkup function."""
        content = (self.assets / 'legacy' / 'bootstrap.js').read_text(encoding='utf-8')
        self.assertIn('officeSceneMarkup', content)

    def test_main_js_exists(self):
        """main.js must exist."""
        self.assertTrue((self.assets / 'main.js').exists())

    # ------------------------------------------------------------------
    # Vendor assets (Pocket Office Quest v9)
    # ------------------------------------------------------------------

    def test_pocket_office_vendor_dir_exists(self):
        """Pocket Office v9 vendor directory must exist."""
        path = self.assets / 'vendor' / 'pocket-office-quest-v9'
        self.assertTrue(path.exists(), f"Missing vendor dir: {path}")

    def test_pocket_office_has_avatar_sheets(self):
        """Pocket Office v9 must have avatar sprite sheets."""
        avatars_dir = self.assets / 'vendor' / 'pocket-office-quest-v9' / 'assets' / 'avatars'
        self.assertTrue(avatars_dir.exists(), f"Missing avatars dir: {avatars_dir}")
        sheets = list(avatars_dir.glob('*-sheet.png'))
        self.assertGreaterEqual(len(sheets), 10,
                                f"Only {len(sheets)} avatar sheets found, expected >= 10")

    # ------------------------------------------------------------------
    # UI tab coverage in index.html
    # ------------------------------------------------------------------

    REQUIRED_TABS = [
        ('dash', 'Dashboard'),
        ('team', 'Team'),
        ('cal', 'Calendar'),
        ('board', 'Board'),
        ('miss', 'Missions'),
        ('conv', 'Conversations'),
        ('off', 'Office'),
        ('acc', 'Access'),
        ('req', 'Requirements'),
        ('tc', 'Test Cases'),
        ('app', 'Appearance'),
    ]

    def test_all_tabs_have_nav_buttons(self):
        """All 11 tabs must have navigation buttons in index.html."""
        content = (self.ui_dist / 'index.html').read_text(encoding='utf-8')
        for tab_id, tab_name in self.REQUIRED_TABS:
            self.assertIn(f"goV('{tab_id}'",
                          content,
                          f"Missing nav button for tab '{tab_name}' (id={tab_id})")

    def test_all_tabs_have_view_containers(self):
        """All 11 tabs must have view containers (V_xxx divs) in index.html."""
        content = (self.ui_dist / 'index.html').read_text(encoding='utf-8')
        for tab_id, tab_name in self.REQUIRED_TABS:
            self.assertIn(f'id="V_{tab_id}"',
                          content,
                          f"Missing view container for tab '{tab_name}' (id=V_{tab_id})")


if __name__ == '__main__':
    unittest.main()
