# Move/Reorder/Swap Integration - IMPLEMENTATION GUIDE

## Status
✅ **Phase 1 Complete**: Backend libraries implemented (StructureMover, StructureSwapper, StructureReorderer)  
✅ **Phase 2 Complete**: Designer methods added (move_phase, move_step, swap_phases, swap_steps, reorder_phases, reorder_steps)  
🔄 **Phase 3 In Progress**: Flow-editor UI integration

## What's Done

### 1. Designer Methods Added ✅
File: `src/control_flow_engine/core/designer.py`

Six new methods added after `delete_step()` and before `get_transformation_history()`:

- `move_phase(from_sequence, to_sequence, preview_only=False)`
- `move_step(phase_id, from_sequence, to_sequence, preview_only=False)`
- `swap_phases(sequence_a, sequence_b, preview_only=False)`
- `swap_steps(phase_id, sequence_a, sequence_b, preview_only=False)`
- `reorder_phases(new_order, preview_only=False)`
- `reorder_steps(phase_id, new_order, preview_only=False)`

All methods:
- Use the Phase 1 libraries (StructureMover, StructureSwapper, StructureReorderer)
- Support preview mode
- Return dict with success/message/mappings
- Save to spec file automatically

### 2. Flow-Editor Menu Integration ✅
File: `src/control_flow_engine/ui/flow_editor.py`

Changes made:
- Added menu option: `{'name': '🔀 Move/Reorder/Swap', 'value': 'move'}`
- Added handler in `run()`: `elif action == 'move': self._move_menu()`

## What Still Needs to Be Done

### Add 7 Methods to Flow-Editor

The following methods need to be added to the `ControlFlowEditor` class in `flow_editor.py`.

**Location**: Insert these methods **AFTER** `_insert_step()` and **BEFORE** `_delete_menu()`

**Approximate line number**: Around line 658 (just before `def _delete_menu(self)`)

---

### Method 1: _move_menu()

```python
def _move_menu(self):
    """Move, swap, or reorder phases/steps."""
    print("\n" + "=" * 70)
    print("  Move / Swap / Reorder")
    print("=" * 70 + "\n")
    
    # Ask what operation to perform
    operation = questionary.select(
        "What operation would you like to perform?",
        choices=[
            {'name': 'Move Phase', 'value': 'move_phase'},
            {'name': 'Move Step', 'value': 'move_step'},
            {'name': 'Swap Phases', 'value': 'swap_phases'},
            {'name': 'Swap Steps', 'value': 'swap_steps'},
            {'name': 'Reorder Phases (batch)', 'value': 'reorder_phases'},
            {'name': 'Reorder Steps (batch)', 'value': 'reorder_steps'}
        ],
        style=custom_style
    ).ask()
    
    if operation == 'move_phase':
        self._move_phase()
    elif operation == 'move_step':
        self._move_step()
    elif operation == 'swap_phases':
        self._swap_phases()
    elif operation == 'swap_steps':
        self._swap_steps()
    elif operation == 'reorder_phases':
        self._reorder_phases()
    elif operation == 'reorder_steps':
        self._reorder_steps()
```

---

### Method 2: _move_phase()

