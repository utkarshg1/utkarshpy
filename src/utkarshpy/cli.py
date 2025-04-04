"""
CLI tool to automate Python project setup with GitHub integration and VS Code configuration
Created by Utkarsh Gaikwad
"""

import json
import os
import re
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import urlopen


# --- Utility Functions ---
def run_command(command, check=True, live_output=False):
    """Run a shell command with error handling and optional real-time output."""
    try:
        if live_output:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
            )
            process.communicate()
            if process.returncode != 0 and check:
                sys.exit(process.returncode)
            return None
        else:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed: {e.stderr}")
        sys.exit(1)


def download_files(url, filename):
    """Download file from URL with proper error handling."""
    try:
        with urlopen(url) as response:
            if response.status != 200:
                raise HTTPError(
                    url, response.status, "HTTP Error", response.headers, None
                )
            with open(filename, "wb") as f:
                f.write(response.read())
        print(f"✓ Downloaded {filename}")
    except Exception as e:
        print(f"✗ Failed to download {filename}: {str(e)}")
        sys.exit(1)


# --- Setup Functions ---
def check_python_version():
    """Verify Python version meets minimum requirements."""
    if sys.version_info < (3, 6):
        print("✗ Python 3.6 or higher required")
        sys.exit(1)


def check_gh_installed():
    """Verify GitHub CLI installation by checking command exit code."""
    result = run_command("gh --version", check=False)
    if result and result.returncode == 0:
        return True
    print("✗ GitHub CLI not installed. Install from https://cli.github.com")
    return False


def github_auth():
    """Handle GitHub authentication."""
    result = run_command("gh auth status", check=False)
    if result.returncode != 0:  # type: ignore
        print("🔑 Authenticating with GitHub...")
        run_command("gh auth login --web --hostname github.com", live_output=True)
    else:
        print("✓ GitHub authentication verified")


def get_github_username():
    """Get authenticated GitHub username."""
    result = run_command("gh api user -q .login")
    return result.stdout.strip()  # type: ignore


def setup_git_config():
    """Set basic Git configuration if missing."""
    print("⚙️ Checking Git configuration...")

    # Set username from GitHub if not configured
    if not run_command("git config --global user.name", check=False).stdout.strip():  # type: ignore
        github_username = get_github_username()
        run_command(f'git config --global user.name "{github_username}"')

    # Set email if not configured
    if not run_command("git config --global user.email", check=False).stdout.strip():  # type: ignore
        email = input("Enter your GitHub email: ").strip()
        run_command(f'git config --global user.email "{email}"')


def initialize_local_repo():
    """Initialize Git repository in current directory."""
    if os.path.exists(".git"):
        print("✓ Git repository already exists")
        return

    print("🔄 Initializing local repository...")
    run_command("git init -b main")
    print("✓ Local repository initialized")


def create_basic_files():
    """Create essential project files if missing."""
    print("\n📂 Creating project structure...")

    # .gitignore
    if not os.path.exists(".gitignore"):
        download_files(
            "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore",
            ".gitignore",
        )

    # LICENSE
    if not os.path.exists("LICENSE"):
        download_files(
            "https://raw.githubusercontent.com/apache/.github/main/LICENSE", "LICENSE"
        )

    # README.md
    if not os.path.exists("README.md"):
        repo_name = os.path.basename(os.getcwd())
        with open("README.md", "w") as f:
            f.write(f"# {repo_name}\n\n## Project Description\n")
        print("✓ Created README.md")


def create_github_repo(repo_name, visibility="public"):
    """Create GitHub repository in current directory."""
    print(f"\n🔄 Creating {visibility} repository '{repo_name}'...")

    try:
        # Stage and attempt initial commit
        run_command("git add .")
        commit_result = run_command(
            'git commit -m "Initial commit"',
            check=False,  # Don't fail if empty
            live_output=False,
        )

        if commit_result and commit_result.returncode == 0:
            print("✓ Initial commit created")
        else:
            print("ℹ️ No changes to commit - creating empty repository")

        # Create repository with GitHub CLI
        run_command(
            f"gh repo create {repo_name} --{visibility} --source=. --remote=origin --push"
        )

        # Get repository URL
        github_username = get_github_username()
        repo_url = f"https://github.com/{github_username}/{repo_name}"

        print(f"✓ Repository created: {repo_url}")
        return repo_url
    except Exception as e:
        print(f"✗ Repository creation failed: {str(e)}")
        sys.exit(1)


