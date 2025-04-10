import subprocess
import sys
import os
import json
import pytest
from unittest.mock import patch, mock_open


from conftest import FakePopen
from utkarshpy import cli


# --- Utility Function Tests ---
class TestUtilityFunctions:
    def test_check_python_version_passes(self):
        # Should pass with current Python version
        cli.check_python_version()

    def test_check_python_version_fails(self, monkeypatch):
        # Should fail with Python 3.5
        monkeypatch.setattr(sys, "version_info", (3, 5, 0))
        with pytest.raises(SystemExit):
            cli.check_python_version()

    def test_run_command_success(self, mock_subprocess):
        # Test basic command execution
        result = cli.run_command("echo test")
        assert result.returncode == 0

    def test_run_command_failure(self, mock_subprocess):
        # Set command to fail
        mock_subprocess.set_response("failing_command", returncode=1, stderr="Error")

        # Should raise SystemExit because sys.exit(1) is called
        with pytest.raises(SystemExit):
            cli.run_command("failing_command")

    def test_run_command_live_output(self, monkeypatch, mock_subprocess):
        # Test live output path with mocked Popen
        fake_popen_instance = FakePopen()
        monkeypatch.setattr(
            "subprocess.Popen", lambda *args, **kwargs: fake_popen_instance
        )

        # Should complete without error
        cli.run_command("test_command", live_output=True, check=False)
        assert fake_popen_instance.returncode == 0

        # Test with non-zero exit code
        fake_popen_instance.returncode = 1
        with pytest.raises(SystemExit):
            cli.run_command("another_command", live_output=True, check=True)

    def test_download_files_success(self, temp_project_dir, mock_urlopen):
        # Test successful file download
        filename = "test.txt"
        cli.download_files("https://example.com/test", filename)

        # Verify file was created
        assert os.path.exists(filename)

        # Test with specific URL
        gitignore = ".gitignore"
        cli.download_files(
            "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore",
            gitignore,
        )

        # Verify file content matches mock
        with open(gitignore, "rb") as f:
            content = f.read()
            assert b"# Python gitignore" in content

    def test_download_files_failure(
        self, monkeypatch, temp_project_dir, disable_system_exit
    ):
        # Mock urlopen to fail
        def failing_urlopen(url):
            raise Exception("Download failed")

        monkeypatch.setattr(cli, "urlopen", failing_urlopen)

        # Should raise SystemExit
        with pytest.raises(SystemExit):
            cli.download_files("http://bad.url", "output.txt")


# --- GitHub Authentication Tests ---
class TestGitHubAuth:
    def test_check_gh_installed_success(self, mock_subprocess):
        # gh is installed
        assert cli.check_gh_installed() is True

    def test_check_gh_installed_failure(self, mock_subprocess):
        # gh is not installed
        mock_subprocess.set_response(
            "gh --version", returncode=127, stderr="command not found"
        )
        assert cli.check_gh_installed() is False

    def test_github_auth_already_authenticated(self, mock_subprocess, capsys):
        # Already authenticated
        cli.github_auth()
        out = capsys.readouterr().out
        assert "GitHub authentication verified" in out

    def test_github_auth_needs_login(self, mock_subprocess, monkeypatch, capsys):
        # Not authenticated
        mock_subprocess.set_response(
            "gh auth status", returncode=1, stderr="not logged in"
        )

        # Mock run_command to capture live command
        commands_run = []
        orig_run_command = cli.run_command

        def mock_run_command(cmd, **kwargs):
            commands_run.append(cmd)
            if kwargs.get("live_output"):
                return None
            return mock_subprocess.run_command(cmd, **kwargs)

        monkeypatch.setattr(cli, "run_command", mock_run_command)

        # Run auth function
        cli.github_auth()
        out = capsys.readouterr().out

        # Verify login command was called
        assert "Authenticating with GitHub" in out
        assert any("gh auth login" in cmd for cmd in commands_run)

    def test_get_github_username(self, mock_subprocess):
        # Set username response
        mock_subprocess.set_response("gh api user -q .login", stdout="testuser\n")

        # Verify username is returned
        assert cli.get_github_username() == "testuser"


# --- Git Configuration Tests ---
class TestGitConfiguration:
    def test_setup_git_config_already_configured(self, mock_subprocess, capsys):
        # Git config already set
        cli.setup_git_config()
        out = capsys.readouterr().out
        assert "Checking Git configuration" in out

    def test_setup_git_config_needs_username(
        self, mock_subprocess, mock_inputs, monkeypatch, capsys
    ):
        # Username not configured, but email is
        mock_subprocess.set_response(
            "git config --global user.name", returncode=0, stdout=""
        )
        mock_subprocess.set_response(
            "git config --global user.email", returncode=0, stdout="user@example.com\n"
        )
        mock_subprocess.set_response(
            "gh api user -q .login", returncode=0, stdout="testuser\n"
        )

        # Track commands
        commands = []
        orig_run_command = cli.run_command

        def track_command(cmd, **kwargs):
            commands.append(cmd)
            return orig_run_command(cmd, **kwargs)

        monkeypatch.setattr(cli, "run_command", track_command)

        # Run setup
        cli.setup_git_config()

        # Verify git config command was run with username
        assert any(
            'git config --global user.name "testuser"' in cmd for cmd in commands
        )

    def test_setup_git_config_needs_email(
        self, mock_subprocess, mock_inputs, monkeypatch, capsys
    ):
        # Email not configured, but username is
        mock_subprocess.set_response(
            "git config --global user.name", returncode=0, stdout="Test User\n"
        )
        mock_subprocess.set_response(
            "git config --global user.email", returncode=0, stdout=""
        )

        # Set email input
        mock_inputs.append("user@example.com")

        # Track commands
        commands = []
        orig_run_command = cli.run_command

        def track_command(cmd, **kwargs):
            commands.append(cmd)
            return orig_run_command(cmd, **kwargs)

        monkeypatch.setattr(cli, "run_command", track_command)

        # Run setup
        cli.setup_git_config()

        # Verify git config command was run with email
        assert any(
            'git config --global user.email "user@example.com"' in cmd
            for cmd in commands
        )


