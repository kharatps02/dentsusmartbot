import os
import streamlit as st
import requests
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import InMemorySaver
import warnings
import uuid

warnings.filterwarnings('ignore')

# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Dentsu AI Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Dentsu Multi-User Conversational AI Research Assistant")

# Default theme in session_state
if "theme" not in st.session_state:
    st.session_state.theme = "Modern Light"

# ============================================================================
# SIDEBAR: CREDENTIALS INPUT
# ============================================================================

st.sidebar.header("🔐 API Credentials")
st.sidebar.markdown("Enter your Azure OpenAI and external API credentials below.")

with st.sidebar.form("credentials_form"):
    st.markdown("### Azure OpenAI Configuration")
    
    endpoint = st.text_input(
        "Model Endpoint",
        placeholder="https://your-resource.openai.azure.com/",
        type="password"
    )
    
    model_name = st.text_input(
        "Chat Model Name (Deployment Name)",
        placeholder="gpt-4-deployment",
        type="password"
    )
    
    api_key = st.text_input(
        "Azure OpenAI API Key",
        placeholder="your-api-key-here",
        type="password"
    )
    
    api_version = st.text_input(
        "API Version",
        value="2024-02-15-preview",
        type="password"
    )
    
    st.markdown("### External APIs")
    
    weather_api_key = st.text_input(
        "Weather API Key (WeatherAPI.com)",
        placeholder="your-weather-api-key",
        type="password"
    )
    
    tavily_api_key = st.text_input(
        "Tavily API Key (Web Search)",
        placeholder="your-tavily-api-key",
        type="password"
    )
    
    submitted = st.form_submit_button("✅ Load Credentials")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "credentials_loaded" not in st.session_state:
    st.session_state.credentials_loaded = False

if submitted:
    # Validate credentials
    if all([endpoint, model_name, api_key, api_version, weather_api_key, tavily_api_key]):
        st.session_state.credentials_loaded = True
        st.session_state.endpoint = endpoint
        st.session_state.model_name = model_name
        st.session_state.api_key = api_key
        st.session_state.api_version = api_version
        st.session_state.weather_api_key = weather_api_key
        st.session_state.tavily_api_key = tavily_api_key
        st.sidebar.success("✅ Credentials loaded successfully!")
    else:
        st.sidebar.error("⚠️ Please fill in all credentials")

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

def initialize_agent():
    """Create and initialize the conversational agent with tools."""
    
    # Initialize Tavily search
    tavily_tool = TavilySearchResults(
        max_results=5,
        search_depth='advanced',
        include_raw_content=True,
        tavily_api_key=st.session_state.tavily_api_key
    )
    
    @tool
    def search_web_extract_info(query: str) -> list:
        """Search the web and return extracted content from Tavily results."""
        results = tavily_tool.invoke(query)
        docs = []
        for result in results:
            title = result.get("title", "No Title")
            content = result.get("content", "")
            url = result.get("url", "")
            formatted = f"**{title}**\n{content}\n*Source: {url}*"
            docs.append(formatted)
        return docs
    
    @tool
    def get_weather(query: str) -> dict:
        """Get the current weather for a given location using WeatherAPI."""
        base_url = "http://api.weatherapi.com/v1/current.json"
        response = requests.get(
            base_url,
            params={"key": st.session_state.weather_api_key, "q": query}
        )
        data = response.json()
        return data if data.get("location") else {"error": "Weather data not found"}
    
    # Create Azure OpenAI LLM
    llm = AzureChatOpenAI(
        azure_deployment=st.session_state.model_name,
        api_version=st.session_state.api_version,
        azure_endpoint=st.session_state.endpoint,
        api_key=st.session_state.api_key,
        temperature=0
    )
    
    # System prompt
    sys_prompt = """You are a helpful Dentsu AI Research Assistant.
You can use these tools when needed:
- search_web_extract_info: for web search on earnings, news, trends
- get_weather: for weather info in different locations
Think step-by-step if required, but keep answers clear and concise.
Context awareness: Remember previous questions in this conversation to provide contextual responses."""
    
    tools = [search_web_extract_info, get_weather]
    
    # Create agent with memory (InMemorySaver checkpointer)
    checkpointer = InMemorySaver()
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=sys_prompt,
        checkpointer=checkpointer,
    )
    
    return agent

# ============================================================================
# CHAT INTERFACE
# ============================================================================

