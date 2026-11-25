"""Unit tests for named project target resolution."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import kicad_cursor_config as config


class ProjectConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempDir = tempfile.TemporaryDirectory()
        self.repoRoot = Path(self.tempDir.name)
        self.configPath = self.repoRoot / "kicad-cursor.yaml"
        self.projectDir = self.repoRoot / "board-a"
        self.otherProjectDir = self.repoRoot / "board-b"
        self.projectDir.mkdir()
        self.otherProjectDir.mkdir()
        (self.projectDir / "board-a.kicad_pro").write_text("", encoding="utf-8")
        (self.otherProjectDir / "board-b.kicad_pro").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempDir.cleanup()

    def writeConfig(self, text: str) -> None:
        self.configPath.write_text(text, encoding="utf-8")

    @mock.patch.object(config, "configFilePath")
    def testResolveActiveProject(self, configFilePath: mock.MagicMock) -> None:
        configFilePath.return_value = self.configPath
        self.writeConfig(
            f"activeProject: board-a\nprojects:\n  board-a: {self.projectDir}\n  board-b: {self.otherProjectDir}\n"
        )
        resolved = config.resolveProjectDir()
        self.assertEqual(resolved, self.projectDir.resolve())

    @mock.patch.object(config, "configFilePath")
    def testResolveNamedOverride(self, configFilePath: mock.MagicMock) -> None:
        configFilePath.return_value = self.configPath
        self.writeConfig(
            f"activeProject: board-a\nprojects:\n  board-a: {self.projectDir}\n  board-b: {self.otherProjectDir}\n"
        )
        resolved = config.resolveProjectDir(projectName="board-b")
        self.assertEqual(resolved, self.otherProjectDir.resolve())

    @mock.patch.object(config, "configFilePath")
    def testLegacyProjectDir(self, configFilePath: mock.MagicMock) -> None:
        configFilePath.return_value = self.configPath
        self.writeConfig(f"projectDir: {self.projectDir}\n")
        resolved = config.resolveProjectDir()
        self.assertEqual(resolved, self.projectDir.resolve())

    @mock.patch.object(config, "configFilePath")
    def testCliPathOverridesNamedTarget(self, configFilePath: mock.MagicMock) -> None:
        configFilePath.return_value = self.configPath
        self.writeConfig(
            f"activeProject: board-a\nprojects:\n  board-a: {self.projectDir}\n  board-b: {self.otherProjectDir}\n"
        )
        resolved = config.resolveProjectDir(cliPath=self.otherProjectDir, projectName="board-a")
        self.assertEqual(resolved, self.otherProjectDir.resolve())

    @mock.patch.object(config, "configFilePath")
    def testEnvProjectName(self, configFilePath: mock.MagicMock) -> None:
        configFilePath.return_value = self.configPath
        self.writeConfig(
            f"activeProject: board-a\nprojects:\n  board-a: {self.projectDir}\n  board-b: {self.otherProjectDir}\n"
        )
        with mock.patch.dict(os.environ, {"KICAD_PROJECT": "board-b"}, clear=False):
            resolved = config.resolveProjectDir()
        self.assertEqual(resolved, self.otherProjectDir.resolve())


if __name__ == "__main__":
    unittest.main()
