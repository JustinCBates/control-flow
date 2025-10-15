# Control-Flow Library Extraction Analysis

**Date**: 2025-10-15  
**Purpose**: Analyze control-flow codebase to identify unit-level functionality that can be extracted into reusable libraries, similar to the pattern established in config-manager and deploy-manager.

## Executive Summary

The control-flow repository contains **~11,600 LOC** across 23 Python files with significant potential for library extraction. Analysis reveals:

- **8 High-Priority Library Candidates** for extraction
- **4 Cross-System Shared Components** applicable to config-manager and tui-form-designer
- **3 Critical Dependencies** between libraries requiring careful extraction order
- **Estimated Effort**: 40-60 hours for complete extraction and testing

## Current Code Structure

### Control-Flow Components (by size)

| File | LOC | Purpose | Library Candidate? |
|------|-----|---------|-------------------|
| `core/transformation.py` | 2,613 | YAML transformation system | ✅ HIGH |
| `scaffolding/generator.py` | 1,293 | Code scaffolding generation | ✅ HIGH |
| `core/designer.py` | 1,272 | High-level design API | ⚠️ ORCHESTRATOR |
| `core/orchestrator_regenerator.py` | 1,246 | Orchestrator code generation | ✅ MEDIUM |
| `core/engine.py` | 987 | Flow execution engine | ⚠️ ORCHESTRATOR |
| `ui/flow_editor.py` | 982 | Interactive TUI editor | ✅ HIGH |
| `tools/renumberer.py` | 801 | Phase/step renumbering | ✅ HIGH |
| `core/scaffolder.py` | 533 | Scaffolding coordinator | ✅ MEDIUM |
| `runtime/path_resolver.py` | 449 | Path resolution service | ✅ HIGH |
| `core/orchestrator_updater.py` | 320 | Orchestrator updates | ✅ LOW |
| `visualizer/graphviz_generator.py` | 294 | Flow visualization | ✅ LOW |
| `core/transformation_regenerator_bridge.py` | 276 | Bridge layer | ⚠️ ORCHESTRATOR |
| `cli/commands.py` | 257 | CLI interface | ⚠️ ORCHESTRATOR |
| `analysis/flow_analyzer.py` | 180 | Flow analysis | ✅ LOW |
| `visualizer/web_server.py` | 87 | Web server for diagrams | ✅ LOW |

### Existing Library Patterns

**Config-Manager Libraries** (18 units):
```
phases/libraries/
├── interactive/
│   └── tui_caller.py
├── validation/
│   ├── dependency_validator.py
│   ├── environment_validator.py
│   └── schema_validator.py
├── export/
│   ├── docker_compose_generator.py
│   ├── cfg_writer.py
│   ├── env_file_generator.py
│   └── manifest_generator.py
├── transformation/
│   └── defaults_transformer.py
└── probing/
    ├── system_detector.py
    ├── network_detector.py
    └── docker_detector.py
```

**Deploy-Manager Libraries** (28 units):
```
src/phases/libraries/
├── docker/
│   ├── compose_executor.py
│   ├── compose_manager.py
│   ├── docker_checker.py
│   ├── startup_monitor.py
│   ├── state_capturer.py
│   ├── image_puller.py
│   └── client_wrapper.py
├── config/
│   ├── config_loader.py
│   ├── env_generator.py
│   ├── config_converter.py
│   ├── config_validator.py
│   └── variable_extractor.py
├── templates/
│   ├── jinja_renderer.py
│   ├── template_filters.py
│   └── template_validator.py
├── prober/
│   └── prober_runner.py
├── reporting/
│   ├── status_reporter.py
│   └── metadata_logger.py
├── health/
├── network/
│   └── port_checker.py
├── system/
│   └── resource_checker.py
├── cleanup/
│   └── cleanup_handler.py
└── snapshot/
```

## Recommended Library Extractions

### Priority 1: High-Value, Self-Contained Units