if st.session_state.credentials_loaded:
    
    # Initialize agent if not already done
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = initialize_agent()
            st.session_state.agent_initialized = True
        except Exception as e:
            st.error(f"❌ Error initializing agent: {str(e)}")
            st.session_state.agent_initialized = False
    
    if st.session_state.get("agent_initialized", False):
        
        # Sidebar: User session management
        st.sidebar.header("👤 User Session")

        # Theme selector
        theme_choice = st.sidebar.radio(
            "Theme",
            ("Modern Light", "Modern Dark"),
            index=0 if st.session_state.theme == "Modern Light" else 1,
        )
        st.session_state.theme = theme_choice

        # Inject theme CSS
        if st.session_state.theme == "Modern Dark":
            st.markdown(
                """
                <style>
                .css-1d391kg {background: linear-gradient(180deg,#0f1724,#071021);} /* main */
                .stApp {background: linear-gradient(180deg,#0f1724,#071021);}
                .css-1lcbmhc {background-color: rgba(255,255,255,0.02);} /* container */
                .block-container{background: rgba(10,20,30,0.6); border-radius:12px; padding:18px}
                .stSidebar {background: linear-gradient(180deg,#071021,#0f1724);}
                .stButton>button {border-radius:8px}
                .stChatMessage {background: rgba(255,255,255,0.03)}
                </style>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <style>
                .stApp {background: linear-gradient(180deg,#f5f7fb,#e9eef8);} 
                .block-container{background: rgba(255,255,255,0.9); border-radius:12px; padding:18px}
                .stSidebar {background: linear-gradient(180deg,#ffffff,#f1f5f9);}
                .stButton>button {border-radius:8px}
                .stChatMessage {background: rgba(0,0,0,0.03)}
                </style>
                """,
                unsafe_allow_html=True,
            )

        # Initialize or persist a session id in session_state
        if "session_id" not in st.session_state or not st.session_state.session_id:
            st.session_state.session_id = f"dentsu_analyst_{uuid.uuid4().hex[:6]}"

        session_id = st.sidebar.text_input(
            "Enter Your User ID",
            value=st.session_state.session_id,
            help="Each user gets their own conversation history"
        )

        # Persist any manual edits to the session id
        st.session_state.session_id = session_id

        # Allow generating a new random session id
        if st.sidebar.button("🔁 Generate New Session ID"):
            st.session_state.session_id = f"dentsu_analyst_{uuid.uuid4().hex[:6]}"
            st.experimental_rerun()

        # Start a completely new session: clear messages and agent/memory
        if st.sidebar.button("🆕 Start New Session"):
            st.session_state.messages = []
            # Remove agent so it will be reinitialized with fresh memory
            if "agent" in st.session_state:
                try:
                    del st.session_state.agent
                except Exception:
                    pass
            st.session_state.agent_initialized = False
            st.session_state.session_id = f"dentsu_analyst_{uuid.uuid4().hex[:6]}"
            st.success("✅ New session started")
            st.experimental_rerun()

        if st.sidebar.button("🔄 Clear Conversation History"):
            # Clear only conversation messages for current session
            st.session_state.messages = []
            st.success("Conversation history cleared for current session.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        st.markdown("### 💬 Conversation")
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # User input
        st.markdown("---")
        user_input = st.chat_input(
            "Ask me about Dentsu, competitors, weather, or trends...",
            key="user_input"
        )
        
        if user_input:
            # Display user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_input)
            
            # Get agent response
            with st.spinner("🔄 Processing your query..."):
                try:
                    result = st.session_state.agent.invoke(
                        {"messages": [{"role": "user", "content": user_input}]},
                        {"configurable": {"thread_id": session_id}}
                    )
                    
                    response = result["messages"][-1].content
                    
                    # Store and display response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(response)
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Info section
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ About This App")
        st.sidebar.markdown("""
        This Streamlit app implements a **Multi-User Conversational AI Research Assistant** for Dentsu.
        
        **Features:**
        - 🔍 Web search via Tavily
        - 🌡️ Real-time weather data
        - 💾 Per-user conversation memory
        - 🤖 Azure OpenAI integration
        
        **How It Works:**
        1. Enter your API credentials
        2. Set your user ID
        3. Ask questions and get contextual responses
        4. Conversation history persists within your session
        """)
    
    else:
        st.warning("⚠️ Failed to initialize the agent. Please check your credentials and try again.")

else:
    st.info("👈 Please enter your API credentials in the sidebar to get started!")
    st.markdown("""
    ## Getting Started
    
    1. **Azure OpenAI Setup**: 
       - Endpoint URL (e.g., `https://your-resource.openai.azure.com/`)
       - Deployment name
       - API key
    
    2. **External APIs**:
       - [WeatherAPI.com](https://www.weatherapi.com/) - Free weather data
       - [Tavily API](https://tavily.com/) - Advanced web search
    
    3. **Enter credentials** in the sidebar and click **Load Credentials**
    
    4. **Start chatting** with your personalized AI research assistant!
    """)
