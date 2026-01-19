# Contributing to OpenAgent

Thank you for your interest in contributing to OpenAgent! This document provides guidelines and information for contributors.

## Getting Started

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/open-agent.git
cd open-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov black isort flake8
```

4. Set up environment variables:
```bash
cp config/config.example.toml config/config.toml
# Edit config.toml with your API keys
```

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Include a clear description of the bug
- Provide steps to reproduce
- Include expected vs actual behavior
- Add relevant logs or screenshots

### Suggesting Features

- Open a GitHub issue with the "enhancement" label
- Describe the feature and its use case
- Discuss potential implementation approaches

### Submitting Code

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following our coding standards

3. Add tests for new functionality:
```bash
pytest tests/ -v
```

4. Format your code:
```bash
black app/ tests/
isort app/ tests/
```

5. Submit a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Test results

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Documentation

- Add docstrings to all public functions and classes
- Follow Google-style docstring format
- Update README for user-facing changes

### Testing

- Write unit tests for new features
- Maintain >80% code coverage
- Tests should be independent and deterministic

## Architecture Guidelines

When adding new components:

### Adding a New Tool

1. Create a new file in `app/tool/`
2. Inherit from `BaseTool`
3. Implement the `_run` method
4. Register in the tool registry
5. Add corresponding tests

```python
from app.tool.base import BaseTool

class MyNewTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_new_tool",
            description="Description of what this tool does"
        )
    
    def _run(self, **kwargs) -> dict:
        # Implementation
        return {"result": "..."}
```

### Adding a New Agent

1. Create a new file in `app/agent/`
2. Inherit from `BaseAgent`
3. Implement the `_run` method
4. Add agent type to `AgentType` enum
5. Add corresponding tests

### Adding a New Flow

1. Create a new file in `app/flow/`
2. Inherit from `BaseFlow`
3. Register in the flow factory

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Request review from maintainers
4. Address review feedback
5. Squash commits before merge

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

Reviewers will check for:
- Code quality and style
- Test coverage
- Documentation
- Backward compatibility
- Security considerations

## Release Process

We follow semantic versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Community

- Be respectful and inclusive
- Follow our Code of Conduct
- Help others in discussions
- Share your use cases and feedback

## Questions?

- Open a GitHub discussion
- Check existing issues and documentation
- Contact the maintainers

Thank you for contributing to OpenAgent!
