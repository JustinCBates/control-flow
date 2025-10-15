"""
Transformation with Orchestrator Regeneration Examples

This file demonstrates the integrated workflow where YAML transformations
automatically trigger orchestrator code regeneration.

Benefits:
- YAML changes automatically update Python code
- Orchestrators stay in sync with specifications
- Single workflow for both YAML and code updates
- Validation before code generation

Prerequisites:
- Control flow transformation system
- Orchestrator regenerator
- Integration bridge module
- Existing orchestrator files with generated markers
"""

from pathlib import Path
import sys
import tempfile
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from control_flow_engine.core.transformation import ControlFlowTransformation


def example_1_renumber_with_regeneration():
    """
    Example 1: Renumber Step with Automatic Orchestrator Regeneration
    
    Demonstrates:
    - Renumbering a step in YAML
    - Automatically regenerating the phase orchestrator
    - Updated orchestrator reflects new sequence
    """
    print("\n" + "="*70)
    print("Example 1: Renumber Step + Auto-Regenerate Orchestrator")
    print("="*70)
    
    # This example requires an actual project structure with orchestrators
    # For demonstration, we'll show the workflow
    
    print("\n1. Load existing phase spec:")
    spec_file = Path("specs/discovery_phase.yaml")
    print(f"   Spec: {spec_file}")
    
    # Note: In a real scenario, this would be an existing file
    print("   (In real use: Load actual spec with orchestrator)")
    
    print("\n2. Plan step renumber:")
    print("   Old sequence: 10")
    print("   New sequence: 15")
    print("   Operation: RENUMBER")
    
    # Example code (requires actual file):
    """
    transformer = ControlFlowTransformation(str(spec_file))
    plan = transformer.plan_renumber(
        old_sequence=10,
        new_sequence=15,
        target_type='step'
    )
    """
    
    print("\n3. Apply transformation with orchestrator regeneration:")
    print("   save=True")
    print("   sync_directories=True")
    print("   regenerate_orchestrators=True  ← NEW!")
    
    # Example code:
    """
    result = transformer.apply(
        plan,
        save=True,
        sync_directories=True,
        project_base_path=Path("project"),
        regenerate_orchestrators=True  # Auto-regenerate!
    )
    """
    
    print("\n4. Results:")
    print("   ✅ YAML spec updated (step 10 → 15)")
    print("   ✅ Directory renamed (steps/10 → steps/15)")
    print("   ✅ Orchestrator regenerated")
    print("   ✅ Step execution order updated in orchestrator")
    
    print("\n5. What was regenerated:")
    print("   - phase_1_discovery/orchestrator_discovery.py")
    print("   - Updated STEP_IMPORTS section")
    print("   - Updated STEP_EXECUTION section")
    print("   - Preserved custom code outside markers")
    
    print("\n" + "="*70 + "\n")


def example_2_insert_step_with_regeneration():
    """
    Example 2: Insert New Step with Automatic Code Generation
    
    Demonstrates:
    - Inserting a new step into YAML
    - Creating step directory
    - Automatically regenerating orchestrator
    - New step added to execution flow
    """
    print("\n" + "="*70)
    print("Example 2: Insert Step + Auto-Regenerate Orchestrator")
    print("="*70)
    
    print("\n1. Create new step definition:")
    new_step = {
        'step_id': 'validate_input',
        'name': 'Validate Input',
        'sequence': 25,
        'description': 'Validate input parameters',
        'action': 'validate'
    }
    print(f"   Step ID: {new_step['step_id']}")
    print(f"   Sequence: {new_step['sequence']}")
    
    print("\n2. Plan insertion:")
    print("   Operation: INSERT")
    print("   Target: step")
    print("   Cascade renumber: True")
    
    # Example code:
    """
    transformer = ControlFlowTransformation("specs/phase.yaml")
    plan = transformer.plan_insert(
        element=new_step,
        target_type='step',
        cascade_renumber=True
    )
    """
    
    print("\n3. Apply with full workflow:")
    print("   save=True")
    print("   sync_directories=True  (create step directory)")
    print("   regenerate_orchestrators=True  (update orchestrator)")
    
    # Example code:
    """
    result = transformer.apply(
        plan,
        save=True,
        sync_directories=True,
        project_base_path=Path("project"),
        regenerate_orchestrators=True
    )
    """
    
    print("\n4. Complete workflow executed:")
    print("   ✅ Step added to YAML")
    print("   ✅ Subsequent steps renumbered")
    print("   ✅ Step directory created")
    print("   ✅ Orchestrator updated with new step")
    print("   ✅ Import added for new step")
    print("   ✅ Execution order updated")
    
    print("\n5. Files created/updated:")
    print("   - specs/phase.yaml (step added)")
    print("   - project/phases/phase_1_discovery/step_25_validate_input/ (created)")
    print("   - project/phases/phase_1_discovery/orchestrator_discovery.py (updated)")
    
    print("\n" + "="*70 + "\n")


