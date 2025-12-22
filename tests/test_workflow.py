"""
工作流测试
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from state import create_initial_state, Repo2DocState, FileInfo, CodeChunk
from config_loader import Config, FileFilterConfig, LLMConfig, OutputConfig, LoggingConfig, PromptConfig
from nodes.node1_scan_files import scan_files
from nodes.node2_filter_files import filter_files
from nodes.node3_chunk_files import chunk_files


@pytest.fixture
def mock_config():
    """创建测试配置"""
    return Config(
        file_filter=FileFilterConfig(
            include_extensions=[".py", ".js"],
            exclude_patterns=["**/node_modules/**", "**/__pycache__/**"],
            max_file_size=102400,
            max_files=100,
        ),
        llm=LLMConfig(
            model="gpt-4o",
            temperature=0.3,
            max_input_tokens=100000,
            reserved_tokens=10000,
        ),
        output=OutputConfig(
            output_dir="./repo2doc-output",
            filename="requirements.md",
            save_intermediate=True,
        ),
        logging=LoggingConfig(
            level="INFO",
            format="%(message)s",
        ),
        prompts=PromptConfig(
            system="Test system prompt",
            first_chunk="Test first chunk prompt",
            incremental="Test incremental prompt",
            next_chunk="Test next chunk prompt",
        ),
    )


@pytest.fixture
def sample_state():
    """创建示例状态"""
    return create_initial_state("/tmp/test-repo")


class TestState:
    """状态测试"""
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        state = create_initial_state("/path/to/repo")
        
        assert state["repo_path"] == "/path/to/repo"
        assert state["status"] == "initialized"
        assert state["all_files"] == []
        assert state["filtered_files"] == []
        assert state["chunks"] == []
        assert state["current_document"] == ""
    
    def test_file_info(self):
        """测试 FileInfo 数据类"""
        file_info = FileInfo(
            path="src/main.py",
            absolute_path="/tmp/repo/src/main.py",
            content="print('hello')",
            extension=".py",
            size=100,
            token_count=10,
        )
        
        assert file_info.path == "src/main.py"
        assert file_info.extension == ".py"
        assert file_info.token_count == 10
    
    def test_code_chunk(self):
        """测试 CodeChunk 数据类"""
        file_info = FileInfo(
            path="test.py",
            absolute_path="/tmp/test.py",
            content="pass",
            extension=".py",
            size=4,
            token_count=1,
        )
        
        chunk = CodeChunk(
            chunk_id=0,
            files=[file_info],
            combined_content="test content",
            token_count=100,
        )
        
        assert chunk.chunk_id == 0
        assert len(chunk.files) == 1
        assert chunk.token_count == 100


class TestConfig:
    """配置测试"""
    
    def test_default_config(self, mock_config):
        """测试默认配置"""
        assert mock_config.llm.model == "gpt-4o"
        assert mock_config.file_filter.max_file_size == 102400
        assert ".py" in mock_config.file_filter.include_extensions


class TestNodes:
    """节点测试"""
    
    def test_scan_files_invalid_path(self, mock_config):
        """测试扫描不存在的路径"""
        state = create_initial_state("/nonexistent/path")
        result = scan_files(state, mock_config)
        
        assert result["status"] == "error"
        assert "不存在" in result["error"]
    
    def test_filter_files_empty(self, mock_config):
        """测试筛选空文件列表"""
        state = create_initial_state("/tmp/repo")
        state["all_files"] = []
        
        result = filter_files(state, mock_config)
        
        assert result["status"] == "error"
        assert "没有找到" in result["error"]
    
    def test_chunk_files_empty(self, mock_config):
        """测试分块空文件列表"""
        state = create_initial_state("/tmp/repo")
        state["filtered_files"] = []
        
        result = chunk_files(state, mock_config)
        
        assert result["status"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
