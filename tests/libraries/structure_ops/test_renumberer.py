"""
Unit tests for StructureRenumberer.

Tests sequence renumbering operations with different strategies.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from control_flow_engine.libraries.structure_ops import (
    StructureRenumberer,
    RenumberOperation,
    RenumberResult,
    RenumberStrategy,
)


class TestStructureRenumberer:
    """Test cases for StructureRenumberer."""

    def test_compact_strategy(self):
        """Test COMPACT strategy to remove gaps."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 5},
                {"id": "item3", "sequence": 10},
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.COMPACT, element_path="items"
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 1
        assert sequences["item2"] == 2
        assert sequences["item3"] == 3

    def test_shift_up_strategy(self):
        """Test SHIFT_UP strategy after insertion."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.SHIFT_UP, starting_from=2, element_path="items"
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 1  # Below threshold, unchanged
        assert sequences["item2"] == 3  # Shifted up
        assert sequences["item3"] == 4  # Shifted up

    def test_shift_down_strategy(self):
        """Test SHIFT_DOWN strategy after deletion."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 3},  # Gap at 2
                {"id": "item3", "sequence": 4},
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.SHIFT_DOWN, starting_from=2, element_path="items"
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 1  # Below threshold, unchanged
        assert sequences["item2"] == 2  # Shifted down
        assert sequences["item3"] == 3  # Shifted down

    def test_explicit_strategy(self):
        """Test EXPLICIT strategy with custom mappings."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.EXPLICIT,
            mappings={1: 10, 2: 20, 3: 30},
            element_path="items",
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 10
        assert sequences["item2"] == 20
        assert sequences["item3"] == 30

    def test_nested_structure(self):
        """Test renumbering in nested structure."""
        structure = {
            "phases": [
                {
                    "phase_id": "phase1",
                    "steps": [
                        {"step_id": "step1", "sequence": 1},
                        {"step_id": "step2", "sequence": 5},
                        {"step_id": "step3", "sequence": 10},
                    ],
                }
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.COMPACT,
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id",
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        steps = result.modified_structure["phases"][0]["steps"]
        sequences = {step["step_id"]: step["sequence"] for step in steps}

        assert sequences["step1"] == 1
        assert sequences["step2"] == 2
        assert sequences["step3"] == 3

    def test_custom_fields(self):
        """Test renumbering with custom field names."""
        structure = {
            "tasks": [
                {"task_id": "task1", "order": 10},
                {"task_id": "task2", "order": 50},
                {"task_id": "task3", "order": 100},
            ]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.COMPACT,
            element_path="tasks",
            id_field="task_id",
            sequence_field="order",
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        orders = {
            task["task_id"]: task["order"]
            for task in result.modified_structure["tasks"]
        }

        assert orders["task1"] == 1
        assert orders["task2"] == 2
        assert orders["task3"] == 3

    def test_compact_already_compact(self):
        """Test COMPACT on already compact sequences."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.COMPACT, element_path="items"
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 1
        assert sequences["item2"] == 2

    def test_dry_run(self):
        """Test dry-run mode."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 10}]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.COMPACT, element_path="items"
        )

        result = renumberer.renumber_elements(structure, operation, dry_run=True)

        assert result.success
        assert result.modified_structure is None
        assert len(result.mappings) > 0

    def test_explicit_missing_mapping(self):
        """Test error when EXPLICIT strategy missing mappings."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.EXPLICIT,
            mappings={1: 10},  # Missing mapping for sequence 2
            element_path="items",
        )

        result = renumberer.renumber_elements(structure, operation)

        assert not result.success
        assert len(result.errors) > 0

    def test_shift_up_with_custom_increment(self):
        """Test SHIFT_UP with custom shift amount."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        renumberer = StructureRenumberer()
        operation = RenumberOperation(
            strategy=RenumberStrategy.SHIFT_UP,
            starting_from=1,
            shift_amount=5,
            element_path="items",
        )

        result = renumberer.renumber_elements(structure, operation)

        assert result.success

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }

        assert sequences["item1"] == 6  # 1 + 5
        assert sequences["item2"] == 7  # 2 + 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
