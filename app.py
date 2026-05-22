"""
Smart Dentsu Buddy — Multi-Agent Agentic RAG
Credentials are entered via the Streamlit sidebar — no .env file required.
"""

import os
import json
import warnings

# ── Must be set BEFORE any chromadb/langchain import ─────────────────────────
# chromadb imports opentelemetry-exporter-otlp-proto-grpc at module load time,
# which pulls in protobuf>=4 and breaks descriptor creation.
# These three env vars prevent that import chain from firing.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"  # force pure-Python protobuf
os.environ["ANONYMIZED_TELEMETRY"] = "False"                      # disable chromadb telemetry
os.environ["CHROMA_OTEL_COLLECTION_ENDPOINT"] = ""               # disable chromadb OTEL export
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Dentsu Buddy",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Credential helpers
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_KEYS = [
    "MODEL_ENDPOINT",
    "CHAT_MODEL_NAME",
    "AZURE_OPENAI_API_KEY",
    "api_version",
    "MODEL_ENDPOINT_EMBEDDING",
    "EMBEDDING_MODEL_NAME",
    "api_version_embedding",
    "TAVILY_API_KEY",
]

def creds_complete(creds: dict) -> bool:
    """Return True only when every required key has a non-empty value."""
    return all(creds.get(k, "").strip() for k in REQUIRED_KEYS)


def render_credentials_form():
    """
    Renders the credential input form in the sidebar.
    Saves values to st.session_state['creds'] on submission.
    Returns True when valid creds are already stored, False otherwise.
    """
    st.sidebar.markdown("## ⚙️ Configuration")

    # Pre-fill from session if already saved
    saved = st.session_state.get("creds", {})

    with st.sidebar.expander("🔑 Azure OpenAI — Chat", expanded=not creds_complete(saved)):
        endpoint = st.text_input(
            "Model Endpoint",
            value=saved.get("MODEL_ENDPOINT", ""),
            placeholder="https://YOUR_RESOURCE.openai.azure.com/",
            key="input_MODEL_ENDPOINT",
        )
        model_name = st.text_input(
            "Chat Deployment Name",
            value=saved.get("CHAT_MODEL_NAME", ""),
            placeholder="gpt-4o",
            key="input_CHAT_MODEL_NAME",
        )
        api_key = st.text_input(
            "API Key",
            value=saved.get("AZURE_OPENAI_API_KEY", ""),
            type="password",
            placeholder="••••••••••••",
            key="input_AZURE_OPENAI_API_KEY",
        )
        api_version = st.text_input(
            "API Version",
            value=saved.get("api_version", "2024-08-01-preview"),
            key="input_api_version",
        )

    with st.sidebar.expander("🔑 Azure OpenAI — Embeddings", expanded=not creds_complete(saved)):
        emb_endpoint = st.text_input(
            "Embedding Endpoint",
            value=saved.get("MODEL_ENDPOINT_EMBEDDING", ""),
            placeholder="https://YOUR_RESOURCE.openai.azure.com/",
            key="input_MODEL_ENDPOINT_EMBEDDING",
        )
        emb_model = st.text_input(
            "Embedding Deployment Name",
            value=saved.get("EMBEDDING_MODEL_NAME", ""),
            placeholder="text-embedding-3-large",
            key="input_EMBEDDING_MODEL_NAME",
        )
        emb_api_version = st.text_input(
            "Embedding API Version",
            value=saved.get("api_version_embedding", "2024-08-01-preview"),
            key="input_api_version_embedding",
        )

    with st.sidebar.expander("🔑 Tavily Web Search", expanded=not creds_complete(saved)):
        tavily_key = st.text_input(
            "Tavily API Key",
            value=saved.get("TAVILY_API_KEY", ""),
            type="password",
            placeholder="tvly-••••••••••",
            key="input_TAVILY_API_KEY",
        )

    new_creds = {
        "MODEL_ENDPOINT":           endpoint.strip(),
        "CHAT_MODEL_NAME":          model_name.strip(),
        "AZURE_OPENAI_API_KEY":     api_key.strip(),
        "api_version":              api_version.strip(),
        "MODEL_ENDPOINT_EMBEDDING": emb_endpoint.strip(),
        "EMBEDDING_MODEL_NAME":     emb_model.strip(),
        "api_version_embedding":    emb_api_version.strip(),
        "TAVILY_API_KEY":           tavily_key.strip(),
    }

    col1, col2 = st.sidebar.columns(2)

    with col1:
        save_clicked = st.button("✅ Save & Connect", use_container_width=True, type="primary")

    with col2:
        reset_clicked = st.button("🔄 Reset", use_container_width=True)

    if reset_clicked:
        st.session_state.pop("creds", None)
        st.session_state.pop("graph_ready", None)
        # Clear the @st.cache_resource so graph rebuilds with new creds
        build_graph.clear()
        st.rerun()

    if save_clicked:
        if creds_complete(new_creds):
            st.session_state["creds"] = new_creds
            # Clear cached graph so it rebuilds with the new credentials
            build_graph.clear()
            st.session_state.pop("graph_ready", None)
            st.sidebar.success("✅ Credentials saved!")
            st.rerun()
        else:
            missing = [k for k in REQUIRED_KEYS if not new_creds.get(k, "").strip()]
            st.sidebar.error(f"Missing: {', '.join(missing)}")
            return False

    return creds_complete(st.session_state.get("creds", {}))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Graph builder (cached per unique credential set)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="⚙️ Loading AI models and knowledge bases — this may take a minute…")
