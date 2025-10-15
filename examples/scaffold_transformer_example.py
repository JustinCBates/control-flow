"""
Scaffold Transformer Examples for Control Flow Transformation System

This file demonstrates how to use the scaffold_transformer function for zero-point
creation of phases and steps. The scaffold_transformer integrates the transformation
system with the scaffolding system to provide a unified interface for creating new
control flow elements.

Prerequisites:
- Control flow transformation system
- Scaffolding system
- Project directory structure (optional, created if doesn't exist)
"""

from pathlib import Path
import sys
import shutil
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from control_flow_engine.core.transformation import scaffold_transformer


def example_1_create_new_phase_with_steps():
    """
    Example 1: Create New Phase with Initial Steps
    
    Demonstrates:
    - Creating a new phase from scratch
    - Adding initial steps to the phase
    - Creating directory structure
    - Initializing transformation history
    """
    print("\n" + "="*70)
    print("Example 1: Create New Phase with Initial Steps")
    print("="*70)
    
    # Create temporary project directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        spec_dir = project_dir / "specs"
        spec_file = spec_dir / "validation_phase.yaml"
        
        print("\n1. Create new phase with 2 initial steps:")
        
        result = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'validation',
                'name': 'Validation Phase',
                'sequence': 10,
                'description': 'Validate configuration files',
                'status': 'not_started',
                'initial_steps': [
                    {
                        'step_id': 'check_syntax',
                        'name': 'Check Syntax',
                        'sequence': 10,
                        'description': 'Validate YAML syntax',
                        'action': 'validate'
                    },
                    {
                        'step_id': 'verify_schema',
                        'name': 'Verify Schema',
                        'sequence': 20,
                        'description': 'Check against schema',
                        'action': 'verify'
                    }
                ]
            },
            project_base_path=str(project_dir),
            create_directories=True,
            initialize_history=True,
            save=True
        )
        
        print(f"\n2. Results:")
        print(f"   Created: {result['created']}")
        print(f"   Spec file: {result['spec_file']}")
        print(f"   Phase directory: {result['phase_dir']}")
        print(f"   Step directory: {result['step_dir']}")
        print(f"   History file: {result['history_file']}")
        
        print(f"\n3. Verify spec file exists:")
        print(f"   Spec exists: {spec_file.exists()}")
        
        if spec_file.exists():
            with open(spec_file, 'r') as f:
                content = f.read()
                print(f"   Spec preview (first 300 chars):")
                print("   " + "\n   ".join(content[:300].split('\n')))
        
        print(f"\n4. Verify directory structure:")
        if result['phase_dir']:
            phase_dir = result['phase_dir']
            print(f"   Phase directory exists: {phase_dir.exists()}")
            
            if phase_dir.exists():
                print(f"   Contents:")
                for item in sorted(phase_dir.rglob('*')):
                    if item.is_file():
                        rel_path = item.relative_to(phase_dir)
                        print(f"      {rel_path}")
        
        print(f"\n5. Verify transformation history:")
        if result['history_file']:
            history_file = result['history_file']
            print(f"   History file exists: {history_file.exists()}")
            
            if history_file.exists():
                import json
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    print(f"   Transformations recorded: {len(history.get('transformations', []))}")
                    if history.get('transformations'):
                        first = history['transformations'][0]
                        print(f"   First entry operation: {first.get('operation')}")
                        print(f"   Created from scaffold: {first.get('metadata', {}).get('created_from_scaffold')}")
    
    print("\n" + "="*70 + "\n")


def example_2_create_minimal_phase():
    """
    Example 2: Create Minimal Phase (No Initial Steps)
    
    Demonstrates:
    - Creating a phase without initial steps
    - Minimal configuration
    - YAML-only creation (no directories)
    """
    print("\n" + "="*70)
    print("Example 2: Create Minimal Phase")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        spec_file = project_dir / "specs" / "minimal_phase.yaml"
        
        print("\n1. Create phase with minimal configuration:")
        
        result = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'export',
                'name': 'Export Phase',
                'sequence': 50,
            },
            create_directories=False,  # YAML only
            initialize_history=True,
            save=True
        )
        
        print(f"\n2. Results:")
        print(f"   Created: {result['created']}")
        print(f"   Spec file: {result['spec_file']}")
        print(f"   Phase directory: {result['phase_dir']}")
        print(f"   History initialized: {result['history_file'] is not None}")
        
        print(f"\n3. Verify spec content:")
        if spec_file.exists():
            with open(spec_file, 'r') as f:
                content = f.read()
                print("   " + "\n   ".join(content.split('\n')))
    
    print("\n" + "="*70 + "\n")


