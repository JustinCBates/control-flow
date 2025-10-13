# 🔄 Control Flow Visualizer

An interactive visualization system for OpenProject control flows, built with Mermaid.js.

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
```bash
cd /opt/openproject/external/config-manager/design_specs
python3 serve_visualizer.py
```
Then open http://localhost:8000/control_flow_visualizer.html

### Option 2: Generate Static Diagrams
```bash
cd /opt/openproject/external/config-manager/design_specs
python3 control_flow_visualizer.py
```
Check `generated_diagrams/` for output files.

## 📊 Available Visualizations

### 1. **Overview** - High-level phase flow
- Shows main configuration phases
- Implementation status (✅ Implemented / ⏳ Pending)
- Sequential flow progression

### 2. **Artifacts** - Data flow between phases
- Process nodes (blue) and data artifacts (purple)
- Producer/consumer relationships
- Artifact lifecycle tracking

### 3. **States** - State machine transitions
- Configuration process as state machine
- Phase descriptions and transitions
- Clear entry/exit points

### 4. **Timeline** - Implementation progress
- Gantt chart of development phases
- Dependencies and overlap
- Historical progress tracking

## 🔧 Architecture

### Components
- **`control_flow_visualizer.py`**: Core parser and Mermaid generator
- **`control_flow_visualizer.html`**: Interactive web interface
- **`serve_visualizer.py`**: Development web server
- **`CONTROL_FLOWS_SPEC.md`**: Source of truth for flow definitions

### Data Flow
```
CONTROL_FLOWS_SPEC.md → Parser → Mermaid Syntax → Web Interface
```

### Supported Diagram Types
- **Flowcharts**: Process flows and dependencies
- **State Diagrams**: Phase transitions
- **Gantt Charts**: Timeline and progress
- **Graph Diagrams**: Artifact relationships

## 🎨 Customization

### Adding New Diagram Types
1. Add generator method to `ControlFlowVisualizer` class
2. Update `generate_all_diagrams()` to include new type
3. Add corresponding tab/section to HTML interface

### Styling
- Mermaid themes configured in HTML
- CSS classes for status indication
- Responsive design for different screen sizes

### Real-time Updates
The web interface includes an API endpoint (`/api/refresh`) that can regenerate diagrams from the latest specification file.

## 🔍 Features

### Interactive Elements
- **Tabbed Interface**: Switch between diagram types
- **Status Legend**: Clear indication of implementation status
- **Responsive Design**: Works on desktop and mobile
- **Live Refresh**: Regenerate diagrams without restart

### Visual Indicators
- **✅ Green**: Implemented phases
- **⏳ Orange**: Pending implementation
- **🔗 Purple**: Data artifacts
- **📊 Blue**: Process phases

### Export Options
- **Mermaid Files**: `.mmd` format for integration
- **Markdown**: Combined diagrams in documentation
- **SVG/PNG**: Via Mermaid CLI (additional setup required)

## 🚀 Integration Ideas

### GitHub Integration
Add to your GitHub workflow:
```yaml
- name: Generate Control Flow Diagrams
  run: |
    cd design_specs
    python control_flow_visualizer.py
    git add generated_diagrams/
```

### Documentation Integration
Include in README.md:
```markdown
## Control Flow
![Control Flow](design_specs/generated_diagrams/control_flow_diagrams.md)
```

### Live Documentation
Host the visualizer on GitHub Pages or similar service for team access.

## 🛠️ Development

### Dependencies
- Python 3.7+
- PyYAML (for YAML parsing)
- Web browser (for interactive interface)

### File Structure
```
design_specs/
├── control_flow_visualizer.py     # Core generator
├── control_flow_visualizer.html   # Web interface  
├── serve_visualizer.py            # Development server
├── CONTROL_FLOWS_SPEC.md          # Source specification
└── generated_diagrams/            # Output directory
    ├── high_level_flow.mmd
    ├── artifact_flow_flow.mmd
    ├── state_diagram_flow.mmd
    └── control_flow_diagrams.md
```

### Extending the Parser
The `ControlFlowVisualizer` class can be extended to:
- Parse additional YAML structures
- Generate custom diagram types
- Export to different formats
- Integrate with other tools

## 🎯 Use Cases

### Development Team
- **Visual Planning**: See flow dependencies before coding
- **Status Tracking**: Monitor implementation progress
- **Documentation**: Auto-generated, always up-to-date diagrams

### Project Management
- **Progress Visualization**: Gantt charts for timeline tracking
- **Dependency Analysis**: Understand phase relationships
- **Stakeholder Communication**: Clear visual status reports

### System Analysis
- **Bottleneck Identification**: Find complex artifact flows
- **Refactoring Planning**: Visualize before restructuring
- **Integration Points**: See where components connect

The visualizer transforms your YAML-based control flow specifications into beautiful, interactive diagrams that make complex system flows easy to understand and communicate.