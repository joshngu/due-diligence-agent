import streamlit as st
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .envdev file
load_dotenv('.envdev')

# 1. Setup Page Config
st.set_page_config(page_title="RMC Manager Scout", page_icon="🕵️")
st.title("🕵️ Investment Manager Scout Agent")
st.caption("Built for Rice Management Company Internship Prep")

# 2. Model Selection and API Keys
with st.sidebar:
    st.header("Configuration")
    
    # Model provider selection
    model_provider = st.selectbox(
        "LLM Provider",
        ["Ollama (Local)", "OpenAI"],
        help="Choose between local Ollama or OpenAI API"
    )
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        tavily_api_key = st.text_input("Tavily API Key", type="password", help="Or set TAVILY_API_KEY in .envdev")
    else:
        st.success("✓ Tavily API Key loaded from environment")
    
    # Provider-specific settings
    if model_provider == "OpenAI":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = st.text_input("OpenAI API Key", type="password", help="Or set OPENAI_API_KEY in .envdev")
        else:
            st.success("✓ OpenAI API Key loaded from environment")
        
        if not openai_api_key:
            st.warning("Please enter your OpenAI API key to continue.")
            st.stop()
    else:  # Ollama
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        ollama_model = st.text_input("Ollama Model", value=ollama_model, help="e.g., llama3.2, mistral, qwen2.5")
        ollama_base_url = st.text_input("Ollama Base URL", value=ollama_base_url, help="Default: http://localhost:11434")
        
        st.info("💡 Make sure Ollama is running locally")

if not tavily_api_key:
    st.warning("Please enter your Tavily API key in the sidebar to continue.")
    st.stop()

# 3. Define the Tools
# Tavily will search the web for us. We set k=5 to get top 5 results per query.
search_tool = TavilySearchResults(tavily_api_key=tavily_api_key, k=5)
tools = [search_tool]

# 4. Define the "Brain" (LLM) - Switch based on provider
if model_provider == "OpenAI":
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=openai_api_key)
else:  # Ollama
    from langchain_ollama import ChatOllama
    llm = ChatOllama(
        model=ollama_model,
        base_url=ollama_base_url,
        temperature=0
    )

# 5. Define the System Prompt (The "Endowment Analyst" Persona)
system_prompt = """You are a senior investment analyst at an automated endowment fund. 
Your goal is to perform initial due diligence on an investment firm.

You must find the following information:
1. **Strategy Overview**: What do they invest in? (e.g., L/S Equity, Venture Capital, Real Estate).
2. **AUM (Assets Under Management)**: What is their most recent reported size?
3. **Key Personnel**: Who are the founders or CIOs?
4. **Recent News/Sentiment**: Are there any recent scandals, big wins, or major news in the last 12 months?

If you cannot find specific data, state "Data not publicly available" rather than hallucinating.
Format your output as a clean Markdown report."""

# 6. Construct the Agent
agent = create_agent(llm, tools, system_prompt=system_prompt)

# 7. The UI Logic
firm_name = st.text_input("Enter Investment Firm Name (e.g. 'Sequoia Capital'):")

if st.button("Generate Due Diligence Report") and firm_name:
    with st.spinner(f"Agent is researching {firm_name} across the web..."):
        try:
            # Run the agent
            response = agent.invoke({"messages": [HumanMessage(content=f"Research the firm: {firm_name}")]})
            
            # Extract the final message from the response
            # The response contains messages, get the last AI message
            messages = response.get("messages", [])
            output = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    output = msg.content
                    break
                elif hasattr(msg, 'content') and msg.content:
                    output = msg.content
                    break
                elif isinstance(msg, dict) and 'content' in msg:
                    output = msg['content']
                    break
            
            # Display Result
            st.success("Research Complete!")
            st.markdown("---")
            st.markdown(output if output else str(response))
            
        except Exception as e:
            st.error(f"An error occurred: {e}")