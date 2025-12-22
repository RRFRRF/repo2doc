"""
节点 1：扫描文件

扫描仓库目录，获取所有文件列表
"""

import logging
from pathlib import Path

from state import Repo2DocState, FileInfo
from config_loader import Config
from utils.file_utils import read_file_content, get_file_extension
from utils.token_counter import count_tokens


logger = logging.getLogger(__name__)


def scan_files(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    扫描仓库目录，获取所有文件
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        更新后的状态
    """
    logger.info(f"开始扫描仓库: {state['repo_path']}")
    
    repo_path = Path(state["repo_path"])
    
    if not repo_path.exists():
        state["status"] = "error"
        state["error"] = f"仓库路径不存在: {state['repo_path']}"
        logger.error(state["error"])
        return state
    
    if not repo_path.is_dir():
        state["status"] = "error"
        state["error"] = f"路径不是目录: {state['repo_path']}"
        logger.error(state["error"])
        return state
    
    all_files: list[FileInfo] = []
    include_extensions = set(config.file_filter.include_extensions)
    
    # 递归扫描目录
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        
        # 检查扩展名
        ext = get_file_extension(str(file_path))
        if ext not in include_extensions:
            continue
        
        # 获取相对路径
        relative_path = str(file_path.relative_to(repo_path))
        
        # 读取文件内容
        content = read_file_content(
            str(file_path),
            max_size=config.file_filter.max_file_size
        )
        
        if content is None:
            continue
        
        # 计算 token 数量
        token_count = count_tokens(content)
        
        file_info = FileInfo(
            path=relative_path,
            absolute_path=str(file_path),
            content=content,
            extension=ext,
            size=file_path.stat().st_size,
            token_count=token_count,
        )
        
        all_files.append(file_info)
    
    # 更新状态
    state["all_files"] = all_files
    state["total_files"] = len(all_files)
    state["status"] = "scanned"
    
    logger.info(f"扫描完成，共找到 {len(all_files)} 个文件")
    
    return state
