#!/usr/bin/env python3
"""
Scaffolding Generator for Control Flow Engine
Generates project structure from control_flows.yml specifications.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


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
    format: str  # yaml, json, cfg, etc.


@dataclass
class PhaseConfig:
    """Configuration for a single phase."""

    phase_id: str
    name: str
    description: str
    status: str
    entry_file: str  # e.g., "discovery.py"
    directory: str  # e.g., "phases/phase_1_discovery"
    steps: List[StepConfig] = field(default_factory=list)
    artifacts_produced: List[ArtifactConfig] = field(default_factory=list)
    artifacts_consumed: List[str] = field(default_factory=list)


class ScaffoldGenerator:
    """Generate project scaffolding from control flow specifications."""

    def __init__(self, spec_file: Path, output_dir: Path):
        self.spec_file = Path(spec_file)
        self.output_dir = Path(output_dir)
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
        self.component_name = self.spec_data.get("component", {}).get(
            "name", "component"
        )

        # 2. Extract phase configurations
        phases = self._extract_phases()

        if dry_run:
            return self._preview_scaffolding(phases)

        # 3. Generate structure
        result = {
            "directories": [],
            "phase_files": [],
            "step_files": [],
            "output_files": [],
            "test_files": [],
            "entry_point": [],
            "metadata": [],
        }

        # 4. Create each phase
        for phase in phases:
            phase_result = self._generate_phase(phase)
            result["directories"].extend(phase_result["directories"])
            result["phase_files"].extend(phase_result["phase_files"])
            result["step_files"].extend(phase_result["step_files"])
            result["output_files"].extend(phase_result["output_files"])
            result["test_files"].extend(phase_result.get("test_files", []))

        # 5. Generate root entry point
        entry_point = self._generate_entry_point(phases)
        result["entry_point"].append(entry_point)

        # 6. Generate metadata files
        metadata = self._generate_metadata()
        result["metadata"].extend(metadata)

        return result

    def _parse_specification(self) -> Dict[str, Any]:
        """Parse YAML control flow specification."""
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {self.spec_file}")

        with open(self.spec_file, "r") as f:
            return yaml.safe_load(f)

    def _extract_phases(self) -> List[PhaseConfig]:
        """Extract phase configurations from specification."""
        phases = []

        flows = self.spec_data.get("flows", {})
        for flow_name, flow_data in flows.items():
            phase_list = flow_data.get("phases", [])

            for idx, phase_data in enumerate(phase_list, start=1):
                phase_id = phase_data.get("phase_id")

                # Determine entry file name (phase orchestrator)
                # Default: orchestrator_{phase_id}.py
                entry_file = phase_data.get("entry_file", f"orchestrator_{phase_id}.py")

                # Determine phase directory
                phase_dir = phase_data.get("phase_directory")
                if not phase_dir:
                    phase_dir = f"phases/phase_{idx}_{phase_id}"

                # Extract steps - support both direct steps and sub_flows
                steps = []

                # First, check for direct steps in the phase definition
                for step_data in phase_data.get("steps", []):
                    step_id = step_data.get("step_id")
                    step_entry = step_data.get("entry_file", f"{step_id}.py")

                    steps.append(
                        StepConfig(
                            step_id=step_id,
                            name=step_data.get("name", step_id),
                            description=step_data.get("description", ""),
                            status=step_data.get("status", "PLANNED"),
                            entry_file=step_entry,
                        )
                    )

                # Second, check for sub_flows and extract their steps
                sub_flows = phase_data.get("sub_flows", [])
                for sub_flow_id in sub_flows:
                    # Look up the sub_flow in the flows section
                    sub_flow_data = flows.get(sub_flow_id, {})
                    for step_data in sub_flow_data.get("steps", []):
                        step_id = step_data.get("step_id")
                        step_entry = step_data.get("entry_file", f"{step_id}.py")

                        steps.append(
                            StepConfig(
                                step_id=step_id,
                                name=step_data.get("name", step_id),
                                description=step_data.get("description", ""),
                                status=step_data.get("status", "PLANNED"),
                                entry_file=step_entry,
                            )
                        )

                # Extract artifacts - handle both dict and string formats
                # Only create output files for artifacts that should be in the phase directory
                artifacts_produced = []
                for artifact in phase_data.get("artifacts_produced", []):
                    if isinstance(artifact, dict):
                        artifacts_produced.append(
                            ArtifactConfig(
                                artifact_id=artifact.get("artifact_id"),
                                output_file=artifact.get("output_file"),
                                format=artifact.get("format", "yaml"),
                            )
                        )
                    else:
                        # Simple string format (backward compatible)
                        # Look up artifact details from artifacts section
                        artifact_details = self.spec_data.get("artifacts", {}).get(
                            artifact, {}
                        )
                        location = artifact_details.get(
                            "location", f"outputs/{artifact}.yml"
                        )
                        state = artifact_details.get("state", "FILE")

                        # Only create files for artifacts that are:
                        # 1. FILE state (not IN_MEMORY)
                        # 2. Located in phase directory (start with 'output' or relative path)
                        # Skip external paths (src/...) and in-memory artifacts
                        if state == "IN_MEMORY":
                            continue
                        if location.startswith("src/") or location.startswith("/"):
                            continue
                        if "Python dict" in location or "Hardcoded" in location:
                            continue

                        # Normalize location to be relative to phase directory
                        if location.startswith("output/"):
                            # Convert output/ to outputs/
                            location = location.replace("output/", "outputs/", 1)
                        elif not location.startswith("outputs/"):
                            # Default to outputs/ directory
                            location = f"outputs/{artifact}.yml"

                        artifacts_produced.append(
                            ArtifactConfig(
                                artifact_id=artifact,
                                output_file=location,
                                format=artifact_details.get("format", "yaml"),
                            )
                        )

                phases.append(
                    PhaseConfig(
                        phase_id=phase_id,
                        name=phase_data.get("name", phase_id),
                        description=phase_data.get("description", ""),
                        status=phase_data.get("status", "PLANNED"),
                        entry_file=entry_file,
                        directory=phase_dir,
                        steps=steps,
                        artifacts_produced=artifacts_produced,
                        artifacts_consumed=phase_data.get("artifacts_consumed", []),
                    )
                )

        return phases

    def _preview_scaffolding(self, phases: List[PhaseConfig]) -> Dict[str, List[str]]:
        """Generate a preview of what would be created."""
        preview = {
            "directories": [],
            "phase_files": [],
            "step_files": [],
            "output_files": [],
            "entry_point": ["run.py"],
            "metadata": [".gitignore", "README_GENERATED.md"],
        }

        for phase in phases:
            phase_dir = phase.directory

            # Directories
            preview["directories"].append(phase_dir)
            preview["directories"].append(f"{phase_dir}/outputs")

            # Phase entry file
            preview["phase_files"].append(f"{phase_dir}/{phase.entry_file}")

            # Step directories and files (numbered)
            for idx, step in enumerate(phase.steps, start=1):
                step_dir = f"{phase_dir}/step_{idx}_{step.step_id}"
                preview["directories"].append(step_dir)
                preview["step_files"].append(f"{step_dir}/{step.entry_file}")

            # Output files
            for artifact in phase.artifacts_produced:
                preview["output_files"].append(f"{phase_dir}/{artifact.output_file}")

        return preview

    def _generate_phase(self, phase: PhaseConfig) -> Dict[str, List[Path]]:
        """Generate all files for a single phase."""
        result = {
            "directories": [],
            "phase_files": [],
            "step_files": [],
            "output_files": [],
            "test_files": [],
        }

        phase_dir = self.output_dir / phase.directory

        # Create base directories
        directories_to_create = [
            phase_dir,
            phase_dir / "outputs",
            phase_dir / "tests",
            phase_dir / "tests" / "unit",
            phase_dir / "tests" / "integration",
        ]

        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
            result["directories"].append(directory)
            logger.info(f"Created directory: {directory}")

        # Generate phase entry file
        phase_file = phase_dir / phase.entry_file
        self._write_phase_file(phase_file, phase)
        result["phase_files"].append(phase_file)

        # Generate step directories and files (numbered like phases)
        for idx, step in enumerate(phase.steps, start=1):
            step_dir_name = f"step_{idx}_{step.step_id}"
            step_dir = phase_dir / step_dir_name
            step_dir.mkdir(parents=True, exist_ok=True)
            result["directories"].append(step_dir)
            logger.info(f"Created step directory: {step_dir}")

            step_file = step_dir / step.entry_file
            self._write_step_file(step_file, step, phase)
            result["step_files"].append(step_file)

            # Generate unit test for this step
            test_file = phase_dir / "tests" / "unit" / f"test_{step.entry_file}"
            self._write_step_unit_test(test_file, step, phase, step_dir_name)
            result["test_files"].append(test_file)

        # Generate integration test for phase orchestrator
        integration_test_file = (
            phase_dir / "tests" / "integration" / f"test_{phase.entry_file}"
        )
        self._write_phase_integration_test(integration_test_file, phase)
        result["test_files"].append(integration_test_file)

        # Generate output files (empty placeholders)
        for artifact in phase.artifacts_produced:
            output_file = phase_dir / artifact.output_file
            self._write_output_file(output_file, artifact)
            result["output_files"].append(output_file)

        return result

    def _write_phase_file(self, file_path: Path, phase: PhaseConfig):
        """Write phase entry point file."""
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
        format_lower = artifact.format.lower() if artifact.format else ""
        if format_lower in ["yaml", "yml"]:
            content = f"# {artifact.artifact_id}\n# Generated by Control Flow Engine\n# This file will be populated by the phase\n"
        elif format_lower == "json":
            content = "{}\n"
        elif format_lower == "cfg":
            content = f"# {artifact.artifact_id}\n# Generated by Control Flow Engine\n"
        else:
            content = ""

        file_path.write_text(content)
        logger.info(f"Generated output file: {file_path}")

    def _generate_phase_content(self, phase: PhaseConfig) -> str:
        """Generate phase file content with PathResolver integration."""
        class_name = self._class_name_from_id(phase.phase_id)

        # Generate imports for steps with conditional handling
        step_imports = []
        step_imports_standalone = []

        if phase.steps:
            # For module context (relative imports)
            step_imports.append(
                "# Conditional imports to handle both module context and standalone execution"
            )
            step_imports.append("if __name__ == '__main__':")
            step_imports.append(
                "    # When running as standalone script, add parent to path and use absolute imports"
            )
            step_imports.append("    import sys")
            step_imports.append("    from pathlib import Path")
            step_imports.append(
                "    sys.path.insert(0, str(Path(__file__).parent.parent.parent))"
            )

            for step in phase.steps:
                module_path = step.entry_file.replace(".py", "")
                # Construct the full import path for standalone mode
                step_imports.append(
                    f"    from phases.{phase.phase_id}.steps.{module_path} import {module_path}"
                )

            # Add PathResolver import for standalone
            step_imports.append(
                "    from control_flow_engine.runtime import PathResolver, PathResolutionError"
            )

            step_imports.append("else:")
            step_imports.append("    # When imported as module, use relative imports")
            for step in phase.steps:
                module_path = step.entry_file.replace(".py", "")
                step_imports.append(
                    f"    from .steps.{module_path} import {module_path}"
                )

            # Add PathResolver import for module context
            step_imports.append(
                "    from control_flow_engine.runtime import PathResolver, PathResolutionError"
            )

        step_imports_str = "\n".join(step_imports) if step_imports else ""

        # Generate output file creation code
        output_creation = []
        for artifact in phase.artifacts_produced:
            output_creation.append(f"        # Generate {artifact.artifact_id}")
            output_creation.append(
                f"        output_file = self.phase_dir / '{artifact.output_file}'"
            )
            output_creation.append(f"        # TODO: Write actual data to output_file")
        output_creation_str = (
            "\n".join(output_creation) if output_creation else "        pass"
        )

        # Generate return dictionary
        return_items = []
        for artifact in phase.artifacts_produced:
            return_items.append(
                f"            '{artifact.artifact_id}': str(self.phase_dir / '{artifact.output_file}')"
            )
        return_dict_str = ",\n".join(return_items) if return_items else ""

        consumed_str = (
            ", ".join(phase.artifacts_consumed) if phase.artifacts_consumed else "None"
        )
        produced_str = ", ".join([a.artifact_id for a in phase.artifacts_produced])

        # Extract phase sequence from directory name (phase_N_id)
        phase_sequence = "1"  # Default
        import re

        dir_match = re.match(r".*phase_(\d+)_", phase.directory)
        if dir_match:
            phase_sequence = dir_match.group(1)

        return f'''"""
