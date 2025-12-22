"""
LangGraph 工作流定义

定义 Repo2Doc 的完整工作流
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from state import Repo2DocState, create_initial_state
from config_loader import Config, setup_logging
from nodes.node1_scan_files import scan_files
from nodes.node2_filter_files import filter_files
from nodes.node3_chunk_files import chunk_files
from nodes.node4_generate_doc import generate_doc
from nodes.node5_save_output import save_output


logger = logging.getLogger(__name__)


class Repo2DocWorkflow:
    """
    Repo2Doc LangGraph 工作流
    
    工作流程：
    1. scan_files: 扫描仓库目录
    2. filter_files: 筛选文件
    3. chunk_files: 分块文件
    4. generate_doc: 生成文档（增量式）
    5. save_output: 保存输出
    """
    
    def __init__(self, config: Config):
        """
        初始化工作流
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        构建 LangGraph 工作流图
        
        Returns:
            编译后的工作流图
        """
        # 创建状态图
        workflow = StateGraph(Repo2DocState)
        
        # 添加节点
        workflow.add_node("scan_files", self._wrap_node(scan_files))
        workflow.add_node("filter_files", self._wrap_node(filter_files))
        workflow.add_node("chunk_files", self._wrap_node(chunk_files))
        workflow.add_node("generate_doc", self._wrap_node(generate_doc))
        workflow.add_node("save_output", self._wrap_node(save_output))
        
        # 设置入口点
        workflow.set_entry_point("scan_files")
        
        # 添加边（条件路由）
        workflow.add_conditional_edges(
            "scan_files",
            self._check_error,
            {
                "continue": "filter_files",
                "error": END,
            }
        )
        
        workflow.add_conditional_edges(
            "filter_files",
            self._check_error,
            {
                "continue": "chunk_files",
                "error": END,
            }
        )
        
        workflow.add_conditional_edges(
            "chunk_files",
            self._check_error,
            {
                "continue": "generate_doc",
                "error": END,
            }
        )
        
        workflow.add_conditional_edges(
            "generate_doc",
            self._check_error,
            {
                "continue": "save_output",
                "error": END,
            }
        )
        
        workflow.add_edge("save_output", END)
        
        # 编译图
        return workflow.compile()
    
    def _wrap_node(self, node_func):
        """
        包装节点函数，注入配置
        
        Args:
            node_func: 节点函数
        
        Returns:
            包装后的函数
        """
        def wrapped(state: Repo2DocState) -> Repo2DocState:
            return node_func(state, self.config)
        return wrapped
    
    def _check_error(self, state: Repo2DocState) -> Literal["continue", "error"]:
        """
        检查是否有错误
        
        Args:
            state: 当前状态
        
        Returns:
            路由决策
        """
        if state.get("status") == "error":
            logger.error(f"工作流错误: {state.get('error')}")
            return "error"
        return "continue"
    
    def run(self, repo_path: str, config_path: str = None) -> Repo2DocState:
        """
        运行工作流
        
        Args:
            repo_path: 仓库路径
            config_path: 配置文件路径（可选）
        
        Returns:
            最终状态
        """
        logger.info(f"开始处理仓库: {repo_path}")
        
        # 创建初始状态
        initial_state = create_initial_state(repo_path, config_path)
        
        # 运行工作流
        final_state = self.graph.invoke(initial_state)
        
        # 输出结果
        if final_state.get("status") == "completed":
            logger.info("✅ 工作流完成")
            logger.info(f"   总文件数: {final_state.get('total_files', 0)}")
            logger.info(f"   筛选后文件数: {len(final_state.get('filtered_files', []))}")
            logger.info(f"   代码块数: {final_state.get('total_chunks', 0)}")
        else:
            logger.error(f"❌ 工作流失败: {final_state.get('error')}")
        
        return final_state


def create_workflow(config_path: str = None) -> Repo2DocWorkflow:
    """
    创建工作流实例
    
    Args:
        config_path: 配置文件路径（可选）
    
    Returns:
        工作流实例
    """
    # 加载配置
    config = Config.load(config_path)
    
    # 设置日志
    setup_logging(config.logging)
    
    # 创建工作流
    return Repo2DocWorkflow(config)


def run_workflow(repo_path: str, config_path: str = None) -> Repo2DocState:
    """
    便捷函数：创建并运行工作流
    
    Args:
        repo_path: 仓库路径
        config_path: 配置文件路径（可选）
    
    Returns:
        最终状态
    """
    workflow = create_workflow(config_path)
    return workflow.run(repo_path, config_path)
