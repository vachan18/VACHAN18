"""Checks that the rendered cards are safe and valid for GitHub's <img> sandbox."""
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "scripts" / "render_readme_cards.py"
CARDS = ROOT / "cards"
README = ROOT / "README.md"


def render(static: bool) -> None:
    env = {**os.environ, "STATIC": "1" if static else "0"}
    subprocess.run([sys.executable, str(RENDER)], check=True, env=env, capture_output=True)


class RenderedCards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        render(static=False)
        cls.cards = {p.name: p.read_text(encoding="utf-8") for p in CARDS.glob("*.svg")}

    @classmethod
    def tearDownClass(cls):
        render(static=False)  # leave the animated versions on disk

    def test_cards_exist(self):
        for name in ["hero.svg", "heatmap.svg", "activity.svg", "portfolio.svg", "ai.svg", "prs.svg",
                     "linkedin.svg",
                     "title-coding-light.svg", "title-coding-dark.svg"]:
            self.assertIn(name, self.cards)
        self.assertEqual(sum(n.startswith("repo-") for n in self.cards), 3)

    def test_valid_xml_with_accessible_label(self):
        for name, src in self.cards.items():
            root = ET.fromstring(src)
            self.assertEqual(root.get("role"), "img", name)
            self.assertTrue(root.get("aria-label"), name)

    def test_nothing_the_img_sandbox_blocks(self):
        for name, src in self.cards.items():
            self.assertNotIn("<script", src, name)
            self.assertNotIn("foreignObject", src, name)
            self.assertIsNone(re.search(r'(?:href|src)\s*=\s*"https?:', src), name)
            self.assertIsNone(re.search(r"url\((?!data:|#)", src), name)

    def test_size_budget(self):
        for name, src in self.cards.items():
            self.assertLess(len(src.encode()), 150_000, name)

    def test_readme_references_existing_cards(self):
        refs = re.findall(r'(?:src|srcset)="\./cards/([^"]+)"', README.read_text(encoding="utf-8"))
        self.assertTrue(refs)
        for ref in refs:
            self.assertIn(ref, self.cards, f"README points at missing card {ref}")

    def test_static_mode_disables_animation(self):
        render(static=True)
        for p in CARDS.glob("*.svg"):
            src = p.read_text(encoding="utf-8")
            self.assertIn("*{animation:none!important}", src, p.name)
            self.assertNotIn("<set ", src, p.name)
            self.assertNotIn("<animateTransform", src, p.name)


class PrTileLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(RENDER.parent))
        from render_readme_cards import pr_tile
        cls.pr_tile = staticmethod(pr_tile)

    def test_no_open_source_yet(self):
        value, unit, line = self.pr_tile({"merged": 144, "repos": 5, "external_merged": 0})
        self.assertEqual((value, unit, line), (144, "PRs merged", "across 5 repos"))
        self.assertNotIn("open-source", line)

    def test_some_open_source(self):
        value, _, line = self.pr_tile({"merged": 150, "repos": 7, "external_merged": 2})
        self.assertEqual(value, 150)
        self.assertIn("· 2 open-source", line)

    def test_open_source_takes_headline(self):
        value, unit, line = self.pr_tile({"merged": 160, "repos": 9, "external_merged": 7, "external_orgs": 3})
        self.assertEqual(value, 7)
        self.assertIn("open-source", unit)
        self.assertIn("160", line)

    def test_missing_data(self):
        self.assertEqual(self.pr_tile({})[0], 0)


if __name__ == "__main__":
    unittest.main()