Phase: {phase.name}
{phase.description}

Generated by Control Flow Engine
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
# These constants define the phase's location in the project structure.
# They work together with PathResolver to ensure consistent path resolution.

# PHASE_SEQUENCE: Physical position in phases directory (changeable during reordering)
# Override via environment: export PHASE_SEQUENCE=N
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '{phase_sequence}'))

# PHASE_ID: Logical identifier (stable, never changes)
PHASE_ID = '{phase.phase_id}'

# Computed paths (automatically adjusted when PHASE_SEQUENCE changes)
PHASE_DIR_NAME = f"phase_{{PHASE_SEQUENCE}}_{{PHASE_ID}}"

# PROJECT_ROOT: Auto-detected or override via environment
# Override via environment: export PROJECT_ROOT=/path/to/project
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()

# PHASE_DIR: Full path to this phase's directory
PHASE_DIR = PROJECT_ROOT / "phases" / PHASE_DIR_NAME

# OUTPUT_DIR: Where this phase writes its artifacts
OUTPUT_DIR = PHASE_DIR / "outputs"

# =============================================================================

{step_imports_str}

logger = logging.getLogger(__name__)


class {class_name}:
    """
    {phase.name}
    Status: {phase.status}
    
    {phase.description}
    
    Artifacts Consumed: {consumed_str}
    Artifacts Produced: {produced_str}
    """
    
    def __init__(self, project_root: Path, ui=None, path_resolver=None):
        self.project_root = project_root
        self.ui = ui
        self.phase_dir = project_root / "{phase.directory}"
        
        # Initialize path resolver for artifact resolution
        if path_resolver:
            self.path_resolver = path_resolver
        else:
            try:
                self.path_resolver = PathResolver.from_execution_context(__file__)
            except PathResolutionError as e:
                logger.warning(f"Could not initialize PathResolver: {{e}}")
                self.path_resolver = None
        
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
        
        # Resolve input artifact paths using PathResolver
        resolved_context = context.copy()
        if self.path_resolver:
            for artifact_id in [{', '.join([f"'{a}'" for a in phase.artifacts_consumed])}]:
                try:
                    artifact_path = self.path_resolver.resolve_artifact_path(
                        artifact_id, 
                        ensure_exists=True
                    )
                    resolved_context[f'{{artifact_id}}_file'] = str(artifact_path)
                    logger.debug(f"Resolved artifact {{artifact_id}}: {{artifact_path}}")
                except PathResolutionError as e:
                    logger.warning(f"Could not resolve artifact {{artifact_id}}: {{e}}")
        
        # TODO: Implement phase logic
        # Call steps as needed:
{self._generate_step_calls(phase)}
        
        # Mock: Generate output files
{output_creation_str}
        
        # Resolve output artifact paths using PathResolver
        result = {{}}
        if self.path_resolver:
            for artifact_id in [{', '.join([f"'{a.artifact_id}'" for a in phase.artifacts_produced])}]:
                try:
                    artifact_path = self.path_resolver.resolve_artifact_path(
                        artifact_id,
                        create_parent=True
                    )
                    result[f'{{artifact_id}}_file'] = str(artifact_path)
                    logger.debug(f"Output artifact {{artifact_id}}: {{artifact_path}}")
                except PathResolutionError as e:
                    logger.error(f"Could not resolve output artifact {{artifact_id}}: {{e}}")
        else:
            # Fallback to manual path construction
            {self._generate_fallback_output_paths(phase)}
        
        logger.info("{phase.name} completed")
        return result


