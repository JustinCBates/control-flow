# Control-Flow Internal Library Architecture

**Date**: 2025-10-16  
**Purpose**: Reorganize control-flow as a standalone universal tool with clean separation between core engine libraries and application-specific components.

## Vision

Control-flow should be a **universal control flow management tool** applicable to **any project** that needs multi-phase workflow orchestration. The current codebase mixes universal library functionality with control-flow-specific application code. This proposal separates them into:

1. **Core Engine Libraries** - Universal, reusable units with no control-flow specifics
2. **Application Layer** - Control-flow-specific orchestration using the core libraries

## Current State Analysis

### Total Codebase: ~11,600 LOC

**Mixed Concerns**:
- YAML I/O mixed with control-flow business logic
- Structure manipulation (move, insert, delete) tightly coupled to transformation system
- Universal path resolution mixed with control-flow-specific artifact handling
- Reusable UI components mixed with control-flow-specific menus

## Proposed Architecture

```
control-flow/
├── src/
│   ├── control_flow_engine/
│   │   ├── libraries/                    # CORE ENGINE (Universal)
│   │   │   ├── yaml_ops/                 # Library 1: YAML Operations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── reader.py
│   │   │   │   ├── writer.py
│   │   │   │   ├── validator.py
│   │   │   │   └── schema.py
│   │   │   │
│   │   │   ├── structure_ops/            # Library 2: Structure Manipulation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── inserter.py           # Insert elements
│   │   │   │   ├── deleter.py            # Delete elements
│   │   │   │   ├── mover.py              # Move elements (NEW)
│   │   │   │   ├── renumberer.py         # Renumber sequences
│   │   │   │   ├── swapper.py            # Swap elements (NEW)
│   │   │   │   └── reorderer.py          # Batch reorder (NEW)
│   │   │   │
│   │   │   ├── sequence_ops/             # Library 3: Sequence Management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── gap_handler.py        # Handle gaps in sequences
│   │   │   │   ├── compactor.py          # Compact sequences
│   │   │   │   └── validator.py          # Validate sequence integrity
│   │   │   │
│   │   │   ├── planning/                 # Library 4: Operation Planning
│   │   │   │   ├── __init__.py
│   │   │   │   ├── planner.py            # Create transformation plans
│   │   │   │   ├── validator.py          # Validate plans
│   │   │   │   └── preview.py            # Preview plan effects
│   │   │   │
│   │   │   ├── history/                  # Library 5: Change History
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tracker.py            # Track changes
│   │   │   │   ├── rollback.py           # Rollback operations
│   │   │   │   └── checksum.py           # File checksums
│   │   │   │
│   │   │   ├── filesystem_sync/          # Library 6: Filesystem Sync
│   │   │   │   ├── __init__.py
│   │   │   │   ├── directory_ops.py      # Directory create/rename/delete
│   │   │   │   ├── code_updater.py       # Update import paths
│   │   │   │   └── doc_updater.py        # Update documentation
│   │   │   │
│   │   │   ├── path_resolution/          # Library 7: Path Resolution
│   │   │   │   ├── __init__.py
│   │   │   │   ├── resolver.py           # Resolve paths from specs
│   │   │   │   ├── detector.py           # Auto-detect project root
│   │   │   │   └── artifact_mapper.py    # Map artifacts to paths
│   │   │   │
│   │   │   ├── interactive_ui/           # Library 8: Interactive UI
│   │   │   │   ├── __init__.py
│   │   │   │   ├── terminal_compat.py    # Terminal compatibility layer
│   │   │   │   ├── menu_builder.py       # Build menus
│   │   │   │   ├── tree_navigator.py     # Navigate hierarchies
│   │   │   │   └── styles.py             # UI styling
│   │   │   │
│   │   │   └── code_generation/          # Library 9: Code Generation
│   │   │       ├── __init__.py
│   │   │       ├── template_engine.py    # Template rendering
│   │   │       ├── scaffolder.py         # Generate scaffolding
│   │   │       └── orchestrator_gen.py   # Generate orchestrators
│   │   │
│   │   ├── core/                         # APPLICATION LAYER (Control-Flow Specific)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                 # Control flow execution engine
│   │   │   ├── transformation.py         # Orchestrates libraries for CF transformations
│   │   │   ├── designer.py               # High-level design API
│   │   │   └── analyzer.py               # Control flow analysis
│   │   │
│   │   ├── ui/                           # APPLICATION LAYER
│   │   │   ├── __init__.py
│   │   │   └── flow_editor.py            # Control-flow-specific editor
│   │   │
│   │   ├── cli/                          # APPLICATION LAYER
│   │   │   ├── __init__.py
│   │   │   └── commands.py               # CLI commands
│   │   │
│   │   └── visualizer/                   # APPLICATION LAYER
│   │       ├── __init__.py
│   │       ├── graphviz_generator.py
│   │       └── web_server.py
│   │
│   └── tests/
│       ├── libraries/                     # Library unit tests
│       │   ├── test_yaml_ops/
│       │   ├── test_structure_ops/
│       │   ├── test_sequence_ops/
│       │   └── ...
│       └── integration/                   # Application integration tests
│
└── docs/
    ├── libraries/                         # Library documentation
    │   ├── YAML_OPS.md
    │   ├── STRUCTURE_OPS.md
    │   └── ...
    └── ARCHITECTURE.md
```

