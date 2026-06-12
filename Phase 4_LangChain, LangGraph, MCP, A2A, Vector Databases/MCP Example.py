# 4.3_mcp_basic.py

import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv


# ============= MCP SIMULATION (Simplified for Learning) =============
# Note: Full MCP requires running separate MCP servers
# This example shows the PATTERN that MCP uses

class MCPResourceType(Enum):
    FILE = "file"
    DATABASE = "database"
    API = "api"
    VECTOR_STORE = "vector_store"


@dataclass
class MCPResource:
    """A resource that an agent can read."""
    uri: str  # Unique identifier like "file:///data/report.txt"
    name: str
    description: str
    mime_type: str
    content: Any = None


@dataclass
class MCPTool:
    """A tool that an agent can call."""
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema for parameters
    handler: callable


class MCPServer:
    """
    MCP Server that provides resources and tools to agents.
    In production, this runs as a separate process.
    """

    def __init__(self, name: str):
        self.name = name
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}

    def add_resource(self, resource: MCPResource):
        """Register a resource that agents can read."""
        self.resources[resource.uri] = resource
        print(f"  📚 MCP Server '{self.name}' added resource: {resource.name}")

    def add_tool(self, tool: MCPTool):
        """Register a tool that agents can call."""
        self.tools[tool.name] = tool
        print(f"  🔧 MCP Server '{self.name}' added tool: {tool.name}")

    async def read_resource(self, uri: str) -> MCPResource:
        """Agent reads a resource."""
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")

        resource = self.resources[uri]
        # In production, this would actually read the file/database
        print(f"  📖 MCP Server '{self.name}' serving resource: {resource.name}")
        return resource

    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """Agent calls a tool."""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        tool = self.tools[name]
        print(f"  🔧 MCP Server '{self.name}' executing tool: {tool.name}")
        return tool.handler(**arguments)