def example_3_add_step_to_existing_phase():
    """
    Example 3: Add Step to Existing Phase
    
    Demonstrates:
    - Adding a step to an existing phase spec
    - Using transformation system for insertion
    - Directory creation for new step
    """
    print("\n" + "="*70)
    print("Example 3: Add Step to Existing Phase")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        spec_file = project_dir / "specs" / "existing_phase.yaml"
        
        # First, create a phase
        print("\n1. Create initial phase:")
        result1 = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'processing',
                'name': 'Processing Phase',
                'sequence': 20,
                'initial_steps': [
                    {
                        'step_id': 'parse_data',
                        'name': 'Parse Data',
                        'sequence': 10,
                        'action': 'parse'
                    }
                ]
            },
            project_base_path=str(project_dir),
            create_directories=True,
            save=True
        )
        
        print(f"   Created phase with {len(result1['transformer'].original_spec['phase']['steps'])} step(s)")
        
        # Now add a new step
        print("\n2. Add new step to existing phase:")
        result2 = scaffold_transformer(
            spec_file=spec_file,
            step_data={
                'step_id': 'transform_data',
                'name': 'Transform Data',
                'sequence': 20,
                'description': 'Transform parsed data',
                'action': 'transform',
                'phase_id': 'processing'
            },
            project_base_path=str(project_dir),
            create_directories=True,
            save=True
        )
        
        print(f"   Created: {result2['created']}")
        print(f"   Step directory: {result2['step_dir']}")
        
        # Verify updated spec
        print("\n3. Verify updated spec:")
        if result2['transformer']:
            steps = result2['transformer'].original_spec['phase']['steps']
            print(f"   Total steps in phase: {len(steps)}")
            for step in steps:
                print(f"      - Step {step['sequence']}: {step['name']} ({step['step_id']})")
        
        # Verify directory structure
        print("\n4. Verify directory structure:")
        phase_dir = project_dir / "phases" / "phase_20_processing"
        if phase_dir.exists():
            print(f"   Phase directory: {phase_dir}")
            for step_dir in sorted(phase_dir.glob("step_*")):
                print(f"      - {step_dir.name}")
    
    print("\n" + "="*70 + "\n")


def example_4_create_phase_with_cascade():
    """
    Example 4: Add Step with Cascade Renumbering
    
    Demonstrates:
    - Adding a step between existing steps
    - Cascade renumbering of subsequent steps
    - Directory renaming integration
    """
    print("\n" + "="*70)
    print("Example 4: Add Step with Cascade Renumbering")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        spec_file = project_dir / "specs" / "cascade_phase.yaml"
        
        # Create phase with multiple steps
        print("\n1. Create phase with 3 steps:")
        result1 = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'workflow',
                'name': 'Workflow Phase',
                'sequence': 30,
                'initial_steps': [
                    {'step_id': 'step_a', 'name': 'Step A', 'sequence': 10, 'action': 'a'},
                    {'step_id': 'step_b', 'name': 'Step B', 'sequence': 20, 'action': 'b'},
                    {'step_id': 'step_c', 'name': 'Step C', 'sequence': 30, 'action': 'c'},
                ]
            },
            project_base_path=str(project_dir),
            create_directories=True,
            save=True
        )
        
        print(f"   Created phase with steps: 10, 20, 30")
        
        # Insert step between 10 and 20 with cascade
        print("\n2. Insert new step at sequence 15 (with cascade):")
        result2 = scaffold_transformer(
            spec_file=spec_file,
            step_data={
                'step_id': 'step_a_half',
                'name': 'Step A.5',
                'sequence': 15,
                'description': 'Inserted between A and B',
                'action': 'a_half',
                'cascade_renumber': True  # Renumber subsequent steps
            },
            project_base_path=str(project_dir),
            create_directories=True,
            save=True
        )
        
        print(f"   Created: {result2['created']}")
        
        # Verify cascade renumbering
        print("\n3. Verify cascade renumbering:")
        if result2['transformer']:
            steps = result2['transformer'].original_spec['phase']['steps']
            print(f"   Step sequences after cascade:")
            for step in sorted(steps, key=lambda s: s['sequence']):
                print(f"      - Step {step['sequence']}: {step['name']} ({step['step_id']})")
    
    print("\n" + "="*70 + "\n")


