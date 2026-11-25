"""The README is also the PyPI page. Found 2026-11-25 by a stranger run of the
published 0.3.1: the "Try the stranger flow" block installed `.`, and in a
folder without a checkout pip stops with "Directory '.' is not installable".
The block has to install the published package, pinned to the shipping version."""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def stranger_block():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = text.split("## Try the stranger flow", 1)[1]
    return re.search(r"```sh\n(.*?)```", section, re.S).group(1)


class StrangerInstall(unittest.TestCase):
    def test_installs_the_published_version_not_a_checkout(self):
        version = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
        installs = [line for line in stranger_block().splitlines() if "pip install" in line]
        self.assertEqual(len(installs), 1, installs)
        self.assertIn(f"transcripto=={version}", installs[0])
        self.assertFalse(installs[0].rstrip().endswith(" ."), installs[0])


if __name__ == "__main__":
    unittest.main()
