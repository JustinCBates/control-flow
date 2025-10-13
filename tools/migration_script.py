#!/usr/bin/env python3
"""
Control Flow Engine Migration Script
Extracts control flow engine components from multiple repositories.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import json


class ControlFlowMigration:
    def __init__(self, source_root: Path, target_repo: Path):
        self.source_root = source_root
        self.target_repo = target_repo
        self.duplicates_found = {}
        self.unique_files = {}
        
    def analyze_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate control flow files across repositories."""
        print("🔍 Analyzing control flow file duplicates...")
        
        # Find all control flow related files
        patterns = [
            "**/control_flow_manager.py",
            "**/analyze_control_flows.py", 
            "**/smart_flow_updater.py",
            "**/control_flow_visualizer.py",
            "**/demo_development_communication.py"
        ]
        
        file_groups = {}
        
        for pattern in patterns:
            files = list(self.source_root.glob(pattern))
            if files:
                base_name = pattern.split('/')[-1]
                file_groups[base_name] = []
                
                for file_path in files:
                    if file_path.stat().st_size > 0:  # Skip empty files
                        file_groups[base_name].append(file_path)
        
        # Analyze duplicates by comparing file sizes and content
        for filename, paths in file_groups.items():
            if len(paths) > 1:
                # Group by file size first
                size_groups = {}
                for path in paths:
                    size = path.stat().st_size
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(path)
                
                # Check for actual duplicates
                for size, group in size_groups.items():
                    if len(group) > 1 and size > 0:
                        self.duplicates_found[filename] = group
                        print(f"  📁 {filename}: {len(group)} duplicates ({size} bytes each)")
                        for path in group:
                            print(f"    • {path}")
        
        return self.duplicates_found
    
    def create_target_structure(self):
        """Create the target repository structure."""
        print(f"🏗️  Creating target repository structure at {self.target_repo}")
        
        directories = [
            "src/control_flow_engine",
            "src/control_flow_engine/core",
            "src/control_flow_engine/visualizer", 
            "src/control_flow_engine/analysis",
            "src/control_flow_engine/cli",
            "templates",
            "examples",
            "docs",
            "tests/unit",
            "tests/integration",
            "tools"
        ]
        
        for directory in directories:
            (self.target_repo / directory).mkdir(parents=True, exist_ok=True)
        
        print(f"  ✅ Created {len(directories)} directories")
    
    def extract_engine_components(self):
        """Extract and consolidate engine components."""
        print("📦 Extracting engine components...")
        
        # Define mapping from source files to target locations
        extractions = {
            "control_flow_manager.py": "src/control_flow_engine/core/engine.py",
            "analyze_control_flows.py": "src/control_flow_engine/analysis/flow_analyzer.py",
            "control_flow_visualizer.py": "src/control_flow_engine/visualizer/mermaid_generator.py",
            "smart_flow_updater.py": "tools/flow_updater.py", 
            "demo_development_communication.py": "examples/demo_communication.py"
        }
        
        for source_name, target_path in extractions.items():
            if source_name in self.duplicates_found:
                # Use the first (presumably canonical) version
                source_file = self.duplicates_found[source_name][0]
                target_file = self.target_repo / target_path
                
                print(f"  📄 {source_name} → {target_path}")
                
                # Copy file with modifications for new structure
                self._copy_and_adapt_file(source_file, target_file)
        
        # Extract visualizer HTML
        html_files = list(self.source_root.glob("**/control_flow_visualizer.html"))
        if html_files:
            target_html = self.target_repo / "src/control_flow_engine/visualizer/templates/interface.html"
            shutil.copy2(html_files[0], target_html)
            print(f"  🌐 control_flow_visualizer.html → visualizer/templates/interface.html")
    
    def _copy_and_adapt_file(self, source: Path, target: Path):
        """Copy file and adapt imports for new structure."""
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Read source content
        with open(source, 'r') as f:
            content = f.read()
        
        # Basic adaptations (could be more sophisticated)
        # Update import paths, documentation references, etc.
        adapted_content = self._adapt_content_for_engine(content, target.name)
        
        # Write to target
        with open(target, 'w') as f:
            f.write(adapted_content)
    
    def _adapt_content_for_engine(self, content: str, filename: str) -> str:
        """Adapt file content for the new engine structure."""
        # Add engine package header
        header = f'''"""
{filename} - OpenProject Control Flow Engine
Extracted and consolidated from multiple project repositories.
"""

'''
        
        # Basic path updates (this could be much more sophisticated)
        content = content.replace(
            'control_flows/CONTROL_FLOWS_SPEC.md',
            'flow_specs/CONTROL_FLOWS_SPEC.md'
        )
        
        return header + content
    
    def create_package_files(self):
        """Create Python package configuration files."""
        print("📦 Creating package configuration...")
        
        # pyproject.toml
        pyproject_content = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "openproject-control-flow-engine"
