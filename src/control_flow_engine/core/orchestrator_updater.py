#!/usr/bin/env python3
"""
Orchestrator Updater

Updates phase orchestrator files to integrate new steps.
Uses AST parsing for reliability.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StepIntegration:
    """Information needed to integrate a step into orchestrator."""

    step_id: str
    step_sequence: int
    step_class_name: str
    step_module: str  # e.g., "step_01_load_config.step_load_config"
    description: str


class OrchestratorUpdater:
    """
    Updates phase orchestrator execute() methods to integrate new steps.

    Uses AST parsing for reliability when modifying Python files.
    """

    def __init__(self, orchestrator_path: Path):
        """
        Initialize updater for an orchestrator file.

        Args:
            orchestrator_path: Path to orchestrator_{phase_id}.py file
        """
        self.orchestrator_path = orchestrator_path
        self.content = orchestrator_path.read_text()
        self.lines = self.content.split("\n")

    def integrate_step(self, step: StepIntegration) -> bool:
        """
        Integrate a step into the orchestrator execute() method.

        Adds:
        1. Import statement at top
        2. Step execution in execute() method in sequence order

        Args:
            step: Step integration information

        Returns:
            True if successful, False otherwise
        """
        # Add import
        if not self._add_import(step):
            return False

        # Add step execution
        if not self._add_step_execution(step):
            return False

        # Write back
        self.orchestrator_path.write_text("\n".join(self.lines))
        return True

    def _add_import(self, step: StepIntegration) -> bool:
        """
        Add import statement for step.

        Adds after other imports, before class definition.
        Format: from .step_XX_name.step_name import StepClassName

        Args:
            step: Step integration information

        Returns:
            True if successful
        """
        # Check if already imported
        import_line = f"from .{step.step_module} import {step.step_class_name}"
        if import_line in self.content:
            print(f"Import already exists: {import_line}")
            return True

        # Find insertion point (after last import before class)
        last_import_idx = -1
        for i, line in enumerate(self.lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = i

        if last_import_idx == -1:
            # No imports found, add after docstring
            for i, line in enumerate(self.lines):
                if line.startswith('"""') or line.startswith("'''"):
                    if i > 0:  # Skip first docstring line
                        # Find end of docstring
                        quote = '"""' if line.startswith('"""') else "'''"
                        for j in range(i + 1, len(self.lines)):
                            if quote in self.lines[j]:
                                last_import_idx = j
                                break
                        break

        if last_import_idx == -1:
            print("❌ Could not find import insertion point")
            return False

        # Insert import
        self.lines.insert(last_import_idx + 1, import_line)
        print(f"✅ Added import: {import_line}")
        return True

    def _add_step_execution(self, step: StepIntegration) -> bool:
        """
        Add step execution to execute() method.

        Finds the execute() method and adds step execution in sequence order.

        Args:
            step: Step integration information

        Returns:
            True if successful
        """
        # Find execute() method
        execute_start = -1
        for i, line in enumerate(self.lines):
            if re.match(r"\s*def execute\(", line):
                execute_start = i
                break

        if execute_start == -1:
            print("❌ Could not find execute() method")
            return False

        # Find indentation level
        indent = self._get_method_indent(execute_start)

        # Find TODO marker or return statement
        insertion_point = -1
        for i in range(execute_start, len(self.lines)):
            line = self.lines[i]

            # Look for TODO marker
            if (
                "TODO: Implement phase logic" in line
                or "TODO: Add phase-specific results" in line
            ):
                insertion_point = i
                break

            # Look for return statement (fallback)
            if re.match(rf"\s{{4,}}return\s+", line):
                insertion_point = i - 1
                break

        if insertion_point == -1:
            print("❌ Could not find insertion point in execute() method")
            return False

        # Generate step execution code
        step_code = self._generate_step_execution(step, indent)

        # Check if step already integrated
        if step.step_class_name in "\n".join(
            self.lines[execute_start : insertion_point + 10]
        ):
            print(f"Step already integrated: {step.step_class_name}")
            return True

        # Insert step code
        for line in reversed(step_code):
            self.lines.insert(insertion_point, line)

        print(f"✅ Added step execution for: {step.step_class_name}")
        return True

    def _get_method_indent(self, method_line_idx: int) -> str:
        """Get the indentation used inside a method."""
        # Look for first indented line after method definition
        for i in range(method_line_idx + 1, len(self.lines)):
            line = self.lines[i]
            if (
                line.strip()
                and not line.strip().startswith('"""')
                and not line.strip().startswith("'''")
            ):
                match = re.match(r"^(\s+)", line)
                if match:
                    return match.group(1)
        return "        "  # Default 8 spaces

    def _generate_step_execution(
        self, step: StepIntegration, base_indent: str
    ) -> List[str]:
        """
        Generate step execution code block.

        Args:
            step: Step integration information
            base_indent: Base indentation for method body

        Returns:
            List of code lines to insert
        """
        # Display number is 1-indexed
        display_num = step.step_sequence + 1
        return [
            "",
            f"{base_indent}# Step {display_num}: {step.description}",
            f'{base_indent}logger.info("Step {display_num}: {step.description}")',
            f"{base_indent}step_{display_num} = {step.step_class_name}(self.project_root, self.ui)",
            f"{base_indent}step_result = step_{display_num}.execute(context)",
            f'{base_indent}context.update(step_result.get("artifacts", {{}}))',
            f'{base_indent}result["artifacts"].update(step_result.get("artifacts", {{}}))',
        ]