#### 1. YAML Transformation Library
**Source**: `core/transformation.py` (2,613 LOC)  
**Target**: `phases/libraries/yaml_transformation/`

**Components**:
- `TransformationType` enum (INSERT, DELETE, MOVE, RENUMBER, UPDATE, MOCK)
- `TransformationMapping` - maps old to new structure
- `ValidationResult` - transformation validation
- `TransformationPlan` - plan-validate-apply workflow
- `TransformationHistory` - history tracking with checksums
- `DirectorySynchronizer` - sync YAML changes to filesystem
- `CodePathUpdater` - update import paths after moves

**Key Features**:
- Safe YAML modifications with validation
- Atomic operations with rollback support
- Change tracking and history
- Directory/file synchronization
- Code update automation

**Dependencies**: None (pure Python + YAML)

**Shareable By**: 
- ✅ **config-manager** - For YAML config transformations
- ✅ **tui-form-designer** - For form spec editing
- ✅ **Any system** - Managing YAML-based specifications

**Extraction Effort**: 6-8 hours
- Extract classes and tests
- Create library interface
- Update imports in control-flow
- Add integration tests

---

#### 2. Sequence Renumbering Library
**Source**: `tools/renumberer.py` (801 LOC)  
**Target**: `phases/libraries/sequence_management/`

**Components**:
- `NumberingStrategy` enum (COMPACT, PRESERVE_GAPS, MINIMAL_SHIFT)
- `RenumberOperation` - single rename operation
- `RenumberPlan` - complete renumbering plan
- `PhaseStepRenumberer` - safe renumbering with rollback

**Key Features**:
- Gap handling strategies
- Directory renaming (phase_3 → phase_4)
- Import path updates in Python files
- Config updates in YAML files
- Documentation updates in Markdown
- Atomic operations with rollback
- Dry-run mode

**Dependencies**: 
- YAML Transformation Library (for config updates)

**Shareable By**:
- ✅ **tui-form-designer** - For reordering form fields/sections
- ✅ **Any system** - With sequenced/numbered components

**Extraction Effort**: 4-6 hours
- Extract renumbering logic
- Separate from control-flow specifics
- Generalize to handle any numbered sequences
- Add tests for move operations

**CRITICAL NOTE**: This is the "move functionality" mentioned by the user. It provides:
```python
# Current API
renumberer.renumber_phases(insert_at=4)  # Makes room at position 4
renumberer.renumber_steps(phase_id='collection', insert_at=2)

# Potential Enhanced API
renumberer.move_item(from_seq=5, to_seq=2)  # Direct move
renumberer.reorder_items([3, 1, 2, 4, 5])   # Batch reorder
```

---

#### 3. Path Resolution Library
**Source**: `runtime/path_resolver.py` (449 LOC)  
**Target**: `phases/libraries/path_resolution/`

**Components**:
- `PathResolver` - centralized path resolution
- `from_execution_context()` - auto-detect project root
- Artifact path resolution from specs
- Phase output directory resolution

**Key Features**:
- Context-aware path resolution (pipeline, phase, step)
- Auto-detection of project root
- Artifact tracking from YAML specs
- Consistent behavior regardless of execution context

**Dependencies**: None (YAML parsing only)

**Shareable By**:
- ✅ **config-manager** - For resolving config artifact paths
- ✅ **deploy-manager** - For resolving deployment artifacts
- ✅ **Any multi-phase system** - With artifact dependencies

**Extraction Effort**: 3-4 hours
- Generalize from control_flows.yml to any spec format
- Extract to library
- Update control-flow imports
- Add tests

---

#### 4. Interactive TUI Editor Library
**Source**: `ui/flow_editor.py` (982 LOC)  
**Target**: `phases/libraries/interactive_editor/`

**Components**:
- `ControlFlowEditor` - menu-driven interface
- `FlowElement` dataclass (phase/step representation)
- Navigation menus (browse, select, edit)
- Questionary-based UI components
- Custom styling

