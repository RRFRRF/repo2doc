"""
Repo2Doc 状态管理模块

定义 LangGraph 工作流的状态数据结构
"""

from typing import TypedDict, Optional
from dataclasses import dataclass


@dataclass
class FileInfo:
    """文件信息"""
    path: str                    # 相对路径
    absolute_path: str           # 绝对路径
    content: str                 # 文件内容
    extension: str               # 文件扩展名
    size: int                    # 文件大小（字节）
    token_count: int = 0         # Token 数量


@dataclass
class CodeChunk:
    """代码块"""
    chunk_id: int                # 块 ID
    files: list[FileInfo]        # 包含的文件列表
    combined_content: str        # 合并后的内容
    token_count: int             # Token 数量


class Repo2DocState(TypedDict):
    """
    Repo2Doc 工作流状态
    
    这是 LangGraph 工作流的核心状态对象，
    在各个节点之间传递和更新。
    """
    # 输入参数
    repo_path: str                          # 仓库路径
    config_path: Optional[str]              # 配置文件路径
    
    # 文件处理阶段
    all_files: list[FileInfo]               # 所有扫描到的文件
    filtered_files: list[FileInfo]          # 筛选后的文件
    
    # 分块阶段
    chunks: list[CodeChunk]                 # 代码块列表
    current_chunk_index: int                # 当前处理的块索引
    total_chunks: int                       # 总块数
    
    # 文档生成阶段
    current_document: str                   # 当前生成的文档
    intermediate_documents: list[str]       # 中间文档列表（每个块生成后的版本）
    
    # 状态信息
    status: str                             # 当前状态
    error: Optional[str]                    # 错误信息
    
    # 统计信息
    total_files: int                        # 总文件数
    total_tokens: int                       # 总 Token 数
    processed_chunks: int                   # 已处理的块数


def create_initial_state(repo_path: str, config_path: Optional[str] = None) -> Repo2DocState:
    """
    创建初始状态
    
    Args:
        repo_path: 仓库路径
        config_path: 配置文件路径（可选）
    
    Returns:
        初始化的状态对象
    """
    return Repo2DocState(
        repo_path=repo_path,
        config_path=config_path,
        all_files=[],
        filtered_files=[],
        chunks=[],
        current_chunk_index=0,
        total_chunks=0,
        current_document="",
        intermediate_documents=[],
        status="initialized",
        error=None,
        total_files=0,
        total_tokens=0,
        processed_chunks=0,
    )
