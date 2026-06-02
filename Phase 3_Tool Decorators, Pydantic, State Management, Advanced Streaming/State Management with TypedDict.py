from typing import TypedDict, List, Optional, Literal
from datetime import datetime


# ============= DEFINE YOUR STATE TYPES =============
class Message(TypedDict):
    """A single message in conversation."""
    role: Literal['user', 'assistant', 'system']
    content: str
    timestamp: datetime


class ExtractedData(TypedDict):
    """Data extracted from conversation."""
    destination: Optional[str]
    date: Optional[str]
    passenger_count: Optional[int]
    preferences: List[str]


class AgentState(TypedDict):
    """Complete state of an agent conversation."""
    user_id: str
    conversation_id: str
    messages: List[Message]
    extracted: ExtractedData
    last_action: Optional[str]
    pending_confirmation: bool


# ============= USING TYPED DICTS =============
from datetime import datetime


def create_initial_state(user_id: str) -> AgentState:
    """Create a new agent state."""
    return {
        "user_id": user_id,
        "conversation_id": f"conv_{datetime.now().timestamp()}",
        "messages": [],
        "extracted": {
            "destination": None,
            "date": None,
            "passenger_count": None,
            "preferences": []
        },
        "last_action": None,
        "pending_confirmation": False
    }


def add_message(state: AgentState, role: str, content: str) -> AgentState:
    """Add a message to state."""
    message: Message = {
        "role": role,  # type: ignore (Literal check)
        "content": content,
        "timestamp": datetime.now()
    }

    state["messages"].append(message)
    return state


def update_extracted_data(state: AgentState, field: str, value):
    """Update extracted data with validation."""
    if field in state["extracted"]:
        state["extracted"][field] = value  # type: ignore
    return state


# ============= DEMO =============
state = create_initial_state("user_123")
print("Initial state:")
print(f"  User: {state['user_id']}")
print(f"  Messages: {len(state['messages'])}")
print(f"  Extracted: {state['extracted']}")
print(f"  Last action: {state['last_action']}")
print(f"  Pending confirmation: {state['pending_confirmation']}")

print("\nAdding messages...")
state = add_message(state, "user", "Book a flight to Tokyo")
state = add_message(state, "assistant", "What date would you like to fly?")

print(f"Messages: {len(state['messages'])}")
print(f"Last message: {state['messages'][-1]['content']}")

print("\nExtracting data...")
state = update_extracted_data(state, "destination", "Tokyo")
print(f"Extracted destination: {state['extracted']['destination']}")
print(f"Extracted date: {state['extracted']['date']}")

# With TypedDict, your IDE will suggest:
# state["extracted"]["destination"]  ← auto-completes!
# state["extracted"]["invalid"]      ← shows error!