#!/usr/bin/env python3
"""
Unit tests for PhaseStepRenumberer

Tests the renumbering utility functionality including:
- Scanning current numbering
- Creating renumbering plans
- Dry-run mode
- Execution and rollback
- Various numbering strategies
"""

import pytest
import shutil
from pathlib import Path
from control_flow_engine.tools.renumberer import (
    PhaseStepRenumberer,
    NumberingStrategy,
    RenumberPlan,
    RenumberOperation,
    ValidationError,
    ExecutionError,
)


@pytest.fixture
def test_project(tmp_path):
    """Create a test project structure with phases and steps."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create phases directory
    phases_dir = project_root / "phases"
    phases_dir.mkdir()

    # Create phases 1, 2, 3, 5 (gap at 4)
    for phase_num in [1, 2, 3, 5]:
        phase_dir = phases_dir / f"phase_{phase_num}_test_phase_{phase_num}"
        phase_dir.mkdir()

        # Create __init__.py
        init_file = phase_dir / "__init__.py"
        init_file.write_text(f'"""Phase {phase_num} - Test Phase"""')

        # Create README.md
        readme = phase_dir / "README.md"
        readme.write_text(
            f"# Phase {phase_num}: Test Phase\n\nThis is phase {phase_num}."
        )

        # Create steps 1, 2, 4 (gap at 3) in phase 2
        if phase_num == 2:
            for step_num in [1, 2, 4]:
                step_dir = phase_dir / f"step_{step_num}_test_step_{step_num}"
                step_dir.mkdir()

                step_init = step_dir / "__init__.py"
                step_init.write_text(f'"""Step {step_num} - Test Step"""')

    # Create some Python files with imports
    main_py = project_root / "main.py"
    main_py.write_text(
        """
from phases.phase_2_test_phase_2 import something
from phases.phase_3_test_phase_3 import other
import phase_5_test_phase_5
"""
    )

    # Create config file
    config_yaml = project_root / "config.yaml"
    config_yaml.write_text(
        """
workflow:
  phases:
    - phase_id: phase_2_test_phase_2
      name: Test Phase 2
    - phase_id: phase_5_test_phase_5
      name: Test Phase 5
"""
    )

    return project_root


class TestNumberingScan:
    """Test scanning current phase/step numbers."""

    def test_scan_phases(self, test_project):
        """Test scanning existing phase numbers."""
        renumberer = PhaseStepRenumberer(test_project)
        numbers = renumberer._scan_current_numbering("phases")

        assert numbers == [1, 2, 3, 5]

    def test_scan_steps(self, test_project):
        """Test scanning existing step numbers."""
        renumberer = PhaseStepRenumberer(test_project)
        phase_dir = test_project / "phases" / "phase_2_test_phase_2"
        numbers = renumberer._scan_current_numbering("steps", phase_dir)

        assert numbers == [1, 2, 4]

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning with no phases."""
        project = tmp_path / "empty_project"
        project.mkdir()
        (project / "phases").mkdir()

        renumberer = PhaseStepRenumberer(project)
        numbers = renumberer._scan_current_numbering("phases")

        assert numbers == []

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning when phases directory doesn't exist."""
        project = tmp_path / "no_phases"
        project.mkdir()

        renumberer = PhaseStepRenumberer(project)
        numbers = renumberer._scan_current_numbering("phases")

        assert numbers == []


