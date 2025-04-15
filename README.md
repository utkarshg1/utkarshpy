# UtkarshPy

CLI tool to automate Python project setup with GitHub integration and VS Code configuration

## Installation

```bash
pip install utkarshpy
```

## Usage

```bash
utkarshpy
```

## Features

- **Checks Python Version:** Ensures Python 3.6 or higher is installed.
- **GitHub Authentication:** Verifies GitHub CLI installation and authenticates the user.
- **Git Configuration:** Automatically sets up Git username and email from GitHub.
- **Project Initialization:** Initializes a local Git repository using `uv` if available.
- **Essential Files Creation:** Generates `.gitignore`, `LICENSE`, and `README.md`.
- **GitHub Repository Creation:** Creates a public or private GitHub repository and pushes the code.
- **Virtual Environment Setup:** Creates and activates a virtual environment using `uv`, then installs dependencies.
- **VS Code Configuration:** Configures workspace settings for auto-save, formatting, and Jupyter.

## Step-by-Step Workflow

1. **Run the CLI Tool:**
   ```bash
   utkarshpy
   ```
2. **Enter the Repository Name:**
   - The tool prompts you to enter a name for your GitHub repository.
3. **Choose Repository Visibility:**
   - Select `public` or `private` (default is `public`).
4. **Verify GitHub CLI Installation:**
   - If `gh` is not installed, the tool provides a download link.
5. **Authenticate with GitHub:**
   - If not logged in, the tool prompts GitHub authentication via the browser.
6. **Setup Git Configuration:**
   - Automatically sets the global Git username and email (or prompts for it).
7. **Initialize Local Repository:**
   - Runs `uv init .` to initialize a new repository if `uv` is installed.
8. **Create Essential Files:**
   - Downloads `.gitignore` for Python projects.
   - Fetches an Apache 2.0 `LICENSE` file.
   - Generates a `README.md` with a basic project description.
9. **Setup Virtual Environment:**
   - Creates a `.venv` directory using `uv` and installs dependencies from `requirements.txt` if available.
   - Upgrades `pip` and syncs `uv` to the lockfile.
10. **Configure VS Code:**
    - Creates a `.vscode/settings.json` file with auto-save, Python formatting, and Jupyter settings.
11. **Push Code to GitHub:**
    - Adds and commits files.
    - Creates the GitHub repository using `gh repo create`.
    - Pushes the initial commit to GitHub.
12. **Setup Complete:**
    - The repository is now available on GitHub.
    - Displays repository URL and local project path.

## Example Output

```
🚀 Python Project Automator - Utkarsh Gaikwad 🚀

Enter GitHub repository name: my-project
Visibility [public/private] (default: public): public
✓ GitHub authentication verified
⚙️ Checking Git configuration...
✓ Local repository initialized
📂 Creating project structure...
✓ Downloaded .gitignore
✓ Created README.md
🔄 Creating virtual environment...
✓ Virtual environment created
🔄 Upgrading pip...
✓ Dependencies installed
✓ VS Code settings configured with your new settings!
🔄 Creating public repository 'my-project'...
✓ Repository created: https://github.com/your-username/my-project

✅ Setup Complete!
➤ Repository: https://github.com/your-username/my-project
➤ Local path: /path/to/my-project
```

This CLI tool saves time by automating tedious setup tasks, ensuring a consistent and streamlined workflow for Python projects!
