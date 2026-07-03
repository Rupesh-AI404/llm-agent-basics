# This is how your agent turns LLM rambling into executable actions.


from typing import Dict, List, Optional


def extract_action_from_llm_response(
        llm_output: str,
        allowed_actions: List[str]
) -> Dict[str, Optional[str]]:
    """
    Agent pattern: Parse LLM output into executable action
    """
    # LLMs often ramble. Extract just what you need.
    lines = llm_output.strip().split('\n')

    action = None
    parameters = {}

    for line in lines:
        if line.startswith("ACTION:"):
            potential_action = line.replace("ACTION:", "").strip()
            if potential_action in allowed_actions:
                action = potential_action
        elif line.startswith("PARAM:"):
            key, value = line.replace("PARAM:", "").split("=", 1)
            parameters[key.strip()] = value.strip()

    return {
        "action": action,
        "parameters": parameters,
        "is_valid": action is not None
    }


# Real usage
llm_response = """I think the user wants to search their email.
ACTION: search_email
PARAM: query=meeting notes
PARAM: max_results=5
Also here's some random text LLMs add."""

result = extract_action_from_llm_response(
    llm_response,
    ["search_email", "send_email", "delete_email"]
)
print(result)
print(result["action"])
print(result["parameters"])