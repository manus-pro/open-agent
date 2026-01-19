# OpenAgent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](./tests)
[![JOSS](https://img.shields.io/badge/JOSS-submitted-orange.svg)](https://joss.theoj.org/)

**OpenAgent** is a modular framework for building autonomous AI agents that can decompose complex tasks, orchestrate multiple tools, and maintain context through memory-enabled execution.

## Key Features

- **Hierarchical Agent Architecture**: Specialized agents (Manus, Planning, ReAct, SWE) with distinct reasoning paradigms
- **Memory-Enabled Planning**: Context persistence across multi-step workflows
- **Extensible Tool Framework**: Dynamic tool registration and discovery via the Tool Registry pattern
- **Multi-Modal Task Execution**: Document generation, web research, code synthesis, and browser automation
- **Graceful Degradation**: LLM-based fallback when tool execution fails

## Installation

```bash
# Clone the repository
git clone https://github.com/manus-pro/open-agent.git
cd open-agent

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config/config.example.toml config/config.toml
# Edit config.toml with your API keys
```

### Environment Variables

```bash
export OPENAI_API_KEY="your_openai_key"
export FIRECRAWL_API_KEY="your_firecrawl_key"  # Optional: for web research
export ANTHROPIC_API_KEY="your_anthropic_key"  # Optional: for Claude
```

## Quick Start

```python
from app.agent.manus import Manus
import asyncio

async def main():
    agent = Manus()
    await agent.run("Research quantum computing and generate a PDF report")

asyncio.run(main())
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Agent Layer                              │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────────┐  │
│  │  Manus  │ │ Planning │ │  ReAct  │ │       SWE       │  │
│  └────┬────┘ └────┬─────┘ └────┬────┘ └────────┬────────┘  │
│       └───────────┴────────────┴───────────────┘            │
│                          │                                   │
│                    BaseAgent                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Tool Layer                              │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐    │
│  │     PDF     │ │   Markdown   │ │   Code Generator  │    │
│  │  Generator  │ │  Generator   │ │                   │    │
│  └─────────────┘ └──────────────┘ └───────────────────┘    │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐    │
│  │  Firecrawl  │ │   Browser    │ │    Bash/Python    │    │
│  │  Research   │ │  Automation  │ │     Execute       │    │
│  └─────────────┘ └──────────────┘ └───────────────────┘    │
│                    Tool Registry                             │
└─────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Description | Use Case |
|-------|-------------|----------|
| **Manus** | Primary orchestrator using OpenAI Functions with task-type inference | General-purpose task execution |
| **Planning** | Memory-enabled multi-step execution with artifact tracking | Complex research workflows |
| **ReAct** | Thought-Action-Observation cycles with reasoning traces | Iterative problem-solving |
| **SWE** | Five-phase workflow (Understand→Plan→Implement→Verify→Iterate) | Code generation and debugging |

## Tools

| Tool | Description |
|------|-------------|
| `pdf_generator` | Generate formatted PDF documents with ReportLab |
| `markdown_generator` | Create structured Markdown files |
| `code_generator` | Multi-language code synthesis with execution |
| `firecrawl_research` | Web research via Firecrawl API |
| `bash` | Shell command execution with timeout |
| `python_execute` | Python code execution in-process/subprocess |
| `file_saver` | File persistence to filesystem |
| `str_replace_editor` | Text/code file editing via search-replace |

## Examples

### Document Generation

```python
from app.tool.pdf_generator import PDFGeneratorTool

pdf_tool = PDFGeneratorTool()
result = pdf_tool.run(
    content="# Report Title\n\nContent here...",
    title="My Report",
    options={"auto_open": True}
)
```

### Multi-Step Planning

```python
from app.agent.planning import PlanningAgent
from app.schema import TaskInput

agent = PlanningAgent()
task = TaskInput(
    task_description="Research AI agents and create a summary",
    parameters={
        "plan": [
            "Search for recent AI agent papers",
            "Extract key findings",
            "Generate PDF report"
        ],
        "memory_enabled": True
    }
)
result = agent.run(task)
```

### Web Research

```python
from app.tool.firecrawl_research import FirecrawlResearchTool

research = FirecrawlResearchTool()
result = research.run(
    query="Large language model agents survey",
    output_format="markdown"
)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Project Structure

```
open-agent/
├── app/
│   ├── agent/          # Agent implementations
│   ├── flow/           # Flow orchestration
│   ├── prompt/         # System prompts
│   ├── tool/           # Tool implementations
│   ├── config.py       # Configuration management
│   ├── llm.py          # LLM interface
│   ├── logger.py       # Logging utilities
│   └── schema.py       # Data models
├── config/             # Configuration files
├── tests/              # Test suite
├── paper.md            # JOSS paper
├── paper.bib           # References
└── requirements.txt    # Dependencies
```

## Citation

If you use OpenAgent in your research, please cite:

```bibtex
@article{zhang2026openagent,
  title={OpenAgent: A Modular Framework for Autonomous Multi-Tool Agent Orchestration with Memory-Enabled Planning},
  author={Zhang, Xinyu},
  journal={Journal of Open Source Software},
  year={2026}
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for the foundational agent framework
- [Firecrawl](https://firecrawl.dev) for web research capabilities
- [OpenAgent Community](https://github.com/mannaandpoem/OpenAgent) for inspiration
