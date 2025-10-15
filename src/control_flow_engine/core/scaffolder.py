#!/usr/bin/env python3
"""
Control Flow Scaffolding System
Automatically creates directory structures and files when inserting phases/steps.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import logging

logger = logging.getLogger(__name__)


class ImplementationStatus(Enum):
    IMPLEMENTED = "IMPLEMENTED"
    IN_PROGRESS = "IN_PROGRESS"
    PLANNED = "PLANNED"
    TODO = "TODO"


@dataclass
class StepInsertion:
    """Definition for inserting a new step."""
    step_id: str
    name: str
    sequence: int
    description: str
    status: ImplementationStatus
    step_type: str  # 'interactive', 'processing', 'io', 'validation' - for documentation only
    
    # Parent phase info
    phase_id: str
    phase_sequence: int
    
    # Scaffolding options
    create_scaffolding: bool = True
    
    # Insert position
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


@dataclass
class PhaseInsertion:
    """Definition for inserting a new phase."""
    phase_id: str
    name: str
    sequence: int
    description: str
    status: ImplementationStatus
    
    # Scaffolding options
    create_scaffolding: bool = True
    orchestrator_class_name: Optional[str] = None
    base_path: Path = Path("phases")
    
    # Initial steps to create
    initial_steps: List[StepInsertion] = field(default_factory=list)


class ScaffoldGenerator:
    """Generates directory structures and files for phases and steps."""
    
    def __init__(self, project_root: Path):
        """
        Initialize scaffold generator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
    
    def _write_file_safe(self, path: Path, content: str, force: bool = False) -> bool:
        """
        Write file only if it doesn't exist or force=True.
        
        Args:
            path: Path to file
            content: File content
            force: If True, overwrite existing files
            
        Returns:
            True if file was written, False if skipped
        """
        if path.exists() and not force:
            logger.warning(f"⚠️  Skipping existing file: {path}")
            logger.info("    Use --force to overwrite existing files")
            return False
        
        path.write_text(content)
        logger.info(f"✅ Created: {path}")
        return True

    def create_phase_scaffolding(
        self,
        phase: PhaseInsertion,
        base_path: Path,
        force: bool = False
    ) -> Optional[Dict[str, Path]]:
        """
        Create directory structure and files for a new phase.
        
        Args:
            phase: Phase definition
            base_path: Base directory (e.g., phases/)
            force: If True, overwrite existing files/directories
            
        Returns:
            Dict mapping file types to created paths, or None if skipped
        """
        created_files = {}
        
        # Create phase directory
        phase_dir = base_path / f"phase_{phase.sequence}_{phase.phase_id}"
        
        # Check if phase directory already exists
        if phase_dir.exists() and not force:
            logger.error(f"❌ Phase directory already exists: {phase_dir}")
            logger.info("    Use --force to overwrite existing phase")
            return None
        
        phase_dir.mkdir(parents=True, exist_ok=True)
        created_files['directory'] = phase_dir
        
        # Create __init__.py
        init_file = phase_dir / "__init__.py"
        init_content = self._generate_phase_init(phase)
        if self._write_file_safe(init_file, init_content, force):
            created_files['init'] = init_file
        
        # Create orchestrator file
        orchestrator_name = f"orchestrator_{phase.phase_id}.py"
        orchestrator_file = phase_dir / orchestrator_name
        orchestrator_content = self._generate_phase_orchestrator(phase)
        if self._write_file_safe(orchestrator_file, orchestrator_content, force):
            created_files['orchestrator'] = orchestrator_file
        
        # Create outputs directory
        outputs_dir = phase_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        created_files['outputs_dir'] = outputs_dir
        
        # Create README
        readme_file = phase_dir / "README.md"
        readme_content = self._generate_phase_readme(phase)
        if self._write_file_safe(readme_file, readme_content, force):
            created_files['readme'] = readme_file
        
        logger.info(f"✅ Created phase scaffolding at {phase_dir}")
        
        # Create initial steps if specified
        if phase.initial_steps:
            for step in phase.initial_steps:
                step_files = self.create_step_scaffolding(step, phase_dir, force)
                if step_files:
                    created_files[f'step_{step.step_id}'] = step_files
        
        return created_files
        
    def create_step_scaffolding(
        self,
        step: StepInsertion,
        base_path: Path,
        force: bool = False
    ) -> Optional[Dict[str, Path]]:
        """
        Create directory structure and files for a new step.
        
        Args:
            step: Step definition
            base_path: Base directory (e.g., phases/phase_1_discovery/)
            force: If True, overwrite existing files/directories
            
        Returns:
            Dict mapping file types to created paths, or None if skipped
        """
        created_files = {}
        
        # Create step directory
        step_dir = base_path / f"step_{step.sequence}_{step.step_id}"
        
        # Check if step directory already exists
        if step_dir.exists() and not force:
            logger.error(f"❌ Step directory already exists: {step_dir}")
            logger.info("    Use --force to overwrite existing step")
            return None
        
        step_dir.mkdir(parents=True, exist_ok=True)
        created_files['directory'] = step_dir
        
        # Create __init__.py
        init_file = step_dir / "__init__.py"
        init_content = self._generate_step_init(step)
        if self._write_file_safe(init_file, init_content, force):
            created_files['init'] = init_file
        
        # Create implementation file (generic stub only)
        impl_file = step_dir / f"{step.step_id}.py"
        impl_content = self._generate_step_implementation(step)
        if self._write_file_safe(impl_file, impl_content, force):
            created_files['implementation'] = impl_file
        
        # Create README
        readme_file = step_dir / "README.md"
        readme_content = self._generate_step_readme(step)
        if self._write_file_safe(readme_file, readme_content, force):
            created_files['readme'] = readme_file
        
        logger.info(f"✅ Created step scaffolding at {step_dir}")
        
        return created_files
    
    def _generate_phase_init(self, phase: PhaseInsertion) -> str:
        """Generate __init__.py content for a phase."""
        class_name = phase.orchestrator_class_name or f'{phase.phase_id.title().replace("_", "")}Phase'
        
        return f'''"""
{phase.name}
{phase.description}
"""

from .orchestrator_{phase.phase_id} import {class_name}

__all__ = ['{class_name}']
'''
    
    def _generate_phase_orchestrator(self, phase: PhaseInsertion) -> str:
        """Generate orchestrator file for a phase."""
        class_name = phase.orchestrator_class_name or f'{phase.phase_id.title().replace("_", "")}Phase'
        
        return f'''#!/usr/bin/env python3
"""
{phase.name}
Status: {phase.status.value}

{phase.description}
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class {class_name}:
    """
    {phase.name}
    
    Status: {phase.status.value}
    Sequence: {phase.sequence}
    
    {phase.description}
    """
    
    PHASE_ID = "{phase.phase_id}"
    PHASE_SEQUENCE = {phase.sequence}
    PHASE_NAME = "{phase.name}"
    
    def __init__(self, project_root: Path, ui=None):
        """
        Initialize {phase.name}.
        
        Args:
            project_root: Root directory of the project
            ui: Optional UI interface for user interaction
        """
        self.project_root = project_root
        self.ui = ui
        self.phase_dir = project_root / "runtime" / f"phase_{phase.sequence}_{phase.phase_id}"
        self.outputs_dir = self.phase_dir / "outputs"
        
        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {phase.name}.
        
        Args:
            context: Execution context from previous phases
            
        Returns:
            Dict with phase results and artifacts
        """
        logger.info("=" * 70)
        logger.info(f"{{self.PHASE_NAME}}")
        logger.info("=" * 70)
        
        if self.ui:
            self.ui.show_phase_header(self.PHASE_NAME, "{phase.description}")
        
        # TODO: Implement phase logic
        # 
        # Example structure:
        # 1. Validate context has required artifacts
        # 2. Execute steps in sequence
        # 3. Collect results
        # 4. Save outputs to self.outputs_dir
        # 5. Return artifacts for next phase
        
        logger.info(f"Executing {{self.PHASE_NAME}}...")
        
        result = {{
            'phase': self.PHASE_ID,
            'status': 'completed',
            'artifacts': {{}}
            # TODO: Add phase-specific results
        }}
        
        logger.info(f"✅ {{self.PHASE_NAME}} completed")
        
        return result
    
    def _validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that context contains required artifacts.
        
        Args:
            context: Execution context
            
        Returns:
            True if valid, False otherwise
        """
        # TODO: Add validation logic
        required_keys = []  # List required context keys
        
        for key in required_keys:
            if key not in context:
                logger.error(f"❌ Required context key missing: {{key}}")
                return False
        
        return True


if __name__ == "__main__":
    # Test standalone
    import sys
    logging.basicConfig(level=logging.INFO)
    
    project_root = Path(__file__).parent.parent.parent
    phase = {class_name}(project_root)
    
    test_context = {{
        'test_mode': True
    }}
    
    result = phase.execute(test_context)
    print(f"\\nResult: {{result}}")
'''
    
    def _generate_phase_readme(self, phase: PhaseInsertion) -> str:
        """Generate README for a phase."""
        class_name = phase.orchestrator_class_name or f'{phase.phase_id.title().replace("_", "")}Phase'
        
        return f'''# {phase.name}

**Status**: {phase.status.value}  
**Sequence**: {phase.sequence}  
**Phase ID**: `{phase.phase_id}`

## Description

{phase.description}

## Structure

```
phase_{phase.sequence}_{phase.phase_id}/
├── __init__.py                     # Module initialization
├── orchestrator_{phase.phase_id}.py # Main orchestrator class
├── outputs/                        # Phase output artifacts
└── README.md                       # This file
```

## Orchestrator

- **File**: `orchestrator_{phase.phase_id}.py`
- **Class**: `{class_name}`
- **Method**: `execute(context) -> Dict[str, Any]`

## Usage

```python
from phases.phase_{phase.sequence}_{phase.phase_id} import {class_name}

phase = {class_name}(project_root)
result = phase.execute(context)
```

## Implementation Checklist

- [ ] Implement `execute()` method
- [ ] Add context validation
- [ ] Implement step execution
- [ ] Add error handling
- [ ] Add logging
- [ ] Save artifacts to `outputs/`
- [ ] Write unit tests
- [ ] Update this README

## Artifacts

### Consumed
- List artifacts this phase needs from previous phases

### Produced
- List artifacts this phase produces for later phases

## Testing

Run standalone:
```bash
cd phases/phase_{phase.sequence}_{phase.phase_id}
python orchestrator_{phase.phase_id}.py
```

Run with project:
```bash
python run_phases.py --start {phase.sequence} --end {phase.sequence}
```

## Notes

Add any phase-specific notes, gotchas, or implementation details here.
'''
    
    def _generate_step_init(self, step: StepInsertion) -> str:
        """Generate __init__.py content for a step."""
        return f'''"""
{step.name}
{step.description}
"""

from .{step.step_id} import execute_{step.step_id}

__all__ = ['execute_{step.step_id}']
'''
    
    def _generate_step_implementation(self, step: StepInsertion) -> str:
        """Generate implementation file for a regular step."""
        return f'''#!/usr/bin/env python3
"""
{step.name}
Status: {step.status.value}

{step.description}
"""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def execute_{step.step_id}(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    {step.name}
    
    Args:
        context: Execution context
        phase_dir: Phase directory path
        
    Returns:
        Dict with step results
    """
    logger.info("Executing: {step.name}")
    
    # TODO: Implement step logic
    
    return {{
        'step': '{step.step_id}',
        'status': 'completed',
        # TODO: Add step-specific results
    }}


if __name__ == "__main__":
    # Test standalone
    from pathlib import Path
    logging.basicConfig(level=logging.INFO)
    
    test_context = {{'test_mode': True}}
    test_phase_dir = Path(__file__).parent.parent
    
    result = execute_{step.step_id}(test_context, test_phase_dir)
    print(f"\\nResult: {{result}}")
'''
    
    def _generate_step_readme(self, step: StepInsertion) -> str:
        """Generate README for a step."""
        step_type_desc = {
            'interactive': 'This step interacts with the user to collect input.',
            'processing': 'This step processes data without user interaction.',
            'io': 'This step performs input/output operations.',
            'validation': 'This step validates data or configuration.'
        }.get(step.step_type, 'This step performs a specific operation.')
        return f'''# {step.name}

**Status**: {step.status.value}  
**Type**: {step.step_type}  
**Sequence**: {step.sequence}

## Description

{step.description}

{step_type_desc}

## Implementation

- **Main file**: `{step.step_id}.py`
- **Function**: `execute_{step.step_id}(context, phase_dir)`
## Testing

Run standalone:
```bash
python {step.step_id}.py
```

## TODO

- [ ] Implement core logic
- [ ] Add error handling
- [ ] Add logging
- [ ] Write unit tests
- [ ] Update documentation
'''
