#!/usr/bin/env python3
"""
PhaseStepRenumberer Usage Examples

Demonstrates common use cases for the renumbering utility.
"""

import sys
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

from control_flow_engine.tools.renumberer import (
    PhaseStepRenumberer,
    NumberingStrategy
)


def example_1_preview_changes():
    """Example 1: Preview changes before applying (dry-run mode)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Preview Changes (Dry-Run)")
    print("=" * 70)
    
    # Initialize renumberer
    renumberer = PhaseStepRenumberer(
        project_root=Path("/opt/openproject"),
        strategy=NumberingStrategy.COMPACT
    )
    
    # Preview what would happen if we insert a phase at position 4
    print("\nPreview: Inserting phase at position 4")
    plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
    print(plan)
    print("\n⚠️  No changes applied (dry-run mode)")


def example_2_insert_phase():
    """Example 2: Insert a new phase and renumber subsequent phases."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Insert New Phase")
    print("=" * 70)
    
    renumberer = PhaseStepRenumberer(
        project_root=Path("/opt/openproject"),
        strategy=NumberingStrategy.MINIMAL_SHIFT
    )
    
    # Step 1: Preview
    print("\nStep 1: Preview renumbering")
    plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
    print(plan)
    
    # Step 2: User confirms, apply changes
    print("\nStep 2: Apply renumbering")
    # renumberer.renumber_phases(insert_at=4, dry_run=False)
    print("✅ (Commented out to prevent actual changes)")
    
    # Step 3: Create the new phase using ScaffoldGenerator
    print("\nStep 3: Create new phase scaffolding")
    print("from control_flow_engine.core.scaffolder import ScaffoldGenerator")
    print("scaffolder = ScaffoldGenerator(...)")
    print("scaffolder.create_phase_scaffolding(phase_def, ...)")


def example_3_compact_numbering():
    """Example 3: Compact phase numbering to remove gaps."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Compact Phase Numbering")
    print("=" * 70)
    
    renumberer = PhaseStepRenumberer(
        project_root=Path("/opt/openproject")
    )
    
    print("\nScenario: Phases are [1, 2, 3, 5] with gap at 4")
    print("Goal: Compact to [1, 2, 3, 4]")
    
    # Preview compacting
    print("\nPreview:")
    plan = renumberer.compact_phase_numbering(dry_run=True)
    print(plan)
    
    # Apply
    print("\nApplying compacting:")
    # renumberer.compact_phase_numbering(dry_run=False)
    print("✅ (Commented out to prevent actual changes)")


def example_4_insert_step():
    """Example 4: Insert a step within a phase."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Insert Step Within Phase")
    print("=" * 70)
    
    renumberer = PhaseStepRenumberer(
        project_root=Path("/opt/openproject")
    )
    
    print("\nScenario: Insert new step 3 in phase 2")
    print("Current steps: [1, 2, 4] (gap at 3)")
    print("After insertion: [1, 2, 3, 5] (new step 3, old step 4 → step 5)")
    
    # Preview
    print("\nPreview:")
    # plan = renumberer.renumber_steps(phase_number=2, insert_at=3, dry_run=True)
    # print(plan)
    print("(Would shift step_4 → step_5)")
    
    # Apply
    # renumberer.renumber_steps(phase_number=2, insert_at=3, dry_run=False)


def example_5_preserve_gaps():
    """Example 5: Use PRESERVE_GAPS strategy."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Preserve Gaps Strategy")
    print("=" * 70)
    
    renumberer = PhaseStepRenumberer(
        project_root=Path("/opt/openproject"),
        strategy=NumberingStrategy.PRESERVE_GAPS
    )
    
    print("\nScenario: Phases [1, 2, 3, 5], insert at 4")
    print("PRESERVE_GAPS: Keep phase 5 as phase 5, just insert new phase 4")
    print("Result: [1, 2, 3, 4, 5] with no renumbering needed")
    
    # Preview
    print("\nPreview:")
    plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
    print(plan)
    print("\n✨ With PRESERVE_GAPS, no existing phases need to be renumbered!")


def example_6_workflow():
    """Example 6: Complete workflow for inserting a phase."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete Insertion Workflow")
    print("=" * 70)
    
    print("""
Complete workflow for inserting a new phase:

Step 1: Preview renumbering
--------------------------
from control_flow_engine.tools.renumberer import PhaseStepRenumberer

renumberer = PhaseStepRenumberer(project_root)
plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
print(plan)  # Review what will change

Step 2: Apply renumbering
--------------------------
# After reviewing the plan, apply it
renumberer.renumber_phases(insert_at=4, dry_run=False)

Step 3: Create new phase scaffolding
-----------------------------------
from control_flow_engine.core.scaffolder import ScaffoldGenerator, PhaseInsertion

scaffolder = ScaffoldGenerator(project_root)
phase_def = PhaseInsertion(
    phase_id="phase_4_testing",
    name="Testing & Validation",
    sequence=4,
    description="Comprehensive testing phase"
)
scaffolder.create_phase_scaffolding(phase_def, Path("phases"))

Step 4: Verify
--------------
# Renumberer automatically:
# - Renamed phase directories
# - Updated Python imports
# - Updated YAML configs
# - Updated Markdown docs
# 
# Manual steps:
# - Review generated code
# - Update any custom references
# - Commit changes to Git
    """)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PhaseStepRenumberer Usage Examples")
    print("=" * 70)
    
    examples = [
        example_1_preview_changes,
        example_2_insert_phase,
        example_3_compact_numbering,
        example_4_insert_step,
        example_5_preserve_gaps,
        example_6_workflow,
    ]
    
    for example in examples:
        example()
    
    print("\n" + "=" * 70)
    print("For complete API documentation, see RENUMBERING_SPEC.md")
    print("=" * 70)


if __name__ == '__main__':
    main()
