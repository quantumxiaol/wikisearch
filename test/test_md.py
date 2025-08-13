from markitdown import MarkItDown

# --- 假设这是你之前保存 HTML 的文件路径 ---
# 例如，使用 WikiSearchAPI.save_html_to_file(...) 保存的
html_file_path = "./output/人工智能.html" 
# ---

try:
    # 1. 创建转换器实例
    md = MarkItDown()
    
    # 2. 将 HTML 文件路径传递给 convert 方法
    #    MarkItDown.convert 也可以接受文件路径 (str)
    result = md.convert(html_file_path)
    
    # 3. 从返回的 MarkItDownDocument 对象中提取 Markdown 文本
    markdown_text = result.markdown
    
    print(f"成功将文件 '{html_file_path}' 转换为 Markdown!")
    print("--- Markdown 预览 (前 300 字符) ---")
    print(markdown_text[:300])
    if len(markdown_text) > 300:
        print("... (内容省略) ...")
    print("----------------------------------")
    
    # --- (可选) 保存到新的 Markdown 文件 ---
    import os
    base_name = os.path.splitext(html_file_path)[0] # 去掉 .html 后缀
    md_file_path = f"{base_name}.md"
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    print(f"Markdown 已保存到 '{md_file_path}'")
    
except FileNotFoundError:
    print(f"错误: 找不到文件 '{html_file_path}'")
except Exception as e:
    print(f"转换文件 '{html_file_path}' 时出错: {e}")