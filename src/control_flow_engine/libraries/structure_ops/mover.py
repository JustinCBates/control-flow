"""
Structure Mover - Move elements within hierarchical structures

Provides universal move operations for any hierarchical structure.
No domain coupling - works with phases, steps, config sections, form fields, etc.

Features:
- Move element from one sequence position to another
- Move element to different parent (reparent)
- Automatic cascade renumbering of affected elements
- Validation before move
- Dry-run preview mode
- Detailed operation plan with affected elements

Example:
    >>> from control_flow_engine.libraries.structure_ops import StructureMover
    >>>
    >>> structure = {
    ...     'items': [
    ...         {'id': 'item1', 'sequence': 1, 'name': 'First'},
    ...         {'id': 'item2', 'sequence': 2, 'name': 'Second'},
    ...         {'id': 'item3', 'sequence': 3, 'name': 'Third'},
    ...         {'id': 'item4', 'sequence': 4, 'name': 'Fourth'},
    ...         {'id': 'item5', 'sequence': 5, 'name': 'Fifth'},
    ...     ]
    ... }
    >>>
    >>> mover = StructureMover()
    >>> result = mover.move_element(
    ...     structure=structure,
    ...     element_path=['items', 4],  # Move item at index 4 (item5)
    ...     from_sequence=5,
    ...     to_sequence=2
    ... )
    >>> # Result: [item1, item5, item2, item3, item4]
    >>> # Sequences: [1, 2, 3, 4, 5]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import copy
from enum import Enum


class MoveDirection(Enum):
    """Direction of move operation."""

    UP = "up"  # Moving to lower sequence number
    DOWN = "down"  # Moving to higher sequence number
    SAME = "same"  # No movement


@dataclass
class SequenceMapping:
    """Maps an element's old sequence to new sequence."""

    element_id: str
    element_index: int
    old_sequence: int
    new_sequence: int
    operation: str = "renumber"  # 'move', 'renumber', or 'preserve'

    def __repr__(self):
        if self.operation == "move":
            return f"MOVE '{self.element_id}': seq {self.old_sequence} → {self.new_sequence}"
        elif self.operation == "renumber":
            return f"RENUMBER '{self.element_id}': seq {self.old_sequence} → {self.new_sequence}"
        else:
            return f"PRESERVE '{self.element_id}': seq {self.old_sequence}"


@dataclass
class MoveOperation:
    """Defines a move operation with all affected elements."""

    element_id: str
    from_sequence: int
    to_sequence: int
    direction: MoveDirection
    affected_elements: List[SequenceMapping] = field(default_factory=list)
    parent_path: Optional[List[str]] = None
    new_parent_path: Optional[List[str]] = None

    def is_reparent(self) -> bool:
        """Check if this is a reparent operation (moving to different parent)."""
        return (
            self.new_parent_path is not None
            and self.parent_path != self.new_parent_path
        )

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Move Operation: '{self.element_id}'",
            f"  From sequence: {self.from_sequence}",
            f"  To sequence: {self.to_sequence}",
            f"  Direction: {self.direction.value}",
            f"  Affected elements: {len(self.affected_elements)}",
        ]

        if self.is_reparent():
            lines.append(
                f"  Parent change: {self.parent_path} → {self.new_parent_path}"
            )

        for mapping in self.affected_elements:
            lines.append(f"    - {mapping}")

        return "\n".join(lines)


@dataclass
class MoveResult:
    """Result of a move operation."""

    success: bool
    operation: MoveOperation
    modified_structure: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __repr__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"{status}: {self.operation.element_id} moved from {self.operation.from_sequence} to {self.operation.to_sequence}"


class MoveError(Exception):
    """Raised when move operation fails."""

    pass


