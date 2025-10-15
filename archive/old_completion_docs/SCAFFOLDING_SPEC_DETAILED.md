# Control Flow Scaffolding Generator - Detailed Specification

## Enhanced Requirements (Updated 2025-10-13)

### Directory Structure Design

```
component-name/
├── run.py                              # Main entry point
├── design_specs/
│   └── control_flows.yml              # Flow specification
├── phases/
│   ├── phase_1_discovery/             # Phase directory
│   │   ├── discovery.py               # Phase entry point (named after phase_id)
│   │   ├── steps/                     # Steps subdirectory
│   │   │   ├── system_scan.py         # Step 1 implementation
│   │   │   ├── network_check.py       # Step 2 implementation
│   │   │   └── defaults_generate.py   # Step 3 implementation
│   │   └── outputs/                   # Phase outputs directory
│   │       ├── discovery_data.yml     # Generated output file (can be empty)
│   │       └── system_report.json     # Generated output file (can be empty)
│   ├── phase_2_validation/
│   │   ├── validation.py              # Phase entry point (named after phase_id)
│   │   ├── steps/
│   │   │   ├── schema_check.py
│   │   │   └── dependency_check.py
│   │   └── outputs/
│   │       └── validation_report.yml
│   └── phase_3_export/
│       ├── export.py                  # Phase entry point (named after phase_id)
│       ├── steps/
│       │   ├── format_config.py
│       │   └── write_files.py
│       └── outputs/
│           └── final_config.cfg
└── output/                            # Global output directory
    └── .gitkeep
```

### Key Design Decisions

1. **No `__init__.py` for Entry Points**
   - Each phase has a dedicated entry file named after `phase_id`
   - Example: `phase_id: "discovery"` → `discovery.py`
   - Default: If no custom name specified, use `phase_id.py`

2. **Steps Subdirectory**
   - Each phase contains `steps/` directory
   - Each step is a separate Python file
   - Step file name derived from `step_id`
   - Example: `step_id: "system_scan"` → `system_scan.py`

3. **Outputs Subdirectory**
   - Each phase contains `outputs/` directory
   - Contains all artifacts produced by that phase
   - Files are pre-created (can be empty) during scaffolding
   - Mock code generates these files during execution

4. **Configurable Entry Point Names**
   - `control_flows.yml` can specify custom entry point names
   - Default behavior: use phase_id/step_id as filename

5. **Mock File Generation**
   - All output files specified in `artifacts_produced` are created
   - Files start empty (or with minimal structure)
   - Mock functions write to these files when executed

## Enhanced Control Flows YAML Schema

```yaml
component:
  name: "config-manager"
  description: "OpenProject configuration manager"
  version: "1.0.0"
  
entry_points:
  configure:
    status: "IMPLEMENTED"
    description: "Run complete configuration process"
    flow_id: "main_config_flow"
    entry_file: "run.py"  # Optional: custom entry point name

flows:
  main_config_flow:
    description: "Primary Configuration Process"
    phases:
      - phase_id: "discovery"
        name: "Discovery Phase"
        status: "IMPLEMENTED"
        description: "Discover system environment"
        entry_file: "discovery.py"  # Optional: defaults to phase_id.py
        phase_directory: "phases/phase_1_discovery"  # Optional: auto-generated
        
        # Steps within this phase
        steps:
          - step_id: "system_scan"
            name: "System Scan"
            status: "IMPLEMENTED"
            description: "Scan system information"
            entry_file: "system_scan.py"  # Optional: defaults to step_id.py
            
          - step_id: "network_check"
            name: "Network Check"
            status: "PLANNED"
            description: "Check network configuration"
            entry_file: "network_check.py"
            
          - step_id: "defaults_generate"
            name: "Generate Defaults"
            status: "IMPLEMENTED"
            description: "Generate intelligent defaults"
            entry_file: "defaults_generate.py"
        
        # Artifacts produced by this phase
        artifacts_produced:
          - artifact_id: "discovery_data"
            output_file: "outputs/discovery_data.yml"
            format: "yaml"
          - artifact_id: "system_report"
            output_file: "outputs/system_report.json"
            format: "json"
        
        # Artifacts consumed by this phase
        artifacts_consumed: []

artifacts:
  discovery_data:
    description: "System discovery information"
    state: "FILE"
    persistence: "TRANSIENT"
    location: "phases/phase_1_discovery/outputs/discovery_data.yml"
    format: "yaml"
    produced_by: ["discovery"]
    consumed_by: ["collection", "validation"]
```

