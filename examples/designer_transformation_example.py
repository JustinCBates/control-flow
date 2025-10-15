#!/usr/bin/env python3
"""
Example: ControlFlowDesigner with Transformation System Integration

Demonstrates using the enhanced ControlFlowDesigner with transformation methods.
"""

from pathlib import Path
import tempfile
import shutil
from control_flow_engine.core.designer import ControlFlowDesigner
from control_flow_engine.core.scaffolder import StepInsertion, PhaseInsertion
from control_flow_engine.core.engine import ImplementationStatus


def example_1_renumber_phase():
    """Example 1: Renumber a phase with cascade."""
    print("=" * 70)
    print("Example 1: Renumber Phase with Cascade")
    print("=" * 70)
    
    # Create temp project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "control_flows.yml"
        
        # Create new project
        designer = ControlFlowDesigner.new_project(
            project_name="test-project",
            project_root=project_root,
            description="Test project for transformation"
        )
        
        # Add some phases
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="initialization",
                name="Initialization Phase",
                sequence=10,
                description="Initialize system",
                status=ImplementationStatus.PLANNED
            )
        )
        
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="processing",
                name="Processing Phase",
                sequence=20,
                description="Process data",
                status=ImplementationStatus.PLANNED
            )
        )
        
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="finalization",
                name="Finalization Phase",
                sequence=30,
                description="Finalize and cleanup",
                status=ImplementationStatus.PLANNED
            )
        )
        
        print("\n📋 Initial phases:")
        for phase in designer.manager.spec['flows']['main_config_flow']['phases']:
            print(f"  {phase['sequence']}: {phase['name']}")
        
        # Preview renumbering
        print("\n🔍 Previewing renumber phase 10 → 15...")
        preview = designer.preview_transformation(
            'renumber_phase',
            old_sequence=10,
            new_sequence=15,
            cascade_renumber=True
        )
        
        if preview['success']:
            print(preview['preview'])
        
        # Apply renumbering
        print("\n✨ Applying renumber...")
        result = designer.renumber_phase(10, 15, cascade_renumber=True)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print("\n📋 Updated phases:")
            for phase in designer.manager.spec['flows']['main_config_flow']['phases']:
                print(f"  {phase['sequence']}: {phase['name']}")
        else:
            print(f"❌ {result['message']}")


def example_2_insert_step():
    """Example 2: Insert a new step with cascade."""
    print("\n" + "=" * 70)
    print("Example 2: Insert Step with Cascade")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "control_flows.yml"
        
        # Create project with phase and steps
        designer = ControlFlowDesigner.new_project(
            project_name="test-project",
            project_root=project_root
        )
        
        # Add phase
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="initialization",
                name="Initialization Phase",
                sequence=10,
                description="Initialize system",
                status=ImplementationStatus.PLANNED
            )
        )
        
        # Add steps
        designer.add_step(
            phase_id="initialization",
            step=StepInsertion(
                step_id="load_config",
                name="Load Configuration",
                sequence=10,
                description="Load config file",
                status=ImplementationStatus.PLANNED,
                step_type="io",
                phase_id="initialization",
                phase_sequence=10,
                is_tui_form=False
            )
        )
        
        designer.add_step(
            phase_id="initialization",
            step=StepInsertion(
                step_id="setup_logging",
                name="Setup Logging",
                sequence=20,
                description="Initialize logging",
                status=ImplementationStatus.PLANNED,
                step_type="setup",
                phase_id="initialization",
                phase_sequence=10,
                is_tui_form=False
            )
        )
        
        print("\n📋 Initial steps:")
        for step in designer.manager.spec['flows']['main_config_flow']['phases'][0]['steps']:
            print(f"  {step['sequence']}: {step['name']}")
        
        # Insert new step in the middle
        new_step = {
            'step_id': 'validate_environment',
            'name': 'Validate Environment',
            'sequence': 15,
            'description': 'Validate system environment',
            'status': 'planned',
            'step_type': 'validation'
        }
        
        print("\n✨ Inserting 'validate_environment' at sequence 15...")
        result = designer.insert_step(new_step, cascade_renumber=True)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print("\n📋 Updated steps:")
            for step in designer.manager.spec['flows']['main_config_flow']['phases'][0]['steps']:
                print(f"  {step['sequence']}: {step['name']}")
        else:
            print(f"❌ {result['message']}")