def main():
    """Standalone entry point for testing this phase."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="{phase.name}")
    parser.add_argument('--output-dir', help='Output directory', default=None)
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--show-paths', action='store_true', help='Display path configuration and exit')
    
    args = parser.parse_args()
    
    # Show path configuration if requested
    if args.show_paths:
        print("\\n" + "=" * 70)
        print("PATH CONFIGURATION")
        print("=" * 70)
        print(f"\\n📍 Phase Identity:")
        print(f"   PHASE_SEQUENCE: {{PHASE_SEQUENCE}}")
        print(f"   PHASE_ID: {{PHASE_ID}}")
        print(f"   PHASE_DIR_NAME: {{PHASE_DIR_NAME}}")
        print(f"\\n📂 Computed Paths:")
        print(f"   PROJECT_ROOT: {{PROJECT_ROOT}}")
        print(f"   PHASE_DIR: {{PHASE_DIR}}")
        print(f"   OUTPUT_DIR: {{OUTPUT_DIR}}")
        
        # Validate against PathResolver
        try:
            path_resolver = PathResolver.from_execution_context(__file__)
            resolver_phase_dir = path_resolver.resolve_phase_directory(PHASE_ID)
            resolver_output_dir = path_resolver.resolve_phase_output_dir(PHASE_ID)
            
            print(f"\\n✅ PathResolver Validation:")
            
            if Path(resolver_phase_dir) == PHASE_DIR:
                print(f"   Phase directory: MATCHES")
            else:
                print(f"   Phase directory: MISMATCH")
                print(f"     Computed: {{PHASE_DIR}}")
                print(f"     Resolver: {{resolver_phase_dir}}")
            
            if Path(resolver_output_dir) == OUTPUT_DIR:
                print(f"   Output directory: MATCHES")
            else:
                print(f"   Output directory: MISMATCH")
                print(f"     Computed: {{OUTPUT_DIR}}")
                print(f"     Resolver: {{resolver_output_dir}}")
        except Exception as e:
            print(f"\\n⚠️  PathResolver validation failed: {{e}}")
        
        print("\\n" + "=" * 70)
        return 0
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize PathResolver to auto-detect project structure
        path_resolver = PathResolver.from_execution_context(__file__)
        project_root = path_resolver.get_project_root()
        
        logger.info(f"Detected project root: {{project_root}}")
        
        # Initialize phase
        phase = {class_name}(project_root=project_root, ui=None, path_resolver=path_resolver)
        
        # Build context from CLI args
        context = {{}}
        
        # Execute phase
        result = phase.execute(context)
        
        print("\\n" + "=" * 70)
        print(f"✅ PHASE COMPLETE: {phase.name}")
        print("=" * 70)
        print(f"\\n📊 Phase Summary:")
        for key, value in result.items():
            print(f"  • {{key}}: {{value}}")
        
        return 0
        
    except PathResolutionError as e:
        print(f"\\n❌ Path resolution failed: {{e}}")
        print("\\nEnsure you're running from within a valid control flow project.")
        return 1
    except Exception as e:
        print(f"\\n❌ Phase failed: {{e}}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
'''

    def _generate_step_calls(self, phase: PhaseConfig) -> str:
        """Generate example step calls."""
        if not phase.steps:
            return "        # No steps defined"

        lines = []
        for step in phase.steps:
            module_name = step.entry_file.replace(".py", "")
            func_name = f"execute_{step.step_id}"
            lines.append(
                f"        # {module_name}.{func_name}(context, self.phase_dir)"
            )
        return "\n".join(lines)

    def _generate_fallback_output_paths(self, phase: PhaseConfig) -> str:
        """Generate fallback path assignments when PathResolver unavailable."""
        lines = []
        for artifact in phase.artifacts_produced:
            lines.append(
                f"            result['{artifact.artifact_id}_file'] = str(self.phase_dir / '{artifact.output_file}')"
            )
        return "\n".join(lines) if lines else "            pass"

    def _generate_step_content(self, step: StepConfig, phase: PhaseConfig) -> str:
        """Generate step file content with PathResolver integration."""
        func_name = f"execute_{step.step_id}"

        # Extract phase sequence from directory name
        phase_sequence = "1"  # Default
        import re

        dir_match = re.match(r".*phase_(\d+)_", phase.directory)
        if dir_match:
            phase_sequence = dir_match.group(1)

        return f'''"""