## Scaffolding Generator Implementation

### Phase 1: Core Generator

**File**: `src/control_flow_engine/scaffolding/generator.py`

```python
#!/usr/bin/env python3
"""
Scaffolding Generator for Control Flow Engine
Generates project structure from control_flows.yml specifications.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PhaseConfig:
    """Configuration for a single phase."""
    phase_id: str
    name: str
    description: str
    status: str
    entry_file: str  # e.g., "discovery.py"
    directory: str   # e.g., "phases/phase_1_discovery"
    steps: List['StepConfig']
    artifacts_produced: List['ArtifactConfig']
    artifacts_consumed: List[str]


@dataclass
class StepConfig:
    """Configuration for a single step within a phase."""
    step_id: str
    name: str
    description: str
    status: str
    entry_file: str  # e.g., "system_scan.py"


@dataclass
class ArtifactConfig:
    """Configuration for an artifact."""
    artifact_id: str
    output_file: str  # Relative path from phase directory
    format: str       # yaml, json, cfg, etc.


class ScaffoldGenerator:
    """Generate project scaffolding from control flow specifications."""
    
    def __init__(self, spec_file: Path, output_dir: Path):
        self.spec_file = spec_file
        self.output_dir = output_dir
        self.spec_data = None
        self.component_name = None
        
    def generate_scaffolding(self, dry_run: bool = False) -> Dict[str, List[Path]]:
        """
        Generate complete project scaffolding.
        
        Args:
            dry_run: If True, only show what would be generated
            
        Returns:
            Dict mapping category to list of generated paths
        """
        logger.info(f"Generating scaffolding from {self.spec_file}")
        
        # 1. Parse specification
        self.spec_data = self._parse_specification()
        self.component_name = self.spec_data.get('component', {}).get('name', 'component')
        
        # 2. Extract phase configurations
        phases = self._extract_phases()
        
        # 3. Generate structure
        result = {
            'directories': [],
            'phase_files': [],
            'step_files': [],
            'output_files': [],
            'entry_point': [],
            'metadata': []
        }
        
        # 4. Create each phase
        for phase in phases:
            phase_result = self._generate_phase(phase, dry_run)
            result['directories'].extend(phase_result['directories'])
            result['phase_files'].extend(phase_result['phase_files'])
            result['step_files'].extend(phase_result['step_files'])
            result['output_files'].extend(phase_result['output_files'])
        
        # 5. Generate root entry point
        entry_point = self._generate_entry_point(phases, dry_run)
        result['entry_point'].append(entry_point)
        
        # 6. Generate metadata files
        metadata = self._generate_metadata(dry_run)
        result['metadata'].extend(metadata)
        
        return result
    
    def _parse_specification(self) -> Dict[str, Any]:
        """Parse YAML control flow specification."""
        with open(self.spec_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _extract_phases(self) -> List[PhaseConfig]:
        """Extract phase configurations from specification."""
        phases = []
        
        flows = self.spec_data.get('flows', {})
        for flow_name, flow_data in flows.items():
            phase_list = flow_data.get('phases', [])
            
            for idx, phase_data in enumerate(phase_list, start=1):
                phase_id = phase_data.get('phase_id')
                
                # Determine entry file name
                entry_file = phase_data.get('entry_file', f"{phase_id}.py")
                
                # Determine phase directory
                phase_dir = phase_data.get('phase_directory')
                if not phase_dir:
                    phase_dir = f"phases/phase_{idx}_{phase_id}"
                
                # Extract steps
                steps = []
                for step_data in phase_data.get('steps', []):
                    step_id = step_data.get('step_id')
                    step_entry = step_data.get('entry_file', f"{step_id}.py")
                    
                    steps.append(StepConfig(
                        step_id=step_id,
                        name=step_data.get('name', step_id),
                        description=step_data.get('description', ''),
                        status=step_data.get('status', 'PLANNED'),
                        entry_file=step_entry
                    ))
                
                # Extract artifacts
                artifacts_produced = []
                for artifact in phase_data.get('artifacts_produced', []):
                    if isinstance(artifact, dict):
                        artifacts_produced.append(ArtifactConfig(
                            artifact_id=artifact.get('artifact_id'),
                            output_file=artifact.get('output_file'),
                            format=artifact.get('format', 'yaml')
                        ))
                    else:
                        # Simple string format (backward compatible)
                        artifacts_produced.append(ArtifactConfig(
                            artifact_id=artifact,
                            output_file=f"outputs/{artifact}.yml",
                            format='yaml'
                        ))
                
                phases.append(PhaseConfig(
                    phase_id=phase_id,
                    name=phase_data.get('name', phase_id),
                    description=phase_data.get('description', ''),
                    status=phase_data.get('status', 'PLANNED'),
                    entry_file=entry_file,
                    directory=phase_dir,
                    steps=steps,
                    artifacts_produced=artifacts_produced,
                    artifacts_consumed=phase_data.get('artifacts_consumed', [])
                ))
        
        return phases
    
    def _generate_phase(self, phase: PhaseConfig, dry_run: bool) -> Dict[str, List[Path]]:
        """Generate all files for a single phase."""
        result = {
            'directories': [],
            'phase_files': [],
            'step_files': [],
            'output_files': []
        }
        
        phase_dir = self.output_dir / phase.directory
        
        # Create directories
        directories_to_create = [
            phase_dir,
            phase_dir / 'steps',
            phase_dir / 'outputs'
        ]
        
        for directory in directories_to_create:
            if not dry_run:
                directory.mkdir(parents=True, exist_ok=True)
            result['directories'].append(directory)
        
        # Generate phase entry file
        phase_file = phase_dir / phase.entry_file
        if not dry_run:
            self._write_phase_file(phase_file, phase)
        result['phase_files'].append(phase_file)
        
        # Generate step files
        for step in phase.steps:
            step_file = phase_dir / 'steps' / step.entry_file
            if not dry_run:
                self._write_step_file(step_file, step, phase)
            result['step_files'].append(step_file)
        
        # Generate output files (empty placeholders)
        for artifact in phase.artifacts_produced:
            output_file = phase_dir / artifact.output_file
            if not dry_run:
                self._write_output_file(output_file, artifact)
            result['output_files'].append(output_file)
        
        return result
    
    def _write_phase_file(self, file_path: Path, phase: PhaseConfig):
        """Write phase entry point file."""
        # Generate from template (Phase 2 of implementation)
        content = self._generate_phase_content(phase)
        file_path.write_text(content)
        logger.info(f"Generated phase file: {file_path}")
    
    def _write_step_file(self, file_path: Path, step: StepConfig, phase: PhaseConfig):
        """Write step implementation file."""
        content = self._generate_step_content(step, phase)
        file_path.write_text(content)
        logger.info(f"Generated step file: {file_path}")
    
    def _write_output_file(self, file_path: Path, artifact: ArtifactConfig):
        """Write empty output file placeholder."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create appropriate empty structure based on format
        if artifact.format == 'yaml':
            content = "# Generated by Control Flow Engine\n# This file will be populated by the phase\n{}\n"
        elif artifact.format == 'json':
            content = "{}\n"
        else:
            content = ""
        
        file_path.write_text(content)
        logger.info(f"Generated output file: {file_path}")
    
    def _generate_phase_content(self, phase: PhaseConfig) -> str:
        """Generate phase file content (will use Jinja2 template in Phase 2)."""
        # Temporary implementation - will be replaced with Jinja2
        return f'''"""
Phase: {phase.name}
{phase.description}
Generated by Control Flow Engine
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class {self._class_name_from_id(phase.phase_id)}:
    """
    {phase.name}
    Status: {phase.status}
    
    {phase.description}
    
    Artifacts Consumed: {", ".join(phase.artifacts_consumed) if phase.artifacts_consumed else "None"}
    Artifacts Produced: {", ".join([a.artifact_id for a in phase.artifacts_produced])}
    """
    
    def __init__(self, project_root: Path, ui=None):
        self.project_root = project_root
        self.ui = ui
        self.phase_dir = project_root / "{phase.directory}"
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {phase.name}.
        
        Args:
            context: Execution context with consumed artifacts
            
        Returns:
            Dict with produced artifacts
        """
        if self.ui:
            self.ui.show_phase_header("{phase.name}", "{phase.description}")
        
        logger.info("Executing {phase.name}")
        
        # TODO: Implement phase logic
        # Import and call steps as needed
        
        # Mock: Generate output files
        {self._generate_output_creation_code(phase)}
        
        logger.info("{phase.name} completed")
        
        return {{
            {self._generate_return_dict(phase)}
        }}
'''
    
    def _generate_step_content(self, step: StepConfig, phase: PhaseConfig) -> str:
        """Generate step file content."""
        return f'''"""
Step: {step.name}
{step.description}
Generated by Control Flow Engine
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def execute_{step.step_id}(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    {step.name}
    Status: {step.status}
    
    {step.description}
    
    Args:
        context: Execution context
        phase_dir: Phase directory path
        
    Returns:
        Dict with step results
    """
    logger.info("Executing step: {step.name}")
    
    # TODO: Implement step logic
    
    result = {{
        'step': '{step.step_id}',
        'status': 'completed'
    }}
    
    logger.info("Step {step.name} completed")
    return result
'''
    
    def _generate_output_creation_code(self, phase: PhaseConfig) -> str:
        """Generate code to create output files."""
        lines = []
        for artifact in phase.artifacts_produced:
            lines.append(f"        # Generate {artifact.artifact_id}")
            lines.append(f"        output_file = self.phase_dir / '{artifact.output_file}'")
            lines.append(f"        # TODO: Write actual data to output_file")
        return "\n".join(lines) if lines else "        pass"
    
    def _generate_return_dict(self, phase: PhaseConfig) -> str:
        """Generate return dictionary for phase."""
        items = []
        for artifact in phase.artifacts_produced:
            items.append(f"'{artifact.artifact_id}': str(self.phase_dir / '{artifact.output_file}')")
        return ",\n            ".join(items) if items else ""
    
    def _class_name_from_id(self, phase_id: str) -> str:
        """Convert phase_id to PascalCase class name."""
        return ''.join(word.capitalize() for word in phase_id.split('_')) + 'Phase'
    
    def _generate_entry_point(self, phases: List[PhaseConfig], dry_run: bool) -> Path:
        """Generate root entry point (run.py)."""
        entry_point = self.output_dir / "run.py"
        
        if not dry_run:
            content = self._generate_entry_point_content(phases)
            entry_point.write_text(content)
            entry_point.chmod(0o755)  # Make executable
        
        return entry_point
    
    def _generate_entry_point_content(self, phases: List[PhaseConfig]) -> str:
        """Generate entry point content."""
        # Will be replaced with Jinja2 template
        return f'''#!/usr/bin/env python3
"""
{self.component_name.replace('-', ' ').title()} Entry Point
Generated by Control Flow Engine
"""

import sys
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("Entry point generated - implement flow orchestration")
sys.exit(0)
'''
    
    def _generate_metadata(self, dry_run: bool) -> List[Path]:
        """Generate metadata files (.gitignore, README, etc.)."""
        files = []
        
        # .gitignore
        gitignore = self.output_dir / '.gitignore'
        if not dry_run:
            gitignore.write_text("# Generated outputs\n*/outputs/*\n!*/outputs/.gitkeep\n")
        files.append(gitignore)
        
        return files
```

### Usage Example

```bash
# Generate scaffolding for config-manager
cd /opt/openproject/external/control-flow
python3 -m control_flow_engine.cli.commands scaffold \
    ../config-manager/design_specs/control_flows.yml \
    --output ../config-manager \
    --dry-run

# Without dry-run to actually create files
python3 -m control_flow_engine.cli.commands scaffold \
    ../config-manager/design_specs/control_flows.yml \
    --output /tmp/test-component
```

## Next Steps

1. **Implement Core Generator** (This document provides the spec)
2. **Add Jinja2 Templates** (Replace string formatting)
3. **Integrate with CLI** (Add scaffold command)
4. **Test with Config-Manager** (Use real spec)
5. **Refine Based on Feedback** (Iterate on design)

## Success Criteria

✅ Generates phases/ directories with custom names
✅ Creates entry files named after phase_id (not __init__.py)
✅ Creates steps/ subdirectory with individual step files
✅ Creates outputs/ subdirectory with placeholder files
✅ Mock functions generate specified output files
✅ All files have proper structure and documentation
✅ Generated code imports without errors
