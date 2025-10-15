# Designer Fix & Full Functionality - Discussion & Planning

**Date**: October 15, 2025  
**Status**: 🚧 Planning Discussion  
**Goal**: Make the designer fully functional and fix identified issues

---

## Current State Summary

### What We Have

**1. Backend Components** ✅
- `ControlFlowTransformation` - Complete transformation system (2,600 lines)
- `ControlFlowDesigner` - High-level API for greenfield workflow (1,273 lines)
- `ScaffoldGenerator` - Auto-scaffolding from specs
- `OrchestratorUpdater` - Code generation

**2. Frontend Component** ⚠️
- `flow_editor.py` - TUI using questionary library
- **Status**: Partially functional but has critical bugs

### Identified Issues

**Critical Bug** 🐛:
- **Arrow keys don't work in VS Code terminal**
- Questionary library limitation
- Makes tool unusable in common dev environment

**Missing Feature** ✨:
- **No Move/Reorder functionality**
- Can insert, delete, renumber
- Cannot simply move items to new positions

---

## Design Discussion Points

### 1. Terminal Compatibility Strategy

**Question**: How do we handle terminal compatibility?

**Option A: Fallback Numbered Menu**
```python
# Detect limited terminal
if is_limited_terminal():
    use_numbered_menu()  # 1, 2, 3 selection
else:
    use_questionary()    # Arrow key navigation
```

**Pros**:
- Works everywhere
- Quick implementation
- Maintains questionary for capable terminals

**Cons**:
- Two code paths to maintain
- Numbered menu less elegant

**Option B: Switch to Click**
```python
# Use click for all menus
@click.command()
@click.option('--operation', type=click.Choice(['browse', 'renumber', 'insert', ...]))
def flow_editor(operation):
    ...
```

**Pros**:
- Single implementation
- Click has better terminal support
- More maintainable

**Cons**:
- Less interactive (command-line vs menu)
- Larger refactor
- May need sub-commands

**Option C: Hybrid - Click + Questionary**
```python
# Click for main commands
@click.group()
def flow_editor():
    pass

@flow_editor.command()
def browse():
    # Use questionary for sub-selections if available
    if can_use_questionary():
        ...
    else:
        ...
```

**Pros**:
- Best of both worlds
- Click for command structure
- Questionary for interactive parts

**Cons**:
- Most complex
- Requires careful design

**🤔 Discussion**: Which approach do you prefer?

---

### 2. Move/Reorder Implementation

**Question**: What's the best UX for moving items?

**Option A: Two-Step Selection**
```
1. Select item to move
   "Move which phase? 2 (Template Rendering)"
2. Select new position
   "Move before which phase? 1 (Preflight)"
3. Preview + confirm
```

**Option B: Direct Position Input**
```
1. Select item to move
   "Move which phase? 2"
2. Enter new sequence
   "New sequence number: 15"
3. Auto-cascade renumber
```

**Option C: Visual Swap**
```
1. Show current order
2. Select two items to swap
3. Confirm swap
```

**🤔 Discussion**: Which UX pattern is most intuitive?

---

### 3. Integration Architecture

**Question**: How should Designer and Transformation system integrate?

**Current**:
```
ControlFlowDesigner
  ├── Uses ScaffoldGenerator (greenfield)
  ├── Uses OrchestratorUpdater (greenfield)
  └── Does NOT use Transformation (brownfield)

ControlFlowTransformation
  ├── Operates on existing specs
  ├── Has all CRUD operations
  └── Independent of Designer
```

**Proposed Integration** (from TODO_7_INTEGRATION_PLAN.md):

**Phase 1: Enhance ControlFlowDesigner Backend**
```python
class ControlFlowDesigner:
    # Add transformation methods
    def renumber_phase(self, old_seq, new_seq, cascade=True)
    def renumber_step(self, phase_seq, old_seq, new_seq, cascade=True)
    def insert_phase(self, phase_data, cascade=True)
    def insert_step(self, phase_seq, step_data, cascade=True)
    def delete_phase(self, phase_seq, cascade=True)
    def delete_step(self, phase_seq, step_seq, cascade=True)
    def move_phase(self, phase_seq, new_position)  # NEW
    def move_step(self, phase_seq, step_seq, new_position)  # NEW
    def get_transformation_history(self, limit=None)
    def rollback_transformation(self, steps=1)
    def preview_transformation(self, operation, **kwargs)
```

