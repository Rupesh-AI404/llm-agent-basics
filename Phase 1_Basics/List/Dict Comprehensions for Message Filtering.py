# Agent conversation history
conversation = [
    {"role": "user", "content": "Hi", "timestamp": 1},
    {"role": "assistant", "content": "Hello!", "timestamp": 2},
    {"role": "user", "content": "   ", "timestamp": 3},  # Empty message
    {"role": "assistant", "content": "How can I help?", "timestamp": 4},
    {"role": "user", "content": "What's the weather?", "timestamp": 5},
    {"role": "assistant", "content": "", "timestamp": 6},  # Empty response
    {"role": "user", "content": "In Tokyo", "timestamp": 7},
    {"role": "assistant", "content": "What time?", "timestamp": 8},
    {"role": "user", "content": "Anytime", "timestamp": 9},
    {"role": "assistant", "content": "Sure, 11:30.", "timestamp": 10}
]

# Remove empty or whitespace-only messages
cleaned = [
    msg for msg in conversation
    if msg["content"].strip()
]

# Extract just user messages for context
user_messages = [
    msg["content"] for msg in conversation
    if msg["role"] == "user"
]

print(f"Original: {len(conversation)} messages")
print(f"Cleaned: {len(cleaned)} messages")
print(f"User said: {user_messages}")