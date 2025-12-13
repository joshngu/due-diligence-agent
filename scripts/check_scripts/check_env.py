"""Quick script to check which Python environment is being used and if packages are installed."""
import sys

print("=" * 60)
print("Python Environment Check")
print("=" * 60)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print()

# Check required packages
packages = [
    "streamlit",
    "langchain",
    "langchain_openai",
    "langchain_community",
    "langchain_core",
    "dotenv",
    "tavily",
]

print("Package Status:")
print("-" * 60)
for package in packages:
    try:
        if package == "dotenv":
            import dotenv
            version = getattr(dotenv, "__version__", "installed")
        elif package == "tavily":
            import tavily
            version = getattr(tavily, "__version__", "installed")
        else:
            mod = __import__(package)
            version = getattr(mod, "__version__", "installed")
        print(f"✓ {package:20s} - {version}")
    except ImportError:
        print(f"✗ {package:20s} - NOT INSTALLED")
    except Exception as e:
        print(f"? {package:20s} - Error: {e}")

print()
print("=" * 60)
print("If any packages show 'NOT INSTALLED', run:")
print("  pip install -r requirements.txt")
print("=" * 60)

