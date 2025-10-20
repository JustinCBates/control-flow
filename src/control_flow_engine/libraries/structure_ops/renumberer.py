"""
Structure Renumbering Library

Universal library for calculating sequence renumbering in hierarchical list structures.
Works on ANY nested data structure without domain coupling.

Author: Control Flow Engine Libraries
Date: 2025-10-16
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
import copy


class RenumberStrategy(Enum):
    """Strategy for handling sequence renumbering."""

    COMPACT = "compact"  # Remove all gaps: [1,2,4,7] → [1,2,3,4]
    SHIFT_UP = "shift_up"  # Shift sequences up from insertion point
    SHIFT_DOWN = "shift_down"  # Shift sequences down after deletion
    EXPLICIT = "explicit"  # Use explicit mapping provided


@dataclass
class SequenceMapping:
    """Maps an element's old sequence to its new sequence."""

    element_id: str
    old_sequence: int
    new_sequence: int

    def __repr__(self):
        if self.old_sequence != self.new_sequence:
            return f"RENUMBER '{self.element_id}': {self.old_sequence} → {self.new_sequence}"
        else:
            return f"PRESERVE '{self.element_id}' at seq {self.new_sequence}"


@dataclass
class RenumberOperation:
    """Complete definition of a renumbering operation."""

    strategy: RenumberStrategy = RenumberStrategy.COMPACT
    element_path: str = "items"  # Path to list in structure
    id_field: str = "id"  # Field containing element ID
    sequence_field: str = "sequence"  # Field containing sequence number
    parent_path: Optional[str] = None  # Path to parent element if nested
    parent_id: Optional[str] = None  # ID of parent element if nested
    parent_id_field: Optional[str] = None  # Field containing parent ID

    # For SHIFT_UP/SHIFT_DOWN strategies
    insertion_point: Optional[int] = None  # Insert at this sequence (shifts >= up by 1)
    deletion_point: Optional[int] = None  # Delete at this sequence (shifts > down by 1)

    # For EXPLICIT strategy
    explicit_mappings: Optional[Dict[str, int]] = None  # {element_id: new_sequence}

    def __repr__(self):
        if self.strategy == RenumberStrategy.COMPACT:
            return f"Compact numbering in '{self.element_path}'"
        elif self.strategy == RenumberStrategy.SHIFT_UP:
            return f"Shift up from sequence {self.insertion_point}"
        elif self.strategy == RenumberStrategy.SHIFT_DOWN:
            return f"Shift down after sequence {self.deletion_point}"
        else:
            return f"Explicit renumber in '{self.element_path}'"


@dataclass
class RenumberResult:
    """Result of a renumbering operation."""

    success: bool
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
                [m for m in self.mappings if m.old_sequence != m.new_sequence]
            )
            return f"✅ RENUMBER SUCCESS: {affected} element{'s' if affected != 1 else ''} renumbered"
        else:
            return f"❌ RENUMBER FAILED: {', '.join(self.errors)}"


class RenumberError(Exception):
    """Exception raised when renumbering operation fails."""

    pass