**Phase 2: Create New TUI Editor**
```python
# New file: control_flow_editor.py
class ControlFlowEditor:
    """TUI that uses enhanced ControlFlowDesigner"""
    
    def __init__(self, designer: ControlFlowDesigner):
        self.designer = designer
        
    def run(self):
        # Main menu loop
        # Uses designer methods
```

**🤔 Discussion**: Should we:
- A) Keep flow_editor.py and fix it
- B) Create new control_flow_editor.py from scratch
- C) Merge both into unified editor

---

### 4. User Experience Flow

**Question**: What should the ideal workflow look like?

**Scenario 1: User wants to move Step 3 to position 1**

**Current (broken)**:
1. Can't navigate menu in VS Code ❌

**Option A: After Fix (numbered menu)**:
```
Main Menu:
1. Browse Flow Structure
2. Move/Reorder
3. Insert Phase/Step
4. Delete Phase/Step
5. Renumber Sequences
6. View History
0. Exit

Select: 2

Move what?
1. Phase
2. Step

Select: 2

Available phases:
1. Phase 10: Preflight Validation
2. Phase 20: Template Rendering
3. Phase 30: Snapshot Creation

Select phase: 1

Steps in Preflight Validation:
1. Step 10: Load Configuration
2. Step 20: Validate Configuration
3. Step 30: Check Docker Daemon

Select step to move: 3

Move to position:
1. Before Step 10 (first)
2. Between Step 10 and Step 20
3. After Step 20 (last)

Select: 1

Preview:
  Step 30 → Step 10 (moved to first)
  Step 10 → Step 20 (renumbered)
  Step 20 → Step 30 (renumbered)

Apply? (y/n): y

✅ Move complete. Step renumbered.
```

**Option B: CLI-style**:
```bash
# More direct for power users
flow-editor move step --phase 10 --step 30 --before 10
flow-editor move phase --phase 30 --before 20
```

**🤔 Discussion**: Which UX flow is better for you?

---

### 5. Testing Strategy

**Question**: How do we ensure quality?

**Option A: Manual Testing Only**
- Test each operation manually
- Document test cases
- Quick but not repeatable

**Option B: Unit Tests**
```python
def test_move_step():
    designer = create_test_designer()
    result = designer.move_step(
        phase_seq=10,
        step_seq=30,
        new_position=1
    )
    assert result.success
    assert get_step_sequence(...) == 10
```

**Option C: Integration Tests**
```python
def test_full_workflow():
    # Create designer
    # Add phases
    # Move items
    # Verify YAML
    # Verify directories
    # Verify orchestrators
```

**🤔 Discussion**: What level of testing do you want?

---

## Proposed Implementation Plan

Based on TODO_7_INTEGRATION_PLAN.md, with additions:

### Phase 1: Fix Terminal Compatibility (2-3 hours)

**File**: `src/control_flow_engine/ui/flow_editor.py`

**Tasks**:
1. Implement terminal detection
2. Create fallback numbered menu system
3. Keep questionary for capable terminals
4. Test in VS Code, standard terminal, SSH

**Success Criteria**:
- ✅ Works in VS Code terminal
- ✅ Works in standard terminal
- ✅ Works over SSH
- ✅ Graceful degradation

### Phase 2: Add Move/Reorder Feature (2-3 hours)

**File**: `src/control_flow_engine/core/designer.py`

**Tasks**:
1. Add `move_phase()` method to Designer
2. Add `move_step()` method to Designer
3. Implement using transformation system
4. Add preview functionality
5. Update UI to expose move operations

**Success Criteria**:
- ✅ Can move phases to new positions
- ✅ Can move steps within phase
- ✅ Auto-renumbers sequences
- ✅ Syncs directories
- ✅ Updates orchestrators

### Phase 3: Enhance ControlFlowDesigner API (3-4 hours)

**File**: `src/control_flow_engine/core/designer.py`

**Tasks** (from TODO_7_INTEGRATION_PLAN.md):
1. Add transformation wrapper methods:
   - `renumber_phase()`, `renumber_step()`
   - `insert_phase()`, `insert_step()`
   - `delete_phase()`, `delete_step()`
   - `get_transformation_history()`
   - `rollback_transformation()`
   - `preview_transformation()`
2. Internally use `ControlFlowTransformation`
3. Enable all automation flags
4. Return user-friendly results

**Success Criteria**:
- ✅ Designer is complete API
- ✅ All transformation operations available
- ✅ Consistent with transformation system
- ✅ Well documented