def build_graph(
    endpoint: str,
    model_name: str,
    api_key: str,
    api_version: str,
    emb_endpoint: str,
    emb_model: str,
    emb_api_version: str,
    tavily_key: str,
):
    """
    Builds and compiles the full LangGraph multi-agent graph.
    Arguments are the credential values — @st.cache_resource re-runs
    only when they change, otherwise returns the cached graph instantly.
    """
    from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_core.tools import create_retriever_tool, tool
    from langchain_tavily import TavilySearch
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from pydantic import BaseModel, Field
    from typing import Annotated, Sequence, TypedDict, Literal

    # Expose Tavily key to environment so TavilySearchResults can pick it up
    os.environ["TAVILY_API_KEY"] = tavily_key

    # ── LLM & Embeddings ──────────────────────────────────────────────────────
    llm = AzureChatOpenAI(
        azure_deployment=model_name,
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
        temperature=0,
    )
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=emb_endpoint,
        azure_deployment=emb_model,
        openai_api_version=emb_api_version,
        api_key=api_key,
    )

    # ── Knowledge Base 1: Campaign JSON ──────────────────────────────────────
    PERSIST_CAMPAIGNS = "campaigns_db_vectorstore"
    if os.path.exists(PERSIST_CAMPAIGNS):
        vectordb_campaigns = Chroma(
            collection_name="campaigns-db",
            persist_directory=PERSIST_CAMPAIGNS,
            embedding_function=embeddings,
        )
    else:
        with open("campaigns_db.json", "r") as f:
            campaigns_raw = json.load(f)
        campaign_documents = [
            Document(
                page_content="\n".join(f"{k}: {v}" for k, v in c.items()),
                metadata={
                    "source": "campaigns_db.json",
                    "index": i,
                    "industry": c.get("industry", ""),
                    "client": c.get("client", ""),
                    "campaign_name": c.get("campaign_name", ""),
                },
            )
            for i, c in enumerate(campaigns_raw)
        ]
        vectordb_campaigns = Chroma.from_documents(
            documents=campaign_documents,
            collection_name="campaigns-db",
            embedding=embeddings,
            persist_directory=PERSIST_CAMPAIGNS,
        )

    retriever_tool_campaigns = create_retriever_tool(
        retriever=vectordb_campaigns.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 5},
        ),
        name="search_campaigns_db",
        description=(
            "Search and return information about marketing campaigns, advertising strategies, "
            "and media plans. Use this tool when the user asks about finding a campaign, channel "
            "recommendations, campaign performance benchmarks, budget allocation examples, or "
            "advertising case studies."
        ),
    )

    # ── Knowledge Base 2: Research PDFs ──────────────────────────────────────
    PERSIST_PDF = "marketing_pdf_db"
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)

    if os.path.exists(PERSIST_PDF):
        vectordb_pdf = Chroma(
            collection_name="marketing-pdf-docs",
            persist_directory=PERSIST_PDF,
            embedding_function=embeddings,
        )
    else:
        pdf_files = [
            "Content_Effects_Advertising_Marketing.pdf",
            "Digital_Transformation_in_Marketing.pdf",
        ]
        all_pdf_docs = []
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                all_pdf_docs.extend(PyMuPDFLoader(pdf_file).load_and_split())
        vectordb_pdf = Chroma.from_documents(
            documents=text_splitter.split_documents(all_pdf_docs),
            collection_name="marketing-pdf-docs",
            embedding=embeddings,
            persist_directory=PERSIST_PDF,
        )

    retriever_tool_pdf = create_retriever_tool(
        retriever=vectordb_pdf.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 5},
        ),
        name="search_marketing_research",
        description=(
            "Search and return information from marketing and advertising research papers about "
            "content effectiveness, digital transformation in marketing, MarTech, data-driven "
            "marketing, omnichannel strategy, programmatic advertising, and marketing automation."
        ),
    )

    # ── Knowledge Base 3: Marketing Law Web Articles ──────────────────────────
    PERSIST_WEB = "marketing_law_articles_db"
    if os.path.exists(PERSIST_WEB):
        vectordb_web = Chroma(
            collection_name="marketing-web-docs",
            persist_directory=PERSIST_WEB,
            embedding_function=embeddings,
        )
    else:
        marketing_urls = [
            "https://tenthings.blog/2023/06/30/ten-things-marketing-law-basics-for-in-house-counsel/",
            "https://blog.ipleaders.in/marketing-media-consumer-protection-law-india/",
        ]
        docs_list = [item for url in marketing_urls for item in WebBaseLoader(url).load()]
        vectordb_web = Chroma.from_documents(
            documents=text_splitter.split_documents(docs_list),
            collection_name="marketing-web-docs",
            embedding=embeddings,
            persist_directory=PERSIST_WEB,
        )

    retriever_tool_web = create_retriever_tool(
        retriever=vectordb_web.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 5},
        ),
        name="search_marketing_law_articles",
        description=(
            "Search and retrieve legal and compliance-focused insights on marketing, advertising, "
            "media, and consumer protection. Use for marketing law basics, advertising compliance, "
            "truthful and non-misleading claims, endorsements, and consumer protection in India."
        ),
    )

    # ── Knowledge Base 4: SQL Database ───────────────────────────────────────
    if not os.path.exists("DentsuAnalytics.db"):
        os.system('sqlite3 DentsuAnalytics.db ".read dentsu_marketing_advertising_create_script.sql"')

    db = SQLDatabase.from_uri("sqlite:///DentsuAnalytics.db")
    sql_agent_executor = create_sql_agent(llm=llm, db=db, agent_type="tool-calling", verbose=False)

    @tool
    def query_database(question: str) -> str:
        """Query the Dentsu marketing and advertising database using natural language.
        Use this tool when the user asks about offices, employees, clients, campaigns,
        media channels, campaign placements, invoices, billing, revenue, budgets,
        impressions, or any structured data stored in the database."""
        return sql_agent_executor.invoke({"input": question})["output"]

    # ── Web Search Tool ───────────────────────────────────────────────────────
    tavily_search = TavilySearch(max_results=5, search_depth="advanced", include_raw_content=True)

    @tool
    def search_web(query: str) -> str:
        """Search the web for current information, news, recent events, or anything
        not in the knowledge bases. Use for recent platform updates, marketing industry
        news, current regulations, or any live information."""
        response = tavily_search.invoke(query)
        # TavilySearch returns list directly; tavily-python backend may wrap in dict
        results = response if isinstance(response, list) else response.get("results", [])
        parts = [
            f"Title: {r.get('title','')}\nContent: {r.get('content','')}\nSource: {r.get('url','')}"
            for r in results
        ]
        return "\n\n---\n\n".join(parts) if parts else "No results found."

    # ── Guardrail ─────────────────────────────────────────────────────────────
    class MarketingDecision(BaseModel):
        decision: Literal["YES", "NO"] = Field(
            description="YES if the query is marketing/advertising related, NO otherwise"
        )

    GUARDRAIL_PROMPT = """
Classify the user query: is it related to marketing, advertising, media planning, brand strategy,
campaign management, digital marketing, content strategy, programmatic advertising, media buying,
creative strategy, audience targeting, marketing analytics, ROI measurement, social media, SEO/SEM,
influencer marketing, MarTech, CRM, advertising technology, marketing operations, or legal/compliance
topics related to marketing, advertising, media, consumer protection, endorsements, or brand comms?

Also classify as YES for business data questions about clients, employees, offices, invoices,
budgets, or any operational data relevant to a marketing and advertising agency.

Return YES or NO only.
"""

    def check_guardrail(query: str) -> dict:
        result = llm.with_structured_output(MarketingDecision).invoke([
            SystemMessage(content=GUARDRAIL_PROMPT),
            HumanMessage(content=query),
        ])
        if result.decision != "YES":
            return {
                "approved": False,
                "message": (
                    "**Out of Scope** — I can only assist with marketing, advertising, "
                    "and related industry queries. Please ask a marketing or advertising question."
                ),
            }
        return {"approved": True, "message": None}

    # ── State ─────────────────────────────────────────────────────────────────
    class MultiAgentState(TypedDict):
        messages: Annotated[Sequence[object], add_messages]
        next_agent: str

    # ── Supervisor ────────────────────────────────────────────────────────────
    class SupervisorRouting(BaseModel):
        next_agent: Literal[
            "campaign_agent", "research_agent", "legal_agent",
            "web_search_agent", "sql_agent", "FINISH"
        ] = Field(description="The next agent to handle the query.")
        reasoning: str = Field(description="Brief explanation of why this agent was chosen.")

    SUPERVISOR_PROMPT = """
You are the Supervisor Agent for Dentsu's Smart Marketing Buddy.
Analyze the user's question and route it to the most appropriate specialized agent.

AVAILABLE AGENTS:
1. campaign_agent   — Campaign examples, strategies, case studies, channel recommendations (ChromaDB/JSON)
2. research_agent   — Research findings, academic insights, marketing theory (PDFs)
3. legal_agent      — Laws, regulations, compliance, consumer protection (web articles)
4. web_search_agent — Current events, recent news, live platform updates (Tavily)
5. sql_agent        — Operational data: offices, employees, clients, budgets, invoices, impressions (SQLite)
6. FINISH           — Simple definitions or general knowledge answerable directly

Choose the MOST relevant agent. If the query spans multiple domains, pick the primary one.
"""

    def supervisor_node(state: MultiAgentState):
        question = state["messages"][0].content
        routing = llm.with_structured_output(SupervisorRouting).invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=f"User question: {question}"),
        ])
        return {
            "messages": [AIMessage(content=f"[Supervisor] → {routing.next_agent}: {routing.reasoning}")],
            "next_agent": routing.next_agent,
        }

    # ── Sub-agent factory ─────────────────────────────────────────────────────
    def make_retriever_agent(agent_name: str, tool_func):
        def agent_node(state: MultiAgentState):
            question = state["messages"][0].content
            results  = tool_func.invoke(question)
            return {"messages": [AIMessage(content=f"[{agent_name}] Retrieved results:\n\n{results}")]}
        agent_node.__name__ = agent_name
        return agent_node

    campaign_agent_node = make_retriever_agent("campaign_agent", retriever_tool_campaigns)
    research_agent_node = make_retriever_agent("research_agent", retriever_tool_pdf)
    legal_agent_node    = make_retriever_agent("legal_agent",    retriever_tool_web)

    def web_search_agent_node(state: MultiAgentState):
        question = state["messages"][0].content
        return {"messages": [AIMessage(content=f"[web_search_agent] Web results:\n\n{search_web.invoke(question)}")]}

    def sql_agent_node(state: MultiAgentState):
        question = state["messages"][0].content
        return {"messages": [AIMessage(content=f"[sql_agent] Database results:\n\n{query_database.invoke(question)}")]}

    # ── Generate & direct-answer nodes ───────────────────────────────────────
    def generate_node(state: MultiAgentState):
        question = state["messages"][0].content
        context  = "\n\n".join(
            msg.content for msg in state["messages"][1:]
            if hasattr(msg, "content") and msg.content
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a helpful marketing and advertising research assistant for Dentsu. "
             "Use the retrieved information below to answer the question accurately. "
             "Include a disclaimer: 'This information is for research and strategic planning "
             "purposes only and should be validated with current market data before making "
             "investment decisions.' Do NOT fabricate data. If documents don't contain the "
             "answer, say so honestly."),
            ("human", "Retrieved Information:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
        ])
        answer = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": question})
        return {"messages": [AIMessage(content=answer)]}

    def direct_answer_node(state: MultiAgentState):
        question = state["messages"][0].content
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful marketing and advertising assistant for Dentsu. "
                       "Answer the question directly and concisely."),
            ("human", "{question}"),
        ])
        answer = (prompt | llm | StrOutputParser()).invoke({"question": question})
        return {"messages": [AIMessage(content=answer)]}

    # ── Router ────────────────────────────────────────────────────────────────
    def supervisor_router(state: MultiAgentState) -> str:
        next_agent = state.get("next_agent", "FINISH")
        return "direct_answer" if next_agent == "FINISH" else next_agent

    # ── Graph assembly ────────────────────────────────────────────────────────
    workflow = StateGraph(MultiAgentState)
    workflow.add_node("supervisor",       supervisor_node)
    workflow.add_node("campaign_agent",   campaign_agent_node)
    workflow.add_node("research_agent",   research_agent_node)
    workflow.add_node("legal_agent",      legal_agent_node)
    workflow.add_node("web_search_agent", web_search_agent_node)
    workflow.add_node("sql_agent",        sql_agent_node)
    workflow.add_node("generate",         generate_node)
    workflow.add_node("direct_answer",    direct_answer_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges("supervisor", supervisor_router, {
        "campaign_agent":   "campaign_agent",
        "research_agent":   "research_agent",
        "legal_agent":      "legal_agent",
        "web_search_agent": "web_search_agent",
        "sql_agent":        "sql_agent",
        "direct_answer":    "direct_answer",
    })
    for agent in ["campaign_agent", "research_agent", "legal_agent", "web_search_agent", "sql_agent"]:
        workflow.add_edge(agent, "generate")
    workflow.add_edge("generate",      END)
    workflow.add_edge("direct_answer", END)

    return workflow.compile(), check_guardrail


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_header():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #000000 0%, #1A1A2E 50%, #E30613 100%);
                padding: 32px 24px; border-radius: 12px; color: white;
                text-align: center; margin-bottom: 24px;">
        <h1 style="color:white; font-size:2em; margin-bottom:4px;">🧠 Smart Dentsu Buddy</h1>
        <h3 style="color:#FFB4B4; font-weight:400; margin-top:0; font-size:1em;">
            Supervisor-Based Multi-Agent Marketing &amp; Advertising Assistant
        </h3>
    </div>
    """, unsafe_allow_html=True)


def render_agent_roster():
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🤖 Agent Roster")
    agents = [
        ("📁", "Campaign Agent",    "Campaign examples, strategies, benchmarks"),
        ("📄", "Research Agent",    "Marketing research PDFs & academic insights"),
        ("⚖️",  "Legal Agent",       "Compliance, consumer protection, ad law"),
        ("🌐", "Web Search Agent",  "Live internet search via Tavily"),
        ("🗄️",  "SQL Agent",         "Dentsu operational database (Text2SQL)"),
    ]
    for icon, name, desc in agents:
        st.sidebar.markdown(f"**{icon} {name}**  \n<small>{desc}</small>", unsafe_allow_html=True)
        st.sidebar.divider()


def render_examples():
    st.sidebar.markdown("## 💡 Example Questions")
    examples = [
        "Find a successful digital campaign for a CPG brand",
        "What are key findings on content effectiveness in advertising?",
        "Legal basics for marketing law and consumer protection in India?",
        "Latest Google Ads platform updates in 2026?",
        "Which media channel has the most impressions booked?",
        "List all employees in the Mumbai office",
        "What does CPM stand for in digital advertising?",
    ]
    for ex in examples:
        if st.sidebar.button(ex, use_container_width=True):
            st.session_state["pending_question"] = ex


def render_trace(steps: list):
    with st.expander("🔍 Agent Trace", expanded=False):
        for step in steps:
            st.markdown(f"**Step {step['step']}** — `{step['node']}`")
            st.caption(step["detail"])
            st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    render_header()

    # ── Step 1: Collect credentials from sidebar ──────────────────────────────
    creds_ready = render_credentials_form()

    if not creds_ready:
        st.info(
            "👈 **Enter your credentials in the sidebar to get started.**\n\n"
            "Fill in your Azure OpenAI and Tavily API keys, then click **Save & Connect**."
        )
        st.stop()   # Don't render the chat until credentials are in

    # ── Step 2: Build (or retrieve cached) graph using the saved credentials ──
    creds = st.session_state["creds"]
    try:
        graph, check_guardrail = build_graph(
            endpoint     = creds["MODEL_ENDPOINT"],
            model_name   = creds["CHAT_MODEL_NAME"],
            api_key      = creds["AZURE_OPENAI_API_KEY"],
            api_version  = creds["api_version"],
            emb_endpoint = creds["MODEL_ENDPOINT_EMBEDDING"],
            emb_model    = creds["EMBEDDING_MODEL_NAME"],
            emb_api_version = creds["api_version_embedding"],
            tavily_key   = creds["TAVILY_API_KEY"],
        )
    except Exception as e:
        st.error(f"❌ Failed to initialise agents: {e}")
        st.info("Please check your credentials in the sidebar and click **Save & Connect** again.")
        build_graph.clear()
        st.stop()

    # ── Step 3: Render agent roster + examples once connected ─────────────────
    render_agent_roster()
    render_examples()

    st.sidebar.success("🟢 Connected & Ready")

    # ── Step 4: Chat UI ───────────────────────────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle sidebar example button
    if "pending_question" in st.session_state:
        user_input = st.session_state.pop("pending_question")
    else:
        user_input = st.chat_input("Ask me anything about marketing, campaigns, or Dentsu data…")

    if not user_input:
        return

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status   = st.empty()
        answer_p = st.empty()
        trace_steps = []

        # Guardrail
        status.info("🛡️ Checking query scope…")
        guardrail = check_guardrail(user_input)

        if not guardrail["approved"]:
            status.empty()
            answer_p.warning(guardrail["message"])
            st.session_state.messages.append({"role": "assistant", "content": guardrail["message"]})
            return

        # Run graph
        status.info("🤖 Supervisor is routing your query…")
        inputs       = {"messages": [("user", user_input)], "next_agent": ""}
        final_answer = ""
        step         = 0

        for event in graph.stream(inputs):
            for node_name, node_output in event.items():
                step += 1
                msgs   = node_output.get("messages", [])
                detail = ""

                if node_name == "supervisor":
                    status.info(f"🧭 Supervisor routing… (step {step})")
                    detail = msgs[-1].content if msgs else ""
                elif node_name in ("generate", "direct_answer"):
                    status.info("✍️ Writing final answer…")
                    if msgs:
                        final_answer = msgs[-1].content
                        detail = f"{len(final_answer)} chars generated"
                else:
                    status.info(f"🔎 {node_name} searching… (step {step})")
                    detail = f"Retrieved {len(msgs[-1].content)} chars" if msgs else ""

                trace_steps.append({"step": step, "node": node_name, "detail": detail})

        status.empty()

        if final_answer:
            answer_p.markdown(final_answer)
            render_trace(trace_steps)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
        else:
            answer_p.error("No answer generated. Please try again.")


if __name__ == "__main__":
    main()