version = "0.1.0"
description = "Control flow engine and visualization tools for OpenProject"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "OpenProject Team", email = "contact@openproject.org"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.8"
dependencies = [
    "pyyaml>=6.0",
    "click>=8.0",
    "jinja2>=3.0",
    "pathlib-extensions>=0.1.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=22.0",
    "flake8>=5.0",
    "mypy>=1.0"
]
web = [
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0"
]

[project.urls]
Homepage = "https://github.com/openproject/control-flow-engine"
Repository = "https://github.com/openproject/control-flow-engine"
Documentation = "https://control-flow-engine.readthedocs.io"

[project.scripts]
flow-engine = "control_flow_engine.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = ["--strict-markers", "--strict-config"]

[tool.black]
line-length = 88
target-version = ["py38"]

[tool.mypy]
python_version = "3.8"
strict = true
'''
        
        with open(self.target_repo / "pyproject.toml", 'w') as f:
            f.write(pyproject_content)
        
        # __init__.py files
        init_files = {
            "src/control_flow_engine/__init__.py": '''"""OpenProject Control Flow Engine."""

from .core.engine import FlowEngine
from .visualizer.mermaid_generator import FlowVisualizer
from .analysis.flow_analyzer import FlowAnalyzer

__version__ = "0.1.0"
__all__ = ["FlowEngine", "FlowVisualizer", "FlowAnalyzer"]
''',
            "src/control_flow_engine/core/__init__.py": '',
            "src/control_flow_engine/visualizer/__init__.py": '',
            "src/control_flow_engine/analysis/__init__.py": '',
            "src/control_flow_engine/cli/__init__.py": ''
        }
        
        for path, content in init_files.items():
            with open(self.target_repo / path, 'w') as f:
                f.write(content)
        
        print("  ✅ Created package configuration files")
    
    def create_cli_interface(self):
        """Create command-line interface."""
        cli_content = '''#!/usr/bin/env python3
"""Command-line interface for Control Flow Engine."""

import click
from pathlib import Path
from ..core.engine import FlowEngine
from ..visualizer.mermaid_generator import FlowVisualizer
from ..analysis.flow_analyzer import FlowAnalyzer


@click.group()
@click.version_option()
def main():
    """OpenProject Control Flow Engine CLI."""
    pass


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
def validate(spec_file):
    """Validate a control flow specification."""
    engine = FlowEngine(spec_file)
    try:
        engine.validate()
        click.echo("✅ Flow specification is valid")
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise click.Abort()


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--format', type=click.Choice(['mermaid', 'html', 'all']), default='all')
def visualize(spec_file, output, format):
    """Generate visualizations from flow specification."""
    engine = FlowEngine(spec_file)
    visualizer = FlowVisualizer(engine)
    
    output_dir = Path(output) if output else Path.cwd() / "flow_diagrams"
    output_dir.mkdir(exist_ok=True)
    
    if format in ['mermaid', 'all']:
        diagrams = visualizer.generate_all_diagrams()
        for name, content in diagrams.items():
            (output_dir / f"{name}.mmd").write_text(content)
        click.echo(f"📊 Mermaid diagrams generated in {output_dir}")
    
    if format in ['html', 'all']:
        html_file = visualizer.generate_html_interface()
        (output_dir / "visualizer.html").write_text(html_file)
        click.echo(f"🌐 HTML interface generated: {output_dir}/visualizer.html")


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=8000, help='Port for web server')
def serve(spec_file, port):
    """Serve interactive flow visualizer."""
    from ..visualizer.web_server import start_server
    start_server(spec_file, port)


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Analysis report file')
def analyze(spec_file, output):
    """Analyze flow complexity and dependencies."""
    engine = FlowEngine(spec_file)
    analyzer = FlowAnalyzer(engine)
    
    report = analyzer.generate_full_report()
    
    if output:
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        click.echo(f"📋 Analysis report saved: {output}")
    else:
        click.echo("📋 Flow Analysis Report:")
        click.echo(f"  Phases: {report['summary']['total_phases']}")
        click.echo(f"  Artifacts: {report['summary']['total_artifacts']}")
        click.echo(f"  Complexity: {report['summary']['complexity_score']}")


if __name__ == "__main__":
    main()
'''
        
        with open(self.target_repo / "src/control_flow_engine/cli/commands.py", 'w') as f:
            f.write(cli_content)
        
        print("  🖥️  Created CLI interface")
    
    def create_documentation(self):
        """Create initial documentation."""
        readme_content = '''# OpenProject Control Flow Engine

