"""
Token 计数工具

使用 tiktoken 进行精确的 token 计数
"""

import logging
from functools import lru_cache

import tiktoken


logger = logging.getLogger(__name__)

# 默认编码器（GPT-4 使用 cl100k_base）
DEFAULT_ENCODING = "cl100k_base"


@lru_cache(maxsize=1)
def get_encoder(encoding_name: str = DEFAULT_ENCODING) -> tiktoken.Encoding:
    """
    获取 tiktoken 编码器（带缓存）
    
    Args:
        encoding_name: 编码器名称
    
    Returns:
        tiktoken 编码器
    """
    return tiktoken.get_encoding(encoding_name)


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    计算文本的 token 数量
    
    Args:
        text: 要计算的文本
        encoding_name: 编码器名称
    
    Returns:
        token 数量
    """
    if not text:
        return 0
    
    encoder = get_encoder(encoding_name)
    return len(encoder.encode(text))


def estimate_tokens(text: str) -> int:
    """
    快速估算 token 数量（不使用 tiktoken，用于快速估算）
    
    规则：
    - 英文：约 4 个字符 = 1 token
    - 中文：约 1.5 个字符 = 1 token
    
    Args:
        text: 要估算的文本
    
    Returns:
        估算的 token 数量
    """
    if not text:
        return 0
    
    # 简单估算：字符数 / 3
    return len(text) // 3


def tokens_to_chars(tokens: int) -> int:
    """
    将 token 数量转换为大约的字符数
    
    Args:
        tokens: token 数量
    
    Returns:
        大约的字符数
    """
    return tokens * 4
