"""Check LangChain version and available functions."""
import sys

try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
    print(f"LangChain location: {langchain.__file__}")
    print()
except Exception as e:
    print(f"Error importing langchain: {e}")
    sys.exit(1)

# Check what's in langchain.agents
try:
    from langchain import agents
    print("Available in langchain.agents:")
    print("-" * 60)
    
    # List all attributes
    attrs = [attr for attr in dir(agents) if not attr.startswith('_')]
    for attr in sorted(attrs):
        print(f"  - {attr}")
    
    print()
    
    # Try to import the specific function
    try:
        from langchain.agents import create_tool_calling_agent
        print("✓ create_tool_calling_agent is available")
    except ImportError as e:
        print(f"✗ create_tool_calling_agent is NOT available: {e}")
        
    try:
        from langchain.agents import AgentExecutor
        print("✓ AgentExecutor is available")
    except ImportError as e:
        print(f"✗ AgentExecutor is NOT available: {e}")
        
except Exception as e:
    print(f"Error checking langchain.agents: {e}")