**Key Features**:
- Browse phases and steps visually
- Insert, delete, renumber operations
- Preview changes before applying
- View transformation history
- Rollback support
- User-friendly error handling

**Dependencies**:
- Questionary library
- YAML Transformation Library
- Sequence Renumbering Library

**Shareable By**:
- ✅ **tui-form-designer** - Could replace current designer.py
- ✅ **config-manager** - For interactive config editing
- ⚠️ **CRITICAL**: This solves the arrow-key bug mentioned in BACKLOG.md

**Extraction Effort**: 8-10 hours
- Generalize from control-flow to generic hierarchical editing
- Abstract phase/step to parent/child model
- Create pluggable transformation backend
- Solve arrow-key issue (see "Terminal Compatibility Fix" below)
- Add tests

**SOLVING THE ARROW-KEY BUG**:
The BACKLOG.md mentions "Arrow keys don't work in VS Code terminal" because questionary relies on terminal emulation. The extracted library should:
1. Detect terminal type (VS Code integrated vs standard)
2. Provide fallback numbered menu for VS Code
3. Use arrow keys where supported
4. Make this configurable

---

### Priority 2: Medium-Value Extraction Candidates

#### 5. Code Scaffolding Library
**Source**: `scaffolding/generator.py` (1,293 LOC) + `core/scaffolder.py` (533 LOC)  
**Target**: `phases/libraries/code_scaffolding/`

**Components**:
- Template-based code generation
- Directory structure creation
- Orchestrator generation
- Step file generation
- Import management

**Shareable By**:
- ✅ Any system needing code generation from specs

**Extraction Effort**: 6-8 hours

---

#### 6. Orchestrator Regeneration Library
**Source**: `core/orchestrator_regenerator.py` (1,246 LOC)  
**Target**: `phases/libraries/orchestrator_generation/`

**Components**:
- Dynamic orchestrator code generation
- Phase registry management
- Step integration
- Mock generation for unimplemented steps

**Shareable By**:
- ✅ **config-manager** - For regenerating phase orchestrators
- ✅ Any multi-phase workflow system

**Extraction Effort**: 6-8 hours

---

### Priority 3: Low-Priority Utilities

#### 7. Flow Visualization Library
**Source**: `visualizer/graphviz_generator.py` (294 LOC) + `web_server.py` (87 LOC)  
**Target**: `phases/libraries/visualization/`

**Extraction Effort**: 3-4 hours

---

#### 8. Flow Analysis Library
**Source**: `analysis/flow_analyzer.py` (180 LOC)  
**Target**: `phases/libraries/flow_analysis/`

**Extraction Effort**: 2-3 hours

---

## Cross-System Shared Components

### 1. YAML Transformation (HIGHEST IMPACT)

**Currently In**: control-flow only  
**Should Be In**: Shared library used by all systems  
**Reason**: All three systems (control-flow, config-manager, tui-form-designer) edit YAML specs

**Shared Capabilities**:
- Safe YAML edit operations (insert, delete, move, renumber)
- Validation before applying
- Atomic operations with rollback
- Change history tracking

**Integration Points**:
```
control-flow: Edit control_flows.yml (add/remove phases/steps)
config-manager: Edit config specs (modify defaults, add fields)
tui-form-designer: Edit form specs (add/remove/reorder fields)
```

**Recommendation**: Extract to top-level shared library
```
openproject/
├── shared_libraries/
│   └── yaml_transformation/
│       ├── transformation.py
│       ├── validation.py
│       └── history.py
└── external/
    ├── control-flow/
    ├── config-manager/
    └── tui-form-designer/
```

---

### 2. Sequence Management / Move-Reorder (HIGH IMPACT)

**Currently In**: control-flow/tools/renumberer.py  
**Needed By**: 
- control-flow (phases, steps)
- tui-form-designer (form fields, sections)
- config-manager (potentially for reordering config sections)

