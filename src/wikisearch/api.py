import os
import glob
from pathlib import Path
from typing import List, Dict, Optional,Union,Tuple
from wikisearch.zim.zim_searcher import ZIMSearcher
from libzim.reader import Archive
import time

from wikisearch.config import config
DEFAULT_ZIM_DIR = config.WIKI_DOWNLOAD_DIR
ZIM_FILE_PATTERN = "*.zim"

class WikiSearchAPI:
    """
    Wiki搜索API接口 (基于 libzim，直接搜索 ZIM 文件)。
    支持从目录加载多个 ZIM 文件。
    """

    def __init__(self, zim_source: Optional[Union[str, List[str]]] = None):
        """
        初始化 WikiSearchAPI。

        Args:
            zim_source (str or list[str], optional):
                - 如果是字符串：
                    - 且是一个存在的文件：则加载该单个 ZIM 文件。
                    - 且是一个存在的目录：则加载该目录下所有 .zim 文件。
                - 如果是字符串列表：则加载列表中的所有 ZIM 文件路径。
                - 如果为 None：则使用配置中的默认目录，并加载其中所有 .zim 文件。
        Raises:
            FileNotFoundError: 如果指定的文件或目录不存在。
            ValueError: 如果提供的路径列表为空或无效。
        """
        self.zim_paths: List[str] = []

        if zim_source is None:
            # 使用默认目录
            zim_source = DEFAULT_ZIM_DIR

        if isinstance(zim_source, str):
            path_obj = Path(zim_source)
            if not path_obj.exists():
                raise FileNotFoundError(f"Path not found: {zim_source}")

            if path_obj.is_file():
                # 单个文件
                if path_obj.suffix.lower() == '.zim':
                    self.zim_paths = [str(path_obj)]
                else:
                    raise ValueError(f"Provided file is not a .zim file: {zim_source}")
            elif path_obj.is_dir():
                # 目录，查找所有 .zim 文件
                zim_pattern_full = str(path_obj / ZIM_FILE_PATTERN)
                found_zims = glob.glob(zim_pattern_full)
                if not found_zims:
                    print(f"Warning: No .zim files found in directory: {zim_source}")
                self.zim_paths = sorted(found_zims) # 排序以保证一致性
            else:
                raise ValueError(f"Provided path is neither a file nor a directory: {zim_source}")

        elif isinstance(zim_source, (list, tuple)):
            # 路径列表
            validated_paths = []
            for p in zim_source:
                p_obj = Path(p)
                if not p_obj.exists():
                    raise FileNotFoundError(f"ZIM file not found: {p}")
                if p_obj.is_file() and p_obj.suffix.lower() == '.zim':
                    validated_paths.append(str(p_obj))
                else:
                    print(f"Warning: Skipping invalid or non-.zim path: {p}")
            if not validated_paths:
                raise ValueError("No valid .zim files provided in the list.")
            self.zim_paths = validated_paths
        else:
            raise TypeError("zim_source must be a string (file/dir path) or a list/tuple of strings (file paths).")

        if not self.zim_paths:
             raise ValueError("No valid ZIM files were found or provided.")

        # 验证所有最终确定的路径确实存在 (冗余检查，但更安全)
        for path in self.zim_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"ZIM file not found: {path}")

        # 创建内部的 ZIMSearcher 实例
        # ZIMSearcher 可以处理多个文件
        try:
            # 将找到的所有 ZIM 文件路径传递给 ZIMSearcher
            self._searcher = ZIMSearcher(self.zim_paths)
            print(f"WikiSearchAPI initialized with ZIM file(s): {self.zim_paths}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ZIMSearcher: {e}") from e

    def search(self, query: str, result_index: int = 0) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        核心搜索方法：在 ZIM 文件中搜索并返回 HTML 内容。

        Args:
            query (str): 搜索关键词。
            result_index (int): 要获取的搜索结果的索引（默认第一个）。

        Returns:
            tuple: (成功标志 (bool), 标题 (str), HTML 内容 (str 或 None), 错误信息 (str 或 None))
                   - 如果成功：(True, title, html_content_str, None)
                   - 如果失败：(False, "", None, error_message)
        """
        # 直接调用内部 ZIMSearcher 的方法
        return self._searcher.search_and_get_html(search_term=query, result_index=result_index)

    # --- 便捷方法，封装搜索以返回更结构化的数据 ---
    def search_article(self, query: str, result_index: int = 0) -> Dict[str, Union[bool, str, None]]:
        """
        搜索文章并返回结构化结果。

        Args:
            query (str): 搜索关键词。
            result_index (int): 结果索引。

        Returns:
            dict: 包含 'success', 'title', 'html', 'error' 键的字典。
        """
        success, title, html_content, error = self.search(query, result_index)
        return {
            "success": success,
            "title": title,
            "html": html_content, # 关键：返回 HTML 内容
            "error": error
        }
    # --- 便捷方法结束 ---

    # --- 元数据获取 ---
    def get_metadata(self) -> List[Dict]:
        """
        获取所有已加载 ZIM 文件的元数据。

        Returns:
            list[dict]: 每个 ZIM 文件的元数据字典组成的列表。
        """
        # 复用 ZIMSearcher 中的逻辑或直接调用其方法
        # 这里直接调用 ZIMSearcher 的方法
        try:
            # 假设 ZIMSearcher 有一个方法可以返回类似信息
            # 如果没有，可以像之前那样重新打开文件读取
            # 为了简单，我们调用一个可能存在的方法
            # 如果 ZIMSearcher 没有 list_open_zims_info，我们需要调整
            open_paths = self._searcher.list_open_zims()
            
            # 由于 ZIMSearcher 没有直接暴露 Archive 对象来获取详细元数据，
            # 我们需要一种方式。这里提供一个基础实现：
            # （理想情况下，ZIMSearcher 应该提供更丰富的信息获取方法）
            metadata_list = []
            
            for path in open_paths:
                try:
                    archive = Archive(path)
                    metadata = {
                        'path': path,
                        'filename': os.path.basename(path),
                        'article_count': getattr(archive, 'article_count', 'N/A'),
                        'uuid': str(getattr(archive, 'uuid', 'unknown')),
                    }
                    # 尝试获取主入口
                    try:
                        if archive.main_entry:
                            metadata['main_path'] = archive.main_entry.get_item().path
                    except Exception:
                         pass
                    metadata_list.append(metadata)
                except Exception as e:
                     metadata_list.append({'path': path, 'error': f"Failed to read metadata: {e}"})
            return metadata_list
        except Exception as e:
            return [{'error': f"Failed to get ZIM list from searcher: {e}"}]

    def list_zim_files(self) -> List[str]:
        """
        列出当前 API 实例管理的所有 ZIM 文件路径。

        Returns:
            list[str]: ZIM 文件路径列表。
        """
        return self._searcher.list_open_zims()

    # --- 管理 ZIM 文件 ---
    def add_zim(self, zim_path: str) -> bool:
        """
        添加一个新的 ZIM 文件到搜索范围。

        Args:
            zim_path (str): ZIM 文件路径。

        Returns:
            bool: 是否成功添加。
        """
        if not os.path.exists(zim_path):
             print(f"Error: ZIM file not found: {zim_path}")
             return False
        # 更新内部路径列表和 searcher
        if zim_path not in self.zim_paths:
            self.zim_paths.append(zim_path)
        return self._searcher.add_zim(zim_path)

    def remove_zim(self, zim_path: str) -> bool:
        """
        从搜索范围中移除一个 ZIM 文件。

        Args:
            zim_path (str): ZIM 文件路径。

        Returns:
            bool: 是否成功移除。
        """
        # 更新内部路径列表和 searcher
        if zim_path in self.zim_paths:
            self.zim_paths.remove(zim_path)
        return self._searcher.remove_zim(zim_path)
    # --- 管理方法结束 ---

    def close(self) -> None:
        """关闭所有 ZIM 档案。"""
        self._searcher.close_all()

    # --- 关于 HTML 内容的处理 ---
    def save_html_to_file(self, html_content: str, title: str, output_dir: str = "./output") -> Optional[str]:
        """
        (简单) 将 HTML 内容保存到文件，方便查看。
        注意：这不会修复链接，所以样式和图片可能无法显示，链接也无法点击。

        Args:
            html_content (str): 要保存的 HTML 字符串。
            title (str): 用于生成文件名。
            output_dir (str): 保存文件的目录。

        Returns:
            str or None: 保存的文件路径，如果失败则返回 None。
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            # 简单处理文件名，避免非法字符
            import re
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"{safe_title}.html"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML content saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Failed to save HTML to file: {e}")
            return None


def search_wiki_html(query: str, result_index: int = 0, zim_source: Optional[Union[str, List[str]]] = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    全局便捷函数：根据指定的 ZIM 源（文件、目录或列表）搜索并返回 HTML 内容。

    Args:
        query (str): 搜索关键词。
        result_index (int): 结果索引。
        zim_source (str or list[str], optional): 
            - 字符串：单个 ZIM 文件路径 或 包含 ZIM 文件的目录路径。
            - 列表：ZIM 文件路径列表。
            - None：使用默认目录。

    Returns:
        tuple: (成功标志, 标题, HTML内容, 错误信息)
    """
    try:
        # 创建临时的 API 实例来执行搜索
        api = WikiSearchAPI(zim_source)
        result = api.search(query, result_index)
        api.close() # 确保关闭
        return result
    except Exception as e:
        return False, "", None, str(e)

