"""
Rollback Examples for Control Flow Transformation System

This file demonstrates how to use the rollback functionality to undo transformations.
The rollback system reads the transformation history and applies inverse transformations
to restore previous states.

Prerequisites:
- A control flow spec YAML file
- Transformations performed that created history entries
"""

from pathlib import Path
from control_flow_engine.core.transformation import ControlFlowTransformation


def example_1_rollback_simple_renumber():
    """
    Example 1: Rollback a Simple Renumber Transformation
    
    Demonstrates:
    - Performing a renumber transformation
    - Rolling back to previous sequence numbers
    - History tracking of rollback
    """
    print("\n" + "="*70)
    print("Example 1: Rollback Simple Renumber")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Initial state:")
    print(f"   Phase: {transformer.original_spec['phase']['name']}")
    print(f"   Step 10 sequence: 10")
    
    # Perform renumber transformation
    print("\n2. Renumber step 10 to 15:")
    plan = transformer.plan_renumber(
        old_sequence=10,
        new_sequence=15,
        target_type='step'
    )
    transformer.apply(plan, save=True)
    print(f"   Step sequence changed: 10 -> 15")
    
    # Check history
    print("\n3. Check transformation history:")
    if transformer.history.can_rollback(1):
        print("   ✓ Rollback is available")
        last_entry = transformer.history.get_transformations(1)[0]
        print(f"   Last transformation: {last_entry['operation']} (sequence {last_entry['old_sequence']} -> {last_entry['new_sequence']})")
    
    # Rollback the transformation
    print("\n4. Rollback the renumber:")
    transformer.rollback(steps=1, save=True)
    print("   ✓ Rolled back to sequence 10")
    
    # Verify rollback
    print("\n5. Verify state after rollback:")
    transformer = ControlFlowTransformation(str(spec_file))
    steps = transformer.original_spec['phase']['steps']
    step = next((s for s in steps if s['sequence'] == 10), None)
    if step:
        print(f"   ✓ Step 10 restored: {step['name']}")
    else:
        print("   ✗ Step 10 not found (still renamed)")
    
    print("\n" + "="*70 + "\n")


def example_2_rollback_insert():
    """
    Example 2: Rollback an Insert Transformation
    
    Demonstrates:
    - Inserting a new step
    - Rolling back to remove the inserted step
    - Cascade sequence number restoration
    """
    print("\n" + "="*70)
    print("Example 2: Rollback Insert (Remove Inserted Step)")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Initial state:")
    initial_count = len(transformer.original_spec['phase']['steps'])
    print(f"   Step count: {initial_count}")
    
    # Perform insert transformation
    print("\n2. Insert new step at sequence 25:")
    new_step = {
        'sequence': 25,
        'name': 'Temporary Step',
        'description': 'This step will be rolled back',
        'action': 'test'
    }
    plan = transformer.plan_insert(
        element=new_step,
        target_type='step',
        cascade_renumber=True
    )
    transformer.apply(plan, save=True)
    print(f"   ✓ Inserted step at sequence 25")
    print(f"   ✓ Subsequent steps renumbered")
    
    # Check new state
    transformer = ControlFlowTransformation(str(spec_file))
    new_count = len(transformer.original_spec['phase']['steps'])
    print(f"   New step count: {new_count}")
    
    # Rollback the insert
    print("\n3. Rollback the insert:")
    transformer.rollback(steps=1, save=True)
    print("   ✓ Removed inserted step")
    print("   ✓ Restored original sequences")
    
    # Verify rollback
    print("\n4. Verify state after rollback:")
    transformer = ControlFlowTransformation(str(spec_file))
    final_count = len(transformer.original_spec['phase']['steps'])
    print(f"   Final step count: {final_count}")
    print(f"   Match original: {final_count == initial_count}")
    
    print("\n" + "="*70 + "\n")


