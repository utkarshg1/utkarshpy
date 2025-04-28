# UtkarshPy

[![CI](https://github.com/utkarshg1/utkarshpy/actions/workflows/ci.yml/badge.svg)](https://github.com/utkarshg1/utkarshpy/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/utkarshpy.svg)](https://pypi.org/project/utkarshpy/)
[![Python Versions](https://img.shields.io/pypi/pyversions/utkarshpy.svg)](https://pypi.org/project/utkarshpy/)
[![License](https://img.shields.io/github/license/utkarshg1/utkarshpy)](https://github.com/utkarshg1/utkarshpy/blob/main/LICENSE)
[![Install with pipx](https://img.shields.io/badge/Install%20with-pipx-ff69b4?logo=pypi)](https://pypa.github.io/pipx/)
[![YouTube Demo](https://img.shields.io/badge/YouTube-Demo-red?logo=youtube)](https://www.youtube.com/watch?v=TWTiICMrZwY)

<p align="center">
  <img src="https://raw.githubusercontent.com/utkarshg1/utkarshpy/main/assets/logo.png" alt="UtkarshPy Logo" width="500"/>
</p>

UtkarshPy is a CLI tool that streamlines Python project setup by automating:

- Environment checks (Python version ≥ 3.8)
- GitHub authentication and repository creation
- Local Git initialization
- Virtual environment setup with `uv`
- VS Code workspace configuration

---

## Demo

Watch the tool in action:

<p align="center">
  <a href="https://www.youtube.com/watch?v=TWTiICMrZwY" target="_blank">
    <img src="https://img.youtube.com/vi/TWTiICMrZwY/maxresdefault.jpg" alt="UtkarshPy Demo Video" width="600" />
  </a>
  <br>
  <strong>🎬 Click on the thumbnail above to watch the YouTube video! 🎬</strong>
</p>

---

## Installation

**Option 1: Install with pipx (Recommended)**

```bash
python -m pip install --user pipx
python -m pipx ensurepath
pipx install utkarshpy
```

**Option 2: Install with pip**

```bash
pip install utkarshpy
```

---

## Usage

```bash
utkarshpy [--version] [--no-push]
```

- `--version`  
  Show the tool version and exit.
- `--no-push`  
  Skip all GitHub-related operations: no authentication prompts, no remote creation or push.

---

## Features

- **Python Version Check**: Verifies that Python 3.8 or higher is installed.
- **GitHub Integration**: Uses GitHub CLI (`gh`) for authentication, repository creation, and push.
- **Skip GitHub Operations**: `--no-push` flag performs local setup without creating or pushing to GitHub.
- **Local Git Setup**: Initializes a new Git repository and generates `.gitignore`, `LICENSE`, and `README.md`.
- **Virtual Environment**: Creates a `.venv` using `uv venv` and manages dependencies with `uv`.
- **VS Code Configuration**: Generates `.vscode/settings.json` with auto-save, formatting, and Jupyter settings.
- **Custom Templates**: Automatically runs `template.py` if present to generate extra folders and files after dependencies are installed.

---

## Step-by-Step Workflow

1. **Invoke the CLI**
   ```bash
   utkarshpy [--no-push]
   ```
2. **(Optional) Enter Repository Name & Visibility**
   - If `--no-push` is omitted, you'll be prompted:
     - **Repository Name** (only letters, numbers, `-`, and `_`)
     - **Visibility** (`public` or `private`, default: `public`)
3. **GitHub CLI Check & Authentication**
   - Verifies `gh` installation or prompts to install.
   - Runs `gh auth login` if not already authenticated.
4. **Git Configuration**
   - Sets global `user.name` and `user.email` from your GitHub account or prompts for input.
5. **Local Initialization**
   - Installs `uv` if not already installed.
   - Runs `uv init .` to create project files and removes redundant `.gitignore`.
6. **File Generation**
   - Downloads a Python-specific `.gitignore` from GitHub.
   - Fetches an Apache 2.0 `LICENSE` from apache/.github repository.
   - Creates a basic `README.md` with project name.
7. **Virtual Environment & Dependencies**
   - Ensures `pyproject.toml` exists or errors.
   - Creates `.venv` via `uv venv`.
   - Installs `requirements.txt` (if present) using `uv add -r requirements.txt`.
   - Syncs dependencies with `uv sync` to create/update lockfile.
   - Provides activation instructions for the virtual environment.
8. **VS Code Setup**
   - Writes `.vscode/settings.json` with recommended Python and Jupyter settings.
9. **(GitHub Only) Repository Creation & Push**
   - If `--no-push` is **not** used:
     - Commits initial files and renames branch to `main`.
     - Executes `gh repo create` with chosen visibility.
     - Pushes to `origin` and displays the repository URL.
   - If `--no-push` **is** used:
     - Skips authentication, remote creation, and push entirely.

---

## Example Output

### Standard Run (with GitHub push)

```
🚀 Python Project Automator - Utkarsh Gaikwad 🚀
Platform detected: Linux

Enter GitHub repository name: my-project
Visibility [public/private] (default: public): public
✓ GitHub authentication verified
⚙️ Checking Git configuration...
✓ Initialized uv folder
📂 Creating project structure...
✓ Downloaded .gitignore
✓ Created README.md
🔄 Creating virtual environment...
✓ Virtual environment created
📦 Installing dependencies...
✓ Dependencies installed
✓ uv synced to lockfile

🔌 Virtual environment activation:
  source .venv/bin/activate

✓ VS Code settings configured with your new settings!
🔄 Creating public repository 'my-project'...
✓ Repository created and pushed: https://github.com/username/my-project

✅ Setup Complete! Repository: https://github.com/username/my-project
➤ Local path: /path/to/my-project
```

### Local-Only Run (skip GitHub)

```bash
utkarshpy --no-push
```

```
🚀 Python Project Automator - Utkarsh Gaikwad 🚀
Platform detected: Linux
⚠️  --no-push mode: skipping all GitHub prompts and authentication
🔄 Initializing local uv git repository...
📂 Creating project structure...
🔄 Creating virtual environment...
✓ Virtual environment created
📦 No requirements.txt found

🔌 Virtual environment activation:
  source .venv/bin/activate

✓ VS Code settings configured with your new settings!

✅ Setup Complete! (no GitHub repo created)
➤ Local path: /path/to/project
```

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](https://github.com/utkarshg1/utkarshpy/blob/main/LICENSE) for details.

---

This CLI tool saves time by automating tedious setup tasks, ensuring a consistent and streamlined workflow for Python projects!