**Missing Functionality** (from BACKLOG.md):
- Direct move operation (move item from position A to B)
- Batch reorder (rearrange multiple items at once)
- Swap operation (exchange two items)

**Enhanced API Proposal**:
```python
class SequenceManager:
    """Manage sequenced items (phases, steps, fields, etc.)"""
    
    # Current capabilities (from renumberer.py)
    def insert_gap(self, position: int) -> RenumberPlan
    def compact_sequence(self) -> RenumberPlan
    
    # NEW: Missing move/reorder features
    def move_item(self, from_seq: int, to_seq: int) -> MovePlan
    def swap_items(self, seq_a: int, seq_b: int) -> SwapPlan
    def reorder_batch(self, new_order: List[int]) -> ReorderPlan
    
    # All operations support:
    # - Dry-run preview
    # - Validation
    # - Directory renaming
    # - File content updates
    # - Rollback
```

**Recommendation**: Extract and enhance renumberer.py into shared sequence_management library

---

### 3. Interactive Editor Pattern (MEDIUM IMPACT)

**Currently In**: 
- control-flow/ui/flow_editor.py
- tui-form-designer/tools/designer.py (different implementation)

**Problem**: Both implement similar editing UIs but with the arrow-key bug in VS Code

**Shared Pattern**:
- Hierarchical navigation (parent → child)
- Edit operations (insert, delete, move, rename)
- Preview before apply
- Questionary-based menus

**Recommendation**: Extract to shared `interactive_editor` library with:
- Generic hierarchical editor framework
- Terminal compatibility layer (fixes arrow-key bug)
- Pluggable transformation backend
- Reusable UI components

---

### 4. Path Resolution (LOW-MEDIUM IMPACT)

**Currently In**: control-flow/runtime/path_resolver.py  
**Could Benefit**: 
- config-manager (artifact paths between phases)
- deploy-manager (runtime artifact locations)

**Shared Capability**: Resolve artifact paths from spec files regardless of execution context

**Recommendation**: Extract to shared library, but lower priority than transformation/sequence

---

## Extraction Roadmap

### Phase 1: Foundation Libraries (High Priority)
**Effort**: 16-22 hours

1. **YAML Transformation Library** (6-8 hours)
   - Most impactful, zero dependencies
   - Immediately usable by all systems
   - Extract to `shared_libraries/yaml_transformation/`

2. **Path Resolution Library** (3-4 hours)
   - No dependencies
   - Clean extraction
   - Extract to `shared_libraries/path_resolution/`

3. **Sequence Management Library** (4-6 hours)
   - Add missing move/reorder features
   - Depends on YAML Transformation
   - Extract to `shared_libraries/sequence_management/`

4. **Integration Testing** (3-4 hours)
   - Test all three libraries together
   - Validate rollback scenarios
   - Performance testing

### Phase 2: UI/Interaction Libraries (Medium Priority)
**Effort**: 12-16 hours

5. **Interactive Editor Library** (8-10 hours)
   - **SOLVES ARROW-KEY BUG**
   - Terminal compatibility layer
   - Generic hierarchical editing
   - Extract to `shared_libraries/interactive_editor/`

6. **Replace tui-form-designer and control-flow editors** (4-6 hours)
   - Migrate both to use shared library
   - Remove duplicate code
   - Add system-specific plugins

### Phase 3: Code Generation Libraries (Lower Priority)
**Effort**: 12-16 hours

7. **Code Scaffolding Library** (6-8 hours)
8. **Orchestrator Generation Library** (6-8 hours)

### Phase 4: Utilities (Lowest Priority)
**Effort**: 5-7 hours

9. **Visualization Library** (3-4 hours)
10. **Analysis Library** (2-3 hours)

---

## Dependency Graph

