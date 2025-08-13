#! /usr/bin/env python3

"""
python src/wikisearch/zim_downloader.py --languages zh --types top_maxi --download
"""
import re
import os
import subprocess
import requests
import argparse  
from collections import defaultdict

from wikisearch.config import config


# --- 配置 ---
# 实时获取的 URL 
INDEX_URL = "https://download.kiwix.org/zim/wikipedia/"
# 本地保存目录
DOWNLOAD_DIR = config.WIKI_DOWNLOAD_DIR
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- 新增：定义所有可用的模式 ---
# 这样可以通过命令行参数组合选择
ALL_PATTERNS = {
    # 英文
    'en_all_maxi': r"wikipedia_en_all_maxi_(\d{4}-\d{2})\.zim",
    'en_all_nopic': r"wikipedia_en_all_nopic_(\d{4}-\d{2})\.zim",
    'en_top_maxi': r"wikipedia_en_top_maxi_(\d{4}-\d{2})\.zim",
    # 中文
    'zh_all_maxi': r"wikipedia_zh_all_maxi_(\d{4}-\d{2})\.zim",
    'zh_all_nopic': r"wikipedia_zh_all_nopic_(\d{4}-\d{2})\.zim",
    'zh_top_maxi': r"wikipedia_zh_top_maxi_(\d{4}-\d{2})\.zim",
    # 可以在这里添加更多语言...
}

# --- 使用 argparse 设置命令行参数 ---
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="从 KiwiX 下载维基百科 ZIM 文件。",
        epilog="示例: python script.py --languages zh --types all_maxi all_nopic --download"
    )
    
    # 添加参数：选择语言 (例如: zh, en)
    parser.add_argument(
        '--languages', '-l',
        nargs='+',  # 允许接收多个值
        default=['zh'],  # 默认只下载中文
        help='要下载的语言代码列表 (例如: zh en fr)。默认: zh'
    )
    
    # 添加参数：选择文件类型 (例如: all_maxi, all_nopic, top_maxi)
    parser.add_argument(
        '--types', '-t',
        nargs='+',
        default=['top_maxi'], # 默认下载 top_maxi 版本
        choices=['all_maxi', 'all_nopic', 'top_maxi'], # 限制可选值
        help='要下载的文件类型。可选: all_maxi, all_nopic, top_maxi。默认: top_maxi'
    )
    
    # 添加参数：是否执行下载 (store_true 意味着如果提供了这个参数，值就是 True)
    parser.add_argument(
        '--download', '-d',
        action='store_true',
        help='如果提供此参数，则自动开始下载。否则只列出匹配的文件。'
    )
    
    # 添加参数：指定下载目录
    parser.add_argument(
        '--output-dir', '-o',
        default=DOWNLOAD_DIR,
        help=f'指定下载目录。默认: {DOWNLOAD_DIR}'
    )

    return parser.parse_args()

# --- 主函数 ---
def main():
    # 解析命令行参数
    args = parse_arguments()
    
    # 使用命令行参数更新配置
    selected_languages = args.languages
    selected_types = args.types
    perform_download = args.download
    global DOWNLOAD_DIR # 如果需要在函数内修改全局变量
    DOWNLOAD_DIR = args.output_dir
    os.makedirs(DOWNLOAD_DIR, exist_ok=True) # 确保目录存在

    # --- 根据命令行参数动态构建 patterns 列表 ---
    patterns = []
    for lang in selected_languages:
        for type_ in selected_types:
            key = f"{lang}_{type_}"
            if key in ALL_PATTERNS:
                patterns.append(ALL_PATTERNS[key])
            else:
                print(f"警告: 未找到语言 '{lang}' 和类型 '{type_}' 的预定义模式。")

    if not patterns:
        print("错误: 没有有效的模式被选中。请检查 --languages 和 --types 参数。")
        return

    print(f"已选择语言: {selected_languages}")
    print(f"已选择类型: {selected_types}")
    print(f"构建的模式: {patterns}")
    print(f"下载目录: {DOWNLOAD_DIR}")
    if perform_download:
        print("下载模式: 已启用")
    else:
        print("下载模式: 仅列出文件 (使用 --download 或 -d 开始下载)")

    # --- 获取网页内容 ---
    print(f"\n正在从 {INDEX_URL} 获取目录列表...")
    try:
        response = requests.get(INDEX_URL, timeout=60)
        response.raise_for_status()
        index_content = response.text
        print("目录列表获取成功。")
    except requests.exceptions.RequestException as e:
        print(f"获取目录列表时出错: {e}")
        return # 使用 return 而不是 exit(1)

    # --- 解析和下载逻辑 ---
    latest_files = defaultdict(lambda: {"filename": "", "date": ""})
    compiled_patterns = [re.compile(p) for p in patterns]

    # --- 新的解析逻辑：从 HTML 中提取 .zim 文件链接 ---
    zim_link_pattern = re.compile(r'<a href="(wikipedia_[^"]+\.zim)">')
    all_zim_filenames = zim_link_pattern.findall(index_content)
    print(f"Debug: 从 HTML 中找到了 {len(all_zim_filenames)} 个 .zim 文件链接。")

    # 遍历所有找到的文件名
    for filename in all_zim_filenames:
        for pattern in compiled_patterns:
            pattern_match = pattern.search(filename)
            if pattern_match:
                date_str = pattern_match.group(1)
                key = pattern.pattern
                if date_str > latest_files[key]["date"]:
                    latest_files[key]["filename"] = filename
                    latest_files[key]["date"] = date_str

    # --- 生成下载链接 ---
    print("\n找到的最新文件:")
    download_urls = []
    for key, info in latest_files.items():
        if info["filename"]:
            url = INDEX_URL.rstrip('/') + '/' + info["filename"]
            download_urls.append(url)
            print(f"  - {url} (日期: {info['date']})")

    if not download_urls:
        print("未找到匹配的文件。请检查 --languages 和 --types 参数。")
        return

    # --- 根据 --download 参数决定是否下载 ---
    if perform_download:
        print("\n开始调用 wget 下载 (支持断点续传)...")
        for url in download_urls:
            try:
                # 构造 wget 命令，支持断点续传
                cmd = f"wget -c -P '{DOWNLOAD_DIR}' --progress=bar --timeout=60 --tries=3 '{url}'"
                print(f"执行: {cmd}")
                result = subprocess.run(cmd, shell=True, check=True)
                print(f"成功下载或续传完成: {url}")
            except subprocess.CalledProcessError as e:
                print(f"wget 下载 {url} 时失败 (退出码 {e.returncode}): {e}")
            except FileNotFoundError:
                print("错误：系统中未找到 wget 命令。请先安装 wget。")
                return # 如果没有 wget，无法继续
        print("所有文件下载尝试已完成。")
    else:
        print("\n已列出匹配的文件。如需下载，请添加 --download 或 -d 参数。")
        # 可选：也生成 urls_to_download.txt 文件
        url_list_file = os.path.join(DOWNLOAD_DIR, "urls_to_download.txt")
        try:
            with open(url_list_file, 'w') as f:
                for url in download_urls:
                    f.write(url + '\n')
            print(f"下载链接已保存到: {url_list_file}")
            print(f"你可以手动运行以下命令来下载:")
            print(f"  wget -c -P '{DOWNLOAD_DIR}' -i '{url_list_file}'")
        except Exception as e:
            print(f"保存 URL 列表时出错: {e}")

if __name__ == "__main__":
    main()