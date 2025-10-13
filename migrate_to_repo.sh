#!/bin/bash
# Migration script to prepare control-flow engine for standalone repository
# Run this script to copy the consolidated engine to your new GitHub repo

set -e

# Configuration
SOURCE_DIR="/opt/openproject/external/control-flow"
TARGET_REPO_URL="https://github.com/JustinCBates/control-flow.git"
TEMP_DIR="/tmp/control-flow-migration"

echo "🚀 Control Flow Engine Migration Script"
echo "======================================="
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_REPO_URL"
echo ""

# Clean up any existing temp directory
if [ -d "$TEMP_DIR" ]; then
    echo "🧹 Cleaning up existing temp directory..."
    rm -rf "$TEMP_DIR"
fi

# Clone the target repository
echo "📥 Cloning target repository..."
git clone "$TARGET_REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"

# Remove any existing files (except .git)
echo "🗑️  Clearing target repository..."
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

# Copy the consolidated engine
echo "📦 Copying consolidated engine..."
cp -r "$SOURCE_DIR"/* .

# Remove files that shouldn't be in the standalone repo
echo "🧹 Cleaning up files specific to the original project..."
if [ -f "CONSOLIDATION_COMPLETE.md" ]; then
    rm "CONSOLIDATION_COMPLETE.md"
fi

if [ -f "test_consolidation.py" ]; then
    rm "test_consolidation.py"
fi

# Create additional files for standalone repo
echo "📝 Creating additional files for standalone repository..."

# Create LICENSE file
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Justin Bates

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Generated content
generated_diagrams/
*.mmd
.mermaid-*

# Temporary files
*.tmp
*.bak
EOF

# Create CONTRIBUTING.md
cat > CONTRIBUTING.md << 'EOF'
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
EOF

# Create GitHub Actions workflow
mkdir -p .github/workflows
cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=control_flow_engine --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      if: matrix.python-version == 3.11
EOF

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    git remote add origin "$TARGET_REPO_URL"
fi

# Add all files
echo "📋 Staging files for commit..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit - repository is up to date"
else
    echo "💾 Committing changes..."
    git commit -m "Add consolidated control flow engine

- Unified control flow engine with visualization
- YAML-based flow specifications
- CLI interface with multiple commands
- Mermaid.js diagram generation
- Flow analysis and validation tools
- Professional package structure ready for PyPI

Migrated from openproject-docker-compose consolidation."

    echo "🚀 Ready to push to repository!"
    echo ""
    echo "To complete the migration:"
    echo "  cd $TEMP_DIR"
    echo "  git push origin main"
    echo ""
    echo "Files are ready in: $TEMP_DIR"
fi

echo "✅ Migration preparation complete!"