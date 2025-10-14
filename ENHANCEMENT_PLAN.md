# Control Flow Engine Enhancement Plan

## Current Capabilities Analysis

### ✅ What the Engine Currently Has

#### 1. **Core Engine** (`src/control_flow_engine/core/engine.py`)
- `ControlFlowManager`: Parses YAML-based flow specifications
- `FlowStep` dataclass: Represents individual steps in a flow
- `FlowInsertion`: Supports dynamic flow modifications
- `ImplementationStatus` enum: IMPLEMENTED, IN_PROGRESS, PLANNED, TODO
- Parses multiple sections: Entry Points, Flow Implementations, Decision Points, External Interfaces

#### 2. **Visualization** (`src/control_flow_engine/visualizer/`)
- `GraphvizFlowVisualizer`: Professional diagram generation using Graphviz
- Supports multiple output formats: SVG, PNG, PDF
- Color-coded status visualization
- Phase flow diagrams with artifacts
- Web server for interactive viewing (`web_server.py`)
- HTML templates for browser-based visualization

#### 3. **Analysis Tools** (`src/control_flow_engine/analysis/`)
- `FlowAnalyzer`: Complexity analysis
- Dependency tracking
- Artifact flow analysis
- Basic metrics (phases, artifacts, flows, complexity score)

#### 4. **CLI Interface** (`src/control_flow_engine/cli/commands.py`)
Commands available:
- `validate` - Validate flow specifications
- `visualize` - Generate diagrams (Mermaid, HTML)
- `serve` - Start interactive web interface
- `analyze` - Analyze complexity and dependencies
- `info` - Show engine information

#### 5. **Templates** (`templates/`)
- `CONTROL_FLOWS_SPEC.template.md`: Basic flow specification template

### ❌ What's Missing (Scaffolding Generation)

The engine currently **reads and visualizes** control flows but does NOT:
- ❌ Generate directory structures from specs
- ❌ Create phase stub files with proper signatures
- ❌ Generate root entry point (run.py)
- ❌ Create boilerplate code for phases
- ❌ Auto-generate imports and dependencies
- ❌ Scaffold test files
- ❌ Generate documentation stubs

## Enhancement Goals

### Primary Goal: Add Scaffolding Generation

Create a new command that:
1. Reads a `control_flows.yml` specification
2. Generates directory structure matching phases
3. Creates Python stub files for each phase
4. Generates a root entry point that orchestrates phases
5. Creates test file stubs
6. Generates README with usage instructions

## Proposed Architecture

### New Module: `src/control_flow_engine/scaffolding/`

```
scaffolding/
├── __init__.py
├── generator.py          # Main scaffolding generator
├── templates/            # Code templates
│   ├── phase.py.jinja2   # Phase class template
│   ├── entry.py.jinja2   # Entry point template
│   ├── test.py.jinja2    # Test file template
│   └── readme.md.jinja2  # README template
└── validators.py         # Validation for generated code
```

### New CLI Command

```bash
flow-engine scaffold <spec_file> [options]

Options:
  --output, -o PATH       Output directory (default: current directory)
  --language, -l LANG     Target language (default: python)
  --dry-run              Show what would be generated without creating files
  --force                Overwrite existing files
  --with-tests           Generate test file stubs
  --with-docs            Generate documentation stubs
```

## Implementation Plan

### Phase 1: Core Scaffolding Generator (Priority: HIGH)

**File**: `src/control_flow_engine/scaffolding/generator.py`

```python
class ScaffoldGenerator:
    """Generate project scaffolding from control flow specifications."""
    
    def __init__(self, spec_file: Path, output_dir: Path):
        self.spec_file = spec_file
        self.output_dir = output_dir
        self.spec_data = None
        
    def generate_scaffolding(self, 
                            with_tests: bool = False,
                            with_docs: bool = False,
                            dry_run: bool = False) -> Dict[str, Path]:
        """
        Generate complete project scaffolding.
        
        Returns:
            Dict mapping component name to generated file path
        """
        # 1. Parse specification
        self.spec_data = self._parse_specification()
        
        # 2. Create directory structure
        dirs = self._create_directory_structure()
        
        # 3. Generate phase files
        phase_files = self._generate_phase_files()
        
        # 4. Generate entry point
        entry_point = self._generate_entry_point()
        
        # 5. Generate tests (if requested)
        test_files = []
        if with_tests:
            test_files = self._generate_test_files()
            
        # 6. Generate docs (if requested)
        doc_files = []
        if with_docs:
            doc_files = self._generate_documentation()
            
        return {
            'directories': dirs,
            'phases': phase_files,
            'entry_point': entry_point,
            'tests': test_files,
            'docs': doc_files
        }
```