def example_5_create_complex_phase():
    """
    Example 5: Create Complex Phase Structure
    
    Demonstrates:
    - Creating a complete phase with multiple steps
    - Rich metadata (descriptions, actions)
    - Full directory and history initialization
    """
    print("\n" + "="*70)
    print("Example 5: Create Complex Phase Structure")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        spec_file = project_dir / "specs" / "complex_phase.yaml"
        
        print("\n1. Create comprehensive phase:")
        
        result = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'deployment',
                'name': 'Deployment Phase',
                'sequence': 90,
                'description': 'Deploy application to production environment',
                'status': 'in_progress',
                'initial_steps': [
                    {
                        'step_id': 'validate_environment',
                        'name': 'Validate Environment',
                        'sequence': 10,
                        'description': 'Check deployment environment prerequisites',
                        'action': 'validate'
                    },
                    {
                        'step_id': 'build_artifacts',
                        'name': 'Build Artifacts',
                        'sequence': 20,
                        'description': 'Compile and package application',
                        'action': 'build'
                    },
                    {
                        'step_id': 'run_tests',
                        'name': 'Run Tests',
                        'sequence': 30,
                        'description': 'Execute integration and smoke tests',
                        'action': 'test'
                    },
                    {
                        'step_id': 'deploy_application',
                        'name': 'Deploy Application',
                        'sequence': 40,
                        'description': 'Deploy to production servers',
                        'action': 'deploy'
                    },
                    {
                        'step_id': 'verify_deployment',
                        'name': 'Verify Deployment',
                        'sequence': 50,
                        'description': 'Confirm deployment success',
                        'action': 'verify'
                    }
                ]
            },
            project_base_path=str(project_dir),
            create_directories=True,
            initialize_history=True,
            save=True
        )
        
        print(f"\n2. Results Summary:")
        print(f"   Created: {result['created']}")
        print(f"   Spec file: {result['spec_file'].exists()}")
        print(f"   Phase directory: {result['phase_dir'] is not None}")
        print(f"   History initialized: {result['history_file'] is not None}")
        
        print(f"\n3. Phase structure:")
        if result['transformer']:
            phase = result['transformer'].original_spec['phase']
            print(f"   Phase ID: {phase['phase_id']}")
            print(f"   Name: {phase['name']}")
            print(f"   Sequence: {phase['sequence']}")
            print(f"   Status: {phase['status']}")
            print(f"   Description: {phase['description']}")
            print(f"   Steps: {len(phase['steps'])}")
            
            print(f"\n4. Step details:")
            for step in phase['steps']:
                print(f"   {step['sequence']:3d}. {step['name']:<25s} ({step['step_id']})")
                print(f"        Action: {step['action']}")
                print(f"        Description: {step['description']}")
        
        print(f"\n5. Directory structure:")
        if result['phase_dir']:
            phase_dir = result['phase_dir']
            print(f"   Phase: {phase_dir.name}")
            
            # List step directories
            for step_dir in sorted(phase_dir.glob("step_*")):
                print(f"      - {step_dir.name}/")
                # List step files
                for step_file in sorted(step_dir.glob("*.py")):
                    print(f"          {step_file.name}")
            
            # List other directories
            for other_dir in sorted(phase_dir.glob("*")):
                if other_dir.is_dir() and not other_dir.name.startswith("step_"):
                    print(f"      - {other_dir.name}/")
    
    print("\n" + "="*70 + "\n")


def example_6_error_handling():
    """
    Example 6: Error Handling and Validation
    
    Demonstrates:
    - Handling invalid inputs
    - Error messages
    - Validation failures
    """
    print("\n" + "="*70)
    print("Example 6: Error Handling and Validation")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Test 1: Missing required data
        print("\n1. Test: Missing both phase_data and step_data")
        try:
            result = scaffold_transformer(
                spec_file=project_dir / "specs" / "test.yaml"
            )
            print("   ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✓ Correctly raised error: {e}")
        
        # Test 2: Adding step to non-existent spec
        print("\n2. Test: Add step to non-existent spec without phase_data")
        try:
            result = scaffold_transformer(
                spec_file=project_dir / "specs" / "nonexistent.yaml",
                step_data={
                    'step_id': 'test_step',
                    'name': 'Test Step',
                    'sequence': 10
                }
            )
            print("   ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✓ Correctly raised error: {e}")
        
        # Test 3: Invalid step insertion (duplicate sequence)
        print("\n3. Test: Invalid step insertion (duplicate sequence)")
        spec_file = project_dir / "specs" / "test_phase.yaml"
        
        # Create initial phase
        result1 = scaffold_transformer(
            spec_file=spec_file,
            phase_data={
                'phase_id': 'test',
                'name': 'Test Phase',
                'sequence': 1,
                'initial_steps': [
                    {'step_id': 'step1', 'name': 'Step 1', 'sequence': 10, 'action': 'test'}
                ]
            },
            create_directories=False,
            save=True
        )
        
        # Try to add step with same sequence (without cascade)
        try:
            result2 = scaffold_transformer(
                spec_file=spec_file,
                step_data={
                    'step_id': 'step2',
                    'name': 'Step 2',
                    'sequence': 10,  # Duplicate!
                    'cascade_renumber': False
                },
                create_directories=False,
                save=True
            )
            print("   ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✓ Correctly raised error (validation failed)")
            print(f"      Error: {str(e)[:100]}...")
    
    print("\n" + "="*70 + "\n")


def main():
    """
    Run all scaffold_transformer examples
    """
    print("\n" + "="*70)
    print("SCAFFOLD TRANSFORMER - EXAMPLES")
    print("="*70)
    
    print("\nThese examples demonstrate the scaffold_transformer function.")
    print("This function provides zero-point creation of phases and steps,")
    print("integrating the transformation system with scaffolding.")
    
    # Run examples
    try:
        example_1_create_new_phase_with_steps()
        example_2_create_minimal_phase()
        example_3_add_step_to_existing_phase()
        example_4_create_phase_with_cascade()
        example_5_create_complex_phase()
        example_6_error_handling()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