Step: {step.name}
{step.description}

Generated by Control Flow Engine
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging
import sys

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
# These constants define the step's location in the project structure.

# PHASE_SEQUENCE: Physical position in phases directory (changeable during reordering)
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '{phase_sequence}'))

# PHASE_ID: Logical phase identifier (stable, never changes)
PHASE_ID = '{phase.phase_id}'

# Computed paths
PHASE_DIR_NAME = f"phase_{{PHASE_SEQUENCE}}_{{PHASE_ID}}"
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent.parent)).resolve()
PHASE_DIR = PROJECT_ROOT / "phases" / PHASE_DIR_NAME
OUTPUT_DIR = PHASE_DIR / "outputs"

# =============================================================================

# Conditional imports to handle both module context and standalone execution
if __name__ == '__main__':
    # When running as standalone script, add parent to path for absolute imports
    sys.path.insert(0, str(PROJECT_ROOT))
    from control_flow_engine.runtime import PathResolver, PathResolutionError
else:
    # When imported as module, use relative imports if needed
    from control_flow_engine.runtime import PathResolver, PathResolutionError

logger = logging.getLogger(__name__)


def {func_name}(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
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


def main():
    """Standalone entry point for testing this step."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="{step.name}")
    parser.add_argument('--output-dir', help='Output directory', default=None)
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--show-paths', action='store_true', help='Display path configuration and exit')
    
    args = parser.parse_args()
    
    # Show path configuration if requested
    if args.show_paths:
        print("\\n" + "=" * 70)
        print("PATH CONFIGURATION")
        print("=" * 70)
        print(f"\\n📍 Phase Identity:")
        print(f"   PHASE_SEQUENCE: {{PHASE_SEQUENCE}}")
        print(f"   PHASE_ID: {{PHASE_ID}}")
        print(f"   PHASE_DIR_NAME: {{PHASE_DIR_NAME}}")
        print(f"\\n📂 Computed Paths:")
        print(f"   PROJECT_ROOT: {{PROJECT_ROOT}}")
        print(f"   PHASE_DIR: {{PHASE_DIR}}")
        print(f"   OUTPUT_DIR: {{OUTPUT_DIR}}")
        
        # Validate against PathResolver
        try:
            path_resolver = PathResolver.from_execution_context(__file__)
            resolver_phase_dir = path_resolver.resolve_phase_directory(PHASE_ID)
            resolver_output_dir = path_resolver.resolve_phase_output_dir(PHASE_ID)
            
            print(f"\\n✅ PathResolver Validation:")
            
            if Path(resolver_phase_dir) == PHASE_DIR:
                print(f"   Phase directory: MATCHES")
            else:
                print(f"   Phase directory: MISMATCH")
                print(f"     Computed: {{PHASE_DIR}}")
                print(f"     Resolver: {{resolver_phase_dir}}")
            
            if Path(resolver_output_dir) == OUTPUT_DIR:
                print(f"   Output directory: MATCHES")
            else:
                print(f"   Output directory: MISMATCH")
                print(f"     Computed: {{OUTPUT_DIR}}")
                print(f"     Resolver: {{resolver_output_dir}}")
        except Exception as e:
            print(f"\\n⚠️  PathResolver validation failed: {{e}}")
        
        print("\\n" + "=" * 70)
        return 0
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize path resolver from current file to auto-detect project structure
        path_resolver = PathResolver.from_execution_context(__file__)
        project_root = path_resolver.get_project_root()
        
        logger.info(f"Detected project root: {{project_root}}")
        
        # Resolve phase directory and output directory
        phase_dir = path_resolver.resolve_phase_directory('{phase.phase_id}')
        
        # If user specified output dir, use it; otherwise use resolver
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = path_resolver.resolve_phase_output_dir('{phase.phase_id}', create=True)
        
        logger.info(f"Phase directory: {{phase_dir}}")
        logger.info(f"Output directory: {{output_dir}}")
        
        # Build context from CLI args
        context = {{}}
        
        # Execute step
        result = {func_name}(context, phase_dir)
        
        print("\\n" + "=" * 70)
        print(f"✅ Step completed: {{result.get('status', 'unknown')}}")
        print("=" * 70)
        print(f"\\n📊 Results:")
        for key, value in result.items():
            if key not in ['step', 'status'] and isinstance(value, (str, int, bool)):
                print(f"  • {{key}}: {{value}}")
        
        return 0
        
    except PathResolutionError as e:
        print(f"\\n❌ Path resolution failed: {{e}}")
        print("\\nEnsure you're running from within a valid control flow project.")
        return 1
    except Exception as e:
        print(f"\\n❌ Step failed: {{e}}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
'''

    def _write_step_unit_test(
        self, file_path: Path, step: StepConfig, phase: PhaseConfig, step_dir_name: str
    ):
        """Write unit test for a step."""
        content = self._generate_step_unit_test_content(step, phase, step_dir_name)
        file_path.write_text(content)
        logger.info(f"Generated step unit test: {file_path}")

    def _write_phase_integration_test(self, file_path: Path, phase: PhaseConfig):
        """Write integration test for phase orchestrator."""
        content = self._generate_phase_integration_test_content(phase)
        file_path.write_text(content)
        logger.info(f"Generated phase integration test: {file_path}")

    def _generate_step_unit_test_content(
        self, step: StepConfig, phase: PhaseConfig, step_dir_name: str
    ) -> str:
        """Generate unit test content for a step."""
        func_name = f"execute_{step.step_id}"
        test_class_name = f"Test{step.step_id.title().replace('_', '')}"

        return f'''"""
Unit Test for Step: {step.name}
{step.description}

Generated by Control Flow Engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import importlib.util

# Load the step module dynamically
project_root = Path(__file__).parent.parent.parent.parent.parent
step_path = project_root / "{phase.directory}" / "{step_dir_name}" / "{step.entry_file}"

spec = importlib.util.spec_from_file_location("{step.step_id}", step_path)
step_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step_module)


