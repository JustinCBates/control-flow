"""
Unit tests for StructureDeleter.

Tests deletion operations with sequence management.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from control_flow_engine.libraries.structure_ops import (
    StructureDeleter, DeleteOperation, DeleteResult
)


class TestStructureDeleter:
    """Test cases for StructureDeleter."""
    
    def test_delete_basic(self):
        """Test basic element deletion."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item2",
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        assert len(result.modified_structure["items"]) == 2
        
        remaining_ids = [item["id"] for item in result.modified_structure["items"]]
        assert "item2" not in remaining_ids
    
    def test_delete_with_cascade(self):
        """Test deletion with cascade renumbering."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3},
                {"id": "item4", "sequence": 4}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item2",
            cascade_renumber=True,
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        
        # Check cascade: item3 should be 2, item4 should be 3
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        
        assert sequences["item1"] == 1
        assert sequences["item3"] == 2
        assert sequences["item4"] == 3
    
    def test_delete_without_cascade(self):
        """Test deletion without cascade renumbering."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2},
                {"id": "item3", "sequence": 3}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item2",
            cascade_renumber=False,
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        
        # Sequences should not change
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        assert sequences["item1"] == 1
        assert sequences["item3"] == 3  # Gap at 2
    
    def test_delete_nested(self):
        """Test deletion from nested structure."""
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
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="step2",
            element_path="steps",
            id_field="step_id",
            parent_path="phases",
            parent_id="phase1",
            parent_id_field="phase_id",
            cascade_renumber=True
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        
        steps = result.modified_structure["phases"][0]["steps"]
        assert len(steps) == 2
        
        sequences = {step["step_id"]: step["sequence"] for step in steps}
        assert sequences["step1"] == 1
        assert sequences["step3"] == 2  # Renumbered
    
    def test_delete_first_element(self):
        """Test deleting first element."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item1",
            cascade_renumber=True,
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        assert sequences["item2"] == 1
    
    def test_delete_last_element(self):
        """Test deleting last element."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item2",
            cascade_renumber=True,
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        
        sequences = {item["id"]: item["sequence"] 
                    for item in result.modified_structure["items"]}
        assert sequences["item1"] == 1  # Unchanged
    
    def test_deleted_element_stored(self):
        """Test that deleted element is stored in result."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1, "data": "important"}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item1",
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert result.success
        assert result.deleted_element is not None
        assert result.deleted_element["id"] == "item1"
        assert result.deleted_element["data"] == "important"
    
    def test_dry_run(self):
        """Test dry-run mode."""
        structure = {
            "items": [
                {"id": "item1", "sequence": 1},
                {"id": "item2", "sequence": 2}
            ]
        }
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="item1",
            cascade_renumber=True,
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation, dry_run=True)
        
        assert result.success
        assert result.modified_structure is None
        assert len(result.mappings) > 0
    
    def test_invalid_element_id(self):
        """Test error when element_id doesn't exist."""
        structure = {"items": [{"id": "item1", "sequence": 1}]}
        
        deleter = StructureDeleter()
        operation = DeleteOperation(
            element_id="nonexistent",
            element_path="items"
        )
        
        result = deleter.delete_element(structure, operation)
        
        assert not result.success
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