class StructureRenumberer:
    """
    Universal structure renumbering engine.

    Calculates and applies sequence renumbering in hierarchical list structures.
    Works on ANY data structure without domain knowledge.

    Features:
    - COMPACT: Remove all gaps in sequences
    - SHIFT_UP: Shift sequences up after insertion
    - SHIFT_DOWN: Shift sequences down after deletion
    - EXPLICIT: Apply explicit sequence mappings

    Example structure:
        {
            "items": [
                {"id": "item1", "sequence": 1, "name": "First"},
                {"id": "item2", "sequence": 2, "name": "Second"},
                {"id": "item3", "sequence": 5, "name": "Third"},  # Gap at 3, 4
            ]
        }

    After COMPACT:
        {
            "items": [
                {"id": "item1", "sequence": 1, "name": "First"},
                {"id": "item2", "sequence": 2, "name": "Second"},
                {"id": "item3", "sequence": 3, "name": "Third"},  # Gap removed
            ]
        }
    """

    def renumber(
        self,
        structure: Dict[str, Any],
        operation: RenumberOperation,
        dry_run: bool = False,
    ) -> RenumberResult:
        """
        Renumber elements in the structure.

        Args:
            structure: The hierarchical structure to modify
            operation: Complete renumbering operation definition
            dry_run: If True, calculate changes without modifying structure

        Returns:
            RenumberResult with success status, mappings, and modified structure

        Raises:
            RenumberError: If operation is invalid or fails
        """
        try:
            # Get target list
            target_list = self._get_target_list(structure, operation)
            if target_list is None:
                return RenumberResult(
                    success=False,
                    errors=[f"Target list '{operation.element_path}' not found"],
                )

            if not target_list:
                return RenumberResult(
                    success=True, errors=["Target list is empty - nothing to renumber"]
                )

            # Calculate new sequences based on strategy
            mappings = self._calculate_renumber_mappings(target_list, operation)

            # Apply changes if not dry run
            modified_structure = structure
            if not dry_run:
                modified_structure = self._apply_renumbering(
                    structure, operation, mappings
                )

            return RenumberResult(
                success=True,
                mappings=mappings,
                modified_structure=modified_structure if not dry_run else None,
            )

        except Exception as e:
            return RenumberResult(success=False, errors=[str(e)])

    def _get_target_list(
        self, structure: Dict[str, Any], operation: RenumberOperation
    ) -> Optional[List[Dict[str, Any]]]:
        """Get the list to renumber."""
        # If renumbering nested structure
        if operation.parent_path and operation.parent_id:
            parent_list = structure.get(operation.parent_path, [])
            parent_id_field = operation.parent_id_field or operation.id_field
            for parent in parent_list:
                if parent.get(parent_id_field) == operation.parent_id:
                    return parent.get(operation.element_path)
            return None
        else:
            # Top-level renumbering
            return structure.get(operation.element_path)

    def _calculate_renumber_mappings(
        self, target_list: List[Dict[str, Any]], operation: RenumberOperation
    ) -> List[SequenceMapping]:
        """Calculate sequence mappings based on strategy."""
        mappings = []
        seq_field = operation.sequence_field
        id_field = operation.id_field

        if operation.strategy == RenumberStrategy.COMPACT:
            # Remove all gaps: assign sequential numbers 1, 2, 3, ...
            sorted_items = sorted(target_list, key=lambda x: x.get(seq_field, 0))
            for idx, item in enumerate(sorted_items, start=1):
                old_seq = item.get(seq_field, 0)
                mappings.append(
                    SequenceMapping(
                        element_id=item.get(id_field),
                        old_sequence=old_seq,
                        new_sequence=idx,
                    )
                )

        elif operation.strategy == RenumberStrategy.SHIFT_UP:
            # Shift sequences >= insertion_point up by 1
            if operation.insertion_point is None:
                raise RenumberError("SHIFT_UP strategy requires insertion_point")

            for item in target_list:
                item_seq = item.get(seq_field, 0)
                item_id = item.get(id_field)

                if item_seq >= operation.insertion_point:
                    new_seq = item_seq + 1
                else:
                    new_seq = item_seq

                mappings.append(
                    SequenceMapping(
                        element_id=item_id, old_sequence=item_seq, new_sequence=new_seq
                    )
                )

        elif operation.strategy == RenumberStrategy.SHIFT_DOWN:
            # Shift sequences > deletion_point down by 1
            if operation.deletion_point is None:
                raise RenumberError("SHIFT_DOWN strategy requires deletion_point")

            for item in target_list:
                item_seq = item.get(seq_field, 0)
                item_id = item.get(id_field)

                if item_seq > operation.deletion_point:
                    new_seq = item_seq - 1
                else:
                    new_seq = item_seq

                mappings.append(
                    SequenceMapping(
                        element_id=item_id, old_sequence=item_seq, new_sequence=new_seq
                    )
                )

        elif operation.strategy == RenumberStrategy.EXPLICIT:
            # Use explicit mappings
            if not operation.explicit_mappings:
                raise RenumberError("EXPLICIT strategy requires explicit_mappings")

            for item in target_list:
                item_id = item.get(id_field)
                old_seq = item.get(seq_field, 0)

                if item_id in operation.explicit_mappings:
                    new_seq = operation.explicit_mappings[item_id]
                else:
                    new_seq = old_seq  # Preserve if not in mapping

                mappings.append(
                    SequenceMapping(
                        element_id=item_id, old_sequence=old_seq, new_sequence=new_seq
                    )
                )

        return mappings

    def _apply_renumbering(
        self,
        structure: Dict[str, Any],
        operation: RenumberOperation,
        mappings: List[SequenceMapping],
    ) -> Dict[str, Any]:
        """Apply the renumbering to the structure."""
        modified = copy.deepcopy(structure)

        # Get target list
        target_list = self._get_target_list(modified, operation)

        # Apply new sequences
        for mapping in mappings:
            if mapping.old_sequence != mapping.new_sequence:
                for item in target_list:
                    if item.get(operation.id_field) == mapping.element_id:
                        item[operation.sequence_field] = mapping.new_sequence
                        break

        return modified


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================


