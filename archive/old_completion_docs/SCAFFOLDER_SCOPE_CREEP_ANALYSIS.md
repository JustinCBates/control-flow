# Control Flow Scaffolder - Scope Creep Analysis

**Date**: October 15, 2025  
**File**: `/opt/openproject/external/control-flow/src/control_flow_engine/core/scaffolder.py`  
**Issue**: Scaffolder contains technology-specific code (TUI forms) that violates separation of concerns

---

## 🔍 Problem Summary

The control-flow scaffolder was designed to scaffold **control-flow structure only** (phases, steps, orchestrators). However, during development it accumulated **technology-specific scaffolding** (TUI layouts, defaults files) that:

1. ❌ **Violates separation of concerns** - Control-flow engine shouldn't know about TUI
2. ❌ **Causes overwriting issues** - Scaffolder regenerates implementation files
3. ❌ **Creates orphaned directories** - Generated `phase_4_collection/` without checking
4. ❌ **Lacks existence checks** - Overwrites existing files without checking

---

## 📋 Evidence of Scope Creep

### 1. TUI-Specific Data Class Fields

**Location**: `StepInsertion` dataclass (lines 34-44)

```python
@dataclass
class StepInsertion:
    # ... basic fields ...
    
    # ❌ TUI-specific (shouldn't be here)
    is_tui_form: bool = False
    layout_file_name: Optional[str] = None
    use_defaults_file: bool = False
    defaults_file_name: Optional[str] = None
    
    # ❌ Mock responses (TUI-specific)
    generate_mock_responses: bool = True
    mock_responses: Optional[Dict[str, Any]] = None
```

**Why this is wrong:**
- Control-flow engine should be **technology-agnostic**
- TUI, API, GUI, CLI are all valid step implementations
- Scaffolder shouldn't favor one technology over others

---

### 2. TUI-Specific Implementation Generation

**Location**: `create_step_scaffolding()` method (lines 171-179)

```python
# ❌ Creates TUI layout files
if step.is_tui_form:
    layout_name = step.layout_file_name or f"{step.step_id}.layout.yml"
    layout_file = step_dir / layout_name
    layout_content = self._generate_tui_layout(step)
    layout_file.write_text(layout_content)  # NO EXISTENCE CHECK!
    created_files['layout'] = layout_file
    
    # ❌ Creates TUI defaults files
    if step.use_defaults_file:
        defaults_name = step.defaults_file_name or f"{step.step_id}.defaults.yml"
        defaults_file = step_dir / defaults_name
        defaults_content = self._generate_tui_defaults(step)
        defaults_file.write_text(defaults_content)  # NO EXISTENCE CHECK!
        created_files['defaults'] = defaults_file
```

**Why this is wrong:**
- **No existence check** - Blindly overwrites existing files
- **TUI-specific logic** - What about API steps? CLI steps?
- **Hard-coded assumptions** - Assumes TUI layout structure

**This caused:**
- ✅ **Confirmed**: `discovery_prompt.layout.yml` was overwritten during scaffolding
- ✅ **Confirmed**: `phase_4_collection/` was created even though Phase 4 is validation

---

### 3. Entire TUI-Specific Generator Methods

**Location**: Lines 532-696

```python
# ❌ 165 lines of TUI-specific code in control-flow engine
def _generate_tui_step_implementation(self, step: StepInsertion) -> str:
    """Generate implementation file for a TUI form step."""
    # ... 80 lines of TUI-specific template code ...
    
def _generate_tui_layout(self, step: StepInsertion) -> str:
    """Generate TUI layout YAML template."""
    # ... 12 lines of TUI layout template ...
    
def _generate_tui_defaults(self, step: StepInsertion) -> str:
    """Generate TUI defaults YAML template."""
    # ... 4 lines of TUI defaults template ...
```

**Why this is wrong:**
- Control-flow engine imports/dependencies shouldn't include TUI
- Other projects can't use scaffolder without dragging in TUI assumptions
- Violates "single responsibility principle"

---

### 4. Hard-Coded TUI Import Paths

**Location**: `_generate_tui_step_implementation()` lines 545-549

