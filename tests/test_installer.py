"""Tests for install_skill.py — verifies installer path resolution, file layout,
idempotent reinstall, and error handling for both target CLIs."""

import json
import sys
import zipfile
from pathlib import Path

import pytest

# Ensure the repo root is on the path so we can import install_skill
sys.path.insert(0, str(Path(__file__).parent.parent))

import install_skill  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def source_dir(tmp_path: Path) -> Path:
    """A minimal valid skill source directory."""
    (tmp_path / "safe_edit.py").write_text("# safe_edit stub\ndef main(): pass\n")
    (tmp_path / "distiller.py").write_text("# distiller stub\ndef main(): pass\n")
    (tmp_path / "SKILL.md").write_text(
        "---\nname: code-intelligence\ndescription: test\n---\n# Skill\n"
    )
    (tmp_path / "requirements.txt").write_text("tree-sitter>=0.20.0\n")
    (tmp_path / "LICENSE").write_text("MIT")
    (tmp_path / "ACKNOWLEDGMENTS.md").write_text("Acknowledgments.")
    return tmp_path


@pytest.fixture()
def skill_archive(tmp_path: Path, source_dir: Path) -> Path:
    """A valid .skill ZIP archive built from *source_dir*."""
    archive = tmp_path / "code-intelligence.skill"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ["safe_edit.py", "distiller.py", "SKILL.md", "requirements.txt"]:
            zf.write(source_dir / name, name)
    return archive


# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------

