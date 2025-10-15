# Todo #7: Designer UI Integration - Implementation Plan

**Date**: October 15, 2025  
**Status**: 🚧 In Progress  

## Objective

Integrate the transformation system with the TUI form designer to enable visual flow editing with automatic YAML updates, directory sync, and orchestrator regeneration.

## Current State Analysis

### Components Identified

1. **ControlFlowDesigner** (`control-flow/src/control_flow_engine/core/designer.py`)
   - High-level API for design-first workflow
   - Uses ScaffoldGenerator and OrchestratorUpdater
   - NOT a UI - it's a programmatic API

2. **InteractiveFlowDesigner** (`tui-form-designer/src/tui_form_designer/tools/designer.py`)
   - TUI interface using Questionary
   - Creates/edits YAML flows
   - Currently edits flow definitions (form layouts), NOT control flow specs

3. **Transformation System** (`control-flow/src/control_flow_engine/core/transformation.py`)
   - ControlFlowTransformation class
   - plan_renumber, plan_insert, plan_delete operations
   - Validation, directory sync, code path updates
   - Orchestrator regeneration

## Integration Strategy

### Option 1: Extend InteractiveFlowDesigner (RECOMMENDED)

Create a new `ControlFlowEditor` class in `tui-form-designer` that:
- Uses the transformation system for all modifications
- Provides visual interface for control flow editing
- Integrates with ControlFlowDesigner for scaffolding

**Pros**:
- Cleanly separates concerns
- Reuses existing TUI framework
- Can have both flow designer and control flow editor
- Transformation system remains library code

**Cons**:
- New file to create
- Need to bridge two projects

### Option 2: Add Transformation to ControlFlowDesigner

Add transformation methods to ControlFlowDesigner class:
- renumber_step(), insert_step(), delete_step()
- Internally uses ControlFlowTransformation
- ControlFlowDesigner becomes the unified API

**Pros**:
- Single API for all control flow operations
- All in one place

**Cons**:
- Mixes UI concerns with core API
- No visual interface still

### Option 3: Hybrid Approach (CHOSEN)

1. **Backend**: Extend ControlFlowDesigner with transformation methods
2. **Frontend**: Create new ControlFlowEditor TUI that uses the enhanced ControlFlowDesigner

**Benefits**:
- Clean separation: API layer + UI layer
- ControlFlowDesigner becomes complete API
- TUI provides visual interface
- Both can be used independently

## Implementation Plan

### Phase 1: Enhance ControlFlowDesigner (Backend)

**File**: `control-flow/src/control_flow_engine/core/designer.py`

Add methods:
```python
def renumber_phase(self, old_seq, new_seq, cascade=True)
def renumber_step(self, phase_seq, old_seq, new_seq, cascade=True)
def insert_phase(self, phase_data, cascade=True)
def insert_step(self, phase_seq, step_data, cascade=True)
def delete_phase(self, phase_seq, cascade=True)
def delete_step(self, phase_seq, step_seq, cascade=True)
def get_transformation_history(self, limit=None)
def rollback_transformation(self, steps=1)
def preview_transformation(self, operation, **kwargs)
```

**Implementation**:
- Internally instantiate ControlFlowTransformation
- Wrap transformation operations
- Enable all flags (sync_directories, update_code_paths, regenerate_orchestrators)
- Return user-friendly results

### Phase 2: Create ControlFlowEditor TUI (Frontend)

**File**: `tui-form-designer/src/tui_form_designer/tools/control_flow_editor.py`

Features:
- List phases and steps visually
- Renumber operations with preview
- Insert new phases/steps with form
- Delete with confirmation
- View transformation history
- Rollback with step selection
- Validate before apply

Menu structure:
```
Control Flow Editor
├── View Current Structure
├── Modify Flow
│   ├── Renumber Phase
│   ├── Renumber Step
│   ├── Insert Phase
│   ├── Insert Step
│   ├── Delete Phase
│   └── Delete Step
├── History
│   ├── View History
│   └── Rollback
├── Utilities
│   ├── Validate Flow
│   └── Generate Diagrams
└── Exit
```

### Phase 3: Integration Testing

Test scenarios:
1. Renumber phase with cascade
2. Insert step in middle of phase
3. Delete step and rollback
4. Multi-step transformation
5. Directory sync verification
6. Orchestrator regeneration check
7. Code path update validation

## File Structure

```
control-flow/
├── src/control_flow_engine/core/
│   └── designer.py (enhanced with transformation methods)
└── docs/
    ├── TODO_7_INTEGRATION_PLAN.md (this file)
    └── TODO_7_COMPLETE.md (after completion)

tui-form-designer/
└── src/tui_form_designer/tools/
    ├── designer.py (existing flow designer)
    └── control_flow_editor.py (NEW - control flow TUI)
```

## Dependencies

### Python Packages
- questionary (already in tui-form-designer)
- PyYAML (already available)
- pathlib (stdlib)

### Internal Dependencies
- control_flow_engine.core.designer.ControlFlowDesigner
- control_flow_engine.core.transformation.ControlFlowTransformation
- tui_form_designer.ui.questionary_ui.QuestionaryUI

## Timeline Estimate

- **Phase 1**: 2-3 hours (enhance ControlFlowDesigner)
- **Phase 2**: 3-4 hours (create TUI editor)
- **Phase 3**: 1-2 hours (integration testing)
- **Total**: 6-9 hours

## Success Criteria

✅ ControlFlowDesigner has transformation methods  
✅ TUI editor can list phases/steps  
✅ TUI editor can renumber with preview  
✅ TUI editor can insert phases/steps  
✅ TUI editor can delete with confirmation  
✅ TUI editor shows transformation history  
✅ TUI editor can rollback transformations  
✅ All operations trigger sync + regeneration  
✅ User-friendly error messages  
✅ Comprehensive examples/documentation  

## Next Steps

1. Review and approve this plan
2. Begin Phase 1: Enhance ControlFlowDesigner
3. Test enhanced API with examples
4. Begin Phase 2: Create TUI editor
5. Integration testing
6. Documentation and examples
7. Mark Todo #7 complete

---

**Status**: Awaiting approval to proceed with Phase 1  
**Last Updated**: October 15, 2025
