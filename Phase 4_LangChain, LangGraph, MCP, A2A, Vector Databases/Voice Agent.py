# production_voice_agent.py

import asyncio
import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Async HTTP for API calls
import aiohttp
import aiofiles

# LangChain/LangGraph
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
import operator

load_dotenv()


# ============= PART 1: MCP SERVERS (Data Access) =============
# Simplified MCP from Example 4.3

class MCPServer:
    """MCP Server providing data/tools to agents."""

    def __init__(self, name: str):
        self.name = name
        self.resources = {}
        self.tools = {}

    def add_tool(self, name: str, description: str, handler):
        self.tools[name] = {"description": description, "handler": handler}


    async def call_tool(self, name: str, **kwargs):
        if name not in self.tools:
            return f"Error: Tool '{name}' not found"
        return self.tools[name]["handler"](**kwargs)


# Create MCP servers for different data sources
weather_mcp = MCPServer("weather_mcp")
email_mcp = MCPServer("email_mcp")
search_mcp = MCPServer("search_mcp")


# Weather MCP tools
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    weather_data = {
        "tokyo": "72°F, sunny, humidity 45%",
        "london": "65°F, cloudy, chance of rain 30%",
        "new york": "80°F, humid, feels like 85°F"
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


weather_mcp.add_tool("get_weather", "Get current weather for a city", get_weather)


# Email MCP tools
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    print(f"\n📧 [EMAIL SENT]")
    print(f"   To: {to}")
    print(f"   Subject: {subject}")
    print(f"   Body: {body[:100]}...")
    print(f" Body: {body[-100:]}...")
    return f"Email sent successfully to {to}"


email_mcp.add_tool("send_email", "Send an email to a recipient", send_email)


# Search MCP tools
def search_web(query: str, max_results: int = 3) -> str:
    """Search the web for information."""
    results = [
        f"Result 1 for '{query}': Important information found...",
        f"Result 2 for '{query}': Additional details...",
        f"Result 3 for '{query}': Further reading..."
        f"Result 4 for '{query}': Further reading..."
    ]
    return "\n".join(results[:max_results])


search_mcp.add_tool("search_web", "Search the web for information", search_web)


# ============= PART 2: A2A AGENTS (Specialized Agents) =============

class AgentCard:
    """Agent's identification card."""

    def __init__(self, name: str, skills: List[str], endpoint: str = "local"):
        self.name = name
        self.skills = skills
        self.endpoint = endpoint


class BaseAgent:
    """Base class for all A2A agents."""

    def __init__(self, name: str, skills: List[str]):
        self.card = AgentCard(name, skills)
        self.other_agents = {}
        self.mcp_servers = {}

    def register_agent(self, agent):
        self.other_agents[agent.card.name] = agent

    def connect_mcp(self, server: MCPServer):
        self.mcp_servers[server.name] = server

    async def send_message(self, recipient_name: str, content: str) -> str:
        if recipient_name not in self.other_agents:
            return f"Error: Agent '{recipient_name}' not found"

        recipient = self.other_agents[recipient_name]
        print(f"  🔄 {self.card.name} → {recipient_name}: {content[:50]}...")
        return await recipient.receive_message(content, self.card.name)

    async def receive_message(self, content: str, sender: str) -> str:
        print(f"  📬 {self.card.name} received from {sender}: {content[:50]}...")
        return await self.handle_message(content, sender)

    async def handle_message(self, content: str, sender: str) -> str:
        """Override in subclass."""
        return f"{self.card.name} received: {content}"


    async def call_mcp(self, server_name: str, tool_name: str, **kwargs) -> str:
        if server_name not in self.mcp_servers:
            return f"Error: MCP server '{server_name}' not connected"
        return await self.mcp_servers[server_name].call_tool(tool_name, **kwargs)


class WeatherAgent(BaseAgent):
    """Specialized agent for weather-related tasks."""

    def __init__(self):
        super().__init__("WeatherAgent", ["get_weather", "weather_forecast"])

    async def handle_message(self, content: str, sender: str) -> str:
        # Extract city from message using simple pattern
        city_match = re.search(r'weather in (\w+)', content, re.IGNORECASE)
        if city_match:
            city = city_match.group(1)
            result = await self.call_mcp("weather_mcp", "get_weather", city=city)
            return f"Weather in {city}: {result}"
        return "I need a city name to get weather. Example: 'weather in Tokyo'"


class EmailAgent(BaseAgent):
    """Specialized agent for email-related tasks."""

    def __init__(self):
        super().__init__("EmailAgent", ["send_email", "read_email"])

    async def handle_message(self, content: str, sender: str) -> str:
        # Extract email content
        to_match = re.search(r'to (\S+@\S+)', content)
        subject_match = re.search(r'subject (.+?)(?=body|$)', content, re.IGNORECASE)

        to = to_match.group(1) if to_match else "user@example.com"
        subject = subject_match.group(1).strip() if subject_match else "Update"

        return await self.call_mcp("email_mcp", "send_email", to=to, subject=subject, body=content)


# ============= PART 3: LANGGRAPH STATE & AGENT =============

class VoiceAgentState(TypedDict):
    """State maintained across agent steps."""
    user_input: str
    transcribed_text: str
    intent: str
    messages: Annotated[List, operator.add]
    tool_calls: List[Dict]
    final_response: str
    streaming_buffer: str
    current_step: str


def create_voice_agent():
    """Create a LangGraph agent for voice interactions."""

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, streaming=True)

    # Step 1: Detect intent
    def detect_intent(state: VoiceAgentState) -> VoiceAgentState:
        print(f"\n🎯 [INTENT DETECTION] Analyzing: {state['user_input']}")

        text = state['user_input'].lower()

        if 'weather' in text:
            state['intent'] = 'weather'
        elif 'email' in text or 'send' in text:
            state['intent'] = 'email'
        elif 'search' in text:
            state['intent'] = 'search'
        else:
            state['intent'] = 'chat'


        state['current_step'] = 'process'
        state['messages'].append({"role": "system", "content": f"Intent detected: {state['intent']}"})
        state['tool_calls'].append({"step": "detect_intent", "intent": state['intent']})
        state['final_response'] = f"Intent detected: {state['intent']}"

        print(f"   Intent: {state['intent']}")
        return state

    # Step 2: Process based on intent
    async def process_intent(state: VoiceAgentState) -> VoiceAgentState:
        print(f"\n⚙️ [PROCESSING] Executing {state['intent']} intent")

        if state['intent'] == 'weather':
            # Extract city
            city_match = re.search(r'weather in (\w+)', state['user_input'], re.IGNORECASE)
            city = city_match.group(1) if city_match else "Tokyo"


            result = get_weather(city)
            state['final_response'] = f"The weather in {city} is {result}"

        elif state['intent'] == 'email':
            result = send_email(
                to="user@example.com",
                subject="Response to your query",
                body=state['user_input'],
                reply_to=None,

            )
            state['final_response'] = result

        elif state['intent'] == 'search':
            query = state['user_input'].replace('search', '').replace('for', '').strip()
            result = search_web(query)
            state['final_response'] = f"Search results: {result}"

        elif state['intent'] == 'chat':
            query = state['user_input'].replace('search', '').replace('for', '').strip()
            result = search_web(query)
            state['final_response'] = f"Search results: {result}"


        else:
            # Chat - use LLM
            response = llm.invoke(state['user_input'])
            state['final_response'] = response.content

        state['current_step'] = 'stream'
        return state

    # Step 3: Stream response
    async def stream_response(state: VoiceAgentState) -> VoiceAgentState:
        print(f"\n🔊 [STREAMING] Response:")
        print("-" * 40)
        print(f"   {state['final_response'][:100]}...")

        # Simulate streaming word by word
        words = state['final_response'].split()
        for i, word in enumerate(words):
            print(word, end=' ', flush=True)
            await asyncio.sleep(0.05)  # Simulate streaming delay
            state['streaming_buffer'] += word + " "
            state['tool_calls'].append({"step": "stream_response", "word": word})
            state['tool_calls'].append({"step": "process_intent", "word": word})

        print("\n" + "-" * 40)
        state['current_step'] = 'complete'
        return state

    # Build the graph
    workflow = StateGraph(VoiceAgentState)

    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("process_intent", process_intent)
    workflow.add_node("stream_response", stream_response)

    workflow.set_entry_point("detect_intent")
    workflow.add_edge("detect_intent", "process_intent")
    workflow.add_edge("process_intent", "stream_response")
    workflow.add_edge("stream_response", END)
    workflow.add_edge("stream_response", "process_intent")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============= PART 4: ORCHESTRATOR (A2A) =============

