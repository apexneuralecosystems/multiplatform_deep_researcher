"""
MCP (Model Context Protocol) server configuration.
Supports SSE and STDIO connection modes for Bright Data.
"""

import logging

from mcp import StdioServerParameters

from backend.core.config import settings


def get_server_params():
    """
    Returns MCP server parameters based on MCP_MODE configuration.
    
    Modes:
    - "sse": Use Bright Data SSE endpoint (remote)
    - "stdio": Use npx @brightdata/mcp locally (default)
    
    Returns:
        StdioServerParameters or dict for SSE.
        
    Raises:
        RuntimeError: If BRIGHT_DATA_API_TOKEN is not configured.
    """
    mode = settings.MCP_MODE
    token = settings.BRIGHT_DATA_API_TOKEN
    
    if not token:
        raise RuntimeError(
            "BRIGHT_DATA_API_TOKEN is not set. "
            "Get your token at: https://brightdata.com/ai/mcp-server"
        )
    
    if mode == "sse":
        # Use Bright Data's remote SSE endpoint
        sse_url = f"https://mcp.brightdata.com/sse?token={token}&groups=advanced_scraping"
        logging.info("MCP Mode: SSE - using remote endpoint")
        return {
            "url": sse_url,
            "transport": "sse"
        }
    else:
        # Default: Use local npx with stdio
        logging.info("MCP Mode: STDIO - using npx @brightdata/mcp")
        return StdioServerParameters(
            command="npx",
            args=["-y", "@brightdata/mcp"],
            env={"API_TOKEN": token, "PRO_MODE": "true"},
        )
