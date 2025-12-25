# Repo2Doc

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**🔄 [English](./README.md)**

基于 LangGraph 的代码库逆向需求文档生成工具，使用大语言模型（LLM）从代码库自动生成需求规格说明书。

## ✨ 特性

- 🔍 **智能文件筛选** - 按扩展名包含、按模式排除
- 📦 **自动分块** - 根据 LLM token 限制自动分块
- 🔄 **增量式生成** - 每个块生成后与之前的文档合并
- 📊 **详细报告** - 生成处理报告和 token 使用统计
- ⚙️ **灵活配置** - 支持 YAML 配置文件

## 🏗️ 工作流程

```
输入仓库路径
      │
      ▼
┌─────────────────────┐
│  1. 扫描文件        │  遍历目录树
├─────────────────────┤
│  2. 筛选文件        │  应用扩展名/模式规则
├─────────────────────┤
│  3. 分块文件        │  按 token 限制分块
├─────────────────────┤
│  4. 生成文档        │  LLM 增量式生成
├─────────────────────┤
│  5. 保存输出        │  保存文档和报告
└─────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
cd repo2doc

# 安装依赖（推荐使用 uv）
uv sync

# 或使用 pip
pip install -e .
```

### 配置

1. 创建 `.env` 文件：
```bash
cp .env.example .env
```

2. 在 `.env` 中设置 API 密钥：
```bash
OPENAI_API_KEY="your-api-key-here"
# 可选：自定义 API 基础 URL
# OPENAI_BASE_URL="https://api.openai.com/v1"
```

3. （可选）自定义 `config.yaml`：
```yaml
file_filter:
  include_extensions: [".py", ".js", ".ts", ".java"]
  max_file_size: 102400  # 100KB

llm:
  model: "gpt-4o"
  temperature: 0.3

output:
  output_dir: "./repo2doc-output"
  save_intermediate: true
```

### 使用

```bash
# 基本用法
uv run python main.py /path/to/repo

# 显示详细日志
uv run python main.py /path/to/repo -v

# 使用自定义配置
uv run python main.py /path/to/repo -c config.yaml
```

### Python API

```python
from llm_workflow import run_workflow

final_state = run_workflow(
    repo_path="/path/to/repo",
    config_path="config.yaml"
)

if final_state["status"] == "completed":
    print(f"文档长度: {len(final_state['current_document'])}")
```

## 📁 输出结构

```
repo2doc-output/
├── requirements.md              # 最终需求文档
├── {timestamp}_requirements.md  # 带时间戳的备份
├── {timestamp}_report.md        # 处理报告
├── {timestamp}_stats.json       # Token 使用统计
└── intermediate/                # 中间结果（如果启用）
    ├── chunk_1.md
    └── ...
```

## 📂 项目结构

```
repo2doc/
├── main.py              # 命令行入口
├── llm_workflow.py      # LangGraph 工作流定义
├── state.py             # 状态管理
├── config_loader.py     # 配置加载器
├── config.yaml          # 默认配置
├── nodes/               # 工作流节点
│   ├── node1_scan_files.py
│   ├── node2_filter_files.py
│   ├── node3_chunk_files.py
│   ├── node4_generate_doc.py
│   └── node5_save_output.py
└── utils/               # 工具函数
```

## 🔧 技术原理

### 增量式文档生成

由于代码库可能超过 LLM 的上下文限制，Repo2Doc 采用增量式生成策略：

```
块 1 → 文档 v1
块 2 + 文档 v1 → 文档 v2
块 3 + 文档 v2 → 文档 v3
...
块 N + 文档 v(N-1) → 最终文档
```

### 分块策略

按 token 限制对文件进行分组：
- 计算每个块的最大 token 数 = `max_input_tokens - reserved_tokens`
- 按顺序添加文件，直到达到限制
- 达到限制时开始新的块

## 🆚 与类似工具对比

| 特性 | Repo2Doc | swark |
|------|----------|-------|
| **输出类型** | 需求文档 | 架构图 |
| **LLM 框架** | LangGraph | VS Code API |
| **分块策略** | 增量式更新 | 截断 |
| **运行环境** | 命令行/Python | VS Code 扩展 |

## 📄 许可证

MIT License

---

**相关项目**：[Repo2Doc Agent](../repo2docAgent) - 基于 Agent 主动探索的变体版本。
