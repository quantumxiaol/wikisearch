from wikisearch.api import WikiSearchAPI
# --- 使用示例 ---
if __name__ == "__main__":
    # 1. 从默认目录加载所有 ZIM 文件
    # api = WikiSearchAPI() 

    # 2. 从指定目录加载所有 ZIM 文件
    api = WikiSearchAPI("./wiki_zim_downloads") 

    # 3. 加载指定的单个或多个 ZIM 文件
    # api = WikiSearchAPI(["./wiki_zim_downloads/file1.zim", "./wiki_zim_downloads/file2.zim"])

    print("Loaded ZIM files:", api.list_zim_files())
    print("Metadata:", api.get_metadata())

    # 执行搜索
    result_dict = api.search_article("人工智能")
    if result_dict["success"]:
        print(f"Found article: {result_dict['title']}")
        html_content = result_dict['html']
        print(f"HTML preview: {html_content[:200]}...")

        # 保存 HTML 到文件 (简单查看)
        saved_path = api.save_html_to_file(html_content, result_dict['title'])
        if saved_path:
            print(f"You can open '{saved_path}' in a text editor to view the raw HTML.")
            print("Note: Links and styles might not work correctly when opened directly in a browser.")

        # --- 要获得完整的浏览体验 ---
        print("\n--- To view content properly in a browser ---")
        print("You need a web server that can:")
        print("1. Serve static assets (CSS, JS, images) from the ZIM file.")
        print("2. Handle requests for other articles and fetch their HTML from the ZIM.")
        print("3. Rewrite links in the HTML to point to the server endpoints.")
        print("Consider using existing tools like 'kiwix-serve' for this purpose.")

    else:
        print(f"Search failed: {result_dict['error']}")

    api.close()
