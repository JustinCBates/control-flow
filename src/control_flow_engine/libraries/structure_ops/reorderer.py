"""
Structure Reorderer - Batch reorder elements in hierarchical structures

Provides universal batch reordering for any hierarchical structure.
No domain coupling - works with phases, steps, config sections, form fields, etc.

Features:
- Reorder multiple elements in one operation
- Specify new sequence order as a list
- Automatic validation of new order
- Dry-run preview mode
- Detailed operation report with all changes

Example:
    >>> from control_flow_engine.libraries.structure_ops import StructureReorderer
    >>> 
    >>> structure = {
    ...     'items': [
    ...         {'id': 'item1', 'sequence': 1},
    ...         {'id': 'item2', 'sequence': 2},
    ...         {'id': 'item3', 'sequence': 3},
    ...         {'id': 'item4', 'sequence': 4},
    ...         {'id': 'item5', 'sequence': 5},
    ...     ]
    ... }
    >>> 
    >>> reorderer = StructureReorderer()
    >>> result = reorderer.reorder_elements(
    ...     structure=structure,
    ...     element_path=['items'],
    ...     new_order=[3, 1, 4, 2, 5]  # New sequence: item3, item1, item4, item2, item5
    ... )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import copy


@dataclass
class ReorderMapping:
    """Maps an element's old sequence to new sequence."""
    element_id: str
    element_index: int
    old_sequence: int
    new_sequence: int
    
    def __repr__(self):
        if self.old_sequence != self.new_sequence:
            return f"REORDER '{self.element_id}': seq {self.old_sequence} → {self.new_sequence}"
        else:
            return f"PRESERVE '{self.element_id}': seq {self.old_sequence}"


@dataclass
class ReorderOperation:
    """Defines a batch reorder operation."""
    original_order: List[int]
    new_order: List[int]
    mappings: List[ReorderMapping] = field(default_factory=list)
    parent_path: Optional[List[str]] = None
    
    def affected_count(self) -> int:
        """Count how many elements changed position."""
        return sum(1 for m in self.mappings if m.old_sequence != m.new_sequence)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Reorder Operation:",
            f"  Original order: {self.original_order}",
            f"  New order: {self.new_order}",
            f"  Elements affected: {self.affected_count()}/{len(self.mappings)}",
        ]
        
        if self.parent_path:
            lines.append(f"  Parent path: {self.parent_path}")
        
        lines.append("\nMappings:")
        for mapping in self.mappings:
            if mapping.old_sequence != mapping.new_sequence:
                lines.append(f"    {mapping}")
        
        return "\n".join(lines)


@dataclass
class ReorderResult:
    """Result of a reorder operation."""
    success: bool
    operation: Optional[ReorderOperation] = None
    modified_structure: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __repr__(self):
        if self.success and self.operation:
            affected = self.operation.affected_count()
            total = len(self.operation.mappings)
            return f"✅ SUCCESS: Reordered {affected}/{total} elements"
        else:
            return f"❌ FAILED: {', '.join(self.errors) if self.errors else 'Unknown error'}"


class ReorderError(Exception):
    """Raised when reorder operation fails."""
    pass