---

## Core Engine Libraries (Universal)

### Library 1: YAML Operations (yaml_ops/)

**Purpose**: Universal YAML read/write/validate operations with no domain knowledge.

**Current Location**: Mixed in `core/transformation.py` (lines 1-500)

**Components**:
- `YAMLReader` - Safe YAML loading with error handling
- `YAMLWriter` - Safe YAML writing with formatting preservation
- `YAMLValidator` - Schema validation
- `YAMLSchema` - Define expected structure

**API Example**:
```python
from control_flow_engine.libraries.yaml_ops import YAMLReader, YAMLWriter, YAMLValidator

# Read YAML
reader = YAMLReader(file_path="spec.yml")
data = reader.load()

# Validate
validator = YAMLValidator(schema_type="hierarchical_list")
result = validator.validate(data)

# Write YAML
writer = YAMLWriter(file_path="spec.yml", preserve_formatting=True)
writer.save(data)
```

**Universal Applicability**: Any project reading/writing YAML configurations.

**LOC Estimate**: 300-400 lines

---

### Library 2: Structure Manipulation (structure_ops/)

**Purpose**: Universal operations for manipulating hierarchical structures (insert, delete, move, renumber, swap, reorder).

**Current Location**: 
- `core/transformation.py` (lines 500-2000) - INSERT, DELETE operations
- `tools/renumberer.py` (lines 1-800) - RENUMBER operation
- **MISSING**: MOVE, SWAP, REORDER operations

**Components**:

#### `inserter.py` - Insert Operations
```python
class StructureInserter:
    """Insert elements into hierarchical structures."""
    
    def insert_element(
        self,
        structure: Dict,
        element: Dict,
        parent_path: Optional[List[str]] = None,
        position: Optional[int] = None,
        cascade_renumber: bool = False
    ) -> InsertionResult:
        """
        Insert element at position in structure.
        
        Args:
            structure: The hierarchical structure (dict/list)
            element: Element to insert
            parent_path: Path to parent (e.g., ['flows', 'main', 'phases'])
            position: Sequence number for insertion
            cascade_renumber: Whether to renumber following elements
            
        Returns:
            InsertionResult with modified structure and metadata
        """
```

#### `deleter.py` - Delete Operations
```python
class StructureDeleter:
    """Delete elements from hierarchical structures."""
    
    def delete_element(
        self,
        structure: Dict,
        element_path: List[str],
        cascade_renumber: bool = True,
        preserve_gaps: bool = False
    ) -> DeletionResult:
        """
        Delete element from structure.
        
        Args:
            structure: The hierarchical structure
            element_path: Full path to element
            cascade_renumber: Whether to renumber after deletion
            preserve_gaps: Keep gap in sequence or compact
            
        Returns:
            DeletionResult with modified structure and metadata
        """
```

#### `mover.py` - Move Operations (NEW)
```python
class StructureMover:
    """Move elements within hierarchical structures."""
    
    def move_element(
        self,
        structure: Dict,
        element_path: List[str],
        from_sequence: int,
        to_sequence: int,
        new_parent_path: Optional[List[str]] = None
    ) -> MoveResult:
        """
        Move element from one position to another.
        
        Handles:
        - Move within same parent (resequence)
        - Move to different parent (reparent + resequence)
        - Cascade renumbering of affected elements
        
        Example:
            Move phase 5 to position 2:
            [1, 2, 3, 4, 5, 6] → [1, 5, 2, 3, 4, 6]
            
        Args:
            structure: The hierarchical structure
            element_path: Path to element to move
            from_sequence: Current sequence number
            to_sequence: Target sequence number
            new_parent_path: If moving to different parent
            
        Returns:
            MoveResult with modified structure and renumber plan
        """
```