def example_3_rollback_delete():
    """
    Example 3: Rollback a Delete Transformation
    
    Demonstrates:
    - Deleting a step
    - Rolling back to restore the deleted step
    - Restoration of complete element data
    """
    print("\n" + "="*70)
    print("Example 3: Rollback Delete (Restore Deleted Step)")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Initial state:")
    steps = transformer.original_spec['phase']['steps']
    step_to_delete = next((s for s in steps if s['sequence'] == 20), None)
    if step_to_delete:
        print(f"   Found step 20: {step_to_delete['name']}")
        original_data = step_to_delete.copy()
    
    # Perform delete transformation
    print("\n2. Delete step 20:")
    plan = transformer.plan_delete(
        sequence=20,
        target_type='step',
        cascade_renumber=True
    )
    transformer.apply(plan, save=True)
    print("   ✓ Deleted step 20")
    print("   ✓ Renumbered subsequent steps")
    
    # Verify deletion
    transformer = ControlFlowTransformation(str(spec_file))
    steps = transformer.original_spec['phase']['steps']
    deleted = next((s for s in steps if s['sequence'] == 20), None)
    print(f"   Step 20 exists: {deleted is not None}")
    
    # Rollback the delete
    print("\n3. Rollback the delete:")
    transformer.rollback(steps=1, save=True)
    print("   ✓ Restored deleted step")
    print("   ✓ Restored original sequences")
    
    # Verify restoration
    print("\n4. Verify restoration:")
    transformer = ControlFlowTransformation(str(spec_file))
    steps = transformer.original_spec['phase']['steps']
    restored = next((s for s in steps if s['sequence'] == 20), None)
    if restored:
        print(f"   ✓ Step 20 restored: {restored['name']}")
        print(f"   Name matches: {restored['name'] == original_data['name']}")
        print(f"   Description matches: {restored.get('description') == original_data.get('description')}")
    else:
        print("   ✗ Step 20 not restored")
    
    print("\n" + "="*70 + "\n")


def example_4_rollback_multiple():
    """
    Example 4: Rollback Multiple Transformations
    
    Demonstrates:
    - Performing multiple transformations
    - Rolling back multiple steps at once
    - Sequential inverse transformation application
    """
    print("\n" + "="*70)
    print("Example 4: Rollback Multiple Transformations")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Initial state:")
    initial_steps = transformer.original_spec['phase']['steps'].copy()
    print(f"   Step count: {len(initial_steps)}")
    
    # Perform multiple transformations
    print("\n2. Perform 3 transformations:")
    
    # Transformation 1: Renumber
    print("   a) Renumber step 10 -> 12")
    plan1 = transformer.plan_renumber(10, 12, 'step')
    transformer.apply(plan1, save=True)
    
    # Transformation 2: Insert
    print("   b) Insert new step at 25")
    transformer = ControlFlowTransformation(str(spec_file))
    new_step = {
        'sequence': 25,
        'name': 'Inserted Step',
        'description': 'Test insert',
        'action': 'test'
    }
    plan2 = transformer.plan_insert(new_step, 'step', cascade_renumber=True)
    transformer.apply(plan2, save=True)
    
    # Transformation 3: Delete
    print("   c) Delete step 30")
    transformer = ControlFlowTransformation(str(spec_file))
    plan3 = transformer.plan_delete(30, 'step', cascade_renumber=True)
    transformer.apply(plan3, save=True)
    
    # Check history
    print("\n3. Check transformation history:")
    transformer = ControlFlowTransformation(str(spec_file))
    history_entries = transformer.history.get_transformations(3)
    print(f"   Total transformations: {len(history_entries)}")
    for i, entry in enumerate(history_entries, 1):
        print(f"   {i}. {entry['operation']} (timestamp: {entry['timestamp']})")
    
    # Rollback all 3 transformations
    print("\n4. Rollback all 3 transformations:")
    transformer.rollback(steps=3, save=True)
    print("   ✓ Rolled back 3 transformations")
    
    # Verify complete restoration
    print("\n5. Verify complete restoration:")
    transformer = ControlFlowTransformation(str(spec_file))
    final_steps = transformer.original_spec['phase']['steps']
    print(f"   Final step count: {len(final_steps)}")
    print(f"   Matches initial: {len(final_steps) == len(initial_steps)}")
    
    # Check specific sequences
    has_10 = any(s['sequence'] == 10 for s in final_steps)
    has_12 = any(s['sequence'] == 12 for s in final_steps)
    has_25 = any(s['sequence'] == 25 for s in final_steps)
    has_30 = any(s['sequence'] == 30 for s in final_steps)
    
    print(f"   Step 10 restored: {has_10}")
    print(f"   Step 12 removed: {not has_12}")
    print(f"   Step 25 removed: {not has_25}")
    print(f"   Step 30 restored: {has_30}")
    
    print("\n" + "="*70 + "\n")


