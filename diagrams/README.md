# Control Flow Diagrams

This directory contains visual representations of the control flow architecture and workflows.

## Diagrams

### Phase Flow
**Files**: `phase_flow.svg`, `phase_flow.png`, `phase_flow.pdf`

Shows the phase-based execution model:
- Phase sequence and dependencies
- Orchestrator pattern
- Context passing between phases

### Artifact Flow
**Files**: `artifact_flow.svg`, `artifact_flow.png`, `artifact_flow.pdf`

Illustrates how artifacts flow through the system:
- Artifact production and consumption
- Data dependencies between steps
- Output management

### Combined Flow
**Files**: `combined_flow.svg`, `combined_flow.png`, `combined_flow.pdf`

Complete view combining:
- Phase execution
- Step processing
- Artifact flow
- Decision points

## Format Notes

- **SVG**: Scalable vector graphics, best for web and documentation
- **PNG**: Raster image, good for presentations
- **PDF**: Print-ready, maintains quality at any size

## Generating Diagrams

These diagrams can be regenerated from YAML specifications using the visualization tools in `tools/visualizer.py`:

```bash
python tools/visualizer.py examples/control_flows.yml --output diagrams/
```

See `docs/visualization_guide.md` for more details.
