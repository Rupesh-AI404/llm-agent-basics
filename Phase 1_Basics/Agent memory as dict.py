"""Why this matters for agents: Every agent call needs context.
You're building this dict dynamically as the conversation flows."""

# Example of a dict that is updated as the conversation flows.

conversation_memory = {
    "user_id": "123",
    "messages": [
        {"role": "user", "content": "Book a flight to Tokyo"},
        {"role": "assistant", "content": "When would you like to depart?"},
        {"role": "user", "content": "Next Monday"}
    ],
    "extracted_data": {
        "destination": "Kathmandu",
        "date": None  # Will fill later
    }
}

# Accessing the last message
last_message = conversation_memory["messages"][-1]["content"]   # [-1] gets the last item in the list
print(f"Last user said: {last_message}")

#updating the extracted_data
if "kathmandu" in last_message:
    conversation_memory["extracted_data"]["destination"] = "Kathmandu"

words = last_message.split()
for word in words:
    if word in ["kathmandu", "chitwan", "next", "monday"]:
        conversation_memory["extracted_data"]["date"] = word

    if word in ["kathmandu", "chitwan"]:
        conversation_memory["extracted_data"]["destination"] = word

    if word in ["one", "two", "three"]:
        conversation_memory["extracted_data"]["passenger_count"] = word

    if word in ["luggage", "baggage"]:
        conversation_memory["extracted_data"]["preferences"].append(word)