def example_3_delete_with_rollback():
    """Example 3: Delete a step and then rollback."""
    print("\n" + "=" * 70)
    print("Example 3: Delete Step and Rollback")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "control_flows.yml"
        
        designer = ControlFlowDesigner.new_project(
            project_name="test-project",
            project_root=project_root
        )
        
        # Add phase with steps
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="processing",
                name="Processing Phase",
                sequence=10,
                description="Process data",
                status=ImplementationStatus.PLANNED
            )
        )
        
        for i, step_name in enumerate(['Step A', 'Step B', 'Step C'], 1):
            designer.add_step(
                phase_id="processing",
                step=StepInsertion(
                    step_id=f"step_{chr(96+i)}",
                    name=step_name,
                    sequence=i*10,
                    description=f"Description for {step_name}",
                    status=ImplementationStatus.PLANNED,
                    step_type="processing",
                    phase_id="processing",
                    phase_sequence=10,
                    is_tui_form=False
                )
            )
        
        print("\n📋 Initial steps:")
        for step in designer.manager.spec['flows']['main_config_flow']['phases'][0]['steps']:
            print(f"  {step['sequence']}: {step['name']}")
        
        # Delete middle step
        print("\n🗑️  Deleting step at sequence 20 (Step B)...")
        result = designer.delete_step(20, cascade_renumber=True)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print("\n📋 After delete:")
            for step in designer.manager.spec['flows']['main_config_flow']['phases'][0]['steps']:
                print(f"  {step['sequence']}: {step['name']}")
        
        # View history
        print("\n📜 Transformation history:")
        history = designer.get_transformation_history(limit=3)
        for entry in history:
            print(f"  {entry['timestamp']}: {entry['transformation_type']} - {entry['description']}")
        
        # Rollback
        print("\n⏮️  Rolling back deletion...")
        rollback_result = designer.rollback_transformation(steps=1)
        
        if rollback_result['success']:
            print(f"✅ {rollback_result['message']}")
            print("\n📋 After rollback:")
            for step in designer.manager.spec['flows']['main_config_flow']['phases'][0]['steps']:
                print(f"  {step['sequence']}: {step['name']}")
        else:
            print(f"❌ {rollback_result['message']}")


