# Graphviz Visualizer Test Example

This directory contains a complete working example of the Graphviz control flow visualizer.

## Files

- **test_flow_spec.yml** - Sample control flow specification with 4 phases and 5 artifacts
- **test_graphviz_visualizer.py** - Test script that generates diagrams from the spec
- **test_output/** - Directory containing generated diagrams in multiple formats

## Running the Example

```bash
cd /opt/openproject/external/control-flow
python3 examples/graphviz_test/test_graphviz_visualizer.py
```

## Expected Output

The script will:
1. Parse the YAML specification
2. Display phase and artifact information
3. Generate 3 types of diagrams in 3 formats each (9 files total):
   - phase_flow.{svg,png,pdf}
   - artifact_flow.{svg,png,pdf}
   - combined_flow.{svg,png,pdf}

## Sample Control Flow

The test spec demonstrates a typical deployment workflow:

1. **Discovery Phase** (completed) → Produces network_map, service_inventory
2. **Configuration Phase** (in_progress) → Consumes network data, produces config_data
3. **Validation Phase** (pending) → Validates configurations, produces validation_report
4. **Deployment Phase** (pending) → Deploys validated configs, produces deployment_log

## Viewing Diagrams

Open any of the generated files:
- **.svg** files can be opened in any web browser
- **.png** files can be viewed with any image viewer
- **.pdf** files can be opened with any PDF reader

## Using This as a Template

You can copy `test_flow_spec.yml` and modify it for your own control flows. The YAML format is straightforward:

```yaml
phases:
  - id: phase_id
    name: "Phase Name"
    status: completed|in_progress|pending|blocked
    description: "What this phase does"
    artifacts_produced: [list, of, artifacts]
    artifacts_consumed: [list, of, artifacts]
    dependencies: [list, of, phase_ids]

artifacts:
  - name: artifact_name
    description: "What this artifact contains"
    producers: [phase_ids]
    consumers: [phase_ids]
    lifecycle: persistent|transient
```
