# 4.4_a2a_basic.py

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


# ============= CORE A2A TYPES =============

class TaskState(Enum):
    """State of a task in A2A."""
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class AgentCard:
    """An agent's ID card - tells other agents who they are."""
    name: str
    description: str
    version: str
    skills: List[str]  # What this agent can do
    endpoint: str = "http://localhost:8000"  # Where to reach this agent

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "skills": self.skills,
            "endpoint": self.endpoint
        }


@dataclass
class Message:
    """A message sent between agents."""
    message_id: str
    sender: str  # Agent name
    recipient: str  # Agent name
    content: str
    task_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "task_id": self.task_id,
            "timestamp": self.timestamp
        }


@dataclass
class Task:
    """A unit of work for an agent."""
    task_id: str
    type: str  # e.g., "weather", "email", "search"
    parameters: Dict[str, Any]
    state: TaskState = TaskState.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "type": self.type,
            "parameters": self.parameters,
            "state": self.state.value,
            "result": self.result,
            "error": self.error,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to
        }


@dataclass
class Artifact:
    """Result of a task that can be passed between agents."""
    artifact_id: str
    task_id: str
    content_type: str  # "text/plain", "application/json", etc.
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============= BASE AGENT CLASS =============

class BaseAgent(ABC):
    """Base class for all A2A agents."""

    def __init__(self, name: str, description: str, skills: List[str]):
        self.card = AgentCard(
            name=name,
            description=description,
            version="1.0.0",
            skills=skills
        )
        self.tasks: Dict[str, Task] = {}
        self.artifacts: Dict[str, Artifact] = {}
        self.other_agents: Dict[str, 'BaseAgent'] = {}  # Registry of known agents

    def register_agent(self, agent: 'BaseAgent'):
        """Register another agent that this agent can talk to."""
        self.other_agents[agent.card.name] = agent
        print(f"  📇 {self.card.name} registered {agent.card.name}")

    def send_message(self, recipient_name: str, content: str, task_id: Optional[str] = None) -> Message:
        """Send a message to another agent."""
        if recipient_name not in self.other_agents:
            raise ValueError(f"Unknown agent: {recipient_name}")

        message = Message(
            message_id=str(uuid.uuid4()),
            sender=self.card.name,
            recipient=recipient_name,
            content=content,
            task_id=task_id
        )

        print(f"\n  💬 {self.card.name} → {recipient_name}: {content[:50]}...")

        # Deliver the message
        recipient = self.other_agents[recipient_name]
        return recipient.receive_message(message)

    def receive_message(self, message: Message) -> Message:
        """Receive a message from another agent."""
        print(f"  📬 {self.card.name} received from {message.sender}: {message.content[:50]}...")

        # Process the message
        response_content = self.handle_message(message)

        # Send response back
        response = Message(
            message_id=str(uuid.uuid4()),
            sender=self.card.name,
            recipient=message.sender,
            content=response_content,
            task_id=message.task_id
        )

        return response

    def create_task(self, task_type: str, parameters: Dict[str, Any], created_by: str) -> Task:
        """Create a new task."""
        task = Task(
            task_id=str(uuid.uuid4()),
            type=task_type,
            parameters=parameters,
            created_by=created_by,
            assigned_to=self.card.name
        )
        self.tasks[task.task_id] = task
        print(f"  📋 {self.card.name} created task {task.task_id[:8]}... ({task_type})")
        return task

    def update_task(self, task_id: str, state: TaskState, result: Any = None, error: str = None):
        """Update a task's status."""
        if task_id in self.tasks:
            self.tasks[task_id].state = state
            self.tasks[task_id].result = result
            self.tasks[task_id].error = error
            print(f"  🔄 {self.card.name} task {task_id[:8]}... → {state.value}")

    def create_artifact(self, task_id: str, content_type: str, content: Any) -> Artifact:
        """Create an artifact (result) from a task."""
        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            task_id=task_id,
            content_type=content_type,
            content=content
        )
        self.artifacts[artifact.artifact_id] = artifact
        return artifact

    @abstractmethod
    def handle_message(self, message: Message) -> str:
        """Handle incoming messages. Override in subclass."""
        pass

    @abstractmethod
    def execute_task(self, task: Task) -> Any:
        """Execute a task. Override in subclass."""
        pass


# ============= SPECIALIZED AGENTS =============

class WeatherAgent(BaseAgent):
    """Agent that handles weather-related tasks."""

    def __init__(self):
        super().__init__(
            name="WeatherAgent",
            description="I can get current weather and forecasts for any city",
            skills=["get_weather", "get_forecast", "weather_alert"]
        )

    def handle_message(self, message: Message) -> str:
        """Handle incoming messages."""
        if "weather" in message.content.lower():
            # Extract city from message (simplified)
            city = "Tokyo"  # In production, use LLM to extract
            task = self.create_task("get_weather", {"city": city}, message.sender)
            result = self.execute_task(task)
            return f"The weather in {city} is 72°F and sunny."
        else:
            return f"I only handle weather queries. You asked about: {message.content}"

    def execute_task(self, task: Task) -> Any:
        """Execute a weather task."""
        self.update_task(task.task_id, TaskState.WORKING)

        # Mock weather data
        weather_data = {
            "Tokyo": "72°F, sunny",
            "London": "65°F, cloudy",
            "New York": "80°F, humid"
        }

        city = task.parameters.get("city", "Tokyo")
        result = weather_data.get(city, f"Weather data not available for {city}")

        self.update_task(task.task_id, TaskState.COMPLETED, result)
        return result