### Phase 4: Testing & Documentation (2-3 hours)

**Tasks**:
1. Create comprehensive test scenarios
2. Test all operations end-to-end
3. Update documentation
4. Create user guide
5. Add examples

**Success Criteria**:
- ✅ All operations tested
- ✅ User guide complete
- ✅ Examples provided
- ✅ Known limitations documented

### Phase 5: Optional Enhancements (if time permits)

- Batch operations
- Templates
- Search/filter
- Visual diagrams
- Export/import

---

## Key Questions for Discussion

### 1. Terminal Compatibility

**Question**: Which approach for terminal compatibility?
- [ ] Option A: Fallback numbered menu
- [ ] Option B: Switch to Click
- [ ] Option C: Hybrid Click + Questionary
- [ ] Other: _______________

**Preference**: ?

---

### 2. Move/Reorder UX

**Question**: Which UX pattern for moving items?
- [ ] Option A: Two-step selection (item, then position)
- [ ] Option B: Direct position input (item, then sequence number)
- [ ] Option C: Visual swap (select two items to swap)
- [ ] Other: _______________

**Preference**: ?

---

### 3. Editor Architecture

**Question**: How should we structure the editor?
- [ ] Option A: Fix existing flow_editor.py
- [ ] Option B: Create new control_flow_editor.py
- [ ] Option C: Merge into unified editor
- [ ] Other: _______________

**Preference**: ?

---

### 4. Testing Level

**Question**: What level of testing?
- [ ] Option A: Manual testing only
- [ ] Option B: Unit tests
- [ ] Option C: Integration tests
- [ ] Option D: All of the above

**Preference**: ?

---

### 5. Implementation Scope

**Question**: What should we implement?
- [ ] Phase 1: Terminal compatibility fix (REQUIRED)
- [ ] Phase 2: Move/reorder feature (HIGH PRIORITY)
- [ ] Phase 3: Enhanced Designer API (HIGH PRIORITY)
- [ ] Phase 4: Testing & docs (REQUIRED)
- [ ] Phase 5: Optional enhancements (NICE TO HAVE)

**Which phases are must-haves for you**: ?

---

## Timeline Estimate

Based on selected options:

**Minimum (Phases 1, 2, 4)**:
- Terminal fix: 2-3 hours
- Move feature: 2-3 hours
- Testing/docs: 2-3 hours
- **Total**: 6-9 hours

**Recommended (Phases 1, 2, 3, 4)**:
- Terminal fix: 2-3 hours
- Move feature: 2-3 hours
- Designer API: 3-4 hours
- Testing/docs: 2-3 hours
- **Total**: 9-13 hours

**Complete (All phases)**:
- All of above: 9-13 hours
- Optional enhancements: 4-6 hours
- **Total**: 13-19 hours

---

## Success Criteria

**Must Have** ✅:
- [ ] Works in VS Code terminal
- [ ] Can move/reorder phases and steps
- [ ] Transformation system integrated
- [ ] Basic documentation

**Should Have** ✨:
- [ ] Designer API complete
- [ ] Comprehensive tests
- [ ] User guide
- [ ] Examples

**Nice to Have** 🎁:
- [ ] Batch operations
- [ ] Templates
- [ ] Search/filter
- [ ] Visual diagrams

---

## Next Steps

1. **Review this document** and answer the key questions
2. **Decide on approach** for each design point
3. **Prioritize phases** (which are must-haves)
4. **Start implementation** based on decisions
5. **Iterate and test** as we build

---

## Open Questions & Discussion Points

### Q1: Should we keep backward compatibility?

The current flow_editor.py works with legacy spec format. Should we:
- A) Maintain compatibility with old format
- B) Only support new format
- C) Auto-convert old to new format

**Impact**: ?

### Q2: Should designer.py handle both greenfield AND brownfield?

Currently:
- Greenfield (new projects): Use ControlFlowDesigner
- Brownfield (existing): Use ControlFlowTransformation

Should Designer be the unified API for both?

**Preference**: ?

### Q3: How important is the interactive menu vs CLI commands?

Some users prefer:
- Interactive menus (current approach)
- CLI commands (`flow-editor move ...`)
- Both

**Which do you use most**: ?

---

**Please review and provide feedback on:**
1. ✅ Which options you prefer for each design point
2. ✅ Which phases are must-have vs nice-to-have
3. ✅ Any concerns or additional requirements
4. ✅ Timeline constraints or priorities

Once we align on the approach, we can start implementation immediately!
