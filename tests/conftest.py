# tests/conftest.py
import os
import sys
import io
import subprocess
import pytest

# 1) Make sure pytest can import from src/utkarshpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import utkarshpy.cli as cli  # now importable


# --- Fake process objects for subprocess.run / Popen ---
class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakePopen:
    def __init__(self, *args, **kwargs):
        pass

    def communicate(self):
        return ("", "")

    @property
    def returncode(self):
        return 0


# 2) Autouse fixture to stub subprocess calls
@pytest.fixture(autouse=True)
def patch_subprocess(monkeypatch):
    # stub subprocess.run → always “succeeds”
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, shell, check, text, stdout, stderr: FakeCompletedProcess(),
    )
    # stub subprocess.Popen → always “succeeds”
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    yield


# 3) Autouse fixture to stub network downloads via urlopen
@pytest.fixture(autouse=True)
def patch_urlopen(monkeypatch):
    class FakeResponse(io.BytesIO):
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url):
        # return  some dummy bytes
        return FakeResponse(b"FAKE-DATA")

    # patch the name that cli.py imported
    monkeypatch.setattr(cli, "urlopen", fake_urlopen)
    yield
