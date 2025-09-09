# Assumes the FastAPI app from above is already defined
from fastmcp import FastMCP
from fastmcp.client import Client
import asyncio
import mcpserver

# Convert to MCP server
mcp = FastMCP.from_fastapi(app=mcpserver.app)

async def demo():
    async with Client(mcp) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")


if __name__ == "__main__":
    asyncio.run(demo())