# --- Repository Initialization Tests ---
class TestRepoInitialization:
    def test_initialize_local_repo_already_exists(self, mock_file_exists, capsys):
        # .git directory already exists
        mock_file_exists.add(".git")

        cli.initialize_local_repo()
        out = capsys.readouterr().out
        assert "Git repository already exists" in out

    def test_initialize_local_repo_creates_new(
        self, temp_project_dir, mock_file_exists, monkeypatch, capsys
    ):
        # No .git directory
        commands = []
        orig_run_command = cli.run_command

        def track_command(cmd, **kwargs):
            commands.append(cmd)
            return orig_run_command(cmd, **kwargs)

        monkeypatch.setattr(cli, "run_command", track_command)

        # Initialize repo
        cli.initialize_local_repo()

        # Verify git init was called
        assert "git init -b main" in commands
        out = capsys.readouterr().out
        assert "Local repository initialized" in out

    def test_is_git_repo(self, mock_subprocess):
        # Test positive case
        mock_subprocess.set_response(
            "git rev-parse --is-inside-work-tree", returncode=0, stdout="true\n"
        )
        assert cli.is_git_repo() is True


# --- Additional Tests for CLI Functions ---


class TestCLI:
    def test_create_basic_files(self, temp_project_dir, mock_file_exists, monkeypatch):
        """Test the creation of basic project files."""
        # Mock os.path.exists to simulate missing files
        mock_file_exists.clear()

        # Mock download_files to avoid actual network calls
        def mock_download_files(url, filename):
            mock_file_exists.add(filename)  # Simulate file creation
            with open(filename, "w") as f:
                f.write("Mock content")

        monkeypatch.setattr(cli, "download_files", mock_download_files)

        # Save the original open function
        original_open = open

        # Mock open for README.md creation
        def mock_open_readme(filename, mode, *args, **kwargs):
            if filename == "README.md" and "w" in mode:
                mock_file_exists.add(filename)  # Simulate file creation
            return original_open(filename, mode, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open_readme)

        # Run the function
        cli.create_basic_files()

        # Verify files were created
        assert ".gitignore" in mock_file_exists
        assert "LICENSE" in mock_file_exists
        assert "README.md" in mock_file_exists

    def test_create_github_repo_success(self, mock_subprocess, monkeypatch):
        """Test successful GitHub repository creation."""
        # Mock get_github_username to return a test username
        monkeypatch.setattr(cli, "get_github_username", lambda: "testuser")

        # Run the function
        repo_url = cli.create_github_repo("test-repo", visibility="public")

        # Verify the repository URL
        assert repo_url == "https://github.com/testuser/test-repo"

    def test_create_github_repo_failure(self, mock_subprocess):
        """Test failure during GitHub repository creation."""
        # Mock run_command to raise an exception
        mock_subprocess.set_response(
            "gh repo create test-repo --public", returncode=1, stderr="Error"
        )

        # Verify SystemExit is raised
        with pytest.raises(SystemExit):
            cli.create_github_repo("test-repo", visibility="public")

    def test_setup_vscode(self, temp_project_dir):
        """Test VS Code settings configuration."""
        # Run the function
        cli.setup_vscode()

        # Verify settings.json was created
        settings_path = os.path.join(".vscode", "settings.json")
        assert os.path.exists(settings_path)

        # Verify settings content
        with open(settings_path, "r") as f:
            settings = json.load(f)
            assert settings["files.autoSave"] == "afterDelay"
            assert (
                settings["[python]"]["editor.defaultFormatter"]
                == "ms-python.black-formatter"
            )

    def test_is_git_repo(self, mock_subprocess):
        """Test checking if the current directory is a Git repository."""
        # Mock positive case
        mock_subprocess.set_response(
            "git rev-parse --is-inside-work-tree", returncode=0, stdout="true\n"
        )
        assert cli.is_git_repo() is True

        # Mock negative case
        mock_subprocess.set_response(
            "git rev-parse --is-inside-work-tree", returncode=1, stderr="Error"
        )
        assert cli.is_git_repo() is False

    def test_has_origin_remote(self, mock_subprocess):
        """Test checking if the Git repository has an 'origin' remote."""
        # Mock positive case
        mock_subprocess.set_response("git remote", stdout="origin\n")
        assert cli.has_origin_remote() is True

        # Mock negative case
        mock_subprocess.set_response("git remote", stdout="")
        assert cli.has_origin_remote() is False
