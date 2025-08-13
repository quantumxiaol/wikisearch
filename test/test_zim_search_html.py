import os
from libzim.reader import Archive
from libzim.search import Query, Searcher
from markitdown import MarkItDown

def get_search_result_html(zim_archive, search_term, result_index=0):
    """
    第一步：根据搜索词获取 ZIM 条目内容（HTML 字符串）。

    Args:
        zim_archive (libzim.reader.Archive): 已打开的 ZIM 文件对象。
        search_term (str): 要搜索的关键词。
        result_index (int): 要获取的搜索结果的索引（默认第一个）。

    Returns:
        tuple: (成功标志 (bool), 标题 (str), HTML 内容 (str 或 None), 错误信息 (str 或 None))
    """
    try:
        print(f"正在搜索关键词: '{search_term}' ...")
        searcher = Searcher(zim_archive)
        query = Query().set_query(search_term)
        search = searcher.search(query)
        estimated_matches = search.getEstimatedMatches()
        print(f"估计匹配数量: {estimated_matches}")

        if estimated_matches > 0:
            # 获取指定索引的结果路径
            results_set = search.getResults(result_index, 1)
            path_list = list(results_set)
            if not path_list:
                return False, "", None, f"无法获取第 {result_index} 个搜索结果的路径。"
            
            path = path_list[0]
            print(f"获取到第 {result_index + 1} 个结果的路径: {path}")

            # 获取条目和内容
            entry = zim_archive.get_entry_by_path(path)
            title = entry.title
            print(f"条目标题: {title}")

            item = entry.get_item()
            if not item.mimetype.startswith('text/'):
                return False, title, None, f"条目内容不是文本类型，MIME类型: {item.mimetype}"

            if item.mimetype != 'text/html':
                print(f"警告: 条目 MIME 类型是 '{item.mimetype}'，不是标准的 'text/html'，但仍尝试处理。")

            content_bytes = bytes(item.content)
            
            # 解码 HTML 内容
            try:
                html_content_str = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    html_content_str = content_bytes.decode('latin-1')
                except UnicodeDecodeError:
                    return False, title, None, f"无法使用 UTF-8 或 Latin-1 解码内容 (大小: {len(content_bytes)} 字节)。"

            print(f"成功获取 HTML 内容，大小: {len(html_content_str)} 字符。")
            return True, title, html_content_str, None

        else:
            return False, "", None, f"没有找到匹配项 '{search_term}'。"

    except Exception as e:
        error_msg = f"搜索或获取内容时发生错误: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, "", None, error_msg


def convert_html_to_markdown(html_content_str, title=""):
    """
    第二步：使用 markitdown 将 HTML 字符串转换为 Markdown。

    Args:
        html_content_str (str): 要转换的 HTML 字符串。
        title (str): 条目的标题，用于可能的文件名生成。

    Returns:
        tuple: (成功标志 (bool), Markdown 内容 (str 或 None), 错误信息 (str 或 None))
    """
    if not isinstance(html_content_str, str):
        return False, None, "输入内容不是字符串。"

    try:
        print("正在使用 markitdown 转换 HTML 为 Markdown...")
        md_converter = MarkItDown() # 可以在类/模块级别复用
        md_result = md_converter.convert(html_content_str)
        markdown_text = md_result.text
        print(f"转换成功，Markdown 大小: {len(markdown_text)} 字符。")
        return True, markdown_text, None

    except Exception as e:
        error_msg = f"转换 Markdown 时出错: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, None, error_msg

def demonstrate_detailed_search(zim_file_path, search_term="Microsoft_Publisher"):
    """
    演示完整的两步搜索和转换流程。
    """
    print(f"=== 演示 ZIM 搜索和转换: '{search_term}' ===")

    if not os.path.exists(zim_file_path):
        print(f"错误: 找不到 ZIM 文件 '{zim_file_path}'")
        return

    try:
        # 1. 打开 ZIM 文件
        zim_archive = Archive(zim_file_path)
        print(f"ZIM 文件已打开。")
        print(f"  文章总数: {zim_archive.article_count}")

        # --- 第一步：获取 HTML ---
        print("\n--- 第一步：获取搜索结果的 HTML 内容 ---")
        success_get, title, html_content, error_get = get_search_result_html(zim_archive, search_term, 0)

        if not success_get:
            print(f"第一步失败: {error_get}")
            return

        print(f"标题: {title}")
        preview_len = 200
        print(f"HTML 内容预览 (前{preview_len}字符):\n{repr(html_content[:preview_len])}...")

        # --- 第二步：转换为 Markdown ---
        print("\n--- 第二步：使用 markitdown 转换为 Markdown ---")
        success_convert, markdown_content, error_convert = convert_html_to_markdown(html_content, title)

        if not success_convert:
            print(f"第二步失败: {error_convert}")
            return

        print(f"标题: {title}")
        md_preview_len = 500
        print(f"Markdown 内容预览 (前{md_preview_len}字符):\n{markdown_content[:md_preview_len]}...")
        if len(markdown_content) > md_preview_len:
            print("... (Markdown 内容省略) ...")

        # --- 可选：保存结果 ---
        # import re
        # safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        # safe_title = re.sub(r'[-\s]+', '_', safe_title)
        # html_filename = f"{safe_title}.html"
        # md_filename = f"{safe_title}.md"
        # try:
        #     with open(html_filename, 'w', encoding='utf-8') as f_html:
        #         f_html.write(html_content)
        #     with open(md_filename, 'w', encoding='utf-8') as f_md:
        #         f_md.write(markdown_content)
        #     print(f"\nHTML 内容已保存到: {html_filename}")
        #     print(f"Markdown 内容已保存到: {md_filename}")
        # except Exception as save_e:
        #     print(f"保存文件时出错: {save_e}")

    except Exception as e:
        print(f"处理 ZIM 文件时发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    zim_path = "./wiki_zim_downloads/wikipedia_zh_top_maxi_2025-07.zim"
    
    # 测试几个不同的词
    test_terms = ["人工智能", "Python", "Microsoft_Publisher"]
    for term in test_terms:
        demonstrate_detailed_search(zim_path, term)
        print("\n" + "="*50 + "\n") # 分隔符
        # 为了不输出太多，只测试第一个
        break