#### `renumberer.py` - Renumber Operations
```python
class SequenceRenumberer:
    """Renumber sequences in hierarchical structures."""
    
    def renumber_sequence(
        self,
        structure: Dict,
        parent_path: List[str],
        strategy: NumberingStrategy = NumberingStrategy.COMPACT
    ) -> RenumberResult:
        """
        Renumber all elements in a sequence.
        
        Strategies:
        - COMPACT: Remove gaps (1,3,5,7 → 1,2,3,4)
        - PRESERVE_GAPS: Keep gaps
        - MINIMAL_SHIFT: Only shift what's necessary
        
        Args:
            structure: The hierarchical structure
            parent_path: Path to parent containing sequence
            strategy: Renumbering strategy
            
        Returns:
            RenumberResult with mapping of old to new sequences
        """
```

#### `swapper.py` - Swap Operations (NEW)
```python
class StructureSwapper:
    """Swap two elements in hierarchical structures."""
    
    def swap_elements(
        self,
        structure: Dict,
        element_a_path: List[str],
        element_b_path: List[str]
    ) -> SwapResult:
        """
        Swap positions of two elements.
        
        Example:
            Swap positions 2 and 5:
            [1, 2, 3, 4, 5, 6] → [1, 5, 3, 4, 2, 6]
            
        Args:
            structure: The hierarchical structure
            element_a_path: Path to first element
            element_b_path: Path to second element
            
        Returns:
            SwapResult with modified structure
        """
```

#### `reorderer.py` - Batch Reorder (NEW)
```python
class StructureReorderer:
    """Batch reorder elements in hierarchical structures."""
    
    def reorder_elements(
        self,
        structure: Dict,
        parent_path: List[str],
        new_order: List[int]
    ) -> ReorderResult:
        """
        Reorder multiple elements in one operation.
        
        Example:
            Reorder [1,2,3,4,5] to [3,1,4,2,5]:
            new_order = [3, 1, 4, 2, 5]
            
        Args:
            structure: The hierarchical structure
            parent_path: Path to parent containing elements
            new_order: New sequence order
            
        Returns:
            ReorderResult with modified structure and full mapping
        """
```

**Universal Applicability**: Any project with hierarchical data structures (JSON, YAML, XML).

**LOC Estimate**: 800-1000 lines total
- inserter.py: 150
- deleter.py: 150
- mover.py: 200 (NEW)
- renumberer.py: 200
- swapper.py: 100 (NEW)
- reorderer.py: 200 (NEW)

---

### Library 3: Sequence Management (sequence_ops/)

**Purpose**: Universal sequence integrity and gap management.

**Current Location**: `tools/renumberer.py` (lines 1-200)

**Components**:
- `GapHandler` - Detect and handle gaps in sequences
- `SequenceCompactor` - Compact sequences to remove gaps
- `SequenceValidator` - Validate sequence integrity (no duplicates, continuous, etc.)

**API Example**:
```python
from control_flow_engine.libraries.sequence_ops import GapHandler, SequenceValidator

# Detect gaps
handler = GapHandler()
gaps = handler.find_gaps([1, 2, 5, 7, 9])  # Returns [3, 4, 6, 8]

# Validate sequence
validator = SequenceValidator()
result = validator.validate([1, 2, 3, 4, 5])  # Returns ValidationResult
```

**Universal Applicability**: Any project with numbered sequences.

**LOC Estimate**: 200-300 lines

---

### Library 4: Operation Planning (planning/)

**Purpose**: Universal plan-validate-apply pattern for structural changes.

**Current Location**: `core/transformation.py` (lines 100-400)

**Components**:
- `OperationPlanner` - Create plans for operations
- `PlanValidator` - Validate plans before execution
- `PlanPreviewer` - Preview plan effects without applying

**API Example**:
```python
from control_flow_engine.libraries.planning import OperationPlanner, PlanValidator

# Create plan
planner = OperationPlanner()
plan = planner.plan_move(
    from_sequence=5,
    to_sequence=2,
    affected_elements=[2, 3, 4, 5]
)

# Validate
validator = PlanValidator()
result = validator.validate(plan)

if result.valid:
    plan.execute()
```

**Universal Applicability**: Any project needing safe, validated operations.

**LOC Estimate**: 400-500 lines

---

### Library 5: Change History (history/)

**Purpose**: Universal change tracking and rollback.

