#!/usr/bin/env python3
"""
Orchestrator Regenerator - Regenerates static execution sections from spec.

Key Features:
1. Parse existing orchestrator files
2. Identify generated sections via markers
3. Regenerate sections from control_flows.yml
4. Preserve custom code (logging setup, helper methods, etc.)
5. Update imports and PHASE_CLASSES registry

Marker Convention:
    # === GENERATED: <section_name> - DO NOT EDIT ===
    ... auto-generated code ...
    # === END GENERATED: <section_name> ===
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml


class OrchestratorRegenerator:
    """Regenerates orchestrator code from specification."""
    
    # Marker patterns
    MARKER_START = "# === GENERATED: {section} - DO NOT EDIT ==="
    MARKER_END = "# === END GENERATED: {section} ==="
    
    # Known generated sections
    SECTIONS = {
        'IMPORTS': 'Phase imports',
        'REGISTRY': 'Phase class registry',
        'SEQUENCE': 'Static execution sequence',
        'STATIC_EXECUTION': 'Static execution method body'
    }
    
    def __init__(self, spec_file: Path):
        """
        Initialize regenerator.
        
        Args:
            spec_file: Path to control_flows.yml
        """
        self.spec_file = spec_file
        self.spec = self._load_spec()
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load specification from YAML file."""
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {self.spec_file}")
        
        with open(self.spec_file, 'r') as f:
            return yaml.safe_load(f)
    
    def regenerate_global_orchestrator(
        self,
        orchestrator_file: Path,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Regenerate global phases orchestrator (e.g., phases_orchestrator.py).
        
        Args:
            orchestrator_file: Path to orchestrator file
            flow_name: Name of flow to generate for
            
        Returns:
            True if successful
        """
        print(f"Regenerating global orchestrator: {orchestrator_file}")
        
        # Get flow from spec
        flow = self.spec.get('flows', {}).get(flow_name)
        if not flow:
            print(f"❌ Flow '{flow_name}' not found in spec")
            return False
        
        phases = flow.get('phases', [])
        if not phases:
            print(f"⚠️  Flow '{flow_name}' has no phases")
            return True
        
        # Read existing file if it exists
        if orchestrator_file.exists():
            original_content = orchestrator_file.read_text()
        else:
            # Create from template
            original_content = self._get_global_orchestrator_template()
        
        # Regenerate each section
        new_content = original_content
        
        # 1. Imports
        imports = self._generate_phase_imports(phases)
        new_content = self._replace_section(new_content, 'IMPORTS', imports)
        
        # 2. Registry
        registry = self._generate_phase_registry(phases)
        new_content = self._replace_section(new_content, 'REGISTRY', registry)
        
        # 3. Sequence
        sequence = self._generate_phase_sequence(phases)
        new_content = self._replace_section(new_content, 'SEQUENCE', sequence)
        
        # 4. Static execution
        execution = self._generate_static_execution(phases)
        new_content = self._replace_section(new_content, 'STATIC_EXECUTION', execution)
        
        # Write updated file
        orchestrator_file.write_text(new_content)
        print(f"✅ Regenerated {orchestrator_file.name}")
        
        return True
    
    def regenerate_phase_orchestrator(
        self,
        orchestrator_file: Path,
        phase_id: str,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Regenerate phase-level orchestrator (e.g., orchestrator_discovery.py).
        
        Args:
            orchestrator_file: Path to phase orchestrator file
            phase_id: ID of the phase
            flow_name: Name of flow containing the phase
            
        Returns:
            True if successful
        """
        print(f"Regenerating phase orchestrator: {orchestrator_file}")
        
        # Get phase from spec
        flow = self.spec.get('flows', {}).get(flow_name)
        if not flow:
            print(f"❌ Flow '{flow_name}' not found in spec")
            return False
        
        phase = None
        for p in flow.get('phases', []):
            if p.get('phase_id') == phase_id:
                phase = p
                break
        
        if not phase:
            print(f"❌ Phase '{phase_id}' not found in flow '{flow_name}'")
            return False
        
        steps = phase.get('steps', [])
        if not steps:
            print(f"⚠️  Phase '{phase_id}' has no steps")
            return True
        
        # Read existing file
        if not orchestrator_file.exists():
            print(f"❌ Orchestrator file not found: {orchestrator_file}")
            return False
        
        original_content = orchestrator_file.read_text()
        new_content = original_content
        
        # 1. Step imports
        imports = self._generate_step_imports(steps, phase)
        new_content = self._replace_section(new_content, 'STEP_IMPORTS', imports)
        
        # 2. Check if infrastructure imports section exists after STEP_IMPORTS
        # If not, add a placeholder comment to guide users
        if '# Infrastructure imports' not in new_content:
            # Find the END GENERATED: STEP_IMPORTS marker
            step_imports_end = self.MARKER_END.format(section='STEP_IMPORTS')
            if step_imports_end in new_content:
                # Add infrastructure imports template after the marker
                infrastructure_template = self._get_infrastructure_imports_template()
                new_content = new_content.replace(
                    step_imports_end,
                    f"{step_imports_end}\n\n{infrastructure_template}"
                )
        
        # 3. Step execution
        execution = self._generate_step_execution(steps, phase)
        new_content = self._replace_section(new_content, 'STEP_EXECUTION', execution)
        
        # Write updated file
        orchestrator_file.write_text(new_content)
        print(f"✅ Regenerated {orchestrator_file.name}")
        
        return True
    
    def generate_library(
        self,
        library_name: str,
        output_dir: Optional[Path] = None,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Generate library __init__.py file with smart detection of existing units.
        
        Only generates mock implementations for units that don't have real
        implementations yet. Preserves existing unit files.
        
        Args:
            library_name: Name of library (e.g., 'probing', 'validation')
            output_dir: Output directory (default: spec_dir/phases/libraries/)
            flow_name: Name of flow to generate for
            
        Returns:
            True if successful
        """
        print(f"Generating library: {library_name}")
        
        # Determine output directory
        if output_dir is None:
            spec_dir = self.spec_file.parent.parent  # Go up from design_specs/
            output_dir = spec_dir / "phases" / "libraries" / library_name
        
        # Create library directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get flow from spec
        flow = self.spec.get('flows', {}).get(flow_name)
        if not flow:
            print(f"❌ Flow '{flow_name}' not found in spec")
            return False
        
        # Collect all units for this library across all phases/steps
        library_units = []
        
        phases = flow.get('phases', [])
        for phase in phases:
            steps = phase.get('steps', [])
            for step in steps:
                units = step.get('units', [])
                for unit in units:
                    if unit.get('library') == library_name:
                        # Avoid duplicates (same unit used by multiple steps)
                        unit_id = unit.get('unit_id')
                        if not any(u.get('unit_id') == unit_id for u in library_units):
                            library_units.append(unit)
        
        if not library_units:
            print(f"⚠️  No units found for library '{library_name}'")
            return True
        
        # Detect which units already have implementations
        existing_units = self._detect_existing_units(output_dir, library_units)
        
        # Generate __init__.py file
        init_file = output_dir / "__init__.py"
        
        # If __init__.py exists, update it; otherwise create new
        if init_file.exists():
            content = self._update_library_init(
                init_file, library_name, library_units, existing_units
            )
        else:
            content = self._generate_library_init(
                library_name, library_units, existing_units
            )
        
        init_file.write_text(content)
        print(f"✅ Generated {init_file}")
        print(f"   - {len(library_units)} units total")
        print(f"   - {len(existing_units)} existing implementations")
        print(f"   - {len(library_units) - len(existing_units)} mock implementations")
        
        return True
    
    def _detect_existing_units(
        self,
        library_dir: Path,
        units: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Detect which units already have real implementations.
        
        Args:
            library_dir: Directory containing unit files
            units: List of unit specifications
            
        Returns:
            List of unit_ids that have existing implementations
        """
        existing = []
        
        for unit in units:
            unit_id = unit.get('unit_id')
            # Check for expected file name patterns
            possible_files = [
                library_dir / f"{unit_id}.py",
                library_dir / f"{unit_id}_unit.py",
                library_dir / unit.get('file', f"{unit_id}.py"),
            ]
            
            for unit_file in possible_files:
                if unit_file.exists():
                    # Verify it contains the expected class
                    class_name = unit.get('class', self._to_class_name(unit_id))
                    if self._file_contains_class(unit_file, class_name):
                        existing.append(unit_id)
                        print(f"   📁 Found existing: {unit_file.name} ({class_name})")
                        break
        
        return existing
    
    def _file_contains_class(self, file_path: Path, class_name: str) -> bool:
        """
        Check if a Python file contains a class definition.
        
        Args:
            file_path: Path to Python file
            class_name: Class name to search for
            
        Returns:
            True if class is found
        """
        try:
            content = file_path.read_text()
            # Simple check for class definition
            return f"class {class_name}" in content
        except Exception:
            return False
    
    def _to_class_name(self, unit_id: str) -> str:
        """Convert unit_id to ClassName format."""
        return unit_id.replace('_', ' ').title().replace(' ', '')
    
    def _update_library_init(
        self,
        init_file: Path,
        library_name: str,
        units: List[Dict[str, Any]],
        existing_units: List[str]
    ) -> str:
        """
        Update existing __init__.py file with new units.
        
        Preserves existing content between markers and updates generated sections.
        
        Args:
            init_file: Path to existing __init__.py
            library_name: Name of the library
            units: List of all unit specifications
            existing_units: List of unit_ids with existing implementations
            
        Returns:
            Updated __init__.py content
        """
        original_content = init_file.read_text()
        
        # Generate new import section
        imports_section = self._generate_library_imports(units, existing_units)
        
        # Generate new mock section
        mocks_section = self._generate_mock_units(units, existing_units)
        
        # Replace LIBRARY_IMPORTS section
        new_content = self._replace_between_markers(
            original_content,
            'LIBRARY_IMPORTS',
            imports_section
        )
        
        # Replace MOCK_UNITS section
        new_content = self._replace_between_markers(
            new_content,
            'MOCK_UNITS',
            mocks_section
        )
        
        return new_content
    
    def _replace_between_markers(
        self,
        content: str,
        marker_name: str,
        new_content: str
    ) -> str:
        """
        Replace content between markers.
        
        Args:
            content: Original content
            marker_name: Name of marker section
            new_content: New content to insert
            
        Returns:
            Updated content
        """
        start_marker = f"# === GENERATED: {marker_name} - DO NOT EDIT ==="
        end_marker = f"# === END GENERATED: {marker_name} ==="
        
        if start_marker not in content or end_marker not in content:
            # Markers don't exist, append at end
            return content + f"\n{start_marker}\n{new_content}\n{end_marker}\n"
        
        # Find marker positions
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker) + len(end_marker)
        
        # Replace content between markers
        return (
            content[:start_pos] +
            f"{start_marker}\n{new_content}\n{end_marker}" +
            content[end_pos:]
        )
    
    def _generate_library_imports(
        self,
        units: List[Dict[str, Any]],
        existing_units: List[str]
    ) -> str:
        """Generate import statements for library units."""
        lines = []
        
        for unit in units:
            unit_id = unit.get('unit_id')
            class_name = unit.get('class', self._to_class_name(unit_id))
            
            if unit_id in existing_units:
                # Real import for existing units
                file_name = unit.get('file', f"{unit_id}.py")
                module_name = file_name.replace('.py', '')
                lines.append(f"from .{module_name} import {class_name}")
            else:
                # Commented import for missing units (use mock instead)
                file_name = unit.get('file', f"{unit_id}.py")
                module_name = file_name.replace('.py', '')
                lines.append(f"# from .{module_name} import {class_name}  # TODO: Implement real unit")
        
        return '\n'.join(lines)
    
    def _generate_mock_units(
        self,
        units: List[Dict[str, Any]],
        existing_units: List[str]
    ) -> str:
        """Generate mock implementations for units that don't exist yet."""
        lines = [
            "# Mock implementations for testing (when real units not available)",
            "",
        ]
        
        mocks_generated = 0
        
        for unit in units:
            unit_id = unit.get('unit_id')
            
            if unit_id not in existing_units:
                # Generate mock for this unit
                class_name = unit.get('class', self._to_class_name(unit_id))
                method_name = unit.get('method', 'execute')
                mock_response = unit.get('mock_response', {})
                description = unit.get('description', 'No description')
                
                lines.extend([
                    "",
                    f"class Mock{class_name}:",
                    f'    """Mock implementation of {class_name} for testing."""',
                    f"    ",
                    f"    def {method_name}(self):",
                    f'        """',
                    f'        {description}',
                    f'        ',
                    f'        Returns mock data for testing.',
                    f'        """',
                    f"        return {mock_response!r}",
                ])
                
                mocks_generated += 1
        
        if mocks_generated == 0:
            lines.append("# All units have real implementations - no mocks needed")
        
        return '\n'.join(lines)
    
    def _generate_library_init(
        self,
        library_name: str,
        units: List[Dict[str, Any]],
        existing_units: List[str]
    ) -> str:
        """
        Generate __init__.py content for a new library.
        
        Args:
            library_name: Name of the library
            units: List of unit specifications from YAML
            existing_units: List of unit_ids with existing implementations
            
        Returns:
            Generated __init__.py content
        """
        from datetime import datetime
        
        # Header
        lines = [
            f'"""',
            f'{library_name.title()} Library',
            f'',
            f'Auto-generated from control_flows.yml',
            f'Generated at: {datetime.now().isoformat()}',
            f'',
            f'Units:',
        ]
        
        # List units in docstring
        for unit in units:
            unit_id = unit.get('unit_id')
            class_name = unit.get('class', self._to_class_name(unit_id))
            description = unit.get('description', 'No description')
            status = '✅' if unit_id in existing_units else '🔨'
            lines.append(f'    {status} {class_name}: {description}')
        
        lines.extend([
            f'',
            f'Legend:',
            f'    ✅ = Real implementation exists',
            f'    🔨 = Using mock implementation (TODO: create real unit)',
            f'"""',
            f'',
        ])
        
        # Imports section
        lines.append(f'# === GENERATED: LIBRARY_IMPORTS - DO NOT EDIT ===')
        imports = self._generate_library_imports(units, existing_units)
        lines.append(imports)
        lines.append(f'# === END GENERATED: LIBRARY_IMPORTS ===')
        lines.append(f'')
        
        # __all__ export (include both real and mock classes)
        lines.append(f'__all__ = [')
        for unit in units:
            unit_id = unit.get('unit_id')
            class_name = unit.get('class', self._to_class_name(unit_id))
            if unit_id in existing_units:
                lines.append(f'    \'{class_name}\',  # Real implementation')
            else:
                lines.append(f'    \'Mock{class_name}\',  # Using mock until real unit is implemented')
        lines.append(f']')
        lines.append(f'')
        lines.append(f'__version__ = \'1.0.0\'')
        lines.append(f'')
        lines.append(f'')
        
        # Mock implementations section
        lines.append(f'# === GENERATED: MOCK_UNITS - DO NOT EDIT ===')
        mocks = self._generate_mock_units(units, existing_units)
        lines.append(mocks)
        lines.append(f'# === END GENERATED: MOCK_UNITS ===')
        lines.append(f'')
        
        return '\n'.join(lines)
    
    def _replace_section(
        self,
        content: str,
        section_name: str,
        new_code: str
    ) -> str:
        """
        Replace a marked section with new code.
        
        Args:
            content: Original file content
            section_name: Name of section to replace
            new_code: New code to insert
            
        Returns:
            Updated content
        """
        start_marker = self.MARKER_START.format(section=section_name)
        end_marker = self.MARKER_END.format(section=section_name)
        
        # Pattern to match section
        pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker)
        
        # Replacement text (includes markers)
        replacement = f"{start_marker}\n{new_code}\n{end_marker}"
        
        # Replace section
        new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
        
        if count == 0:
            print(f"⚠️  Section marker not found: {section_name}")
            print(f"   Add markers to enable regeneration:")
            print(f"   {start_marker}")
            print(f"   {end_marker}")
        
        return new_content
    
    def _generate_phase_imports(self, phases: List[Dict[str, Any]]) -> str:
        """Generate phase import statements."""
        lines = []
        
        for phase in sorted(phases, key=lambda p: p.get('sequence', 0)):
            phase_id = phase['phase_id']
            sequence = phase.get('sequence', 1)
            impl = phase.get('implementation', {})
            
            # Get class name from implementation or derive it
            class_name = impl.get('class', f"{phase_id.title().replace('_', '')}Phase")
            
            # Module path
            module = impl.get('module', f"phases.phase_{sequence}_{phase_id}")
            orchestrator_module = f".phase_{sequence}_{phase_id}.orchestrator_{phase_id}"
            
            lines.append(f"from {orchestrator_module} import {class_name}")
        
        return '\n'.join(lines)
    
    def _generate_phase_registry(self, phases: List[Dict[str, Any]]) -> str:
        """Generate PHASE_CLASSES registry dict."""
        lines = ["PHASE_CLASSES = {"]
        
        for phase in sorted(phases, key=lambda p: p.get('sequence', 0)):
            phase_id = phase['phase_id']
            impl = phase.get('implementation', {})
            class_name = impl.get('class', f"{phase_id.title().replace('_', '')}Phase")
            
            lines.append(f"    '{phase_id}': {class_name},")
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _generate_phase_sequence(self, phases: List[Dict[str, Any]]) -> str:
        """Generate STATIC_SEQUENCE list."""
        lines = ["STATIC_SEQUENCE = ["]
        
        for phase in sorted(phases, key=lambda p: p.get('sequence', 0)):
            phase_id = phase['phase_id']
            sequence = phase.get('sequence', 1)
            status = phase.get('status', 'planned')
            
            lines.append(f"    {{'phase_id': '{phase_id}', 'sequence': {sequence}, 'status': '{status}'}},")
        
        lines.append("]")
        
        return '\n'.join(lines)
    
    def _generate_static_execution(self, phases: List[Dict[str, Any]]) -> str:
        """Generate static execution method body."""
        lines = []
        total = len(phases)
        
        for i, phase in enumerate(sorted(phases, key=lambda p: p.get('sequence', 0)), 1):
            phase_id = phase['phase_id']
            phase_name = phase.get('name', phase_id)
            impl = phase.get('implementation', {})
            class_name = impl.get('class', f"{phase_id.title().replace('_', '')}Phase")
            
            lines.append(f"# Phase {i}: {phase_name} (sequence={phase.get('sequence', i)})")
            lines.append(f'logger.info("=" * 70)')
            lines.append(f'logger.info("Phase {i}/{total}: {phase_name}")')
            lines.append(f'logger.info("=" * 70)')
            lines.append(f"{phase_id}_phase = {class_name}(self.project_root, self.ui)")
            lines.append(f"{phase_id}_result = {phase_id}_phase.execute(context)")
            lines.append(f"context.update({phase_id}_result.get('artifacts', {{}}))")
            lines.append(f'logger.info(f"✅ {phase_name} completed")')
            lines.append("")
        
        lines.append('logger.info("=" * 70)')
        lines.append('logger.info("✅ All phases completed successfully")')
        lines.append('logger.info("=" * 70)')
        lines.append("")
        lines.append("return context")
        
        return '\n        '.join(lines)  # Indent for method body
    
    def _generate_step_imports(
        self,
        steps: List[Dict[str, Any]],
        phase: Dict[str, Any]
    ) -> str:
        """Generate step import statements for phase orchestrator."""
        lines = []
        phase_id = phase['phase_id']
        phase_seq = phase.get('sequence', 1)
        
        # Generate conditional imports for both standalone and module usage
        lines.append("# Handle both relative imports (when called by parent) and absolute imports (when run standalone)")
        lines.append("if __name__ == '__main__':")
        lines.append("    # Running standalone - use absolute imports")
        lines.append("    sys.path.insert(0, str(Path(__file__).parent.parent.parent))")
        
        # Absolute imports for standalone
        for step in sorted(steps, key=lambda s: s.get('sequence', 0)):
            step_id = step['step_id']
            sequence = step.get('sequence', 0)
            class_name = f"{step_id.title().replace('_', '')}Step"
            abs_import = f"phases.phase_{phase_seq}_{phase_id}.step_{sequence}_{step_id}.{step_id}"
            lines.append(f"    from {abs_import} import {class_name}")
        
        lines.append("else:")
        lines.append("    # When imported as module, use relative imports")
        
        # Relative imports for module usage
        for step in sorted(steps, key=lambda s: s.get('sequence', 0)):
            step_id = step['step_id']
            sequence = step.get('sequence', 0)
            class_name = f"{step_id.title().replace('_', '')}Step"
            rel_import = f".step_{sequence}_{step_id}.{step_id}"
            lines.append(f"    from {rel_import} import {class_name}")
        
        return '\n'.join(lines)
    
    def _generate_step_execution(
        self,
        steps: List[Dict[str, Any]],
        phase: Dict[str, Any]
    ) -> str:
        """Generate step execution code for phase orchestrator."""
        lines = []
        total = len(steps)
        
        for i, step in enumerate(sorted(steps, key=lambda s: s.get('sequence', 0)), 1):
            step_id = step['step_id']
            step_name = step.get('name', step_id)
            description = step.get('description', step_name)
            sequence = step.get('sequence', 0)
            
            # Derive class name
            class_name = f"{step_id.title().replace('_', '')}Step"
            
            lines.append(f"# Step {i}: {description}")
            lines.append(f'logger.info("Step {i}: {description}")')
            lines.append(f"step_{i} = {class_name}(self.project_root, self.ui)")
            lines.append(f"step_result = step_{i}.execute(context)")
            lines.append(f'context.update(step_result.get("artifacts", {{}}))')
            lines.append(f'result["artifacts"].update(step_result.get("artifacts", {{}}))')
            lines.append("")
        
        return '\n        '.join(lines)  # Indent for method body
    
    def _get_infrastructure_imports_template(self) -> str:
        """
        Get template for infrastructure imports section.
        
        This template is added after STEP_IMPORTS if not already present.
        It provides common infrastructure imports that phases may need.
        """
        return """# Infrastructure imports (preserved, not regenerated)
# Add phase-specific infrastructure imports here:
# - PathResolver for artifact resolution
# - Custom utilities or helpers
# - External dependencies
#
# Example:
# try:
#     from control_flow_engine.runtime import PathResolver, PathResolutionError
# except ImportError:
#     PathResolver = None
#     PathResolutionError = Exception"""
    
    def _get_global_orchestrator_template(self) -> str:
        """Get template for new global orchestrator."""
        return '''"""
Global Phases Orchestrator

Generated by: Control Flow Engine
DO NOT EDIT sections marked with GENERATED comments
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging

# === GENERATED: IMPORTS - DO NOT EDIT ===
# Phase imports will be generated here
# === END GENERATED: IMPORTS ===

logger = logging.getLogger(__name__)


class PhasesOrchestrator:
    """Global orchestrator for phases."""
    
    # === GENERATED: REGISTRY - DO NOT EDIT ===
    PHASE_CLASSES = {}
    # === END GENERATED: REGISTRY ===
    
    # === GENERATED: SEQUENCE - DO NOT EDIT ===
    STATIC_SEQUENCE = []
    # === END GENERATED: SEQUENCE ===
    
    def __init__(
        self,
        project_root: Path,
        ui: Optional[Any] = None,
        mode: str = "static"
    ):
        self.project_root = project_root
        self.ui = ui
        self.mode = mode
    
    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the complete flow."""
        context = context or {}
        
        if self.mode == "static":
            return self._execute_static(context)
        else:
            return self._execute_dynamic(context)
    
    def _execute_static(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using generated static sequence."""
        logger.info("Executing in STATIC mode")
        
        # === GENERATED: STATIC_EXECUTION - DO NOT EDIT ===
        # Static execution sequence will be generated here
        return context
        # === END GENERATED: STATIC_EXECUTION ===
    
    def _execute_dynamic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using runtime spec (custom implementation)."""
        logger.info("Executing in DYNAMIC mode")
        # Custom dynamic execution logic here
        return context
'''
    
    def regenerate_dual_mode_phase(
        self,
        orchestrator_file: Path,
        phase_id: str,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Regenerate phase orchestrator with dual-mode support using Jinja2 template.
        
        This generates a phase orchestrator that supports both 'hardcoded' and 'dynamic' modes.
        NEVER clobbers existing implementations - only fills in missing parts.
        
        Args:
            orchestrator_file: Path to phase orchestrator file
            phase_id: ID of the phase
            flow_name: Name of flow containing the phase
            
        Returns:
            True if successful
        """
        print(f"Regenerating dual-mode phase orchestrator: {orchestrator_file}")
        
        # Get phase from spec
        flow = self.spec.get('flows', {}).get(flow_name)
        if not flow:
            print(f"❌ Flow '{flow_name}' not found in spec")
            return False
        
        phase = None
        for p in flow.get('phases', []):
            if p.get('phase_id') == phase_id:
                phase = p
                break
        
        if not phase:
            print(f"❌ Phase '{phase_id}' not found in flow '{flow_name}'")
            return False
        
        # Prepare template data
        phase_data = self._prepare_phase_template_data(phase, flow)
        
        # Check if orchestrator exists
        if orchestrator_file.exists():
            # Update existing orchestrator (preserve handwritten code)
            return self._update_dual_mode_orchestrator(orchestrator_file, phase_data)
        else:
            # Generate new dual-mode orchestrator from template
            return self._generate_dual_mode_orchestrator(orchestrator_file, phase_data)
    
    def _prepare_phase_template_data(
        self,
        phase: Dict[str, Any],
        flow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare data for Jinja2 template rendering.
        
        Args:
            phase: Phase specification from YAML
            flow: Flow specification from YAML
            
        Returns:
            Dict with template data
        """
        # Derive class name from phase_id
        phase_id = phase.get('phase_id', '')
        class_name = ''.join(word.capitalize() for word in phase_id.split('_')) + 'Phase'
        
        # Prepare steps data
        steps = []
        for step in phase.get('steps', []):
            step_id = step.get('step_id', '')
            step_class_name = ''.join(word.capitalize() for word in step_id.split('_')) + 'Step'
            steps.append({
                'step_id': step_id,
                'name': step.get('name', step_id),
                'description': step.get('description', ''),
                'status': step.get('status', 'PLANNED'),
                'class_name': step_class_name,
                'units': step.get('units', [])
            })
        
        return {
            'phase': {
                'phase_id': phase_id,
                'name': phase.get('name', phase_id),
                'description': phase.get('description', ''),
                'status': phase.get('status', 'PLANNED'),
                'class_name': class_name,
                'phase_directory': phase.get('implementation', {}).get('phase_directory', f'phases/phase_{phase_id}'),
                'artifacts_produced': phase.get('artifacts_produced', []),
                'artifacts_consumed': phase.get('artifacts_consumed', []),
                'steps': steps
            },
            'flow': {
                'flow_id': flow.get('flow_id', 'main_config_flow'),
                'description': flow.get('description', '')
            }
        }
    
    def _generate_dual_mode_orchestrator(
        self,
        orchestrator_file: Path,
        phase_data: Dict[str, Any]
    ) -> bool:
        """
        Generate new dual-mode orchestrator from Jinja2 template.
        
        Args:
            orchestrator_file: Path to orchestrator file to create
            phase_data: Prepared template data
            
        Returns:
            True if successful
        """
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            
            # Find template directory
            template_dir = Path(__file__).parent.parent.parent.parent / 'templates'
            
            if not template_dir.exists():
                print(f"❌ Template directory not found: {template_dir}")
                return False
            
            # Setup Jinja2 environment
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Load template
            template = env.get_template('phase_orchestrator_dual_mode.py.j2')
            
            # Render template
            content = template.render(**phase_data)
            
            # Write file
            orchestrator_file.parent.mkdir(parents=True, exist_ok=True)
            orchestrator_file.write_text(content)
            
            print(f"✅ Generated dual-mode orchestrator: {orchestrator_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate dual-mode orchestrator: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_dual_mode_orchestrator(
        self,
        orchestrator_file: Path,
        phase_data: Dict[str, Any]
    ) -> bool:
        """
        Update existing orchestrator to add dual-mode support.
        
        NEVER clobbers existing implementations. Only adds missing methods/sections.
        
        Args:
            orchestrator_file: Path to existing orchestrator file
            phase_data: Prepared template data
            
        Returns:
            True if successful
        """
        print(f"Updating existing orchestrator (preserving handwritten code)...")
        
        try:
            original_content = orchestrator_file.read_text()
            
            # Check what's missing
            has_mode_param = 'mode:' in original_content or 'mode =' in original_content
            has_execute_dynamic = '_execute_dynamic' in original_content
            has_execute_hardcoded = '_execute_hardcoded' in original_content
            
            if has_mode_param and has_execute_dynamic:
                print("  ℹ️  Orchestrator already has dual-mode support")
                # Still regenerate STEP_IMPORTS and STEP_EXECUTION markers
                return self.regenerate_phase_orchestrator(
                    orchestrator_file=orchestrator_file,
                    phase_id=phase_data['phase']['phase_id'],
                    flow_name=phase_data['flow']['flow_id']
                )
            
            # Read as lines for easier manipulation
            lines = original_content.split('\n')
            
            # Add mode parameter to __init__ if missing
            if not has_mode_param:
                lines = self._add_mode_parameter(lines)
                print("  ✅ Added mode parameter to __init__")
            
            # Add _execute_dynamic method if missing
            if not has_execute_dynamic:
                dynamic_method = self._generate_execute_dynamic_method(phase_data)
                lines = self._insert_method_before_execute(lines, dynamic_method, '_execute_dynamic')
                print("  ✅ Added _execute_dynamic() method")
            
            # Rename existing execute() to _execute_hardcoded() if needed
            if not has_execute_hardcoded and 'def execute(' in original_content:
                lines = self._wrap_execute_with_mode_switch(lines)
                print("  ✅ Added mode switching to execute() method")
            
            # Write updated content
            updated_content = '\n'.join(lines)
            orchestrator_file.write_text(updated_content)
            
            print(f"✅ Updated orchestrator with dual-mode support")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update orchestrator: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_mode_parameter(self, lines: List[str]) -> List[str]:
        """Add mode parameter to __init__ method."""
        new_lines = []
        in_init = False
        added = False
        
        for i, line in enumerate(lines):
            if 'def __init__' in line:
                in_init = True
            
            if in_init and not added and 'ui=' in line:
                # Add mode parameter after ui
                indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                new_lines.append(' ' * indent + 'mode: str = \'hardcoded\',')
                new_lines.append(' ' * indent + 'spec_file: Optional[Path] = None,')
                new_lines.append(' ' * indent + 'phase_spec: Optional[Dict[str, Any]] = None')
                added = True
                continue
            
            if in_init and added and 'self.ui = ui' in line:
                # Add mode instance variable
                indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                new_lines.append(' ' * indent + 'self.mode = mode')
                new_lines.append(' ' * indent + 'self.spec_file = spec_file or self.project_root / "design_specs/control_flows.yml"')
                new_lines.append(' ' * indent + 'self.phase_spec = phase_spec')
                continue
            
            new_lines.append(line)
        
        return new_lines
    
    def _generate_execute_dynamic_method(self, phase_data: Dict[str, Any]) -> str:
        """Generate _execute_dynamic method code."""
        return '''    def _execute_dynamic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute phase using YAML specification (dynamic mode).
        
        Reads steps from phase_spec['steps'] and executes them in sequence.
        """
        if not self.phase_spec:
            logger.warning("No phase spec available, falling back to hardcoded mode")
            return self._execute_hardcoded(context)
        
        logger.info("Using YAML-driven execution")
        result = {'artifacts': {}}
        
        for step_spec in self.phase_spec.get('steps', []):
            step_id = step_spec['step_id']
            step_status = step_spec.get('status', 'PLANNED')
            
            if step_status in ['PLANNED', 'SKIPPED']:
                logger.info(f"Skipping step {step_id} (status: {step_status})")
                continue
            
            logger.info(f"Executing step: {step_id}")
            
            if 'units' in step_spec and step_spec['units']:
                step_result = self._execute_step_with_units(step_spec, context)
            else:
                step_result = self._execute_step_traditional(step_spec, context)
            
            if step_result:
                context.update(step_result.get("artifacts", {}))
                result["artifacts"].update(step_result.get("artifacts", {}))
        
        return self._build_result(result, context)
'''
    
    def _insert_method_before_execute(
        self,
        lines: List[str],
        method_code: str,
        method_name: str
    ) -> List[str]:
        """Insert method code before the execute method."""
        new_lines = []
        inserted = False
        
        for i, line in enumerate(lines):
            if not inserted and 'def execute(' in line:
                # Insert new method before execute
                new_lines.extend(method_code.split('\n'))
                new_lines.append('')
                inserted = True
            
            new_lines.append(line)
        
        return new_lines
    
    def _wrap_execute_with_mode_switch(self, lines: List[str]) -> List[str]:
        """Wrap existing execute() with mode switching logic."""
        new_lines = []
        in_execute = False
        execute_indent = 0
        first_statement_found = False
        
        for i, line in enumerate(lines):
            if 'def execute(' in line:
                in_execute = True
                execute_indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                continue
            
            if in_execute and not first_statement_found:
                # Skip docstring and initial comments
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    new_lines.append(line)
                    continue
                if line.strip().startswith('#') or not line.strip():
                    new_lines.append(line)
                    continue
                
                # Found first real statement - add mode switch
                new_lines.append(' ' * (execute_indent + 4) + 'if self.mode == "dynamic":')
                new_lines.append(' ' * (execute_indent + 8) + 'return self._execute_dynamic(context)')
                new_lines.append(' ' * (execute_indent + 4) + 'else:')
                new_lines.append(' ' * (execute_indent + 8) + 'return self._execute_hardcoded(context)')
                new_lines.append('')
                new_lines.append(' ' * (execute_indent + 4) + 'def _execute_hardcoded(self, context: Dict[str, Any]) -> Dict[str, Any]:')
                new_lines.append(' ' * (execute_indent + 8) + '"""Hardcoded execution mode (original implementation)."""')
                
                first_statement_found = True
                in_execute = False
                
                # Indent the rest of the method body
                new_lines.append(' ' * (execute_indent + 8) + line.strip())
                continue
            
            new_lines.append(line)
        
        return new_lines


def main():
    """CLI for testing regenerator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Regenerate orchestrator from spec")
    parser.add_argument('--spec', type=Path, required=True, help='Path to control_flows.yml')
    parser.add_argument('--orchestrator', type=Path, help='Path to orchestrator file (not required for library type)')
    parser.add_argument('--type', choices=['global', 'phase', 'library'], required=True, help='Type to generate')
    parser.add_argument('--phase-id', help='Phase ID (required for phase type)')
    parser.add_argument('--flow', default='main_config_flow', help='Flow name')
    parser.add_argument('--library-name', help='Library name (required for library type)')
    parser.add_argument('--output-dir', type=Path, help='Output directory for library (default: phases/libraries/)')
    parser.add_argument('--dual-mode', action='store_true', help='Generate/update with dual-mode support (hardcoded + dynamic)')
    
    args = parser.parse_args()
    
    regenerator = OrchestratorRegenerator(args.spec)
    
    if args.type == 'library':
        if not args.library_name:
            print("❌ --library-name required for library type")
            return 1
        
        success = regenerator.generate_library(
            library_name=args.library_name,
            output_dir=args.output_dir,
            flow_name=args.flow
        )
    elif args.type == 'global':
        if not args.orchestrator:
            print("❌ --orchestrator required for global type")
            return 1
        
        success = regenerator.regenerate_global_orchestrator(
            orchestrator_file=args.orchestrator,
            flow_name=args.flow
        )
    else:  # phase
        if not args.orchestrator:
            print("❌ --orchestrator required for phase type")
            return 1
        if not args.phase_id:
            print("❌ --phase-id required for phase orchestrator")
            return 1
        
        if args.dual_mode:
            # Use dual-mode regeneration (adds dynamic support without clobbering)
            success = regenerator.regenerate_dual_mode_phase(
                orchestrator_file=args.orchestrator,
                phase_id=args.phase_id,
                flow_name=args.flow
            )
        else:
            # Use standard regeneration (only updates markers)
            success = regenerator.regenerate_phase_orchestrator(
                orchestrator_file=args.orchestrator,
                phase_id=args.phase_id,
                flow_name=args.flow
            )
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
