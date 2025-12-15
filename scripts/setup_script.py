"""
Automated setup script for the Due Diligence Agent project.

This script will:
1. Check Python version (requires 3.10+)
2. Create a virtual environment if it doesn't exist
3. Install required dependencies from requirements.txt
4. Create a .envdev template file for API keys
5. Run basic environment checks

Usage:
    python scripts/setup_script.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================
MIN_PYTHON_VERSION = (3, 10)
VENV_NAME = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
ENV_FILE = ".envdev"

# Get the project root (parent of scripts folder)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


# ============================================================================
# Utility Functions
# ============================================================================
def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step: int, text: str) -> None:
    """Print a step indicator."""
    print(f"\n[Step {step}] {text}")
    print("-" * 40)


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"✓ {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"⚠ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"✗ {text}")


def run_command(cmd: list, cwd: Path = None, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result
    except Exception as e:
        print_error(f"Command failed: {e}")
        return None


# ============================================================================
# Setup Steps
# ============================================================================
def check_python_version() -> bool:
    """Check if Python version meets minimum requirements."""
    print_step(1, "Checking Python Version")
    
    current_version = sys.version_info[:2]
    print(f"  Current Python: {sys.version}")
    print(f"  Required: >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
    
    if current_version >= MIN_PYTHON_VERSION:
        print_success(f"Python {current_version[0]}.{current_version[1]} meets requirements")
        return True
    else:
        print_error(f"Python {current_version[0]}.{current_version[1]} does not meet minimum version {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
        return False


def create_virtual_environment() -> bool:
    """Create a virtual environment if it doesn't exist."""
    print_step(2, "Setting Up Virtual Environment")
    
    venv_path = PROJECT_ROOT / VENV_NAME
    
    if venv_path.exists():
        print_success(f"Virtual environment already exists at: {venv_path}")
        return True
    
    print(f"  Creating virtual environment at: {venv_path}")
    result = run_command([sys.executable, "-m", "venv", str(venv_path)])
    
    if result and result.returncode == 0:
        print_success("Virtual environment created successfully")
        return True
    else:
        print_error("Failed to create virtual environment")
        return False


def get_venv_python() -> Path:
    """Get the path to the Python executable in the virtual environment."""
    venv_path = PROJECT_ROOT / VENV_NAME
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip() -> Path:
    """Get the path to pip in the virtual environment."""
    venv_path = PROJECT_ROOT / VENV_NAME
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_requirements() -> bool:
    """Install requirements from requirements.txt."""
    print_step(3, "Installing Dependencies")
    
    requirements_path = PROJECT_ROOT / REQUIREMENTS_FILE
    
    if not requirements_path.exists():
        print_error(f"Requirements file not found: {requirements_path}")
        return False
    
    pip_path = get_venv_pip()
    
    if not pip_path.exists():
        print_error(f"Pip not found at: {pip_path}")
        return False
    
    # Upgrade pip first
    print("  Upgrading pip...")
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    
    # Install requirements
    print(f"  Installing packages from {REQUIREMENTS_FILE}...")
    result = run_command([str(pip_path), "install", "-r", str(requirements_path)])
    
    if result and result.returncode == 0:
        print_success("All dependencies installed successfully")
        return True
    else:
        print_error("Failed to install some dependencies")
        return False


def create_env_file() -> bool:
    """Create a .envdev template file if it doesn't exist."""
    print_step(4, "Setting Up Environment Variables File")
    
    env_path = PROJECT_ROOT / ENV_FILE
    
    if env_path.exists():
        print_success(f"Environment file already exists: {env_path}")
        print_warning("Review the file and add your API keys if not already set")
        return True
    
    env_template = """# Environment variables for Due Diligence Agent
# Copy this file or rename to .envdev and fill in your API keys

# ==============================================================================
# REQUIRED: Tavily API Key (for web search)
# Get your key at: https://tavily.com/
# ==============================================================================
TAVILY_API_KEY=your_tavily_api_key_here

# ==============================================================================
# OPTIONAL: OpenAI API Key (only if using OpenAI as LLM provider)
# Get your key at: https://platform.openai.com/api-keys
# ==============================================================================
OPENAI_API_KEY=your_openai_api_key_here

# ==============================================================================
# OPTIONAL: Ollama Configuration (for local LLM)
# Download Ollama at: https://ollama.com/
# ==============================================================================
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    try:
        with open(env_path, "w") as f:
            f.write(env_template)
        print_success(f"Created environment template file: {env_path}")
        print_warning("IMPORTANT: Edit .envdev and add your API keys before running the app")
        return True
    except Exception as e:
        print_error(f"Failed to create environment file: {e}")
        return False


def verify_installation() -> bool:
    """Verify that all packages are installed correctly."""
    print_step(5, "Verifying Installation")
    
    python_path = get_venv_python()
    
    packages_to_check = [
        "streamlit",
        "langchain",
        "langchain_openai",
        "langchain_ollama",
        "langchain_community",
        "dotenv",
    ]
    
    all_ok = True
    for package in packages_to_check:
        result = run_command(
            [str(python_path), "-c", f"import {package}"],
            capture_output=True
        )
        if result and result.returncode == 0:
            print_success(f"{package} - installed")
        else:
            print_error(f"{package} - NOT FOUND")
            all_ok = False
    
    return all_ok


def print_next_steps() -> None:
    """Print instructions for next steps."""
    print_header("Setup Complete! Next Steps")
    
    venv_activate = ".venv\\Scripts\\Activate.ps1" if platform.system() == "Windows" else "source .venv/bin/activate"
    
    print(f"""
1. Activate the virtual environment:
   {venv_activate}

2. Edit the .envdev file and add your API keys:
   - TAVILY_API_KEY (required for web search)
   - OPENAI_API_KEY (optional, if using OpenAI)

3. If using Ollama (local LLM), make sure it's running:
   ollama run llama3.2

4. Run the application:
   streamlit run app.py

5. (Optional) Run health checks:
   python unit_tests/app_is_working.py
""")


# ============================================================================
# Main Entry Point
# ============================================================================
def main() -> int:
    """Main setup function."""
    print_header("Due Diligence Agent - Environment Setup")
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    
    # Step 1: Check Python version
    if not check_python_version():
        print_error("Setup cannot continue. Please install Python 3.10 or higher.")
        return 1
    
    # Step 2: Create virtual environment
    if not create_virtual_environment():
        print_error("Setup cannot continue. Failed to create virtual environment.")
        return 1
    
    # Step 3: Install requirements
    if not install_requirements():
        print_warning("Some packages may not have installed correctly.")
        print_warning("Try running: pip install -r requirements.txt")
    
    # Step 4: Create .envdev file
    create_env_file()
    
    # Step 5: Verify installation
    if not verify_installation():
        print_warning("Some packages could not be verified.")
        print_warning("The app may still work - try running it.")
    
    # Print next steps
    print_next_steps()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