class TestPlanCreation:
    """Test creating renumbering plans."""

    def test_plan_insert_phase(self, test_project):
        """Test plan creation for phase insertion."""
        renumberer = PhaseStepRenumberer(
            test_project, strategy=NumberingStrategy.MINIMAL_SHIFT
        )

        # Insert at position 4 (should shift phase 5 → 6)
        plan = renumberer.renumber_phases(insert_at=4, dry_run=True)

        assert len(plan.operations) == 1
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 6
        assert plan.operations[0].type == "phase"

    def test_plan_remove_phase_compact(self, test_project):
        """Test plan creation for phase removal with compacting."""
        renumberer = PhaseStepRenumberer(
            test_project, strategy=NumberingStrategy.COMPACT
        )

        # Remove phase 3 (should shift phase 5 → 3)
        # Note: We're not actually removing the directory, just planning for after removal
        # In real usage, you'd remove the directory first, then renumber
        current_numbers = [1, 2, 5]  # After removing 3
        plan = renumberer._create_renumber_plan(
            current_numbers=current_numbers, insert_at=None, remove_at=3, scope="phases"
        )

        assert len(plan.operations) == 1
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 4

    def test_plan_insert_step(self, test_project):
        """Test plan creation for step insertion."""
        renumberer = PhaseStepRenumberer(test_project)

        # Insert step 3 in phase 2 (should shift step 4 → 5)
        plan = renumberer.renumber_steps(phase_number=2, insert_at=3, dry_run=True)

        assert len(plan.operations) == 1
        assert plan.operations[0].old_number == 4
        assert plan.operations[0].new_number == 5
        assert plan.operations[0].type == "step"

    def test_plan_no_changes_needed(self, test_project):
        """Test plan when no renumbering is needed."""
        renumberer = PhaseStepRenumberer(test_project)

        # Insert before position 1 (nothing to shift)
        plan = renumberer.renumber_phases(insert_at=1, dry_run=True)

        assert len(plan.operations) == 0


class TestCompactNumbering:
    """Test compacting numbering to remove gaps."""

    def test_compact_phases(self, test_project):
        """Test compacting phase numbering."""
        renumberer = PhaseStepRenumberer(test_project)

        # Phases are [1, 2, 3, 5], should become [1, 2, 3, 4]
        plan = renumberer.compact_phase_numbering(dry_run=True)

        assert len(plan.operations) == 1
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 4
        assert plan.strategy == NumberingStrategy.COMPACT

    def test_compact_already_compact(self, tmp_path):
        """Test compacting when already compact."""
        # Create project with sequential phases
        project = tmp_path / "compact_project"
        project.mkdir()
        phases_dir = project / "phases"
        phases_dir.mkdir()

        for num in [1, 2, 3, 4]:
            (phases_dir / f"phase_{num}_test").mkdir()

        renumberer = PhaseStepRenumberer(project)
        plan = renumberer.compact_phase_numbering(dry_run=True)

        assert len(plan.operations) == 0


class TestDryRun:
    """Test dry-run mode doesn't modify filesystem."""

    def test_dry_run_no_filesystem_changes(self, test_project):
        """Test dry-run doesn't modify directories."""
        renumberer = PhaseStepRenumberer(test_project)

        # Get initial state
        phases_dir = test_project / "phases"
        initial_dirs = set(d.name for d in phases_dir.iterdir())

        # Run in dry-run mode
        plan = renumberer.renumber_phases(insert_at=4, dry_run=True)

        # Verify no changes
        final_dirs = set(d.name for d in phases_dir.iterdir())
        assert initial_dirs == final_dirs

        # But plan should exist
        assert len(plan.operations) > 0

    def test_dry_run_default_behavior(self, test_project):
        """Test that dry_run=True is the default."""
        renumberer = PhaseStepRenumberer(test_project)

        phases_dir = test_project / "phases"
        initial_dirs = set(d.name for d in phases_dir.iterdir())

        # Don't specify dry_run (should default to True)
        renumberer.renumber_phases(insert_at=4)

        final_dirs = set(d.name for d in phases_dir.iterdir())
        assert initial_dirs == final_dirs


class TestExecution:
    """Test actual execution of renumbering plans."""

    def test_execute_phase_renumbering(self, test_project):
        """Test executing phase renumbering."""
        renumberer = PhaseStepRenumberer(test_project)

        # Insert at position 4 (shifts phase 5 → 6)
        plan = renumberer.renumber_phases(insert_at=4, dry_run=False)

        # Verify directory was renamed
        phases_dir = test_project / "phases"
        assert not (phases_dir / "phase_5_test_phase_5").exists()
        assert (phases_dir / "phase_6_test_phase_5").exists()

        # Verify imports were updated
        main_py = test_project / "main.py"
        content = main_py.read_text()
        assert "phase_6_test_phase_5" in content
        assert "phase_5_test_phase_5" not in content

    def test_execute_step_renumbering(self, test_project):
        """Test executing step renumbering."""
        renumberer = PhaseStepRenumberer(test_project)

        # Insert step 3 (shifts step 4 → 5)
        plan = renumberer.renumber_steps(phase_number=2, insert_at=3, dry_run=False)

        # Verify directory was renamed
        phase_dir = test_project / "phases" / "phase_2_test_phase_2"
        assert not (phase_dir / "step_4_test_step_4").exists()
        assert (phase_dir / "step_5_test_step_4").exists()

    def test_execute_compact(self, test_project):
        """Test executing compact numbering."""
        renumberer = PhaseStepRenumberer(test_project)

        # Compact phases [1,2,3,5] → [1,2,3,4]
        plan = renumberer.compact_phase_numbering(dry_run=False)

        # Verify phase 5 → phase 4
        phases_dir = test_project / "phases"
        assert not (phases_dir / "phase_5_test_phase_5").exists()
        assert (phases_dir / "phase_4_test_phase_5").exists()

        # Verify all phases are now sequential
        numbers = renumberer._scan_current_numbering("phases")
        assert numbers == [1, 2, 3, 4]


