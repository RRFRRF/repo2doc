# Repo2Doc

A LangGraph-based tool for reverse-engineering requirements documentation from codebases.

## Overview

Repo2Doc is a tool that uses Large Language Models (LLMs) to automatically generate requirements specification documents from code repositories. It draws inspiration from [swark](https://github.com/swark-io/swark)'s design philosophy, implementing features like file filtering, code chunking, and incremental document generation.

### Key Features

- 🔍 **Smart File Filtering**: Support for extension-based inclusion and pattern-based exclusion
- 📦 **Auto Chunking**: Automatic chunking based on LLM token limits
- 🔄 **Incremental Generation**: Each chunk's output is merged with the previous document
- 📊 **Detailed Reports**: Generates processing reports and intermediate results
- ⚙️ **Flexible Configuration**: YAML configuration file support

## Workflow

```
┌─────────────────┐
│   Input Repo    │
│      Path       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  1. Scan Files  │  Scan directory, get all files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Filter Files │  Filter by extension and exclude patterns
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Chunk Files  │  Chunk by token limit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Generate Doc │  LLM incremental generation
│    (loop)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Save Output  │  Save document and report
└─────────────────┘
```

## Installation

### Using uv (Recommended)

```bash
cd repo2doc
uv sync
```

### Using pip

```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit the `.env` file to set your API key:

```bash
OPENAI_API_KEY="your-api-key-here"

# Optional: Custom API base URL
# OPENAI_BASE_URL="https://api.openai.com/v1"
```

### Configuration File

Edit `config.yaml` to customize settings:

```yaml
# File filter configuration
file_filter:
  include_extensions:
    - ".py"
    - ".js"
    - ".ts"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/__pycache__/**"
  max_file_size: 102400  # 100KB
  max_files: 500

# LLM configuration
llm:
  model: "gpt-4o"
  temperature: 0.3
  max_input_tokens: 100000
  reserved_tokens: 10000

# Output configuration
output:
  output_dir: "./repo2doc-output"
  filename: "requirements.md"
  save_intermediate: true
```

## Usage

### Command Line

```bash
# Use default configuration
uv run python main.py /path/to/repo

# Use custom configuration
uv run python main.py /path/to/repo -c config.yaml

# Show verbose logs
uv run python main.py /path/to/repo -v
```

### Python API

```python
from llm_workflow import run_workflow

# Run workflow
final_state = run_workflow(
    repo_path="/path/to/repo",
    config_path="config.yaml"
)

# Check result
if final_state["status"] == "completed":
    print("Document generated successfully!")
    print(f"Output: {final_state['current_document'][:500]}...")
else:
    print(f"Generation failed: {final_state['error']}")
```

## Output

After running, a `repo2doc-output/` folder will be created in the repository directory:

```
repo2doc-output/
├── requirements.md           # Final requirements document
├── 2024-01-01_12-00-00_requirements.md  # Timestamped backup
├── 2024-01-01_12-00-00_report.md        # Processing report
└── intermediate/             # Intermediate results (if enabled)
    ├── chunk_1.md
    ├── chunk_2.md
    └── ...
```

## Project Structure

```
repo2doc/
├── main.py              # Main entry point
├── llm_workflow.py      # LangGraph workflow definition
├── state.py             # State management
├── config_loader.py     # Configuration loader
├── config.yaml          # Default configuration
├── nodes/               # Workflow nodes
│   ├── node1_scan_files.py
│   ├── node2_filter_files.py
│   ├── node3_chunk_files.py
│   ├── node4_generate_doc.py
│   └── node5_save_output.py
├── utils/               # Utility functions
│   ├── token_counter.py
│   └── file_utils.py
├── tests/               # Tests
│   └── test_workflow.py
├── pyproject.toml       # Project configuration
├── .env.example         # Environment variables example
├── readme.cn.md         # Chinese documentation
└── readme.en.md         # English documentation
```

## Technical Principles

### Incremental Document Generation

Since codebases may exceed LLM context limits, Repo2Doc uses an incremental generation strategy:

1. **Initial Generation**: Generate initial document using the first code chunk
2. **Incremental Update**: Subsequent chunks are input to LLM along with the previous document
3. **Merge Strategy**: LLM merges newly discovered features into the existing document

```
Chunk 1 → Document v1
Chunk 2 + Document v1 → Document v2
Chunk 3 + Document v2 → Document v3
...
Chunk N + Document v(N-1) → Final Document
```

### Chunking Strategy

```python
# Calculate max tokens per chunk
max_tokens_per_chunk = max_input_tokens - reserved_tokens

# Add files to current chunk sequentially
for file in files:
    if current_tokens + file_tokens > max_tokens_per_chunk:
        # Create new chunk
        save_current_chunk()
        start_new_chunk()
    add_file_to_chunk(file)
```

## Comparison with swark

| Feature | Repo2Doc | swark |
|---------|----------|-------|
| **Output Type** | Requirements Doc | Architecture Diagram |
| **LLM Framework** | LangGraph | VS Code API |
| **Chunking Strategy** | Incremental Update | Truncation |
| **File Filtering** | Similar | Similar |
| **Runtime Environment** | CLI/Python | VS Code Extension |

## License

MIT License
