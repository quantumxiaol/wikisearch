import os
from libzim.reader import Archive
from libzim.search import Query, Searcher

def demonstrate_detailed_search(zim_file_path, search_term="Microsoft_Publisher"):
    """
    演示如何使用 libzim 进行搜索并获取详细的条目信息。
    """
    print(f"=== 演示 ZIM 搜索: '{search_term}' ===")

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
                    # --- 修复：从路径中提取命名空间 ---
                    # 命名空间通常是路径的第一个部分，用'/'分隔
                    namespace = path.split('/')[0] if '/' in path else 'A' # 默认为'A'
                    print(f"命名空间 (从路径推断): {namespace}")
                    print(f"条目路径: {entry.path}") # 确认路径

                    # 8. 从条目获取内容项 (Item) 对象
                    # --- 修复：对 get_item() 也进行异常处理 ---
                    try:
                        item = entry.get_item()
                        print(f"内容大小: {item.size} 字节")
                        print(f"MIME 类型: {item.mimetype}")

                        # 9. 获取并显示内容预览 (仅对文本内容)
                        if item.mimetype.startswith('text/'):
                            try:
                                content_bytes = bytes(item.content)
                                # 尝试 UTF-8 解码
                                try:
                                    content_str = content_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    # 如果失败，尝试 Latin-1 或其他方式
                                    try:
                                        content_str = content_bytes.decode('latin-1')
                                    except UnicodeDecodeError:
                                        content_str = f"<Binary data or unknown encoding, size: {len(content_bytes)} bytes>"
                                
                                # 打印内容的前 N 个字符
                                preview_length = 500 # 增加预览长度
                                if len(content_str) > preview_length:
                                    print(f"内容预览 (前{preview_length}字符):\n{repr(content_str[:preview_length])}...")
                                else:
                                    print(f"内容预览:\n{repr(content_str)}")
                                    
                                # 也可以尝试打印可读的前几行
                                print("\n--- 内容前几行 (美化后) ---")
                                lines = content_str.splitlines()
                                for i, line in enumerate(lines[:10]): # 打印前10行
                                    # 限制单行长度输出
                                    display_line = line[:100] + "..." if len(line) > 100 else line
                                    print(f"{i+1:2}: {display_line}")
                                    if i >= 20 and len(line.strip()) == 0: # 避免打印太多空行
                                         break
                                if len(lines) > 10:
                                     print("... (内容省略) ...")
                                     
                            except Exception as content_e:
                                print(f"获取/解码内容时出错: {content_e}")
                        else:
                            print(f"(非文本内容，MIME类型: {item.mimetype})")
                            
                    except Exception as item_e:
                        print(f"从条目获取内容项时出错: {item_e}")
                        
                except Exception as entry_e:
                    print(f"根据路径获取条目 '{path}' 时出错: {entry_e}")
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
        break