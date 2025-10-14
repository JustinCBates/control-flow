# Control Flow System - Complete Reference

**Version:** 2.0  
**Last Updated:** October 14, 2025  
**Purpose:** Complete reference for the control-flow engine system - use this document to recover full understanding of the system architecture, patterns, and capabilities.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Concepts](#core-concepts)
3. [Architecture](#architecture)
4. [YAML-Driven Design](#yaml-driven-design)
5. [Orchestrator Pattern](#orchestrator-pattern)
6. [Units & Libraries Pattern](#units--libraries-pattern)
7. [Generator Tools](#generator-tools)
8. [Runtime System](#runtime-system)
9. [Best Practices](#best-practices)
10. [Migration & Evolution](#migration--evolution)

---

## System Overview

### What is Control Flow?

The **Control Flow System** is a YAML-driven workflow orchestration engine that enables declarative definition of multi-phase, multi-step processes. It provides:

- **Declarative specification** - Define workflows in YAML, execute dynamically
- **Hierarchical organization** - Flows → Phases → Steps → Units
- **Automatic code generation** - Generate orchestrators from YAML specs
- **Runtime flexibility** - Workflows adapt based on YAML configuration
- **Reusable components** - Shared units organized in domain libraries

### Design Philosophy

**Key Principles:**

1. **YAML is the source of truth** - Structure defined in YAML, not hardcoded
2. **Generate, don't handwrite** - Use generators for boilerplate
3. **Runtime flexibility** - Read YAML dynamically at runtime
4. **Single responsibility** - Each component does one thing well
5. **Composability** - Build complex workflows from simple components

**The Control Flow Way:**

```
❌ Old Way: Hardcode workflow logic in Python
✅ New Way: Define workflow in YAML, generate orchestrators, execute dynamically
```

---

## Core Concepts

### Hierarchy

```
Flow (e.g., main_config_flow)
└── Phase (e.g., discovery)
    ├── Step (e.g., system_discovery)
    │   └── Units (e.g., docker_detector, network_detector)
    │       └── From Libraries (e.g., libraries/probing/)
    └── Step (e.g., env_discovery)
        └── Units (e.g., env_scanner)
```

### Components

#### 1. Flow

**Definition:** A complete end-to-end workflow

**Characteristics:**
- Contains multiple phases
- Has entry points (CLI commands)
- Produces final artifacts
- Orchestrated by global orchestrator

**Example:**
```yaml
flows:
  main_config_flow:
    description: Primary Configuration Process
    orchestrator: phases/phases_orchestrator.py::PhasesOrchestrator
    phases:
      - discovery
      - tui_mapping
      - collection
      - validation
      - export
```

#### 2. Phase

**Definition:** A major segment of work with clear inputs/outputs

**Characteristics:**
- Contains multiple steps
- Has phase-level orchestrator
- Produces/consumes artifacts
- Can be executed independently

**Example:**
```yaml
phases:
  - phase_id: discovery
    name: Discovery Phase
    status: IMPLEMENTED
    orchestrator_file: phases/phase_1_discovery/orchestrator_discovery.py
    steps:
      - env_discovery
      - system_discovery
      - defaults_generation
```

#### 3. Step

**Definition:** An atomic unit of work within a phase

**Characteristics:**
- Single purpose/responsibility
- Produces specific artifacts
- Can depend on other steps
- Orchestrates units

**Example:**
```yaml
steps:
  - step_id: system_discovery
    name: System Discovery
    type: discovery
    status: IMPLEMENTED
    sequence: 2
    dependencies:
      - env_discovery
    artifacts_produced:
      - system_data
      - docker_data
      - network_data
    units:
      - docker_detector
      - network_detector
      - system_detector
```

#### 4. Unit

**Definition:** A file-level single-responsibility component

**Characteristics:**
- Reusable across steps/phases
- Organized in domain libraries
- Independently testable
- Domain-specific interface (detect, validate, transform, etc.)

**Example:**
```yaml
units:
  - unit_id: docker_detector
    library: probing
    class: DockerDiscovery
    method: discover
    description: Discovers Docker environment and existing containers
```

---

## Architecture

### Directory Structure

```
control-flow/
├── src/
│   └── control_flow_engine/
│       ├── core/
│       │   ├── orchestrator_regenerator.py    # Generator tool
│       │   ├── scaffolder.py                  # Scaffolding tool
│       │   └── yaml_processor.py              # YAML parsing
│       └── runtime/
│           ├── path_resolver.py               # Runtime path resolution
│           └── context_manager.py             # Execution context
├── templates/
│   ├── phase_orchestrator.py.j2              # Phase orchestrator template
│   ├── global_orchestrator.py.j2             # Global orchestrator template
│   ├── step_template.py.j2                   # Step template
│   └── library_init.py.j2                    # Library __init__ template
├── docs/
│   ├── CONTROL_FLOW_SYSTEM_REFERENCE.md      # This document
│   ├── UNITS_LIBRARIES_PATTERN.md            # Units & Libraries guide
│   ├── LIBRARY_GENERATOR_USAGE.md            # Generator usage
│   └── ARCHITECTURE_DISCUSSION_OCT14.md      # Historical discussions
└── examples/
    └── graphviz_test/                         # Visualization examples
```

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| `orchestrator_regenerator.py` | Generate orchestrators from YAML | YAML spec | Python orchestrators |
| `scaffolder.py` | Create initial project structure | Project params | Directory structure |
| `yaml_processor.py` | Parse and validate YAML specs | YAML file | Python objects |
| `path_resolver.py` | Resolve paths at runtime | Relative paths | Absolute paths |
| Templates (Jinja2) | Define orchestrator structure | YAML data | Generated Python |

---

## YAML-Driven Design

### Why YAML?

The control-flow system is **intentionally YAML-driven** because:

1. **Single source of truth** - Structure defined once, used everywhere
2. **Runtime flexibility** - Change workflow without code changes
3. **Documentation** - YAML serves as living documentation
4. **Validation** - Can validate structure before execution
5. **Tooling** - Generators can create code from YAML
6. **Non-programmer friendly** - Easier to understand than code

### YAML Specification Structure

```yaml
# Entry points define CLI commands
entry_points:
  configure:
    description: Run complete configuration process
    flow_id: main_config_flow

# Flows define complete workflows
flows:
  main_config_flow:
    description: Primary Configuration Process
    orchestrator: phases/phases_orchestrator.py::PhasesOrchestrator
    phases:
      - phase_id: discovery
        name: Discovery Phase
        steps:
          - step_id: system_discovery
            name: System Discovery
            type: discovery
            units:
              - unit_id: docker_detector
                library: probing
                class: DockerDiscovery
                method: discover
```

### Runtime YAML Usage

**Orchestrators read YAML dynamically:**

```python
# Global orchestrator loads YAML at runtime
class PhasesOrchestrator:
    def __init__(self, spec_file: Path):
        self.spec = yaml.safe_load(spec_file.read_text())
        self.flow = self.spec['flows']['main_config_flow']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Execute phases based on YAML
        for phase_spec in self.flow['phases']:
            phase_id = phase_spec['phase_id']
            # Dynamic execution based on YAML
```

**This enables:**
- Adding new phases without code changes
- Reordering phases via YAML
- Conditional execution based on YAML
- Different workflows for different scenarios

---

## Orchestrator Pattern

### Three Levels of Orchestrators

#### 1. Global Orchestrator

**Purpose:** Execute entire flow (all phases)

**Location:** `phases/phases_orchestrator.py`

**Responsibilities:**
- Load YAML specification
- Initialize execution context
- Execute phases in sequence
- Aggregate results
- Handle errors/recovery

**Example:**
```python
class PhasesOrchestrator:
    """Global orchestrator for main configuration flow."""
    
    def __init__(self, spec_file: Path):
        """Initialize with YAML spec."""
        self.spec = yaml.safe_load(spec_file.read_text())
        self.flow = self.spec['flows']['main_config_flow']
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all phases."""
        for phase_spec in self.flow['phases']:
            phase_id = phase_spec['phase_id']
            phase_result = self._execute_phase(phase_id, context)
            context.update(phase_result)
        return context
```

#### 2. Phase Orchestrator

**Purpose:** Execute all steps within a phase

**Location:** `phases/phase_X_name/orchestrator_name.py`

**Responsibilities:**
- Load YAML for this phase
- Execute steps in sequence
- Pass artifacts between steps
- Produce phase-level outputs

**Example:**
```python
class DiscoveryPhase:
    """Phase orchestrator for discovery."""
    
    def __init__(self, spec_file: Path):
        """Initialize with YAML spec."""
        self.spec = yaml.safe_load(spec_file.read_text())
        self.phase = self._find_phase('discovery')
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all steps in discovery phase."""
        for step_spec in self.phase['steps']:
            step_id = step_spec['step_id']
            step_result = self._execute_step(step_id, context)
            context.update(step_result)
        return context
```

#### 3. Step Execution Function

**Purpose:** Execute single atomic task

**Location:** `phases/phase_X_name/step_Y_name/step_name.py`

**Responsibilities:**
- Orchestrate units
- Process input artifacts
- Produce output artifacts
- Handle step-specific logic

**Example:**
```python
def execute_system_discovery(
    context: Dict[str, Any],
    phase_dir: Path
) -> Dict[str, Any]:
    """Execute system discovery step."""
    # Import units from libraries
    from phases.libraries.probing import (
        DockerDiscovery,
        NetworkDiscovery,
        SystemDiscovery
    )
    
    # Orchestrate units
    docker_data = DockerDiscovery().discover()
    network_data = NetworkDiscovery().discover()
    system_data = SystemDiscovery().discover()
    
    # Return results
    return {
        'docker_data': docker_data,
        'network_data': network_data,
        'system_data': system_data
    }
```

### Generated Markers

Orchestrators use markers to separate generated from handwritten code:

```python
# === GENERATED: STEP_IMPORTS - DO NOT EDIT ===
from .step_1_env_discovery.env_discovery import execute_env_discovery
from .step_2_system_discovery.system_discovery import execute_system_discovery
# === END GENERATED: STEP_IMPORTS ===

# === INFRASTRUCTURE IMPORTS - DO NOT REGENERATE ===
import os
import sys
from pathlib import Path
try:
    from control_flow_engine.runtime import PathResolver
except ImportError:
    PathResolver = None
# === END INFRASTRUCTURE IMPORTS ===
```

**Markers serve two purposes:**

1. **During regeneration** - Generator knows what to update vs preserve
2. **For developers** - Clear what's auto-generated vs handwritten

---

## Units & Libraries Pattern

### Overview

**Units** are file-level single-responsibility components that can be shared across steps and phases. **Libraries** are domain-organized collections of related units.

### Why Units?

**Problems without units:**
- Code duplication across steps
- Hard to test granular functionality
- Unclear what's reusable vs step-specific
- No organization for shared components

**Solutions with units:**
- DRY principle enforced
- Units tested independently
- Clear library organization
- Discoverability of reusable components

### Library Organization

```
phases/libraries/
├── __init__.py
├── probing/                    # Discovery & detection
│   ├── __init__.py
│   ├── docker_detector.py
│   ├── network_detector.py
│   ├── system_detector.py
│   └── port_checker.py
├── validation/                 # Validation & checking
│   ├── __init__.py
│   ├── schema_validator.py
│   ├── dependency_checker.py
│   └── config_validator.py
├── transformation/             # Data transformation
│   ├── __init__.py
│   ├── config_transformer.py
│   └── defaults_mapper.py
├── io/                        # File operations
│   ├── __init__.py
│   ├── yaml_handler.py
│   └── json_handler.py
└── export/                    # Export generation
    ├── __init__.py
    ├── docker_compose_generator.py
    └── env_generator.py
```

### Domain Method Conventions

Units use domain-specific method names:

| Library | Primary Method | Purpose | Example |
|---------|---------------|---------|---------|
| `probing` | `detect()` | Discover system state | `docker_detector.detect()` |
| `validation` | `validate()` | Check validity | `schema_validator.validate()` |
| `transformation` | `transform()` | Convert data | `config_transformer.transform()` |
| `io` | `load()` / `write()` | Read/write data | `yaml_handler.load()` |
| `export` | `generate()` | Create output | `env_generator.generate()` |

### Unit Structure Template

```python
# phases/libraries/probing/docker_detector.py
"""
Docker detection unit.

Unit: DockerDiscovery
Library: probing
Domain Method: discover()

Used by:
    - phase_1_discovery/step_2_system_discovery
    - phase_4_validation/step_3_environment_validation

Stability: Stable (v1.0.0)
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class DockerDiscovery:
    """
    Unit: Detect Docker installation and status.
    
    Single Responsibility: Check if Docker is installed and running.
    
    Interface:
        discover() -> Dict[str, Any]
    
    Returns:
        {
            'installed': bool,
            'running': bool,
            'version': str or None,
            'compose_available': bool
        }
    """
    
    def __init__(self):
        """Initialize Docker detector."""
        self.docker_available = False
        self.docker_client = None
    
    def discover(self) -> Dict[str, Any]:
        """
        Detect Docker installation and running status.
        
        Returns:
            Dictionary with Docker status information
        """
        try:
            import docker
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            
            return {
                'installed': True,
                'running': True,
                'version': self.docker_client.version()['Version'],
                'compose_available': True
            }
        except ImportError:
            logger.warning("Docker package not available")
            return {
                'installed': False,
                'running': False,
                'version': None,
                'compose_available': False
            }
        except Exception as e:
            logger.warning(f"Docker not accessible: {e}")
            return {
                'installed': True,
                'running': False,
                'version': None,
                'compose_available': False
            }
```

### Library __init__.py

```python
# phases/libraries/probing/__init__.py
"""
Probing Library

System and environment discovery units for detecting Docker, network,
system resources, ports, and services.

Units:
    - DockerDiscovery: Check Docker installation/status
    - NetworkDiscovery: Detect network configuration
    - SystemDiscovery: Detect system resources
    - PortChecker: Check port availability

Stability: Stable
Version: 1.0.0
"""

from .docker_detector import DockerDiscovery
from .network_detector import NetworkDiscovery
from .system_detector import SystemDiscovery
from .port_checker import PortChecker

__all__ = [
    'DockerDiscovery',
    'NetworkDiscovery',
    'SystemDiscovery',
    'PortChecker'
]

__version__ = '1.0.0'
```

### Using Units in Steps

```python
# phases/phase_1_discovery/step_2_system_discovery/system_discovery.py
"""
Step: System Discovery

Uses units from libraries:
    - libraries.probing (DockerDiscovery, NetworkDiscovery, SystemDiscovery)
"""

from pathlib import Path
from typing import Dict, Any
import logging

# Import from libraries
from phases.libraries.probing import (
    DockerDiscovery,
    NetworkDiscovery,
    SystemDiscovery
)

logger = logging.getLogger(__name__)


def execute_system_discovery(
    context: Dict[str, Any],
    phase_dir: Path
) -> Dict[str, Any]:
    """
    Execute system discovery using library units.
    
    Units used:
        - DockerDiscovery: Checks Docker installation and status
        - NetworkDiscovery: Detects network configuration
        - SystemDiscovery: Detects system resources
    
    Args:
        context: Execution context
        phase_dir: Phase directory path
        
    Returns:
        Dict with system_data, docker_data, network_data
    """
    logger.info("Executing step: System Discovery")
    
    # Instantiate and execute units
    docker_discovery = DockerDiscovery()
    network_discovery = NetworkDiscovery()
    system_discovery = SystemDiscovery()
    
    # Execute units (order doesn't matter - independent)
    docker_data = docker_discovery.discover()
    network_data = network_discovery.discover()
    system_data = system_discovery.discover()
    
    # Aggregate results
    return {
        'docker_data': docker_data,
        'network_data': network_data,
        'system_data': system_data
    }
```

### Decision Guidelines

#### When to Create a Unit?

✅ **CREATE a unit when:**
- Logic has single, clear responsibility
- Logic is >50 lines of code
- Logic is used by 2+ steps
- Logic needs independent testing
- Logic is complex/error-prone
- You want to swap implementations (e.g., mock for testing)

❌ **DON'T create a unit when:**
- Logic is <50 lines and simple
- Logic is specific to one step only
- Just a utility function (put in `utils/` instead)
- Logic is trivial/obvious

#### When to Create a Library?

✅ **CREATE a library when:**
- You have 3+ related units
- Clear domain theme emerges
- Units will be shared across phases
- Want to version/stabilize a set of units

❌ **DON'T create a library when:**
- Only 1-2 units exist
- No clear domain theme
- Units are too diverse
- Over-engineering for current needs

#### Where to Put a Unit?

**Decision Tree:**

```
1. Is this unit used by multiple steps?
   ├─ NO → Co-locate with step
   │        Example: step_2_foo/bar_unit.py
   └─ YES → Does a library exist for this domain?
            ├─ YES → Add to library
            │        Example: libraries/probing/new_detector.py
            └─ NO → Do you have 3+ units in this domain?
                     ├─ YES → Create library
                     │        Example: libraries/new_domain/
                     └─ NO → Co-locate, extract later
                              Example: step_2_foo/bar_unit.py
```

### Declaring Units in YAML

Units can be declared in YAML for documentation and testing:

```yaml
steps:
  - step_id: system_discovery
    name: System Discovery
    type: discovery
    units:
      - unit_id: docker_detector
        library: probing
        class: DockerDiscovery
        method: discover
        description: Discovers Docker environment and existing containers
      
      - unit_id: network_detector
        library: probing
        class: NetworkDiscovery
        method: discover
        description: Discovers network configuration and interfaces
      
      - unit_id: system_detector
        library: probing
        class: SystemDiscovery
        method: discover
        description: Discovers system information (OS, CPU, memory, disk)
```

**Benefits:**
- Documentation - Clear which units a step uses
- Validation - Can verify units exist in libraries
- Dependency tracking - Understand step dependencies
- Testing support - Can generate mocks

**Note:** YAML declaration is **optional** - units work without YAML declaration, but declaring them enables additional tooling and documentation.

---

## Generator Tools

### Orchestrator Regenerator

**Purpose:** Generate and regenerate orchestrators from YAML specs

**Location:** `src/control_flow_engine/core/orchestrator_regenerator.py`

**Usage:**

```bash
# Generate global orchestrator
python3 orchestrator_regenerator.py \
    --spec control_flows.yml \
    --type global \
    --orchestrator phases/phases_orchestrator.py \
    --flow main_config_flow

# Generate phase orchestrator
python3 orchestrator_regenerator.py \
    --spec control_flows.yml \
    --type phase \
    --orchestrator phases/phase_1_discovery/orchestrator_discovery.py \
    --phase-id discovery \
    --flow main_config_flow

# Generate library __init__.py
python3 orchestrator_regenerator.py \
    --spec control_flows.yml \
    --type library \
    --library-name probing \
    --flow main_config_flow
```

**What it does:**
- Reads YAML specification
- Generates orchestrator code from templates
- Preserves handwritten code outside markers
- Updates imports based on YAML
- Safe to run multiple times (idempotent)

**Markers it manages:**

```python
# === GENERATED: STEP_IMPORTS - DO NOT EDIT ===
# Auto-generated imports
# === END GENERATED: STEP_IMPORTS ===

# === GENERATED: STEP_EXECUTION - DO NOT EDIT ===
# Auto-generated step execution
# === END GENERATED: STEP_EXECUTION ===

# === INFRASTRUCTURE IMPORTS - DO NOT REGENERATE ===
# Preserved infrastructure imports
# === END INFRASTRUCTURE IMPORTS ===
```

### Scaffolder

**Purpose:** Create initial project structure for new projects

**Location:** `src/control_flow_engine/core/scaffolder.py`

**Usage:**

```bash
# Create new control-flow project
python3 scaffolder.py \
    --name my_project \
    --output-dir /path/to/output \
    --phases discovery,collection,validation,export
```

**What it creates:**
- Directory structure (phases/, design_specs/, etc.)
- Initial YAML specification
- Phase and step templates
- README documentation
- Basic orchestrators

---

## Runtime System

### Path Resolver

**Purpose:** Resolve relative paths to absolute at runtime

**Location:** `src/control_flow_engine/runtime/path_resolver.py`

**Usage:**

```python
from control_flow_engine.runtime import PathResolver, PathResolutionError

# Initialize with base path
resolver = PathResolver(base_path=Path('/opt/project'))

# Resolve relative paths
abs_path = resolver.resolve('phases/phase_1_discovery')
# Returns: Path('/opt/project/phases/phase_1_discovery')

# Resolve with validation
abs_path = resolver.resolve('outputs/data.yml', must_exist=True)
# Raises PathResolutionError if doesn't exist
```

**Features:**
- Converts relative → absolute paths
- Validates path existence (optional)
- Handles Path objects and strings
- Thread-safe
- Caches resolutions

### Context Manager

**Purpose:** Manage execution context across phases/steps

**Location:** `src/control_flow_engine/runtime/context_manager.py`

**Usage:**

```python
from control_flow_engine.runtime import ContextManager

# Initialize context
context = ContextManager()

# Store artifacts
context.set_artifact('discovery_data', discovery_results)

# Retrieve artifacts
discovery_data = context.get_artifact('discovery_data')

# Check artifact existence
if context.has_artifact('validated_config'):
    # Use it
```

---

## Best Practices

### 1. YAML First, Code Second

❌ **Bad:** Hardcode workflow in Python
```python
def execute_workflow():
    run_discovery()
    run_collection()
    run_validation()
    run_export()
```

✅ **Good:** Define workflow in YAML
```yaml
flows:
  main_flow:
    phases:
      - discovery
      - collection
      - validation
      - export
```

### 2. Use Markers Properly

❌ **Bad:** Edit generated sections
```python
# === GENERATED: STEP_IMPORTS - DO NOT EDIT ===
from .step_1_foo.foo import execute_foo
from .my_custom_import import something  # ❌ Will be lost
# === END GENERATED: STEP_IMPORTS ===
```

✅ **Good:** Add custom imports outside markers
```python
# === GENERATED: STEP_IMPORTS - DO NOT EDIT ===
from .step_1_foo.foo import execute_foo
# === END GENERATED: STEP_IMPORTS ===

# Custom imports (preserved during regeneration)
from .my_custom_import import something
```

### 3. Single Responsibility Units

❌ **Bad:** Multi-purpose unit
```python
class SystemAnalyzer:
    def detect_docker(self): ...
    def detect_network(self): ...
    def validate_config(self): ...  # ❌ Too many responsibilities
```

✅ **Good:** Focused units
```python
class DockerDiscovery:
    def discover(self): ...  # ✅ One responsibility

class NetworkDiscovery:
    def discover(self): ...  # ✅ One responsibility
```

### 4. Domain-Specific Methods

❌ **Bad:** Generic method names
```python
class DockerDetector:
    def run(self): ...  # ❌ Too generic
    def execute(self): ...  # ❌ Not domain-specific
```

✅ **Good:** Domain method names
```python
class DockerDiscovery:
    def discover(self): ...  # ✅ Probing domain

class SchemaValidator:
    def validate(self): ...  # ✅ Validation domain
```

### 5. Document Unit Usage

❌ **Bad:** No documentation
```python
class DockerDetector:
    def detect(self): ...
```

✅ **Good:** Document where used
```python
class DockerDiscovery:
    """
    Unit: Detect Docker installation.
    
    Library: probing
    Used by:
        - phase_1_discovery/step_2_system_discovery
        - phase_4_validation/step_3_environment_validation
    
    Stability: Stable (v1.0.0)
    """
    def discover(self): ...
```

### 6. Return Structured Data

❌ **Bad:** Tuple returns
```python
def detect(self) -> Tuple[bool, str]:
    return (True, '24.0.7')  # ❌ Hard to extend
```

✅ **Good:** Dictionary returns
```python
def discover(self) -> Dict[str, Any]:
    return {
        'installed': True,
        'version': '24.0.7',
        'metadata': {...}  # ✅ Easy to extend
    }
```

---

## Migration & Evolution

### Adopting Control Flow in Existing Projects

**Phase 1: Assessment**
1. Identify current workflow structure
2. Map to Flow → Phase → Step hierarchy
3. Identify reusable components (future units)

**Phase 2: YAML Specification**
1. Create `control_flows.yml`
2. Define flows and phases
3. Define steps with dependencies
4. Declare artifacts

**Phase 3: Generate Orchestrators**
1. Use orchestrator_regenerator to create orchestrators
2. Migrate existing logic into step functions
3. Test each phase independently

**Phase 4: Extract Units**
1. Identify duplicated code across steps
2. Create libraries for domains
3. Extract units from steps
4. Update imports to use libraries

**Phase 5: Continuous Evolution**
1. Add new phases via YAML
2. Regenerate orchestrators as needed
3. Extract new units as patterns emerge
4. Version libraries for stability

### Version Management

**Semantic Versioning for Libraries:**

```
Version: MAJOR.MINOR.PATCH

MAJOR: Breaking interface changes
MINOR: New features, backward compatible
PATCH: Bug fixes, backward compatible
```

**Example:**
```python
# phases/libraries/probing/__init__.py
__version__ = '1.2.3'

# Breaking change: v1 → v2
class DockerDiscovery:
    def discover(self):  # v1.x.x
        ...
    
    def detect(self):    # v2.0.0 (renamed method)
        ...
```

---

## Summary

### Key Takeaways

1. **YAML drives everything** - Structure in YAML, execute dynamically
2. **Hierarchy is clear** - Flow → Phase → Step → Unit
3. **Generators reduce boilerplate** - Use tools, don't handwrite
4. **Units enable reuse** - Build libraries of domain components
5. **Runtime flexibility** - Change workflows via YAML updates

### Quick Reference

| Need | Solution |
|------|----------|
| Define workflow | Create/edit `control_flows.yml` |
| Generate orchestrator | Run `orchestrator_regenerator.py` |
| Add new phase | Add to YAML, regenerate global orchestrator |
| Add new step | Add to YAML, regenerate phase orchestrator |
| Share code between steps | Create unit in appropriate library |
| Create new library | Make `libraries/domain_name/` directory |
| Test in isolation | Write unit tests for units |
| Change workflow order | Update YAML sequence numbers |

### Common Patterns

**Adding a new phase:**
1. Add phase to `control_flows.yml`
2. Create phase directory `phases/phase_X_name/`
3. Create step directories under phase
4. Generate phase orchestrator
5. Regenerate global orchestrator

**Adding a new step:**
1. Add step to phase in `control_flows.yml`
2. Create step directory `phases/phase_X/step_Y_name/`
3. Implement step function `execute_step_name()`
4. Regenerate phase orchestrator

**Creating a library:**
1. Create `phases/libraries/domain_name/`
2. Create `__init__.py` with exports
3. Add unit files (e.g., `some_detector.py`)
4. Import in steps: `from phases.libraries.domain_name import Unit`

---

## Additional Resources

- **UNITS_LIBRARIES_PATTERN.md** - Detailed units & libraries guide
- **LIBRARY_GENERATOR_USAGE.md** - Library generation examples
- **ARCHITECTURE_DISCUSSION_OCT14.md** - Historical architecture decisions
- **examples/** - Example projects using control-flow

---

**Document Status:** Complete and current  
**Maintenance:** Update when system architecture changes  
**Purpose:** Context recovery and onboarding reference
