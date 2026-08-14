from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NoHooksTests(unittest.TestCase):
    def test_plugin_does_not_ship_lifecycle_hooks(self) -> None:
        self.assertFalse(
            (ROOT / "hooks").exists(),
            "Nuko Nova Unslop must not intercept client lifecycle or final-output events",
        )


if __name__ == "__main__":
    unittest.main()
