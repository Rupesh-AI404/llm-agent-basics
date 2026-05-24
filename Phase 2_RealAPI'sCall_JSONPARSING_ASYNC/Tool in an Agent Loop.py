def agent_turn(user_message: str, history: list):
    """Simple agent turn example"""
    history.append({"role": "user", "content": user_message})

    # In real code, you send history to LLM and it decides to call tool
    # For now we simulate LLM deciding to use search
    print("Agent decided to search...")

    tool_result = web_search(user_message)

    # Add tool result to history (critical pattern)
    history.append({
        "role": "tool",
        "content": json.dumps(tool_result),  # Convert dict to string
        "tool_name": "web_search"
    })

    print("Tool returned:", tool_result["success"])
    return history