class TestPathResolution:
    def test_gemini_user_scope(self):
        result = install_skill.get_gemini_skills_dir("user")
        assert result == Path.home() / ".gemini" / "skills" / install_skill.SKILL_NAME

    def test_gemini_workspace_scope(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = install_skill.get_gemini_skills_dir("workspace")
        assert result == tmp_path / ".gemini" / "skills" / install_skill.SKILL_NAME

    def test_claude_user_scope(self):
        result = install_skill.get_claude_plugin_dir("user")
        assert result == Path.home() / ".claude" / "plugins" / install_skill.SKILL_NAME

    def test_claude_workspace_scope(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = install_skill.get_claude_plugin_dir("workspace")
        assert result == tmp_path / ".claude" / "plugins" / install_skill.SKILL_NAME


# ---------------------------------------------------------------------------
# Source resolution tests
# ---------------------------------------------------------------------------

class TestSourceResolution:
    def test_resolve_valid_directory(self, source_dir: Path):
        result = install_skill.resolve_source(str(source_dir))
        assert result == source_dir

    def test_resolve_skill_archive(self, skill_archive: Path):
        result = install_skill.resolve_source(str(skill_archive))
        # Should be a directory with extracted contents
        assert result.is_dir()
        assert (result / "SKILL.md").exists()
        assert (result / "safe_edit.py").exists()

    def test_resolve_missing_path_exits(self):
        with pytest.raises(SystemExit):
            install_skill.resolve_source("/nonexistent/path/that/does/not/exist")

    def test_resolve_directory_missing_required_files_exits(self, tmp_path: Path):
        # Create a directory without SKILL.md
        (tmp_path / "safe_edit.py").write_text("stub")
        with pytest.raises(SystemExit):
            install_skill.resolve_source(str(tmp_path))


# ---------------------------------------------------------------------------
# Gemini CLI installation tests
# ---------------------------------------------------------------------------

class TestGeminiInstall:
    def test_install_creates_correct_layout(self, source_dir: Path, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: tmp_path / "gemini")
        dest = install_skill.install_gemini(source_dir, "user")

        assert (dest / "SKILL.md").exists()
        assert (dest / "safe_edit.py").exists()
        assert (dest / "distiller.py").exists()
        assert (dest / "requirements.txt").exists()
        assert (dest / "LICENSE").exists()

    def test_install_idempotent(self, source_dir: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        # Run twice — should not raise
        install_skill.install_gemini(source_dir, "user")
        install_skill.install_gemini(source_dir, "user")
        assert (gemini_dir / "SKILL.md").exists()

    def test_uninstall_removes_directory(self, source_dir: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        install_skill.install_gemini(source_dir, "user")
        assert gemini_dir.exists()

        install_skill.uninstall_gemini("user")
        assert not gemini_dir.exists()

    def test_uninstall_when_not_installed_does_not_raise(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            install_skill, "get_gemini_skills_dir", lambda scope: tmp_path / "nonexistent"
        )
        # Should print a message but not raise
        install_skill.uninstall_gemini("user")


# ---------------------------------------------------------------------------
# Claude Code installation tests
# ---------------------------------------------------------------------------

class TestClaudeInstall:
    def test_install_creates_correct_layout(self, source_dir: Path, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: tmp_path / "claude")
        dest = install_skill.install_claude(source_dir, "user")

        assert (dest / ".claude-plugin" / "plugin.json").exists()
        assert (dest / "skills" / install_skill.SKILL_NAME / "SKILL.md").exists()
        assert (dest / "safe_edit.py").exists()
        assert (dest / "distiller.py").exists()

    def test_plugin_json_valid(self, source_dir: Path, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: tmp_path / "claude")
        dest = install_skill.install_claude(source_dir, "user")

        plugin_json = json.loads((dest / ".claude-plugin" / "plugin.json").read_text())
        assert plugin_json["name"] == install_skill.SKILL_NAME
        assert "version" in plugin_json
        assert "description" in plugin_json

    def test_install_idempotent(self, source_dir: Path, tmp_path: Path, monkeypatch):
        claude_dir = tmp_path / "claude"
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: claude_dir)
        install_skill.install_claude(source_dir, "user")
        install_skill.install_claude(source_dir, "user")
        assert (claude_dir / "skills" / install_skill.SKILL_NAME / "SKILL.md").exists()

    def test_uninstall_removes_directory(self, source_dir: Path, tmp_path: Path, monkeypatch):
        claude_dir = tmp_path / "claude"
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: claude_dir)
        install_skill.install_claude(source_dir, "user")
        assert claude_dir.exists()

        install_skill.uninstall_claude("user")
        assert not claude_dir.exists()

    def test_uninstall_when_not_installed_does_not_raise(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            install_skill, "get_claude_plugin_dir", lambda scope: tmp_path / "nonexistent"
        )
        install_skill.uninstall_claude("user")


# ---------------------------------------------------------------------------
# Install from .skill archive tests
# ---------------------------------------------------------------------------

class TestInstallFromArchive:
    def test_gemini_install_from_archive(self, skill_archive: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        source_dir = install_skill.resolve_source(str(skill_archive))
        install_skill.install_gemini(source_dir, "user")
        assert (gemini_dir / "SKILL.md").exists()
        assert (gemini_dir / "safe_edit.py").exists()

    def test_claude_install_from_archive(self, skill_archive: Path, tmp_path: Path, monkeypatch):
        claude_dir = tmp_path / "claude"
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: claude_dir)
        source_dir = install_skill.resolve_source(str(skill_archive))
        install_skill.install_claude(source_dir, "user")
        assert (claude_dir / "skills" / install_skill.SKILL_NAME / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# verify_install tests
# ---------------------------------------------------------------------------

class TestVerifyInstall:
    def test_verify_gemini_passes_after_install(self, source_dir: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        install_skill.install_gemini(source_dir, "user")
        # Should not raise or exit
        install_skill.verify_install("gemini-cli", gemini_dir)

    def test_verify_claude_passes_after_install(self, source_dir: Path, tmp_path: Path, monkeypatch):
        claude_dir = tmp_path / "claude"
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: claude_dir)
        install_skill.install_claude(source_dir, "user")
        install_skill.verify_install("claude-code", claude_dir)

    def test_verify_gemini_fails_on_missing_file(self, tmp_path: Path):
        incomplete_dir = tmp_path / "incomplete"
        incomplete_dir.mkdir()
        # Only create one of the required files
        (incomplete_dir / "SKILL.md").write_text("stub")
        with pytest.raises(SystemExit):
            install_skill.verify_install("gemini-cli", incomplete_dir)

    def test_verify_claude_fails_on_missing_plugin_json(self, tmp_path: Path):
        incomplete_dir = tmp_path / "incomplete"
        (incomplete_dir / "skills" / install_skill.SKILL_NAME).mkdir(parents=True)
        (incomplete_dir / "skills" / install_skill.SKILL_NAME / "SKILL.md").write_text("stub")
        # Missing .claude-plugin/plugin.json
        with pytest.raises(SystemExit):
            install_skill.verify_install("claude-code", incomplete_dir)


# ---------------------------------------------------------------------------
# CLI entrypoint (main) smoke tests
# ---------------------------------------------------------------------------

class TestMainEntrypoint:
    def test_install_all_via_main(self, source_dir: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        claude_dir = tmp_path / "claude"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: claude_dir)

        install_skill.main([
            "--target", "all",
            "--scope", "user",
            "--source", str(source_dir),
        ])

        assert (gemini_dir / "SKILL.md").exists()
        assert (claude_dir / ".claude-plugin" / "plugin.json").exists()

    def test_uninstall_via_main(self, source_dir: Path, tmp_path: Path, monkeypatch):
        gemini_dir = tmp_path / "gemini"
        monkeypatch.setattr(install_skill, "get_gemini_skills_dir", lambda scope: gemini_dir)
        monkeypatch.setattr(install_skill, "get_claude_plugin_dir", lambda scope: tmp_path / "claude")

        install_skill.main(["--target", "gemini-cli", "--source", str(source_dir)])
        assert gemini_dir.exists()

        install_skill.main(["--target", "gemini-cli", "--uninstall"])
        assert not gemini_dir.exists()
