"""
Structure Swapper - Swap two elements in hierarchical structures

Provides universal swap operations for any hierarchical structure.
No domain coupling - works with phases, steps, config sections, form fields, etc.

Features:
- Swap positions of two elements by sequence number
- Validation before swap
- Dry-run preview mode
- Detailed operation report

Example:
    >>> from control_flow_engine.libraries.structure_ops import StructureSwapper
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
    >>> swapper = StructureSwapper()
    >>> result = swapper.swap_elements(
    ...     structure=structure,
    ...     element_path=['items'],
    ...     sequence_a=2,
    ...     sequence_b=5
    ... )
    >>> # Result: item2 and item5 swap positions
    >>> # Before: [1:item1, 2:item2, 3:item3, 4:item4, 5:item5]
    >>> # After:  [1:item1, 2:item5, 3:item3, 4:item4, 5:item2]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import copy


@dataclass
class SwapOperation:
    """Defines a swap operation between two elements."""

    element_a_id: str
    element_a_sequence: int
    element_b_id: str
    element_b_sequence: int
    parent_path: Optional[List[str]] = None

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Swap Operation:",
            f"  Element A: '{self.element_a_id}' (sequence {self.element_a_sequence})",
            f"  Element B: '{self.element_b_id}' (sequence {self.element_b_sequence})",
            f"  Result: A takes B's position, B takes A's position",
        ]

        if self.parent_path:
            lines.append(f"  Parent path: {self.parent_path}")

        return "\n".join(lines)


@dataclass
class SwapResult:
    """Result of a swap operation."""

    success: bool
    operation: Optional[SwapOperation] = None
    modified_structure: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __repr__(self):
        if self.success and self.operation:
            return (
                f"✅ SUCCESS: Swapped '{self.operation.element_a_id}' (seq {self.operation.element_a_sequence}) "
                f"with '{self.operation.element_b_id}' (seq {self.operation.element_b_sequence})"
            )
        else:
            return f"❌ FAILED: {', '.join(self.errors) if self.errors else 'Unknown error'}"


class SwapError(Exception):
    """Raised when swap operation fails."""

    pass


class StructureSwapper:
    """
    Universal structure swapper for hierarchical data.

    Swaps the sequence positions of two elements. Unlike move operations,
    swap is a simple exchange - element A takes element B's sequence number
    and vice versa. No other elements are affected.

    Key Features:
    - Direct swap of two elements
    - No cascade effects on other elements
    - Validation before swap
    - Dry-run mode
    - Detailed operation report

    No domain coupling - element types, parent types, and structure
    are discovered dynamically from the data.

    Example Use Cases:
    - Swap two phases in a workflow
    - Exchange positions of form fields
    - Reorder config sections
    - Any two elements in a sequence
    """

    def __init__(self, sequence_field: str = "sequence", id_field: str = "id"):
        """
        Initialize structure swapper.

        Args:
            sequence_field: Name of the sequence number field (default: "sequence")
            id_field: Name of the ID field (default: "id")
        """
        self.sequence_field = sequence_field
        self.id_field = id_field

    def swap_elements(
        self,
        structure: Dict[str, Any],
        element_path: List[str],
        sequence_a: int,
        sequence_b: int,
        dry_run: bool = False,
        validate: bool = True,
    ) -> SwapResult:
        """
        Swap two elements by their sequence numbers.

        Args:
            structure: The hierarchical structure (will be modified in-place unless dry_run)
            element_path: Path to the parent list containing the elements
            sequence_a: Sequence number of first element
            sequence_b: Sequence number of second element
            dry_run: If True, don't modify structure, just return plan
            validate: If True, validate swap before applying

        Returns:
            SwapResult with operation details and modified structure

        Raises:
            SwapError: If validation fails or swap is invalid

        Example:
            >>> result = swapper.swap_elements(
            ...     structure=my_structure,
            ...     element_path=['items'],
            ...     sequence_a=2,
            ...     sequence_b=5
            ... )
        """
        # Work with copy if dry_run
        work_structure = copy.deepcopy(structure) if dry_run else structure

        # Get parent list
        parent_list = self._navigate_to_path(work_structure, element_path)
        if not isinstance(parent_list, list):
            return SwapResult(
                success=False, errors=[f"Path {element_path} does not point to a list"]
            )

        # Find both elements
        index_a = self._find_element_by_sequence(parent_list, sequence_a)
        index_b = self._find_element_by_sequence(parent_list, sequence_b)

        if index_a is None:
            return SwapResult(
                success=False, errors=[f"No element found with sequence {sequence_a}"]
            )

        if index_b is None:
            return SwapResult(
                success=False, errors=[f"No element found with sequence {sequence_b}"]
            )

        # Get element details
        element_a = parent_list[index_a]
        element_b = parent_list[index_b]

        element_a_id = element_a.get(self.id_field, f"element_{index_a}")
        element_b_id = element_b.get(self.id_field, f"element_{index_b}")

        # Create operation
        operation = SwapOperation(
            element_a_id=element_a_id,
            element_a_sequence=sequence_a,
            element_b_id=element_b_id,
            element_b_sequence=sequence_b,
            parent_path=element_path,
        )

        # Validate if requested
        if validate:
            validation_errors = self._validate_swap(
                parent_list, operation, index_a, index_b
            )
            if validation_errors:
                return SwapResult(
                    success=False, operation=operation, errors=validation_errors
                )

        # Perform the swap
        try:
            if not dry_run:
                self._apply_swap(parent_list, index_a, index_b, sequence_a, sequence_b)

            return SwapResult(
                success=True,
                operation=operation,
                modified_structure=work_structure if dry_run else structure,
            )

        except Exception as e:
            return SwapResult(
                success=False, operation=operation, errors=[f"Swap failed: {str(e)}"]
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
                    raise SwapError(
                        f"Invalid path: cannot access index '{key}' in list"
                    )
            else:
                raise SwapError(f"Invalid path: {path}")

            if current is None:
                raise SwapError(f"Path not found: {path}")

        return current

    def _find_element_by_sequence(
        self, elements: List[Dict], sequence: int
    ) -> Optional[int]:
        """Find index of element with given sequence number."""
        for i, elem in enumerate(elements):
            if elem.get(self.sequence_field) == sequence:
                return i
        return None

    def _validate_swap(
        self,
        parent_list: List[Dict],
        operation: SwapOperation,
        index_a: int,
        index_b: int,
    ) -> List[str]:
        """Validate that swap operation is valid."""
        errors = []

        # Check if trying to swap with itself
        if operation.element_a_sequence == operation.element_b_sequence:
            errors.append("Cannot swap element with itself")

        # Check for duplicate sequences (data integrity)
        sequences = [elem.get(self.sequence_field) for elem in parent_list]
        if len(sequences) != len(set(sequences)):
            errors.append("Duplicate sequences found in structure - cannot safely swap")

        return errors

    def _apply_swap(
        self,
        parent_list: List[Dict],
        index_a: int,
        index_b: int,
        sequence_a: int,
        sequence_b: int,
    ):
        """Apply the swap operation to the structure."""
        # Simply swap the sequence numbers
        parent_list[index_a][self.sequence_field] = sequence_b
        parent_list[index_b][self.sequence_field] = sequence_a

        # Sort list by new sequence numbers to maintain order
        parent_list.sort(key=lambda x: x.get(self.sequence_field, 0))


def demo():
    """Demonstrate structure swapper usage."""
    print("=" * 60)
    print("Structure Swapper Demo")
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
        print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")

    # Example 1: Swap items 2 and 5
    print("\n" + "=" * 60)
    print("Example 1: Swap items at positions 2 and 5")
    print("=" * 60)

    swapper = StructureSwapper()
    result = swapper.swap_elements(
        structure=structure,
        element_path=["items"],
        sequence_a=2,
        sequence_b=5,
        dry_run=False,  # Actually modify
    )

    print(f"\nResult: {result}")
    print(f"\nOperation Plan:")
    print(result.operation.summary())

    if result.success:
        print("\nStructure after swap:")
        for item in structure["items"]:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")

    # Example 2: Swap items 1 and 6
    print("\n" + "=" * 60)
    print("Example 2: Swap items at positions 1 and 6")
    print("=" * 60)

    result2 = swapper.swap_elements(
        structure=structure,
        element_path=["items"],
        sequence_a=1,
        sequence_b=6,
        dry_run=False,  # Actually modify
    )

    print(f"\nResult: {result2}")
    print(f"\nOperation Plan:")
    print(result2.operation.summary())

    if result2.success:
        print("\nStructure after second swap:")
        for item in structure["items"]:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")

    # Example 3: Try invalid swap (same element)
    print("\n" + "=" * 60)
    print("Example 3: Try to swap element with itself (should fail)")
    print("=" * 60)

    result3 = swapper.swap_elements(
        structure=structure,
        element_path=["items"],
        sequence_a=3,
        sequence_b=3,
        dry_run=True,
    )

    print(f"\nResult: {result3}")
    if result3.errors:
        print(f"Errors: {', '.join(result3.errors)}")


if __name__ == "__main__":
    demo()