class TestValidation:
    """Test validation and error handling."""

    def test_validate_both_insert_and_remove(self, test_project):
        """Test error when both insert_at and remove_at specified."""
        renumberer = PhaseStepRenumberer(test_project)

        with pytest.raises(ValueError, match="Cannot specify both"):
            renumberer.renumber_phases(insert_at=4, remove_at=3)

    def test_validate_neither_insert_nor_remove(self, test_project):
        """Test error when neither insert_at nor remove_at specified."""
        renumberer = PhaseStepRenumberer(test_project)

        with pytest.raises(ValueError, match="Must specify either"):
            renumberer.renumber_phases()

    def test_validate_phase_not_found(self, test_project):
        """Test error when phase doesn't exist."""
        renumberer = PhaseStepRenumberer(test_project)

        with pytest.raises(ValidationError, match="Phase 99 not found"):
            renumberer.renumber_steps(phase_number=99, insert_at=1)


class TestRenumberPlan:
    """Test RenumberPlan dataclass."""

    def test_plan_string_representation(self):
        """Test plan string output."""
        op1 = RenumberOperation(
            old_number=5,
            new_number=6,
            old_path=Path("phases/phase_5_test"),
            new_path=Path("phases/phase_6_test"),
            type="phase",
        )

        plan = RenumberPlan(operations=[op1], strategy=NumberingStrategy.COMPACT)

        plan_str = str(plan)
        assert "Renumbering Plan" in plan_str
        assert "Operations: 1" in plan_str
        assert "phase_5_test → phase_6_test" in plan_str

    def test_empty_plan_string(self):
        """Test empty plan string output."""
        plan = RenumberPlan()
        assert str(plan) == "No renumbering needed"


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_single_phase_project(self, tmp_path):
        """Test renumbering with only one phase."""
        project = tmp_path / "single_phase"
        project.mkdir()
        phases_dir = project / "phases"
        phases_dir.mkdir()
        (phases_dir / "phase_1_only").mkdir()

        renumberer = PhaseStepRenumberer(project)

        # Insert at position 1 (nothing to shift)
        plan = renumberer.renumber_phases(insert_at=1, dry_run=True)
        assert len(plan.operations) == 0

        # Insert at position 2 (also nothing to shift, new phase will be 2)
        plan = renumberer.renumber_phases(insert_at=2, dry_run=True)
        assert len(plan.operations) == 0

    def test_empty_phases_directory(self, tmp_path):
        """Test renumbering with no phases."""
        project = tmp_path / "empty"
        project.mkdir()
        (project / "phases").mkdir()

        renumberer = PhaseStepRenumberer(project)
        plan = renumberer.renumber_phases(insert_at=1, dry_run=True)

        assert len(plan.operations) == 0

    def test_large_gap_in_numbering(self, tmp_path):
        """Test compacting with large gaps."""
        project = tmp_path / "gaps"
        project.mkdir()
        phases_dir = project / "phases"
        phases_dir.mkdir()

        # Create phases with large gaps: 1, 5, 10, 20
        for num in [1, 5, 10, 20]:
            (phases_dir / f"phase_{num}_test").mkdir()

        renumberer = PhaseStepRenumberer(project)
        plan = renumberer.compact_phase_numbering(dry_run=True)

        # Should compact to [1, 2, 3, 4]
        assert len(plan.operations) == 3
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 2
        assert plan.operations[1].old_number == 10
        assert plan.operations[1].new_number == 3
        assert plan.operations[2].old_number == 20
        assert plan.operations[2].new_number == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
