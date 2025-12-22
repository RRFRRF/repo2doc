"""
配置加载器模块

负责加载和验证配置文件
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "file_filter": {
        "include_extensions": [
            ".py", ".js", ".jsx", ".ts", ".tsx",
            ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp",
            ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
            ".vue", ".svelte"
        ],
        "exclude_patterns": [
            "**/node_modules/**",
            "**/.git/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/dist/**",
            "**/build/**",
        ],
        "max_file_size": 102400,  # 100KB
        "max_files": 500,
    },
    "llm": {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_input_tokens": 100000,
        "reserved_tokens": 10000,
    },
    "output": {
        "output_dir": "./repo2doc-output",
        "filename": "requirements.md",
        "save_intermediate": True,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}


@dataclass
class FileFilterConfig:
    """文件筛选配置"""
    include_extensions: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    max_file_size: int = 102400
    max_files: int = 500


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_input_tokens: int = 100000
    reserved_tokens: int = 10000
    base_url: Optional[str] = None
    api_key: Optional[str] = None


@dataclass
class OutputConfig:
    """输出配置"""
    output_dir: str = "./repo2doc-output"
    filename: str = "requirements.md"
    save_intermediate: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class PromptConfig:
    """提示词配置"""
    system: str = ""
    first_chunk: str = ""
    incremental: str = ""
    next_chunk: str = ""


@dataclass
class Config:
    """完整配置"""
    file_filter: FileFilterConfig
    llm: LLMConfig
    output: OutputConfig
    logging: LoggingConfig
    prompts: PromptConfig
    
    @staticmethod
    def load(config_path: Optional[str] = None) -> "Config":
        """
        加载配置
        
        Args:
            config_path: 配置文件路径（可选）
        
        Returns:
            配置对象
        """
        # 加载环境变量
        load_dotenv()
        
        # 加载 YAML 配置
        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
            logger.info(f"从 {config_path} 加载配置")
        else:
            yaml_data = DEFAULT_CONFIG.copy()
            logger.info("使用默认配置")
        
        # 合并默认配置
        merged = _deep_merge(DEFAULT_CONFIG, yaml_data)
        
        # 创建配置对象
        file_filter = FileFilterConfig(
            include_extensions=merged["file_filter"]["include_extensions"],
            exclude_patterns=merged["file_filter"]["exclude_patterns"],
            max_file_size=merged["file_filter"]["max_file_size"],
            max_files=merged["file_filter"]["max_files"],
        )
        
        llm = LLMConfig(
            model=os.getenv("OPENAI_MODEL", merged["llm"]["model"]),
            temperature=merged["llm"]["temperature"],
            max_input_tokens=merged["llm"]["max_input_tokens"],
            reserved_tokens=merged["llm"]["reserved_tokens"],
            base_url=os.getenv("OPENAI_BASE_URL", merged["llm"].get("base_url")),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        output = OutputConfig(
            output_dir=merged["output"]["output_dir"],
            filename=merged["output"]["filename"],
            save_intermediate=merged["output"]["save_intermediate"],
        )
        
        logging_config = LoggingConfig(
            level=merged["logging"]["level"],
            format=merged["logging"]["format"],
        )
        
        prompts = PromptConfig(
            system=merged.get("prompts", {}).get("system", ""),
            first_chunk=merged.get("prompts", {}).get("first_chunk", ""),
            incremental=merged.get("prompts", {}).get("incremental", ""),
            next_chunk=merged.get("prompts", {}).get("next_chunk", ""),
        )
        
        return Config(
            file_filter=file_filter,
            llm=llm,
            output=output,
            logging=logging_config,
            prompts=prompts,
        )


def _deep_merge(base: dict, override: dict) -> dict:
    """
    深度合并两个字典
    
    Args:
        base: 基础字典
        override: 覆盖字典
    
    Returns:
        合并后的字典
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def setup_logging(config: LoggingConfig) -> None:
    """
    设置日志
    
    Args:
        config: 日志配置
    """
    logging.basicConfig(
        level=getattr(logging, config.level.upper()),
        format=config.format,
    )
