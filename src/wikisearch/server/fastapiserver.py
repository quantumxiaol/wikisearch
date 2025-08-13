# server/fastapiserver.py
import os
from pathlib import Path
from typing import Optional

# FastAPI 相关导入
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from wikisearch.api import WikiSearchAPI, search_wiki_html
from wikisearch.config import config
from wikisearch.tools.convert_html import convert_html_to_markdown
from wikisearch.tools.tools import search_html_content, search_markdown_content, SearchError
from dotenv import load_dotenv
load_dotenv()


# --- 配置 ---
# 从环境变量获取 ZIM 源目录，或使用 WikiSearchAPI 的默认值
ZIM_SOURCE_ENV=os.getenv("WIKI_DOWNLOAD_DIR", "")
# 从环境变量获取服务器 host 和 port
SERVER_HOST = os.getenv("WIKI_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("WIKI_SERVER_PORT", 8000))

# --- FastAPI 应用 ---
app = FastAPI(
    title="WikiSearch ZIM API",
    description="一个基于 ZIM 文件的 Wiki 搜索 API，可以返回 HTML 或 Markdown 格式的结果。"
)

# --- 全局状态管理 (使用 lifespan 推荐) ---
from contextlib import asynccontextmanager

# 全局 WikiSearchAPI 实例
wiki_api: Optional[WikiSearchAPI] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wiki_api
    # 启动时初始化
    print("Initializing WikiSearchAPI...")
    try:
        # 使用环境变量或默认值
        zim_source = ZIM_SOURCE_ENV
        wiki_api = WikiSearchAPI(zim_source=zim_source) # zim_source 可以是 None, 字符串, 或列表
        print("WikiSearchAPI initialized successfully.")
        print(f"Loaded ZIM files: {wiki_api.list_zim_files()}")
    except Exception as e:
        print(f"Failed to initialize WikiSearchAPI: {e}")
        wiki_api = None # 标记为不可用

    yield # 应用运行期间

    # 关闭时清理
    if wiki_api:
        print("Closing WikiSearchAPI...")
        wiki_api.close()
        print("WikiSearchAPI closed.")

app = FastAPI(lifespan=lifespan, title=app.title, description=app.description)

# --- 依赖项 ---
def get_wiki_api():
    if wiki_api is None:
        raise HTTPException(status_code=503, detail="WikiSearchAPI 未初始化或初始化失败。")
    return wiki_api


# --- API 路由 ---

@app.get("/")
async def read_root():
    """根路径，返回简单的欢迎信息和文档链接"""
    return {
        "message": "欢迎使用 WikiSearch ZIM API!",
        "description": "该 API 可以从 ZIM 文件中搜索维基百科内容。",
        "docs": "/docs", # Swagger UI
        "redoc": "/redoc", # ReDoc
        "endpoints": {
            "search_html": "/search/html",
            "search_markdown": "/search/markdown"
        }
    }

@app.get("/search/html", response_class=HTMLResponse)
async def search_html(
    query: str = Query(..., description="要搜索的关键词"),
    index: int = Query(0, ge=0, description="结果索引 (从0开始)"),
    searcher: WikiSearchAPI = Depends(get_wiki_api)
):
    """
    根据关键词搜索文章并返回原始 HTML 内容。
    
    - **query**: 搜索关键词 (必需)。
    - **index**: 结果索引 (默认 0，即第一个结果)。
    """
    try:
        result = search_html_content(searcher, query, index)
        return HTMLResponse(content=result["content"], status_code=200)
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/search/markdown")
async def search_markdown(
    query: str = Query(..., description="要搜索的关键词"),
    index: int = Query(0, ge=0, description="结果索引 (从0开始)"),
    searcher: WikiSearchAPI = Depends(get_wiki_api)
):
    """
    根据关键词搜索文章，将结果转换为 Markdown 并返回。
    
    - **query**: 搜索关键词 (必需)。
    - **index**: 结果索引 (默认 0，即第一个结果)。
    """
    try:
        result = search_markdown_content(searcher, query, index)
        return result
    except SearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
@app.get("/metadata")
async def get_metadata(searcher: WikiSearchAPI = Depends(get_wiki_api)):
    """
    获取已加载 ZIM 文件的元数据。
    """
    metadata = searcher.get_metadata()
    return metadata

@app.get("/zim-files")
async def list_zim_files(searcher: WikiSearchAPI = Depends(get_wiki_api)):
    """
    列出当前加载的 ZIM 文件路径。
    """
    files = searcher.list_zim_files()
    return {"zim_files": files}

# --- 运行入口 ---
if __name__ == "__main__":
    import uvicorn
    print(f"Starting WikiSearch ZIM API server on http://{SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        "fastapiserver:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=os.getenv("WIKI_SERVER_RELOAD", "false").lower() == "true"
    )