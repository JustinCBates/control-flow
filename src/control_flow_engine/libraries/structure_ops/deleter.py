"""
Structure Deletion Library

Universal library for deleting elements from hierarchical list structures with sequence management.
Works on ANY nested data structure without domain coupling.

Author: Control Flow Engine Libraries
Date: 2025-01-XX
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import copy


@dataclass
class SequenceMapping:
    """Maps an element's old sequence to its new sequence after deletion."""

    element_id: str
    old_sequence: int
    new_sequence: Optional[int]
    is_deleted: bool = False

    def __repr__(self):
        if self.is_deleted:
            return f"DELETE '{self.element_id}' (was seq {self.old_sequence})"
        elif self.old_sequence != self.new_sequence:
            return f"RENUMBER '{self.element_id}': {self.old_sequence} → {self.new_sequence}"
        else:
            return f"PRESERVE '{self.element_id}' at seq {self.new_sequence}"


@dataclass
class DeleteOperation:
    """Complete definition of a deletion operation."""

    element_id: str  # ID of element to delete
    cascade_renumber: bool = True
    element_path: str = "items"  # Path to list in structure
    id_field: str = "id"  # Field containing element ID
    sequence_field: str = "sequence"  # Field containing sequence number
    parent_path: Optional[str] = None  # Path to parent element if nested
    parent_id: Optional[str] = None  # ID of parent element if nested
    parent_id_field: Optional[str] = (
        None  # Field containing parent ID (defaults to id_field)
    )

    def __repr__(self):
        parent_info = f" from parent '{self.parent_id}'" if self.parent_id else ""
        return f"Delete '{self.element_id}'{parent_info}"


@dataclass
class DeleteResult:
    """Result of a deletion operation."""

    success: bool
    element_id: str
    deleted_sequence: Optional[int] = None
    deleted_element: Optional[Dict[str, Any]] = None  # For rollback capability
    mappings: List[SequenceMapping] = None
    errors: List[str] = None
    modified_structure: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.mappings is None:
            self.mappings = []
        if self.errors is None:
            self.errors = []

    def __repr__(self):
        if self.success:
            affected = len(
                [
                    m
                    for m in self.mappings
                    if m.old_sequence != m.new_sequence or m.is_deleted
                ]
            )
            return f"✅ DELETE SUCCESS: '{self.element_id}' (was seq {self.deleted_sequence}, affected {affected} element{'s' if affected != 1 else ''})"
        else:
            return f"❌ DELETE FAILED: {', '.join(self.errors)}"


class DeleteError(Exception):
    """Exception raised when deletion operation fails."""

    pass


