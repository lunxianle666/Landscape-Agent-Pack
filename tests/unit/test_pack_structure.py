"""Offline checks for shipped skill discovery, imports and release inventory."""
import hashlib
import importlib
import json
from pathlib import Path
import pkgutil
import re
import subprocess
import unittest

import landscape_agent_pack

ROOT = Path(__file__).resolve().parents[2]


class PackStructureTests(unittest.TestCase):
    def test_shipped_skill_entry_points_and_local_links(self):
        agent_entry = (ROOT / "AGENT_CONTEXT.md").read_text(encoding="utf-8")
        entries = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertTrue(entries, "No usable Skill packaged")
        for entry in entries:
            with self.subTest(skill=entry.parent.name):
                text = entry.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                _, header, body = text.split("---\n", 2)
                self.assertRegex(header, rf"(?m)^name: {re.escape(entry.parent.name)}$")
                self.assertRegex(header, r"(?m)^description: \S")
                self.assertTrue((entry.parent / "LICENSE").is_file())
                self.assertIn(entry.relative_to(ROOT).as_posix(), agent_entry)
                for link in re.findall(r"\]\(([^\s:)]+\.md)(?:#[^)]*)?\)", body):
                    self.assertTrue((entry.parent / link).is_file(), f"{entry.name}: missing {link}")

    def test_runtime_modules_import_without_installed_cad_applications(self):
        self.assertEqual(Path(landscape_agent_pack.__file__).resolve().parent,
                         ROOT / "landscape_agent_pack")
        modules = list(pkgutil.walk_packages(landscape_agent_pack.__path__,
                                            landscape_agent_pack.__name__ + "."))
        self.assertTrue(modules)
        for item in modules:
            with self.subTest(module=item.name):
                importlib.import_module(item.name)

    @unittest.skipUnless((ROOT / ".git").exists(), "Tracked-file check requires a Git checkout")
    def test_manifest_covers_all_tracked_release_inputs(self):
        files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        expected = set(files) - {"", "manifest.json", "SHA256SUMS.txt"}
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({entry["relative_path"] for entry in manifest["files"]}, expected)

    def test_checksum_list_matches_manifest(self):
        manifest_path = ROOT / "manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        listed = {}
        for row in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, path = row.split("  ", 1)
            self.assertNotIn(path, listed)
            listed[path] = digest
        expected = {e["relative_path"]: e["sha256"] for e in json.loads(manifest_bytes)["files"]}
        expected["manifest.json"] = hashlib.sha256(manifest_bytes).hexdigest()
        self.assertEqual(listed, expected)