class MCPClient:
    """
    MCP Client (your agent) that connects to MCP servers.
    """

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}

    def connect(self, server: MCPServer):
        """Connect to an MCP server."""
        self.servers[server.name] = server
        print(f"🔌 MCP Client connected to server: {server.name}")

    async def read(self, uri: str) -> MCPResource:
        """Read a resource using its URI."""
        # Parse URI to find the right server
        # URI format: "server_name://path/to/resource"
        parts = uri.split("://", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid URI: {uri}")

        server_name, resource_path = parts
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")

        return await self.servers[server_name].read_resource(uri)

    async def call(self, server_name: str, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on a specific server."""
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")

        return await self.servers[server_name].call_tool(tool_name, arguments)

    async def list_resources(self) -> List[MCPResource]:
        """List all available resources across all servers."""
        all_resources = []
        for server in self.servers.values():
            all_resources.extend(server.resources.values())
        return all_resources

    async def list_tools(self) -> List[MCPTool]:
        """List all available tools across all servers."""
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.tools.values())
        return all_tools


# ============= CREATE MCP SERVERS (Data Sources) =============

# Server 1: File System
file_server = MCPServer("filesystem")

# Add a file resource
file_server.add_resource(MCPResource(
    uri="filesystem:///data/report.txt",
    name="Quarterly Report",
    description="Q4 2025 financial report",
    mime_type="text/plain",
    content="Q4 revenue: $10.2M, up 15% from Q3. Operating expenses: $7.1M."
))


# Add file tools
def list_files(directory: str) -> str:
    """List files in a directory."""
    return f"Files in {directory}: report.txt, data.csv, config.json"


def read_file(path: str) -> str:
    """Read a file's contents."""
    return f"Contents of {path}: Sample file content here..."


file_server.add_tool(MCPTool(
    name="list_files",
    description="List all files in a directory",
    input_schema={"directory": {"type": "string"}},
    handler=list_files
))

file_server.add_tool(MCPTool(
    name="read_file",
    description="Read contents of a file",
    input_schema={"path": {"type": "string"}},
    handler=read_file
))

# Server 2: Database
db_server = MCPServer("database")

# Add database resource
db_server.add_resource(MCPResource(
    uri="database:///users",
    name="Users Table",
    description="All user records",
    mime_type="application/json",
    content='[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
))


# Add database tools
def query_db(sql: str) -> str:
    """Execute SQL query."""
    return f"Query '{sql}' returned 3 rows"


db_server.add_tool(MCPTool(
    name="query",
    description="Execute SQL query on database",
    input_schema={"sql": {"type": "string"}},
    handler=query_db
))

# Server 3: Vector Store (for RAG)
vector_server = MCPServer("vectorstore")


def vector_search(query: str, top_k: int = 5) -> str:
    """Search vector database for similar documents."""
    return f"Found {top_k} documents matching '{query}': Doc1, Doc2, Doc3..."


vector_server.add_tool(MCPTool(
    name="search",
    description="Search vector database for similar content",
    input_schema={
        "query": {"type": "string"},
        "top_k": {"type": "integer", "default": 5}
    },
    handler=vector_search
))


# ============= CREATE MCP CLIENT (YOUR AGENT) =============

async def run_mcp_agent():
    """Your agent using MCP to access multiple data sources."""

    print("=" * 60)
    print("MCP (MODEL CONTEXT PROTOCOL) DEMO")
    print("=" * 60)
    print("This demo shows how to use MCP to access data from multiple sources.")

    # Create client
    client = MCPClient()

    # Connect to all servers
    print("\n🔌 CONNECTING TO MCP SERVERS:")
    client.connect(file_server)
    client.connect(db_server)
    client.connect(vector_server)

    # List available resources
    print("\n📚 AVAILABLE RESOURCES:")
    resources = await client.list_resources()
    for r in resources:
        print(f"   • {r.name} ({r.uri})")

    # List available tools
    print("\n🔧 AVAILABLE TOOLS:")
    tools = await client.list_tools()
    for t in tools:
        print(f"   • {t.name}: {t.description}")

    # ============= YOUR AGENT USING MCP =============
    print("\n" + "=" * 60)
    print("AGENT USING MCP TO ACCESS DATA")
    print("=" * 60)

    # Example 1: Read a resource
    print("\n📖 EXAMPLE 1: Reading a resource")
    print("   Agent: 'I need to read the quarterly report'")
    resource = await client.read("filesystem:///data/report.txt")
    print(f"   Result: {resource.content[:100]}...")
    print("   Agent: 'What does the report say about revenue?'")
    # In production, your agent would use an LLM to parse the report content
    print("   Agent: 'Revenue is $10.2M, up 15% from Q3.'")

    # Example 2: Call a tool
    print("\n🔧 EXAMPLE 2: Calling a tool")
    print("   Agent: 'List files in the /data directory'")
    result = await client.call("filesystem", "list_files", {"directory": "/data"})
    print(f"   Result: {result}")

    # Example 3: Query database
    print("\n🗄️ EXAMPLE 3: Querying database")
    print("   Agent: 'How many users are in the database?'")
    result = await client.call("database", "query", {"sql": "SELECT COUNT(*) FROM users"})
    print(f"   Result: {result}")

    # Example 4: Vector search
    print("\n🔍 EXAMPLE 4: Vector search (RAG)")
    print("   Agent: 'Find documents about AI agents'")
    result = await client.call("vectorstore", "search", {"query": "AI agents", "top_k": 3})
    print(f"   Result: {result}")
    print("\n" + "=" * 60)
    print("MCP DEMO COMPLETE")

    return client


# ============= INTEGRATING MCP WITH LANGCHAIN =============

def create_mcp_tools_for_langchain(client: MCPClient):
    """
    Convert MCP tools to LangChain tools.
    This is how you use MCP with any agent framework.
    """
    from langchain.tools import tool

    # Dynamically create LangChain tools for each MCP tool
    langchain_tools = []

    async def create_tool_wrapper(server_name: str, mcp_tool: MCPTool):
        """Wrapper that calls MCP tool from LangChain."""

        @tool
        def wrapper(**kwargs):
            """MCP tool wrapper"""
            import asyncio
            # Run async MCP call in sync context
            return asyncio.run(client.call(server_name, mcp_tool.name, kwargs))

        # Update the wrapper's metadata
        wrapper.__name__ = mcp_tool.name
        wrapper.__doc__ = mcp_tool.description
        return wrapper

    # This would create tools dynamically
    # For demo, we'll just return a mock list
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "server": server_name
        }
        for server_name, server in client.servers.items()
        for tool in server.tools.values()
    ]


# ============= RUN THE DEMO =============
if __name__ == "__main__":
    asyncio.run(run_mcp_agent())