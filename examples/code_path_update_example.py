#!/usr/bin/env python3
"""
Example demonstrating automatic code path updates after transformations.

This example shows how the transformation system can automatically update:
1. Python import statements
2. Configuration file paths  
3. Documentation references

After renumbering steps from 0,1,2 to 1,2,3, all code paths are updated accordingly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.control_flow_engine.core.engine import ControlFlowManager
from src.control_flow_engine.core.transformation import TransformationType


def example_1_renumber_with_code_updates():
    """
    Example 1: Renumber steps and automatically update all code paths.
    
    Scenario:
    - Phase has steps: 0, 1, 2
    - Renumber to: 1, 2, 3
    - Python files import from step_0_prompt, step_1_validate, step_2_execute
    - After transformation, imports updated to step_1_prompt, step_2_validate, step_3_execute
    """
    print("=" * 80)
    print("Example 1: Renumber with Code Path Updates")
    print("=" * 80)
    
    # Create a sample control flow spec
    spec = {
        'flows': {
            'example_flow': {
                'flow_id': 'example_flow',
                'name': 'Example Flow',
                'phases': [
                    {
                        'phase_id': 'processing',
                        'sequence': 1,
                        'steps': [
                            {
                                'step_id': 'prompt',
                                'sequence': 0,
                                'name': 'Prompt User',
                                'artifacts_produced': ['user_input']
                            },
                            {
                                'step_id': 'validate',
                                'sequence': 1,
                                'name': 'Validate Input',
                                'dependencies': ['prompt'],
                                'artifacts_consumed': ['user_input'],
                                'artifacts_produced': ['validated_input']
                            },
                            {
                                'step_id': 'execute',
                                'sequence': 2,
                                'name': 'Execute Action',
                                'dependencies': ['validate'],
                                'artifacts_consumed': ['validated_input'],
                                'artifacts_produced': ['result']
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    # Create transformer directly with spec (not using ControlFlowManager)
    from src.control_flow_engine.core.transformation import ControlFlowTransformation
    
    transformer = ControlFlowTransformation(spec, spec_file=None)
    
    print("\n📋 Original structure:")
    print("  phase_1_processing/")
    print("    step_0_prompt/")
    print("    step_1_validate/")
    print("    step_2_execute/")
    
    print("\n🎯 Goal: Renumber steps starting from 1")
    print("  Expected after transformation:")
    print("    step_1_prompt/")
    print("    step_2_validate/")
    print("    step_3_execute/")
    
    # Create renumber transformation
    print("\n📝 Creating renumber transformation...")
    plan = transformer.plan_renumber(
        flow_name='example_flow',
        phase_id='processing',
        start_from=1,
        strategy='compact'
    )
    
    print(f"  Created plan with {len(plan.mappings)} mappings:")
    for mapping in plan.mappings:
        print(f"    - {mapping}")
    
    # Validate
    print("\n✅ Validating transformation...")
    validation = transformer.validate(plan)
    print(f"  Valid: {validation.valid}")
    if validation.warnings:
        print(f"  Warnings: {len(validation.warnings)}")
    
    # Show what would be updated
    print("\n📝 Code paths that would be updated:")
    print("  Python imports:")
    print("    from phases.phase_1_processing.step_0_prompt import X")
    print("    → from phases.phase_1_processing.step_1_prompt import X")
    print()
    print("    from phases.phase_1_processing.step_1_validate import Y")
    print("    → from phases.phase_1_processing.step_2_validate import Y")
    print()
    print("  Config file paths:")
    print("    path: phases/phase_1_processing/step_0_prompt")
    print("    → path: phases/phase_1_processing/step_1_prompt")
    print()
    print("  Documentation:")
    print("    See [step_0_prompt](phases/phase_1_processing/step_0_prompt/README.md)")
    print("    → See [step_1_prompt](phases/phase_1_processing/step_1_prompt/README.md)")
    
    print("\n🔍 DRY RUN MODE (no changes applied)")
    print("  To apply with code path updates, use:")
    print("  transformer.apply(")
    print("      plan,")
    print("      sync_directories=True,")
    print("      update_code_paths=True,")
    print("      project_base_path=Path('/path/to/project')")
    print("  )")
    
    print("\n✅ Example 1 complete\n")


def example_2_insert_with_code_updates():
    """
    Example 2: Insert a new step and update code paths.
    
    Scenario:
    - Insert step_1.5 between step_1 and step_2
    - Step 2 becomes step 3 (cascade renumber)
    - Update all imports referencing step_2 to step_3
    """
    print("=" * 80)
    print("Example 2: Insert Step with Cascade Renumber and Code Updates")
    print("=" * 80)
    
    spec = {
        'flows': {
            'example_flow': {
                'flow_id': 'example_flow',
                'name': 'Example Flow',
                'phases': [
                    {
                        'phase_id': 'processing',
                        'sequence': 1,
                        'steps': [
                            {
                                'step_id': 'load',
                                'sequence': 1,
                                'name': 'Load Data',
                                'artifacts_produced': ['raw_data']
                            },
                            {
                                'step_id': 'process',
                                'sequence': 2,
                                'name': 'Process Data',
                                'dependencies': ['load'],
                                'artifacts_consumed': ['raw_data'],
                                'artifacts_produced': ['processed_data']
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    from src.control_flow_engine.core.transformation import ControlFlowTransformation
    transformer = ControlFlowTransformation(spec, spec_file=None)
    
    print("\n📋 Original structure:")
    print("  phase_1_processing/")
    print("    step_1_load/")
    print("    step_2_process/")
    
    print("\n🎯 Goal: Insert validation step between load and process")
    print("  Expected after transformation:")
    print("    step_1_load/")
    print("    step_2_validate/  ← NEW")
    print("    step_3_process/   ← RENUMBERED from step_2")
    
    # Create insert transformation
    print("\n📝 Creating insert transformation...")
    new_step = {
        'step_id': 'validate',
        'name': 'Validate Data',
        'dependencies': ['load'],
        'artifacts_consumed': ['raw_data'],
        'artifacts_produced': ['validated_data']
    }
    
    plan = transformer.plan_insert(
        flow_name='example_flow',
        phase_id='processing',
        new_element=new_step,
        insert_after='load',
        cascade_renumber=True
    )
    
    print(f"  Created plan with {len(plan.mappings)} mappings:")
    for mapping in plan.mappings:
        print(f"    - {mapping}")
    
    # Validate
    print("\n✅ Validating transformation...")
    validation = transformer.validate(plan)
    print(f"  Valid: {validation.valid}")
    
    # Show code path updates
    print("\n📝 Code paths that would be updated:")
    print("  Directory operations:")
    print("    CREATE: step_2_validate/")
    print("    MOVE:   step_2_process/ → step_3_process/")
    print()
    print("  Python imports (automatic updates):")
    print("    from phases.phase_1_processing.step_2_process import X")
    print("    → from phases.phase_1_processing.step_3_process import X")
    print()
    print("  Config references:")
    print("    next_step: step_2_process")
    print("    → next_step: step_3_process")
    
    print("\n🔍 DRY RUN MODE (no changes applied)")
    print("\n✅ Example 2 complete\n")


def example_3_delete_with_code_updates():
    """
    Example 3: Delete a step and update references.
    
    Scenario:
    - Delete step_2
    - Steps 3,4,5 renumber to 2,3,4
    - Update all code paths
    - Detect broken dependencies
    """
    print("=" * 80)
    print("Example 3: Delete Step with Code Path Updates")
    print("=" * 80)
    
    spec = {
        'flows': {
            'example_flow': {
                'flow_id': 'example_flow',
                'name': 'Example Flow',
                'phases': [
                    {
                        'phase_id': 'pipeline',
                        'sequence': 1,
                        'steps': [
                            {'step_id': 'fetch', 'sequence': 1},
                            {'step_id': 'transform', 'sequence': 2, 'dependencies': ['fetch']},
                            {'step_id': 'validate', 'sequence': 3, 'dependencies': ['transform']},
                            {'step_id': 'save', 'sequence': 4, 'dependencies': ['validate']}
                        ]
                    }
                ]
            }
        }
    }
    
    from src.control_flow_engine.core.transformation import ControlFlowTransformation
    transformer = ControlFlowTransformation(spec, spec_file=None)
    
    print("\n📋 Original structure:")
    print("  phase_1_pipeline/")
    print("    step_1_fetch/")
    print("    step_2_transform/")
    print("    step_3_validate/")
    print("    step_4_save/")
    
    print("\n🎯 Goal: Delete transform step")
    print("  Expected after transformation:")
    print("    step_1_fetch/")
    print("    step_2_validate/    ← RENUMBERED from step_3")
    print("    step_3_save/        ← RENUMBERED from step_4")
    
    # Create delete transformation
    print("\n📝 Creating delete transformation...")
    plan = transformer.plan_delete(
        flow_name='example_flow',
        phase_id='pipeline',
        element_id='transform',
        cascade_renumber=True
    )
    
    print(f"  Created plan with {len(plan.mappings)} mappings:")
    for mapping in plan.mappings:
        print(f"    - {mapping}")
    
    # Validate
    print("\n⚠️  Validating transformation...")
    validation = transformer.validate(plan)
    print(f"  Valid: {validation.valid}")
    
    if validation.errors:
        print(f"\n❌ Validation errors detected:")
        for error in validation.errors:
            print(f"    - {error}")
        print("\n  The validation catches that 'validate' step depends on 'transform'")
        print("  which is being deleted. This prevents broken dependencies!")
    
    if validation.warnings:
        print(f"\n⚠️  Warnings:")
        for warning in validation.warnings:
            print(f"    - {warning}")
    
    print("\n📝 If this were valid, code paths would be updated:")
    print("  Directory operations:")
    print("    DELETE: step_2_transform/")
    print("    MOVE:   step_3_validate/ → step_2_validate/")
    print("    MOVE:   step_4_save/ → step_3_save/")
    print()
    print("  Python imports (automatic updates):")
    print("    from phases.phase_1_pipeline.step_3_validate import X")
    print("    → from phases.phase_1_pipeline.step_2_validate import X")
    
    print("\n✅ Example 3 complete (blocked by validation as expected)\n")


def example_4_full_workflow():
    """
    Example 4: Complete workflow with all features enabled.
    
    Shows the full power of the transformation system:
    1. Create transformation plan
    2. Validate (catches errors)
    3. Apply to YAML
    4. Sync directories
    5. Update code paths
    6. Everything stays in sync!
    """
    print("=" * 80)
    print("Example 4: Complete Workflow (All Features)")
    print("=" * 80)
    
    print("\n🎯 Complete transformation workflow:")
    print("  1. PLAN     - Create transformation with mappings")
    print("  2. VALIDATE - Check dependencies, sequences, artifacts")
    print("  3. APPLY    - Update YAML specification")
    print("  4. SYNC     - Rename/move/create directories")
    print("  5. UPDATE   - Fix Python imports, configs, docs")
    print("  6. VERIFY   - Everything stays in sync!")
    
    print("\n📝 Example code:")
    print("```python")
    print("# Load spec")
    print("manager = ControlFlowManager(")
    print("    spec_file='control_flows.yml'")
    print(")")
    print()
    print("# Create transformation")
    print("plan = manager.create_transformation(")
    print("    'renumber',")
    print("    flow_name='main_config_flow',")
    print("    phase_id='discovery',")
    print("    start_from=1,")
    print("    strategy='compact'")
    print(")")
    print()
    print("# Validate (catches errors!)")
    print("validation = manager.validate_transformation(plan)")
    print("if not validation.valid:")
    print("    print('Errors:', validation.errors)")
    print("    return")
    print()
    print("# Apply with ALL features enabled")
    print("new_spec = manager.apply_transformation(")
    print("    plan,")
    print("    save=True,                          # Save YAML")
    print("    sync_directories=True,              # Rename directories")
    print("    update_code_paths=True,             # Update imports/paths")
    print("    project_base_path=Path.cwd()")
    print(")")
    print()
    print("# Result:")
    print("# ✅ YAML updated")
    print("# ✅ Directories renamed")
    print("# ✅ Python imports updated")
    print("# ✅ Config paths updated")
    print("# ✅ Documentation updated")
    print("# ✅ Everything in sync!")
    print("```")
    
    print("\n💡 Key Benefits:")
    print("  ✅ Safe transformations with validation")
    print("  ✅ Automatic directory synchronization")
    print("  ✅ Automatic code path updates")
    print("  ✅ Preview before applying (dry_run)")
    print("  ✅ Transformation history tracking")
    print("  ✅ Rollback support (coming soon)")
    
    print("\n✅ Example 4 complete\n")


def main():
    """Run all examples."""
    print("\n")
    print("🔄 " + "=" * 74)
    print("🔄 CODE PATH UPDATE EXAMPLES")
    print("🔄 " + "=" * 74)
    print()
    print("These examples demonstrate automatic code path updates after")
    print("directory transformations. The system updates:")
    print("  • Python import statements")
    print("  • Configuration file paths")
    print("  • Documentation references")
    print()
    
    try:
        example_1_renumber_with_code_updates()
        example_2_insert_with_code_updates()
        example_3_delete_with_code_updates()
        example_4_full_workflow()
        
        print("=" * 80)
        print("✅ All code path update examples completed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Try these transformations on a real project")
        print("  2. Use dry_run=True to preview changes")
        print("  3. Enable update_code_paths=True for automatic path updates")
        print("  4. Review the updated files to verify correctness")
        print()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