**Features to implement**:
- ✅ Parse control_flows.yml (YAML format)
- ✅ Extract component metadata (name, version, description)
- ✅ Extract flows and phases
- ✅ Extract artifacts and their relationships
- ✅ Create phases/ directory structure (phase_1_name, phase_2_name, etc.)
- ✅ Generate phase class stubs with execute() method
- ✅ Generate entry point (run.py) that reads spec and orchestrates phases
- ✅ Handle artifact passing between phases via context dict
- ✅ Generate proper imports and dependencies
- ✅ Add docstrings with artifact information

### Phase 2: Template System (Priority: HIGH)

**Files**: `src/control_flow_engine/scaffolding/templates/*.jinja2`

Use Jinja2 templates for code generation:

#### `phase.py.jinja2`
```python
"""
Phase {{ phase.id }}: {{ phase.name }}
{{ phase.description }}
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class {{ phase.class_name }}:
    """
    {{ phase.name }}
    {{ phase.description }}
    
    Artifacts Consumed:
    {% for artifact in phase.artifacts_consumed %}
    - {{ artifact }} ({{ artifact_types[artifact] }})
    {% endfor %}
    
    Artifacts Produced:
    {% for artifact in phase.artifacts_produced %}
    - {{ artifact }} ({{ artifact_types[artifact] }})
    {% endfor %}
    """
    
    def __init__(self, project_root: Path, ui=None):
        self.project_root = project_root
        self.ui = ui
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {{ phase.name }}.
        
        Args:
            context: Dict containing:
            {% for artifact in phase.artifacts_consumed %}
                - {{ artifact }}: {{ artifact_descriptions[artifact] }}
            {% endfor %}
        
        Returns:
            Dict with:
            {% for artifact in phase.artifacts_produced %}
                - {{ artifact }}: {{ artifact_descriptions[artifact] }}
            {% endfor %}
        """
        if self.ui:
            self.ui.show_phase_header("{{ phase.name }}", "{{ phase.description }}")
        
        logger.info("{{ phase.name }} - implementation pending")
        raise NotImplementedError("{{ phase.name }} needs to be implemented")
```

#### `entry.py.jinja2`
```python
#!/usr/bin/env python3
"""
{{ component.name }} Entry Point
Reads design_specs/control_flows.yml and executes the specified flow.
"""

import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any


class {{ component.class_name }}Runner:
    """Executes {{ component.name }} flows defined in control_flows.yml"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.spec_path = self.repo_root / "design_specs" / "control_flows.yml"
        self.spec = None
        
        # Add phases to Python path
        sys.path.insert(0, str(self.repo_root))
    
    # ... rest of implementation ...
```

### Phase 3: Enhanced CLI Command (Priority: HIGH)

**File**: `src/control_flow_engine/cli/commands.py`

Add new command:

```python
@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default='.')
@click.option('--dry-run', is_flag=True, help='Show what would be generated')
@click.option('--force', is_flag=True, help='Overwrite existing files')
@click.option('--with-tests', is_flag=True, help='Generate test stubs')
@click.option('--with-docs', is_flag=True, help='Generate documentation')
def scaffold(spec_file, output, dry_run, force, with_tests, with_docs):
    """Generate project scaffolding from control flow specification."""
    try:
        from control_flow_engine.scaffolding.generator import ScaffoldGenerator
        
        spec_path = Path(spec_file)
        output_dir = Path(output)
        
        generator = ScaffoldGenerator(spec_path, output_dir)
        
        if dry_run:
            click.echo("🔍 Dry run mode - showing what would be generated:")
            preview = generator.preview_scaffolding()
            for category, items in preview.items():
                click.echo(f"\n📁 {category}:")
                for item in items:
                    click.echo(f"  - {item}")
            return
        
        # Check for existing files
        if not force and generator.check_existing_files():
            click.echo("⚠️  Some files already exist. Use --force to overwrite.")
            raise click.Abort()
        
        # Generate scaffolding
        click.echo(f"🏗️  Generating scaffolding from: {spec_path}")
        result = generator.generate_scaffolding(
            with_tests=with_tests,
            with_docs=with_docs
        )
        
        # Report results
        click.echo(f"\n✅ Scaffolding generated successfully!")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo(f"📝 Files created: {len(result['phases'])} phases, 1 entry point")
        
        if with_tests:
            click.echo(f"🧪 Test files: {len(result['tests'])}")
        if with_docs:
            click.echo(f"📚 Documentation: {len(result['docs'])}")
        
        click.echo(f"\n🚀 Next steps:")
        click.echo(f"  1. cd {output_dir}")
        click.echo(f"  2. Implement phase logic in phases/*/")
        click.echo(f"  3. Run: python3 run.py --list")
        
    except Exception as e:
        click.echo(f"❌ Scaffolding generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()
```

### Phase 4: Validation & Quality (Priority: MEDIUM)

**File**: `src/control_flow_engine/scaffolding/validators.py`

