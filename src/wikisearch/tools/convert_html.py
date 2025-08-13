import os
import io
from typing import Union, Tuple, Optional
from markitdown import MarkItDown

def convert_html_to_markdown(
    html_input: Union[str, os.PathLike], 
    output_path: Optional[Union[str, os.PathLike]] = None,
    title: str = ""
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    将 HTML (字符串或文件) 转换为 Markdown (字符串或文件)。

    Args:
        html_input (str or PathLike): 
            - 如果是有效的文件路径，则从该文件读取 HTML。
            - 否则，将其视为 HTML 内容字符串。
        output_path (str or PathLike, optional): 
            - 如果提供，则将 Markdown 内容保存到此文件路径。
            - 如果不提供，则只返回 Markdown 字符串。
        title (str, optional): 
            - 输入的标题或描述，用于日志。

    Returns:
        tuple: (成功标志 (bool), Markdown 内容 (str 或 None), 错误信息 (str 或 None))
               - 如果 output_path 未提供：(True, markdown_string, None) 或 (False, None, error_msg)
               - 如果 output_path 已提供：(True, markdown_string, None) 或 (False, None, error_msg)
                 (即使保存到文件，也仍返回字符串，方便后续使用)
    """
    html_content_str = None
    markdown_text = None
    input_source_desc = "unknown source"

    # --- 1. 获取 HTML 内容 ---
    try:
        if isinstance(html_input, (str, os.PathLike)):
            input_path_str = os.fspath(html_input) if isinstance(html_input, os.PathLike) else html_input
            
            # 检查 html_input 是否是一个存在的文件路径
            if os.path.isfile(input_path_str):
                print(f"正在从文件 '{input_path_str}' 读取 HTML...")
                with open(input_path_str, 'r', encoding='utf-8') as f:
                    html_content_str = f.read()
                input_source_desc = f"文件 '{input_path_str}'"
            else:
                # 否则，将其视为 HTML 字符串内容
                html_content_str = input_path_str
                input_source_desc = f"提供的字符串内容 (标题: '{title}')"
        else:
            return False, None, f"无效的 html_input 类型: {type(html_input)}。期望 str 或 PathLike。"

        if not html_content_str or not html_content_str.strip():
            return False, None, f"HTML 内容为空或只包含空白字符 (来源: {input_source_desc})。"

    except FileNotFoundError:
        return False, None, f"找不到指定的 HTML 文件: {html_input}"
    except Exception as e:
        return False, None, f"读取 HTML 输入时出错 (来源: {input_source_desc}): {e}"

    # --- 2. 使用 markitdown 转换 ---
    try:
        print(f"正在使用 markitdown 转换 {input_source_desc} 为 Markdown...")
        md_converter = MarkItDown()
        html_bytes = html_content_str.encode('utf-8')
        html_stream = io.BytesIO(html_bytes)
        # MarkItDown.convert 可以接受 str 或文件路径
        md_result = md_converter.convert(html_stream) 
        # markitdown 支持 BinaryIO，会进入 convert_stream 分支
        markdown_text = md_result.markdown 
        
        print(f"转换成功，Markdown 大小: {len(markdown_text)} 字符。")
        
    except AttributeError as ae:
        # 如果 .markdown 属性不存在，尝试打印调试信息
        error_detail = f"MarkItDown 返回对象缺少 'markdown' 属性。对象类型: {type(md_result)}, 可用属性: {[attr for attr in dir(md_result) if not attr.startswith('_')]}"
        print(f"转换时出错: {ae}")
        print(error_detail)
        return False, None, f"转换结果对象结构不符合预期: {ae}. {error_detail}"
    except Exception as e:
        error_msg = f"转换 Markdown 时出错: {e}"
        print(error_msg)
        # import traceback
        # traceback.print_exc() # 如果需要详细堆栈信息，取消注释
        return False, None, error_msg

    # --- 3. (可选) 保存到文件 ---
    if output_path and markdown_text:
        try:
            output_path_str = os.fspath(output_path) if isinstance(output_path, os.PathLike) else output_path
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path_str)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path_str, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"Markdown 内容已保存到文件: {output_path_str}")
        except Exception as e:
            # 即使保存文件失败，也返回已生成的 Markdown 字符串，但报告错误
            save_error_msg = f"转换成功，但保存到文件 '{output_path}' 时出错: {e}"
            print(save_error_msg)
            return False, markdown_text, save_error_msg # 或者 return True, markdown_text, save_error_msg 如果认为转换本身成功

    # --- 4. 返回结果 ---
    return True, markdown_text, None


def html_str_to_md_str(html_string: str, title: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
    """HTML 字符串 -> Markdown 字符串"""
    return convert_html_to_markdown(html_string, output_path=None, title=title)

def html_file_to_md_str(html_file_path: Union[str, os.PathLike]) -> Tuple[bool, Optional[str], Optional[str]]:
    """HTML 文件 -> Markdown 字符串"""
    return convert_html_to_markdown(html_file_path, output_path=None)

def html_str_to_md_file(html_string: str, md_file_path: Union[str, os.PathLike], title: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
    """HTML 字符串 -> Markdown 文件"""
    return convert_html_to_markdown(html_string, output_path=md_file_path, title=title)

def html_file_to_md_file(html_file_path: Union[str, os.PathLike], md_file_path: Union[str, os.PathLike]) -> Tuple[bool, Optional[str], Optional[str]]:
    """HTML 文件 -> Markdown 文件"""
    return convert_html_to_markdown(html_file_path, output_path=md_file_path)