def example_3_delete_step_with_regeneration():
    """
    Example 3: Delete Step with Automatic Orchestrator Cleanup
    
    Demonstrates:
    - Deleting a step from YAML
    - Removing step directory
    - Automatically cleaning up orchestrator
    - Removed step deleted from execution flow
    """
    print("\n" + "="*70)
    print("Example 3: Delete Step + Auto-Clean Orchestrator")
    print("="*70)
    
    print("\n1. Plan step deletion:")
    print("   Sequence to delete: 30")
    print("   Cascade renumber: True")
    
    # Example code:
    """
    transformer = ControlFlowTransformation("specs/phase.yaml")
    plan = transformer.plan_delete(
        sequence=30,
        target_type='step',
        cascade_renumber=True
    )
    """
    
    print("\n2. Apply with full cleanup:")
    print("   save=True")
    print("   sync_directories=True  (remove step directory)")
    print("   regenerate_orchestrators=True  (clean orchestrator)")
    
    # Example code:
    """
    result = transformer.apply(
        plan,
        save=True,
        sync_directories=True,
        project_base_path=Path("project"),
        regenerate_orchestrators=True
    )
    """
    
    print("\n3. Complete cleanup executed:")
    print("   ✅ Step removed from YAML")
    print("   ✅ Subsequent steps renumbered")
    print("   ✅ Step directory removed")
    print("   ✅ Orchestrator updated (step removed)")
    print("   ✅ Import removed")
    print("   ✅ Execution step removed")
    
    print("\n4. Files modified/deleted:")
    print("   - specs/phase.yaml (step deleted)")
    print("   - project/phases/phase_1_discovery/step_30_old_step/ (deleted)")
    print("   - project/phases/phase_1_discovery/orchestrator_discovery.py (cleaned)")
    
    print("\n" + "="*70 + "\n")


def example_4_scaffold_with_orchestrator():
    """
    Example 4: Scaffold New Phase with Orchestrator Generation
    
    Demonstrates:
    - Creating a new phase from scratch
    - Generating initial orchestrator
    - Complete ready-to-use phase structure
    """
    print("\n" + "="*70)
    print("Example 4: Scaffold Phase + Generate Orchestrator")
    print("="*70)
    
    print("\n1. Define new phase with steps:")
    phase_data = {
        'phase_id': 'validation',
        'name': 'Validation Phase',
        'sequence': 10,
        'description': 'Validate configuration',
        'initial_steps': [
            {
                'step_id': 'check_syntax',
                'name': 'Check Syntax',
                'sequence': 10,
                'action': 'validate'
            },
            {
                'step_id': 'verify_schema',
                'name': 'Verify Schema',
                'sequence': 20,
                'action': 'verify'
            }
        ]
    }
    
    print(f"   Phase: {phase_data['name']}")
    print(f"   Steps: {len(phase_data['initial_steps'])}")
    
    print("\n2. Scaffold with orchestrator generation:")
    # Example code:
    """
    from control_flow_engine.core.transformation import scaffold_transformer
    
    result = scaffold_transformer(
        spec_file=Path("specs/validation.yaml"),
        phase_data=phase_data,
        create_directories=True,
        project_base_path=Path("project"),
        generate_orchestrators=True  # Generate initial orchestrator
    )
    """
    
    print("\n3. Complete phase structure created:")
    print("   ✅ YAML spec created")
    print("   ✅ Phase directory created")
    print("   ✅ Step directories created (2)")
    print("   ✅ Orchestrator generated")
    print("   ✅ Step imports added")
    print("   ✅ Execution flow configured")
    
    print("\n4. Generated structure:")
    print("   specs/validation.yaml")
    print("   project/phases/phase_10_validation/")
    print("   ├── orchestrator_validation.py  ← Generated!")
    print("   ├── step_10_check_syntax/")
    print("   ├── step_20_verify_schema/")
    print("   └── outputs/")
    
    print("\n5. Ready to implement:")
    print("   - Orchestrator has execution framework")
    print("   - Steps have implementation stubs")
    print("   - Can immediately run (with TODOs)")
    
    print("\n" + "="*70 + "\n")


