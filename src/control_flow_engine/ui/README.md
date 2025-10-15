# Control Flow Editor - Interactive TUI

An interactive terminal user interface for editing control flow specifications with real-time preview and full transformation support.

## Quick Start

```bash
# Install dependencies
pip install questionary

# Launch the editor
./bin/flow-editor /path/to/your/project

# Or use current directory
./bin/flow-editor .
```

## Features

### 📋 Browse Flow Structure
View your complete control flow with phases and steps organized hierarchically.

### 🔢 Renumber Sequences
Clean up sequence numbers with customizable starting points (0, 1, or any number) and strategies (compact or minimal).

### ➕ Insert Phase/Step
Add new phases or steps with precise position control:
- Insert at end
- Insert before existing element
- Insert after existing element
- Optional cascade renumbering

### 🗑️ Delete Phase/Step
Remove phases or steps with automatic cleanup:
- Cascade renumbering of remaining elements
- Preview before deletion
- Confirmation required

### 📜 View History
See the last 20 transformations with timestamps and descriptions.

### ↩️ Rollback Changes
Undo one or more transformations with preview support.

## Usage Example

```bash
$ ./bin/flow-editor /opt/myproject

======================================================================
  Control Flow Editor - Interactive Transformation Tool
======================================================================
  Project: myproject
  Flow: main_flow
======================================================================

? What would you like to do? (Use arrow keys)
 » 📋 Browse Flow Structure
   🔢 Renumber Sequences
   ➕ Insert Phase/Step
   🗑️  Delete Phase/Step
   📜 View History
   ↩️  Rollback Changes
   ─────────────
   🚪 Exit
```

## Safety Features

- **Preview Mode**: ALL operations show preview before applying
- **Confirmation Prompts**: Destructive operations require confirmation
- **Validation**: Input validated before processing
- **Error Handling**: Clear error messages with guidance
- **Rollback Support**: Undo transformations if needed

## Workflow Integration

Every transformation automatically triggers:
1. ✅ YAML specification update
2. ✅ Directory synchronization (create/rename/delete)
3. ✅ Import path updates in code files
4. ✅ Orchestrator regeneration

## Navigation

- **Arrow keys**: Navigate menu options
- **Enter**: Select option
- **Ctrl+C**: Cancel current operation
- **Type and Enter**: Text input fields

## Requirements

- Python 3.7+
- questionary library: `pip install questionary`
- Control Flow project with valid specification

## Tips

1. **Browse first** - Understand current structure
2. **Always preview** - Review changes before applying
3. **Use cascade renumber** - Keeps sequences clean
4. **Check history** - Verify transformations
5. **Rollback available** - Mistakes can be undone

## Architecture

```
flow_editor.py
└── ControlFlowEditor
    ├── Browse flow structure
    ├── Renumber menu
    ├── Insert menu (phase/step)
    ├── Delete menu (phase/step)
    ├── View history
    └── Rollback menu
```

Uses `ControlFlowDesigner` API as backend for all transformations.

## See Also

- **Phase 1 Documentation**: `docs/TODO_7_PHASE1_COMPLETE.md` - Backend API
- **Phase 2 Documentation**: `docs/TODO_7_PHASE2_COMPLETE.md` - TUI Details
- **Examples**: `examples/designer_transformation_demo.py` - Programmatic API usage

## Troubleshooting

**Error: questionary not installed**
```bash
pip install questionary
```

**Error: Project root does not exist**
- Check path is correct
- Use absolute path or current directory (.)

**Error: Flow not found**
- Ensure project has valid control flow specification
- Check YAML file exists and is properly formatted

---

**Version**: 1.0  
**Created**: October 15, 2025  
**Part of**: Control Flow Transformation System