def example_4_complex_workflow():
    """Example 4: Complex multi-operation workflow."""
    print("\n" + "=" * 70)
    print("Example 4: Complex Multi-Operation Workflow")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "control_flows.yml"
        
        # Create project
        designer = ControlFlowDesigner.new_project(
            project_name="complex-project",
            project_root=project_root,
            description="Complex transformation workflow"
        )
        
        # Add initial structure
        print("\n1️⃣ Creating initial structure...")
        for i in range(1, 4):
            designer.add_phase(
                phase=PhaseInsertion(
                    phase_id=f"phase_{i}",
                    name=f"Phase {i}",
                    sequence=i*10,
                    description=f"Description for phase {i}",
                    status=ImplementationStatus.PLANNED
                )
            )
        
        # Add steps to phase 1
        for i in range(1, 4):
            designer.add_step(
                phase_id="phase_1",
                step=StepInsertion(
                    step_id=f"p1_step_{i}",
                    name=f"Phase 1 Step {i}",
                    sequence=i*10,
                    description=f"Step {i} of phase 1",
                    status=ImplementationStatus.PLANNED,
                    step_type="processing",
                    phase_id="phase_1",
                    phase_sequence=10,
                    is_tui_form=False
                )
            )
        
        print("✅ Initial structure created")
        
        # Operation 1: Renumber phase
        print("\n2️⃣ Renumbering phase 2 from 20 to 25...")
        result = designer.renumber_phase(20, 25, cascade_renumber=True)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
        # Operation 2: Insert new step
        print("\n3️⃣ Inserting new step in phase 1...")
        new_step = {
            'step_id': 'p1_validation',
            'name': 'Validation Step',
            'sequence': 15,
            'description': 'Validate intermediate results',
            'status': 'planned',
            'step_type': 'validation'
        }
        result = designer.insert_step(new_step, cascade_renumber=True)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
        # Operation 3: Insert new phase
        print("\n4️⃣ Inserting new phase at sequence 15...")
        new_phase = {
            'phase_id': 'validation_phase',
            'name': 'Validation Phase',
            'sequence': 15,
            'description': 'Comprehensive validation',
            'status': 'planned'
        }
        result = designer.insert_phase(new_phase, cascade_renumber=True)
        print(f"{'✅' if result['success'] else '❌'} {result['message']}")
        
        # Show final state
        print("\n📋 Final structure:")
        print("\nPhases:")
        for phase in designer.manager.spec['flows']['main_config_flow']['phases']:
            print(f"  {phase['sequence']}: {phase['name']}")
        
        print("\nPhase 1 Steps:")
        for phase in designer.manager.spec['flows']['main_config_flow']['phases']:
            if phase['phase_id'] == 'phase_1' and 'steps' in phase:
                for step in phase['steps']:
                    print(f"  {step['sequence']}: {step['name']}")
        
        # Show history
        print("\n📜 Transformation history:")
        history = designer.get_transformation_history()
        for entry in history[:5]:  # Show last 5
            print(f"  {entry['timestamp']}: {entry['transformation_type']}")


def example_5_validation_and_preview():
    """Example 5: Using validation and preview features."""
    print("\n" + "=" * 70)
    print("Example 5: Validation and Preview")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        designer = ControlFlowDesigner.new_project(
            project_name="validation-test",
            project_root=project_root
        )
        
        # Add phase
        designer.add_phase(
            phase=PhaseInsertion(
                phase_id="test_phase",
                name="Test Phase",
                sequence=10,
                description="Test phase",
                status=ImplementationStatus.PLANNED
            )
        )
        
        # Add steps
        for i in [10, 20, 30]:
            designer.add_step(
                phase_id="test_phase",
                step=StepInsertion(
                    step_id=f"step_{i}",
                    name=f"Step {i}",
                    sequence=i,
                    description=f"Step at {i}",
                    status=ImplementationStatus.PLANNED,
                    step_type="processing",
                    phase_id="test_phase",
                    phase_sequence=10,
                    is_tui_form=False
                )
            )
        
        # Preview multiple operations
        print("\n🔍 Preview 1: Renumber step 20 → 25")
        preview = designer.preview_transformation(
            'renumber_step',
            old_sequence=20,
            new_sequence=25,
            cascade_renumber=True
        )
        if preview['success']:
            print(preview['preview'][:500])  # Show first 500 chars
        
        print("\n🔍 Preview 2: Delete step 20")
        preview = designer.preview_transformation(
            'delete_step',
            sequence=20,
            cascade_renumber=True
        )
        if preview['success']:
            print(preview['preview'][:500])
        
        # Validate spec
        print("\n✅ Validating specification...")
        validation = designer.validate()
        print(f"Valid: {validation.is_valid}")
        if validation.warnings:
            print("Warnings:")
            for warning in validation.warnings:
                print(f"  ⚠️  {warning}")


def main():
    """Run all examples."""
    print("\n" + "🎨" * 35)
    print("ControlFlowDesigner Transformation System Examples")
    print("🎨" * 35 + "\n")
    
    try:
        example_1_renumber_phase()
        example_2_insert_step()
        example_3_delete_with_rollback()
        example_4_complex_workflow()
        example_5_validation_and_preview()
        
        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
