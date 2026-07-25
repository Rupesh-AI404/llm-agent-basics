from typing import Callable, Dict, Any, get_type_hints
import inspect
import json


# ============= THE TOOL DECORATOR =============
class Tool:
    """
    Represents a function that an LLM can call.
    """

    def __init__(self, func: Callable, name: str, description: str, parameters: Dict[str, Any]):
        self.func = func
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func.__name__ = name

    def __call__(self, *args, **kwargs):
        """Allow the tool to be called like a normal function."""
        return self.func(*args, **kwargs)

    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI's function calling format.
        This is what tells the LLM what tools are available.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys())
                }
            }
        }


def tool(func: Callable) -> Tool:
    """
    Decorator that converts a function into an LLM-callable tool.

    Usage:
        @tool
        def get_weather(city: str) -> str:
            '''Get weather for a city.'''
            return f"Weather in {city}: sunny"
    """
    # Extract function name
    name = func.__name__

    # Extract description from docstring (first line)
    docstring = inspect.getdoc(func) or ""
    description = docstring.strip().split('\n')[0]

    # Extract parameter types from function signature
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)

    parameters = {}
    for param_name, param in signature.parameters.items():
        param_type = type_hints.get(param_name, str).__name__

        # Get default value if exists
        has_default = param.default != inspect.Parameter.empty

        parameters[param_name] = {
            "type": param_type.lower(),
            "description": f"Parameter: {param_name}"
        }

        if has_default:
            parameters[param_name]["default"] = param.default

    return Tool(func, name, description, parameters)


# ============= EXAMPLE TOOLS =============
@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a specific city.
    Returns temperature and conditions.
    """
    # In production, call actual weather API
    weather_data = {
        "Tokyo": "72°F, sunny",
        "London": "65°F, cloudy",
        "New York": "80°F, humid"
    }
    return weather_data.get(city, f"Weather data not available for {city}")


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a recipient.
    """
    # In production, call actual email API
    print(f"\n📧 SENDING EMAIL:")
    print(f"   To: {to}")
    print(f"   Subject: {subject}")
    print(f"   Body: {body}")
    return f"Email sent successfully to {to}"


@tool
def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web for information.
    """
    # In production, call Google/Bing API
    results = [
        f"Result 1 for '{query}': Lorem ipsum",
        f"Result 2 for '{query}': Dolor sit amet",
        f"Result 3 for '{query}': Consectetur adipiscing"
    ]
    return "\n".join(results[:max_results])


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============= TOOL REGISTRY =============
class ToolRegistry:
    """
    Manages all available tools and helps LLM decide which to call.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        print(f"🔧 Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool:
        """Get a tool by name."""
        return self.tools.get(name)

    def get_openai_schemas(self) -> list:
        """Get all tools in OpenAI format."""
        return [tool.to_openai_schema() for tool in self.tools.values()]

    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"

        try:
            return tool(**parameters)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"


# ============= PUTTING IT ALL TOGETHER =============
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def call_llm_with_tools(prompt: str, tools: ToolRegistry) -> Dict[str, Any]:
    """
    Call LLM and let it decide which tool(s) to use.
    This is the core of agent tool use.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "tools": tools.get_openai_schemas(),  # Tell LLM what tools exist
        "tool_choice": "auto"  # Let LLM decide when to use tools
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    print(f"LLM response: {result}")
    print(f"Tool call: {result['choices'][0]['message']['tool_calls'][0]}")

    return result["choices"][0]["message"]



# ============= DEMO =============
def run_agent_demo():
    """Demonstrate how agents use tools."""

    # Create registry and register tools
    registry = ToolRegistry()
    registry.register(get_weather)
    registry.register(send_email)
    registry.register(search_web)
    registry.register(get_current_time)


    print("\n" + "=" * 60)
    print("AVAILABLE TOOLS:")
    for tool in registry.tools.values():
        print(f"  • {tool.name}: {tool.description}")
        print(f"    Parameters: {tool.parameters}")

    # Test 1: Call tool directly (no LLM)
    print("\n" + "=" * 60)
    print("TEST 1: Direct tool call")
    result = get_weather(city="Tokyo")
    print(f"Result: {result}")

    # Test 2: Execute via registry
    print("\n" + "=" * 60)
    print("TEST 2: Registry execution")
    result = registry.execute("get_weather", {"city": "London"})
    print(f"Result: {result}")

    # Test 3: LLM decides which tool to use
    print("\n" + "=" * 60)
    print("TEST 3: LLM tool selection (requires API key)")
    print("Prompt: 'What's the weather in Paris?'")
    print("Response:")
    llm_response = call_llm_with_tools("What's the weather in Paris?", registry)
    print(json.dumps(llm_response, indent=2))
    print("---")

    #Test 4: LLM decides which tool to use
    print("\n" + "=" * 60)
    print("TEST 4: LLM tool selection (requires API key)")
    print("Prompt: 'What's the weather in Paris?'")


    # Uncomment to test with real API
    llm_response = call_llm_with_tools("What's the weather in Paris?", registry)
    print(f"LLM decided: {llm_response}")
    print(f"Tool call: {llm_response['tool_calls'][0]}")
    print(f"Tool result: {llm_response['tool_calls'][0]['function']['arguments']}")


if __name__ == "__main__":
    run_agent_demo()