```python
def _move_phase(self):
    """Move a phase to a new position."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if not phases:
        print("\n⚠️  No phases found.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    # Display current order
    print("\nCurrent Phase Order:")
    for phase in sorted_phases:
        print(f"  [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
    
    # Ask which phase to move
    from_seq = questionary.text(
        "\nEnter sequence number of phase to move:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    from_seq = int(from_seq)
    
    # Ask where to move it
    to_seq = questionary.text(
        f"Move phase from [{from_seq}] to which sequence?",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    to_seq = int(to_seq)
    
    if from_seq == to_seq:
        print("\n⚠️  Source and target are the same. Nothing to do.")
        input("\nPress Enter to continue...")
        return
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.move_phase(
        from_sequence=from_seq,
        to_sequence=to_seq,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSequence Changes:")
    for old_seq, new_seq in sorted(preview_result['mappings'].items()):
        if old_seq != new_seq:
            print(f"  [{old_seq}] → [{new_seq}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply these changes?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.move_phase(
            from_sequence=from_seq,
            to_sequence=to_seq,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

### Method 3: _move_step()

```python
def _move_step(self):
    """Move a step to a new position within its phase."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if not phases:
        print("\n⚠️  No phases found.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    phase_choices = []
    for phase in sorted_phases:
        steps_count = len(phase.get('steps', []))
        phase_choices.append({
            'name': f"{phase['name']} ({steps_count} steps)",
            'value': phase['phase_id']
        })
    
    phase_id = questionary.select(
        "Select phase containing the step:",
        choices=phase_choices,
        style=custom_style
    ).ask()
    
    # Find the phase
    target_phase = None
    for phase in phases:
        if phase['phase_id'] == phase_id:
            target_phase = phase
            break
    
    if not target_phase:
        print("\n❌ Phase not found.")
        input("\nPress Enter to continue...")
        return
    
    steps = target_phase.get('steps', [])
    if len(steps) < 2:
        print("\n⚠️  Phase must have at least 2 steps to move.")
        input("\nPress Enter to continue...")
        return
    
    sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
    
    # Display current order
    print(f"\nCurrent Step Order in '{target_phase['name']}':")
    for step in sorted_steps:
        print(f"  [{step['sequence']}] {step['name']} ({step['step_id']})")
    
    # Ask which step to move
    from_seq = questionary.text(
        "\nEnter sequence number of step to move:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    from_seq = int(from_seq)
    
    # Ask where to move it
    to_seq = questionary.text(
        f"Move step from [{from_seq}] to which sequence?",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    to_seq = int(to_seq)
    
    if from_seq == to_seq:
        print("\n⚠️  Source and target are the same. Nothing to do.")
        input("\nPress Enter to continue...")
        return
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.move_step(
        phase_id=phase_id,
        from_sequence=from_seq,
        to_sequence=to_seq,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSequence Changes:")
    for old_seq, new_seq in sorted(preview_result['mappings'].items()):
        if old_seq != new_seq:
            print(f"  [{old_seq}] → [{new_seq}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply these changes?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.move_step(
            phase_id=phase_id,
            from_sequence=from_seq,
            to_sequence=to_seq,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

### Method 4: _swap_phases()

```python
def _swap_phases(self):
    """Swap two phases."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if len(phases) < 2:
        print("\n⚠️  Need at least 2 phases to swap.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    # Display current order
    print("\nCurrent Phase Order:")
    for phase in sorted_phases:
        print(f"  [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
    
    # Ask which phases to swap
    seq_a = questionary.text(
        "\nEnter sequence number of first phase:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    seq_a = int(seq_a)
    
    seq_b = questionary.text(
        "Enter sequence number of second phase:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    seq_b = int(seq_b)
    
    if seq_a == seq_b:
        print("\n⚠️  Cannot swap a phase with itself.")
        input("\nPress Enter to continue...")
        return
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.swap_phases(
        sequence_a=seq_a,
        sequence_b=seq_b,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSwap:")
    print(f"  Phase at [{seq_a}] ↔ Phase at [{seq_b}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply this swap?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.swap_phases(
            sequence_a=seq_a,
            sequence_b=seq_b,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

### Method 5: _swap_steps()

```python
def _swap_steps(self):
    """Swap two steps within a phase."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if not phases:
        print("\n⚠️  No phases found.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    phase_choices = []
    for phase in sorted_phases:
        steps_count = len(phase.get('steps', []))
        phase_choices.append({
            'name': f"{phase['name']} ({steps_count} steps)",
            'value': phase['phase_id']
        })
    
    phase_id = questionary.select(
        "Select phase containing the steps:",
        choices=phase_choices,
        style=custom_style
    ).ask()
    
    # Find the phase
    target_phase = None
    for phase in phases:
        if phase['phase_id'] == phase_id:
            target_phase = phase
            break
    
    if not target_phase:
        print("\n❌ Phase not found.")
        input("\nPress Enter to continue...")
        return
    
    steps = target_phase.get('steps', [])
    if len(steps) < 2:
        print("\n⚠️  Need at least 2 steps to swap.")
        input("\nPress Enter to continue...")
        return
    
    sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
    
    # Display current order
    print(f"\nCurrent Step Order in '{target_phase['name']}':")
    for step in sorted_steps:
        print(f"  [{step['sequence']}] {step['name']} ({step['step_id']})")
    
    # Ask which steps to swap
    seq_a = questionary.text(
        "\nEnter sequence number of first step:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    seq_a = int(seq_a)
    
    seq_b = questionary.text(
        "Enter sequence number of second step:",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
    ).ask()
    seq_b = int(seq_b)
    
    if seq_a == seq_b:
        print("\n⚠️  Cannot swap a step with itself.")
        input("\nPress Enter to continue...")
        return
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.swap_steps(
        phase_id=phase_id,
        sequence_a=seq_a,
        sequence_b=seq_b,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSwap:")
    print(f"  Step at [{seq_a}] ↔ Step at [{seq_b}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply this swap?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.swap_steps(
            phase_id=phase_id,
            sequence_a=seq_a,
            sequence_b=seq_b,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

### Method 6: _reorder_phases()

```python
def _reorder_phases(self):
    """Batch reorder phases."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if len(phases) < 2:
        print("\n⚠️  Need at least 2 phases to reorder.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    # Display current order
    print("\nCurrent Phase Order:")
    for i, phase in enumerate(sorted_phases, 1):
        print(f"  {i}. [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
    
    print("\n" + "=" * 70)
    print("Enter new order as comma-separated list of sequence numbers.")
    print("Example: 3,1,2 means phase at [3] becomes first, [1] second, [2] third")
    print("=" * 70)
    
    new_order_input = questionary.text(
        "\nEnter new order:",
        validate=lambda x: all(s.strip().isdigit() for s in x.split(',')) or "Must be comma-separated numbers"
    ).ask()
    
    # Parse the new order
    new_order_list = [int(s.strip()) for s in new_order_input.split(',')]
    
    # Validate completeness
    current_sequences = sorted([p['sequence'] for p in phases])
    if sorted(new_order_list) != current_sequences:
        print(f"\n❌ Error: New order must include all sequences: {current_sequences}")
        input("\nPress Enter to continue...")
        return
    
    # Build the mapping (old_seq -> new_seq)
    new_order_map = {}
    for new_position, old_sequence in enumerate(new_order_list, 1):
        new_order_map[old_sequence] = new_position
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.reorder_phases(
        new_order=new_order_map,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSequence Changes:")
    for old_seq, new_seq in sorted(preview_result['mappings'].items()):
        if old_seq != new_seq:
            print(f"  [{old_seq}] → [{new_seq}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply these changes?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.reorder_phases(
            new_order=new_order_map,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

### Method 7: _reorder_steps()

```python
def _reorder_steps(self):
    """Batch reorder steps within a phase."""
    spec = self.manager.get_specification()
    flow = spec.get('flows', {}).get(self.manager.flow_name, {})
    phases = flow.get('phases', [])
    
    if not phases:
        print("\n⚠️  No phases found.")
        input("\nPress Enter to continue...")
        return
    
    sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
    
    phase_choices = []
    for phase in sorted_phases:
        steps_count = len(phase.get('steps', []))
        phase_choices.append({
            'name': f"{phase['name']} ({steps_count} steps)",
            'value': phase['phase_id']
        })
    
    phase_id = questionary.select(
        "Select phase containing the steps:",
        choices=phase_choices,
        style=custom_style
    ).ask()
    
    # Find the phase
    target_phase = None
    for phase in phases:
        if phase['phase_id'] == phase_id:
            target_phase = phase
            break
    
    if not target_phase:
        print("\n❌ Phase not found.")
        input("\nPress Enter to continue...")
        return
    
    steps = target_phase.get('steps', [])
    if len(steps) < 2:
        print("\n⚠️  Need at least 2 steps to reorder.")
        input("\nPress Enter to continue...")
        return
    
    sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
    
    # Display current order
    print(f"\nCurrent Step Order in '{target_phase['name']}':")
    for i, step in enumerate(sorted_steps, 1):
        print(f"  {i}. [{step['sequence']}] {step['name']} ({step['step_id']})")
    
    print("\n" + "=" * 70)
    print("Enter new order as comma-separated list of sequence numbers.")
    print("Example: 3,1,2 means step at [3] becomes first, [1] second, [2] third")
    print("=" * 70)
    
    new_order_input = questionary.text(
        "\nEnter new order:",
        validate=lambda x: all(s.strip().isdigit() for s in x.split(',')) or "Must be comma-separated numbers"
    ).ask()
    
    # Parse the new order
    new_order_list = [int(s.strip()) for s in new_order_input.split(',')]
    
    # Validate completeness
    current_sequences = sorted([s['sequence'] for s in steps])
    if sorted(new_order_list) != current_sequences:
        print(f"\n❌ Error: New order must include all sequences: {current_sequences}")
        input("\nPress Enter to continue...")
        return
    
    # Build the mapping (old_seq -> new_seq)
    new_order_map = {}
    for new_position, old_sequence in enumerate(new_order_list, 1):
        new_order_map[old_sequence] = new_position
    
    # Preview
    print("\n" + "=" * 70)
    print("  Preview Changes")
    print("=" * 70)
    
    preview_result = self.designer.reorder_steps(
        phase_id=phase_id,
        new_order=new_order_map,
        preview_only=True
    )
    
    if not preview_result['success']:
        print(f"\n❌ Error: {preview_result['message']}")
        input("\nPress Enter to continue...")
        return
    
    print("\nSequence Changes:")
    for old_seq, new_seq in sorted(preview_result['mappings'].items()):
        if old_seq != new_seq:
            print(f"  [{old_seq}] → [{new_seq}]")
    
    # Confirm
    confirm = questionary.confirm(
        "\nApply these changes?",
        default=False,
        style=custom_style
    ).ask()
    
    if confirm:
        result = self.designer.reorder_steps(
            phase_id=phase_id,
            new_order=new_order_map,
            preview_only=False
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ Error: {result['message']}")
    else:
        print("\n❌ Cancelled.")
    
    input("\nPress Enter to continue...")
```

---

## Summary

**To complete the integration:**

1. Open `src/control_flow_engine/ui/flow_editor.py`
2. Find line ~658 (just before `def _delete_menu(self):`)
3. Insert all 7 methods above in order
4. Save the file
5. Test with flow-editor

**After adding these methods, the move/reorder/swap feature will be 100% complete!**

## Testing Plan

1. Run flow-editor
2. Select "🔀 Move/Reorder/Swap" from main menu
3. Test each operation:
   - Move Phase
   - Move Step
   - Swap Phases
   - Swap Steps
   - Reorder Phases (batch)
   - Reorder Steps (batch)
4. Verify preview shows correct changes
5. Verify actual changes are applied correctly
6. Check that spec file is saved

## Files Modified

- ✅ `src/control_flow_engine/core/designer.py` - 6 methods added (~400 LOC)
- ✅ `src/control_flow_engine/ui/flow_editor.py` - Menu option and handler added
- ⏳ `src/control_flow_engine/ui/flow_editor.py` - 7 UI methods need to be added (~700 LOC)

**Total New Code**: ~1,100 LOC