def setup_virtualenv():
    """Create virtual environment and install dependencies."""
    # Check if uv is installed
    uv_check = run_command("uv --version", check=False)
    if uv_check.returncode != 0:  # type: ignore
        print("\n✗ uv is not installed. Installing via pip...")
        run_command(f"{sys.executable} -m pip install uv", live_output=True)
    
    venv_dir = "venv"

    # Create virtual environment
    if not os.path.exists(venv_dir):
        print("\n🔄 Creating virtual environment...")
        run_command(f"uv venv {venv_dir}")
        print("✓ Virtual environment created")
    else:
        print("\n✓ Virtual environment exists")

    # Platform-specific activation commands
    activate_cmd = (
        "venv\\Scripts\\activate.bat"
        if sys.platform == "win32"
        else "source venv/bin/activate"
    )

    # Upgrade pip
    print("\n🔄 Upgrading pip...")
    run_command(
        f"{activate_cmd} && uv pip install --upgrade pip", live_output=True
    )

    # Install requirements
    if os.path.exists("requirements.txt"):
        print("\n📦 Installing dependencies...")
        run_command(
            f"{activate_cmd} && uv pip install -r requirements.txt", live_output=True
        )
        print("✓ Dependencies installed")
    else:
        print("\nℹ️ No requirements.txt found")

    # Activation instructions
    print("\n🔌 Virtual environment activation:")
    print(f"  {activate_cmd}")


def setup_vscode():
    """Configure VS Code workspace settings with auto-save, Python formatting, analysis, and Jupyter options."""
    vscode_dir = ".vscode"
    settings_path = os.path.join(vscode_dir, "settings.json")

    # Create the .vscode folder if it doesn't exist
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)

    settings = {
        "files.autoSave": "afterDelay",
        "files.autoSaveDelay": 1000,
        "[python]": {
            "editor.defaultFormatter": "ms-python.black-formatter",
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.fixAll": "always"},
        },
        "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
        "jupyter.askForKernelRestart": False,
        "notebook.formatOnCellExecution": True,
        "notebook.codeActionsOnSave": {"notebook.source.fixAll": "explicit"},
    }

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print("\n✓ VS Code settings configured with your new settings!")


def is_git_repo():
    """Check if the current directory is a Git repository."""
    result = run_command(
        "git rev-parse --is-inside-work-tree", check=False, live_output=False
    )
    return result.returncode == 0


def has_origin_remote():
    """Check if the Git repository has an 'origin' remote."""
    result = run_command("git remote", check=False, live_output=False)
    return "origin" in result.stdout.split()


# --- Main Flow ---
def main():
    try:
        print("\n🚀 Python Project Automator - Utkarsh Gaikwad 🚀")
        check_python_version()

        # Prevent execution if origin remote exists
        if is_git_repo() and has_origin_remote():
            print(
                "\n✗ This script should be used for first-time repository setup only."
            )
            print("   Remote 'origin' already exists - aborting.")
            sys.exit(1)

        # Get repository info
        repo_name = ""
        while not repo_name:
            repo_name = input("\nEnter GitHub repository name: ").strip()
            if not re.match(r"^[a-zA-Z0-9_-]+$", repo_name):
                print("Invalid name - only letters, numbers, - and _ allowed")
                repo_name = ""

        visibility = (
            input("Visibility [public/private] (default: public): ").strip().lower()
        )
        visibility = visibility if visibility in ["public", "private"] else "public"

        # Setup workflow
        if not check_gh_installed():
            sys.exit(1)

        github_auth()
        setup_git_config()
        initialize_local_repo()
        create_basic_files()
        # Development environment setup
        setup_virtualenv()
        setup_vscode()
        repo_url = create_github_repo(repo_name, visibility)

        # Final output
        print("\n✅ Setup Complete!")
        print(f"➤ Repository: {repo_url}")
        print(f"➤ Local path: {os.getcwd()}")
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