def example_5_rollback_with_directory_sync():
    """
    Example 5: Rollback with Directory Synchronization
    
    Demonstrates:
    - Performing transformation with directory sync
    - Rolling back with directory sync to restore file structure
    - Synchronized rollback of YAML and directories
    """
    print("\n" + "="*70)
    print("Example 5: Rollback with Directory Sync")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    project_base = Path("project")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Initial state:")
    print(f"   Spec file: {spec_file}")
    print(f"   Project base: {project_base}")
    
    # Perform transformation with directory sync
    print("\n2. Renumber step 10 -> 15 with directory sync:")
    plan = transformer.plan_renumber(10, 15, 'step')
    transformer.apply(
        plan,
        save=True,
        sync_directories=True,
        project_base_path=str(project_base)
    )
    print("   ✓ Renamed step in YAML")
    print("   ✓ Renamed step directory: steps/10 -> steps/15")
    
    # Check directory structure
    step_10_dir = project_base / transformer.original_spec['phase']['name'] / "steps" / "10"
    step_15_dir = project_base / transformer.original_spec['phase']['name'] / "steps" / "15"
    print(f"   Step 10 directory exists: {step_10_dir.exists()}")
    print(f"   Step 15 directory exists: {step_15_dir.exists()}")
    
    # Rollback with directory sync
    print("\n3. Rollback with directory sync:")
    transformer = ControlFlowTransformation(str(spec_file))
    transformer.rollback(
        steps=1,
        save=True,
        sync_directories=True,
        project_base_path=str(project_base)
    )
    print("   ✓ Restored step in YAML")
    print("   ✓ Restored step directory: steps/15 -> steps/10")
    
    # Verify directory restoration
    print("\n4. Verify directory restoration:")
    step_10_dir = project_base / transformer.original_spec['phase']['name'] / "steps" / "10"
    step_15_dir = project_base / transformer.original_spec['phase']['name'] / "steps" / "15"
    print(f"   Step 10 directory exists: {step_10_dir.exists()}")
    print(f"   Step 15 directory exists: {step_15_dir.exists()}")
    
    # Verify YAML restoration
    transformer = ControlFlowTransformation(str(spec_file))
    steps = transformer.original_spec['phase']['steps']
    has_10 = any(s['sequence'] == 10 for s in steps)
    has_15 = any(s['sequence'] == 15 for s in steps)
    print(f"   Step 10 in YAML: {has_10}")
    print(f"   Step 15 in YAML: {has_15}")
    
    print("\n" + "="*70 + "\n")


def example_6_check_rollback_availability():
    """
    Example 6: Check Rollback Availability
    
    Demonstrates:
    - Checking if rollback is available
    - Handling cases where rollback is not possible
    - Rollback limitations and error handling
    """
    print("\n" + "="*70)
    print("Example 6: Check Rollback Availability")
    print("="*70)
    
    # Setup
    spec_file = Path("specs/example_phase.yaml")
    transformer = ControlFlowTransformation(str(spec_file))
    
    print("\n1. Check initial rollback availability:")
    can_rollback_1 = transformer.history.can_rollback(1)
    can_rollback_5 = transformer.history.can_rollback(5)
    can_rollback_10 = transformer.history.can_rollback(10)
    
    print(f"   Can rollback 1 step: {can_rollback_1}")
    print(f"   Can rollback 5 steps: {can_rollback_5}")
    print(f"   Can rollback 10 steps: {can_rollback_10}")
    
    # Get transformation count
    all_transformations = transformer.history.get_transformations()
    rollbackable = [t for t in all_transformations if t.get('can_rollback', True)]
    print(f"   Total transformations: {len(all_transformations)}")
    print(f"   Rollbackable transformations: {len(rollbackable)}")
    
    # Attempt rollback
    print("\n2. Attempt rollback:")
    if transformer.history.can_rollback(1):
        print("   Rollback available - proceeding")
        transformer.rollback(steps=1, save=True)
        print("   ✓ Rollback completed")
    else:
        print("   ✗ No transformations available to rollback")
    
    # Check after rollback
    print("\n3. After rollback:")
    transformer = ControlFlowTransformation(str(spec_file))
    
    # Note: Rollback entries themselves cannot be rolled back
    latest = transformer.history.get_transformations(1)
    if latest and latest[0]['operation'] == 'ROLLBACK':
        print(f"   Latest entry is ROLLBACK")
        print(f"   Can rollback this ROLLBACK: {latest[0].get('can_rollback', True)}")
    
    # Count remaining rollbackable transformations
    all_transformations = transformer.history.get_transformations()
    rollbackable = [t for t in all_transformations if t.get('can_rollback', True)]
    print(f"   Remaining rollbackable transformations: {len(rollbackable)}")
    
    print("\n" + "="*70 + "\n")


def main():
    """
    Run all rollback examples
    """
    print("\n" + "="*70)
    print("CONTROL FLOW TRANSFORMATION - ROLLBACK EXAMPLES")
    print("="*70)
    
    print("\nThese examples demonstrate the rollback functionality.")
    print("Rollback allows you to undo transformations by applying inverse operations.")
    
    # Note: These examples assume you have:
    # 1. A spec file at specs/example_phase.yaml
    # 2. Transformations already performed that created history
    # 3. (Optional) Project directory structure for directory sync examples
    
    # Run examples
    try:
        example_1_rollback_simple_renumber()
        example_2_rollback_insert()
        example_3_rollback_delete()
        example_4_rollback_multiple()
        example_5_rollback_with_directory_sync()
        example_6_check_rollback_availability()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
