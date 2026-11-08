import json
from pathlib import Path
import tempfile
import unittest

from nuke_codex_panel.installer.notices import generate_notices, verify_notices


class NoticeGenerationTests(unittest.TestCase):
    def test_unresolved_package_preserves_only_one_readme(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime" / "pi"
            package = runtime / "node_modules" / "data-uri-to-buffer"
            package.mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({
                "name": "data-uri-to-buffer", "version": "4.0.1", "license": "MIT",
            }), encoding="utf-8")
            # On a case-insensitive filesystem these are aliases; elsewhere they are distinct files.
            (package / "README.md").write_text("uppercase readme\n", encoding="utf-8")
            (package / "readme.md").write_text("lowercase readme\n", encoding="utf-8")
            (runtime / "package-lock.json").write_text(json.dumps({
                "packages": {"node_modules/data-uri-to-buffer": {"version": "4.0.1"}},
            }), encoding="utf-8")
            (runtime / "notice-supplements.json").write_text(json.dumps({
                "unresolved": [{"package": "data-uri-to-buffer", "note": "Test evidence."}],
            }), encoding="utf-8")
            node = runtime / "node"
            npm = node / "lib" / "node_modules" / "npm"
            npm.mkdir(parents=True)
            (node / "LICENSE").write_text("Node license\n", encoding="utf-8")
            (npm / "LICENSE").write_text("npm license\n", encoding="utf-8")
            (root / "LICENSE").write_text("Project license\n", encoding="utf-8")
            manifest = {
                "node": {"version": "26.12.0", "install_dir": "node"},
                "notices": {"allowed_licenses": ["MIT"]},
            }
            node_spec = {"npm_cli": "lib/node_modules/npm/bin/npm-cli.js"}
            notices = root / "third-party-notices"

            index = generate_notices(
                runtime_dir=runtime, project_root=root, manifest=manifest,
                node_spec=node_spec, out_dir=notices,
            )

            record = index["packages"][0]
            self.assertEqual(len(record["evidence_files"]), 2)  # package.json and one README
            self.assertEqual(verify_notices(notices, runtime, manifest), [])


if __name__ == "__main__":
    unittest.main()
