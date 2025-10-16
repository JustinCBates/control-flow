"""
Unit tests for StructureReorderer.

Tests batch reordering operations.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from control_flow_engine.libraries.structure_ops import (
    StructureReorderer, ReorderOperation, ReorderResult
)


class TestStructureReorderer:
    """Test cases for StructureReorderer."""
    
    def test_reorder_basic(self):
        """Test basic reordering."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={1: 3, 2: 1, 3: 2},  # Rotate
            element_path="items"
        )
        
        result = reorderer.reorder_elements(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item1"] == 3
        assert sequences["item2"] == 1
        assert sequences["item3"] == 2
    
    def test_reorder_by_ids(self):
        """Test reordering by ID list."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            element_path="items"
        )
        
        # Reverse order
        result = reorderer.reorder_by_ids(
            structure, 
            operation, 
            ["item3", "item2", "item1"]
        )
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item3"] == 1
        assert sequences["item2"] == 2
        assert sequences["item1"] == 3
    
    def test_reorder_nested(self):
        """Test reordering in nested structure."""
        structure = {
            "phases": [
                {
                    "phase_id": "phase1",
                    "steps": [
                        {"step_id": "step1", "sequence": 1},
                        {"step_id": "step2", "sequence": 2},
                        {"step_id": "step3", "sequence": 3}
                    ]
                }
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={1: 2, 2: 3, 3: 1},
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id"
        )
        
        result = reorderer.reorder_elements(structure, operation)
        
        assert result.success
        
        steps = result.modified_structure["phases"][0]["steps"]
        sequences = {step["step_id"]: step["sequence"] for step in steps}
        
        assert sequences["step1"] == 2
        assert sequences["step2"] == 3
        assert sequences["step3"] == 1
    
    def test_reorder_custom_fields(self):
        """Test reorder with custom field names."""
        structure = {
            "tasks": [
                {"task_id": "task1", "order": 10},
                {"task_id": "task2", "order": 20}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={10: 20, 20: 10},
            element_path="tasks",
            id_field="task_id",
            sequence_field="order"
        )
        
        result = reorderer.reorder_elements(structure, operation)
        
        assert result.success
        
        orders = {task["task_id"]: task["order"] 
                 for task in result.modified_structure["tasks"]}
        
        assert orders["task1"] == 20
        assert orders["task2"] == 10
    
    def test_reorder_partial(self):
        """Test partial reordering (only some elements)."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
                {"id": "item4", "sequence": 4}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={1: 3, 3: 1},  # Only swap 1 and 3
            element_path="items"
        )
        
        result = reorderer.reorder_elements(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item1"] == 3
        assert sequences["item2"] == 2  # Unchanged
        assert sequences["item3"] == 1
        assert sequences["item4"] == 4  # Unchanged
    
    def test_dry_run(self):
        """Test dry-run mode."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={1: 2, 2: 1},
            element_path="items"
        )
        
        result = reorderer.reorder_elements(structure, operation, dry_run=True)
        
        assert result.success
        assert result.modified_structure is None
        assert len(result.mappings) > 0
    
    def test_invalid_new_order(self):
        """Test error with invalid new_order."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(
            new_order={1: 99},  # 99 doesn't exist
            element_path="items"
        )
        
        result = reorderer.reorder_elements(structure, operation)
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_reorder_by_ids_missing_id(self):
        """Test error when ID list is incomplete."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(element_path="items")
        
        # Only one ID (should have both)
        result = reorderer.reorder_by_ids(structure, operation, ["item1"])
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_reorder_by_ids_extra_id(self):
        """Test error when ID list has extras."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1}
            ]
        }
        
        reorderer = StructureReorderer()
        operation = ReorderOperation(element_path="items")
        
        # Extra ID that doesn't exist
        result = reorderer.reorder_by_ids(
            structure, 
            operation, 
            ["item1", "item2"]
        )
        
        assert not result.success
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
