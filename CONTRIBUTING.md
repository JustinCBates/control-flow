# Contributing to Control Flow Engine

Thank you for your interest in contributing to the Control Flow Engine! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/control-flow.git
   cd control-flow
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=control_flow_engine

# Run specific test file
pytest tests/test_analyzer.py
```

## Code Style

We use Black for code formatting and Flake8 for linting:

```bash
# Format code
black src tests

# Check formatting
black --check src tests

# Lint code
flake8 src tests
```

## Type Checking

We use MyPy for type checking:

```bash
mypy src/control_flow_engine
```

## Submitting Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass
3. Commit your changes:
   ```bash
   git commit -m "Add your feature description"
   ```

4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Create a Pull Request

## Pull Request Guidelines

- Provide a clear description of the changes
- Include tests for new functionality
- Ensure all tests pass
- Update documentation as needed
- Follow the existing code style

## Release Process

Releases are managed by the maintainers. Version bumps follow semantic versioning.

## Questions?

Feel free to open an issue for questions or discussion!
