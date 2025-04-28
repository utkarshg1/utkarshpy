# conftest.py

# tests/conftest.py
import os
import sys
import io
import json
import subprocess
import pytest
from unittest.mock import MagicMock

# Make sure pytest can import from src/utkarshpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import utkarshpy.cli as cli  # now importable


# --- Mock Classes ---
class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakePopen:
    def __init__(
        self,
        command=None,
        shell=None,
        stdout=None,
        stderr=None,
        text=None,
        executable=None,
    ):
        self.command = command
        self.shell = shell
        # Ensure stdout and stderr are always StringIO objects
        self.stdout = (
            io.StringIO()
            if stdout is None
            else (stdout if hasattr(stdout, "getvalue") else io.StringIO(str(stdout)))
        )
        self.stderr = (
            io.StringIO()
            if stderr is None
            else (stderr if hasattr(stderr, "getvalue") else io.StringIO(str(stderr)))
        )
        self.text = text
        self.executable = executable
        self._returncode = 0

    def communicate(self):
        # Always return strings from the StringIO objects
        if hasattr(self.stdout, "getvalue"):
            stdout_value = self.stdout.getvalue()
        else:
            stdout_value = str(self.stdout)

        if hasattr(self.stderr, "getvalue"):
            stderr_value = self.stderr.getvalue()
        else:
            stderr_value = str(self.stderr)

        return (stdout_value, stderr_value)

    @property
    def returncode(self):
        return self._returncode

    @returncode.setter
    def returncode(self, value):
        self._returncode = value


# --- Custom Command Router ---
class CommandRouter:
    """Routes mock responses for different shell commands"""

    def __init__(self):
        self.responses = {
            # Default responses for common commands
            "gh --version": FakeCompletedProcess(
                returncode=0, stdout="gh version 2.35.0"
            ),
            "gh auth status": FakeCompletedProcess(
                returncode=0, stdout="✓ Logged in to github.com as testuser"
            ),
            "git config --global user.name": FakeCompletedProcess(
                returncode=0, stdout="Test User\n"
            ),
            "git config --global user.email": FakeCompletedProcess(
                returncode=0, stdout="user@example.com\n"
            ),
            "git rev-parse --is-inside-work-tree": FakeCompletedProcess(
                returncode=0, stdout="true\n"
            ),
            "git remote": FakeCompletedProcess(returncode=0, stdout=""),
            "gh api user -q .login": FakeCompletedProcess(
                returncode=0, stdout="testuser\n"
            ),
            "uv --version": FakeCompletedProcess(returncode=0, stdout="uv 1.0.0\n"),
            "uv init .": FakeCompletedProcess(returncode=0, stdout=""),
            "uv venv": FakeCompletedProcess(returncode=0, stdout=""),
            "uv add -r requirements.txt": FakeCompletedProcess(returncode=0, stdout=""),
            "uv sync": FakeCompletedProcess(returncode=0, stdout=""),
            "git init -b main": FakeCompletedProcess(returncode=0, stdout=""),
            "git add .": FakeCompletedProcess(returncode=0, stdout=""),
            'git commit -m "Initial commit"': FakeCompletedProcess(
                returncode=0, stdout=""
            ),
            "git branch -M main": FakeCompletedProcess(returncode=0, stdout=""),
            "gh repo create test-repo --public --source=. --remote=origin --push": FakeCompletedProcess(
                returncode=0, stdout="https://github.com/testuser/test-repo"
            ),
            "gh repo create test-repo --private --source=. --remote=origin --push": FakeCompletedProcess(
                returncode=0, stdout="https://github.com/testuser/test-repo"
            ),
            "pip install uv": FakeCompletedProcess(returncode=0, stdout=""),
            ".venv\\Scripts\\activate.bat && uv add -r requirements.txt": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
            ".venv\\Scripts\\activate.bat && uv sync": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
            ".venv\\Scripts\\activate.bat && uv run template.py": FakeCompletedProcess(
                returncode=0, stdout="Generated extra folders and files"
            ),
            "bash -c 'source .venv/bin/activate && uv add -r requirements.txt'": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
            "bash -c 'source .venv/bin/activate && uv sync'": FakeCompletedProcess(
                returncode=0, stdout=""
            ),
            "bash -c 'source .venv/bin/activate && uv run template.py'": FakeCompletedProcess(
                returncode=0, stdout="Generated extra folders and files"
            ),
        }

    def run_command(
        self,
        cmd,
        shell=True,
        check=True,
        text=True,
        stdout=None,
        stderr=None,
        executable=None,
        **kwargs
    ):
        """Match commands and return appropriate responses"""
        # Try exact matches first
        if cmd in self.responses:
            response = self.responses[cmd]
            if check and response.returncode != 0:
                raise subprocess.CalledProcessError(
                    response.returncode,
                    cmd,
                    output=response.stdout,
                    stderr=response.stderr,
                )
            return response

        # Then check for partial matches (more specific matches should be added above if needed)
        for command, response in self.responses.items():
            if command in cmd:
                if check and response.returncode != 0:
                    raise subprocess.CalledProcessError(
                        response.returncode,
                        cmd,
                        output=response.stdout,
                        stderr=response.stderr,
                    )
                return response

        # Default success response if no match
        return FakeCompletedProcess(returncode=0, stdout="", stderr="")

    def set_response(self, command, returncode=0, stdout="", stderr=""):
        """Set a custom response for a command"""
        self.responses[command] = FakeCompletedProcess(
            returncode=returncode, stdout=stdout, stderr=stderr
        )

    def clear_responses(self):
        """Reset to default responses"""
        self.__init__()


# --- Network-related mocks ---
class FakeResponse(io.BytesIO):
    """Mock for urlopen responses"""

    def __init__(self, content=b"FAKE-DATA", status=200, headers=None):
        super().__init__(content)
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status


# --- Fixtures ---
@pytest.fixture
def command_router():
    """Fixture to access and configure the command router"""
    router = CommandRouter()
    yield router
    router.clear_responses()


@pytest.fixture
def mock_subprocess(monkeypatch, command_router):
    """Fixture to mock subprocess with command routing"""
    monkeypatch.setattr(subprocess, "run", command_router.run_command)
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    yield command_router


@pytest.fixture
def mock_urlopen(monkeypatch):
    """Fixture to mock URL downloads"""
    url_content_map = {
        "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore": b"# Python gitignore\n*.pyc\n__pycache__/\n",
        "https://raw.githubusercontent.com/apache/.github/main/LICENSE": b"Apache License Version 2.0",
    }

    def fake_urlopen(url):
        content = url_content_map.get(url, b"DEFAULT CONTENT")
        return FakeResponse(content)

    monkeypatch.setattr(cli, "urlopen", fake_urlopen)
    return url_content_map


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory and cd into it"""
    orig_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(orig_dir)


@pytest.fixture
def mock_inputs(monkeypatch):
    """Mock user input with configurable values"""
    inputs = []

    def mock_input(prompt=""):
        if not inputs:
            return ""
        return inputs.pop(0)

    monkeypatch.setattr("builtins.input", mock_input)
    return inputs


@pytest.fixture
def mock_file_exists(monkeypatch):
    """Mock os.path.exists with configurable values"""
    existing_files = set()

    def mock_exists(path):
        return path in existing_files

    monkeypatch.setattr(os.path, "exists", mock_exists)
    return existing_files


@pytest.fixture
def disable_system_exit(monkeypatch):
    """Prevent sys.exit from exiting during tests"""

    def mock_exit(code=0):
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", mock_exit)
