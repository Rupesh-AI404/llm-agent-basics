# 4.1_basic_langchain.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# ============= STEP 1: DEFINE TOOLS (using LangChain's @tool) =============
# This is similar to our Phase 3 decorator, but LangChain's version
# has more features built-in

@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a specific city.
    Returns temperature and conditions.
    """
    # Mock weather data
    weather_data = {
        "tokyo": "72°F, sunny",
        "london": "65°F, cloudy",
        "new york": "80°F, humid",
        "kathmandu": "68°F, clear"
    }
    city_lower = city.lower()
    return weather_data.get(city_lower, f"Weather data not available for {city}")


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============= STEP 2: CREATE THE LLM =============
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ============= STEP 3: CREATE THE PROMPT TEMPLATE =============
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to tools."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")  # Where LangChain stores intermediate steps
])

# ============= STEP 4: CREATE THE AGENT =============
tools = [get_weather, get_current_time]

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# ============= STEP 5: CREATE THE AGENT EXECUTOR =============
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # Shows you what the agent is thinking
    max_iterations=3  # Prevent infinite loops
)

# ============= STEP 6: RUN THE AGENT =============
if __name__ == "__main__":
    print("=" * 50)
    print("LANGCHAIN AGENT DEMO")
    print("=" * 50)

    # Test 1: Weather question
    print("\n📝 User: What's the weather in Tokyo?")
    result = agent_executor.invoke({"input": "What's the weather in Tokyo?"})
    print(f"🤖 Agent: {result['output']}")

    print("\n" + "-" * 30)

    # Test 2: Time question
    print("\n📝 User: What time is it right now?")
    result = agent_executor.invoke({"input": "What time is it right now?"})
    print(f"🤖 Agent: {result['output']}")