"""
节点 3：分块文件

将文件按 token 限制分成多个块
优先处理根目录文件（包括 README），然后按模块分组
"""

import logging
import os
from collections import defaultdict

from state import Repo2DocState, FileInfo, CodeChunk
from config_loader import Config
from utils.file_utils import format_file_for_prompt


logger = logging.getLogger(__name__)


def chunk_files(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    将文件分成多个块，每个块不超过 token 限制
    
    分块策略：
    1. 优先处理根目录文件（包括 README）
    2. 按模块（顶层目录）分组处理
    3. 如果添加后超过限制，创建新块
    4. 单个文件超过限制时，单独成块
    
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
    
    # 按优先级排序文件
    sorted_files = _sort_files_by_priority(filtered_files)
    
    # 计算每个块的最大 token 数
    max_tokens_per_chunk = config.llm.max_input_tokens - config.llm.reserved_tokens
    
    logger.info(f"每个块最大 token 数: {max_tokens_per_chunk:,}")
    
    chunks: list[CodeChunk] = []
    current_chunk_files: list[FileInfo] = []
    current_chunk_tokens = 0
    chunk_id = 0
    
    for file_info in sorted_files:
        # 计算格式化后的 token 数（包含文件路径和分隔符）
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


def _sort_files_by_priority(files: list[FileInfo]) -> list[FileInfo]:
    """
    按优先级排序文件
    
    排序规则：
    1. 根目录的 README 文件（最高优先级）
    2. 根目录的其他文件（配置文件、入口文件等）
    3. 按顶层模块分组的文件
    
    Args:
        files: 原始文件列表
    
    Returns:
        排序后的文件列表
    """
    # 分类文件
    readme_files = []          # README 文件
    root_config_files = []     # 根目录配置文件
    root_other_files = []      # 根目录其他文件
    module_files = defaultdict(list)  # 按模块分组的文件
    
    # 重要的配置文件名（优先处理）
    config_names = {
        'package.json', 'pyproject.toml', 'setup.py', 'requirements.txt',
        'pom.xml', 'build.gradle', 'go.mod', 'Cargo.toml',
        'tsconfig.json', 'webpack.config.js', 'vite.config.js',
        '.env.example', 'docker-compose.yml', 'Dockerfile',
        'Makefile', 'CMakeLists.txt'
    }
    
    for file_info in files:
        path = file_info.path
        parts = path.replace('\\', '/').split('/')
        filename = parts[-1].lower()
        
        # 判断是否是根目录文件
        is_root = len(parts) == 1
        
        if is_root:
            if 'readme' in filename:
                readme_files.append(file_info)
            elif filename in {f.lower() for f in config_names}:
                root_config_files.append(file_info)
            else:
                root_other_files.append(file_info)
        else:
            # 获取顶层模块名
            module_name = parts[0]
            module_files[module_name].append(file_info)
    
    # 对每个模块内的文件排序（入口文件优先）
    entry_patterns = ['__init__', 'index', 'main', 'app', 'mod', 'lib']
    
    def file_priority(f: FileInfo) -> tuple:
        filename = os.path.basename(f.path).lower()
        name_without_ext = os.path.splitext(filename)[0]
        
        # 入口文件优先
        for i, pattern in enumerate(entry_patterns):
            if pattern in name_without_ext:
                return (0, i, filename)
        return (1, 0, filename)
    
    # 组合结果
    sorted_files = []
    
    # 1. README 文件
    sorted_files.extend(sorted(readme_files, key=lambda f: f.path.lower()))
    
    # 2. 根目录配置文件
    sorted_files.extend(sorted(root_config_files, key=lambda f: f.path.lower()))
    
    # 3. 根目录其他文件
    sorted_files.extend(sorted(root_other_files, key=file_priority))
    
    # 4. 按模块分组的文件（模块名按字母排序）
    for module_name in sorted(module_files.keys()):
        module_file_list = module_files[module_name]
        module_file_list.sort(key=file_priority)
        sorted_files.extend(module_file_list)
    
    logger.info(f"文件排序完成:")
    logger.info(f"  README 文件: {len(readme_files)} 个")
    logger.info(f"  根目录配置文件: {len(root_config_files)} 个")
    logger.info(f"  根目录其他文件: {len(root_other_files)} 个")
    logger.info(f"  模块数: {len(module_files)} 个")
    
    return sorted_files


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
