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
                     "title-coding.svg"]:
            self.assertIn(name, self.cards)
        self.assertEqual(sum(n.startswith("repo-") for n in self.cards), 3)
        for name in ["link-portfolio.svg", "link-linkedin.svg", "link-devfolio.svg", "link-email.svg"]:
            self.assertIn(name, self.cards)

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
        # Strip GitHub's #gh-light-mode-only / #gh-dark-mode-only theme fragments.
        refs = re.findall(r'(?:src|srcset)="\./cards/([^"#]+)', README.read_text(encoding="utf-8"))
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


class ReadmeLayout(unittest.TestCase):
    def test_title_is_theme_independent(self):
        # One title card with its own background, no light/dark variants: those break when
        # a browser extension darkens a light-mode GitHub page.
        body = re.sub(r"<!--.*?-->", "", README.read_text(encoding="utf-8"), flags=re.S)
        self.assertIn('src="./cards/title-coding.svg"', body)
        self.assertNotIn("<picture>", body)
        self.assertNotIn("mode-only", body)

    def test_title_card_has_background(self):
        render(static=True)
        try:
            src = (CARDS / "title-coding.svg").read_text(encoding="utf-8")
            self.assertRegex(src, r'<rect x="\.5" y="\.5"[^>]*fill="#f3f3f1"')
        finally:
            render(static=False)


class WeeklyActivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(RENDER.parent))
        from render_readme_cards import weekly_totals
        cls.weekly_totals = staticmethod(weekly_totals)

    def test_groups_by_sunday_week_and_keeps_last_n(self):
        # 2026-01-04 is a Sunday. Three full weeks with 1, 2 and 3 contributions per day.
        from datetime import date, timedelta
        start = date(2026, 1, 4)
        days = [{"date": (start + timedelta(i)).isoformat(), "weekday": i % 7, "count": i // 7 + 1}
                for i in range(21)]
        weeks = self.weekly_totals(days, n=2)
        self.assertEqual([w["count"] for w in weeks], [14, 21])
        self.assertEqual(weeks[0]["start"], "2026-01-11")


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