```python
# ❌ Hard-coded assumption about TUI location
tui_path = Path(__file__).parent.parent.parent.parent.parent / 'tui-form-designer' / 'src'
sys.path.insert(0, str(tui_path))
from tui_form_engine.renderer import FormRenderer
```

**Why this is wrong:**
- Assumes specific directory structure
- Breaks in different project layouts
- TUI may not even be installed!

---

## ✅ What the Scaffolder SHOULD Do

### Core Responsibilities (Technology-Agnostic)

1. **Phase Scaffolding** ✅
   - Create `phase_{N}_{phase_id}/` directory
   - Create `__init__.py` with imports
   - Create `orchestrator_{phase_id}.py` stub
   - Create `outputs/` directory
   - Create `README.md` template

2. **Step Scaffolding** ✅
   - Create `step_{N}_{step_id}/` directory
   - Create `__init__.py` with imports
   - Create `{step_id}.py` implementation **stub only**
   - Create `README.md` template

3. **Safety Checks** ❌ **MISSING**
   - Check if phase directory exists before creating
   - Check if step directory exists before creating
   - Check if files exist before writing
   - Provide `--force` flag to override safety checks

4. **YAML Update** ✅
   - Add phase to `control_flows.yml`
   - Add step to phase's `sub_flows` section
   - Update sequence numbers if needed

---

## ❌ What the Scaffolder SHOULD NOT Do

1. **Technology-Specific Files** ❌
   - ❌ TUI layout files
   - ❌ TUI defaults files
   - ❌ API route definitions
   - ❌ GUI component files
   - ❌ Database schema files

2. **Implementation Code** ❌
   - ❌ Hard-coded import paths
   - ❌ Specific library imports (TUI, requests, etc.)
   - ❌ Technology-specific logic

3. **Overwriting** ❌
   - ❌ Regenerate existing implementation files
   - ❌ Overwrite user-modified files
   - ❌ Destroy working code

---

## 🔧 Recommended Refactoring

### Phase 1: Remove TUI-Specific Code (High Priority)

**Files to modify:**
- `src/control_flow_engine/core/scaffolder.py`

**Changes:**

1. **Remove TUI fields from `StepInsertion`:**
   ```python
   @dataclass
   class StepInsertion:
       step_id: str
       name: str
       sequence: int
       description: str
       status: ImplementationStatus
       step_type: str  # Keep for documentation only
       
       phase_id: str
       phase_sequence: int
       
       create_scaffolding: bool = True
       insert_before: Optional[str] = None
       insert_after: Optional[str] = None
       
       # ❌ REMOVE: is_tui_form, layout_file_name, use_defaults_file, etc.
   ```

2. **Remove TUI generator methods:**
   - ❌ Delete `_generate_tui_step_implementation()`
   - ❌ Delete `_generate_tui_layout()`
   - ❌ Delete `_generate_tui_defaults()`
   - ❌ Delete `_generate_mock_responses()`

3. **Simplify step scaffolding:**
   ```python
   def create_step_scaffolding(self, step: StepInsertion, base_path: Path):
       # Only create directory structure and stub
       step_dir = base_path / f"step_{step.sequence}_{step.step_id}"
       
       # ✅ ADD: Check existence
       if step_dir.exists():
           logger.warning(f"Step directory already exists: {step_dir}")
           return None
       
       step_dir.mkdir(parents=True)
       
       # Create minimal stub only
       (step_dir / "__init__.py").write_text(self._generate_step_init(step))
       (step_dir / f"{step.step_id}.py").write_text(self._generate_generic_step_stub(step))
       (step_dir / "README.md").write_text(self._generate_step_readme(step))
       
       # ✅ NO TUI-specific files
       # ✅ NO mock responses
       # ✅ User adds implementation-specific files themselves
   ```

---

### Phase 2: Add Safety Checks (High Priority)

**Add existence checking:**

```python
def create_phase_scaffolding(self, phase: PhaseInsertion, base_path: Path, force: bool = False):
    phase_dir = base_path / f"phase_{phase.sequence}_{phase.phase_id}"
    
    # ✅ Check existence
    if phase_dir.exists() and not force:
        logger.error(f"❌ Phase directory already exists: {phase_dir}")
        logger.info("Use --force to overwrite")
        return None
    
    # ... continue with creation ...
```