class StructureDeleter:
    """
    Universal structure deletion engine.

    Deletes elements from hierarchical list structures while managing
    sequence numbers. Works on ANY data structure without domain knowledge.

    Example structure:
        {
            "items": [
                {"id": "item1", "sequence": 1, "name": "First"},
                {"id": "item2", "sequence": 2, "name": "Second"},
                {"id": "item3", "sequence": 3, "name": "Third"},
            ]
        }

    Can also work on nested structures:
        {
            "phases": [
                {
                    "phase_id": "phase1",
                    "sequence": 1,
                    "steps": [
                        {"step_id": "step1", "sequence": 1},
                        {"step_id": "step2", "sequence": 2}
                    ]
                }
            ]
        }
    """

    def delete_element(
        self,
        structure: Dict[str, Any],
        operation: DeleteOperation,
        dry_run: bool = False,
    ) -> DeleteResult:
        """
        Delete an element from the structure.

        Args:
            structure: The hierarchical structure to modify
            operation: Complete deletion operation definition
            dry_run: If True, calculate changes without modifying structure

        Returns:
            DeleteResult with success status, mappings, and modified structure

        Raises:
            DeleteError: If operation is invalid or fails
        """
        try:
            # Get target list
            target_list = self._get_target_list(structure, operation)
            if target_list is None:
                return DeleteResult(
                    success=False,
                    element_id=operation.element_id,
                    errors=[f"Target list '{operation.element_path}' not found"],
                )

            # Find element to delete
            deleted_element = None
            deleted_seq = None

            for item in target_list:
                if item.get(operation.id_field) == operation.element_id:
                    deleted_element = copy.deepcopy(item)
                    deleted_seq = item.get(operation.sequence_field, 0)
                    break

            if deleted_element is None:
                return DeleteResult(
                    success=False,
                    element_id=operation.element_id,
                    errors=[f"Element '{operation.element_id}' not found"],
                )

            # Calculate sequence mappings
            mappings = self._calculate_mappings(
                target_list, operation.element_id, deleted_seq, operation
            )

            # Apply changes if not dry run
            modified_structure = structure
            if not dry_run:
                modified_structure = self._apply_deletion(
                    structure, operation, mappings
                )

            return DeleteResult(
                success=True,
                element_id=operation.element_id,
                deleted_sequence=deleted_seq,
                deleted_element=deleted_element,
                mappings=mappings,
                modified_structure=modified_structure if not dry_run else None,
            )

        except Exception as e:
            return DeleteResult(
                success=False, element_id=operation.element_id, errors=[str(e)]
            )

    def _get_target_list(
        self, structure: Dict[str, Any], operation: DeleteOperation
    ) -> Optional[List[Dict[str, Any]]]:
        """Get the list to delete from."""
        # If deleting from nested structure
        if operation.parent_path and operation.parent_id:
            parent_list = structure.get(operation.parent_path, [])
            # Use parent_id_field if specified, otherwise use id_field
            parent_id_field = operation.parent_id_field or operation.id_field
            for parent in parent_list:
                if parent.get(parent_id_field) == operation.parent_id:
                    return parent.get(operation.element_path)
            return None
        else:
            # Top-level deletion
            return structure.get(operation.element_path)

    def _calculate_mappings(
        self,
        target_list: List[Dict[str, Any]],
        delete_id: str,
        deleted_seq: int,
        operation: DeleteOperation,
    ) -> List[SequenceMapping]:
        """Calculate sequence mappings for all affected elements."""
        mappings = []
        seq_field = operation.sequence_field
        id_field = operation.id_field

        # Add mapping for deleted element
        mappings.append(
            SequenceMapping(
                element_id=delete_id,
                old_sequence=deleted_seq,
                new_sequence=None,
                is_deleted=True,
            )
        )

        # Calculate renumber mappings if cascade enabled
        if operation.cascade_renumber:
            for item in target_list:
                item_id = item.get(id_field)
                if item_id == delete_id:
                    continue  # Skip deleted element

                item_seq = item.get(seq_field, 0)
                new_seq = item_seq - 1 if item_seq > deleted_seq else item_seq

                mappings.append(
                    SequenceMapping(
                        element_id=item_id,
                        old_sequence=item_seq,
                        new_sequence=new_seq,
                        is_deleted=False,
                    )
                )
        else:
            # No cascade - preserve existing sequences
            for item in target_list:
                item_id = item.get(id_field)
                if item_id == delete_id:
                    continue

                item_seq = item.get(seq_field, 0)
                mappings.append(
                    SequenceMapping(
                        element_id=item_id,
                        old_sequence=item_seq,
                        new_sequence=item_seq,
                        is_deleted=False,
                    )
                )

        return mappings

    def _apply_deletion(
        self,
        structure: Dict[str, Any],
        operation: DeleteOperation,
        mappings: List[SequenceMapping],
    ) -> Dict[str, Any]:
        """Apply the deletion to the structure."""
        modified = copy.deepcopy(structure)

        # Get target list
        target_list = self._get_target_list(modified, operation)

        # Apply renumbering to remaining elements
        for mapping in mappings:
            if not mapping.is_deleted and mapping.old_sequence != mapping.new_sequence:
                for item in target_list:
                    if item.get(operation.id_field) == mapping.element_id:
                        item[operation.sequence_field] = mapping.new_sequence

        # Remove deleted element
        if operation.parent_path and operation.parent_id:
            # Nested deletion
            parent_list = modified.get(operation.parent_path, [])
            parent_id_field = operation.parent_id_field or operation.id_field
            for parent in parent_list:
                if parent.get(parent_id_field) == operation.parent_id:
                    parent[operation.element_path] = [
                        item
                        for item in parent.get(operation.element_path, [])
                        if item.get(operation.id_field) != operation.element_id
                    ]
        else:
            # Top-level deletion
            modified[operation.element_path] = [
                item
                for item in modified.get(operation.element_path, [])
                if item.get(operation.id_field) != operation.element_id
            ]

        return modified


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================