class StructureReorderer:
    """
    Universal structure reorderer for hierarchical data.
    
    Reorders multiple elements in a single operation by specifying the
    desired final sequence. This is more efficient than multiple individual
    move operations when you know the final desired order.
    
    Key Features:
    - Batch reorder in single operation
    - Specify final order as list of sequence numbers
    - Automatic validation of new order
    - Dry-run mode
    - Detailed mapping of all changes
    
    No domain coupling - element types, parent types, and structure
    are discovered dynamically from the data.
    
    Example Use Cases:
    - Reorganize workflow phases based on user input
    - Reorder form fields after drag-and-drop
    - Rearrange config sections
    - Any batch sequence modification
    """
    
    def __init__(self, sequence_field: str = "sequence", id_field: str = "id"):
        """
        Initialize structure reorderer.
        
        Args:
            sequence_field: Name of the sequence number field (default: "sequence")
            id_field: Name of the ID field (default: "id")
        """
        self.sequence_field = sequence_field
        self.id_field = id_field
    
    def reorder_elements(
        self,
        structure: Dict[str, Any],
        element_path: List[str],
        new_order: List[int],
        dry_run: bool = False,
        validate: bool = True
    ) -> ReorderResult:
        """
        Reorder elements to match the specified sequence.
        
        Args:
            structure: The hierarchical structure (will be modified in-place unless dry_run)
            element_path: Path to the parent list containing the elements
            new_order: List of sequence numbers in desired final order
                      Example: [3, 1, 4, 2, 5] means:
                        - Item with sequence 3 becomes position 1
                        - Item with sequence 1 becomes position 2
                        - Item with sequence 4 becomes position 3
                        - etc.
            dry_run: If True, don't modify structure, just return plan
            validate: If True, validate reorder before applying
            
        Returns:
            ReorderResult with operation details and modified structure
            
        Raises:
            ReorderError: If validation fails or reorder is invalid
            
        Example:
            >>> # Reorder [1,2,3,4,5] to [3,1,4,2,5]
            >>> result = reorderer.reorder_elements(
            ...     structure=my_structure,
            ...     element_path=['items'],
            ...     new_order=[3, 1, 4, 2, 5]
            ... )
        """
        # Work with copy if dry_run
        work_structure = copy.deepcopy(structure) if dry_run else structure
        
        # Get parent list
        parent_list = self._navigate_to_path(work_structure, element_path)
        if not isinstance(parent_list, list):
            return ReorderResult(
                success=False,
                errors=[f"Path {element_path} does not point to a list"]
            )
        
        # Get original order
        original_sequences = [elem.get(self.sequence_field) for elem in parent_list]
        original_order = sorted(original_sequences)
        
        # Create operation
        operation = ReorderOperation(
            original_order=original_order,
            new_order=new_order,
            parent_path=element_path
        )
        
        # Validate if requested
        if validate:
            validation_errors = self._validate_reorder(parent_list, operation)
            if validation_errors:
                return ReorderResult(
                    success=False,
                    operation=operation,
                    errors=validation_errors
                )
        
        # Calculate mappings
        mappings = self._calculate_mappings(parent_list, new_order)
        operation.mappings = mappings
        
        # Perform the reorder
        try:
            if not dry_run:
                self._apply_reorder(parent_list, mappings)
            
            return ReorderResult(
                success=True,
                operation=operation,
                modified_structure=work_structure if dry_run else structure
            )
            
        except Exception as e:
            return ReorderResult(
                success=False,
                operation=operation,
                errors=[f"Reorder failed: {str(e)}"]
            )
    
    def reorder_by_ids(
        self,
        structure: Dict[str, Any],
        element_path: List[str],
        id_order: List[str],
        dry_run: bool = False,
        validate: bool = True
    ) -> ReorderResult:
        """
        Reorder elements by specifying the desired ID order.
        
        This is a convenience method that converts ID order to sequence order.
        
        Args:
            structure: The hierarchical structure
            element_path: Path to the parent list
            id_order: List of element IDs in desired final order
            dry_run: If True, don't modify structure
            validate: If True, validate before applying
            
        Returns:
            ReorderResult with operation details
            
        Example:
            >>> result = reorderer.reorder_by_ids(
            ...     structure=my_structure,
            ...     element_path=['items'],
            ...     id_order=['item3', 'item1', 'item4', 'item2', 'item5']
            ... )
        """
        # Get parent list
        work_structure = copy.deepcopy(structure) if dry_run else structure
        parent_list = self._navigate_to_path(work_structure, element_path)
        
        if not isinstance(parent_list, list):
            return ReorderResult(
                success=False,
                errors=[f"Path {element_path} does not point to a list"]
            )
        
        # Convert ID order to sequence order
        id_to_sequence = {
            elem.get(self.id_field): elem.get(self.sequence_field)
            for elem in parent_list
        }
        
        try:
            new_order = [id_to_sequence[elem_id] for elem_id in id_order]
        except KeyError as e:
            return ReorderResult(
                success=False,
                errors=[f"Unknown element ID in id_order: {e}"]
            )
        
        # Use regular reorder with sequence order
        return self.reorder_elements(
            structure=work_structure if dry_run else structure,
            element_path=element_path,
            new_order=new_order,
            dry_run=dry_run,
            validate=validate
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
                    raise ReorderError(f"Invalid path: cannot access index '{key}' in list")
            else:
                raise ReorderError(f"Invalid path: {path}")
            
            if current is None:
                raise ReorderError(f"Path not found: {path}")
        
        return current
    
    def _validate_reorder(
        self,
        parent_list: List[Dict],
        operation: ReorderOperation
    ) -> List[str]:
        """Validate that reorder operation is valid."""
        errors = []
        
        # Check that new_order has correct length
        if len(operation.new_order) != len(parent_list):
            errors.append(
                f"new_order length ({len(operation.new_order)}) "
                f"does not match list length ({len(parent_list)})"
            )
        
        # Check that new_order contains all original sequences
        original_set = set(operation.original_order)
        new_set = set(operation.new_order)
        
        if original_set != new_set:
            missing = original_set - new_set
            extra = new_set - original_set
            if missing:
                errors.append(f"new_order missing sequences: {sorted(missing)}")
            if extra:
                errors.append(f"new_order has invalid sequences: {sorted(extra)}")
        
        # Check for duplicates in new_order
        if len(operation.new_order) != len(set(operation.new_order)):
            errors.append("new_order contains duplicate sequences")
        
        return errors
    
    def _calculate_mappings(
        self,
        parent_list: List[Dict],
        new_order: List[int]
    ) -> List[ReorderMapping]:
        """Calculate how each element's sequence will change."""
        mappings = []
        
        # Create mapping of old_sequence -> element
        old_seq_to_elem = {
            elem.get(self.sequence_field): (i, elem)
            for i, elem in enumerate(parent_list)
        }
        
        # For each position in new order, assign new sequence
        for new_seq_pos, old_seq in enumerate(new_order, start=1):
            elem_index, elem = old_seq_to_elem[old_seq]
            elem_id = elem.get(self.id_field, f"element_{elem_index}")
            
            mappings.append(ReorderMapping(
                element_id=elem_id,
                element_index=elem_index,
                old_sequence=old_seq,
                new_sequence=new_seq_pos
            ))
        
        return mappings
    
    def _apply_reorder(self, parent_list: List[Dict], mappings: List[ReorderMapping]):
        """Apply the reorder operation to the structure."""
        # Update all sequence numbers
        for mapping in mappings:
            parent_list[mapping.element_index][self.sequence_field] = mapping.new_sequence
        
        # Sort list by new sequence numbers
        parent_list.sort(key=lambda x: x.get(self.sequence_field, 0))


def demo():
    """Demonstrate structure reorderer usage."""
    print("=" * 60)
    print("Structure Reorderer Demo")
    print("=" * 60)
    
    # Example structure
    structure = {
        'project': 'demo',
        'items': [
            {'id': 'item1', 'sequence': 1, 'name': 'First Item'},
            {'id': 'item2', 'sequence': 2, 'name': 'Second Item'},
            {'id': 'item3', 'sequence': 3, 'name': 'Third Item'},
            {'id': 'item4', 'sequence': 4, 'name': 'Fourth Item'},
            {'id': 'item5', 'sequence': 5, 'name': 'Fifth Item'},
        ]
    }
    
    print("\nOriginal structure:")
    for item in structure['items']:
        print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")
    
    # Example 1: Reorder to [3, 1, 4, 2, 5]
    print("\n" + "=" * 60)
    print("Example 1: Reorder to [3, 1, 4, 2, 5]")
    print("(item3 first, then item1, then item4, then item2, then item5)")
    print("=" * 60)
    
    reorderer = StructureReorderer()
    result = reorderer.reorder_elements(
        structure=structure,
        element_path=['items'],
        new_order=[3, 1, 4, 2, 5],
        dry_run=False  # Actually modify
    )
    
    print(f"\nResult: {result}")
    print(f"\nOperation Plan:")
    print(result.operation.summary())
    
    if result.success:
        print("\nStructure after reorder:")
        for item in structure['items']:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")
    
    # Example 2: Reorder by IDs
    print("\n" + "=" * 60)
    print("Example 2: Reorder by ID list")
    print("['item5', 'item3', 'item1', 'item2', 'item4']")
    print("=" * 60)
    
    # Reset structure
    structure2 = {
        'items': [
            {'id': 'item1', 'sequence': 1, 'name': 'First Item'},
            {'id': 'item2', 'sequence': 2, 'name': 'Second Item'},
            {'id': 'item3', 'sequence': 3, 'name': 'Third Item'},
            {'id': 'item4', 'sequence': 4, 'name': 'Fourth Item'},
            {'id': 'item5', 'sequence': 5, 'name': 'Fifth Item'},
        ]
    }
    
    result2 = reorderer.reorder_by_ids(
        structure=structure2,
        element_path=['items'],
        id_order=['item5', 'item3', 'item1', 'item2', 'item4'],
        dry_run=False
    )
    
    print(f"\nResult: {result2}")
    
    if result2.success:
        print("\nStructure after reorder by ID:")
        for item in structure2['items']:
            print(f"  Seq {item['sequence']}: {item['id']} - {item['name']}")
    
    # Example 3: Invalid reorder (wrong length)
    print("\n" + "=" * 60)
    print("Example 3: Try invalid reorder (should fail)")
    print("=" * 60)
    
    result3 = reorderer.reorder_elements(
        structure=structure,
        element_path=['items'],
        new_order=[1, 2, 3],  # Wrong length
        dry_run=True
    )
    
    print(f"\nResult: {result3}")
    if result3.errors:
        print(f"Errors: {', '.join(result3.errors)}")


if __name__ == "__main__":
    demo()