**Add file-level checks:**

```python
def _write_file_safe(self, path: Path, content: str, force: bool = False):
    """Write file only if it doesn't exist or force=True."""
    if path.exists() and not force:
        logger.warning(f"⚠️  Skipping existing file: {path}")
        return False
    
    path.write_text(content)
    logger.info(f"✅ Created: {path}")
    return True
```

---

### Phase 3: Plugin System for Technology-Specific Scaffolding (Medium Priority)

**Create extension point:**

```python
class ScaffoldPlugin:
    """Base class for technology-specific scaffolding plugins."""
    
    def can_handle(self, step: StepInsertion) -> bool:
        """Check if this plugin can handle the step type."""
        raise NotImplementedError
    
    def scaffold_files(self, step: StepInsertion, step_dir: Path) -> List[Path]:
        """Create technology-specific files."""
        raise NotImplementedError

class TUIScaffoldPlugin(ScaffoldPlugin):
    """Plugin for scaffolding TUI form steps."""
    
    def can_handle(self, step: StepInsertion) -> bool:
        return step.step_type == 'tui_interactive'
    
    def scaffold_files(self, step: StepInsertion, step_dir: Path) -> List[Path]:
        # Create TUI-specific files (layout, defaults)
        # But THIS code should live in tui-form-designer repo!
        pass
```

**Location for plugins:**
- TUI plugin: `external/tui-form-designer/plugins/scaffold_plugin.py`
- API plugin: `external/api-manager/plugins/scaffold_plugin.py` (future)
- Control-flow just provides the interface

---

## 📊 Impact Analysis

### What Gets Fixed

1. ✅ **Scaffolder won't overwrite implementation files**
   - No more `discovery_prompt.layout.yml` overwrites
   - Existing steps preserved

2. ✅ **Scaffolder won't create orphaned directories**
   - Checks control_flows.yml before creating phases
   - No more `phase_4_collection/` mistakes

3. ✅ **Control-flow engine becomes truly generic**
   - Can be used for non-TUI projects
   - No technology assumptions

4. ✅ **Better separation of concerns**
   - Control-flow handles flow structure
   - Technology repos handle their own templates

---

### What Needs Migration

**Existing TUI scaffolding users:**

If anyone was using the TUI scaffolding features, they'll need to:

1. Copy TUI template files to their project
2. Manually create layout files (which they should be doing anyway)
3. Use TUI form designer tools directly

**Migration impact: LOW**
- Most users weren't using the TUI scaffolding anyway
- Those who were can copy templates from old version
- Better long-term design

---

## 🎯 Action Plan

### Immediate (This Session)

- [x] Document the scope creep issues
- [ ] Create backup of current scaffolder.py
- [ ] Remove TUI-specific code from scaffolder
- [ ] Add existence checking
- [ ] Test with config-manager

### Short Term (Next Few Days)

- [ ] Create plugin system design
- [ ] Move TUI scaffolding to tui-form-designer repo
- [ ] Update documentation
- [ ] Update any scripts that used TUI scaffolding

### Long Term (Next Few Weeks)

- [ ] Implement plugin system
- [ ] Create TUI scaffold plugin
- [ ] Document plugin development
- [ ] Create example plugins for other technologies

---

## 📝 Notes

### Why This Happened

During the migration to the new control-flow system (Oct 13-14), the scaffolder was trying to be "helpful" by auto-generating TUI files. This seemed convenient at the time but violated architectural principles.

### Lessons Learned

1. **Separation of concerns matters**
   - Generic tools should stay generic
   - Technology-specific code belongs in technology repos

2. **Existence checks are critical**
   - Never blindly overwrite files
   - Always provide escape hatches (--force)

3. **Test thoroughly before committing**
   - The `phase_4_collection/` mistake would have been caught by tests
   - Tests should validate control_flows.yml matches reality

---

**Status**: Analysis complete, ready for refactoring  
**Risk**: Low - removing unused code  
**Effort**: ~2 hours to refactor and test
