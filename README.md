# WikiSearch

通过本地的wiki的zim文件，提供search功能，返回html或者是markdown。

有fastapi server 和streamable http 的MCP Server。

## Environment

### 创建虚拟环境

```bash
## use UV
uv venv
source .venv/bin/activate
uv lock
uv sync

## use conda
conda create -n wikisearch python=3.12
conda activate wikisearch
pip install -r requirements.txt

cat .env.template > .env
```
### 下载wiki zim文件

```bash
python download_zim.py
```

这将下载一个wiki zim文件到wiki_zim_downloads目录下，具体下载什么zim文件可以在

```python
patterns = [
    # r"wikipedia_en_all_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_en_all_nopic_(\d{4}-\d{2})\.zim",
    # r"wikipedia_en_top_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_zh_all_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_zh_all_nopic_(\d{4}-\d{2})\.zim",
    r"wikipedia_zh_top_maxi_(\d{4}-\d{2})\.zim",
]
```

中选择，这个patterns列表可以自己添加，也可以自己修改，会从网站上获取相关zim的最新的文件。

可能需要代理才能下载zim文件

```bash
export http_proxy=http://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10808
```

## Usage

开启FastAPI的查询服务
```bash
python ./src/wikisearch/server/fastapiserver.py
# or
python -m wikisearch.server.fastapiserver
# or
python -m wikisearch.server fastapi

```

开启MCP Server
```bash
python ./src/wikisearch/server/mcpserver.py --http
# or
python -m wikisearch.server.mcpserver --http
# or
python -m wikisearch.server mcp --http
```

SERVER_HOST在.env中定义。


## Wikipedia ZIM
[ZIM download](https://download.kiwix.org/zim/wikipedia/)

英文维基百科 (wikipedia_en):

最全版本 (all_maxi): 这是包含所有内容和图片的版本。列表中最新的 wikipedia_en_all_maxi_2024-01.zim 文件大小为 102GB。请注意，列表中没有更新的 all_maxi 版本，可能是因为文件太大且更新频繁。如果你需要最新的英文内容，可能需要考虑其他版本或在线更新工具。

无图版本 (all_nopic): 包含所有文章，但不含图片。最新的 wikipedia_en_all_nopic_2025-07.zim 文件大小为 43GB。

精选/迷你版本 (100 或 top):
- wikipedia_en_100_maxi_2025-08.zim: 约 46MB (含图)。
- wikipedia_en_100_nopic_2025-08.zim: 约 12MB (无图)。
- wikipedia_en_top_maxi_2025-08.zim: 约 7.0GB (含图)。
- wikipedia_en_top_nopic_2025-08.zim: 约 1.6GB (无图)。

其他专业版本: 如 medicine, molcell, movies 等，大小从几十 MB 到几 GB 不等。

中文维基百科 (wikipedia_zh):

最全版本 (all_maxi): 列表中最新的 wikipedia_zh_all_maxi_2025-07.zim 文件大小为 6.4GB。

无图版本 (all_nopic): 列表中最新的 wikipedia_zh_all_nopic_2025-07.zim 文件大小为 2.2GB。

精选/迷你版本 (top):
- wikipedia_zh_top_maxi_2025-08.zim: 约 1.7GB (含图)。
- wikipedia_zh_top_nopic_2025-08.zim: 约 554MB (无图)。

## NOTICE
Disclaimer for Generated Content:

The software may generate content, output, or data as a result of its operation. The copyright holder provides no warranty, express or implied, regarding the accuracy, reliability, or suitability of such generated content. The use of the software and any content it generates is entirely at your own risk. The copyright holder shall not be liable for any damages, losses, or consequences arising from the use or misuse of the generated content.

关于生成内容的免责声明：

本软件在运行过程中可能生成内容、输出或数据。版权持有者对这些生成内容的准确性、可靠性或适用性不提供任何形式的担保。使用本软件及其生成内容的风险完全由使用者自行承担。版权持有者不对因使用或误用生成内容而造成的任何损害、损失或后果承担责任。