class {test_class_name}(unittest.TestCase):
    """Unit tests for {step.name} step."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_context = {{
            'test_data': 'mock_value',
            'phase': '{phase.phase_id}'
        }}
        self.mock_phase_dir = Path('/mock/phase/dir')
    
    def test_step_execution_success(self):
        """Test successful step execution."""
        # Execute step
        result = step_module.{func_name}(self.mock_context, self.mock_phase_dir)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn('step', result)
        self.assertEqual(result['step'], '{step.step_id}')
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'completed')
    
    def test_step_execution_with_empty_context(self):
        """Test step execution with empty context."""
        empty_context = {{}}
        
        # Execute step
        result = step_module.{func_name}(empty_context, self.mock_phase_dir)
        
        # Should still return valid result
        self.assertIsInstance(result, dict)
        self.assertIn('step', result)
    
    def test_step_returns_expected_keys(self):
        """Test that step returns all expected keys."""
        result = step_module.{func_name}(self.mock_context, self.mock_phase_dir)
        
        # Check for required keys
        required_keys = ['step', 'status']
        for key in required_keys:
            self.assertIn(key, result, f"Missing required key: {{{{key}}}}")
    
    @patch('logging.getLogger')
    def test_step_logging(self, mock_logger):
        """Test that step logs appropriately."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        # Re-import to get mocked logger
        importlib.reload(step_module)
        
        # Execute step
        step_module.{func_name}(self.mock_context, self.mock_phase_dir)
        
        # Verify logging calls were made
        # Note: Actual log calls depend on implementation


