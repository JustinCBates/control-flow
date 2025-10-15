#!/usr/bin/env python3
"""
Directory Synchronization Example

Demonstrates how transformations automatically synchronize the directory structure
to match YAML changes.

Author: Control Flow Engine  
Date: 2025-10-15
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from control_flow_engine.core.engine import ControlFlowManager


def example_renumber_with_directory_sync():
    """
    Example: Renumber sequences and sync directories
    
    This shows how renumbering step 0→1 also renames directories:
    - step_0_discovery_prompt/ → step_1_discovery_prompt/
    - step_1_env_discovery/ → step_2_env_discovery/
    - etc.
    """
    print("=" * 70)
    print("EXAMPLE: Renumber with Directory Synchronization")
    print("=" * 70)
    
    # Load specification
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    # Project base path (where phases/ directory is)
    project_base = Path("/opt/openproject/external/config-manager")
    
    print("\n📋 Transformation: Renumber discovery steps (0,1,2,3 → 1,2,3,4)")
    print(f"📁 Project base: {project_base}")
    
    # Preview with directory sync (dry run)
    print("\n" + "=" * 70)
    print("PREVIEW (Dry Run)")
    print("=" * 70)
    
    manager.transform_and_apply(
        transformation_type="renumber",
        flow_name="main_config_flow",
        phase_id="discovery",
        start_from=1,
        strategy="compact",
        dry_run=True,  # Just preview
        sync_directories=False  # Don't preview directory ops yet
    )
    
    print("\n" + "=" * 70)
    print("DIRECTORY SYNC PREVIEW")
    print("=" * 70)
    print("\nIf we apply with sync_directories=True, the following will happen:")
    print("  1. YAML sequences updated (0→1, 1→2, 2→3, 3→4)")
    print("  2. Directories renamed to match:")
    print("     - phases/phase_1_discovery/step_0_discovery_prompt/")
    print("       → phases/phase_1_discovery/step_1_discovery_prompt/")
    print("     - phases/phase_1_discovery/step_1_env_discovery/")
    print("       → phases/phase_1_discovery/step_2_env_discovery/")
    print("     - phases/phase_1_discovery/step_2_system_discovery/")
    print("       → phases/phase_1_discovery/step_3_system_discovery/")
    print("     - phases/phase_1_discovery/step_3_defaults_generation/")
    print("       → phases/phase_1_discovery/step_4_defaults_generation/")
    
    print("\n" + "=" * 70)
    print("To apply with directory sync, run:")
    print("=" * 70)
    print("""
manager.transform_and_apply(
    transformation_type="renumber",
    flow_name="main_config_flow",
    phase_id="discovery",
    start_from=1,
    dry_run=False,
    sync_directories=True,
    project_base_path=Path("/opt/openproject/external/config-manager")
)
    """)


def example_delete_with_directory_sync():
    """
    Example: Delete a step and remove its directory
    
    Shows how deletion also removes the physical directory.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Delete with Directory Synchronization")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    project_base = Path("/opt/openproject/external/config-manager")
    
    print("\n📋 Transformation: Delete 'discovery_prompt' step")
    print(f"📁 Project base: {project_base}")
    
    # Create plan
    plan = manager.create_transformation(
        transformation_type="delete",
        flow_name="main_config_flow",
        element_id="discovery_prompt",
        phase_id="discovery",
        cascade_renumber=True
    )
    
    # Validate
    validation = manager.validate_transformation(plan)
    print(f"\n✓ Validation: {validation.status.value}")
    
    # Preview
    print("\n" + "=" * 70)
    print("YAML CHANGES")
    print("=" * 70)
    preview = manager.preview_transformation(plan)
    print(preview)
    
    print("\n" + "=" * 70)
    print("DIRECTORY OPERATIONS (if sync_directories=True)")
    print("=" * 70)
    print("\nThe following would happen:")
    print("  1. Delete step 'discovery_prompt' from YAML")
    print("  2. Renumber subsequent steps (1→0, 2→1, 3→2)")
    print("  3. DELETE directory: phases/phase_1_discovery/step_0_discovery_prompt/")
    print("  4. MOVE directory:")
    print("     - step_1_env_discovery/ → step_0_env_discovery/")
    print("     - step_2_system_discovery/ → step_1_system_discovery/")
    print("     - step_3_defaults_generation/ → step_2_defaults_generation/")
    
    print("\n⚠️  NOTE: Dry run only - no changes applied")


def example_insert_with_directory_sync():
    """
    Example: Insert a step and create its directory
    
    Shows how insertion creates a new directory structure.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Insert with Directory Synchronization")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    project_base = Path("/opt/openproject/external/config-manager")
    
    # Define new step
    new_step = {
        'step_id': 'confirmation_prompt',
        'name': 'User Confirmation',
        'type': 'interactive',
        'description': 'Ask user to confirm discovered settings',
        'status': 'PLANNED',
        'dependencies': ['defaults_generation']
    }
    
    print("\n📋 Transformation: Insert 'confirmation_prompt' step")
    print(f"📁 Project base: {project_base}")
    
    # Create plan
    plan = manager.create_transformation(
        transformation_type="insert",
        flow_name="main_config_flow",
        phase_id="discovery",
        new_element=new_step,
        insert_after="defaults_generation",
        cascade_renumber=True
    )
    
    # Validate
    validation = manager.validate_transformation(plan)
    print(f"\n✓ Validation: {validation.status.value}")
    
    # Preview
    print("\n" + "=" * 70)
    print("YAML CHANGES")
    print("=" * 70)
    for mapping in plan.mappings:
        print(f"  {mapping}")
    
    print("\n" + "=" * 70)
    print("DIRECTORY OPERATIONS (if sync_directories=True)")
    print("=" * 70)
    print("\nThe following would happen:")
    print("  1. Insert step 'confirmation_prompt' in YAML at sequence 4")
    print("  2. CREATE directory:")
    print("     - phases/phase_1_discovery/step_4_confirmation_prompt/")
    print("  3. Auto-generate __init__.py in new directory")
    
    print("\n⚠️  NOTE: Dry run only - no changes applied")


def main():
    """Run all directory sync examples."""
    print("\n🔄 Control Flow Directory Synchronization Examples\n")
    
    try:
        example_renumber_with_directory_sync()
        example_delete_with_directory_sync()
        example_insert_with_directory_sync()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        
        print("\nKey Takeaways:")
        print("  1. Set sync_directories=True to auto-sync directory structure")
        print("  2. RENUMBER → Renames directories (step_0_* → step_1_*)")
        print("  3. DELETE → Removes directories and renumbers remaining")
        print("  4. INSERT → Creates new directories with __init__.py")
        print("  5. All directory operations are preview-able before applying")
        
        print("\nSafety Features:")
        print("  ✓ Dry run mode for directory operations")
        print("  ✓ Automatic parent directory creation")
        print("  ✓ Error handling with detailed messages")
        print("  ✓ Can preview directory ops without executing")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
