"""
文件处理工具

提供文件读取、格式化等功能
"""

import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)

# 文件分隔符（类似 swark 的设计）
FILE_SEPARATOR = "\n" + "=" * 60 + "\n"


def read_file_content(file_path: str, max_size: int = 102400) -> Optional[str]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        max_size: 最大文件大小（字节）
    
    Returns:
        文件内容，如果读取失败返回 None
    """
    try:
        path = Path(file_path)
        
        # 检查文件大小
        if path.stat().st_size > max_size:
            logger.warning(f"文件过大，跳过: {file_path}")
            return None
        
        # 尝试多种编码读取
        encodings = ["utf-8", "gbk", "latin-1"]
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        logger.warning(f"无法解码文件: {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"读取文件失败 {file_path}: {e}")
        return None


def format_file_for_prompt(file_path: str, content: str) -> str:
    """
    格式化文件内容用于 prompt
    
    格式：
    ```
    文件路径: path/to/file.py
    ----------------------------------------
    文件内容
    ----------------------------------------
    ```
    
    Args:
        file_path: 文件相对路径
        content: 文件内容
    
    Returns:
        格式化后的字符串
    """
    header = f"文件路径: {file_path}"
    separator = "-" * 40
    
    return f"{header}\n{separator}\n{content}\n{separator}"


def combine_files_for_prompt(files: list[tuple[str, str]]) -> str:
    """
    合并多个文件用于 prompt
    
    Args:
        files: 文件列表，每个元素为 (路径, 内容)
    
    Returns:
        合并后的字符串
    """
    formatted_files = [
        format_file_for_prompt(path, content)
        for path, content in files
    ]
    
    return FILE_SEPARATOR.join(formatted_files)


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件扩展名（包含点号，如 ".py"）
    """
    return Path(file_path).suffix.lower()


def is_text_file(file_path: str) -> bool:
    """
    判断是否为文本文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否为文本文件
    """
    text_extensions = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
        ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
        ".kt", ".scala", ".vue", ".svelte", ".html", ".css", ".scss",
        ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt",
        ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    }
    
    ext = get_file_extension(file_path)
    return ext in text_extensions
