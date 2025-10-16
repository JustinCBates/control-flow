"""
Structure Insertion Library

Universal library for inserting elements into hierarchical list structures with sequence management.
Works on ANY nested data structure without domain coupling.

Author: Control Flow Engine Libraries
Date: 2025-01-XX
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
import copy


class InsertPosition(Enum):
    """Where to insert the new element."""
    BEFORE = "before"
    AFTER = "after"
    AT_SEQUENCE = "at_sequence"
    AT_END = "at_end"
    AT_START = "at_start"


@dataclass
class InsertionPoint:
    """Defines where to insert a new element."""
    position: InsertPosition
    reference_id: Optional[str] = None  # ID of element to insert before/after
    target_sequence: Optional[int] = None  # Explicit sequence number
    
    def __repr__(self):
        if self.position == InsertPosition.AT_SEQUENCE:
            return f"at sequence {self.target_sequence}"
        elif self.position in [InsertPosition.BEFORE, InsertPosition.AFTER]:
            return f"{self.position.value} element '{self.reference_id}'"
        else:
            return self.position.value


@dataclass
class SequenceMapping:
    """Maps an element's old sequence to its new sequence after insertion."""
    element_id: str
    old_sequence: Optional[int]
    new_sequence: int
    is_new_element: bool = False
    
    def __repr__(self):
        if self.is_new_element:
            return f"INSERT '{self.element_id}' at seq {self.new_sequence}"
        elif self.old_sequence != self.new_sequence:
            return f"RENUMBER '{self.element_id}': {self.old_sequence} → {self.new_sequence}"
        else:
            return f"PRESERVE '{self.element_id}' at seq {self.new_sequence}"


@dataclass
class InsertOperation:
    """Complete definition of an insertion operation."""
    new_element: Dict[str, Any]
    insertion_point: InsertionPoint
    cascade_renumber: bool = True
    element_path: str = "items"  # Path to list in structure (e.g., "items", "phases", "steps")
    id_field: str = "id"  # Field containing element ID
    sequence_field: str = "sequence"  # Field containing sequence number
    parent_path: Optional[str] = None  # Path to parent element if nested
    parent_id: Optional[str] = None  # ID of parent element if nested
    parent_id_field: Optional[str] = None  # Field containing parent ID (defaults to id_field)
    
    def __repr__(self):
        new_id = self.new_element.get(self.id_field, 'unknown')
        parent_info = f" in parent '{self.parent_id}'" if self.parent_id else ""
        return f"Insert '{new_id}' {self.insertion_point}{parent_info}"


@dataclass
class InsertResult:
    """Result of an insertion operation."""
    success: bool
    element_id: str
    insert_sequence: Optional[int] = None
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
            affected = len([m for m in self.mappings if m.old_sequence != m.new_sequence or m.is_new_element])
            return f"✅ INSERT SUCCESS: '{self.element_id}' at sequence {self.insert_sequence} (affected {affected} element{'s' if affected != 1 else ''})"
        else:
            return f"❌ INSERT FAILED: {', '.join(self.errors)}"


class InsertError(Exception):
    """Exception raised when insertion operation fails."""
    pass