if __name__ == '__main__':
    unittest.main()
'''

    def _generate_phase_integration_test_content(self, phase: PhaseConfig) -> str:
        """Generate integration test content for phase orchestrator."""
        class_name = self._class_name_from_id(phase.phase_id)
        test_class_name = f"Test{class_name}Integration"

        step_execution_checks = []
        for step in phase.steps:
            step_execution_checks.append(
                f"        # Verify {step.step_id} was executed"
            )
        step_checks_str = (
            "\n".join(step_execution_checks)
            if step_execution_checks
            else "        # No steps to verify"
        )

        consumed_artifacts = (
            ", ".join(phase.artifacts_consumed) if phase.artifacts_consumed else "None"
        )
        produced_artifacts = ", ".join(
            [a.artifact_id for a in phase.artifacts_produced]
        )

        return f'''"""
Integration Test for Phase: {phase.name}
{phase.description}

Generated by Control Flow Engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import tempfile
import shutil

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class {test_class_name}(unittest.TestCase):
    """Integration tests for {phase.name} orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_project_root = self.temp_dir
        
        # Create necessary directories
        self.phase_dir = self.mock_project_root / "{phase.directory}"
        self.phase_dir.mkdir(parents=True, exist_ok=True)
        (self.phase_dir / "outputs").mkdir(exist_ok=True)
        
        # Mock context with consumed artifacts
        self.mock_context = {{
            'project_root': str(self.mock_project_root),
            # Add consumed artifacts: {consumed_artifacts}
        }}
        
        # Mock UI
        self.mock_ui = Mock()
        self.mock_ui.show_phase_header = Mock()
        self.mock_ui.update_progress = Mock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_phase_initialization(self):
        """Test phase can be initialized."""
        # Note: This test structure assumes orchestrator follows generated pattern
        # Adjust based on actual implementation
        
        # Phase should initialize without error
        self.assertTrue(self.phase_dir.exists())
        self.assertTrue((self.phase_dir / "outputs").exists())
    
    def test_phase_context_handling(self):
        """Test phase properly handles context."""
        # Verify consumed artifacts are available
        # Consumed: {consumed_artifacts}
        
        # This is a placeholder - adjust based on actual orchestrator implementation
        self.assertIsInstance(self.mock_context, dict)
    
    def test_phase_produces_artifacts(self):
        """Test phase produces expected artifacts."""
        # Expected produced artifacts: {produced_artifacts}
        
        # This is a placeholder - implement based on actual orchestrator
        expected_artifacts = [{', '.join([f"'{a.artifact_id}'" for a in phase.artifacts_produced])}]
        
        for artifact in expected_artifacts:
            # Verify artifact would be produced
            pass
    
    def test_phase_steps_execution_order(self):
        """Test that phase executes steps in correct order."""
{step_checks_str}
        
        # This is a placeholder - implement based on actual orchestrator
        pass
    
    def test_phase_error_handling(self):
        """Test phase handles errors gracefully."""
        # Test with invalid context
        invalid_context = {{}}
        
        # Phase should handle gracefully or raise appropriate error
        # Implement based on actual orchestrator behavior
        pass
    
    def test_phase_with_ui_mock(self):
        """Test phase works with UI mock."""
        # Verify UI methods would be called
        self.assertIsNotNone(self.mock_ui)
        
        # Simulate UI interactions
        self.mock_ui.show_phase_header("{phase.name}", "{phase.description}")
        self.mock_ui.show_phase_header.assert_called_once()