**Current Location**: `core/transformation.py` (lines 150-350)

**Components**:
- `ChangeTracker` - Track all modifications
- `RollbackManager` - Rollback changes
- `ChecksumCalculator` - Calculate file checksums

**API Example**:
```python
from control_flow_engine.libraries.history import ChangeTracker, RollbackManager

# Track change
tracker = ChangeTracker(history_file=".changes.json")
tracker.record(
    operation="move",
    before=before_state,
    after=after_state
)

# Rollback
rollback = RollbackManager(history_file=".changes.json")
rollback.undo_last()
```

**Universal Applicability**: Any project needing change tracking.

**LOC Estimate**: 300-400 lines

---

### Library 6: Filesystem Sync (filesystem_sync/)

**Purpose**: Universal filesystem operations synchronized with structural changes.

**Current Location**: 
- `core/transformation.py` (DirectorySynchronizer - lines 700-1200)
- `tools/renumberer.py` (directory operations - lines 200-600)

**Components**:
- `DirectoryOperations` - Create, rename, delete directories
- `CodeUpdater` - Update import paths in code files
- `DocUpdater` - Update references in documentation

**API Example**:
```python
from control_flow_engine.libraries.filesystem_sync import DirectoryOperations, CodeUpdater

# Sync directories to structure changes
dir_ops = DirectoryOperations(base_path="/project")
dir_ops.rename_directory(
    old_name="phase_5_validation",
    new_name="phase_2_validation"
)

# Update code imports
code_updater = CodeUpdater(project_root="/project")
code_updater.update_imports(
    old_path="phase_5_validation",
    new_path="phase_2_validation"
)
```

**Universal Applicability**: Any project with code and docs that reference structural elements.

**LOC Estimate**: 600-700 lines

---

### Library 7: Path Resolution (path_resolution/)

**Purpose**: Universal path resolution from specifications.

**Current Location**: `runtime/path_resolver.py` (all 449 lines)

**Components**:
- `PathResolver` - Resolve paths from specs
- `ProjectRootDetector` - Auto-detect project root
- `ArtifactMapper` - Map artifacts to filesystem paths

**API Example**:
```python
from control_flow_engine.libraries.path_resolution import PathResolver

# Auto-detect and resolve
resolver = PathResolver.from_execution_context(__file__)
artifact_path = resolver.resolve_path(
    artifact_id="user_config",
    spec_file="specs/control_flows.yml"
)
```

**Universal Applicability**: Any multi-file project with artifact dependencies.

**LOC Estimate**: 450 lines (existing code is already universal)

---

### Library 8: Interactive UI (interactive_ui/)

**Purpose**: Universal terminal UI components with compatibility handling.

**Current Location**: `ui/flow_editor.py` (lines 1-300 - reusable UI patterns)

**Components**:
- `TerminalCompatibility` - Detect terminal type, handle limitations
- `MenuBuilder` - Build interactive menus
- `TreeNavigator` - Navigate hierarchical structures
- `StyleManager` - Manage UI styling

**API Example**:
```python
from control_flow_engine.libraries.interactive_ui import MenuBuilder, TerminalCompatibility

# Build menu with auto-compat
compat = TerminalCompatibility()
menu = MenuBuilder(compatibility=compat)

choice = menu.select(
    message="Choose action:",
    choices=["Insert", "Delete", "Move", "Renumber"],
    fallback_to_numbers=compat.is_vscode_terminal()
)
```

**Universal Applicability**: Any project with interactive TUI.

**Solves**: Arrow-key bug in VS Code terminal.

**LOC Estimate**: 400-500 lines

---

### Library 9: Code Generation (code_generation/)

**Purpose**: Universal template-based code generation.

**Current Location**: 
- `scaffolding/generator.py` (1,293 lines)
- `core/orchestrator_regenerator.py` (1,246 lines)

**Components**:
- `TemplateEngine` - Template rendering
- `CodeScaffolder` - Generate code from templates
- `OrchestratorGenerator` - Generate orchestrator code

**API Example**:
```python
from control_flow_engine.libraries.code_generation import TemplateEngine, CodeScaffolder

# Generate from template
engine = TemplateEngine(template_dir="templates/")
code = engine.render(
    template="class_template.py.jinja",
    context={"class_name": "MyClass", "methods": ["run", "stop"]}
)

# Create scaffolding
scaffolder = CodeScaffolder(output_dir="src/")
scaffolder.create_module(
    module_name="my_module",
    structure={"files": ["__init__.py", "main.py"]}
)
```

