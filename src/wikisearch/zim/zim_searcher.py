import os
import json
import pickle
import re
from pathlib import Path
from typing import List, Dict, Optional,Tuple
from libzim.reader import Archive
from libzim.search import Query, Searcher
from wikisearch.config import config

DEFAULT_ZIM_FILE_PATH=config.ZIM_FILE_PATH


class ZIMSearcher:
    """
    用于搜索 ZIM 文件并检索条目 HTML 内容的类。
    支持处理单个 ZIM 文件，并可以动态切换或同时管理多个文件。
    """

    def __init__(self, zim_file_path: Optional[str] = None):
        """
        初始化 ZIMSearcher。

        Args:
            zim_file_path (str, optional): ZIM 文件的路径。
                                       如果未提供，则使用配置中的默认路径。
                                       如果为列表，则打开多个 ZIM 文件。
        """
        self.default_zim_paths: List[str] = []
        self.current_zim_paths: List[str] = []
        self.zim_archives: List[Archive] = []
        self.searchers: List[Searcher] = []

        # 处理初始化时提供的路径（单个或多个）
        initial_paths = []
        if isinstance(zim_file_path, str):
            initial_paths = [zim_file_path]
        elif isinstance(zim_file_path, (list, tuple)):
            initial_paths = list(zim_file_path)
        # 如果 zim_file_path 为 None 或其他情况，则使用默认路径
        if not initial_paths:
            initial_paths = [DEFAULT_ZIM_FILE_PATH]

        # 打开初始 ZIM 文件
        for path in initial_paths:
            self.add_zim(path)

    def add_zim(self, zim_file_path: str) -> bool:
        """
        添加并打开一个新的 ZIM 文件到搜索器中。

        Args:
            zim_file_path (str): 要添加的 ZIM 文件路径。

        Returns:
            bool: 是否成功添加。
        """
        if not os.path.exists(zim_file_path):
            print(f"Error: ZIM file not found at: {zim_file_path}")
            return False

        if zim_file_path in self.current_zim_paths:
            print(f"ZIM file '{zim_file_path}' is already added.")
            return True

        try:
            archive = Archive(zim_file_path)
            searcher = Searcher(archive) # 为每个 Archive 创建一个 Searcher
            
            self.zim_archives.append(archive)
            self.searchers.append(searcher)
            self.current_zim_paths.append(zim_file_path)
            
            print(f"Successfully added ZIM file: {zim_file_path} (Article count: {archive.article_count})")
            return True
        except Exception as e:
            print(f"Failed to add ZIM file '{zim_file_path}': {e}")
            return False

    def remove_zim(self, zim_file_path: str) -> bool:
        """
        从搜索器中移除一个 ZIM 文件。

        Args:
            zim_file_path (str): 要移除的 ZIM 文件路径。

        Returns:
            bool: 是否成功移除。
        """
        if zim_file_path not in self.current_zim_paths:
            print(f"ZIM file '{zim_file_path}' is not in the list.")
            return False

        try:
            index = self.current_zim_paths.index(zim_file_path)
            # 移除引用，让 Python 垃圾回收处理
            del self.zim_archives[index]
            del self.searchers[index]
            del self.current_zim_paths[index]
            print(f"Successfully removed ZIM file: {zim_file_path}")
            return True
        except Exception as e:
            print(f"Failed to remove ZIM file '{zim_file_path}': {e}")
            return False

    def search_and_get_html(self, search_term: str, result_index: int = 0) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        根据搜索词在所有已添加的 ZIM 文件中搜索，并获取第一个匹配条目的 HTML 内容。

        Args:
            search_term (str): 要搜索的关键词。
            result_index (int): 要获取的搜索结果的索引（默认第一个）。
                           注意：此参数在多ZIM场景下可能需要更复杂的逻辑来确定全局第N个结果。

        Returns:
            tuple: (成功标志 (bool), 标题 (str), HTML 内容 (str 或 None), 错误信息 (str 或 None))
                   - 如果成功：(True, title, html_content_str, None)
                   - 如果失败：(False, "", None, error_message)
                   返回的是在所有 ZIM 文件中找到的第一个匹配项。
        """
        if not self.zim_archives:
            return False, "", None, "No ZIM archives are open."

        try:
            # 遍历所有已打开的 ZIM 文件进行搜索
            for i, (archive, searcher) in enumerate(zip(self.zim_archives, self.searchers)):
                # print(f"Searching in ZIM '{self.current_zim_paths[i]}' for term: '{search_term}' ...")
                
                query = Query().set_query(search_term)
                search = searcher.search(query)
                estimated_matches = search.getEstimatedMatches()
                # print(f"Estimated matches in '{self.current_zim_paths[i]}': {estimated_matches}")

                if estimated_matches > 0:
                    if result_index >= estimated_matches:
                        # 如果当前 ZIM 文件的结果不够，则继续下一个 ZIM 文件
                        # print(f"Requested index {result_index} out of range in '{self.current_zim_paths[i]}'. Checking next ZIM...")
                        continue

                    # 获取指定索引的结果路径
                    results_set = search.getResults(result_index, 1)
                    path_list = list(results_set)
                    if not path_list:
                        # print(f"Failed to retrieve path for result index {result_index} in '{self.current_zim_paths[i]}'. Checking next ZIM...")
                        continue # 尝试下一个 ZIM 文件
                
                    path = path_list[0]
                    # print(f"Found result in '{self.current_zim_paths[i]}', path: {path}")

                    # 获取条目和内容
                    try:
                        entry = archive.get_entry_by_path(path)
                    except Exception as entry_e:
                        # print(f"Failed to get entry by path '{path}' in '{self.current_zim_paths[i]}': {entry_e}. Checking next ZIM...")
                        continue # 尝试下一个 ZIM 文件

                    title = entry.title
                    # print(f"Entry title: {title}")

                    try:
                        item = entry.get_item()
                    except Exception as item_e:
                        return False, title, None, f"Failed to get item for entry '{path}' in '{self.current_zim_paths[i]}': {item_e}"

                    if not item.mimetype.startswith('text/'):
                        return False, title, None, f"Entry content is not text type in '{self.current_zim_paths[i]}', MIME type: {item.mimetype}"

                    try:
                        content_bytes = bytes(item.content)
                    except Exception as content_e:
                        return False, title, None, f"Failed to get content bytes for entry '{path}' in '{self.current_zim_paths[i]}': {content_e}"
                
                    # 解码 HTML 内容
                    html_content_str = None
                    decode_errors = []
                    for encoding in ['utf-8', 'latin-1']: # 尝试常用编码
                        try:
                            html_content_str = content_bytes.decode(encoding)
                            # print(f"Successfully decoded content using {encoding}.")
                            break
                        except UnicodeDecodeError as ue:
                            decode_errors.append(f"{encoding}: {ue}")
                
                    if html_content_str is None:
                        error_msg = f"Failed to decode content (size: {len(content_bytes)} bytes) in '{self.current_zim_paths[i]}' using common encodings. Errors: {'; '.join(decode_errors)}"
                        return False, title, None, error_msg

                    # print(f"Successfully retrieved HTML content, size: {len(html_content_str)} characters.")
                    return True, title, html_content_str, None

            # 如果所有 ZIM 文件都搜索完还没有结果
            return False, "", None, f"No matches found for term '{search_term}' in any of the added ZIM files."

        except Exception as e:
            error_msg = f"Error during search or content retrieval: {e}"
            # import traceback
            # traceback.print_exc() # 可选：打印堆栈
            return False, "", None, error_msg

    def close_all(self) -> None:
        """关闭所有 ZIM 档案。"""
        if self.zim_archives:
            count = len(self.zim_archives)
            self.zim_archives.clear()
            self.searchers.clear()
            closed_paths = self.current_zim_paths.copy()
            self.current_zim_paths.clear()
            print(f"Closed {count} ZIM archive(s): {closed_paths}")

    def list_open_zims(self) -> List[str]:
        """列出当前打开的所有 ZIM 文件路径。"""
        return self.current_zim_paths.copy()

# --- 便捷函数 ---
def search_wiki_html(search_term: str, result_index: int = 0, zim_paths: Optional[List[str]] = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    便捷函数：搜索一个或多个 ZIM 文件并返回 HTML 内容。

    Args:
        search_term (str): 搜索关键词。
        result_index (int): 结果索引。
        zim_paths (list[str], optional): ZIM 文件路径列表。
                                         如果未提供，使用默认路径。

    Returns:
        tuple: (成功标志, 标题, HTML内容, 错误信息)
    """
    try:
        # 根据提供的路径列表创建搜索器
        searcher = ZIMSearcher(zim_paths) # ZIMSearcher 可以处理列表
        
        # 执行搜索
        result = searcher.search_and_get_html(search_term, result_index)
        
        # 关闭所有档案 (实例销毁时会自动清理，但显式调用更清晰)
        searcher.close_all()
        
        return result
    except Exception as e:
        return False, "", None, str(e)

