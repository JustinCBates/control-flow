#!/usr/bin/env python3
"""
Integration Tests for Control Flow Designer Transformation System

Tests all transformation operations through both programmatic API and
validates the complete workflow: YAML → Directories → Code → Orchestrators

Test Categories:
1. API Tests - Test ControlFlowDesigner methods
2. Workflow Tests - Verify full transformation pipeline
3. Edge Case Tests - Boundary conditions and error handling
4. Rollback Tests - Verify undo functionality
5. Integration Tests - Real-world scenarios
"""

import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from control_flow_engine.core.designer import ControlFlowDesigner
from control_flow_engine.core.engine import ControlFlowManager


class TestHarness:
    """Test harness for transformation system integration tests."""

    def __init__(self):
        """Initialize test harness."""
        self.test_dir = None
        self.designer = None
        self.manager = None
        self.results = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}

    def setup_test_environment(self):
        """Create a test environment with sample control flow."""
        print("\n" + "=" * 70)
        print("  Setting Up Test Environment")
        print("=" * 70)

        # Create temp directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="cf_test_"))
        print(f"📁 Test directory: {self.test_dir}")

        # Create sample YAML specification
        spec_dir = self.test_dir / "control"
        spec_dir.mkdir(parents=True)

        sample_spec = {
            "version": "1.0",
            "flows": {
                "test_flow": {
                    "name": "Test Flow",
                    "phases": [
                        {
                            "phase_id": "init",
                            "name": "Initialization",
                            "sequence": 0,
                            "steps": [
                                {"step_id": "setup", "name": "Setup", "sequence": 0},
                                {
                                    "step_id": "validate",
                                    "name": "Validate",
                                    "sequence": 5,
                                },
                            ],
                        },
                        {
                            "phase_id": "process",
                            "name": "Processing",
                            "sequence": 10,
                            "steps": [
                                {
                                    "step_id": "transform",
                                    "name": "Transform",
                                    "sequence": 0,
                                }
                            ],
                        },
                        {
                            "phase_id": "cleanup",
                            "name": "Cleanup",
                            "sequence": 30,
                            "steps": [],
                        },
                    ],
                }
            },
        }

        spec_file = spec_dir / "test_flow.yaml"
        with open(spec_file, "w") as f:
            import yaml

            yaml.dump(sample_spec, f, default_flow_style=False)

        print(f"✅ Created test specification: {spec_file}")

        # Initialize designer and manager
        self.designer = ControlFlowDesigner(project_root=str(self.test_dir))
        self.manager = ControlFlowManager(project_root=str(self.test_dir))

        print("✅ Designer and Manager initialized")
        print("=" * 70)

        return True

    def teardown_test_environment(self):
        """Clean up test environment."""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"\n🧹 Cleaned up test directory: {self.test_dir}")

    def assert_true(self, condition: bool, message: str) -> bool:
        """Assert a condition is true."""
        if condition:
            self.results["passed"] += 1
            print(f"  ✅ {message}")
            return True
        else:
            self.results["failed"] += 1
            self.results["errors"].append(message)
            print(f"  ❌ {message}")
            return False

    def assert_success(self, result: Dict[str, Any], operation: str) -> bool:
        """Assert an operation succeeded."""
        success = result.get("success", False)
        if success:
            self.results["passed"] += 1
            print(f"  ✅ {operation}: {result.get('message', 'OK')}")
            return True
        else:
            self.results["failed"] += 1
            error_msg = f"{operation} failed: {result.get('message', 'Unknown error')}"
            self.results["errors"].append(error_msg)
            print(f"  ❌ {error_msg}")
            return False

    def print_section(self, title: str):
        """Print a test section header."""
        print(f"\n{'─' * 70}")
        print(f"  {title}")
        print("─" * 70)

    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 70)
        print("  Control Flow Designer - Integration Test Suite")
        print("=" * 70)

        try:
            # Setup
            if not self.setup_test_environment():
                print("❌ Failed to setup test environment")
                return False

            # Run test suites
            self.test_api_renumber()
            self.test_api_insert()
            self.test_api_delete()
            self.test_preview_mode()
            self.test_cascade_renumber()
            self.test_history_and_rollback()
            self.test_edge_cases()
            self.test_workflow_integration()
            self.test_real_world_scenarios()

            # Print results
            self.print_results()

        except Exception as e:
            print(f"\n❌ Test suite error: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.teardown_test_environment()

        return self.results["failed"] == 0

    def test_api_renumber(self):
        """Test renumber operations."""
        self.print_section("Test Suite: Renumber API")

        # Test 1: Renumber all phases starting from 1
        result = self.designer.renumber_phase(start_from=1, strategy="compact")
        self.assert_success(result, "Renumber all phases from 1")

        # Verify sequences
        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        sequences = [p["sequence"] for p in phases]
        self.assert_true(
            sequences == [1, 2, 3], f"Phases renumbered correctly: {sequences}"
        )

        # Test 2: Renumber all phases starting from 0
        result = self.designer.renumber_phase(start_from=0, strategy="compact")
        self.assert_success(result, "Renumber all phases from 0")

        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        sequences = [p["sequence"] for p in phases]
        self.assert_true(
            sequences == [0, 1, 2], f"Phases renumbered from 0: {sequences}"
        )

        # Test 3: Renumber steps in specific phase
        result = self.designer.renumber_phase(
            phase_id="init", start_from=1, strategy="compact"
        )
        self.assert_success(result, "Renumber steps in 'init' phase")

        spec = self.manager.get_specification()
        init_phase = next(
            p for p in spec["flows"]["test_flow"]["phases"] if p["phase_id"] == "init"
        )
        step_sequences = [s["sequence"] for s in init_phase["steps"]]
        self.assert_true(
            step_sequences == [1, 2], f"Steps renumbered: {step_sequences}"
        )

    def test_api_insert(self):
        """Test insert operations."""
        self.print_section("Test Suite: Insert API")

        # Test 1: Insert phase at end
        phase_data = {
            "phase_id": "finalize",
            "name": "Finalization",
            "description": "Final phase",
        }
        result = self.designer.insert_phase(
            phase_data=phase_data, cascade_renumber=True
        )
        self.assert_success(result, "Insert phase at end")

        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        phase_ids = [p["phase_id"] for p in phases]
        self.assert_true("finalize" in phase_ids, f"Phase inserted: {phase_ids}")

        # Test 2: Insert phase after specific phase
        phase_data = {"phase_id": "validate_phase", "name": "Validation"}
        result = self.designer.insert_phase(
            phase_data=phase_data, insert_after="init", cascade_renumber=True
        )
        self.assert_success(result, "Insert phase after 'init'")

        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        phase_ids = [p["phase_id"] for p in phases]
        init_idx = phase_ids.index("init")
        validate_idx = phase_ids.index("validate_phase")
        self.assert_true(
            validate_idx == init_idx + 1, f"Phase inserted after init: {phase_ids}"
        )

        # Test 3: Insert step into phase
        step_data = {"step_id": "pre_check", "name": "Pre-Check"}
        result = self.designer.insert_step(
            phase_id="init",
            step_data=step_data,
            insert_after="setup",
            cascade_renumber=True,
        )
        self.assert_success(result, "Insert step after 'setup'")

        spec = self.manager.get_specification()
        init_phase = next(
            p for p in spec["flows"]["test_flow"]["phases"] if p["phase_id"] == "init"
        )
        step_ids = [s["step_id"] for s in init_phase["steps"]]
        self.assert_true("pre_check" in step_ids, f"Step inserted: {step_ids}")

    def test_api_delete(self):
        """Test delete operations."""
        self.print_section("Test Suite: Delete API")

        # Test 1: Delete a step
        result = self.designer.delete_step(
            phase_id="init", step_id="pre_check", cascade_renumber=True
        )
        self.assert_success(result, "Delete step 'pre_check'")

        spec = self.manager.get_specification()
        init_phase = next(
            p for p in spec["flows"]["test_flow"]["phases"] if p["phase_id"] == "init"
        )
        step_ids = [s["step_id"] for s in init_phase["steps"]]
        self.assert_true("pre_check" not in step_ids, f"Step deleted: {step_ids}")

        # Test 2: Delete a phase
        result = self.designer.delete_phase(
            phase_id="validate_phase", cascade_renumber=True
        )
        self.assert_success(result, "Delete phase 'validate_phase'")

        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        phase_ids = [p["phase_id"] for p in phases]
        self.assert_true(
            "validate_phase" not in phase_ids, f"Phase deleted: {phase_ids}"
        )

    def test_preview_mode(self):
        """Test preview mode for all operations."""
        self.print_section("Test Suite: Preview Mode")

        # Test 1: Preview renumber
        result = self.designer.renumber_phase(start_from=1, preview_only=True)
        self.assert_success(result, "Preview renumber")
        self.assert_true("preview" in result, "Preview text included in result")

        # Test 2: Preview insert
        phase_data = {"phase_id": "preview_test", "name": "Preview Test"}
        result = self.designer.insert_phase(phase_data=phase_data, preview_only=True)
        self.assert_success(result, "Preview insert phase")

        # Verify phase not actually inserted
        spec = self.manager.get_specification()
        phase_ids = [p["phase_id"] for p in spec["flows"]["test_flow"]["phases"]]
        self.assert_true(
            "preview_test" not in phase_ids, "Phase not inserted (preview only)"
        )

        # Test 3: Preview delete
        result = self.designer.delete_phase(phase_id="cleanup", preview_only=True)
        self.assert_success(result, "Preview delete phase")

        # Verify phase still exists
        spec = self.manager.get_specification()
        phase_ids = [p["phase_id"] for p in spec["flows"]["test_flow"]["phases"]]
        self.assert_true("cleanup" in phase_ids, "Phase still exists (preview only)")

    def test_cascade_renumber(self):
        """Test cascade renumbering behavior."""
        self.print_section("Test Suite: Cascade Renumbering")

        # Insert with cascade
        phase_data = {"phase_id": "cascade_test", "name": "Cascade Test"}
        result = self.designer.insert_phase(
            phase_data=phase_data, insert_after="init", cascade_renumber=True
        )
        self.assert_success(result, "Insert with cascade renumber")

        # Verify sequences are contiguous
        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        sequences = sorted([p["sequence"] for p in phases])
        expected = list(range(len(sequences)))
        self.assert_true(sequences == expected, f"Sequences contiguous: {sequences}")

        # Delete without cascade (if implemented) - for now all deletes cascade
        # This verifies cascade works correctly

    def test_history_and_rollback(self):
        """Test transformation history and rollback."""
        self.print_section("Test Suite: History and Rollback")

        # Get initial phase count
        spec = self.manager.get_specification()
        initial_phase_count = len(spec["flows"]["test_flow"]["phases"])

        # Perform operation
        phase_data = {"phase_id": "rollback_test", "name": "Rollback Test"}
        result = self.designer.insert_phase(phase_data=phase_data)
        self.assert_success(result, "Insert phase for rollback test")

        # Check history
        result = self.designer.get_transformation_history(limit=5)
        self.assert_success(result, "Get transformation history")
        self.assert_true(len(result.get("history", [])) > 0, "History contains entries")

        # Rollback
        result = self.designer.rollback_transformation(steps=1)
        self.assert_success(result, "Rollback last transformation")

        # Verify rollback worked
        spec = self.manager.get_specification()
        final_phase_count = len(spec["flows"]["test_flow"]["phases"])
        self.assert_true(
            final_phase_count == initial_phase_count,
            f"Phase count restored: {initial_phase_count} == {final_phase_count}",
        )

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        self.print_section("Test Suite: Edge Cases")

        # Test 1: Insert with invalid phase_id (empty)
        result = self.designer.insert_phase(phase_data={})
        self.assert_true(not result["success"], "Empty phase_data rejected")

        # Test 2: Delete non-existent phase
        result = self.designer.delete_phase(phase_id="nonexistent")
        self.assert_true(not result["success"], "Non-existent phase deletion rejected")

        # Test 3: Delete non-existent step
        result = self.designer.delete_step(phase_id="init", step_id="nonexistent")
        self.assert_true(not result["success"], "Non-existent step deletion rejected")

        # Test 4: Insert step with invalid phase
        step_data = {"step_id": "test_step", "name": "Test"}
        result = self.designer.insert_step(
            phase_id="nonexistent_phase", step_data=step_data
        )
        self.assert_true(
            not result["success"], "Insert into non-existent phase rejected"
        )

    def test_workflow_integration(self):
        """Test full workflow: YAML → Directories → Code → Orchestrators."""
        self.print_section("Test Suite: Workflow Integration")

        # Note: Full workflow requires actual project structure
        # Here we test that operations complete without errors

        # Test 1: Operation completes full workflow
        phase_data = {"phase_id": "workflow_test", "name": "Workflow Test"}
        result = self.designer.insert_phase(phase_data=phase_data)
        self.assert_success(result, "Insert phase (full workflow)")

        # Test 2: YAML updated
        spec = self.manager.get_specification()
        phase_ids = [p["phase_id"] for p in spec["flows"]["test_flow"]["phases"]]
        self.assert_true("workflow_test" in phase_ids, "YAML specification updated")

        # Test 3: Subsequent operations work
        result = self.designer.renumber_phase(start_from=0)
        self.assert_success(result, "Renumber after insert (workflow validation)")

    def test_real_world_scenarios(self):
        """Test realistic usage scenarios."""
        self.print_section("Test Suite: Real-World Scenarios")

        # Scenario 1: Reorganize flow structure
        print("\n  Scenario: Reorganize flow structure")

        # Add new phase
        result = self.designer.insert_phase(
            phase_data={"phase_id": "validation", "name": "Validation"},
            insert_after="init",
        )
        self.assert_success(result, "Add validation phase")

        # Add steps to new phase
        for step_id, step_name in [
            ("check_input", "Check Input"),
            ("verify", "Verify"),
        ]:
            result = self.designer.insert_step(
                phase_id="validation", step_data={"step_id": step_id, "name": step_name}
            )
            self.assert_success(result, f"Add step '{step_id}'")

        # Renumber everything
        result = self.designer.renumber_phase(start_from=1)
        self.assert_success(result, "Renumber all phases")

        # Verify final structure
        spec = self.manager.get_specification()
        phases = spec["flows"]["test_flow"]["phases"]
        self.assert_true(len(phases) >= 4, f"Flow has multiple phases: {len(phases)}")

        validation_phase = next(
            (p for p in phases if p["phase_id"] == "validation"), None
        )
        if validation_phase:
            self.assert_true(
                len(validation_phase["steps"]) == 2,
                f"Validation phase has 2 steps: {len(validation_phase['steps'])}",
            )

    def print_results(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("  Test Results Summary")
        print("=" * 70)

        total = (
            self.results["passed"] + self.results["failed"] + self.results["skipped"]
        )
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        print(f"\n  Total Tests:  {total}")
        print(f"  ✅ Passed:    {self.results['passed']}")
        print(f"  ❌ Failed:    {self.results['failed']}")
        print(f"  ⏭️  Skipped:   {self.results['skipped']}")
        print(f"  📊 Pass Rate: {pass_rate:.1f}%")

        if self.results["errors"]:
            print("\n  Errors:")
            for i, error in enumerate(self.results["errors"], 1):
                print(f"    {i}. {error}")

        print("\n" + "=" * 70)

        if self.results["failed"] == 0:
            print("  🎉 ALL TESTS PASSED!")
        else:
            print("  ⚠️  SOME TESTS FAILED")

        print("=" * 70 + "\n")


def main():
    """Run the test suite."""
    harness = TestHarness()
    success = harness.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