A powerful, reusable control flow engine and visualization system extracted from the OpenProject ecosystem.

## 🚀 Quick Start

### Installation
```bash
pip install openproject-control-flow-engine
```

### Usage
```python
from control_flow_engine import FlowEngine, FlowVisualizer

# Load and validate flow
engine = FlowEngine("flow_specs/CONTROL_FLOWS_SPEC.md")
engine.validate()

# Generate visualizations
visualizer = FlowVisualizer(engine)
visualizer.serve_web_interface(port=8080)
```

### CLI Usage
```bash
# Validate flows
flow-engine validate flow_specs/CONTROL_FLOWS_SPEC.md

# Generate diagrams
flow-engine visualize flow_specs/CONTROL_FLOWS_SPEC.md --output docs/

# Serve web interface
flow-engine serve flow_specs/CONTROL_FLOWS_SPEC.md --port 8080

# Analyze complexity
flow-engine analyze flow_specs/CONTROL_FLOWS_SPEC.md
```

## 📊 Features

- **Flow Engine**: Parse and execute YAML-based control flows
- **Visualizations**: Generate Mermaid diagrams, interactive HTML interfaces  
- **Analysis Tools**: Complexity analysis, dependency tracking
- **CLI Interface**: Command-line tools for validation, visualization, analysis
- **Web Interface**: Interactive flow exploration and real-time updates

## 🏗️ Architecture

This engine was extracted from multiple OpenProject repositories to eliminate duplication and provide a centralized, reusable control flow system.

### Components
- `core/`: Flow parsing and execution engine
- `visualizer/`: Mermaid diagram generation and web interfaces
- `analysis/`: Flow analysis and complexity tools
- `cli/`: Command-line interface
- `templates/`: Flow specification templates

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Flow Specification Format](docs/specification_format.md)  
- [Visualization Guide](docs/visualization_guide.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contributing

This engine serves the OpenProject ecosystem. Contributions welcome!

## 📄 License

MIT License - see LICENSE file for details.
'''
        
        with open(self.target_repo / "README.md", 'w') as f:
            f.write(readme_content)
        
        print("  📚 Created documentation")
    
    def generate_migration_report(self):
        """Generate a migration report."""
        report = {
            "migration_summary": {
                "source_repositories": len(list(self.source_root.glob("external/*"))),
                "duplicates_found": len(self.duplicates_found),
                "total_duplicate_files": sum(len(files) for files in self.duplicates_found.values()),
                "target_repository": str(self.target_repo),
                "migration_date": "2025-10-13"
            },
            "duplicates_eliminated": self.duplicates_found,
            "extraction_mapping": {
                "control_flow_manager.py": "src/control_flow_engine/core/engine.py",
                "analyze_control_flows.py": "src/control_flow_engine/analysis/flow_analyzer.py", 
                "control_flow_visualizer.py": "src/control_flow_engine/visualizer/mermaid_generator.py",
                "smart_flow_updater.py": "tools/flow_updater.py",
                "demo_development_communication.py": "examples/demo_communication.py"
            },
            "next_steps": [
                "Set up CI/CD for the new repository",
                "Publish to PyPI as openproject-control-flow-engine",
                "Update consumer repositories to use the package",
                "Remove duplicate files from consumer repositories",
                "Update documentation and examples"
            ]
        }
        
        with open(self.target_repo / "migration_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Migration report saved: {self.target_repo}/migration_report.json")
        return report
    
    def run_migration(self):
        """Execute the complete migration process."""
        print("🚀 Starting Control Flow Engine Migration")
        print("=" * 50)
        
        # Analysis phase
        self.analyze_duplicates()
        
        # Migration phase
        self.create_target_structure()
        self.extract_engine_components()
        self.create_package_files()
        self.create_cli_interface()
        self.create_documentation()
        
        # Reporting
        report = self.generate_migration_report()
        
        print("\n🎉 Migration Complete!")
        print("=" * 50)
        print(f"📦 New repository created: {self.target_repo}")
        print(f"🔧 Eliminated {report['migration_summary']['total_duplicate_files']} duplicate files")
        print(f"📊 Found {report['migration_summary']['duplicates_found']} duplicate file types")
        print("\nNext steps:")
        for step in report['next_steps']:
            print(f"  • {step}")


def main():
    """Main migration script."""
    source_root = Path("/opt/openproject")
    target_repo = Path("/tmp/openproject-control-flow-engine")
    
    migration = ControlFlowMigration(source_root, target_repo)
    migration.run_migration()
    
    print(f"\n🎯 Ready to create repository at: {target_repo}")
    print("💡 Consider creating it as: github.com/openproject/control-flow-engine")


if __name__ == "__main__":
    main()