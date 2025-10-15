#!/usr/bin/env python3
"""
Example demonstrating transformation history persistence.

This example shows how the transformation system automatically tracks
all transformations in a .transformation_history.json file, enabling:
1. Audit trail of all changes
2. Change tracking with timestamps
3. Rollback support (Todo #4)
4. Debugging and analysis
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.control_flow_engine.core.transformation import (
    ControlFlowTransformation,
    TransformationHistory
)


def example_1_basic_history():
    """
    Example 1: Basic history tracking.
    
    Shows how transformations are automatically recorded in history.
    """
    print("=" * 80)
    print("Example 1: Basic History Tracking")
    print("=" * 80)
    
    # Create a sample spec
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
                            {'step_id': 'load', 'sequence': 0},
                            {'step_id': 'validate', 'sequence': 1},
                            {'step_id': 'process', 'sequence': 2}
                        ]
                    }
                ]
            }
        }
    }
    
    # Create transformer with a spec file path
    spec_file = Path('/tmp/test_control_flows.yml')
    transformer = ControlFlowTransformation(spec, spec_file=spec_file)
    
    print("\n📋 Transformer initialized")
    print(f"  History file: {transformer.history_manager.history_file}")
    
    # Create and apply a transformation
    print("\n📝 Creating renumber transformation...")
    plan = transformer.plan_renumber(
        flow_name='example_flow',
        phase_id='processing',
        start_from=1,
        strategy='compact'
    )
    
    # Validate
    validation = transformer.validate(plan)
    print(f"  Valid: {validation.valid}")
    
    # Apply (without actually saving to avoid cluttering filesystem)
    print("\n✅ Applying transformation...")
    new_spec = transformer.apply(
        plan,
        save=False,  # Don't save to avoid creating files
        sync_directories=False,
        update_code_paths=False
    )
    
    print("\n📜 History recorded!")
    print(f"  Total transformations in history: {len(transformer.history_manager.history['transformations'])}")
    
    # Get history summary
    print("\n" + transformer.show_history_summary())
    
    # Get last transformation
    last = transformer.history_manager.get_last_transformation()
    if last:
        print("\n📖 Last transformation details:")
        print(f"  Timestamp: {last['timestamp']}")
        print(f"  Type: {last['transformation_type']}")
        print(f"  Flow: {last['flow_name']}")
        print(f"  Description: {last['description']}")
        print(f"  Mappings: {len(last['mappings'])}")
        print(f"  Can rollback: {last['can_rollback']}")
    
    print("\n✅ Example 1 complete\n")


def example_2_multiple_transformations():
    """
    Example 2: Track multiple transformations.
    
    Shows history accumulation over multiple operations.
    """
    print("=" * 80)
    print("Example 2: Multiple Transformations")
    print("=" * 80)
    
    spec = {
        'flows': {
            'data_pipeline': {
                'flow_id': 'data_pipeline',
                'name': 'Data Pipeline',
                'phases': [
                    {
                        'phase_id': 'ingestion',
                        'sequence': 1,
                        'steps': [
                            {'step_id': 'fetch', 'sequence': 0},
                            {'step_id': 'parse', 'sequence': 1}
                        ]
                    }
                ]
            }
        }
    }
    
    spec_file = Path('/tmp/test_pipeline.yml')
    transformer = ControlFlowTransformation(spec, spec_file=spec_file)
    
    print("\n🔄 Applying multiple transformations...")
    
    # Transformation 1: Renumber
    print("\n1. Renumbering steps...")
    plan1 = transformer.plan_renumber('data_pipeline', 'ingestion', start_from=1)
    transformer.validate(plan1)
    transformer.apply(plan1, save=False, sync_directories=False)
    print("  ✅ Renumber complete")
    
    # Transformation 2: Insert
    print("\n2. Inserting validation step...")
    new_step = {
        'step_id': 'validate',
        'name': 'Validate Data',
        'dependencies': ['parse']
    }
    plan2 = transformer.plan_insert(
        'data_pipeline',
        'ingestion',
        new_step,
        insert_after='parse',
        cascade_renumber=True
    )
    transformer.validate(plan2)
    transformer.apply(plan2, save=False, sync_directories=False)
    print("  ✅ Insert complete")
    
    # Show history
    print("\n📜 Transformation history:")
    history = transformer.get_persistent_history()
    
    for i, entry in enumerate(history, 1):
        print(f"\n{i}. {entry['transformation_type'].upper()}")
        print(f"   Time: {entry['timestamp']}")
        print(f"   Flow: {entry['flow_name']}")
        print(f"   Desc: {entry['description']}")
        print(f"   Mappings: {len(entry['mappings'])}")
    
    print(f"\n✅ Total transformations: {len(history)}")
    print("\n✅ Example 2 complete\n")


def example_3_history_file_format():
    """
    Example 3: Inspect history file format.
    
    Shows the structure of .transformation_history.json.
    """
    print("=" * 80)
    print("Example 3: History File Format")
    print("=" * 80)
    
    spec = {
        'flows': {
            'test_flow': {
                'flow_id': 'test_flow',
                'phases': [
                    {
                        'phase_id': 'test_phase',
                        'sequence': 1,
                        'steps': [
                            {'step_id': 'step_a', 'sequence': 1},
                            {'step_id': 'step_b', 'sequence': 2}
                        ]
                    }
                ]
            }
        }
    }
    
    spec_file = Path('/tmp/test_format.yml')
    transformer = ControlFlowTransformation(spec, spec_file=spec_file)
    
    # Apply a transformation
    plan = transformer.plan_renumber('test_flow', 'test_phase', start_from=10)
    transformer.validate(plan)
    transformer.apply(plan, save=False, sync_directories=False)
    
    # Show file contents
    history_file = transformer.history_manager.history_file
    print(f"\n📄 History file: {history_file}")
    
    if history_file.exists():
        print("\n📖 File contents:")
        print("-" * 60)
        
        with open(history_file, 'r') as f:
            content = json.load(f)
        
        # Pretty print with limited detail
        print(f"Version: {content.get('version')}")
        print(f"Created: {content.get('created_at')}")
        print(f"Transformations: {len(content.get('transformations', []))}")
        
        if content.get('transformations'):
            print("\nFirst transformation:")
            entry = content['transformations'][0]
            print(json.dumps(entry, indent=2, default=str)[:500] + "...")
        
        print("-" * 60)
    
    print("\n✅ Example 3 complete\n")


def example_4_rollback_check():
    """
    Example 4: Check rollback capability.
    
    Shows how to check if transformations can be rolled back.
    """
    print("=" * 80)
    print("Example 4: Rollback Capability Check")
    print("=" * 80)
    
    spec = {
        'flows': {
            'rollback_test': {
                'flow_id': 'rollback_test',
                'phases': [
                    {
                        'phase_id': 'phase1',
                        'sequence': 1,
                        'steps': [
                            {'step_id': 'a', 'sequence': 1},
                            {'step_id': 'b', 'sequence': 2},
                            {'step_id': 'c', 'sequence': 3}
                        ]
                    }
                ]
            }
        }
    }
    
    spec_file = Path('/tmp/test_rollback.yml')
    transformer = ControlFlowTransformation(spec, spec_file=spec_file)
    
    # Apply multiple transformations
    print("\n🔄 Applying 3 transformations...")
    
    for i in range(3):
        plan = transformer.plan_renumber(
            'rollback_test',
            'phase1',
            start_from=1 + i
        )
        transformer.validate(plan)
        transformer.apply(plan, save=False, sync_directories=False)
        print(f"  ✅ Transformation {i+1} complete")
    
    # Check rollback capability
    print("\n🔍 Checking rollback capability...")
    
    for steps in [1, 2, 3, 5]:
        can_rollback, reason = transformer.can_rollback(steps)
        
        if can_rollback:
            print(f"  ✅ Can rollback {steps} step(s)")
        else:
            print(f"  ❌ Cannot rollback {steps} step(s): {reason}")
    
    # Show what would be rolled back
    history = transformer.get_persistent_history(limit=3)
    print(f"\n📜 Last 3 transformations (would be rolled back):")
    for i, entry in enumerate(history, 1):
        print(f"  {i}. {entry['transformation_type']} - {entry['description']}")
    
    print("\n💡 Note: Actual rollback implementation coming in Todo #4")
    print("\n✅ Example 4 complete\n")


def example_5_history_export():
    """
    Example 5: Export and backup history.
    
    Shows how to export history for backup or analysis.
    """
    print("=" * 80)
    print("Example 5: History Export and Backup")
    print("=" * 80)
    
    spec = {
        'flows': {
            'export_test': {
                'flow_id': 'export_test',
                'phases': [
                    {'phase_id': 'p1', 'sequence': 1, 'steps': [
                        {'step_id': 's1', 'sequence': 1}
                    ]}
                ]
            }
        }
    }
    
    spec_file = Path('/tmp/test_export.yml')
    transformer = ControlFlowTransformation(spec, spec_file=spec_file)
    
    # Apply some transformations
    print("\n🔄 Creating transformation history...")
    plan = transformer.plan_renumber('export_test', 'p1', start_from=10)
    transformer.validate(plan)
    transformer.apply(plan, save=False, sync_directories=False)
    
    # Export history
    export_file = Path('/tmp/transformation_history_backup.json')
    print(f"\n💾 Exporting history to: {export_file}")
    
    transformer.history_manager.export_history(export_file)
    
    if export_file.exists():
        size = export_file.stat().st_size
        print(f"  ✅ Export successful ({size} bytes)")
        
        # Show it's a valid JSON file
        with open(export_file, 'r') as f:
            backup = json.load(f)
        print(f"  ✅ Valid JSON with {len(backup['transformations'])} transformation(s)")
    
    print("\n💡 Use cases for exported history:")
    print("  • Backup before major changes")
    print("  • Share transformation history with team")
    print("  • Audit trail for compliance")
    print("  • Analysis and debugging")
    
    print("\n✅ Example 5 complete\n")


def cleanup():
    """Clean up temporary test files."""
    test_files = [
        '/tmp/test_control_flows.yml',
        '/tmp/test_pipeline.yml',
        '/tmp/test_format.yml',
        '/tmp/test_rollback.yml',
        '/tmp/test_export.yml',
        '/tmp/.transformation_history.json',
        '/tmp/transformation_history_backup.json'
    ]
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            path.unlink()


def main():
    """Run all examples."""
    print("\n")
    print("🔄 " + "=" * 74)
    print("🔄 TRANSFORMATION HISTORY EXAMPLES")
    print("🔄 " + "=" * 74)
    print()
    print("These examples demonstrate automatic transformation history tracking.")
    print("All transformations are saved to .transformation_history.json with:")
    print("  • Timestamps")
    print("  • Complete mappings")
    print("  • File checksums")
    print("  • Rollback capability info")
    print()
    
    try:
        example_1_basic_history()
        example_2_multiple_transformations()
        example_3_history_file_format()
        example_4_rollback_check()
        example_5_history_export()
        
        print("=" * 80)
        print("✅ All transformation history examples completed successfully!")
        print("=" * 80)
        print()
        print("Key features demonstrated:")
        print("  ✅ Automatic history tracking")
        print("  ✅ Persistent .transformation_history.json file")
        print("  ✅ Timestamps and metadata")
        print("  ✅ Rollback capability checking")
        print("  ✅ History export and backup")
        print()
        print("Next steps:")
        print("  • History is now tracked automatically")
        print("  • Use show_history_summary() to view history")
        print("  • Rollback implementation coming in Todo #4")
        print()
        
        # Cleanup
        cleanup()
        print("🧹 Cleaned up temporary test files")
        print()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