**Universal Applicability**: Any project with code generation needs.

**LOC Estimate**: 1,000-1,200 lines

---

## Application Layer (Control-Flow Specific)

### core/transformation.py (Orchestrator)

**New Role**: Orchestrates core libraries for control-flow-specific transformations.

**Current**: 2,613 LOC (mixed concerns)  
**After**: ~500-700 LOC (orchestration only)

**Uses Libraries**:
```python
from control_flow_engine.libraries.yaml_ops import YAMLReader, YAMLWriter
from control_flow_engine.libraries.structure_ops import StructureMover, StructureInserter
from control_flow_engine.libraries.planning import OperationPlanner, PlanValidator
from control_flow_engine.libraries.history import ChangeTracker
from control_flow_engine.libraries.filesystem_sync import DirectoryOperations

class ControlFlowTransformation:
    """
    Orchestrates libraries to transform control flow specifications.
    
    This is control-flow-specific: understands flows, phases, steps.
    Libraries are universal: understand hierarchies, sequences, elements.
    """
    
    def __init__(self, spec_file: str):
        # Use universal libraries
        self.yaml_reader = YAMLReader(spec_file)
        self.yaml_writer = YAMLWriter(spec_file)
        self.planner = OperationPlanner()
        self.validator = PlanValidator()
        self.tracker = ChangeTracker()
        
    def move_phase(self, phase_id: str, from_seq: int, to_seq: int):
        """Control-flow-specific: Move a phase."""
        # Load spec using universal library
        spec = self.yaml_reader.load()
        
        # Find phase in control-flow structure
        phase_path = ['flows', 'main', 'phases', phase_id]
        
        # Use universal mover library
        from control_flow_engine.libraries.structure_ops import StructureMover
        mover = StructureMover()
        
        result = mover.move_element(
            structure=spec,
            element_path=phase_path,
            from_sequence=from_seq,
            to_sequence=to_seq
        )
        
        # Save using universal library
        self.yaml_writer.save(result.structure)
        
        # Track using universal library
        self.tracker.record(result.metadata)
```

**Reduction**: 2,613 → 600 LOC (~75% reduction by using libraries)

---

### core/designer.py

**New Role**: High-level API using libraries.

**Current**: 1,272 LOC  
**After**: ~400-500 LOC (uses libraries)

---

### ui/flow_editor.py

**New Role**: Control-flow-specific editor using UI libraries.

**Current**: 982 LOC  
**After**: ~300-400 LOC (uses interactive_ui library)

---

## Library Extraction Phases

### Phase 1: Foundation Libraries (Week 1-2)

**Priority 1**: Structure Operations
1. Extract `structure_ops/inserter.py` from transformation.py
2. Extract `structure_ops/deleter.py` from transformation.py
3. **Create NEW** `structure_ops/mover.py` (missing functionality)
4. Extract `structure_ops/renumberer.py` from renumberer.py
5. **Create NEW** `structure_ops/swapper.py` (missing functionality)
6. **Create NEW** `structure_ops/reorderer.py` (missing functionality)

**Priority 2**: YAML Operations
7. Extract `yaml_ops/reader.py` from transformation.py
8. Extract `yaml_ops/writer.py` from transformation.py
9. Extract `yaml_ops/validator.py` from transformation.py

**Testing**: Unit tests for each library

**Effort**: 30-40 hours

---

### Phase 2: Planning & History (Week 3)

**Priority 3**: Planning Library
1. Extract `planning/planner.py` from transformation.py
2. Extract `planning/validator.py` from transformation.py
3. Create `planning/preview.py`

**Priority 4**: History Library
4. Extract `history/tracker.py` from transformation.py
5. Extract `history/rollback.py` from transformation.py

**Testing**: Integration tests with Phase 1 libraries

**Effort**: 20-25 hours

---

### Phase 3: Filesystem & Path (Week 4)

**Priority 5**: Filesystem Sync
1. Extract `filesystem_sync/directory_ops.py` from transformation.py
2. Extract `filesystem_sync/code_updater.py` from transformation.py
3. Extract `filesystem_sync/doc_updater.py` from renumberer.py

**Priority 6**: Path Resolution
4. Move `path_resolution/` (already universal, just relocate)

**Testing**: Integration tests with filesystem operations

**Effort**: 25-30 hours

---

### Phase 4: UI & Generation (Week 5)

