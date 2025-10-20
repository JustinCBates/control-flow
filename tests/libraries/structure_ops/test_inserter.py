"""
Unit tests for StructureInserter.

Tests insertion operations with sequence management.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from control_flow_engine.libraries.structure_ops import (
    StructureInserter,
    InsertOperation,
    InsertResult,
    InsertPosition,
    InsertionPoint,
)


class TestStructureInserter:
    """Test cases for StructureInserter."""

    def test_insert_at_end(self):
        """Test inserting at end of list."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item3", "name": "New"},
            insertion_point=InsertionPoint(position=InsertPosition.AT_END),
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        assert result.insert_sequence == 3
        assert len(result.modified_structure["items"]) == 3

    def test_insert_after_with_cascade(self):
        """Test inserting after element with cascade renumbering."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
            ]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item_new"},
            insertion_point=InsertionPoint(
                position=InsertPosition.AFTER, reference_id="item1"
            ),
            cascade_renumber=True,
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        assert result.insert_sequence == 2

        # Check cascade: item2 should be 3, item3 should be 4
        items = result.modified_structure["items"]
        sequences = {item["id"]: item["sequence"] for item in items}

        assert sequences["item1"] == 1
        assert sequences["item_new"] == 2
        assert sequences["item2"] == 3
        assert sequences["item3"] == 4

    def test_insert_before(self):
        """Test inserting before element."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item_new"},
            insertion_point=InsertionPoint(
                position=InsertPosition.BEFORE, reference_id="item2"
            ),
            cascade_renumber=True,
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        assert result.insert_sequence == 2

        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }
        assert sequences["item_new"] == 2
        assert sequences["item2"] == 3

    def test_insert_at_sequence(self):
        """Test inserting at specific sequence."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
            ]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item_new"},
            insertion_point=InsertionPoint(
                position=InsertPosition.AT_SEQUENCE, target_sequence=2
            ),
            cascade_renumber=True,
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        assert result.insert_sequence == 2

    def test_insert_without_cascade(self):
        """Test inserting without cascade renumbering."""
        structure = {
            "items": [{"id": "item1", "sequence": 1}, {"id": "item2", "sequence": 2}]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item_new"},
            insertion_point=InsertionPoint(
                position=InsertPosition.AFTER, reference_id="item1"
            ),
            cascade_renumber=False,
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        # Existing items should keep their sequences
        sequences = {
            item["id"]: item["sequence"] for item in result.modified_structure["items"]
        }
        assert sequences["item2"] == 2  # Not changed

    def test_insert_nested(self):
        """Test inserting into nested structure."""
        structure = {
            "phases": [
                {
                    "phase_id": "phase1",
                    "steps": [
                        {"step_id": "step1", "sequence": 1},
                        {"step_id": "step2", "sequence": 2},
                    ],
                }
            ]
        }

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"step_id": "step_new"},
            insertion_point=InsertionPoint(
                position=InsertPosition.BEFORE, reference_id="step2"
            ),
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id",
            cascade_renumber=True,
        )

        result = inserter.insert_element(structure, operation)

        assert result.success

        steps = result.modified_structure["phases"][0]["steps"]
        assert len(steps) == 3

        sequences = {step["step_id"]: step["sequence"] for step in steps}
        assert sequences["step_new"] == 2
        assert sequences["step2"] == 3

    def test_insert_into_empty_list(self):
        """Test inserting into empty list."""
        structure = {"items": []}

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item1"},
            insertion_point=InsertionPoint(position=InsertPosition.AT_END),
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert result.success
        assert result.insert_sequence == 1
        assert len(result.modified_structure["items"]) == 1

    def test_dry_run(self):
        """Test dry-run mode."""
        structure = {"items": [{"id": "item1", "sequence": 1}]}

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item2"},
            insertion_point=InsertionPoint(position=InsertPosition.AT_END),
            element_path="items",
        )

        result = inserter.insert_element(structure, operation, dry_run=True)

        assert result.success
        assert result.modified_structure is None
        assert len(result.mappings) > 0

    def test_invalid_reference_id(self):
        """Test error when reference_id doesn't exist."""
        structure = {"items": [{"id": "item1", "sequence": 1}]}

        inserter = StructureInserter()
        operation = InsertOperation(
            new_element={"id": "item2"},
            insertion_point=InsertionPoint(
                position=InsertPosition.AFTER, reference_id="nonexistent"
            ),
            element_path="items",
        )

        result = inserter.insert_element(structure, operation)

        assert not result.success
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
