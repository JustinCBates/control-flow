"""
Unit tests for StructureSwapper.

Tests swap operations between two elements.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from control_flow_engine.libraries.structure_ops import (
    StructureSwapper, SwapOperation, SwapResult
)


class TestStructureSwapper:
    """Test cases for StructureSwapper."""
    
    def test_swap_basic(self):
        """Test basic swap operation."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3}
            ]
        }
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="item1",
            element_b_id="item3",
            element_path="items"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item1"] == 3
        assert sequences["item2"] == 2  # Unchanged
        assert sequences["item3"] == 1
    
    def test_swap_adjacent(self):
        """Test swapping adjacent elements."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="item1",
            element_b_id="item2",
            element_path="items"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item1"] == 2
        assert sequences["item2"] == 1
    
    def test_swap_nested(self):
        """Test swapping in nested structure."""
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
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="step1",
            element_b_id="step3",
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert result.success
        
        steps = result.modified_structure["phases"][0]["steps"]
        sequences = {step["step_id"]: step["sequence"] for step in steps}
        
        assert sequences["step1"] == 3
        assert sequences["step2"] == 2
        assert sequences["step3"] == 1
    
    def test_swap_custom_fields(self):
        """Test swap with custom field names."""
        structure = {
            "tasks": [
                {"task_id": "task1", "order": 10},
                {"task_id": "task2", "order": 20}
            ]
        }
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="task1",
            element_b_id="task2",
            element_path="tasks",
            id_field="task_id",
            sequence_field="order"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert result.success
        
        orders = {task["task_id"]: task["order"] 
                 for task in result.modified_structure["tasks"]}
        
        assert orders["task1"] == 20
        assert orders["task2"] == 10
    
    def test_dry_run(self):
        """Test dry-run mode."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="item1",
            element_b_id="item2",
            element_path="items"
        )
        
        result = swapper.swap_elements(structure, operation, dry_run=True)
        
        assert result.success
        assert result.modified_structure is None
        assert len(result.mappings) > 0
    
    def test_swap_same_element_error(self):
        """Test error when trying to swap element with itself."""
        structure = {"items": [{"id": "item1", "sequence": 1}]}
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="item1",
            element_b_id="item1",
            element_path="items"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_invalid_element_id(self):
        """Test error when element doesn't exist."""
        structure = {"items": [{"id": "item1", "sequence": 1}]}
        
        swapper = StructureSwapper()
        operation = SwapOperation(
            element_a_id="item1",
            element_b_id="nonexistent",
            element_path="items"
        )
        
        result = swapper.swap_elements(structure, operation)
        
        assert not result.success
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