**Priority 7**: Interactive UI
1. Extract `interactive_ui/terminal_compat.py` (NEW - fixes arrow-key bug)
2. Extract `interactive_ui/menu_builder.py` from flow_editor.py
3. Extract `interactive_ui/tree_navigator.py` from flow_editor.py

**Priority 8**: Code Generation
4. Extract `code_generation/` from scaffolding/ and orchestrator_regenerator.py

**Testing**: End-to-end tests with all libraries

**Effort**: 35-40 hours

---

### Phase 5: Application Layer Refactor (Week 6)

**Refactor Application Components**:
1. Refactor `core/transformation.py` to use libraries (2,613 → 600 LOC)
2. Refactor `core/designer.py` to use libraries (1,272 → 500 LOC)
3. Refactor `ui/flow_editor.py` to use libraries (982 → 400 LOC)

**Testing**: Full regression testing

**Effort**: 25-30 hours

---

## Total Effort Estimate

| Phase | Duration | Hours |
|-------|----------|-------|
| Phase 1: Foundation | 2 weeks | 30-40 |
| Phase 2: Planning & History | 1 week | 20-25 |
| Phase 3: Filesystem & Path | 1 week | 25-30 |
| Phase 4: UI & Generation | 1 week | 35-40 |
| Phase 5: Application Refactor | 1 week | 25-30 |
| **TOTAL** | **6 weeks** | **135-165 hours** |

---

## Universal Applicability Examples

### Example 1: Using structure_ops for JSON config management

```python
# Any project managing hierarchical JSON configs
from control_flow_engine.libraries.structure_ops import StructureMover

config = {
    "sections": [
        {"id": "sec1", "sequence": 1, "name": "Section 1"},
        {"id": "sec2", "sequence": 2, "name": "Section 2"},
        {"id": "sec3", "sequence": 3, "name": "Section 3"},
    ]
}

mover = StructureMover()
result = mover.move_element(
    structure=config,
    element_path=["sections", 2],  # Move section 3
    from_sequence=3,
    to_sequence=1                   # To position 1
)
# Result: [sec3, sec1, sec2]
```

### Example 2: Using yaml_ops for any YAML editing

```python
# Any project with YAML configs
from control_flow_engine.libraries.yaml_ops import YAMLReader, YAMLWriter

reader = YAMLReader("app_config.yml")
config = reader.load()

# Modify config
config["database"]["host"] = "localhost"

writer = YAMLWriter("app_config.yml", preserve_formatting=True)
writer.save(config)
```

### Example 3: Using interactive_ui for any TUI app

```python
# Any project with terminal UI
from control_flow_engine.libraries.interactive_ui import MenuBuilder, TerminalCompatibility

compat = TerminalCompatibility()
menu = MenuBuilder(compatibility=compat)

action = menu.select(
    "What do you want to do?",
    choices=["Create", "Edit", "Delete", "Exit"],
    fallback_to_numbers=compat.is_vscode_terminal()  # Auto-handles arrow-key bug
)
```

---

## Success Metrics

### Code Quality
- ✅ **Single Responsibility**: Each library does one thing well
- ✅ **No Domain Coupling**: Libraries don't know about "phases" or "flows"
- ✅ **High Cohesion**: Related functionality grouped together
- ✅ **Low Coupling**: Libraries independent, composable

### Code Reduction
- **Before**: 11,600 LOC mixed concerns
- **After**: 
  - ~4,000 LOC in 9 universal libraries
  - ~2,000 LOC in application layer (uses libraries)
  - **~5,600 LOC eliminated** through clean separation

### Functionality Gains
- ✅ **NEW: Move operation** (structure_ops/mover.py)
- ✅ **NEW: Swap operation** (structure_ops/swapper.py)
- ✅ **NEW: Batch reorder** (structure_ops/reorderer.py)
- ✅ **FIXED: Arrow-key bug** (interactive_ui/terminal_compat.py)

### Universal Applicability
- ✅ Libraries usable by **any project**, not just control-flow
- ✅ Clear separation between engine and application
- ✅ Easy to adopt incrementally in other projects

---

## Next Steps

1. **Review this proposal** - Validate architecture and library boundaries
2. **Prioritize libraries** - Confirm Phase 1 as starting point
3. **Create library templates** - Set up structure, tests, docs
4. **Begin Phase 1** - Start with structure_ops (highest value, adds missing features)

**Recommended Start**: `structure_ops/mover.py` - The missing functionality mentioned in BACKLOG.md

Would you like to proceed with Phase 1, or would you like to discuss any aspect of this architecture?