if __name__ == '__main__':
    unittest.main()
'''

    def _class_name_from_id(self, phase_id: str) -> str:
        """Convert phase_id to PascalCase class name."""
        return "".join(word.capitalize() for word in phase_id.split("_")) + "Phase"

    def _generate_entry_point(self, phases: List[PhaseConfig]) -> Path:
        """Generate root entry point (run.py)."""
        entry_point = self.output_dir / "run.py"
        content = f'''#!/usr/bin/env python3
"""
{self.component_name.replace('-', ' ').title()} Entry Point
Generated by Control Flow Engine from {self.spec_file.name}

Usage:
    python3 run.py                    # Run default flow
    python3 run.py --flow <name>      # Run specific flow
    python3 run.py --list             # List available flows
"""

import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any


class {self._class_name_from_id(self.component_name.replace('-', '_'))}Runner:
    """Executes {self.component_name} flows defined in control_flows.yml"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.spec_path = self.repo_root / "design_specs" / "control_flows.yml"
        self.spec = None
        
        # Add project to path
        sys.path.insert(0, str(self.repo_root))
    
    def load_spec(self) -> Dict[str, Any]:
        """Load control_flows.yml specification."""
        if not self.spec_path.exists():
            print(f"ERROR: Control flow specification not found: {{self.spec_path}}")
            sys.exit(1)
        
        with open(self.spec_path) as f:
            self.spec = yaml.safe_load(f)
        
        return self.spec
    
    def list_flows(self):
        """List all available flows."""
        if not self.spec:
            self.load_spec()
        
        print("\\nAvailable flows:")
        for flow_name, flow_data in self.spec.get('flows', {{}}).items():
            desc = flow_data.get('description', 'No description')
            print(f"  - {{flow_name}}: {{desc}}")
        print()
    
    def execute_flow(self, flow_name: str) -> bool:
        """Execute a flow by name."""
        if not self.spec:
            self.load_spec()
        
        flows = self.spec.get('flows', {{}})
        if flow_name not in flows:
            print(f"ERROR: Flow '{{flow_name}}' not found")
            self.list_flows()
            return False
        
        flow = flows[flow_name]
        phases = flow.get('phases', [])
        
        print(f"\\nExecuting flow: {{flow_name}}")
        print(f"Description: {{flow.get('description')}}")
        print(f"Phases: {{len(phases)}}\\n")
        
        context = {{}}
        
        for idx, phase_data in enumerate(phases, start=1):
            phase_id = phase_data['phase_id']
            phase_name = phase_data['name']
            entry_file = phase_data.get('entry_file', f"{{phase_id}}.py")
            phase_dir = phase_data.get('phase_directory', f"phases/phase_{{idx}}_{{phase_id}}")
            
            print(f"→ Phase: {{phase_name}}")
            
            success = self._execute_phase(phase_id, entry_file, phase_dir, context)
            
            if not success:
                print(f"ERROR: Phase '{{phase_name}}' failed")
                return False
            
            print(f"✓ Phase '{{phase_name}}' completed\\n")
        
        print(f"✓ Flow '{{flow_name}}' completed successfully\\n")
        return True
    
    def _execute_phase(self, phase_id: str, entry_file: str, 
                      phase_dir: str, context: Dict[str, Any]) -> bool:
        """Execute a single phase."""
        try:
            # Import phase module
            module_path = phase_dir.replace('/', '.')
            module_name = entry_file.replace('.py', '')
            full_module = f"{{module_path}}.{{module_name}}"
            
            phase_module = __import__(full_module, fromlist=['*'])
            
            # Get phase class (PascalCase from phase_id)
            class_name = ''.join(word.capitalize() for word in phase_id.split('_')) + 'Phase'
            phase_class = getattr(phase_module, class_name)
            
            # Execute
            phase_instance = phase_class(project_root=self.repo_root)
            result = phase_instance.execute(context)
            
            if result:
                context.update(result)
            
            return True
            
        except NotImplementedError as e:
            print(f"NOTICE: {{e}}")
            return False
        except Exception as e:
            print(f"ERROR: {{e}}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='{self.component_name.replace("-", " ").title()}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--flow', help='Flow to execute')
    parser.add_argument('--list', action='store_true', help='List available flows')
    
    args = parser.parse_args()
    
    runner = {self._class_name_from_id(self.component_name.replace('-', '_'))}Runner()
    
    if args.list:
        runner.list_flows()
        sys.exit(0)
    
    # Get default flow from spec
    runner.load_spec()
    default_flow = list(runner.spec.get('flows', {{}}).keys())[0] if runner.spec.get('flows') else None
    flow_name = args.flow or default_flow
    
    if not flow_name:
        print("ERROR: No flow specified and no flows found in specification")
        sys.exit(1)
    
    success = runner.execute_flow(flow_name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
'''

        entry_point.write_text(content)
        entry_point.chmod(0o755)  # Make executable
        logger.info(f"Generated entry point: {entry_point}")

        return entry_point

    def _generate_metadata(self) -> List[Path]:
        """Generate metadata files (.gitignore, README, etc.)."""
        files = []

        # .gitignore
        gitignore = self.output_dir / ".gitignore"
        gitignore.write_text(
            "# Generated outputs\n"
            "*/outputs/*\n"
            "!*/outputs/.gitkeep\n"
            "*.pyc\n"
            "__pycache__/\n"
        )
        files.append(gitignore)
        logger.info(f"Generated .gitignore: {gitignore}")

        # README
        readme = self.output_dir / "README_GENERATED.md"
        readme.write_text(
            f"""# {self.component_name.replace('-', ' ').title()} - Generated Scaffolding

> **Generated by Control Flow Engine** from `{self.spec_file.name}`

## Usage

```bash
# List available flows
python3 run.py --list

# Execute default flow
python3 run.py

# Execute specific flow
python3 run.py --flow <flow_name>
```

## Structure

This scaffolding was automatically generated. Implement phase logic in each phase file and step file.

## Generated Files

- Phase entry points: Named after phase_id (e.g., `discovery.py`)
- Step implementations: In `steps/` subdirectories
- Output files: Pre-created in `outputs/` subdirectories

---

**Generated by**: Control Flow Engine  
**Source**: {self.spec_file}
"""
        )
        files.append(readme)
        logger.info(f"Generated README: {readme}")

        return files
