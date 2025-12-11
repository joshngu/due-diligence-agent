

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 1. Setup Page Config
st.set_page_config(page_title="RMC Manager Scout", page_icon="🕵️")
st.title("🕵️ Investment Manager Scout Agent")
st.caption("Built for Rice Management Company Internship Prep")

# 2. Sidebar for API Keys (keeps it secure)
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    tavily_api_key = st.text_input("Tavily API Key", type="password")

if not openai_api_key or not tavily_api_key:
    st.warning("Please enter your API keys in the sidebar to continue.")
    st.stop()

# 3. Define the Tools
# Tavily will search the web for us. We set k=5 to get top 5 results per query.
search_tool = TavilySearchResults(tavily_api_key=tavily_api_key, k=5)
tools = [search_tool]

# 4. Define the "Brain" (LLM)
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=openai_api_key)

# 5. Define the Prompt (The "Endowment Analyst" Persona)
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior investment analyst at an automated endowment fund. 
    Your goal is to perform initial due diligence on an investment firm.
    
    You must find the following information:
    1. **Strategy Overview**: What do they invest in? (e.g., L/S Equity, Venture Capital, Real Estate).
    2. **AUM (Assets Under Management)**: What is their most recent reported size?
    3. **Key Personnel**: Who are the founders or CIOs?
    4. **Recent News/Sentiment**: Are there any recent scandals, big wins, or major news in the last 12 months?
    
    If you cannot find specific data, state "Data not publicly available" rather than hallucinating.
    Format your output as a clean Markdown report."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 6. Construct the Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 7. The UI Logic
firm_name = st.text_input("Enter Investment Firm Name (e.g. 'Sequoia Capital'):")

if st.button("Generate Due Diligence Report") and firm_name:
    with st.spinner(f"Agent is researching {firm_name} across the web..."):
        try:
            # Run the agent
            response = agent_executor.invoke({"input": f"Research the firm: {firm_name}"})
            
            # Display Result
            st.success("Research Complete!")
            st.markdown("---")
            st.markdown(response["output"])
            
        except Exception as e:
            st.error(f"An error occurred: {e}")