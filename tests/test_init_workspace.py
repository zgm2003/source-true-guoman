import tempfile
import unittest
from pathlib import Path

from scripts.init_workspace import ASSET_DIRS, init_workspace


class InitWorkspaceTests(unittest.TestCase):
    def test_init_workspace_creates_standard_asset_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            created = init_workspace(workspace)

            self.assertEqual([path.name for path in created], list(ASSET_DIRS))
            for dirname in ASSET_DIRS:
                self.assertTrue((workspace / dirname).is_dir())

    def test_init_workspace_is_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script = workspace / "第一章.txt"
            script.write_text("原始剧本", encoding="utf-8")

            existing_dir = workspace / "场景资产"
            existing_dir.mkdir()
            marker = existing_dir / "existing.txt"
            marker.write_text("keep", encoding="utf-8")

            init_workspace(workspace)

            self.assertEqual(script.read_text(encoding="utf-8"), "原始剧本")
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
