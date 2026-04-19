"""
Friday MCP Server — Entry Point
Run with: python server.py
"""

import logging
from mcp.server.fastmcp import FastMCP
from friday.tools import register_all_tools
from friday.prompts import register_all_prompts
from friday.resources import register_all_resources
from friday.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("friday-server")

# Create the MCP server instance
mcp = FastMCP(
    name=config.SERVER_NAME,
    instructions=(
        "You are Friday, a Tony Stark-style AI assistant. "
        "You have access to a set of tools to help the user. "
        "Be concise, accurate, and a little witty."
    ),
)

# Register tools, prompts, and resources
logger.info("Registering tools...")
register_all_tools(mcp)
logger.info("Tools registered. Starting server...")

register_all_prompts(mcp)
register_all_resources(mcp)

def main():
    mcp.run(transport='sse')

if __name__ == "__main__":
    main()
