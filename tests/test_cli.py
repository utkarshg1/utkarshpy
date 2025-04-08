# tests/test_cli.py
import sys
import os
import pytest

from utkarshpy import cli


def test_check_python_version_passes():
    # default sys.version_info >= 3.6
    cli.check_python_version()


def test_check_python_version_fails(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 5, 0))
    with pytest.raises(SystemExit):
        cli.check_python_version()


def test_run_command_returns_fake_completed():
    res = cli.run_command("echo hi", check=True)
    # our FakeCompletedProcess has returncode 0 and empty stdout
    assert hasattr(res, "stdout")
    assert res.returncode == 0


def test_run_command_live_output(monkeypatch, capsys):
    # ensure live_output path uses our FakePopen without error
    cli.run_command("anything", live_output=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_download_files_success(tmp_path, capsys):
    target = tmp_path / "out.bin"
    cli.download_files("http://example.com/foo", str(target))
    assert target.read_bytes() == b"FAKE-DATA"

    out = capsys.readouterr().out
    # ✅ check that "Downloaded" and "out.bin" are both in output
    assert "Downloaded" in out
    assert "out.bin" in out


def test_download_files_failure(monkeypatch, tmp_path):
    # simulate a download error
    def bad_urlopen(url):
        raise Exception("network error")

    monkeypatch.setattr(cli, "urlopen", bad_urlopen)

    with pytest.raises(SystemExit):
        cli.download_files("http://bad", str(tmp_path / "fail.bin"))


def test_initialize_local_repo_creates(monkeypatch, tmp_path, capsys):
    # simulate no .git dir
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    calls = []
    monkeypatch.setattr(cli, "run_command", lambda cmd, **kw: calls.append(cmd))

    cli.initialize_local_repo()
    out = capsys.readouterr().out
    assert "Initializing local repository" in out
    assert any("git init -b main" in c for c in calls)


def test_main_end_to_end(monkeypatch, tmp_path, capsys):
    # stub every step in main()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli, "check_python_version", lambda: None)
    monkeypatch.setattr(cli, "check_gh_installed", lambda: True)
    monkeypatch.setattr(cli, "github_auth", lambda: None)
    monkeypatch.setattr(cli, "setup_git_config", lambda: None)
    monkeypatch.setattr(cli, "initialize_local_repo", lambda: None)
    monkeypatch.setattr(cli, "create_basic_files", lambda: None)
    monkeypatch.setattr(cli, "setup_virtualenv", lambda: None)
    monkeypatch.setattr(cli, "setup_vscode", lambda: None)
    monkeypatch.setattr(
        cli, "create_github_repo", lambda name, vis: "https://fake/repo"
    )

    # feed inputs for repo name & visibility
    inputs = iter(["myrepo", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    cli.main()
    out = capsys.readouterr().out
    assert "✅ Setup Complete!" in out
    assert "https://fake/repo" in out
