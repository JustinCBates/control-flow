# Control Flow Engine

A powerful, reusable control flow engine and visualization system for complex software architectures.

## 🚀 Features

- **📊 Flow Visualization**: Generate interactive Mermaid.js diagrams from YAML specifications
- **🔍 Flow Analysis**: Validate and analyze control flow completeness and consistency
- **🛠️ CLI Interface**: Professional command-line tools for flow management
- **� YAML Configuration**: Clean, structured flow definitions
- **🎯 Design-First**: Plan flows before implementation
- **🔄 Live Updates**: Real-time visualization with web interface

## 📦 Installation

### From PyPI (coming soon)
```bash
pip install control-flow-engine
```

### From Source
```bash
git clone https://github.com/JustinCBates/control-flow.git
cd control-flow
pip install -e .
```

## 🎯 Quick Start

### 1. Define Your Control Flows

Create a `control_flows.yml` file:

```yaml
component:
  name: "my-component"
  description: "Example component"
  version: "1.0.0"

entry_points:
  main:
    status: "IMPLEMENTED"
    description: "Main entry point"
    flow_id: "main_flow"

flows:
  main_flow:
    description: "Primary process flow"
    steps:
      - step_id: "init"
        name: "Initialize"
        status: "IMPLEMENTED"
        description: "Setup component"
      - step_id: "process"
        name: "Process Data"
        status: "PLANNED"
        description: "Main processing logic"

implementation_status:
  overall: "IN_PROGRESS"
  last_updated: "2025-10-13"
```

### 2. Generate Visualizations

```bash
# Generate all diagram types
flow-engine visualize --all

# Generate specific diagram
flow-engine visualize --type overview

# Start interactive web interface
flow-engine serve --port 8000
```

### 3. Analyze Flows

```bash
# Validate flow structure
flow-engine analyze --validate

# Generate summary report
flow-engine analyze --summary
```

## 🏗️ API Usage

### Python API

```python
from control_flow_engine import ControlFlowManager, ControlFlowVisualizer

# Load and manage flows
manager = ControlFlowManager("control_flows.yml")
manager.load_specification()

# Generate visualizations
visualizer = ControlFlowVisualizer()
diagrams = visualizer.generate_all_diagrams()

# Analyze flows
from control_flow_engine import ControlFlowAnalyzer
analyzer = ControlFlowAnalyzer("/path/to/component")
summary = analyzer.generate_summary()
```
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

This engine was consolidated from multiple OpenProject repositories to eliminate duplication and provide a centralized, reusable control flow system.

### Components
- `src/control_flow_engine/core/`: Flow parsing and execution engine
- `src/control_flow_engine/visualizer/`: Mermaid diagram generation and web interfaces
- `src/control_flow_engine/analysis/`: Flow analysis and complexity tools
- `src/control_flow_engine/cli/`: Command-line interface
- `templates/`: Flow specification templates
- `tools/`: Migration and update utilities
- `examples/`: Sample flows and generated diagrams

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Visualization Guide](docs/visualization_guide.md)
- [Visualizer Usage](docs/visualizer_usage.md)

## 🛠️ Development

### Structure
```
external/control-flow/
├── src/control_flow_engine/     # Main package
├── templates/                   # Flow templates
├── examples/                    # Examples and demos
├── docs/                       # Documentation  
├── tests/                      # Test suite
└── tools/                      # Utilities
```

### Migration from Distributed Files

This engine consolidates control flow functionality that was previously duplicated across:
- `design_specs/control_flow_manager.py` (4 copies, 385 lines each)
- `design_specs/analyze_control_flows.py` (multiple copies)
- `design_specs/control_flow_visualizer.py` (visualization tools)
- Various control flow documentation and examples

## 🤝 Integration

### Consumer Repositories
After this consolidation, other repositories should:
1. Add dependency: `openproject-control-flow-engine`
2. Move flow specs to: `flow_specs/CONTROL_FLOWS_SPEC.md`
3. Remove duplicate control flow files
4. Use centralized engine and tools

### Benefits
- ✅ **Eliminates 30+ duplicate files**
- ✅ **Centralized updates benefit all projects**
- ✅ **Professional package structure**
- ✅ **Clean separation of concerns**
- ✅ **Reusable by other teams/projects**

## 📄 License

MIT License - see LICENSE file for details.