```
┌─────────────────────────────────────────────────┐
│ Shared Libraries (Top Level)                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────┐                   │
│  │ yaml_transformation     │◄───────┐          │
│  └─────────────────────────┘        │          │
│            ▲                         │          │
│            │                         │          │
│  ┌─────────────────────────┐        │          │
│  │ sequence_management     │────────┘          │
│  │ (includes move/reorder) │                   │
│  └─────────────────────────┘                   │
│            ▲                                     │
│            │                                     │
│  ┌─────────────────────────┐                   │
│  │ interactive_editor      │                   │
│  │ (fixes arrow-key bug)   │                   │
│  └─────────────────────────┘                   │
│                                                  │
│  ┌─────────────────────────┐                   │
│  │ path_resolution         │                   │
│  └─────────────────────────┘                   │
│                                                  │
└─────────────────────────────────────────────────┘
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
┌───────────┐ ┌───────────┐ ┌────────────────┐
│ control-  │ │  config-  │ │ tui-form-      │
│ flow      │ │  manager  │ │ designer       │
└───────────┘ └───────────┘ └────────────────┘
```

---

## Critical Findings: Move/Reorder Functionality

### Current State

**Location**: `control-flow/tools/renumberer.py`

**What It Does**:
- Renumbers phases/steps when inserting or deleting
- Handles directory renaming (e.g., `phase_3/` → `phase_4/`)
- Updates import paths in Python files
- Updates references in YAML configs
- Updates documentation

**What It DOESN'T Do** (from BACKLOG.md):
- ❌ Direct "move" operation (move phase 5 to position 2)
- ❌ Simple reorder (rearrange [1,2,3,4,5] to [3,1,4,2,5])
- ❌ Swap operation (swap positions 2 and 4)

### Why This Matters

Both control-flow and tui-form-designer need move/reorder:

**control-flow**:
```
Current: Insert gap, then manually move files, then compact
Needed:  Direct move (move phase 5 to position 2)
```

**tui-form-designer**:
```
Current: Delete and re-insert fields to change order
Needed:  Direct reorder of form fields
```

### Recommended Enhancement

Add to `PhaseStepRenumberer` class:

```python
def move_item(
    self,
    item_type: str,  # 'phase' or 'step'
    from_sequence: int,
    to_sequence: int,
    parent_id: Optional[str] = None,
    dry_run: bool = True
) -> RenumberPlan:
    """
    Move an item from one sequence position to another.
    
    Example:
        Move phase 5 to position 2:
        Before: [1, 2, 3, 4, 5, 6]
        After:  [1, 5, 2, 3, 4, 6]
        
        This requires:
        - Rename phase_5 → phase_2
        - Rename phase_2 → phase_3
        - Rename phase_3 → phase_4
        - Rename phase_4 → phase_5
        
    Args:
        item_type: 'phase' or 'step'
        from_sequence: Current position
        to_sequence: Target position
        parent_id: For steps, the parent phase_id
        dry_run: If True, only generate plan without executing
        
    Returns:
        RenumberPlan with all required operations
    """
```

---

## Recommended File Structure After Extraction

