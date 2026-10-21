import importlib.util
import contextlib
import io
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "repository_audit", Path(__file__).resolve().parents[1] / "repository_audit.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RepositoryAuditTests(unittest.TestCase):
    def test_cli_warning_exit_policy(self):
        report = {"errors": 0, "warnings": 1}
        with patch.object(MODULE, "audit", return_value=report), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, MODULE.main(["."]))
            self.assertEqual(1, MODULE.main([".", "--warnings-as-errors"]))

    def test_cli_non_repository_exit(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(2, MODULE.main([directory]))
        self.assertIn("Audit failed", output.getvalue())

    def test_generated_and_private_paths(self):
        for path in (".godot/a.bin", "a.blend1", "a.log", ".continue/mcp.yaml", "a.pmx", ".env"):
            with self.subTest(path=path):
                self.assertTrue(MODULE.inspect_path(path, 1))

    def test_source_metadata_is_kept(self):
        for path in ("a.blend", "a.gd.uid", "image.png.import", ".env.example"):
            self.assertEqual([], MODULE.inspect_path(path, 1))

    def test_size_boundaries(self):
        self.assertEqual("warning", MODULE.inspect_path("a.bin", 10 * 1024**2)[0][0])
        self.assertEqual("error", MODULE.inspect_path("a.bin", 100 * 1024**2)[0][0])

    def test_credential_signatures(self):
        self.assertTrue(MODULE.contains_secret(b"ghp_" + b"a" * 36))
        self.assertTrue(MODULE.contains_secret(b"-----BEGIN " + b"PRIVATE KEY-----"))
        self.assertFalse(MODULE.contains_secret(b"use os.environ['API_KEY']"))

    def test_scans_index_not_worktree_and_redacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def run(*args):
                subprocess.run(["git", "-C", directory, *args], check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            run("init", "-q")
            secret = "ghp_" + "a" * 36
            path = root / "space name.txt"
            path.write_text(secret, encoding="utf-8")
            run("add", "--", path.name)
            path.write_text("not staged", encoding="utf-8")
            report = MODULE.audit(root)
            self.assertEqual(1, report["errors"])
            self.assertNotIn(secret, str(report))
            self.assertEqual("space name.txt", report["findings"][0]["path"])


if __name__ == "__main__":
    unittest.main()