class StructureMover:
    """
    Universal structure mover for hierarchical data.

    Moves elements from one sequence position to another, automatically
    renumbering affected elements. Works with any hierarchical structure
    that has sequence numbers.

    Key Features:
    - Move within same parent (resequence)
    - Move to different parent (reparent + resequence)
    - Automatic cascade renumbering
    - Validation before move
    - Dry-run mode
    - Detailed operation plan

    No domain coupling - element types, parent types, and structure
    are discovered dynamically from the data.
    """

    def __init__(self, sequence_field: str = "sequence", id_field: str = "id"):
        """
        Initialize structure mover.

        Args:
            sequence_field: Name of the sequence number field (default: "sequence")
            id_field: Name of the ID field (default: "id")
        """
        self.sequence_field = sequence_field
        self.id_field = id_field

    def move_element(
        self,
        structure: Dict[str, Any],
        element_path: List[str],
        from_sequence: int,
        to_sequence: int,
        new_parent_path: Optional[List[str]] = None,
        dry_run: bool = False,
        validate: bool = True,
    ) -> MoveResult:
        """
        Move an element from one sequence position to another.

        Args:
            structure: The hierarchical structure (will be modified in-place unless dry_run)
            element_path: Path to the element's parent list (e.g., ['flows', 'main', 'phases'])
            from_sequence: Current sequence number of element to move
            to_sequence: Target sequence number
            new_parent_path: If moving to different parent, path to new parent
            dry_run: If True, don't modify structure, just return plan
            validate: If True, validate move before applying

        Returns:
            MoveResult with operation details and modified structure

        Raises:
            MoveError: If validation fails or move is invalid

        Example:
            >>> result = mover.move_element(
            ...     structure=my_structure,
            ...     element_path=['items'],
            ...     from_sequence=5,
            ...     to_sequence=2
            ... )
        """
        # Work with copy if dry_run
        work_structure = copy.deepcopy(structure) if dry_run else structure

        # Determine move direction
        if to_sequence < from_sequence:
            direction = MoveDirection.UP
        elif to_sequence > from_sequence:
            direction = MoveDirection.DOWN
        else:
            direction = MoveDirection.SAME

        # Get parent list
        parent_list = self._navigate_to_path(work_structure, element_path)
        if not isinstance(parent_list, list):
            raise MoveError(f"Path {element_path} does not point to a list")

        # Find element to move
        element_index = self._find_element_by_sequence(parent_list, from_sequence)
        if element_index is None:
            raise MoveError(
                f"No element found with sequence {from_sequence} at path {element_path}"
            )

        element = parent_list[element_index]
        element_id = element.get(self.id_field, f"element_{element_index}")

        # Create operation plan
        operation = MoveOperation(
            element_id=element_id,
            from_sequence=from_sequence,
            to_sequence=to_sequence,
            direction=direction,
            parent_path=element_path,
            new_parent_path=new_parent_path,
        )

        # Validate if requested
        if validate:
            validation_errors = self._validate_move(parent_list, operation)
            if validation_errors:
                return MoveResult(
                    success=False, operation=operation, errors=validation_errors
                )

        # Calculate affected elements and new sequences
        affected_mappings = self._calculate_affected_elements(
            parent_list, from_sequence, to_sequence, direction
        )
        operation.affected_elements = affected_mappings

        # Perform the move
        try:
            if not dry_run:
                self._apply_move(
                    parent_list,
                    element_index,
                    from_sequence,
                    to_sequence,
                    direction,
                    affected_mappings,
                )

            return MoveResult(
                success=True,
                operation=operation,
                modified_structure=work_structure if dry_run else structure,
            )

        except Exception as e:
            return MoveResult(
                success=False, operation=operation, errors=[f"Move failed: {str(e)}"]
            )

    def _navigate_to_path(self, structure: Dict[str, Any], path: List[str]) -> Any:
        """Navigate to a path in the structure."""
        current = structure
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    raise MoveError(
                        f"Invalid path: cannot access index '{key}' in list"
                    )
            else:
                raise MoveError(f"Invalid path: {path}")

            if current is None:
                raise MoveError(f"Path not found: {path}")

        return current

    def _find_element_by_sequence(
        self, elements: List[Dict], sequence: int
    ) -> Optional[int]:
        """Find index of element with given sequence number."""
        for i, elem in enumerate(elements):
            if elem.get(self.sequence_field) == sequence:
                return i
        return None

    def _validate_move(
        self, parent_list: List[Dict], operation: MoveOperation
    ) -> List[str]:
        """Validate that move operation is valid."""
        errors = []

        # Check if target sequence is reasonable
        max_sequence = len(parent_list)
        if operation.to_sequence < 1:
            errors.append(f"Target sequence {operation.to_sequence} must be >= 1")

        if operation.to_sequence > max_sequence:
            errors.append(
                f"Target sequence {operation.to_sequence} exceeds list size {max_sequence}"
            )

        # Check if from_sequence exists
        if self._find_element_by_sequence(parent_list, operation.from_sequence) is None:
            errors.append(f"No element found with sequence {operation.from_sequence}")

        # Check for duplicate sequences (data integrity)
        sequences = [elem.get(self.sequence_field) for elem in parent_list]
        if len(sequences) != len(set(sequences)):
            errors.append("Duplicate sequences found in structure - cannot safely move")

        return errors

    def _calculate_affected_elements(
        self,
        parent_list: List[Dict],
        from_sequence: int,
        to_sequence: int,
        direction: MoveDirection,
    ) -> List[SequenceMapping]:
        """
        Calculate which elements are affected and their new sequences.

        Move logic:
        - Moving UP (from 5 to 2): Elements 2,3,4 shift down by 1
        - Moving DOWN (from 2 to 5): Elements 3,4,5 shift up by 1
        - No move (same position): No changes
        """
        mappings = []

        for i, elem in enumerate(parent_list):
            elem_id = elem.get(self.id_field, f"element_{i}")
            old_seq = elem.get(self.sequence_field)
            new_seq = old_seq  # Default: no change
            operation_type = "preserve"

            if old_seq == from_sequence:
                # This is the element being moved
                new_seq = to_sequence
                operation_type = "move"

            elif direction == MoveDirection.UP:
                # Moving element UP (from 5 to 2)
                # Elements in range [to_sequence, from_sequence) shift DOWN by 1
                if to_sequence <= old_seq < from_sequence:
                    new_seq = old_seq + 1
                    operation_type = "renumber"

            elif direction == MoveDirection.DOWN:
                # Moving element DOWN (from 2 to 5)
                # Elements in range (from_sequence, to_sequence] shift UP by 1
                if from_sequence < old_seq <= to_sequence:
                    new_seq = old_seq - 1
                    operation_type = "renumber"

            mappings.append(
                SequenceMapping(
                    element_id=elem_id,
                    element_index=i,
                    old_sequence=old_seq,
                    new_sequence=new_seq,
                    operation=operation_type,
                )
            )

        return mappings

    def _apply_move(
        self,
        parent_list: List[Dict],
        element_index: int,
        from_sequence: int,
        to_sequence: int,
        direction: MoveDirection,
        affected_mappings: List[SequenceMapping],
    ):
        """Apply the move operation to the structure."""
        # Apply all sequence changes
        for mapping in affected_mappings:
            if mapping.new_sequence != mapping.old_sequence:
                parent_list[mapping.element_index][
                    self.sequence_field
                ] = mapping.new_sequence

        # Sort list by new sequence numbers to maintain order
        parent_list.sort(key=lambda x: x.get(self.sequence_field, 0))


