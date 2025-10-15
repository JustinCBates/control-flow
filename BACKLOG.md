# Control-Flow Feature & Bug Backlog

**Date Created**: October 15, 2025  
**Source**: User testing of flow-editor with deploy-manager control_flows.yml

---

## High Priority Bugs

### 🐛 Flow-Editor: Arrow Keys Don't Work in VS Code Terminal
**Status**: Reported  
**Severity**: High  
**Component**: `src/control_flow_engine/ui/flow_editor.py`

**Description**:
The `questionary` library used for the interactive menu doesn't work properly in VS Code integrated terminals. Arrow keys don't affect UI state, making navigation impossible.

**Impact**:
- Users cannot navigate menus in VS Code terminal
- Tool is unusable in this common development environment

**Suggested Fix**:
Implement fallback menu system:
1. Detect if running in limited terminal (check `TERM` env var)
2. Fall back to numbered menu with text input when arrow keys unavailable
3. Keep questionary for full terminal support

**Example**:
```python
# Fallback numbered menu
print("\nMain Menu:")
print("1. Browse Flow Structure")
print("2. Renumber Sequences")
print("3. Insert Phase/Step")
print("4. Delete Phase/Step")
print("5. View History")
print("6. Rollback Changes")
print("0. Exit")
choice = input("\nSelect option (0-6): ")
```

**Related**: Consider using `click` instead of `questionary` for better terminal compatibility

---

## High Priority Features

### ✨ Flow-Editor: Add Move/Reorder Feature
**Status**: Feature Request  
**Priority**: High  
**Component**: `src/control_flow_engine/ui/flow_editor.py`

**Description**:
Currently there is no way to move or reorder phases/steps in the flow-editor. Users can only:
- Insert new items
- Delete items
- Renumber sequences

But there's no direct "move" operation to reorder existing items.

**Use Cases**:
1. User wants to move Step 3 to become Step 1
2. User wants to swap two phases
3. User realizes steps are in wrong order after creation

**Suggested Implementation**:
Add new menu option: "Move/Reorder Phase/Step"

Workflow:
```
1. Select scope (phases or steps within phase)
2. Show current order with numbers
3. Select item to move
4. Select new position (before/after another item)
5. Automatically renumber sequences
6. Preview changes
7. Confirm and apply
```

**Alternative Approach**:
Implement drag-and-drop style interaction:
```
Current order:
  [10] Phase A
  [20] Phase B
  [30] Phase C

Move which phase? 3 (Phase C)
Move before which phase? 1 (Phase A)

New order:
  [10] Phase C  ← moved
  [20] Phase A
  [30] Phase B

Apply changes? (y/n)
```

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
