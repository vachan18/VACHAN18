"""Automated unit test suite for VACHAN.EXE Cyberpunk Dashboard Generator.
Validates XML integrity, text sanitization, wrapping, and telemetry parsing.
"""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root and scripts dir to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from generate_dashboard import esc, wrap_text, panel_container, ASSETS_DIR


class TestDashboardGenerator(unittest.TestCase):
    """Test suite for dashboard helper functions and SVG generation integrity."""

    def test_xml_escaping(self):
        """Verify that XML reserved characters are properly escaped."""
        self.assertEqual(esc("Hello & World"), "Hello &amp; World")
        self.assertEqual(esc("<script>alert('xss')</script>"), "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")
        self.assertEqual(esc('Quote "test"'), "Quote &quot;test&quot;")
        self.assertEqual(esc(12345), "12345")
        self.assertEqual(esc(None), "None")

    def test_text_wrapping(self):
        """Verify that long text wraps without splitting individual words incorrectly."""
        text = "Autonomous robot for plant disease detection and precision spraying."
        lines = wrap_text(text, 24)
        self.assertTrue(len(lines) >= 2)
        # Verify no line exceeds reasonable boundary
        for line in lines:
            self.assertTrue(len(line) <= 30)
        # Rejoined words should match original
        rejoined = " ".join(lines)
        self.assertEqual(rejoined, text)

    def test_panel_container_generation(self):
        """Verify that futuristic clipped-corner path containers are generated."""
        container_xml = panel_container(x=10, y=20, w=300, h=200, border="#00E5FF", bg="#060A16", notch=16)
        self.assertIn('<path d="M 26 20', container_xml)
        self.assertIn('stroke="#00E5FF"', container_xml)
        self.assertIn('fill="#060A16"', container_xml)

    def test_master_dossier_svg_exists_and_parses(self):
        """Verify that generated dossier.svg exists, is valid XML, and has 1536x1024 viewBox."""
        dossier_file = ASSETS_DIR / "dossier.svg"
        self.assertTrue(dossier_file.exists(), "dossier.svg must exist")
        tree = ET.parse(dossier_file)
        root = tree.getroot()
        self.assertIn("svg", root.tag.lower())
        self.assertEqual(root.attrib.get("width"), "1536")
        self.assertEqual(root.attrib.get("height"), "1024")
        self.assertEqual(root.attrib.get("viewBox"), "0 0 1536 1024")

    def test_telemetry_svg_exists_and_parses(self):
        """Verify that generated telemetry.svg exists and parses cleanly."""
        telemetry_file = ASSETS_DIR / "telemetry.svg"
        self.assertTrue(telemetry_file.exists(), "telemetry.svg must exist")
        tree = ET.parse(telemetry_file)
        root = tree.getroot()
        self.assertIn("svg", root.tag.lower())
        self.assertEqual(root.attrib.get("width"), "800")
        self.assertEqual(root.attrib.get("height"), "420")


if __name__ == "__main__":
    unittest.main()