# --- 示例/测试代码 (如果直接运行此脚本) ---
if __name__ == "__main__":
    import sys

    print("--- Example using ZIMSearcher class with potential for multiple ZIMs ---")
    try:
        # 有 ZIM 文件
        zim1_path = DEFAULT_ZIM_FILE_PATH # 使用配置的默认路径
        # zim2_path = "/path/to/another/wiki.zim" # 替换为你的另一个 ZIM 文件路径

        # 1. 创建一个搜索器实例，初始添加一个 ZIM
        searcher = ZIMSearcher(zim1_path)
        print(f"Initial ZIMs open: {searcher.list_open_zims()}")

        # 2. 搜索默认 ZIM 文件
        print(f"\n1. Searching for '人工智能' in added ZIMs")
        success1, title1, html1, error1 = searcher.search_and_get_html("人工智能", 0)
        if success1:
            print(f"   Success! Title: {title1}")
            print(f"   HTML Preview (first 150 chars): {repr(html1[:150])}...")
        else:
            print(f"   Failed! Error: {error1}")

        # 3. (可选) 添加另一个 ZIM 文件并再次搜索
        # if os.path.exists(zim2_path):
        #     print(f"\n2. Adding another ZIM: {zim2_path}")
        #     searcher.add_zim(zim2_path)
        #     print(f"ZIMs open after adding: {searcher.list_open_zims()}")
        #     
        #     print(f"\n3. Searching for 'Python' across all added ZIMs")
        #     success2, title2, html2, error2 = searcher.search_and_get_html("Python", 0)
        #     if success2:
        #         print(f"   Success! Title: {title2}")
        #         print(f"   HTML Preview (first 150 chars): {repr(html2[:150])}...")
        #         # 可以检查 title2 或内容来判断它来自哪个 ZIM
        #     else:
        #         print(f"   Failed! Error: {error2}")
        # else:
        #     print(f"\n2 & 3. Skipping second ZIM addition/search, file not found: {zim2_path}")

        # 4. 再次搜索 (在所有已添加的 ZIM 中)
        print(f"\n4. Searching for '机器学习' across all added ZIMs")
        success3, title3, html3, error3 = searcher.search_and_get_html("机器学习", 0)
        if success3:
            print(f"   Success! Title: {title3}")
            print(f"   HTML Preview (first 150 chars): {repr(html3[:150])}...")
        else:
            print(f"   Failed! Error: {error3}")

        # 5. 关闭所有档案
        searcher.close_all()
        print(f"\n5. All ZIM searchers closed.")

    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n" + "="*50 + "\n")

    # --- 示例使用便捷函数 ---
    print("--- Example using convenience function ---")
    term = "人工智能"
    # 使用默认 ZIM
    print(f"\n1. Searching for: '{term}' using convenience function (default ZIM)")
    success, title, html, error = search_wiki_html(term, 0) # 不指定 zim_paths

    if success:
        print(f"   Success! Title: {title}")
        print(f"   HTML Preview (first 150 chars): {repr(html[:150])}...")
    else:
        print(f"   Failed! Error: {error}")

    # 如果要指定 ZIM 文件路径列表:
    # print(f"\n2. Searching for: '{term}' using convenience function (specific ZIMs)")
    # specific_zims = [zim1_path] # , zim2_path] # 添加更多路径
    # success, title, html, error = search_wiki_html(term, 0, zim_paths=specific_zims)
    # if success:
    #     print(f"   Success! Title: {title}")
    #     print(f"   HTML Preview (first 150 chars): {repr(html[:150])}...")
    # else:
    #     print(f"   Failed! Error: {error}")