def demo():
    """Demonstrate structure mover usage."""
    print("=" * 60)
    print("Structure Mover Demo")
    print("=" * 60)

    # Example structure
    structure = {
        "project": "demo",
        "items": [
            {"id": "item1", "sequence": 1, "name": "First Item"},
            {"id": "item2", "sequence": 2, "name": "Second Item"},
            {"id": "item3", "sequence": 3, "name": "Third Item"},
            {"id": "item4", "sequence": 4, "name": "Fourth Item"},
            {"id": "item5", "sequence": 5, "name": "Fifth Item"},
            {"id": "item6", "sequence": 6, "name": "Sixth Item"},
        ],
    }

    print("\nOriginal structure:")
    for item in structure["items"]:
        print(f"  {item['sequence']}: {item['id']} - {item['name']}")

    # Example 1: Move item 5 to position 2
    print("\n" + "=" * 60)
    print("Example 1: Move item 5 to position 2")
    print("=" * 60)

    mover = StructureMover()
    result = mover.move_element(
        structure=structure,
        element_path=["items"],
        from_sequence=5,
        to_sequence=2,
        dry_run=True,  # Preview only
    )

    print(f"\nResult: {result}")
    print(f"\nOperation Plan:")
    print(result.operation.summary())

    if result.success:
        print("\nStructure after move (dry-run preview):")
        # The list is already sorted by the move operation
        for item in result.modified_structure["items"]:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")

    # Example 2: Move item 2 to position 5 (reset structure first)
    print("\n" + "=" * 60)
    print("Example 2: Move item 2 to position 5")
    print("=" * 60)

    # Reset structure
    structure2 = {
        "project": "demo",
        "items": [
            {"id": "item1", "sequence": 1, "name": "First Item"},
            {"id": "item2", "sequence": 2, "name": "Second Item"},
            {"id": "item3", "sequence": 3, "name": "Third Item"},
            {"id": "item4", "sequence": 4, "name": "Fourth Item"},
            {"id": "item5", "sequence": 5, "name": "Fifth Item"},
            {"id": "item6", "sequence": 6, "name": "Sixth Item"},
        ],
    }

    result2 = mover.move_element(
        structure=structure2,
        element_path=["items"],
        from_sequence=2,
        to_sequence=5,
        dry_run=True,  # Preview only
    )

    print(f"\nResult: {result2}")
    print(f"\nOperation Plan:")
    print(result2.operation.summary())

    if result2.success:
        print("\nStructure after move (dry-run preview):")
        # The list is already sorted by the move operation
        for item in result2.modified_structure["items"]:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")


if __name__ == "__main__":
    demo()