```
openproject/
├── shared_libraries/                      # NEW: Shared across all repos
│   ├── __init__.py
│   ├── yaml_transformation/
│   │   ├── __init__.py
│   │   ├── transformation.py              # TransformationPlan, etc.
│   │   ├── validation.py                  # ValidationResult, etc.
│   │   ├── history.py                     # TransformationHistory
│   │   └── tests/
│   ├── sequence_management/
│   │   ├── __init__.py
│   │   ├── renumberer.py                  # PhaseStepRenumberer
│   │   ├── mover.py                       # NEW: Move/reorder operations
│   │   └── tests/
│   ├── interactive_editor/
│   │   ├── __init__.py
│   │   ├── editor.py                      # Generic hierarchical editor
│   │   ├── terminal_compat.py             # Fixes arrow-key bug
│   │   ├── ui_components.py               # Reusable questionary components
│   │   └── tests/
│   ├── path_resolution/
│   │   ├── __init__.py
│   │   ├── resolver.py                    # PathResolver
│   │   └── tests/
│   └── code_scaffolding/
│       ├── __init__.py
│       ├── generator.py
│       ├── templates/
│       └── tests/
│
├── external/
│   ├── control-flow/
│   │   ├── src/control_flow_engine/
│   │   │   ├── core/
│   │   │   │   ├── engine.py              # Uses shared libs
│   │   │   │   ├── designer.py            # Uses shared libs
│   │   │   │   └── transformation_regenerator_bridge.py
│   │   │   ├── cli/
│   │   │   └── analysis/
│   │   └── phases/
│   │       └── libraries/                 # Control-flow-specific libs
│   │
│   ├── config-manager/
│   │   └── phases/
│   │       └── libraries/                 # Config-manager-specific libs
│   │           ├── export/
│   │           ├── validation/
│   │           └── probing/
│   │
│   └── tui-form-designer/
│       └── src/
│           └── libraries/                 # Form-designer-specific libs
│
└── pyproject.toml                         # Add shared_libraries package
```

---

## Integration Strategy

### Step 1: Create Shared Libraries Package

```toml
# pyproject.toml (main repo)
[project]
name = "openproject-shared-libraries"
version = "1.0.0"

[project.optional-dependencies]
yaml-transformation = ["pyyaml>=6.0"]
interactive-editor = ["questionary>=2.0"]
all = [
    "pyyaml>=6.0",
    "questionary>=2.0"
]
```

### Step 2: Update Submodule Dependencies

```toml
# external/control-flow/pyproject.toml
[project]
dependencies = [
    "openproject-shared-libraries[all]",
    # ... other deps
]
```

### Step 3: Migration Pattern

```python
# Before (control-flow/core/transformation.py)
from control_flow_engine.core.transformation import TransformationPlan

# After
from shared_libraries.yaml_transformation import TransformationPlan
```

---

## Testing Strategy

### Unit Tests (Per Library)
- Test each library in isolation
- Mock dependencies
- Cover all public APIs

### Integration Tests (Cross-Library)
- Test YAML Transformation + Sequence Management together
- Test Interactive Editor + YAML Transformation
- Test rollback scenarios

### System Tests (Per Repo)
- Test control-flow with new shared libraries
- Test config-manager with new shared libraries
- Test tui-form-designer with new shared libraries

### Compatibility Tests
- Ensure no breaking changes to existing functionality
- Test migration path
- Validate performance

---

## Success Metrics

### Code Reduction
- **Target**: Reduce total codebase by 15-20% through deduplication
- **Current**: ~11,600 LOC in control-flow + unknown in tui-form-designer
- **After**: Shared libraries eliminate duplicate editing logic

### Feature Parity
- ✅ All existing functionality preserved
- ✅ Arrow-key bug fixed
- ✅ Move/reorder feature added
- ✅ Consistent behavior across all systems

### Maintainability
- ✅ Single source of truth for YAML editing
- ✅ Single source of truth for sequence management
- ✅ Easier to add new features (benefit all systems)
- ✅ Easier to fix bugs (fix once, benefit all)

### Developer Experience
- ✅ Clear library boundaries
- ✅ Well-documented APIs
- ✅ Easy to test
- ✅ Easy to import and use

---

## Risk Assessment

### High Risk
- **Breaking Changes**: Extracting core functionality could break existing code
  - *Mitigation*: Comprehensive test suite, gradual migration
  
### Medium Risk
- **Circular Dependencies**: Shared libraries depending on each other
  - *Mitigation*: Careful dependency graph design (see diagram above)

### Low Risk
- **Performance**: Extraction could add overhead
  - *Mitigation*: Performance testing, optimize hot paths

---

## Next Steps

### Immediate Actions (This Week)
1. **Review this analysis** with stakeholders
2. **Prioritize libraries** to extract (recommend Phase 1)
3. **Set up shared_libraries package** structure
4. **Create test framework** for shared libraries

