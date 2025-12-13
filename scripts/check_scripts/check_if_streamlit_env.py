"""Check if Streamlit's Python environment has langchain installed."""
import sys
import subprocess
import importlib.util

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

def check_langchain_in_python(python_exe):
    """Check if langchain is installed in the given Python environment."""
    try:
        # Use the Python interpreter to check if langchain can be imported
        result = subprocess.run(
            [python_exe, "-c", "import langchain; print('langchain installed')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "langchain installed" in result.stdout:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking langchain: {e}")
        return False

def main():
    """Main function to check if Streamlit's Python has langchain."""
    print("Checking Streamlit's Python environment...")
    print("-" * 60)
    
    python_exe, streamlit_path = find_streamlit_python()
    
    if python_exe is None:
        print("Could not determine Streamlit's Python environment.")
        return
    
    print(f"Streamlit Python: {python_exe}")
    print(f"Streamlit location: {streamlit_path}")
    print()
    
    print("Checking for langchain...")
    has_langchain = check_langchain_in_python(python_exe)
    
    print("-" * 60)
    if has_langchain:
        print("✓ streamlit has langchain installed")
    else:
        print("✗ streamlit does NOT have langchain installed")
        print("\nTo install langchain, run:")
        print(f"  {python_exe} -m pip install langchain")

if __name__ == "__main__":
    main()

