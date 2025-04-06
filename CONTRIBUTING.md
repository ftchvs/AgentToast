# Contributing to AgentToast

Thank you for your interest in contributing to AgentToast! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

If you find a bug in the project:

1. Check if the bug has already been reported by searching the [Issues](https://github.com/ftchvs/AgentToast/issues).
2. If the bug hasn't been reported, [open a new issue](https://github.com/ftchvs/AgentToast/issues/new). Be sure to include:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior vs. actual behavior
   - Environment details (OS, Python version, etc.)
   - Any relevant logs or screenshots

### Suggesting Enhancements

If you have ideas for new features or improvements:

1. Check if the enhancement has already been suggested by searching the [Issues](https://github.com/ftchvs/AgentToast/issues).
2. If it hasn't been suggested, [open a new issue](https://github.com/ftchvs/AgentToast/issues/new). Include:
   - A clear, descriptive title
   - Detailed description of the proposed enhancement
   - Any relevant examples or mockups
   - Explanation of why this enhancement would be useful

### Contributing Code

1. Fork the repository
2. Create a new branch for your feature or bugfix: `git checkout -b feature/your-feature-name` or `git checkout -b fix/your-bugfix-name`
3. Make your changes
4. Add or update tests as necessary
5. Run tests to ensure they pass: `pytest`
6. Commit your changes with clear, descriptive commit messages
7. Push your branch to your fork
8. Submit a pull request to the main repository

#### Pull Request Guidelines

- Fill out the pull request template completely
- Link to any relevant issues
- Include screenshots or code examples if applicable
- Make sure all tests pass
- Update documentation as needed

## Development Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys following the pattern in `.env.example`

## Style Guidelines

- Follow PEP 8 style guidelines for Python code
- Use descriptive variable and function names
- Include docstrings for all functions, classes, and modules
- Add comments for complex code sections

## Adding New Agents

When adding a new agent to the system:

1. Create a new file in `src/agents/` with your agent class
2. Extend the `BaseAgent` class
3. Implement the required methods
4. Update the coordinator to use your new agent
5. Add appropriate tests in the `tests/` directory

## Questions?

If you have questions about contributing, feel free to open an issue labeled "question" or reach out to the maintainers.

Thank you for contributing to AgentToast! 
