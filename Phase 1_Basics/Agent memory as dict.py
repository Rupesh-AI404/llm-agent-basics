"""Why this matters for agents: Every agent call needs context.
You're building this dict dynamically as the conversation flows."""

# Example of a dict that is updated as the conversation flows.

conversation_memory = {
    "user_id": "123",
    "messages": [
        {"role": "user", "content": "Book a flight to Tokyo"},
        {"role": "assistant", "content": "When would you like to depart?"},
        {"role": "user", "content": "Next Monday"},
        {"role": "assistant", "content": "What type of travel would you like?"},
        {"role": "user", "content": "Flight"},
        {"role": "assistant", "content": "How many passengers?"},
        {"role": "user", "content": "Two"},
        {"role": "assistant", "content": "Do you have any luggage?"},
        {"role": "user", "content": "Yes"},
        {"role": "assistant", "content": "Do you need confirmation?"},
        {"role": "user", "content": "Yes"},
        {"role": "assistant", "content": "Thank you! Your flight has been booked."},
        {"role": "user", "content": "What is the weather like in Kathmandu?"},
        {"role": "assistant", "content": "It's sunny and warm."}
    ],
    "extracted_data": {
        "destination": "Kathmandu",
        "date": None, # Will fill later
        "passenger_count": None,
        "preferences": [],
        "travel_mode": None,
        "travel_class": None,
        "confirmation": None
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
        print(f"User wants {word}!")

    if word in ["flight", "train", "bus"]:
        conversation_memory["extracted_data"]["travel_mode"] = word
        print(f"User wants to travel by {word}!")

    if word in ["economy", "business", "first"]:
        conversation_memory["extracted_data"]["travel_class"] = word
        print(f"User wants to travel with {word} class!")

    if word in ["yes", "no"]:
        conversation_memory["extracted_data"]["confirmation"] = word
        print(f"User wants confirmation!")


    if word in ["yes", "no"]:
        conversation_memory["pending_confirmation"] = word
        print(f"User wants confirmation!")
