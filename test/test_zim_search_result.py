# test/test_zim_search.py
import os
from libzim.reader import Archive
from libzim.search import Query, Searcher
from markitdown import MarkItDown

def demonstrate_detailed_search(zim_file_path, search_term="Microsoft_Publisher"):
    """
    演示如何使用 libzim 进行搜索并获取详细的条目信息。
    """
    print(f"=== 演示 ZIM 搜索: '{search_term}' ===")
    
    # 初始化 MarkItDown 转换器 (可以复用)
    md_converter = MarkItDown()

    if not os.path.exists(zim_file_path):
        print(f"错误: 找不到 ZIM 文件 '{zim_file_path}'")
        return

    try:
        # 1. 打开 ZIM 文件
        zim_archive = Archive(zim_file_path)
        print(f"ZIM 文件已打开。")
        print(f"  文章总数: {zim_archive.article_count}")

        # 2. 创建搜索器
        searcher = Searcher(zim_archive)

        # 3. 创建查询
        query = Query().set_query(search_term)
        
        # 4. 执行搜索
        print(f"正在搜索关键词: '{search_term}' ...")
        search = searcher.search(query)
        
        # 5. 获取估计的匹配数量
        estimated_matches = search.getEstimatedMatches()
        print(f"估计匹配数量: {estimated_matches}")

        if estimated_matches > 0:
            # 6. 获取实际的搜索结果 (路径列表)
            # 我们只获取第一个结果来详细展示
            num_results_to_fetch = min(1, estimated_matches)
            results_set = search.getResults(0, num_results_to_fetch)
            
            print(f"\n--- 处理搜索结果 ---")
            result_count = 0
            for path in results_set:
                if result_count >= num_results_to_fetch:
                    break
                    
                print(f"\n--- 结果 {result_count + 1} ---")
                print(f"路径: {path}")
                
                # 7. 使用路径获取完整的条目 (Entry) 对象
                try:
                    entry = zim_archive.get_entry_by_path(path)
                    print(f"标题: {entry.title}")
                    namespace = path.split('/')[0] if '/' in path else 'A'
                    print(f"命名空间 (从路径推断): {namespace}")
                    print(f"条目路径: {entry.path}")

                    # 8. 从条目获取内容项 (Item) 对象
                    try:
                        item = entry.get_item()
                        print(f"内容大小: {item.size} 字节")
                        print(f"MIME 类型: {item.mimetype}")

                        # 9. 获取并显示内容预览
                        if item.mimetype.startswith('text/'):
                            try:
                                content_bytes = bytes(item.content)
                                try:
                                    content_str = content_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    try:
                                        content_str = content_bytes.decode('latin-1')
                                    except UnicodeDecodeError:
                                        content_str = f"<Binary data or unknown encoding, size: {len(content_bytes)} bytes>"

                                if isinstance(content_str, str):
                                    preview_length = 500
                                    if len(content_str) > preview_length:
                                        print(f"HTML 内容预览 (前{preview_length}字符):\n{repr(content_str[:preview_length])}...")
                                    else:
                                        print(f"HTML 内容预览:\n{repr(content_str)}")

                                    if item.mimetype == 'text/html':
                                        try:
                                            md_result = md_converter.convert(content_str)
                                            markdown_text = md_result.text
                                            print(f"\n--- 转换为 Markdown (前1000字符) ---")
                                            output_length = min(1000, len(markdown_text))
                                            print(markdown_text[:output_length])
                                            if len(markdown_text) > 1000:
                                                print("... (Markdown 内容省略) ...")
                                        except Exception as md_e:
                                            print(f"将 HTML 转换为 Markdown 时出错: {md_e}")
                                            import traceback
                                            traceback.print_exc()
                                else:
                                    print(f"警告: 解码后的内容不是字符串，类型为 {type(content_str)}")

                            except Exception as content_e:
                                print(f"读取或解码内容时出错: {content_e}")
                    except Exception as item_e:
                        print(f"获取条目内容 (get_item) 时出错: {item_e}")
                        import traceback
                        traceback.print_exc()

                except Exception as entry_e:
                    print(f"获取条目 (get_entry_by_path) 时出错: {entry_e}")
                    import traceback
                    traceback.print_exc()

                result_count += 1
            
            print(f"\n总共处理了 {result_count} 个结果。")

        else:
            print(f"没有找到匹配项 '{search_term}'。")

    except Exception as e:
        print(f"处理 ZIM 文件时发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    zim_path = "./wiki_zim_downloads/wikipedia_zh_top_maxi_2025-07.zim"
    # 你可以通过命令行参数传递搜索词
    # import sys
    # search_term = sys.argv[1] if len(sys.argv) > 1 else "Microsoft_Publisher"
    
    # 测试几个不同的词
    test_terms = ["人工智能", "Python", "Microsoft_Publisher"]
    for term in test_terms:
        demonstrate_detailed_search(zim_path, term)
        print("\n" + "="*50 + "\n") # 分隔符
        # 为了不输出太多，只测试第一个
        break
