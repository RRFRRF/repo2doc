"""
节点 4：生成文档

使用 LLM 生成需求文档，支持增量式更新
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from state import Repo2DocState, CodeChunk
from config_loader import Config


logger = logging.getLogger(__name__)


def generate_doc(state: Repo2DocState, config: Config) -> Repo2DocState:
    """
    使用 LLM 生成需求文档
    
    支持增量式更新：
    1. 第一个块：使用系统提示 + 首次生成提示
    2. 后续块：使用增量更新提示 + 之前的文档
    
    Args:
        state: 当前状态
        config: 配置对象
    
    Returns:
        更新后的状态
    """
    logger.info("开始生成需求文档...")
    
    chunks = state["chunks"]
    
    if not chunks:
        state["status"] = "error"
        state["error"] = "没有代码块可处理"
        logger.error(state["error"])
        return state
    
    # 创建 LLM 客户端
    llm = _create_llm(config)
    
    current_document = state.get("current_document", "")
    intermediate_documents = state.get("intermediate_documents", [])
    
    # 逐块处理
    for i, chunk in enumerate(chunks):
        chunk_index = i + 1
        total_chunks = len(chunks)
        
        logger.info(f"处理块 {chunk_index}/{total_chunks}...")
        logger.info(f"  文件数: {len(chunk.files)}, Token 数: {chunk.token_count:,}")
        
        try:
            if i == 0:
                # 第一个块：使用系统提示
                new_document = _generate_first_chunk(
                    llm, chunk, chunk_index, total_chunks, config
                )
            else:
                # 后续块：增量更新
                new_document = _generate_next_chunk(
                    llm, chunk, chunk_index, total_chunks, current_document, config
                )
            
            # 更新当前文档
            current_document = new_document
            intermediate_documents.append(new_document)
            
            logger.info(f"块 {chunk_index} 处理完成，文档长度: {len(new_document)} 字符")
            
        except Exception as e:
            logger.error(f"处理块 {chunk_index} 时出错: {e}")
            state["status"] = "error"
            state["error"] = f"处理块 {chunk_index} 时出错: {e}"
            return state
    
    # 更新状态
    state["current_document"] = current_document
    state["intermediate_documents"] = intermediate_documents
    state["processed_chunks"] = len(chunks)
    state["status"] = "generated"
    
    logger.info(f"文档生成完成，共处理 {len(chunks)} 个块")
    
    return state


def _create_llm(config: Config) -> ChatOpenAI:
    """
    创建 LLM 客户端
    
    Args:
        config: 配置对象
    
    Returns:
        ChatOpenAI 客户端
    """
    kwargs = {
        "model": config.llm.model,
        "temperature": config.llm.temperature,
    }
    
    if config.llm.api_key:
        kwargs["api_key"] = config.llm.api_key
    
    if config.llm.base_url:
        kwargs["base_url"] = config.llm.base_url
    
    return ChatOpenAI(**kwargs)


def _generate_first_chunk(
    llm: ChatOpenAI,
    chunk: CodeChunk,
    chunk_index: int,
    total_chunks: int,
    config: Config
) -> str:
    """
    生成第一个块的文档
    
    Args:
        llm: LLM 客户端
        chunk: 代码块
        chunk_index: 块索引
        total_chunks: 总块数
        config: 配置对象
    
    Returns:
        生成的文档
    """
    # 构建消息
    messages = [
        SystemMessage(content=config.prompts.system),
        HumanMessage(content=config.prompts.first_chunk.format(
            code_content=chunk.combined_content,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
        ))
    ]
    
    # 调用 LLM
    response = llm.invoke(messages)
    
    return response.content


def _generate_next_chunk(
    llm: ChatOpenAI,
    chunk: CodeChunk,
    chunk_index: int,
    total_chunks: int,
    previous_document: str,
    config: Config
) -> str:
    """
    增量更新文档
    
    Args:
        llm: LLM 客户端
        chunk: 代码块
        chunk_index: 块索引
        total_chunks: 总块数
        previous_document: 之前的文档
        config: 配置对象
    
    Returns:
        更新后的文档
    """
    # 构建消息
    messages = [
        SystemMessage(content=config.prompts.incremental.format(
            previous_document=previous_document
        )),
        HumanMessage(content=config.prompts.next_chunk.format(
            code_content=chunk.combined_content,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
        ))
    ]
    
    # 调用 LLM
    response = llm.invoke(messages)
    
    return response.content
