# Control-Flow Feature & Bug Backlog

**Date Created**: October 15, 2025  
**Source**: User testing of flow-editor with deploy-manager control_flows.yml

---

## High Priority Bugs

### ✅ FIXED: Flow-Editor: Arrow Keys Don't Work in VS Code Terminal
**Status**: ✅ **RESOLVED** (October 16, 2025)  
**Severity**: High → FIXED  
**Component**: `src/control_flow_engine/ui/flow_editor.py`  
**Solution**: `src/control_flow_engine/libraries/interactive_ui/` (UniversalMenu)

**Original Problem**:
The `questionary` library used for the interactive menu doesn't work properly in VS Code integrated terminals. Arrow keys don't affect UI state, making navigation impossible.

**Impact**:
- ~~Users cannot navigate menus in VS Code terminal~~
- ~~Tool is unusable in this common development environment~~

**Solution Implemented**:
Created **UniversalMenu** library that automatically detects terminal capabilities:
1. ✅ Detects if running in VS Code/limited terminal (TERM env var, VSCODE_INJECTION, etc.)
2. ✅ Falls back to numbered menu with text input when arrow keys unavailable
3. ✅ Uses questionary for full terminal support when available
4. ✅ Consistent API across all terminal types

**Implementation**:
```python
from control_flow_engine.libraries.interactive_ui import UniversalMenu

menu = UniversalMenu()  # Auto-detects terminal
result = menu.select("Choose:", choices=[...])
```

**Test Results**: ✅ VERIFIED in VS Code terminal
- See: `docs/ARROW_KEY_BUG_FIX_RESULTS.md`
- Tests: `tests/test_arrow_key_fix.py`, `tests/test_interactive_fix.py`
- Demo: `demos/demo_interactive_ui.py`

**Commits**:
- 6606739: feat: add Interactive UI Library - SOLVES ARROW-KEY BUG!
- ef7d199: test: verify arrow-key bug fix works in VS Code terminal

**Next Steps**:
- [ ] Integrate UniversalMenu into flow_editor.py (replace questionary calls)
- [ ] Update tui-form-designer to use UniversalMenu (has same issue)
- [ ] Test in additional terminal environments

---

## High Priority Features

### ✅ IMPLEMENTED: Flow-Editor: Add Move/Reorder Feature
**Status**: ✅ **COMPLETE** (October 16, 2025)  
**Priority**: High → DONE  
**Component**: `src/control_flow_engine/ui/flow_editor.py`, `src/control_flow_engine/core/designer.py`

**Original Request**:
Currently there is no way to move or reorder phases/steps in the flow-editor. Users can only:
- Insert new items
- Delete items
- Renumber sequences

~~But there's no direct "move" operation to reorder existing items.~~

**Solution Implemented**:
Added complete move/swap/reorder functionality using Phase 1 libraries:

**Backend (designer.py)**:
- ✅ `move_phase(from_seq, to_seq)` - Move phase to new position
- ✅ `move_step(phase_id, from_seq, to_seq)` - Move step within phase
- ✅ `swap_phases(seq_a, seq_b)` - Swap two phases
- ✅ `swap_steps(phase_id, seq_a, seq_b)` - Swap two steps
- ✅ `reorder_phases(new_order)` - Batch reorder all phases
- ✅ `reorder_steps(phase_id, new_order)` - Batch reorder steps

**UI (flow_editor.py)**:
- ✅ New menu option: "🔀 Move/Reorder/Swap"
- ✅ 7 UI methods with preview and confirmation
- ✅ Shows current order before operation
- ✅ Previews changes before applying
- ✅ Confirms with user before execution
- ✅ Displays success/error messages

**Features**:
- ✅ Automatic cascade renumbering
- ✅ Preview mode (dry-run)
- ✅ User confirmation
- ✅ Error handling
- ✅ Sequence mapping display

**Commits**:
- 9356298: feat: add move/swap/reorder functionality (Part 1 - Backend)
- 1e7e75e: feat: add move/swap/reorder UI methods (Part 2 - Complete)

**Documentation**: `MOVE_REORDER_INTEGRATION_GUIDE.md`

**Uses**: Phase 1 structure_ops libraries (StructureMover, StructureSwapper, StructureReorderer)

---

## Medium Priority Features

### ✨ Batch Operations
**Status**: Feature Request  
**Priority**: Medium

**Description**:
Add ability to perform operations on multiple items at once:
- Move multiple steps
- Delete multiple phases/steps
- Copy multiple items

---

### ✨ Template-Based Creation
**Status**: Feature Request  
**Priority**: Medium

**Description**:
Add templates for common phase/step patterns:
- Standard validation phase template
- Standard deployment phase template
- Common step templates (config loading, health checks, etc.)

---

### ✨ Search and Filter
**Status**: Feature Request  
**Priority**: Medium

**Description**:
Add search functionality:
- Search for phase/step by name or ID
- Filter by status (planned/in-progress/implemented)
- Filter by library usage
- Jump to specific phase/step

---

## Low Priority Features

### ✨ Visual Flow Diagram
**Status**: Feature Request  
**Priority**: Low

**Description**:
Generate ASCII art or simple visualization of flow structure

Example:
```
[Phase 1: Preflight] → [Phase 2: Template] → [Phase 3: Snapshot]
    ↓                       ↓                      ↓
  6 steps                 4 steps                3 steps
```

---

### ✨ Export/Import
**Status**: Feature Request  
**Priority**: Low

**Description**:
- Export flow to Markdown documentation
- Export to JSON for external tools
- Import phases/steps from templates

---

### ✨ Dependency Visualization
**Status**: Feature Request  
**Priority**: Low

**Description**:
Show which units are used by which steps, identify unused units, show library coverage.

---

## Documentation Needs

### 📚 Terminal Compatibility Guide
Document which terminals work with questionary and provide workarounds

### 📚 Flow-Editor User Guide
Comprehensive guide for all operations with examples

### 📚 Best Practices
Guide for structuring control flows, naming conventions, etc.

---

## Technical Debt

### 🔧 Refactor Flow-Editor
Current code assumes specific spec structure (legacy flow-based format). Need to:
- Support multiple spec formats (flow-based vs phase-based)
- Auto-detect format
- Provide format conversion

### 🔧 Add Unit Tests
Flow-editor has no automated tests. Need comprehensive test coverage.

### 🔧 Error Handling Audit
While improved, error handling could be more comprehensive:
- Validate all user inputs
- Handle malformed YAML gracefully
- Better error messages

---

## Won't Fix / Known Limitations

### ⚠️ Questionary Terminal Compatibility
Questionary doesn't work in all terminals. This is a library limitation. Workaround: Use fallback numbered menu.

---

## Testing Notes

**Tested With**:
- Spec: deploy-manager control_flows.yml (6 phases, 24 steps, 28 units)
- Environment: VS Code integrated terminal on Linux
- Python: 3.x

**Test Results**:
- ✅ Browse Flow Structure: Works (after fixes)
- ❌ Arrow key navigation: Fails in VS Code terminal
- ⚠️ Other menu options: Not tested (navigation blocked)

---

**Maintained By**: GitHub Copilot / AI Assistant  
**Last Updated**: October 15, 2025
