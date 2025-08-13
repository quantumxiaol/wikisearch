"""
python ./src/wikisearch/server/mcpserver.py --http
python -m wikisearch.server.mcpserver --http

"""

import os
import httpx
import sys
import asyncio
import argparse
import uvicorn
import contextlib
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from typing import Dict, Any, Optional, AsyncIterator, List

from mcp.server import FastMCP
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from wikisearch.api import WikiSearchAPI, search_wiki_html
from wikisearch.config import config
from wikisearch.tools.convert_html import convert_html_to_markdown
from wikisearch.tools.tools import search_html_content, search_markdown_content, SearchError
from dotenv import load_dotenv
load_dotenv()

WIKI_DOWNLOAD_DIR = os.getenv("WIKI_DOWNLOAD_DIR", "")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", 8089))

mcp = FastMCP(name="WIKI Search MCP Server")

wiki_api: Optional[WikiSearchAPI] = None
def get_wiki_api():
    if wiki_api is None:
        raise BaseException("WikiSearchAPI 未初始化或初始化失败。")
    return wiki_api

try:
    def init_wiki_search():
        global wiki_api
        try:
            zim_source = WIKI_DOWNLOAD_DIR if WIKI_DOWNLOAD_DIR else None
            wiki_api = WikiSearchAPI(zim_source=zim_source)
            print("WikiSearchAPI initialized successfully.")
            print(f"Loaded ZIM files: {wiki_api.list_zim_files()}")
            return True
        except Exception as e:
            print(f"Failed to initialize WikiSearchAPI: {e}")
            wiki_api = None
            return False
    
    # 在应用启动时初始化
    init_wiki_search()
    
except ImportError as e:
    print(f"Warning: WikiSearch modules not available: {e}")
    wiki_api = None

@mcp.tool(
    name="search_wiki_html",
    description="""
    Search Wikipedia articles from ZIM files and return HTML content.
    This tool searches for articles matching the query and returns the raw HTML content.
    """
)
async def search_wiki_html(query: str, index: int = 0) -> Dict[str, Any]:
    """搜索维基百科并返回HTML内容"""
    if wiki_api is None:
        return {
            "status": "error",
            "message": "WikiSearchAPI 未初始化或初始化失败"
        }
    
    try:
        result = search_html_content(wiki_api, query, index)
        return {
            "status": "success",
            "result": {
                "title": result["title"],
                "content": result["content"],
                "query": query,
                "index": index
            }
        }
    except SearchError as e:
        status = "not found" if e.status_code == 404 else "error"
        return {
            "status": status,
            "message": e.message
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索过程中发生错误: {str(e)}"
        }

@mcp.tool(
    name="search_wiki_markdown",
    description="""
    Search Wikipedia articles from ZIM files and return Markdown content.
    This tool searches for articles, converts HTML to Markdown, and returns the formatted content.
    """
)
async def search_wiki_markdown(query: str, index: int = 0) -> Dict[str, Any]:
    """搜索维基百科并返回Markdown内容"""
    if wiki_api is None:
        return {
            "status": "error",
            "message": "WikiSearchAPI 未初始化或初始化失败"
        }
    
    try:
        result = search_markdown_content(wiki_api, query, index)
        return {
            "status": "success",
            "result": {
                "title": result["title"],
                "markdown": result["markdown"],
                "query": query,
                "index": index
            }
        }
    except SearchError as e:
        status = "not found" if e.status_code == 404 else "error"
        return {
            "status": status,
            "message": e.message
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索过程中发生错误: {str(e)}"
        }


# --- 创建 Starlette 应用  ---
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            print("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                print("Application shutting down...")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/mcp", app=handle_streamable_http),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

starlette_app = create_starlette_app(mcp._mcp_server, debug=False)

# --- Main entry point ---
def main():
    # 获取 FastMCP 内部的 Server 实例
    mcp_server = mcp._mcp_server
    
    parser = argparse.ArgumentParser(description="McpFileServer API Client Wrapper")

    parser.add_argument(
        "--http",
        action="store_true",
        help="Run the server with Streamable HTTP and SSE transport rather than STDIO (default: False)",
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="(Deprecated) An alias for --http (default: False)",
    )
    parser.add_argument(
        "--host", default=None, help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Port to listen on (default: 8890)"
    )
    args = parser.parse_args()

    use_http = args.http or args.sse

    if not use_http and (args.host or args.port):
        parser.error(
            "Host and port arguments are only valid when using streamable HTTP or SSE transport (see: --http)."
        )
        sys.exit(1)

    if use_http:
        # 使用你提供的 create_starlette_app 函数创建应用
        # starlette_app = create_starlette_app(mcp_server, debug=True)
        uvicorn.run(
            starlette_app,
            host=args.host if args.host else MCP_SERVER_HOST,
            port=args.port if args.port else MCP_SERVER_PORT,
            log_level="info",
            access_log=True,
        )
    else:
        # 默认使用 STDIO
        mcp.run()
    


if __name__ == "__main__":
    main()