def demo_deleter():
    """Demonstrate structure deletion functionality."""
    print("=" * 70)
    print("STRUCTURE DELETER LIBRARY - DEMO")
    print("=" * 70)

    deleter = StructureDeleter()

    # Example 1: Delete from middle with cascade
    print("\n📝 Example 1: Delete 'item2' with cascade renumbering")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1, "name": "First"},
            {"id": "item2", "sequence": 2, "name": "Second"},
            {"id": "item3", "sequence": 3, "name": "Third"},
            {"id": "item4", "sequence": 4, "name": "Fourth"},
        ]
    }

    print("Before:")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']} - {item['name']}")

    operation = DeleteOperation(
        element_id="item2", cascade_renumber=True, element_path="items"
    )

    result = deleter.delete_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter:")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']} - {item.get('name', 'N/A')}")

    # Example 2: Delete last element (no cascade needed)
    print("\n\n📝 Example 2: Delete last element 'item4'")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1, "name": "First"},
            {"id": "item2", "sequence": 2, "name": "Second"},
            {"id": "item3", "sequence": 3, "name": "Third"},
            {"id": "item4", "sequence": 4, "name": "Fourth"},
        ]
    }

    print("Before:")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")

    operation = DeleteOperation(
        element_id="item4", cascade_renumber=True, element_path="items"
    )

    result = deleter.delete_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter:")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    # Example 3: Delete from nested structure
    print("\n\n📝 Example 3: Delete step from phase (nested structure)")
    print("-" * 70)

    structure = {
        "phases": [
            {
                "phase_id": "phase1",
                "sequence": 1,
                "steps": [
                    {"step_id": "step1", "sequence": 1, "name": "First Step"},
                    {"step_id": "step2", "sequence": 2, "name": "Second Step"},
                    {"step_id": "step3", "sequence": 3, "name": "Third Step"},
                ],
            }
        ]
    }

    print("Before:")
    for phase in structure["phases"]:
        print(f"  Phase {phase['phase_id']}:")
        for step in phase.get("steps", []):
            print(f"    seq {step['sequence']}: {step['step_id']} - {step['name']}")

    operation = DeleteOperation(
        element_id="step2",
        element_path="steps",
        id_field="step_id",
        parent_path="phases",
        parent_id="phase1",
        parent_id_field="phase_id",
        cascade_renumber=True,
    )

    result = deleter.delete_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter:")
        for phase in result.modified_structure["phases"]:
            print(f"  Phase {phase['phase_id']}:")
            for step in phase.get("steps", []):
                print(f"    seq {step['sequence']}: {step['step_id']} - {step['name']}")

    # Example 4: Delete without cascade
    print("\n\n📝 Example 4: Delete without cascade renumbering")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1},
            {"id": "item2", "sequence": 2},
            {"id": "item3", "sequence": 3},
        ]
    }

    print("Before:")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")

    operation = DeleteOperation(
        element_id="item2", cascade_renumber=False, element_path="items"  # No cascade
    )

    result = deleter.delete_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter (note: sequence gap at 2):")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_deleter()