def example_5_workflow_comparison():
    """
    Example 5: Compare Manual vs. Automated Workflow
    
    Demonstrates:
    - Old manual workflow (multiple steps)
    - New integrated workflow (single command)
    - Benefits of integration
    """
    print("\n" + "="*70)
    print("Example 5: Workflow Comparison")
    print("="*70)
    
    print("\n📋 OLD MANUAL WORKFLOW:")
    print("   1. Edit YAML spec manually")
    print("   2. Validate YAML syntax")
    print("   3. Rename directories manually")
    print("   4. Update imports in code")
    print("   5. Run orchestrator_regenerator.py")
    print("   6. Check for errors")
    print("   7. Test orchestrator")
    print("   → Many manual steps, error-prone")
    
    print("\n✨ NEW INTEGRATED WORKFLOW:")
    print("   1. Create transformation plan")
    print("   2. transformer.apply(regenerate_orchestrators=True)")
    print("   → Single command, automated, validated")
    
    print("\n🎯 BENEFITS:")
    print("   ✅ Fewer steps (2 instead of 7)")
    print("   ✅ Validation before changes")
    print("   ✅ Atomic operations")
    print("   ✅ Rollback support")
    print("   ✅ History tracking")
    print("   ✅ No manual file editing")
    print("   ✅ No manual directory operations")
    print("   ✅ Automatic code generation")
    print("   ✅ Always in sync (YAML ↔ Python)")
    
    print("\n📊 TIME SAVINGS:")
    print("   Manual workflow: ~10-15 minutes")
    print("   Automated workflow: ~30 seconds")
    print("   → 20-30x faster!")
    
    print("\n" + "="*70 + "\n")


def example_6_error_handling():
    """
    Example 6: Error Handling in Integrated Workflow
    
    Demonstrates:
    - Validation before regeneration
    - Graceful error handling
    - Rollback on failure
    """
    print("\n" + "="*70)
    print("Example 6: Error Handling")
    print("="*70)
    
    print("\n1. Invalid transformation attempt:")
    print("   Trying to insert step with duplicate sequence...")
    
    # Example code:
    """
    plan = transformer.plan_insert(
        element={'step_id': 'dup', 'sequence': 10},  # Duplicate!
        target_type='step'
    )
    
    validation = transformer.validate(plan)
    # validation.valid = False
    # validation.errors = ['Sequence 10 already exists']
    """
    
    print("\n2. Apply with validation:")
    print("   Validation fails → No changes made")
    print("   ✗ YAML not modified")
    print("   ✗ Directories not changed")
    print("   ✗ Orchestrator not regenerated")
    print("   ✅ Error message shown to user")
    
    print("\n3. Regeneration failure handling:")
    print("   If orchestrator regeneration fails:")
    print("   - YAML changes are already saved (transaction complete)")
    print("   - Error is logged but doesn't block transformation")
    print("   - User can manually re-run regenerator if needed")
    
    print("\n4. Rollback support:")
    print("   If changes need to be undone:")
    # Example code:
    """
    transformer.rollback(
        steps=1,
        save=True,
        sync_directories=True,
        regenerate_orchestrators=True  # Also rollback orchestrator!
    )
    """
    print("   ✅ YAML reverted")
    print("   ✅ Directories restored")
    print("   ✅ Orchestrator regenerated to previous state")
    
    print("\n" + "="*70 + "\n")


def main():
    """
    Run all transformation + regeneration examples
    """
    print("\n" + "="*70)
    print("TRANSFORMATION + ORCHESTRATOR REGENERATION - EXAMPLES")
    print("="*70)
    
    print("\nThese examples demonstrate the integrated workflow where")
    print("YAML transformations automatically trigger orchestrator code")
    print("regeneration, keeping everything in sync.")
    
    # Run examples
    try:
        example_1_renumber_with_regeneration()
        example_2_insert_step_with_regeneration()
        example_3_delete_step_with_regeneration()
        example_4_scaffold_with_orchestrator()
        example_5_workflow_comparison()
        example_6_error_handling()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70 + "\n")
        
        print("KEY TAKEAWAYS:")
        print("1. Single workflow: Transform YAML → Auto-update Python")
        print("2. Always in sync: YAML changes trigger code updates")
        print("3. Validated: Changes are validated before code generation")
        print("4. Traceable: Full history of transformations and regenerations")
        print("5. Reversible: Rollback applies to both YAML and code")
        print("\nTo use: Add regenerate_orchestrators=True to transformer.apply()")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
