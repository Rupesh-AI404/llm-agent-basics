"""Forgetting lower()—LLMs capitalize randomly. Always normalize."""

# example for conditional routing based on user input (agent decision logic)

def route_intent(user_input: str):
    """Agent decides which tool to call based on input"""
    input_lower = user_input.lower()  # Normalize input for consistent matching

    if any(word in input_lower for word in ["weather", "forecast"]):
        return "call_weather_api"
    elif any(word in input_lower for word in ["news", "headlines"]):
        return "call_news_api"
    elif "?" in user_input and len(user_input.split()) < 5:
        return "call_faq_tool"
    else:
        return "call_general_search"

# Real agent use
user_input = "What's the weather like in Kathmandu?"
action = route_intent(user_input)
print(f"Agent decided to: {action}")
print(f"User input: {user_input}")
print(f"Normalized input: {user_input.lower()}")