"""
节点 2：筛选文件

根据配置的排除规则筛选文件
"""

import logging
from pathlib import Path

import pathspec

from state import Repo2DocState, FileInfo
from config_loader import Config


logger = logging.getLogger(__name__)


def filter_files(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    根据排除规则筛选文件
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        更新后的状态
    """
    logger.info("开始筛选文件...")
    
    all_files = state["all_files"]
    
    if not all_files:
        state["status"] = "error"
        state["error"] = "没有找到任何文件"
        logger.error(state["error"])
        return state
    
    # 创建 pathspec 匹配器
    exclude_patterns = config.file_filter.exclude_patterns
    spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern,
        exclude_patterns
    )
    
    filtered_files: list[FileInfo] = []
    excluded_count = 0
    
    for file_info in all_files:
        # 检查是否匹配排除规则
        if spec.match_file(file_info.path):
            excluded_count += 1
            logger.debug(f"排除文件: {file_info.path}")
            continue
        
        filtered_files.append(file_info)
    
    # 限制最大文件数
    max_files = config.file_filter.max_files
    if len(filtered_files) > max_files:
        logger.warning(f"文件数超过限制 ({len(filtered_files)} > {max_files})，截取前 {max_files} 个")
        filtered_files = filtered_files[:max_files]
    
    # 按路径排序（确保一致性）
    filtered_files.sort(key=lambda f: f.path)
    
    # 计算总 token 数
    total_tokens = sum(f.token_count for f in filtered_files)
    
    # 更新状态
    state["filtered_files"] = filtered_files
    state["total_tokens"] = total_tokens
    state["status"] = "filtered"
    
    logger.info(
        f"筛选完成: {len(filtered_files)} 个文件保留, "
        f"{excluded_count} 个文件排除, "
        f"总 token 数: {total_tokens:,}"
    )
    
    return state