def update_orchestrator_with_step(
    orchestrator_path: Path,
    step_id: str,
    step_sequence: int,
    step_class_name: str,
    description: str,
) -> bool:
    """
    Convenience function to update orchestrator with a new step.

    Args:
        orchestrator_path: Path to orchestrator file
        step_id: Step identifier
        step_sequence: Step sequence number
        step_class_name: Step class name
        description: Step description

    Returns:
        True if successful

    Example:
        >>> update_orchestrator_with_step(
        ...     Path("phases/phase_01_init/orchestrator_init.py"),
        ...     "load_config",
        ...     1,
        ...     "LoadConfigStep",
        ...     "Load configuration"
        ... )
    """
    # Module path matches directory structure: step_{seq}_{id}/{id}.py
    # E.g., step_0_load_config/load_config.py → .step_0_load_config.load_config
    step_module = f"step_{step_sequence}_{step_id}.{step_id}"

    step_integration = StepIntegration(
        step_id=step_id,
        step_sequence=step_sequence,
        step_class_name=step_class_name,
        step_module=step_module,
        description=description,
    )

    updater = OrchestratorUpdater(orchestrator_path)
    return updater.integrate_step(step_integration)


if __name__ == "__main__":
    # Demo
    import tempfile

    # Create sample orchestrator
    sample_orchestrator = '''#!/usr/bin/env python3
"""
Sample Phase
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class SamplePhase:
    """Sample phase orchestrator."""
    
    def __init__(self, project_root: Path, ui=None):
        self.project_root = project_root
        self.ui = ui
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute phase."""
        logger.info("Executing Sample Phase")
        
        # TODO: Implement phase logic
        
        result = {
            'phase': 'sample',
            'status': 'completed',
            'artifacts': {}
        }
        
        return result
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(sample_orchestrator)
        temp_path = Path(f.name)

    try:
        print("Original orchestrator:")
        print(temp_path.read_text())
        print("\n" + "=" * 70 + "\n")

        # Update with step
        success = update_orchestrator_with_step(
            temp_path,
            step_id="load_config",
            step_sequence=1,
            step_class_name="LoadConfigStep",
            description="Load configuration",
        )

        print(f"\nUpdate successful: {success}\n")
        print("=" * 70 + "\n")
        print("Updated orchestrator:")
        print(temp_path.read_text())

    finally:
        temp_path.unlink()