class StructureInserter:
    """
    Universal structure insertion engine.
    
    Inserts new elements into hierarchical list structures while managing
    sequence numbers. Works on ANY data structure without domain knowledge.
    
    Example structure:
        {
            "items": [
                {"id": "item1", "sequence": 1, "name": "First"},
                {"id": "item2", "sequence": 2, "name": "Second"},
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
    
    def insert_element(
        self,
        structure: Dict[str, Any],
        operation: InsertOperation,
        dry_run: bool = False
    ) -> InsertResult:
        """
        Insert a new element into the structure.
        
        Args:
            structure: The hierarchical structure to modify
            operation: Complete insertion operation definition
            dry_run: If True, calculate changes without modifying structure
            
        Returns:
            InsertResult with success status, mappings, and modified structure
            
        Raises:
            InsertError: If operation is invalid or fails
        """
        try:
            # Validate operation
            self._validate_operation(operation)
            
            # Get target list
            target_list = self._get_target_list(structure, operation)
            if target_list is None:
                return InsertResult(
                    success=False,
                    element_id=operation.new_element.get(operation.id_field, 'unknown'),
                    errors=[f"Target list '{operation.element_path}' not found"]
                )
            
            # Determine insertion sequence
            insert_seq = self._calculate_insert_sequence(target_list, operation)
            if insert_seq is None:
                return InsertResult(
                    success=False,
                    element_id=operation.new_element.get(operation.id_field, 'unknown'),
                    errors=[f"Could not determine insertion sequence"]
                )
            
            # Calculate sequence mappings
            mappings = self._calculate_mappings(
                target_list,
                insert_seq,
                operation
            )
            
            # Apply changes if not dry run
            modified_structure = structure
            if not dry_run:
                modified_structure = self._apply_insertion(
                    structure,
                    operation,
                    insert_seq,
                    mappings
                )
            
            new_id = operation.new_element.get(operation.id_field, 'unknown')
            
            return InsertResult(
                success=True,
                element_id=new_id,
                insert_sequence=insert_seq,
                mappings=mappings,
                modified_structure=modified_structure if not dry_run else None
            )
            
        except Exception as e:
            return InsertResult(
                success=False,
                element_id=operation.new_element.get(operation.id_field, 'unknown'),
                errors=[str(e)]
            )
    
    def _validate_operation(self, operation: InsertOperation):
        """Validate the insertion operation."""
        # Check new element has required fields
        if operation.id_field not in operation.new_element:
            raise InsertError(f"New element missing required field '{operation.id_field}'")
        
        # Check insertion point is valid
        if operation.insertion_point.position == InsertPosition.AT_SEQUENCE:
            if operation.insertion_point.target_sequence is None:
                raise InsertError("AT_SEQUENCE position requires target_sequence")
        elif operation.insertion_point.position in [InsertPosition.BEFORE, InsertPosition.AFTER]:
            if not operation.insertion_point.reference_id:
                raise InsertError(f"{operation.insertion_point.position.value} position requires reference_id")
    
    def _get_target_list(
        self,
        structure: Dict[str, Any],
        operation: InsertOperation
    ) -> Optional[List[Dict[str, Any]]]:
        """Get the list to insert into."""
        # If inserting into nested structure
        if operation.parent_path and operation.parent_id:
            parent_list = structure.get(operation.parent_path, [])
            # Use parent_id_field if specified, otherwise use id_field
            parent_id_field = operation.parent_id_field or operation.id_field
            for parent in parent_list:
                if parent.get(parent_id_field) == operation.parent_id:
                    # Initialize element path if missing
                    if operation.element_path not in parent:
                        parent[operation.element_path] = []
                    return parent.get(operation.element_path)
            return None
        else:
            # Top-level insertion
            if operation.element_path not in structure:
                structure[operation.element_path] = []
            return structure.get(operation.element_path)
    
    def _calculate_insert_sequence(
        self,
        target_list: List[Dict[str, Any]],
        operation: InsertOperation
    ) -> Optional[int]:
        """Calculate the sequence number for the new element."""
        seq_field = operation.sequence_field
        
        if operation.insertion_point.position == InsertPosition.AT_END:
            if not target_list:
                return 1
            return max([item.get(seq_field, 0) for item in target_list]) + 1
        
        elif operation.insertion_point.position == InsertPosition.AT_START:
            return 1
        
        elif operation.insertion_point.position == InsertPosition.AT_SEQUENCE:
            return operation.insertion_point.target_sequence
        
        elif operation.insertion_point.position == InsertPosition.AFTER:
            for item in target_list:
                if item.get(operation.id_field) == operation.insertion_point.reference_id:
                    return item.get(seq_field, 0) + 1
            raise InsertError(f"Reference element '{operation.insertion_point.reference_id}' not found")
        
        elif operation.insertion_point.position == InsertPosition.BEFORE:
            for item in target_list:
                if item.get(operation.id_field) == operation.insertion_point.reference_id:
                    return item.get(seq_field, 0)
            raise InsertError(f"Reference element '{operation.insertion_point.reference_id}' not found")
        
        return None
    
    def _calculate_mappings(
        self,
        target_list: List[Dict[str, Any]],
        insert_seq: int,
        operation: InsertOperation
    ) -> List[SequenceMapping]:
        """Calculate sequence mappings for all affected elements."""
        mappings = []
        seq_field = operation.sequence_field
        id_field = operation.id_field
        
        # Add mapping for new element
        new_id = operation.new_element.get(id_field)
        mappings.append(SequenceMapping(
            element_id=new_id,
            old_sequence=None,
            new_sequence=insert_seq,
            is_new_element=True
        ))
        
        # Calculate renumber mappings if cascade enabled
        if operation.cascade_renumber:
            for item in target_list:
                item_seq = item.get(seq_field, 0)
                new_seq = item_seq + 1 if item_seq >= insert_seq else item_seq
                
                mappings.append(SequenceMapping(
                    element_id=item.get(id_field),
                    old_sequence=item_seq,
                    new_sequence=new_seq,
                    is_new_element=False
                ))
        else:
            # No cascade - preserve existing sequences
            for item in target_list:
                item_seq = item.get(seq_field, 0)
                mappings.append(SequenceMapping(
                    element_id=item.get(id_field),
                    old_sequence=item_seq,
                    new_sequence=item_seq,
                    is_new_element=False
                ))
        
        return mappings
    
    def _apply_insertion(
        self,
        structure: Dict[str, Any],
        operation: InsertOperation,
        insert_seq: int,
        mappings: List[SequenceMapping]
    ) -> Dict[str, Any]:
        """Apply the insertion to the structure."""
        modified = copy.deepcopy(structure)
        
        # Get target list
        target_list = self._get_target_list(modified, operation)
        
        # Apply renumbering to existing elements
        for mapping in mappings:
            if not mapping.is_new_element and mapping.old_sequence != mapping.new_sequence:
                for item in target_list:
                    if item.get(operation.id_field) == mapping.element_id:
                        item[operation.sequence_field] = mapping.new_sequence
        
        # Insert new element
        new_element = copy.deepcopy(operation.new_element)
        new_element[operation.sequence_field] = insert_seq
        target_list.append(new_element)
        
        # Sort by sequence (optional, but helps maintain order)
        target_list.sort(key=lambda x: x.get(operation.sequence_field, 0))
        
        return modified


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================

def demo_inserter():
    """Demonstrate structure insertion functionality."""
    print("=" * 70)
    print("STRUCTURE INSERTER LIBRARY - DEMO")
    print("=" * 70)
    
    inserter = StructureInserter()
    
    # Example 1: Insert at end
    print("\n📝 Example 1: Insert at end of list")
    print("-" * 70)
    
    structure = {
        "items": [
            {"id": "item1", "sequence": 1, "name": "First"},
            {"id": "item2", "sequence": 2, "name": "Second"},
            {"id": "item3", "sequence": 3, "name": "Third"}
        ]
    }
    
    print("Before:")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']} - {item['name']}")
    
    operation = InsertOperation(
        new_element={"id": "item4", "name": "Fourth"},
        insertion_point=InsertionPoint(position=InsertPosition.AT_END),
        element_path="items"
    )
    
    result = inserter.insert_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")
    
    if result.success:
        print("\nAfter:")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']} - {item.get('name', 'N/A')}")
    
    # Example 2: Insert after specific element with cascade
    print("\n\n📝 Example 2: Insert after 'item1' with cascade renumbering")
    print("-" * 70)
    
    structure = {
        "items": [
            {"id": "item1", "sequence": 1, "name": "First"},
            {"id": "item2", "sequence": 2, "name": "Second"},
            {"id": "item3", "sequence": 3, "name": "Third"}
        ]
    }
    
    print("Before:")
    for item in structure["items"]:
        print(f"  seq {item['sequence']}: {item['id']}")
    
    operation = InsertOperation(
        new_element={"id": "item_new", "name": "Inserted"},
        insertion_point=InsertionPoint(
            position=InsertPosition.AFTER,
            reference_id="item1"
        ),
        cascade_renumber=True,
        element_path="items"
    )
    
    result = inserter.insert_element(structure, operation)
    print(f"\n{result}")
    print("\nSequence Mappings:")
    for mapping in result.mappings:
        print(f"  {mapping}")
    
    if result.success:
        print("\nAfter:")
        for item in result.modified_structure["items"]:
            print(f"  seq {item['sequence']}: {item['id']}")
    
    # Example 3: Insert into nested structure
    print("\n\n📝 Example 3: Insert step into phase (nested structure)")
    print("-" * 70)
    
    structure = {
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
    
    print("Before:")
    for phase in structure["phases"]:
        print(f"  Phase {phase['phase_id']}:")
        for step in phase.get("steps", []):
            print(f"    seq {step['sequence']}: {step['step_id']}")
    
    operation = InsertOperation(
        new_element={"step_id": "step_new", "name": "New Step"},
        insertion_point=InsertionPoint(
            position=InsertPosition.BEFORE,
            reference_id="step2"
        ),
        element_path="steps",
        id_field="step_id",
        parent_path="phases",
        parent_id="phase1",
        parent_id_field="phase_id",
        cascade_renumber=True
    )
    
    result = inserter.insert_element(structure, operation, dry_run=False)
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
    demo_inserter()
