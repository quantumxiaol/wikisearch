import re
import os
import subprocess
import requests
import argparse
from collections import defaultdict

# --- 配置 ---
# 实时获取的 URL
INDEX_URL = "https://download.kiwix.org/zim/wikipedia/"
# 本地保存目录
DOWNLOAD_DIR = "./wiki_zim_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 定义要下载的文件模式 (使用正则表达式)
# 匹配英文和中文的 all_maxi, all_nopic, top_maxi
patterns = [
    # r"wikipedia_en_all_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_en_all_nopic_(\d{4}-\d{2})\.zim",
    # r"wikipedia_en_top_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_zh_all_maxi_(\d{4}-\d{2})\.zim",
    # r"wikipedia_zh_all_nopic_(\d{4}-\d{2})\.zim",
    r"wikipedia_zh_top_maxi_(\d{4}-\d{2})\.zim",
    
]

# --- 获取网页内容 ---
print(f"正在从 {INDEX_URL} 获取目录列表...")
try:
    response = requests.get(INDEX_URL, timeout=60)
    response.raise_for_status() # 如果状态码不是 200，会抛出异常
    # print(response.text[:1000]) # 打印前1000个字符看看
    index_content = response.text
    print("目录列表获取成功。")
except requests.exceptions.RequestException as e:
    print(f"获取目录列表时出错: {e}")
    exit(1)

# --- 解析和下载逻辑 ---
# 用于存储每种模式下找到的最新文件
latest_files = defaultdict(lambda: {"filename": "", "date": ""})

# 编译正则表达式以提高效率
compiled_patterns = [re.compile(p) for p in patterns]

# --- 新的解析逻辑：从 HTML 中提取 .zim 文件链接 ---
# 使用正则表达式查找所有指向 .zim 文件的 <a> 标签
# 这个模式匹配 <a href="...filename.zim"> 中的 filename.zim
zim_link_pattern = re.compile(r'<a href="(wikipedia_[^"]+\.zim)">')

# 在整个 HTML 内容中查找所有匹配项
all_zim_filenames = zim_link_pattern.findall(index_content)

print(f"Debug: 从 HTML 中找到了 {len(all_zim_filenames)} 个 .zim 文件链接。")

# 遍历所有找到的文件名
for filename in all_zim_filenames:
    # print(f"Debug: Processing {filename}") # 可选：打印每个处理的文件名
    # 检查文件名是否匹配任何我们定义的模式
    for pattern in compiled_patterns:
        pattern_match = pattern.search(filename)
        if pattern_match:
            # 提取日期
            date_str = pattern_match.group(1) # 获取第一个捕获组 (日期)
            key = pattern.pattern # 使用模式字符串作为 key

            # 比较日期，保留最新的
            if date_str > latest_files[key]["date"]:
                latest_files[key]["filename"] = filename
                latest_files[key]["date"] = date_str
            # (可选) 如果日期相同，也可以处理，但对于文件名唯一的场景，通常不需要

# --- 生成下载链接或调用 wget ---
print("\n找到的最新文件:")
download_urls = []
for key, info in latest_files.items():
    if info["filename"]:
        # 构造完整的下载 URL (确保 INDEX_URL 以 / 结尾)
        url = INDEX_URL.rstrip('/') + '/' + info["filename"]
        download_urls.append(url)
        print(f"  - {url} (日期: {info['date']})")

if not download_urls:
    print("未找到匹配的文件。请检查 patterns 正则表达式是否正确。")
    # 调试：打印前几个找到的文件名，检查格式
    print("\nDebug: 前10个找到的文件名示例:")
    for fn in list(all_zim_filenames)[:10]:
        print(f"  - {fn}")
    exit(0)

# --- 方法 1: 生成一个 URL 列表文件，供 wget -i 使用 ---
url_list_file = os.path.join(DOWNLOAD_DIR, "urls_to_download.txt")
# try:
#     with open(url_list_file, 'w') as f:
#         for url in download_urls:
#             f.write(url + '\n')
#     print(f"\n下载链接已保存到: {url_list_file}")
#     print(f"你可以运行以下命令来下载:")
#     print(f"  wget -nc -P '{DOWNLOAD_DIR}' -i '{url_list_file}'")
# except Exception as e:
#     print(f"保存 URL 列表时出错: {e}")

# --- 方法 2: 直接在 Python 中调用 wget 下载 ---
print("\n开始调用 wget 下载...")
for url in download_urls:
    try:
        # 构造 wget 命令
        # 使用 shell=True 来处理路径中的空格等，但要注意安全问题
        cmd = f"wget -c -P '{DOWNLOAD_DIR}' '{url}'"
        print(f"执行: {cmd}")
        # 调用 wget
        # 使用 shell=True 需要小心命令注入，但在这里 URL 来源相对可信
        result = subprocess.run(cmd, shell=True, check=True)
        print(f"成功下载: {url}")
    except subprocess.CalledProcessError as e:
        print(f"wget 下载 {url} 时失败 (退出码 {e.returncode}): {e}")
    except FileNotFoundError:
        print("错误：系统中未找到 wget 命令。请先安装 wget。")
        break # 如果没有 wget，后续的也无法执行
print("所有文件下载尝试已完成。")
