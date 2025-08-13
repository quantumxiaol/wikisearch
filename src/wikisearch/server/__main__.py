#!/usr/bin/env python3
# src/wikisearch/server/__main__.py

"""
python -m wikisearch.server fastapi
python -m wikisearch.server mcp --http
"""

import argparse
import os
import sys

from wikisearch.server.fastapiserver import app as fastapi_app
from wikisearch.server.mcpserver import main as mcp_main, create_starlette_app, mcp, MCP_SERVER_HOST, MCP_SERVER_PORT

import uvicorn


def start_fastapi_server():
    from wikisearch.server.fastapiserver import SERVER_HOST, SERVER_PORT

    print(f"Starting WikiSearch ZIM API server on http://{SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        fastapi_app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=os.getenv("WIKI_SERVER_RELOAD", "false").lower() == "true",
    )


def start_mcp_server(http_mode=True, host=None, port=None):
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    host = host or MCP_SERVER_HOST
    port = port or MCP_SERVER_PORT

    print(f"Starting MCP Server with HTTP transport on http://{host}:{port}")
    uvicorn.run(starlette_app, host=host, port=port, log_level="info", access_log=True)


def main():
    parser = argparse.ArgumentParser(description="Unified Server Launcher for WikiSearch")
    subparsers = parser.add_subparsers(dest="server", help="Choose which server to run", required=True)

    # FastAPI Server
    fastapi_parser = subparsers.add_parser("fastapi", help="Run the FastAPI query server")

    # MCP Server
    mcp_parser = subparsers.add_parser("mcp", help="Run the MCP server with HTTP/SSE")
    mcp_parser.add_argument(
        "--http", "-H",
        action="store_true",
        help="Use HTTP/SSE transport (default)",
    )
    mcp_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind MCP server (default: 127.0.0.1)",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind MCP server (default: 8890)",
    )

    args = parser.parse_args()

    if args.server == "fastapi":
        start_fastapi_server()
    elif args.server == "mcp":
        start_mcp_server(http_mode=args.http, host=args.host, port=args.port)
    else:
        print("Unknown server type.")
        sys.exit(1)


if __name__ == "__main__":
    main()