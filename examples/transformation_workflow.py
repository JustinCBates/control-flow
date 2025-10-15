#!/usr/bin/env python3
"""
Control Flow Transformation Workflow Examples

Demonstrates the safe, validated transformation workflow for modifying
control flow specifications.

Author: Control Flow Engine
Date: 2025-10-15
"""

from pathlib import Path
import sys
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from control_flow_engine.core.engine import ControlFlowManager


def example_1_renumber_sequences():
    """
    Example 1: Renumber step sequences from 0,1,2,3 to 1,2,3,4
    
    This is the primary use case - fixing sequences after insertions
    that created step 0.
    """
    print("=" * 70)
    print("EXAMPLE 1: Renumber Sequences (0,1,2,3 → 1,2,3,4)")
    print("=" * 70)
    
    # Load specification
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    print("\n📋 Original step sequences in discovery phase:")
    discovery_phase = None
    for phase in manager.flows['main_config_flow']['phases']:
        if phase.get('phase_id') == 'discovery':
            discovery_phase = phase
            break
    
    if discovery_phase and 'steps' in discovery_phase:
        for step in discovery_phase['steps']:
            print(f"   {step.get('step_id'):25} seq: {step.get('sequence')}")
    
    # Method 1: Using the convenience method
    print("\n🔄 Using transform_and_apply() for quick transformation...")
    manager.transform_and_apply(
        transformation_type="renumber",
        flow_name="main_config_flow",
        phase_id="discovery",
        start_from=1,
        strategy="compact",
        dry_run=True  # Preview only
    )
    
    print("\n" + "=" * 70)


def example_2_detailed_workflow():
    """
    Example 2: Detailed step-by-step transformation workflow
    
    Shows the complete PLAN → VALIDATE → PREVIEW → APPLY cycle.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Detailed Transformation Workflow")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    # STEP 1: Create transformation plan
    print("\n1️⃣  PLAN: Create transformation plan")
    plan = manager.create_transformation(
        transformation_type="renumber",
        flow_name="main_config_flow",
        phase_id="discovery",
        start_from=1,
        strategy="compact"
    )
    print(f"   ✅ Created plan with {len(plan.mappings)} mappings")
    print(f"   Description: {plan.description}")
    
    # STEP 2: Validate the plan
    print("\n2️⃣  VALIDATE: Check transformation integrity")
    validation = manager.validate_transformation(plan)
    print(f"   Status: {validation.status.value}")
    print(f"   Valid: {validation.valid}")
    print(f"   Errors: {len(validation.errors)}")
    print(f"   Warnings: {len(validation.warnings)}")
    print(f"   Checks performed: {', '.join(validation.checks_performed.keys())}")
    
    # STEP 3: Preview changes
    print("\n3️⃣  PREVIEW: Review what will change")
    preview = manager.preview_transformation(plan)
    print(preview)
    
    # STEP 4: Apply transformation (commented out to avoid modifying files)
    print("\n4️⃣  APPLY: Execute transformation")
    print("   (Skipped in example - would call manager.apply_transformation(plan))")
    
    print("\n" + "=" * 70)


def example_3_insert_step():
    """
    Example 3: Insert a new step with automatic renumbering
    
    Shows how insertion can cascade renumber subsequent steps.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Insert New Step with Cascade Renumbering")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    # Define new step
    new_step = {
        'step_id': 'confirmation_prompt',
        'name': 'User Confirmation',
        'type': 'interactive',
        'description': 'Ask user to confirm discovered settings before proceeding',
        'status': 'PLANNED',
        'dependencies': ['defaults_generation'],
        'artifacts_consumed': ['enhanced_defaults_file'],
        'artifacts_produced': ['user_confirmed_settings']
    }
    
    print("\n📝 Creating plan to insert new step after 'defaults_generation'...")
    
    # Create insertion plan
    plan = manager.create_transformation(
        transformation_type="insert",
        flow_name="main_config_flow",
        phase_id="discovery",
        new_element=new_step,
        insert_after="defaults_generation",
        cascade_renumber=True
    )
    
    print(f"   ✅ Plan created with {len(plan.mappings)} mappings")
    print(f"   - Inserts: {len(plan.get_inserts())}")
    print(f"   - Renumbers: {len(plan.get_renumbers())}")
    
    # Validate
    validation = manager.validate_transformation(plan)
    print(f"\n✓ Validation: {validation.status.value}")
    
    if validation.warnings:
        print("\n⚠️  Warnings:")
        for warning in validation.warnings:
            print(f"   - {warning}")
    
    # Preview
    print("\n📋 Preview of changes:")
    for mapping in plan.mappings:
        print(f"   {mapping}")
    
    print("\n" + "=" * 70)


