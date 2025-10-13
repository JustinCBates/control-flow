# 🔄 Control Flow Visualizer

An interactive visualization system for OpenProject control flows, built with Mermaid.js.

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
```bash
cd /opt/openproject/external/control-flow
python3 -m control_flow_engine.visualizer.web_server
```
Then open http://localhost:8000/

### Option 2: Generate Static Diagrams
```bash
cd /opt/openproject/external/control-flow
python3 -m control_flow_engine.visualizer.mermaid_generator
```
Check output for generated diagrams.

## 📊 Available Visualizations

### 1. **Overview** - High-level phase flow
- Shows main configuration phases
- Implementation status (✅ Implemented / ⏳ Pending)
- Sequential flow progression

### 2. **Artifacts** - Data flow between phases
- Process nodes (blue) and data artifacts (purple)
- Producer/consumer relationships

### 3. **Timeline** - Implementation timeline view
- Gantt chart showing development phases
- Current progress tracking
- Dependencies between components

### 4. **State Diagram** - System state transitions
- Configuration states and transitions
- Error states and recovery paths
- User interaction flows

## 🛠️ Features

### Interactive Web Interface
- **Tabbed Interface**: Switch between different visualization types
- **Live Refresh**: Update diagrams without page reload
- **Responsive Design**: Works on desktop and mobile
- **Export Options**: Save diagrams as SVG or PNG

### Python API
```python
from control_flow_engine.visualizer import ControlFlowVisualizer

visualizer = ControlFlowVisualizer()
diagrams = visualizer.generate_all_diagrams()
```

### CLI Interface
```bash
# Generate all diagrams
flow-engine visualize --all

# Generate specific diagram type
flow-engine visualize --type overview

# Start web server
flow-engine serve --port 8000
```

## 📁 Generated Outputs

Diagrams are saved to:
- `generated_diagrams/overview.md` - Overview flow diagram
- `generated_diagrams/artifacts.md` - Data flow diagram  
- `generated_diagrams/timeline.md` - Timeline Gantt chart
- `generated_diagrams/states.md` - State transition diagram

## 🔧 Configuration

The visualizer reads from:
- `CONTROL_FLOWS_SPEC.md` - Main specification file
- `config/visualization.yml` - Visualization settings
- Environment variables for customization

## 📚 Technical Details

### Architecture
- **Parser**: Extracts flow data from YAML specifications
- **Generator**: Creates Mermaid.js syntax
- **Server**: Serves interactive HTML interface
- **Templates**: Customizable HTML/CSS templates

### Dependencies
- Python 3.8+
- No external JavaScript dependencies (uses CDN for Mermaid.js)
- Built-in HTTP server for development

### Browser Support
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🤝 Integration

### With Control Flow Engine
The visualizer is fully integrated with the control flow engine:
```python
from control_flow_engine import ControlFlowManager

manager = ControlFlowManager()
manager.visualize()  # Opens web interface
```

### With CI/CD
Generate diagrams in your pipeline:
```bash
flow-engine visualize --output docs/diagrams/
```

## 🎯 Use Cases

1. **Development**: Visualize planned control flows before implementation
2. **Documentation**: Generate diagrams for technical documentation  
3. **Debugging**: Understand complex flow interactions
4. **Communication**: Share flow designs with stakeholders
5. **Planning**: Track implementation progress visually

---

*Part of the unified Control Flow Engine package*