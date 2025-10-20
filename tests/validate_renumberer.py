#!/usr/bin/env python3
"""
Simple validation script for PhaseStepRenumberer
Tests basic functionality without pytest dependency
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from control_flow_engine.tools.renumberer import (
    PhaseStepRenumberer,
    NumberingStrategy,
    RenumberPlan,
)


def create_test_project(root: Path):
    """Create a test project structure."""
    phases_dir = root / "phases"
    phases_dir.mkdir()

    # Create phases 1, 2, 3, 5 (gap at 4)
    for phase_num in [1, 2, 3, 5]:
        phase_dir = phases_dir / f"phase_{phase_num}_test_phase"
        phase_dir.mkdir()

        init_file = phase_dir / "__init__.py"
        init_file.write_text(f'"""Phase {phase_num}"""')

        readme = phase_dir / "README.md"
        readme.write_text(f"# Phase {phase_num}: Test\n")

    # Create main.py with imports
    main_py = root / "main.py"
    main_py.write_text(
        """
from phases.phase_2_test_phase import something
from phases.phase_5_test_phase import other
"""
    )

    return root


def test_scan_numbering():
    """Test 1: Scan current phase numbers."""
    print("\n" + "=" * 70)
    print("TEST 1: Scan Current Numbering")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        project = create_test_project(Path(tmpdir))
        renumberer = PhaseStepRenumberer(project)

        numbers = renumberer._scan_current_numbering("phases")
        print(f"✓ Found phases: {numbers}")

        assert numbers == [1, 2, 3, 5], f"Expected [1,2,3,5], got {numbers}"
        print("✅ PASS: Correctly scanned phase numbers")


def test_dry_run():
    """Test 2: Dry-run mode doesn't modify filesystem."""
    print("\n" + "=" * 70)
    print("TEST 2: Dry-Run Mode")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        project = create_test_project(Path(tmpdir))
        renumberer = PhaseStepRenumberer(project)

        phases_dir = project / "phases"
        initial_dirs = set(d.name for d in phases_dir.iterdir())
        print(f"Initial directories: {sorted(initial_dirs)}")

        # Run dry-run
        plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
        print(f"\n{plan}")

        final_dirs = set(d.name for d in phases_dir.iterdir())

        assert initial_dirs == final_dirs, "Dry-run modified filesystem!"
        assert (
            len(plan.operations) == 1
        ), f"Expected 1 operation, got {len(plan.operations)}"
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 6

        print("✅ PASS: Dry-run didn't modify filesystem, plan created correctly")


def test_insert_execution():
    """Test 3: Execute phase insertion."""
    print("\n" + "=" * 70)
    print("TEST 3: Execute Phase Insertion")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        project = create_test_project(Path(tmpdir))
        renumberer = PhaseStepRenumberer(project)

        print("Inserting phase at position 4 (shifts phase 5 → 6)...")
        plan = renumberer.renumber_phases(insert_at=4, dry_run=False)

        phases_dir = project / "phases"

        # Verify directory renamed
        assert not (
            phases_dir / "phase_5_test_phase"
        ).exists(), "Old directory still exists"
        assert (phases_dir / "phase_6_test_phase").exists(), "New directory not created"

        # Verify imports updated
        main_py = project / "main.py"
        content = main_py.read_text()
        assert "phase_6_test_phase" in content, "Import not updated"
        assert "phase_5_test_phase" not in content, "Old import still present"

        print("✅ PASS: Phase renumbering executed successfully")


def test_compact():
    """Test 4: Compact phase numbering."""
    print("\n" + "=" * 70)
    print("TEST 4: Compact Phase Numbering")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        project = create_test_project(Path(tmpdir))
        renumberer = PhaseStepRenumberer(project)

        print("Compacting phases [1,2,3,5] → [1,2,3,4]...")
        plan = renumberer.compact_phase_numbering(dry_run=False)

        phases_dir = project / "phases"

        # Verify phase 5 → phase 4
        assert not (phases_dir / "phase_5_test_phase").exists()
        assert (phases_dir / "phase_4_test_phase").exists()

        # Verify sequential numbering
        numbers = renumberer._scan_current_numbering("phases")
        assert numbers == [1, 2, 3, 4], f"Expected [1,2,3,4], got {numbers}"

        print("✅ PASS: Phase numbering compacted successfully")


def test_preserve_gaps_strategy():
    """Test 5: Preserve gaps strategy."""
    print("\n" + "=" * 70)
    print("TEST 5: Preserve Gaps Strategy")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        project = create_test_project(Path(tmpdir))
        renumberer = PhaseStepRenumberer(
            project, strategy=NumberingStrategy.PRESERVE_GAPS
        )

        print("Inserting at position 4 with PRESERVE_GAPS strategy...")
        plan = renumberer.renumber_phases(insert_at=4, dry_run=True)

        # Should shift phase 5 → 6, keeping the gap
        assert len(plan.operations) == 1
        assert plan.operations[0].old_number == 5
        assert plan.operations[0].new_number == 6

        print("✅ PASS: Preserve gaps strategy works correctly")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PhaseStepRenumberer Validation Tests")
    print("=" * 70)

    tests = [
        test_scan_numbering,
        test_dry_run,
        test_insert_execution,
        test_compact,
        test_preserve_gaps_strategy,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
