from typing import Tuple, Dict, Any, Union
from wikisearch.api import WikiSearchAPI
from wikisearch.tools.convert_html import convert_html_to_markdown

class SearchError(Exception):
    """搜索工具专用异常"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
def search_html_content(searcher: WikiSearchAPI, query: str, index: int = 0) -> Dict[str, Any]:
    """
    使用 WikiSearchAPI 搜索并返回原始 HTML 内容。
    
    Returns:
        Dict: 包含 success, title, content 的字典
        
    Raises:
        SearchError: 搜索失败时抛出
    """
    success, title, html_content, error = searcher.search(query, index)

    if success and html_content:
        return {
            "success": True,
            "title": title,
            "content": html_content
        }
    else:
        status_code = 404 if error and "not found" in error.lower() else 500
        raise SearchError(error or f"未找到文章 '{query}' (索引 {index})。", status_code)


def search_markdown_content(searcher: WikiSearchAPI, query: str, index: int = 0) -> Dict[str, Any]:
    """
    使用 WikiSearchAPI 搜索并将结果转换为 Markdown 格式。
    
    Returns:
        Dict: 包含 success, query, index, title, markdown 的字典
        
    Raises:
        SearchError: 搜索或转换失败时抛出
    """
    try:
        result = search_html_content(searcher, query, index)
        title = result["title"]
        html_content = result["content"]
    except SearchError as e:
        raise SearchError(e.message, e.status_code)

    md_success, markdown_content, md_error = convert_html_to_markdown(html_content, None, title)

    if md_success and markdown_content:
        return {
            "success": True,
            "query": query,
            "index": index,
            "title": title,
            "markdown": markdown_content
        }
    else:
        raise SearchError(f"HTML 转 Markdown 失败: {md_error}", 500)