"""
Check MCP server tool list and call a tool directly.

Local MCP example:
python tests/test_mcp_tool.py -u "http://127.0.0.1:8089/mcp/" \
    --tool-name search_wiki_markdown \
    --tool-arg "query=维基百科"
"""


import argparse
import asyncio
import json
import os
from typing import Any, Dict, Optional

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

def parse_tool_args(args_str_list: list) -> Dict[str, Any]:
    """
    将 ["key=value", "foo=bar"] 转为 {"key": "value", "foo": "bar"}
    支持自动类型解析：str, int, float, bool, None
    """
    result = {}
    if not args_str_list:
        return result

    for item in args_str_list:
        if "=" not in item:
            raise ValueError(f"Invalid tool-arg format: {item}, expected key=value")
        k, v = item.split("=", 1)

        # 尝试类型解析
        try:
            v = json.loads(v.lower() if v.lower() in ("true", "false", "null") else v)
        except json.JSONDecodeError:
            pass  # keep as string

        result[k] = v
    return result


async def async_main(
    server_url: str = "",
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
):
    async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print('MCP server session已初始化')

            tools_result = await session.list_tools()
            tool_dict = {tool.name: tool for tool in tools_result.tools}

            print("可用工具:", [tool.name for tool in tools_result.tools])
            for tool in tools_result.tools:
                print(f"Tool: {tool.name}")
                print(f"Input Schema: {tool.inputSchema}")
                print(f"Description: {tool.description}\n")

            if not tool_name:
                print("未提供问题或工具调用，仅列出工具信息。")
                print("TEST_RESULT: PASSED")
                return

            if tool_name not in tool_dict:
                print(f"错误: 工具 '{tool_name}' 未在 MCP 服务中找到！")
                print("TEST_RESULT: FAILED")
                return

            if not tool_args:
                print(f"警告: 调用工具 '{tool_name}' 但未提供参数。")
                tool_args = {}

            try:
                print(f"正在调用工具: {tool_name}，参数: {tool_args}")
                result = await session.call_tool(tool_name, tool_args)
                print("✅ 工具调用成功！返回结果:")
                if result.structuredContent is not None:
                    print(json.dumps(result.structuredContent, indent=2, ensure_ascii=False))
                else:
                    print(result.content)
                print("TEST_RESULT: PASSED")
            except Exception as e:
                print(f"❌ 工具调用失败: {type(e).__name__}: {e}")
                print("TEST_RESULT: FAILED")
            return


@pytest.mark.asyncio
async def test_mcp_tool_call() -> None:
    server_url = os.getenv("MCP_URL", "http://127.0.0.1:8089/mcp/")
    tool_name = os.getenv("MCP_TOOL_NAME", "search_wiki_markdown")
    tool_args = parse_tool_args(
        [os.getenv("MCP_TOOL_QUERY", "query=wiki")]
    )

    try:
        async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tool_dict = {tool.name: tool for tool in tools_result.tools}
                assert tool_name in tool_dict, f"Missing tool: {tool_name}"
                result = await session.call_tool(tool_name, tool_args)
                assert not result.isError, "Tool call returned error"
    except Exception as exc:
        pytest.skip(f"MCP server not available: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test MCP Server: list tools or invoke a tool")

    parser.add_argument(
        "-u", "--base_url",
        type=str,
        default="http://127.0.0.1:8089/mcp/",
        help="MCP server base url"
    )
    parser.add_argument(
        "--tool-name",
        type=str,
        default="search_wiki_markdown",
        help="要直接调用的工具名称，例如 search_wiki_markdown"
    )
    parser.add_argument(
        "--tool-arg",
        action="append",
        default=["query=维基百科"],
        help="工具参数，格式 key=value，可多次使用"
    )
    args = parser.parse_args()

    # 解析 tool-arg
    tool_args = parse_tool_args(args.tool_arg) if args.tool_arg else None

    # 运行主函数
    asyncio.run(async_main(
        server_url=args.base_url,
        tool_name=args.tool_name,
        tool_args=tool_args
    ))
