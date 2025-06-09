#!/usr/bin/env python3
"""
NetworkTables Model Context Protocol (MCP) Server

This server provides MCP access to NetworkTables data, enabling AI agents
to interact with FRC robot data through a standardized protocol.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from nt_manager import NetworkTablesManager

from fastmcp import FastMCP, Context
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def nt_context(server: FastMCP) -> AsyncIterator[NetworkTablesManager]:
    nt_manager = NetworkTablesManager()
    try:
        yield nt_manager
    finally:
        nt_manager.disconnect()


mcp = FastMCP("NetworkTables MCP Server", lifespan=nt_context)


@mcp.tool
async def nt_connect(
    team_number: Optional[int] = None,
    server_ip: Optional[str] = None,
    server_port: int = 5810,
    identity: str = "MCP-NT-Server",
    ctx: Context = None,
) -> Dict[str, Any]:
    """Connect to NetworkTables server"""
    try:
        nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
        nt_manager.configure_connection(
            team_number=team_number,
            server_ip=server_ip,
            server_port=server_port,
            identity=identity,
        )

        # Wait a moment for connection to establish
        time.sleep(0.5)

        return {"success": True, "connection_info": nt_manager.get_connection_info()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
def nt_disconnect(ctx: Context = None) -> Dict[str, Any]:
    """Disconnect from NetworkTables server"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    try:
        nt_manager.disconnect()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
async def nt_connection_info(ctx: Context = None) -> Dict[str, Any]:
    """Get NetworkTables connection information"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.get_connection_info()


@mcp.tool
async def nt_time_sync_info(ctx: Context = None) -> Dict[str, Any]:
    """Get NetworkTables time sync information"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.get_time_sync_info()


@mcp.tool
def nt_list_topics(
    topic_prefix: Optional[str] = None, ctx: Context = None
) -> List[str]:
    """List available NetworkTables topics"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.list_topics(topic_prefix)


@mcp.tool
def nt_get_info(topic: str, ctx: Context = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about a topic"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.get_topic_info(unquote(topic))


@mcp.tool
def nt_get(topic: str, ctx: Context = None) -> Any:
    """Get value from a NetworkTables topic"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.get_value(unquote(topic))


@mcp.tool
def nt_get_multiple(topics: List[str], ctx: Context = None) -> Dict[str, Any]:
    """Get values from multiple NetworkTables topics"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.get_multiple_values([unquote(topic) for topic in topics])


@mcp.tool
def nt_set(topic: str, value: Any, ctx: Context = None) -> bool:
    """Set value to a NetworkTables topic"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.set_value(unquote(topic), value)

@mcp.tool
def nt_set_array(topic: str, value: Any, ctx: Context = None) -> bool:
    """Set value to a NetworkTables topic"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.set_value(unquote(topic), json.loads(value))


@mcp.tool
def nt_set_multiple(updates: Dict[str, Any], ctx: Context = None) -> Dict[str, bool]:
    """Set values to multiple NetworkTables topics"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    return nt_manager.set_multiple_values(updates)


@mcp.tool
async def nt_subscribe(
    topic_prefixes: List[str], duration: float = 10.0, ctx: Context = None
) -> Dict[str, Any]:
    """Subscribe to topics for real-time monitoring (simplified for MCP)"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    try:
        samples = await nt_manager.subscribe(topic_prefixes, duration)

        return {
            "success": True,
            "samples": samples,
        }

    except Exception as e:
        await ctx.error(f"{e}")
        return {"success": False, "error": str(e)}


@mcp.resource("nt://topics", mime_type="application/json")
def list_nt_topics(ctx: Context = None) -> List[Dict[str, Any]]:
    """List all NetworkTables topics as resources"""
    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    topics = nt_manager.list_topics()
    resources = []

    for topic in topics:
        resources.append(
            {
                "uri": f"nt://{quote(topic)}",
                "data": nt_manager.get_topic_info(topic),
            }
        )

    return {"resources": resources}


@mcp.resource("nt://{uri}", mime_type="application/json")
def get_nt_topic(uri: str, ctx: Context = None) -> Dict[str, Any]:
    """Get NetworkTables topic value as resource"""
    topic_name = unquote(uri)

    nt_manager: NetworkTablesManager = ctx.request_context.lifespan_context
    value = nt_manager.get_value(topic_name)
    topic_info = nt_manager.get_topic_info(topic_name)

    return {
        "topic_info": topic_info,
        "value": value,
    }


def main():
    """Main entry point"""

    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
