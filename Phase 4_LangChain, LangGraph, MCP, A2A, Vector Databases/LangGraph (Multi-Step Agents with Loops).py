# 4.2_langgraph_basic.py

import os
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
import operator

load_dotenv()

# ============= STEP 1: DEFINE OUR TOOLS =============
@tool
def search_web(query: str) -> str:
    """
    Search the web for information on a topic.
    Returns search results as text.
    """
    # Mock search results (in production, use SerpAPI or similar)
    mock_results = {
        "AI trends": "Top AI trends in 2025: 1. Agentic AI systems that autonomously complete tasks. 2. Multi-modal models combining text, image, and video. 3. Smaller, efficient models running on edge devices.",
        "machine learning": "Key ML breakthroughs: 1. Test-time training for rapid adaptation. 2. Mixture of Experts for efficiency. 3. Self-supervised learning reducing need for labeled data.",
        "LLM agents": "LLM agents are evolving from simple chatbots to complex reasoning systems with memory, planning, and tool use capabilities."
    }

    for key, value in mock_results.items():
        if key.lower() in query.lower():
            return value

    return f"Search results for '{query}': Found relevant information about AI and machine learning advancements."


@tool
def read_article(url: str) -> str:
    """
    Read and summarize an article from a URL.
    """
    # Mock article reading
    return f"Article summary from {url}: This article discusses recent advances in AI agents, including improved reasoning, longer context windows, and better tool integration."


@tool
def write_summary(content: str) -> str:
    """
    Write a final summary based on researched information.
    """
    return f"FINAL SUMMARY:\n{content}\n\n[Summary written successfully]"


# ============= STEP 2: DEFINE THE STATE =============
class ResearchState(TypedDict):
    """State that persists across agent steps."""
    query: str  # Original user question
    search_results: List[str]  # Accumulated search results
    articles_read: List[str]  # URLs that have been read
    current_step: str  # What step we're on
    iterations: int  # How many loops so far
    final_answer: str  # Final response to user
    messages: Annotated[List, operator.add]  # Conversation history


# ============= STEP 3: DEFINE THE NODES (each step) =============
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)


def search_node(state: ResearchState) -> ResearchState:
    """Node 1: Search for information."""
    print(f"\n🔍 [SEARCH] Searching for: {state['query']}")

    # Perform search
    search_result = search_web.invoke({"query": state['query']})

    # Update state
    state['search_results'].append(search_result)
    state['current_step'] = "analyze"
    state['iterations'] += 1

    print(f"   Found: {search_result[:100]}...")
    return state


def analyze_node(state: ResearchState) -> ResearchState:
    """Node 2: Analyze if we need more information."""
    print(f"\n🧠 [ANALYZE] Analyzing research depth...")

    # Use LLM to decide if we have enough information
    prompt = f"""
    User query: {state['query']}

    Search results so far:
    {chr(10).join(state['search_results'])}

    Have we gathered enough information to answer thoroughly?
    Answer with ONLY "ENOUGH" or "NEED_MORE".
    """

    response = llm.invoke(prompt)
    decision = response.content.strip().upper()

    if "NEED_MORE" in decision and state['iterations'] < 3:
        print(f"   Decision: Need more information (iteration {state['iterations']}/3)")
        state['current_step'] = "search"
        # Refine query for next search
        state['query'] = f"{state['query']} latest developments"
    else:
        print(f"   Decision: Enough information gathered")
        state['current_step'] = "synthesize"

    return state


def read_node(state: ResearchState) -> ResearchState:
    """Node 3: Read and extract details from sources."""
    print(f"\n📖 [READ] Reading detailed sources...")

    # In production, you'd extract URLs from search results
    mock_url = "https://example.com/ai-article"
    if mock_url not in state['articles_read']:
        article_content = read_article.invoke({"url": mock_url})
        state['articles_read'].append(mock_url)
        state['search_results'].append(f"Details from article: {article_content}")
        print(f"   Read and extracted insights")

    state['current_step'] = "analyze"
    return state


def synthesize_node(state: ResearchState) -> ResearchState:
    """Node 4: Synthesize all information into final answer."""
    print(f"\n📝 [SYNTHESIZE] Creating final answer...")

    prompt = f"""
    User asked: {state['query']}

    Research gathered:
    {chr(10).join(state['search_results'])}

    Please provide a comprehensive, well-structured answer based on this research.
    Include key insights and cite the information where appropriate.
    """

    response = llm.invoke(prompt)
    state['final_answer'] = response.content
    state['current_step'] = "end"

    print(f"   Final answer created ({len(state['final_answer'])} characters)")
    return state


# ============= STEP 4: BUILD THE GRAPH =============
def create_research_agent():
    """Build the LangGraph workflow."""

    # Create the graph
    workflow = StateGraph(ResearchState)

    # Add nodes (steps)
    workflow.add_node("search", search_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("read", read_node)
    workflow.add_node("synthesize", synthesize_node)

    # Set the entry point
    workflow.set_entry_point("search")

    # Add edges (transitions between nodes)
    workflow.add_edge("search", "analyze")
    workflow.add_conditional_edges(
        "analyze",
        lambda state: state['current_step'],
        {
            "search": "search",  # Loop back to search
            "read": "read",  # Go to read before analyzing again
            "synthesize": "synthesize",  # Go to final synthesis
            "end": END  # End the workflow
        }
    )
    workflow.add_edge("read", "analyze")
    workflow.add_edge("synthesize", END)

    # Add memory to persist state
    memory = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=memory)

    return app


# ============= STEP 5: RUN THE AGENT =============
def run_research_agent(query: str):
    """Run the multi-step research agent."""

    print("=" * 60)
    print("LANGGRAPH MULTI-STEP RESEARCH AGENT")
    print("=" * 60)
    print(f"\n📝 User Query: {query}\n")

    # Initialize state
    initial_state = {
        "query": query,
        "search_results": [],
        "articles_read": [],
        "current_step": "search",
        "iterations": 0,
        "final_answer": "",
        "messages": []
    }

    # Create and run the agent
    app = create_research_agent()

    # Run with config (thread_id for conversation persistence)
    config = {"configurable": {"thread_id": "research_session_1"}}

    final_state = app.invoke(initial_state, config)

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(final_state['final_answer'])

    print("\n" + "=" * 60)
    print(f"📊 STATISTICS:")
    print(f"   Iterations: {final_state['iterations']}")
    print(f"   Sources found: {len(final_state['search_results'])}")
    print(f"   Articles read: {len(final_state['articles_read'])}")

    return final_state


if __name__ == "__main__":
    # Run a research task
    result = run_research_agent("What are the latest trends in AI agents?")