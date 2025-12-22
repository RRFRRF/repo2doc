"""
节点 3：分块文件

将文件按 token 限制分成多个块
"""

import logging

from state import Repo2DocState, FileInfo, CodeChunk
from config_loader import Config
from utils.file_utils import format_file_for_prompt


logger = logging.getLogger(__name__)


def chunk_files(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    将文件分成多个块，每个块不超过 token 限制
    
    分块策略：
    1. 计算每个块的最大 token 数
    2. 按顺序将文件添加到当前块
    3. 如果添加后超过限制，创建新块
    4. 单个文件超过限制时，单独成块（会在 LLM 调用时截断）
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        更新后的状态
    """
    logger.info("开始分块文件...")
    
    filtered_files = state["filtered_files"]
    
    if not filtered_files:
        state["status"] = "error"
        state["error"] = "没有筛选后的文件"
        logger.error(state["error"])
        return state
    
    # 计算每个块的最大 token 数
    max_tokens_per_chunk = config.llm.max_input_tokens - config.llm.reserved_tokens
    
    logger.info(f"每个块最大 token 数: {max_tokens_per_chunk:,}")
    
    chunks: list[CodeChunk] = []
    current_chunk_files: list[FileInfo] = []
    current_chunk_tokens = 0
    chunk_id = 0
    
    for file_info in filtered_files:
        # 计算格式化后的 token 数（包含文件路径和分隔符）
        formatted_content = format_file_for_prompt(file_info.path, file_info.content)
        file_tokens = file_info.token_count + 100  # 额外的格式化开销
        
        # 检查是否需要创建新块
        if current_chunk_tokens + file_tokens > max_tokens_per_chunk:
            # 保存当前块（如果有内容）
            if current_chunk_files:
                chunk = _create_chunk(chunk_id, current_chunk_files, current_chunk_tokens)
                chunks.append(chunk)
                chunk_id += 1
                logger.debug(f"创建块 {chunk_id}: {len(current_chunk_files)} 个文件, {current_chunk_tokens:,} tokens")
            
            # 重置当前块
            current_chunk_files = []
            current_chunk_tokens = 0
        
        # 添加文件到当前块
        current_chunk_files.append(file_info)
        current_chunk_tokens += file_tokens
    
    # 保存最后一个块
    if current_chunk_files:
        chunk = _create_chunk(chunk_id, current_chunk_files, current_chunk_tokens)
        chunks.append(chunk)
        logger.debug(f"创建块 {chunk_id + 1}: {len(current_chunk_files)} 个文件, {current_chunk_tokens:,} tokens")
    
    # 更新状态
    state["chunks"] = chunks
    state["total_chunks"] = len(chunks)
    state["current_chunk_index"] = 0
    state["status"] = "chunked"
    
    logger.info(f"分块完成: 共 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks):
        logger.info(f"  块 {i + 1}: {len(chunk.files)} 个文件, {chunk.token_count:,} tokens")
    
    return state


def _create_chunk(chunk_id: int, files: list[FileInfo], token_count: int) -> CodeChunk:
    """
    创建代码块
    
    Args:
        chunk_id: 块 ID
        files: 文件列表
        token_count: token 数量
    
    Returns:
        代码块对象
    """
    # 合并文件内容
    combined_parts = []
    for file_info in files:
        formatted = format_file_for_prompt(file_info.path, file_info.content)
        combined_parts.append(formatted)
    
    combined_content = "\n\n" + "=" * 60 + "\n\n".join(combined_parts)
    
    return CodeChunk(
        chunk_id=chunk_id,
        files=files,
        combined_content=combined_content,
        token_count=token_count,
    )