def example_4_delete_step():
    """
    Example 4: Delete a step with cascade renumbering
    
    Shows how deletion updates subsequent step sequences.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Delete Step with Cascade Renumbering")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    print("\n🗑️  Creating plan to delete 'discovery_prompt' step...")
    
    # Create deletion plan
    plan = manager.create_transformation(
        transformation_type="delete",
        flow_name="main_config_flow",
        element_id="discovery_prompt",
        phase_id="discovery",
        cascade_renumber=True
    )
    
    print(f"   ✅ Plan created with {len(plan.mappings)} mappings")
    print(f"   - Deletes: {len(plan.get_deletes())}")
    print(f"   - Renumbers: {len(plan.get_renumbers())}")
    
    # Validate
    validation = manager.validate_transformation(plan)
    print(f"\n✓ Validation: {validation.status.value}")
    
    if validation.errors:
        print("\n❌ Errors:")
        for error in validation.errors:
            print(f"   - {error}")
    
    if validation.warnings:
        print("\n⚠️  Warnings:")
        for warning in validation.warnings:
            print(f"   - {warning}")
    
    # Preview
    print("\n📋 Preview of changes:")
    for mapping in plan.mappings:
        print(f"   {mapping}")
    
    print("\n" + "=" * 70)


def example_5_validation_catches_errors():
    """
    Example 5: Validation catching broken dependencies
    
    Demonstrates how validation prevents breaking changes.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Validation Catches Broken Dependencies")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    print("\n🧪 Attempting to delete a step that other steps depend on...")
    
    # Try to delete env_discovery (which system_discovery depends on)
    plan = manager.create_transformation(
        transformation_type="delete",
        flow_name="main_config_flow",
        element_id="env_discovery",
        phase_id="discovery",
        cascade_renumber=True
    )
    
    # Validate - should catch the broken dependency
    validation = manager.validate_transformation(plan)
    
    print(f"\n✓ Validation status: {validation.status.value}")
    print(f"   Valid: {validation.valid}")
    
    if validation.errors:
        print("\n❌ Errors detected (this is expected):")
        for error in validation.errors:
            print(f"   - {error}")
    
    if not validation.valid:
        print("\n✅ Validation correctly prevented a breaking change!")
    
    print("\n" + "=" * 70)


def example_6_transformation_history():
    """
    Example 6: Tracking transformation history
    
    Shows how to view the history of all transformations applied.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Transformation History Tracking")
    print("=" * 70)
    
    spec_file = Path("/opt/openproject/external/config-manager/design_specs/control_flows.yml")
    manager = ControlFlowManager(spec_file)
    manager.load_specification()
    
    # Apply a few transformations (dry run to avoid actual changes)
    print("\n📚 Simulating multiple transformations...")
    
    # Transform 1: Renumber
    plan1 = manager.create_transformation(
        "renumber",
        flow_name="main_config_flow",
        phase_id="discovery",
        start_from=1
    )
    manager.validate_transformation(plan1)
    print(f"   1. {plan1.description}")
    
    # Transform 2: Insert
    new_step = {
        'step_id': 'test_step',
        'name': 'Test Step',
        'description': 'A test step',
        'status': 'PLANNED'
    }
    plan2 = manager.create_transformation(
        "insert",
        flow_name="main_config_flow",
        phase_id="discovery",
        new_element=new_step,
        insert_after="env_discovery"
    )
    manager.validate_transformation(plan2)
    print(f"   2. {plan2.description}")
    
    # View history (after applying, which we skip in example)
    print("\n📖 Transformation History:")
    print("   (Would show all applied transformations)")
    print(f"   Current history length: {len(manager.transformer.get_history())}")
    
    print("\n" + "=" * 70)


def main():
    """Run all examples."""
    print("\n" + "🔄 Control Flow Transformation Workflow Examples")
    print("\n")
    
    # Run examples
    try:
        example_1_renumber_sequences()
        example_2_detailed_workflow()
        example_3_insert_step()
        example_4_delete_step()
        example_5_validation_catches_errors()
        example_6_transformation_history()
        
        print("\n✅ All examples completed successfully!")
        print("\nKey Takeaways:")
        print("  1. Always use PLAN → VALIDATE → PREVIEW → APPLY workflow")
        print("  2. Validation catches breaking changes before they happen")
        print("  3. Cascade renumbering keeps sequences clean after modifications")
        print("  4. Preview lets you see exactly what will change")
        print("  5. Transformation history provides auditability")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
