# test/test_zim.py
import sys
import os
from libzim.reader import Archive
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher

def test_direct_zim_search(zim_file_path):
    """
    直接使用 libzim 库测试 ZIM 文件的读取和搜索功能。
    """
    print(f"=== 开始测试 ZIM 文件: {zim_file_path} ===")

    if not os.path.exists(zim_file_path):
        print(f"错误: 找不到 ZIM 文件 '{zim_file_path}'")
        return

    try:
        zim_archive = Archive(zim_file_path)
        print(f"  成功打开。文章总数: {zim_archive.article_count}")
        print(f"  UUID: {zim_archive.uuid}")

        try:
            if zim_archive.main_entry:
                main_item = zim_archive.main_entry.get_item()
                print(f"  主条目路径: {main_item.path}")
                print(f"  主条目标题: {zim_archive.main_entry.title}")
            else:
                print("  未找到主条目。")
        except Exception as e:
            print(f"  获取主条目时出错: {e}")

        # --- 再次修改后的搜索部分 ---
        print("\n--- 开始全文搜索测试 ---")
        search_terms = ["Python", "人工智能", "Microsoft", "Publisher", "Office"]
        searcher = Searcher(zim_archive)

        for term in search_terms:
            print(f"\n  搜索关键词: '{term}'")
            try:
                query = Query().set_query(term)
                search = searcher.search(query)
                estimated_matches = search.getEstimatedMatches()
                print(f"    估计匹配数量: {estimated_matches}")

                if estimated_matches > 0:
                    num_to_fetch = min(5, estimated_matches)
                    try:
                        # --- 关键修改：检查 getResults 返回值的类型 ---
                        results_raw = search.getResults(0, num_to_fetch)
                        print(f"    getResults 返回类型: {type(results_raw)}, 内容: {results_raw}")

                        # 如果返回的是字符串列表 (路径列表)
                        if isinstance(results_raw, list) and len(results_raw) > 0 and isinstance(results_raw[0], str):
                            print(f"    成功获取 {len(results_raw)} 个路径结果:")
                            for i, path in enumerate(results_raw):
                                # 使用路径获取完整条目信息
                                try:
                                    entry = zim_archive.get_entry_by_path(path)
                                    print(f"      {i+1}. 标题: '{entry.title}', 路径: '{entry.path}'")
                                except Exception as entry_e:
                                    print(f"        获取路径 '{path}' 的条目信息失败: {entry_e}")
                        # 如果返回的是 SearchResult 对象列表 (不太可能，但以防万一)
                        elif hasattr(results_raw, '__iter__'): # 检查是否可迭代
                             results_list = list(results_raw)
                             print(f"    成功获取 {len(results_list)} 个对象结果:")
                             for i, result in enumerate(results_list):
                                 if hasattr(result, 'path') and hasattr(result, 'title'):
                                     print(f"      {i+1}. 标题: '{result.title}', 路径: '{result.path}'")
                                 else:
                                     # 如果对象没有 path/title，尝试打印对象本身
                                     print(f"      {i+1}. 结果对象: {result} (类型: {type(result)})")
                        else:
                            print(f"    getResults 返回了意外的类型: {type(results_raw)}")

                    except Exception as results_e:
                        print(f"    调用 getResults 或处理结果时出错: {results_e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"    没有找到匹配项。")

            except Exception as e:
                print(f"    搜索 '{term}' 时出错: {e}")
                import traceback
                traceback.print_exc()

        # --- 再次修改后的建议部分 ---
        print("\n--- 开始建议功能测试 ---")
        suggestion_terms = ["Py", "Micro", "人工智能"]
        suggestion_searcher = SuggestionSearcher(zim_archive)

        for term in suggestion_terms:
            print(f"\n  获取 '{term}' 的建议:")
            try:
                suggestion = suggestion_searcher.suggest(term)
                estimated_suggestions = suggestion.getEstimatedMatches()
                print(f"    估计建议数量: {estimated_suggestions}")

                if estimated_suggestions > 0:
                    num_to_fetch = min(5, estimated_suggestions)
                    try:
                        # --- 关键修改：检查 getResults 返回值的类型 ---
                        suggestions_raw = suggestion.getResults(0, num_to_fetch)
                        print(f"    getResults 返回类型: {type(suggestions_raw)}, 内容: {suggestions_raw}")

                        # 如果返回的是字符串列表 (路径列表)
                        if isinstance(suggestions_raw, list) and len(suggestions_raw) > 0 and isinstance(suggestions_raw[0], str):
                            print(f"    成功获取 {len(suggestions_raw)} 个建议路径:")
                            for i, path in enumerate(suggestions_raw):
                                # 使用路径获取完整条目信息
                                try:
                                    entry = zim_archive.get_entry_by_path(path)
                                    print(f"      {i+1}. 标题: '{entry.title}', 路径: '{entry.path}'")
                                except Exception as entry_e:
                                    print(f"        获取建议路径 '{path}' 的条目信息失败: {entry_e}")
                        # 如果返回的是 SuggestionResult 对象列表 (不太可能，但以防万一)
                        elif hasattr(suggestions_raw, '__iter__'):
                             suggestions_list = list(suggestions_raw)
                             print(f"    成功获取 {len(suggestions_list)} 个建议对象:")
                             for i, suggestion_result in enumerate(suggestions_list):
                                 if hasattr(suggestion_result, 'path') and hasattr(suggestion_result, 'title'):
                                     print(f"      {i+1}. 标题: '{suggestion_result.title}', 路径: '{suggestion_result.path}'")
                                 else:
                                     print(f"      {i+1}. 建议对象: {suggestion_result} (类型: {type(suggestion_result)})")
                        else:
                            print(f"    getResults 返回了意外的类型: {type(suggestions_raw)}")

                    except Exception as suggestions_e:
                        print(f"    调用 getResults 或处理建议结果时出错: {suggestions_e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"    没有找到相关建议。")

            except Exception as e:
                print(f"    获取 '{term}' 的建议时出错: {e}")
                import traceback
                traceback.print_exc()
        # --- 修改结束 ---

    except Exception as e:
        print(f"打开或处理 ZIM 文件时发生致命错误: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n=== ZIM 文件测试结束 ===")


if __name__ == "__main__":
    zim_path = "./wiki_zim_downloads/wikipedia_zh_top_maxi_2025-07.zim"
    test_direct_zim_search(zim_path)