class VoiceOrchestrator(BaseAgent):
    """
    Main orchestrator that coordinates between:
    - Voice input/output
    - LangGraph agent
    - Specialized A2A agents
    - MCP data sources
    """

    def __init__(self):
        super().__init__("VoiceOrchestrator", ["voice", "orchestration", "routing"])
        self.langgraph_agent = None
        self.conversation_history = []

    def set_langgraph_agent(self, agent):
        self.langgraph_agent = agent

    async def process_voice_command(self, voice_text: str) -> str:
        """Main entry point for voice commands."""

        print(f"\n{'=' * 60}")
        print(f"🎤 VOICE COMMAND: {voice_text}")

        # Store in history
        self.conversation_history.append({"role": "user", "content": voice_text})

        # Check if we should delegate to specialized agents
        delegated = await self.try_delegate(voice_text)
        if delegated:
            return delegated

        # Otherwise use LangGraph agent
        if self.langgraph_agent:
            result = await self.run_langgraph_agent(voice_text)
            self.conversation_history.append({"role": "assistant", "content": result})
            return result

        return "I'm not sure how to help with that."

    async def try_delegate(self, text: str) -> Optional[str]:
        """Try to delegate to specialized agents based on intent."""
        text_lower = text.lower()

        if 'weather' in text_lower:
            print(f"\n🔀 Delegating to WeatherAgent...")
            return await self.send_message("WeatherAgent", text)

        elif 'email' in text_lower or 'send' in text_lower:
            print(f"\n🔀 Delegating to EmailAgent...")
            return await self.send_message("EmailAgent", text)

        return None

    async def run_langgraph_agent(self, text: str) -> str:
        """Run the LangGraph agent for complex tasks."""
        print(f"\n🤖 Running LangGraph agent...")
        print(f"   Input: {text}")
        print(f"   History:")


        print(f"      {'-' * 20}")
        for i, msg in enumerate(self.conversation_history):
            print(f"      {i+1}. {msg['role'].upper()}: {msg['content']}")
        print(f"      {'-' * 20}")




        initial_state = {
            "user_input": text,
            "transcribed_text": text,
            "intent": "",
            "messages": [],
            "tool_calls": [],
            "final_response": "",
            "streaming_buffer": "",
            "current_step": "detect_intent"

        }

        # Run the graph
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Note: In production, you'd await the graph invocation
        # For this demo, we'll simulate
        final_state = initial_state
        final_state['final_response'] = f"Processed: {text}"

        return final_state['final_response']

    async def handle_message(self, content: str, sender: str) -> str:
        """Handle incoming messages from other agents."""
        return await self.process_voice_command(content)


