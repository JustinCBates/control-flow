# Understanding control_flows.yml

## 📋 What It Is

`control_flows.yml` is a **design-first specification** that documents how your component works BEFORE you write the code. It's like a blueprint for your software.

## 🎯 Purpose

- **Plan before coding**: Design the flow, then implement
- **Track progress**: Mark phases as IMPLEMENTED, PLANNED, IN_PROGRESS, etc.
- **Document data flow**: See what data goes in and out of each phase
- **Communicate**: Share designs with team before building
- **Visualize**: Generate professional diagrams automatically

## 📐 Structure

### 1. **Component Info**
Basic metadata about what you're building:
```yaml
component:
  name: "config-manager"
  description: "OpenProject configuration management component"
  version: "1.0.0"
```

### 2. **Entry Points**
How users/systems interact with your component:
```yaml
entry_points:
  configure:
    status: "IMPLEMENTED"
    description: "Run complete configuration process"
    flow_id: "main_config_flow"  # Links to a flow below
```

### 3. **Flows**
The main workflows, broken into phases:
```yaml
flows:
  main_config_flow:
    description: "Primary Configuration Process"
    phases:
      - phase_id: "discovery"
        name: "Discovery Phase"
        status: "IMPLEMENTED"
        artifacts_produced: ["discovery_data"]  # What it creates
        artifacts_consumed: []                   # What it needs
```

### 4. **Artifacts**
Data products that flow through the system:
```yaml
artifacts:
  discovery_data:
    description: "Raw discovery data from environment scanning"
    format: "JSON"
```

### 5. **Decision Points**
Configuration options and branching logic:
```yaml
decision_points:
  continue_on_validation_failure:
    options: ["continue", "abort", "fix_and_retry"]
    default: "fix_and_retry"
```

### 6. **Implementation Status**
Overall tracking:
```yaml
implementation_status:
  overall: "IMPLEMENTED"
  last_updated: "2025-10-13"
  notes: "Core configuration flow fully implemented"
```

## 🔄 Example: Config-Manager Flow

The config-manager has this flow:

```
1. Discovery Phase (IMPLEMENTED)
   └─→ Produces: discovery_data, enhanced_defaults_file
   
2. TUI Defaults Mapping (IMPLEMENTED)
   ├─→ Consumes: enhanced_defaults_file
   └─→ Produces: tui_defaults_file
   
3. Interactive Collection (IMPLEMENTED)
   ├─→ Consumes: tui_defaults_file
   └─→ Produces: user_configuration
   
4. Validation Phase (IMPLEMENTED)
   ├─→ Consumes: user_configuration
   └─→ Produces: validated_configuration, validation_report
   
5. Export Phase (IMPLEMENTED)
   ├─→ Consumes: validated_configuration
   └─→ Produces: final_configuration_files
```

## 📊 Data Flow

```
[Discovery] → discovery_data → [Enhanced Defaults]
                                       ↓
                              enhanced_defaults_file
                                       ↓
                            [TUI Defaults Mapping]
                                       ↓
                               tui_defaults_file
                                       ↓
                           [Interactive Collection]
                                       ↓
                              user_configuration
                                       ↓
                             [Validation Phase]
                                       ↓
                          validated_configuration
                                       ↓
                              [Export Phase]
                                       ↓
                        final_configuration_files
```

## 💡 How to Use It

### 1. **Design Phase**
Before coding, create the control_flows.yml:
- Define your phases
- List artifacts each phase produces/consumes
- Mark everything as "PLANNED"

### 2. **Development Phase**
As you implement:
- Change status to "IN_PROGRESS" when you start
- Change to "IMPLEMENTED" when done
- Add new phases as you discover them

### 3. **Documentation Phase**
- Generate diagrams with Graphviz visualizer
- Include in README or design docs
- Share with team

### 4. **Maintenance Phase**
- Update when you refactor
- Always keep it in sync with code
- Use for onboarding new developers

## 🎨 Visualization

The control_flows.yml can be visualized using the Graphviz generator:

```bash
cd external/control-flow
python3 -m src.control_flow_engine.visualizer.graphviz_generator \
    ../config-manager/design_specs/control_flows.yml \
    --output-dir diagrams \
    --formats svg png pdf
```

This creates:
- **phase_flow diagram**: Shows execution sequence
- **artifact_flow diagram**: Shows data dependencies  
- **combined_flow diagram**: Shows everything together

## ✅ Benefits

1. **Design First**: Think through the flow before coding
2. **Documentation**: Always accurate (if you keep it updated)
3. **Visual Communication**: Diagrams > walls of text
4. **Progress Tracking**: See what's done vs planned
5. **Dependency Analysis**: Find missing data or circular deps
6. **Onboarding**: New developers understand flow quickly

## 🔧 Editing Tips

### Adding a New Phase
```yaml
- phase_id: "my_new_phase"
  name: "My New Phase"
  status: "PLANNED"  # Start with PLANNED
  description: "What this phase does"
  artifacts_produced: ["new_artifact"]
  artifacts_consumed: ["existing_artifact"]
```

### Updating Status
Simply change:
```yaml
status: "PLANNED"  # To any of:
# "PLANNED" - Not started yet
# "IN_PROGRESS" - Currently working on it
# "IMPLEMENTED" - Done and tested
# "BLOCKED" - Can't proceed (waiting on something)
# "DEPRECATED" - No longer used
```

### Adding Decision Points
```yaml
decision_points:
  my_decision:
    description: "What to do when X happens"
    options: ["option1", "option2", "option3"]
    default: "option1"
```

## 📁 File Locations

In your project:
```
external/
  ├── config-manager/
  │   └── design_specs/
  │       └── control_flows.yml      ← Config manager flow
  ├── deploy-manager/
  │   └── design_specs/
  │       └── control_flows.yml      ← Deploy manager flow
  └── control-flow/
      ├── src/control_flow_engine/   ← Visualizer code
      └── examples/graphviz_test/    ← Example specs
```

## 🚀 Quick Start

1. **View the example**:
   ```bash
   cat external/config-manager/design_specs/control_flows.yml
   ```

2. **Run the explanation**:
   ```bash
   python3 explain_control_flows.py
   ```

3. **Copy the template** for your own component:
   ```bash
   cp external/config-manager/design_specs/control_flows.yml \
      my-component/design_specs/control_flows.yml
   ```

4. **Edit** and customize for your needs

5. **Visualize**:
   ```bash
   cd external/control-flow
   python3 examples/graphviz_test/test_graphviz_visualizer.py
   ```

## 📚 Related Files

- `examples/graphviz_test/test_flow_spec.yml` - Simple example
- `external/control-flow/MIGRATION_MERMAID_TO_GRAPHVIZ.md` - Visualization tech details
- `explain_control_flows.py` - Interactive explanation script

---

**Remember**: The control_flows.yml is a living document. Update it as your design evolves!