```python
class CodeValidator:
    """Validate generated code quality and structure."""
    
    def validate_phase_structure(self, phase_dir: Path) -> List[str]:
        """Validate phase directory structure."""
        issues = []
        
        # Check for __init__.py
        if not (phase_dir / "__init__.py").exists():
            issues.append(f"Missing __init__.py in {phase_dir}")
        
        # Check for required class
        # ... validation logic ...
        
        return issues
    
    def validate_imports(self, file_path: Path) -> List[str]:
        """Check that all imports are valid."""
        # ... import validation logic ...
        
    def validate_docstrings(self, file_path: Path) -> List[str]:
        """Ensure proper documentation."""
        # ... docstring validation ...
```

### Phase 5: Enhanced Templates & Examples (Priority: LOW)

**Additional templates**:
- `test_phase.py.jinja2` - Pytest test file template
- `phase_with_helper.py.jinja2` - Phase with helper module
- `README.md.jinja2` - Component README
- `ARCHITECTURE.md.jinja2` - Architecture documentation

**Example specs**:
- Create example control_flows.yml files for common patterns
- Data processing pipeline
- Web service configuration
- Multi-stage deployment

## Testing Strategy

### Unit Tests
- Test ScaffoldGenerator with mock specs
- Test template rendering
- Test directory creation
- Test file generation

### Integration Tests
- Generate scaffolding from real config-manager spec
- Verify generated code imports successfully
- Verify generated entry point works
- Compare generated structure with manual implementation

### End-to-End Test
```bash
# Generate scaffolding for a new component
flow-engine scaffold examples/simple_pipeline.yml --output /tmp/test-component

# Verify structure
cd /tmp/test-component
python3 run.py --list
python3 -c "from phases.phase_1_init import InitPhase; print('OK')"
```

## Success Metrics

✅ **Phase 1 Complete When**:
- Can generate phases/ directory structure from control_flows.yml
- Can generate phase class stubs with correct signatures
- Can generate run.py that orchestrates phases
- Generated code imports without errors

✅ **Phase 2 Complete When**:
- Template system supports customization
- Can generate different code styles (async, sync, etc.)
- Templates are maintainable and well-documented

✅ **Phase 3 Complete When**:
- CLI command works end-to-end
- Dry-run mode shows accurate preview
- Force mode handles file overwrites correctly
- Output is user-friendly with clear next steps

✅ **Overall Success When**:
- Can replicate config-manager structure in <1 minute
- Generated code quality matches hand-written code
- Other developers can use it without guidance
- Documentation is complete and clear

## Timeline Estimate

- **Phase 1** (Core Generator): 4-6 hours
- **Phase 2** (Templates): 2-3 hours  
- **Phase 3** (CLI Integration): 2-3 hours
- **Phase 4** (Validation): 2-3 hours
- **Phase 5** (Enhanced Templates): 2-3 hours
- **Testing & Documentation**: 3-4 hours

**Total**: ~15-22 hours of development

## Benefits

### For Config-Manager
- Could have generated the phases/ structure in minutes instead of manual work
- Ensures consistency across all phases
- Reduces boilerplate code writing

### For Other Components
- deploy-manager can be scaffolded quickly
- prober can follow same pattern
- Any new component gets instant structure

### For Future Development
- New flows can be prototyped rapidly
- Experimentation with different structures is fast
- Onboarding new developers is easier

## Next Immediate Steps

1. ✅ Initialize control-flow submodule (DONE)
2. ✅ Explore current capabilities (DONE - THIS DOCUMENT)
3. 🎯 **Implement Phase 1**: Core ScaffoldGenerator
4. 🎯 **Implement Phase 2**: Basic templates
5. 🎯 **Implement Phase 3**: CLI command
6. 🧪 Test with config-manager spec
7. 📚 Document usage
8. 🚀 Use for other components

## Questions to Resolve

1. **Language Support**: Start with Python-only or design for multi-language?
   - Recommendation: Python first, design for extensibility

2. **Template Engine**: Use Jinja2 or string formatting?
   - Recommendation: Jinja2 for flexibility

3. **Validation**: How strict should validation be?
   - Recommendation: Warnings for style, errors for structure

4. **Overwrite Behavior**: What's safe to overwrite?
   - Recommendation: Never overwrite by default, require --force

5. **Integration**: Generate into existing repo or new directory?
   - Recommendation: Support both via --output option

## References

- Config-Manager Implementation: `/opt/openproject/external/config-manager/`
- Control Flows Spec: `external/config-manager/design_specs/control_flows.yml`
- Current run.py: `external/config-manager/run.py`
- Phase Examples: `external/config-manager/phases/phase_*`

---

**Status**: 📋 Planning Complete - Ready for Implementation
**Next Action**: Create `src/control_flow_engine/scaffolding/generator.py`