class EmailAgent(BaseAgent):
    """Agent that handles email-related tasks."""

    def __init__(self):
        super().__init__(
            name="EmailAgent",
            description="I can send and read emails",
            skills=["send_email", "read_email", "search_email"]
        )

    def handle_message(self, message: Message) -> str:
        """Handle incoming messages."""
        if "send" in message.content.lower() or "email" in message.content.lower():
            task = self.create_task("send_email", {"to": "user@example.com", "body": message.content}, message.sender)
            result = self.execute_task(task)
            return f"Email sent successfully. {result}"
        else:
            return f"I only handle email tasks. You asked about: {message.content}"

    def execute_task(self, task: Task) -> Any:
        """Execute an email task."""
        self.update_task(task.task_id, TaskState.WORKING)

        to_addr = task.parameters.get("to", "unknown")
        body = task.parameters.get("body", "")

        # Mock email sending
        print(f"\n  📧 SENDING EMAIL:")
        print(f"     To: {to_addr}")
        print(f"     Body: {body[:100]}...")

        result = f"Email sent to {to_addr}"
        self.update_task(task.task_id, TaskState.COMPLETED, result)
        return result


class OrchestratorAgent(BaseAgent):
    """
    The main agent that coordinates other agents.
    This is the "boss" agent that decides which agent to call.
    """

    def __init__(self):
        super().__init__(
            name="Orchestrator",
            description="I coordinate between specialized agents to fulfill user requests",
            skills=["coordinate", "delegate", "synthesize"]
        )
        self.conversation_history: List[Message] = []

    def handle_message(self, message: Message) -> str:
        """Handle user messages by delegating to other agents."""

        content_lower = message.content.lower()

        # Decide which agent to call based on intent
        if "weather" in content_lower:
            target_agent = "WeatherAgent"
            response = self.send_message(target_agent, message.content)
            return f"🌤️ Weather Agent says: {response.content}"

        elif "email" in content_lower or "send" in content_lower:
            target_agent = "EmailAgent"
            response = self.send_message(target_agent, message.content)
            return f"📧 Email Agent says: {response.content}"

        elif "both" in content_lower or "weather and email" in content_lower:
            # Complex: Call multiple agents and combine results
            weather_response = self.send_message("WeatherAgent", "What's the weather in Tokyo?")
            email_response = self.send_message("EmailAgent", f"Send an email about: {weather_response.content}")
            return f"✅ Done! Weather info sent via email."

        else:
            return f"I can help with weather or email tasks. You asked: {message.content}"

    def execute_task(self, task: Task) -> Any:
        """Execute a coordination task."""
        self.update_task(task.task_id, TaskState.WORKING)

        task_type = task.type
        parameters = task.parameters

        if task_type == "delegate":
            target = parameters.get("target_agent")
            user_query = parameters.get("query")
            response = self.send_message(target, user_query)
            result = response.content
        else:
            result = f"Unknown task type: {task_type}"

        self.update_task(task.task_id, TaskState.COMPLETED, result)
        return result


# ============= USER AGENT (Simplified) =============

class UserAgent:
    """
    Simulates a user interacting with the orchestrator.
    In production, this would be your chat interface.
    """

    def __init__(self, orchestrator: OrchestratorAgent):
        self.orchestrator = orchestrator
        self.conversation_id = str(uuid.uuid4())

    def ask(self, query: str) -> str:
        """User asks a question."""
        print(f"\n👤 User: {query}")

        message = Message(
            message_id=str(uuid.uuid4()),
            sender="User",
            recipient=orchestrator.card.name,
            content=query,
            task_id=self.conversation_id
        )

        response = orchestrator.receive_message(message)
        print(f"🤖 Orchestrator: {response.content}")
        return response.content


# ============= RUN THE DEMO =============

async def run_a2a_demo():
    """Demonstrate agent-to-agent communication."""

    print("=" * 60)
    print("A2A (AGENT-TO-AGENT) PROTOCOL DEMO")
    print("=" * 60)
    print("This demo shows how agents can communicate with each other.")

    # Create specialized agents
    print("\n🏗️ CREATING AGENTS:")
    weather_agent = WeatherAgent()
    email_agent = EmailAgent()
    orchestrator = OrchestratorAgent()

    # Register agents with each other
    print("\n🔗 REGISTERING AGENTS:")
    orchestrator.register_agent(weather_agent)
    orchestrator.register_agent(email_agent)
    weather_agent.register_agent(orchestrator)
    email_agent.register_agent(orchestrator)

    # Create user interface
    user = UserAgent(orchestrator)

    # Demo interactions
    print("\n" + "=" * 60)
    print("💬 CONVERSATIONS")
    print("=" * 60)
    print("This is a simplified chat interface. In production, this would be your chatbot.")

    # Test 1: Weather query
    print("\n--- TEST 1: WEATHER QUERY ---")
    user.ask("What's the weather in Tokyo?")

    # Test 2: Email query
    print("\n--- TEST 2: EMAIL QUERY ---")
    user.ask("Send an email to my boss about the meeting")

    # Test 3: Complex query (multi-agent)
    print("\n--- TEST 3: MULTI-AGENT (Weather + Email) ---")
    user.ask("Get the weather in London and send it to me via email")

    # Show task history
    print("\n" + "=" * 60)
    print("📋 TASK HISTORY")
    print("=" * 60)

    all_tasks = []
    for agent in [weather_agent, email_agent, orchestrator]:
        for task in agent.tasks.values():
            all_tasks.append(task)

    for task in all_tasks:
        status = "✅" if task.state == TaskState.COMPLETED else "⏳"
        print(f"  {status} {task.type} ({task.assigned_to}) - {task.state.value}")


if __name__ == "__main__":
    asyncio.run(run_a2a_demo())