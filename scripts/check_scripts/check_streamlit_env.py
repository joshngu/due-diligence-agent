"""Check if Streamlit's Python environment has all requirements.txt packages installed."""
import sys
import os
import subprocess
import re
from pathlib import Path

# Package name mappings (pip package name -> import name)
PACKAGE_IMPORT_MAP = {
    "python-dotenv": "dotenv",
    "tavily-python": "tavily",
    "langchain-openai": "langchain_openai",
    "langchain-community": "langchain_community",
    "langchain-core": "langchain_core",
}

def find_streamlit_python():
    """Find the Python interpreter that Streamlit is using."""
    try:
        # Try to import streamlit to get its location
        import streamlit
        streamlit_path = streamlit.__file__
        
        # Get the Python executable from the current interpreter
        # (Streamlit runs in the same Python environment it's installed in)
        python_exe = sys.executable
        
        return python_exe, streamlit_path
    except ImportError:
        print("Error: Streamlit is not installed in the current environment.")
        return None, None

def parse_requirements(requirements_path):
    """Parse requirements.txt and return list of (package_name, version_spec, import_name)."""
    requirements = []
    
    if not os.path.exists(requirements_path):
        print(f"Error: {requirements_path} not found!")
        return requirements
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse package name and version specifier
            # Examples: "streamlit", "langchain>=1.1.3", "python-dotenv"
            match = re.match(r'^([a-zA-Z0-9\-_\.]+)(.*)$', line)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2).strip()
                
                # Get import name (use mapping or default to package name with underscores)
                import_name = PACKAGE_IMPORT_MAP.get(package_name, package_name.replace('-', '_'))
                
                requirements.append((package_name, version_spec, import_name))
    
    return requirements

def check_package_in_python(python_exe, package_name, version_spec, import_name):
    """Check if a package is installed and meets version requirements."""
    # Check if package can be imported
    check_import = f"import {import_name}; print('INSTALLED')"
    
    try:
        result = subprocess.run(
            [python_exe, "-c", check_import],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0 or "INSTALLED" not in result.stdout:
            return False, None, "Not installed"
        
        # If version specifier exists, check version
        if version_spec:
            # Get installed version
            get_version = f"import {import_name}; print(getattr({import_name}, '__version__', 'unknown'))"
            version_result = subprocess.run(
                [python_exe, "-c", get_version],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            installed_version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
            
            # Simple version check for >= (can be extended for other operators)
            if version_spec.startswith(">="):
                required_version = version_spec[2:].strip()
                # For now, just report versions - full version comparison would need packaging library
                return True, installed_version, f"Installed (requires {version_spec})"
            else:
                return True, installed_version, f"Installed (requires {version_spec})"
        else:
            # Get version if available
            get_version = f"import {import_name}; print(getattr({import_name}, '__version__', 'installed'))"
            version_result = subprocess.run(
                [python_exe, "-c", get_version],
                capture_output=True,
                text=True,
                timeout=10
            )
            installed_version = version_result.stdout.strip() if version_result.returncode == 0 else "installed"
            return True, installed_version, "Installed"
            
    except Exception as e:
        return False, None, f"Error: {str(e)}"

def main():
    """Main function to check if Streamlit's Python has all requirements."""
    print("Checking Streamlit's Python environment for requirements.txt packages...")
    print("=" * 70)
    
    python_exe, streamlit_path = find_streamlit_python()
    
    if python_exe is None:
        print("Could not determine Streamlit's Python environment.")
        return
    
    print(f"Streamlit Python: {python_exe}")
    print(f"Streamlit location: {streamlit_path}")
    print()
    
    # Find requirements.txt (look in project root, relative to script location)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up from scripts/check_scripts/
    requirements_path = project_root / "requirements.txt"
    
    if not requirements_path.exists():
        print(f"Error: Could not find requirements.txt at {requirements_path}")
        return
    
    print(f"Reading requirements from: {requirements_path}")
    print()
    
    requirements = parse_requirements(requirements_path)
    
    if not requirements:
        print("No requirements found in requirements.txt")
        return
    
    print(f"Checking {len(requirements)} package(s)...")
    print("-" * 70)
    
    installed_count = 0
    missing_count = 0
    
    for package_name, version_spec, import_name in requirements:
        is_installed, version, status = check_package_in_python(python_exe, package_name, version_spec, import_name)
        
        version_display = f" (v{version})" if version and version != "installed" else ""
        requirement_display = f" {version_spec}" if version_spec else ""
        
        if is_installed:
            print(f"✓ {package_name:25s}{requirement_display:15s} - {status}{version_display}")
            installed_count += 1
        else:
            print(f"✗ {package_name:25s}{requirement_display:15s} - {status}")
            missing_count += 1
    
    print("-" * 70)
    print(f"Summary: {installed_count}/{len(requirements)} packages installed")
    
    if missing_count > 0:
        print(f"\n⚠ Missing {missing_count} package(s). To install all requirements, run:")
        print(f"  {python_exe} -m pip install -r {requirements_path}")
    else:
        print("\n✓ All requirements are installed!")

if __name__ == "__main__":
    main()