### Short Term (Next 2 Weeks)
5. **Extract YAML Transformation Library** (highest impact)
6. **Extract Sequence Management Library** (adds move/reorder)
7. **Integrate with control-flow** (validate no regressions)
8. **Integrate with config-manager** (add YAML editing)

### Medium Term (Next Month)
9. **Extract Interactive Editor Library** (fixes arrow-key bug)
10. **Replace tui-form-designer editor** (eliminate duplication)
11. **Complete documentation** (API docs, migration guides)
12. **Add to CI/CD** (automated testing)

---

## Appendix: Key Classes and Methods

### YAML Transformation (2,613 LOC)

**Classes**:
- `TransformationType(Enum)`: INSERT, DELETE, MOVE, RENUMBER, UPDATE, MOCK
- `ValidationStatus(Enum)`: PENDING, VALID, INVALID, WARNING
- `TransformationMapping`: Maps old structure to new
- `ValidationResult`: Validation errors/warnings/checks
- `TransformationPlan`: Plan-validate-apply workflow
- `DirectoryOperation`: Directory create/rename/delete
- `TransformationHistory`: Change tracking with checksums
- `DirectorySynchronizer`: Sync YAML to filesystem
- `CodePathUpdater`: Update import paths in code

**Key Methods**:
- `plan.validate()`: Validate transformation
- `plan.apply()`: Apply to YAML
- `synchronizer.sync_directories()`: Sync to filesystem
- `updater.update_imports()`: Update code imports
- `history.record_transformation()`: Track changes
- `history.rollback_transformation()`: Undo changes

### Sequence Management (801 LOC)

**Classes**:
- `NumberingStrategy(Enum)`: COMPACT, PRESERVE_GAPS, MINIMAL_SHIFT
- `RenumberOperation`: Single rename operation
- `RenumberPlan`: Complete renumbering plan
- `PhaseStepRenumberer`: Safe renumbering with rollback

**Key Methods**:
- `renumber_phases(insert_at)`: Make gap for insertion
- `renumber_steps(phase_id, insert_at)`: Renumber steps in phase
- `_rename_directories()`: Rename phase/step dirs
- `_update_imports()`: Update Python import paths
- `_update_configs()`: Update YAML references
- `_update_docs()`: Update Markdown docs
- `_rollback()`: Undo renumbering

**Missing Methods** (to add):
- `move_item(from, to)`: Direct move operation
- `swap_items(a, b)`: Swap two items
- `reorder_batch(new_order)`: Batch reorder

### Path Resolution (449 LOC)

**Classes**:
- `PathResolver`: Centralized path resolution

**Key Methods**:
- `from_execution_context(__file__)`: Auto-detect project root
- `resolve_artifact_path(artifact_id)`: Get artifact path from spec
- `resolve_phase_output_dir(phase_id)`: Get phase output directory

### Interactive Editor (982 LOC)

**Classes**:
- `ControlFlowEditor`: Menu-driven TUI
- `FlowElement`: Phase/step representation

**Key Methods**:
- `run()`: Main editor loop
- `browse_flows()`: Navigate phases/steps
- `renumber_phase()`: Renumber operation
- `insert_phase()`: Insert operation
- `delete_phase()`: Delete operation

---

## Conclusion

The control-flow codebase contains significant reusable functionality that should be extracted into shared libraries. The highest-priority extractions are:

1. **YAML Transformation** - Needed by all three systems
2. **Sequence Management** - Adds missing move/reorder features
3. **Interactive Editor** - Fixes arrow-key bug, eliminates duplication

These three libraries will provide immediate value to control-flow, config-manager, and tui-form-designer while reducing code duplication and improving maintainability.

**Recommended Next Action**: Begin with YAML Transformation Library extraction (Phase 1, Step 1) as it has zero dependencies and immediate applicability across all systems.
