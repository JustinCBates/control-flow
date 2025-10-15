# Control Flow Engine

A powerful, reusable control flow engine and visualization system for complex software architectures.

## 🚀 Features

### Core Capabilities
- **📊 Flow Visualization**: Generate professional diagrams with Graphviz from YAML specifications
- **🔍 Flow Analysis**: Validate and analyze control flow completeness and consistency
- **🛠️ CLI Interface**: Professional command-line tools for flow management
- **📋 YAML Configuration**: Clean, structured flow definitions
- **🎯 Design-First**: Plan flows before implementation
- **🖼️ Multiple Formats**: Output to SVG, PNG, PDF for documentation and presentations

### ✨ NEW: Greenfield (Design-First) Workflow 
- **🏗️ Auto-Scaffolding**: Automatically generate complete project structure from specs
- **🔄 Orchestrator Integration**: Steps automatically added to phase orchestrators
- **📈 Progress Tracking**: Real-time implementation status and metrics
- **✅ Validation**: Catch specification errors before runtime
- **📝 Documentation**: Auto-generated README files for phases and steps

**See [Phase 2 Documentation](docs/PHASE2_IMPLEMENTATION_COMPLETE.md) for complete guide.**

### 🔄 NEW: Transformation System (Production Ready)
- **🎯 Safe YAML Modifications**: Plan, validate, and apply changes to control flow specs
- **📁 Directory Sync**: Automatically sync directories with YAML changes
- **🔙 Full Rollback**: Undo any transformation with complete restoration
- **🤖 Auto-Regeneration**: Orchestrators automatically updated after changes
- **📊 History Tracking**: Complete audit trail of all transformations
- **🏗️ Zero-Point Creation**: Scaffold new phases/steps from scratch
- **⚡ 20-30x Faster**: Integrated workflow vs manual updates

**See [Transformation System Documentation](docs/TRANSFORMATION_SYSTEM.md) for complete API reference and examples.**

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

# Transform control flows safely
from control_flow_engine.core.transformation import ControlFlowTransformation

transformer = ControlFlowTransformation("specs/my_phase.yaml")

# Plan and apply transformation
plan = transformer.plan_renumber(old_sequence=10, new_sequence=15, target_type='step')
if transformer.validate(plan).valid:
    transformer.apply(
        plan,
        save=True,
        sync_directories=True,
        regenerate_orchestrators=True
    )
```
flow-engine visualize flow_specs/CONTROL_FLOWS_SPEC.md --output docs/

# Serve web interface
flow-engine serve flow_specs/CONTROL_FLOWS_SPEC.md --port 8080

# Analyze complexity
flow-engine analyze flow_specs/CONTROL_FLOWS_SPEC.md
```

## 📊 Features

- **Flow Engine**: Parse and execute YAML-based control flows
- **Transformation System**: Safe, validated YAML modifications with rollback support
- **Visualizations**: Generate professional diagrams with Graphviz (SVG, PNG, PDF)
- **Analysis Tools**: Complexity analysis, dependency tracking  
- **CLI Interface**: Command-line tools for validation, visualization, analysis
- **Auto-Scaffolding**: Generate complete project structures from specs
- **Directory Sync**: Automatically sync directories with YAML changes
- **Orchestrator Integration**: Auto-regenerate orchestrators after transformations
- **History Tracking**: Complete audit trail with rollback capability
- **Publication Quality**: Production-ready diagrams for documentation and presentations

## 🏗️ Architecture

This engine was consolidated from multiple OpenProject repositories to eliminate duplication and provide a centralized, reusable control flow system.

### Components
- `src/control_flow_engine/core/`: Flow parsing and execution engine
- `src/control_flow_engine/visualizer/`: Graphviz diagram generation
- `src/control_flow_engine/analysis/`: Flow analysis and complexity tools
- `src/control_flow_engine/cli/`: Command-line interface
- `templates/`: Flow specification templates
- `tools/`: Migration and update utilities
- `examples/`: Sample flows and generated diagrams

## 📚 Documentation

- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete index of all documentation
- **[Transformation System](docs/TRANSFORMATION_SYSTEM.md)** - Complete API reference for safe YAML modifications
- **[Quick Reference](docs/TRANSFORMATION_QUICK_REFERENCE.md)** - Common commands and patterns
- **[Output Directory Architecture](docs/ARCHITECTURE_OUTPUT_DIRECTORIES.md)** - Runtime output directory structure
- [Architecture Overview](docs/architecture.md)
- [Visualization Guide](docs/visualization_guide.md)
- [Visualizer Usage](docs/visualizer_usage.md)
- [Runnable Code Pattern](docs/RUNNABLE_CODE_PATTERN.md) - Design principles for standalone testability
- [Runnable Pattern Implementation](docs/RUNNABLE_PATTERN_COMPLETE.md) - Complete implementation guide

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