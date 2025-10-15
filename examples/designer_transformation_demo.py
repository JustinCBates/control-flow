#!/usr/bin/env python3
"""
Demonstration of ControlFlowDesigner transformation capabilities.

This example shows how to use the designer's transformation methods
to modify control flow specifications programmatically.

Features demonstrated:
1. Renumber operations (cleanup sequence numbering)
2. Insert operations (add new phases/steps)
3. Delete operations (remove phases/steps)
4. Preview mode (see changes before applying)
5. History and rollback (undo transformations)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from control_flow_engine.core.designer import ControlFlowDesigner


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_result(result: dict):
    """Print operation result."""
    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
    print(f"\n{status}: {result['message']}")
    
    if 'preview' in result:
        print("\nPreview:")
        print(result['preview'])
    
    if 'warnings' in result and result['warnings']:
        print(f"\nWarnings: {', '.join(result['warnings'])}")
    
    if 'errors' in result:
        print(f"Errors: {', '.join(result['errors'])}")


def example_1_renumber_operations():
    """Example 1: Renumber phases and steps."""
    print_section("Example 1: Renumber Operations")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. Preview renumbering all phases starting from 0:")
    result = designer.renumber_phase(start_from=0, preview_only=True)
    print_result(result)
    
    print("\n2. Renumber all phases starting from 1 (default):")
    result = designer.renumber_phase(start_from=1)
    print_result(result)
    
    print("\n3. Renumber steps within a specific phase starting from 0:")
    result = designer.renumber_phase(
        phase_id='development',
        start_from=0,
        strategy='compact'
    )
    print_result(result)


def example_2_insert_operations():
    """Example 2: Insert new phases and steps."""
    print_section("Example 2: Insert Operations")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. Insert a new phase at the end:")
    result = designer.insert_phase({
        'phase_id': 'deployment',
        'name': 'Deployment Phase',
        'description': 'Deploy to production environment'
    })
    print_result(result)
    
    print("\n2. Insert a phase after 'development':")
    result = designer.insert_phase(
        phase_data={
            'phase_id': 'testing',
            'name': 'Testing Phase',
            'description': 'Run automated tests'
        },
        insert_after='development'
    )
    print_result(result)
    
    print("\n3. Insert a step into a phase:")
    result = designer.insert_step(
        phase_id='development',
        step_data={
            'step_id': 'code_review',
            'name': 'Code Review',
            'description': 'Review code changes',
            'handler': 'code_review_handler.py'
        },
        insert_after='unit_tests'
    )
    print_result(result)
    
    print("\n4. Preview inserting without applying:")
    result = designer.insert_step(
        phase_id='testing',
        step_data={
            'step_id': 'integration_tests',
            'name': 'Integration Tests',
            'description': 'Run integration test suite'
        },
        preview_only=True
    )
    print_result(result)


def example_3_delete_operations():
    """Example 3: Delete phases and steps."""
    print_section("Example 3: Delete Operations")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. Delete a phase:")
    result = designer.delete_phase(
        phase_id='obsolete_phase',
        cascade_renumber=True
    )
    print_result(result)
    
    print("\n2. Delete a step from a phase:")
    result = designer.delete_step(
        phase_id='development',
        step_id='deprecated_task',
        cascade_renumber=True
    )
    print_result(result)
    
    print("\n3. Preview deletion without applying:")
    result = designer.delete_phase(
        phase_id='testing',
        preview_only=True
    )
    print_result(result)


def example_4_cascade_renumber():
    """Example 4: Cascade renumbering behavior."""
    print_section("Example 4: Cascade Renumbering")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. Insert with cascade renumbering (default):")
    print("   Subsequent elements will be renumbered automatically")
    result = designer.insert_phase(
        phase_data={
            'phase_id': 'security_scan',
            'name': 'Security Scan',
            'description': 'Run security analysis'
        },
        insert_after='testing',
        cascade_renumber=True
    )
    print_result(result)
    
    print("\n2. Delete with cascade renumbering:")
    print("   Subsequent elements will shift down")
    result = designer.delete_phase(
        phase_id='security_scan',
        cascade_renumber=True
    )
    print_result(result)
    
    print("\n3. Insert without cascade renumbering:")
    print("   May create gaps in sequence numbers")
    result = designer.insert_step(
        phase_id='development',
        step_data={
            'step_id': 'static_analysis',
            'name': 'Static Analysis'
        },
        cascade_renumber=False
    )
    print_result(result)


def example_5_history_and_rollback():
    """Example 5: View history and rollback transformations."""
    print_section("Example 5: History and Rollback")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. View transformation history:")
    result = designer.get_transformation_history(limit=5)
    print_result(result)
    
    if result['success'] and result.get('history'):
        print("\nRecent transformations:")
        for i, entry in enumerate(result['history'], 1):
            print(f"  {i}. {entry.get('type', 'unknown')} - {entry.get('timestamp', 'N/A')}")
    
    print("\n2. Rollback the last transformation:")
    result = designer.rollback_transformation(steps=1)
    print_result(result)
    
    print("\n3. Preview rollback without applying:")
    result = designer.rollback_transformation(steps=2, preview_only=True)
    print_result(result)


def example_6_complex_workflow():
    """Example 6: Complex multi-operation workflow."""
    print_section("Example 6: Complex Workflow")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    print("\n1. Insert a new phase:")
    result = designer.insert_phase({
        'phase_id': 'qa',
        'name': 'Quality Assurance',
        'description': 'QA testing and validation'
    })
    print_result(result)
    
    if result['success']:
        print("\n2. Add steps to the new phase:")
        steps = [
            {
                'step_id': 'manual_testing',
                'name': 'Manual Testing',
                'description': 'Manual test execution'
            },
            {
                'step_id': 'acceptance_criteria',
                'name': 'Acceptance Criteria',
                'description': 'Verify acceptance criteria'
            }
        ]
        
        for step_data in steps:
            result = designer.insert_step(
                phase_id='qa',
                step_data=step_data
            )
            print_result(result)
    
    print("\n3. Clean up sequence numbering:")
    result = designer.renumber_phase(start_from=1, strategy='compact')
    print_result(result)


def example_7_preview_all_operations():
    """Example 7: Preview mode for all operations."""
    print_section("Example 7: Preview Mode")
    
    designer = ControlFlowDesigner(project_root='/path/to/project')
    
    operations = [
        ("Renumber", lambda: designer.renumber_phase(start_from=0, preview_only=True)),
        ("Insert Phase", lambda: designer.insert_phase(
            phase_data={'phase_id': 'preview_test', 'name': 'Preview Test'},
            preview_only=True
        )),
        ("Delete Phase", lambda: designer.delete_phase(
            phase_id='preview_test',
            preview_only=True
        )),
        ("Insert Step", lambda: designer.insert_step(
            phase_id='development',
            step_data={'step_id': 'preview_step', 'name': 'Preview Step'},
            preview_only=True
        )),
    ]
    
    for name, operation in operations:
        print(f"\n{name} Preview:")
        result = operation()
        print_result(result)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  ControlFlowDesigner Transformation Demonstrations")
    print("=" * 70)
    print("\nThese examples demonstrate the transformation API.")
    print("NOTE: Update project_root paths before running with real data.")
    print("=" * 70)
    
    # Uncomment individual examples to run:
    
    # example_1_renumber_operations()
    # example_2_insert_operations()
    # example_3_delete_operations()
    # example_4_cascade_renumber()
    # example_5_history_and_rollback()
    # example_6_complex_workflow()
    # example_7_preview_all_operations()
    
    print("\n" + "=" * 70)
    print("  Demonstrations Complete")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
