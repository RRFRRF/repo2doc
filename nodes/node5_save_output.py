"""
节点 5：保存输出

将生成的文档保存到文件
"""

import logging
from pathlib import Path
from datetime import datetime

from state import Repo2DocState
from config_loader import Config


logger = logging.getLogger(__name__)


def save_output(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    保存生成的文档到文件
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        更新后的状态
    """
    logger.info("保存输出文件...")
    
    current_document = state.get("current_document", "")
    
    if not current_document:
        state["status"] = "error"
        state["error"] = "没有生成的文档可保存"
        logger.error(state["error"])
        return state
    
    # 创建输出目录
    repo_path = Path(state["repo_path"])
    output_dir = repo_path / config.output.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # 保存最终文档
    output_file = output_dir / config.output.filename
    _save_file(output_file, current_document)
    logger.info(f"最终文档已保存: {output_file}")
    
    # 保存带时间戳的备份
    backup_file = output_dir / f"{timestamp}_{config.output.filename}"
    _save_file(backup_file, current_document)
    logger.info(f"备份文档已保存: {backup_file}")
    
    # 保存中间结果（如果配置启用）
    if config.output.save_intermediate:
        intermediate_documents = state.get("intermediate_documents", [])
        if intermediate_documents:
            intermediate_dir = output_dir / "intermediate"
            intermediate_dir.mkdir(parents=True, exist_ok=True)
            
            for i, doc in enumerate(intermediate_documents):
                intermediate_file = intermediate_dir / f"chunk_{i + 1}.md"
                _save_file(intermediate_file, doc)
            
            logger.info(f"中间结果已保存: {intermediate_dir}")
    
    # 保存处理报告
    report = _generate_report(state, config)
    report_file = output_dir / f"{timestamp}_report.md"
    _save_file(report_file, report)
    logger.info(f"处理报告已保存: {report_file}")
    
    # 更新状态
    state["status"] = "completed"
    
    logger.info("输出保存完成")
    
    return state


def _save_file(file_path: Path, content: str) -> None:
    """
    保存文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def _generate_report(state: Repo2DocState, config: Config) -> str:
    """
    生成处理报告
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        报告内容
    """
    chunks = state.get("chunks", [])
    filtered_files = state.get("filtered_files", [])
    
    # 统计文件类型
    extension_counts = {}
    for file_info in filtered_files:
        ext = file_info.extension
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # 生成报告
    report_lines = [
        "# Repo2Doc 处理报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**仓库路径**: {state['repo_path']}",
        "",
        "## 统计信息",
        "",
        f"- **总文件数**: {state.get('total_files', 0)}",
        f"- **筛选后文件数**: {len(filtered_files)}",
        f"- **总 Token 数**: {state.get('total_tokens', 0):,}",
        f"- **代码块数**: {len(chunks)}",
        f"- **已处理块数**: {state.get('processed_chunks', 0)}",
        "",
        "## 文件类型分布",
        "",
    ]
    
    for ext, count in sorted(extension_counts.items(), key=lambda x: -x[1]):
        report_lines.append(f"- `{ext}`: {count} 个文件")
    
    report_lines.extend([
        "",
        "## 代码块详情",
        "",
    ])
    
    for i, chunk in enumerate(chunks):
        report_lines.append(f"### 块 {i + 1}")
        report_lines.append(f"- **文件数**: {len(chunk.files)}")
        report_lines.append(f"- **Token 数**: {chunk.token_count:,}")
        report_lines.append("- **包含文件**:")
        for file_info in chunk.files[:10]:  # 只显示前 10 个
            report_lines.append(f"  - `{file_info.path}`")
        if len(chunk.files) > 10:
            report_lines.append(f"  - ... 还有 {len(chunk.files) - 10} 个文件")
        report_lines.append("")
    
    report_lines.extend([
        "## 配置信息",
        "",
        f"- **LLM 模型**: {config.llm.model}",
        f"- **最大输入 Token**: {config.llm.max_input_tokens:,}",
        f"- **预留 Token**: {config.llm.reserved_tokens:,}",
        f"- **最大文件大小**: {config.file_filter.max_file_size:,} 字节",
        f"- **最大文件数**: {config.file_filter.max_files}",
    ])
    
    return "\n".join(report_lines)