# ============= PART 5: VOICE STREAMING MANAGER =============

class VoiceStreamingManager:
    """
    Manages streaming responses for voice output.
    Simulates TTS (Text-to-Speech) word by word.
    """

    def __init__(self):
        self.buffer = ""
        self.is_speaking = False

    async def stream_to_voice(self, text: str, tts_callback=None):
        """
        Stream text to voice output word by word.
        In production, tts_callback would call ElevenLabs/OpenAI TTS.
        """
        words = text.split()

        print(f"\n🗣️ [VOICE OUTPUT]")
        print("-" * 40)

        for i, word in enumerate(words):
            # Simulate TTS latency
            await asyncio.sleep(0.08)

            # Print to console (simulates speaking)
            print(word, end=' ', flush=True)

            # Call TTS callback if provided
            if tts_callback:
                await tts_callback(word)

        print("\n" + "-" * 40)
        return True


# ============= PART 6: PRODUCTION VOICE AGENT =============

class ProductionVoiceAgent:
    """
    Complete production-ready voice agent combining:
    - Phase 1: Error handling, conditionals
    - Phase 2: Async, streaming, API calls
    - Phase 3: Tools, state management
    - Phase 4: LangGraph, MCP, A2A
    """

    def __init__(self):
        print("\n" + "=" * 60)
        print("🚀 INITIALIZING PRODUCTION VOICE AGENT")
        print("=" * 60)

        # Initialize components
        self.voice_streamer = VoiceStreamingManager()
        self.orchestrator = VoiceOrchestrator()
        self.weather_agent = WeatherAgent()

        # Create and connect specialized agents
        print("\n📡 CONNECTING A2A AGENTS:")
        self.weather_agent = WeatherAgent()
        self.email_agent = EmailAgent()

        self.orchestrator.register_agent(self.weather_agent)
        self.orchestrator.register_agent(self.email_agent)

        # Connect MCP servers
        print("\n🔌 CONNECTING MCP SERVERS:")
        self.orchestrator.connect_mcp(weather_mcp)
        self.orchestrator.connect_mcp(email_mcp)
        self.orchestrator.connect_mcp(search_mcp)
        self.weather_agent.connect_mcp(weather_mcp)
        self.email_agent.connect_mcp(email_mcp)

        # Create LangGraph agent
        print("\n🧠 CREATING LANGGRAPH AGENT:")
        self.langgraph_agent = create_voice_agent()
        self.orchestrator.set_langgraph_agent(self.langgraph_agent)

        # Conversation history
        self.conversation_id = str(uuid.uuid4())
        self.history = []

        print("\n✅ Voice Agent Ready!")


    async def process_voice_input(self, transcribed_text: str) -> str:
        """
        Process voice input and return streaming response.
        This is the main method called by your voice interface.
        """
        try:
            # Step 1: Process through orchestrator
            response = await self.orchestrator.process_voice_command(transcribed_text)

            # Step 2: Stream to voice
            await self.voice_streamer.stream_to_voice(response)

            # Step 3: Store in history
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "user": transcribed_text,
                "agent": response
            })

            return response

        except Exception as e:
            error_msg = f"Error processing voice command: {str(e)}"
            print(f"❌ {error_msg}")
            return "Sorry, I encountered an error. Please try again."

    async def run_interactive_session(self):
        """Run an interactive voice session (simulated voice input)."""

        print("\n" + "=" * 60)
        print("🎙️ VOICE AGENT INTERACTIVE SESSION")
        print("=" * 60)
        print("\nType your commands (or 'quit' to exit):")
        print("Examples:")
        print("  • 'What's the weather in Tokyo?'")
        print("  • 'Send an email to boss@company.com'")
        print("  • 'Search for AI news'")
        print("-" * 60)

        while True:
            user_input = input("\n🎤 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            # Process the command
            await self.process_voice_input(user_input)

    def get_conversation_history(self) -> List[Dict]:
        """Get full conversation history."""
        return self.history

    def get_stats(self) -> Dict:
        """Get agent statistics."""
        return {
            "conversation_id": self.conversation_id,
            "total_interactions": len(self.history),
            "available_agents": [self.orchestrator.card.name, self.weather_agent.card.name, self.email_agent.card.name],
            "connected_mcp_servers": ["weather_mcp", "email_mcp", "search_mcp"]
        }


# ============= MAIN ENTRY POINT =============

async def main():
    """Main entry point for the voice agent."""

    # Create the agent
    agent = ProductionVoiceAgent()

    # Show stats
    print("\n📊 AGENT STATS:")
    stats = agent.get_stats()
    print(f"   Conversation ID: {stats['conversation_id']}")
    print(f"   Available Agents: {', '.join(stats['available_agents'])}")
    print(f"   MCP Servers: {', '.join(stats['connected_mcp_servers'])}")
    print(f"   Total Interactions: {stats['total_interactions']}")
    print("=" * 60)

    # Run interactive session
    await agent.run_interactive_session()

    # Show final stats
    print("\n" + "=" * 60)
    print("📊 SESSION SUMMARY")
    print("=" * 60)
    history = agent.get_conversation_history()
    print(f"   Total interactions: {len(history)}")
    print(f"   Conversation ID: {stats['conversation_id']}")
    print(f"   Available Agents: {', '.join(stats['available_agents'])}")

    if history:
        print("\n   Last interaction:")
        last = history[-1]
        print(f"     User: {last['user'][:50]}...")
        print(f"     Agent: {last['agent'][:50]}...")
        print("=" * 60)
        print("   Conversation History:")
        for i, interaction in enumerate(history):
            print(f"   {i+1}. User: {interaction['user'][:50]}...")
            print(f"        Agent: {interaction['agent'][:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
