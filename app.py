"""
Smart Dentsu Buddy — Multi-Agent Agentic RAG
Streamlit app converted from Jupyter notebook.
"""

import os
import json
import warnings
import streamlit as st

warnings.filterwarnings("ignore")

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Smart Dentsu Buddy",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy imports (inside functions so Streamlit renders while loading) ─────────
@st.cache_resource(show_spinner="Loading AI models and knowledge bases…")
def build_graph():
    """
    Builds and compiles the full LangGraph multi-agent graph.
    Cached so it only runs once per Streamlit session.
    """
    from dotenv import load_dotenv
    from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
    from langchain_core.tools import create_retriever_tool, tool
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from pydantic import BaseModel, Field
    from typing import Annotated, Sequence, TypedDict, Literal

    load_dotenv()

    ENDPOINT              = os.environ["MODEL_ENDPOINT"]
    MODEL_NAME            = os.environ["CHAT_MODEL_NAME"]
    API_KEY               = os.environ["AZURE_OPENAI_API_KEY"]
    API_VERSION           = os.environ["api_version"]
    EMBEDDINGS_MODEL      = os.environ["EMBEDDING_MODEL_NAME"]
    EMBEDDINGS_ENDPOINT   = os.environ["MODEL_ENDPOINT_EMBEDDING"]
    API_VERSION_EMBEDDING = os.environ["api_version_embedding"]
    TAVILY_KEY            = os.environ["TAVILY_API_KEY"]

    os.environ["ANONYMIZED_TELEMETRY"] = "False"

    # ── LLM & Embeddings ──────────────────────────────────────────────────────
    llm = AzureChatOpenAI(
        azure_deployment=MODEL_NAME,
        api_version=API_VERSION,
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
        temperature=0,
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=EMBEDDINGS_ENDPOINT,
        azure_deployment=EMBEDDINGS_MODEL,
        openai_api_version=API_VERSION_EMBEDDING,
        api_key=API_KEY,
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

    retriever_campaigns = vectordb_campaigns.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5, "k": 5},
    )
    retriever_tool_campaigns = create_retriever_tool(
        retriever=retriever_campaigns,
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
                docs = PyMuPDFLoader(pdf_file).load_and_split()
                all_pdf_docs.extend(docs)

        pdf_texts = text_splitter.split_documents(all_pdf_docs)
        vectordb_pdf = Chroma.from_documents(
            documents=pdf_texts,
            collection_name="marketing-pdf-docs",
            embedding=embeddings,
            persist_directory=PERSIST_PDF,
        )

    retriever_pdf = vectordb_pdf.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5, "k": 5},
    )
    retriever_tool_pdf = create_retriever_tool(
        retriever=retriever_pdf,
        name="search_marketing_research",
        description=(
            "Search and return information from marketing and advertising research papers about "
            "content effectiveness in advertising, creative strategy, audience engagement, digital "
            "transformation in marketing, MarTech, data-driven marketing, omnichannel strategy, "
            "programmatic advertising, and marketing automation."
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
        docs = [WebBaseLoader(url).load() for url in marketing_urls]
        docs_list = [item for sublist in docs for item in sublist]
        web_texts = text_splitter.split_documents(docs_list)
        vectordb_web = Chroma.from_documents(
            documents=web_texts,
            collection_name="marketing-web-docs",
            embedding=embeddings,
            persist_directory=PERSIST_WEB,
        )

    retriever_web = vectordb_web.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5, "k": 5},
    )
    retriever_tool_web = create_retriever_tool(
        retriever=retriever_web,
        name="search_marketing_law_articles",
        description=(
            "Search and retrieve legal and compliance-focused insights on marketing, advertising, "
            "media, and consumer protection topics. Use for questions related to marketing law basics, "
            "advertising compliance, truthful and non-misleading claims, endorsements, and consumer "
            "protection considerations in India."
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
        result = sql_agent_executor.invoke({"input": question})
        return result["output"]

    # ── Web Search Tool ───────────────────────────────────────────────────────
    tavily_search = TavilySearchResults(max_results=5, search_depth="advanced", include_raw_content=True)

    @tool
    def search_web(query: str) -> str:
        """Search the web for current information, news, recent events, or any general
        knowledge question not in the knowledge bases. Use for recent platform updates,
        marketing industry news, current regulations, or anything not in the other sources."""
        results = tavily_search.invoke(query)
        parts = [
            f"Title: {r.get('title', '')}\nContent: {r.get('content', '')}\nSource: {r.get('url', '')}"
            for r in results
        ]
        return "\n\n---\n\n".join(parts) if parts else "No results found."

    # ── Guardrail ─────────────────────────────────────────────────────────────
    class MarketingDecision(BaseModel):
        decision: Literal["YES", "NO"] = Field(
            description="YES if the query is marketing/advertising related, NO otherwise"
        )

    GUARDRAIL_PROMPT = """
Classify the following user query according to whether it is related to marketing, advertising,
media planning, brand strategy, campaign management, digital marketing, content strategy,
programmatic advertising, media buying, creative strategy, audience targeting, marketing analytics,
ROI measurement, social media marketing, SEO/SEM, influencer marketing, MarTech, CRM,
advertising technology, marketing operations, or legal and compliance topics related to marketing,
advertising, media, consumer protection, misleading claims, endorsements, disclosures, promotions,
and brand communications.

Also classify as YES if the query is about business data, clients, employees, offices, invoices,
budgets, or any operational data relevant to a marketing and advertising agency.

Return either YES or NO.
"""

    def check_guardrail(query: str) -> dict:
        messages = [SystemMessage(content=GUARDRAIL_PROMPT), HumanMessage(content=query)]
        classifier = llm.with_structured_output(MarketingDecision)
        result = classifier.invoke(messages)
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
        messages: Annotated[Sequence[BaseMessage], add_messages]
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
4. web_search_agent — Current events, recent news, platform updates (live Tavily search)
5. sql_agent        — Operational data: offices, employees, clients, budgets, invoices, impressions (SQLite)
6. FINISH           — Simple definitions or general knowledge you can answer directly

Choose the MOST relevant agent. If the query spans multiple domains, pick the primary one.
"""

    def supervisor_node(state: MultiAgentState):
        question = state["messages"][0].content
        router_llm = llm.with_structured_output(SupervisorRouting)
        routing = router_llm.invoke([
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
            results = tool_func.invoke(question)
            return {"messages": [AIMessage(content=f"[{agent_name}] Retrieved results:\n\n{results}")]}
        agent_node.__name__ = agent_name
        return agent_node

    campaign_agent_node = make_retriever_agent("campaign_agent", retriever_tool_campaigns)
    research_agent_node = make_retriever_agent("research_agent", retriever_tool_pdf)
    legal_agent_node    = make_retriever_agent("legal_agent",    retriever_tool_web)

    def web_search_agent_node(state: MultiAgentState):
        question = state["messages"][0].content
        results  = search_web.invoke(question)
        return {"messages": [AIMessage(content=f"[web_search_agent] Web results:\n\n{results}")]}

    def sql_agent_node(state: MultiAgentState):
        question = state["messages"][0].content
        results  = query_database.invoke(question)
        return {"messages": [AIMessage(content=f"[sql_agent] Database results:\n\n{results}")]}

    # ── Generate node ─────────────────────────────────────────────────────────
    def generate_node(state: MultiAgentState):
        question = state["messages"][0].content
        context  = "\n\n".join(
            msg.content for msg in state["messages"][1:] if hasattr(msg, "content") and msg.content
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
                       "Answer the following question directly and concisely."),
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

    graph = workflow.compile()

    return graph, check_guardrail


# ── UI ─────────────────────────────────────────────────────────────────────────

def render_header():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #000000 0%, #1A1A2E 50%, #E30613 100%);
                padding: 32px 24px; border-radius: 12px; color: white; text-align: center; margin-bottom: 24px;">
        <h1 style="color: white; font-size: 2em; margin-bottom: 4px;">🧠 Smart Dentsu Buddy</h1>
        <h3 style="color: #FFB4B4; font-weight: 400; margin-top: 0; font-size: 1em;">
            Supervisor-Based Multi-Agent Marketing &amp; Advertising Assistant
        </h3>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🤖 Agent Roster")
        agents = [
            ("📁", "Campaign Agent",    "Campaign examples, strategies, benchmarks"),
            ("📄", "Research Agent",    "Marketing research PDFs & academic insights"),
            ("⚖️",  "Legal Agent",       "Compliance, consumer protection, ad law"),
            ("🌐", "Web Search Agent",  "Live internet search via Tavily"),
            ("🗄️",  "SQL Agent",         "Dentsu operational database (Text2SQL)"),
        ]
        for icon, name, desc in agents:
            st.markdown(f"**{icon} {name}**  \n<small>{desc}</small>", unsafe_allow_html=True)
            st.divider()

        st.markdown("## 💡 Example Questions")
        examples = [
            "Find a successful digital campaign for a CPG brand",
            "What are key findings on content effectiveness in advertising?",
            "What are the legal basics for marketing law and consumer protection in India?",
            "Latest Google Ads platform updates in 2026?",
            "Which media channel has the most impressions booked?",
            "List all employees in the Mumbai office",
            "What does CPM stand for in digital advertising?",
        ]
        for ex in examples:
            if st.button(ex, use_container_width=True):
                st.session_state["pending_question"] = ex


def render_trace(steps: list):
    with st.expander("🔍 Agent Trace", expanded=False):
        for step in steps:
            st.markdown(f"**Step {step['step']}** — `{step['node']}`")
            st.caption(step["detail"])
            st.divider()


def main():
    render_header()
    render_sidebar()

    # Load graph once
    graph, check_guardrail = build_graph()

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle sidebar example button clicks
    if "pending_question" in st.session_state:
        user_input = st.session_state.pop("pending_question")
    else:
        user_input = st.chat_input("Ask me anything about marketing, campaigns, or Dentsu data…")

    if user_input:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            status_placeholder = st.empty()
            answer_placeholder  = st.empty()
            trace_steps = []

            # Guardrail check
            status_placeholder.info("🛡️ Checking query scope…")
            guardrail = check_guardrail(user_input)

            if not guardrail["approved"]:
                status_placeholder.empty()
                answer_placeholder.warning(guardrail["message"])
                st.session_state.messages.append({"role": "assistant", "content": guardrail["message"]})
                return

            # Run agent graph
            status_placeholder.info("🤖 Supervisor is routing your query…")
            inputs = {"messages": [("user", user_input)], "next_agent": ""}
            final_answer = ""
            step = 0

            for event in graph.stream(inputs):
                for node_name, node_output in event.items():
                    step += 1
                    msgs = node_output.get("messages", [])
                    detail = ""

                    if node_name == "supervisor":
                        status_placeholder.info(f"🧭 Supervisor routing… (step {step})")
                        if msgs:
                            detail = msgs[-1].content
                    elif node_name in ("generate", "direct_answer"):
                        status_placeholder.info("✍️ Writing final answer…")
                        if msgs:
                            final_answer = msgs[-1].content
                            detail = f"{len(final_answer)} chars generated"
                    else:
                        status_placeholder.info(f"🔎 {node_name} is searching… (step {step})")
                        if msgs:
                            detail = f"Retrieved {len(msgs[-1].content)} chars"

                    trace_steps.append({"step": step, "node": node_name, "detail": detail})

            status_placeholder.empty()

            if final_answer:
                answer_placeholder.markdown(final_answer)
                render_trace(trace_steps)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            else:
                answer_placeholder.error("No answer generated. Please try again.")


if __name__ == "__main__":
    main()
