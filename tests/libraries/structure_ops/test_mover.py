"""
Unit tests for StructureMover.

Tests move operations with cascade renumbering.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from control_flow_engine.libraries.structure_ops import (
    StructureMover,
    MoveOperation,
    MoveResult,
    MoveDirection,
)


class TestStructureMover:
    """Test cases for StructureMover."""

    def test_move_up_basic(self):
        """Test moving element up in sequence."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
                {"id": "item4", "sequence": 4},
            ]
        }

        mover = StructureMover()
        operation = MoveOperation(from_sequence=3, to_sequence=1, element_path="items")

        result = mover.move_element(structure, operation)

        assert result.success
        assert result.direction == MoveDirection.UP
        assert len(result.mappings) == 4

        # Verify final sequences in modified structure
        items = result.modified_structure["items"]
        item_by_id = {item["id"]: item["sequence"] for item in items}

        assert item_by_id["item3"] == 1  # Moved element
        assert item_by_id["item1"] == 2  # Shifted down
        assert item_by_id["item2"] == 3  # Shifted down
        assert item_by_id["item4"] == 4  # Unchanged

    def test_move_down_basic(self):
        """Test moving element down in sequence."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
                {"id": "item4", "sequence": 4},
            ]
        }

        mover = StructureMover()
        operation = MoveOperation(from_sequence=2, to_sequence=4, element_path="items")

        result = mover.move_element(structure, operation)

        assert result.success
        assert result.direction == MoveDirection.DOWN

        items = result.modified_structure["items"]
        item_by_id = {item["id"]: item["sequence"] for item in items}

        assert item_by_id["item1"] == 1  # Unchanged
        assert item_by_id["item2"] == 4  # Moved element
        assert item_by_id["item3"] == 2  # Shifted up
        assert item_by_id["item4"] == 3  # Shifted up

    def test_move_no_change(self):
        """Test moving element to same position (no-op)."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        mover = StructureMover()
        operation = MoveOperation(from_sequence=2, to_sequence=2, element_path="items")

        result = mover.move_element(structure, operation)

        assert result.success
        # All sequences should remain unchanged
        for mapping in result.mappings:
            assert mapping.old_sequence == mapping.new_sequence

    def test_dry_run(self):
        """Test dry-run mode doesn't modify structure."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
            ]
        }

        mover = StructureMover()
        operation = MoveOperation(from_sequence=3, to_sequence=1, element_path="items")

        result = mover.move_element(structure, operation, dry_run=True)

        assert result.success
        assert result.modified_structure is None  # No modification
        assert len(result.mappings) > 0  # But mappings calculated

    def test_nested_structure(self):
        """Test moving in nested structure."""
        structure = {
            "phases": [
                {
                    "phase_id": "phase1",
                    "steps": [
                        {"step_id": "step1", "sequence": 1},
                        {"step_id": "step2", "sequence": 2},
                        {"step_id": "step3", "sequence": 3},
                    ],
                }
            ]
        }

        mover = StructureMover()
        operation = MoveOperation(
            from_sequence=3,
            to_sequence=1,
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id",
        )

        result = mover.move_element(structure, operation)

        assert result.success

        steps = result.modified_structure["phases"][0]["steps"]
        step_by_id = {step["step_id"]: step["sequence"] for step in steps}

        assert step_by_id["step3"] == 1  # Moved to front
        assert step_by_id["step1"] == 2
        assert step_by_id["step2"] == 3

    def test_invalid_from_sequence(self):
        """Test error when from_sequence doesn't exist."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        mover = StructureMover()
        operation = MoveOperation(
            from_sequence=99, to_sequence=1, element_path="items"  # Doesn't exist
        )

        result = mover.move_element(structure, operation)

        assert not result.success
        assert len(result.errors) > 0

    def test_custom_fields(self):
        """Test with custom field names."""
        structure = {
            "tasks": [
                {"task_id": "t1", "order": 10},
                {"task_id": "t2", "order": 20},
                {"task_id": "t3", "order": 30},
            ]
        }

        mover = StructureMover()
        operation = MoveOperation(
            from_sequence=30,
            to_sequence=10,
            element_path="tasks",
            id_field="task_id",
            sequence_field="order",
        )

        result = mover.move_element(structure, operation)

        assert result.success

        tasks = result.modified_structure["tasks"]
        task_by_id = {task["task_id"]: task["order"] for task in tasks}

        assert task_by_id["t3"] == 10  # Moved to front
        assert task_by_id["t1"] == 20
        assert task_by_id["t2"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