def demo_renumberer():
    """Demonstrate structure renumbering functionality."""
    print("=" * 70)
    print("STRUCTURE RENUMBERER LIBRARY - DEMO")
    print("=" * 70)

    renumberer = StructureRenumberer()

    # Example 1: COMPACT - Remove gaps
    print("\n📝 Example 1: COMPACT strategy (remove gaps)")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1, "name": "First"},
            {"id": "item2", "sequence": 2, "name": "Second"},
            {"id": "item3", "sequence": 5, "name": "Third"},  # Gap
            {"id": "item4", "sequence": 7, "name": "Fourth"},  # Gap
        ]
    }

    print("Before (has gaps):")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")

    operation = RenumberOperation(
        strategy=RenumberStrategy.COMPACT, element_path="items"
    )

    result = renumberer.renumber(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter (gaps removed):")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    # Example 2: SHIFT_UP - After insertion
    print("\n\n📝 Example 2: SHIFT_UP strategy (after inserting at sequence 3)")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1},
            {"id": "item2", "sequence": 2},
            {"id": "item3", "sequence": 3},
            {"id": "item4", "sequence": 4},
        ]
    }

    print("Before (preparing to insert at sequence 3):")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")

    operation = RenumberOperation(
        strategy=RenumberStrategy.SHIFT_UP, insertion_point=3, element_path="items"
    )

    result = renumberer.renumber(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter (sequences 3,4 shifted to 4,5 - ready for new item at 3):")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    # Example 3: SHIFT_DOWN - After deletion
    print("\n\n📝 Example 3: SHIFT_DOWN strategy (after deleting sequence 2)")
    print("-" * 70)

    structure = {
        "items": [
            {"id": "item1", "sequence": 1},
            {"id": "item3", "sequence": 3},  # item2 was deleted
            {"id": "item4", "sequence": 4},
        ]
    }

    print("Before (item2 was deleted, leaving gap):")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")

    operation = RenumberOperation(
        strategy=RenumberStrategy.SHIFT_DOWN, deletion_point=2, element_path="items"
    )

    result = renumberer.renumber(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter (sequences > 2 shifted down):")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    # Example 4: EXPLICIT - Custom reordering
    print("\n\n📝 Example 4: EXPLICIT strategy (custom sequence assignments)")
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

    operation = RenumberOperation(
        strategy=RenumberStrategy.EXPLICIT,
        explicit_mappings={"item1": 10, "item2": 20, "item3": 30},
        element_path="items",
    )

    result = renumberer.renumber(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter (custom sequences applied):")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")

    # Example 5: Nested structure
    print("\n\n📝 Example 5: COMPACT in nested structure (steps within phase)")
    print("-" * 70)

    structure = {
        "phases": [
            {
                "phase_id": "phase1",
                "sequence": 1,
                "steps": [
                    {"step_id": "step1", "sequence": 1},
                    {"step_id": "step2", "sequence": 3},  # Gap
                    {"step_id": "step3", "sequence": 5},  # Gap
                ],
            }
        ]
    }

    print("Before:")
    for phase in structure["phases"]:
        print(f"  Phase {phase['phase_id']}:")
        for step in phase.get("steps", []):
            print(f"    seq {step['sequence']}: {step['step_id']}")

    operation = RenumberOperation(
        strategy=RenumberStrategy.COMPACT,
        element_path="steps",
        id_field="step_id",
        parent_path="phases",
        parent_id="phase1",
        parent_id_field="phase_id",
    )

    result = renumberer.renumber(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")

    if result.success:
        print("\nAfter:")
        for phase in result.modified_structure["phases"]:
            print(f"  Phase {phase['phase_id']}:")
            for step in phase.get("steps", []):
                print(f"    seq {step['sequence']}: {step['step_id']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_renumberer()
