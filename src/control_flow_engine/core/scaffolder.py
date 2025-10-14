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
    step_type: str  # 'interactive', 'processing', 'io', 'validation'
    
    # Parent phase info
    phase_id: str
    phase_sequence: int
    
    # Scaffolding options
    create_scaffolding: bool = True
    
    # TUI-specific
    is_tui_form: bool = False
    layout_file_name: Optional[str] = None
    use_defaults_file: bool = False
    defaults_file_name: Optional[str] = None
    
    # Mock responses
    generate_mock_responses: bool = True
    mock_responses: Optional[Dict[str, Any]] = None
    
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
        
    def create_step_scaffolding(
        self,
        step: StepInsertion,
        base_path: Path
    ) -> Dict[str, Path]:
        """
        Create directory structure and files for a new step.
        
        Args:
            step: Step definition
            base_path: Base directory (e.g., phases/phase_1_discovery/)
            
        Returns:
            Dict mapping file types to created paths
        """
        created_files = {}
        
        # Create step directory
        step_dir = base_path / f"step_{step.sequence}_{step.step_id}"
        step_dir.mkdir(parents=True, exist_ok=True)
        created_files['directory'] = step_dir
        
        # Create __init__.py
        init_file = step_dir / "__init__.py"
        init_content = self._generate_step_init(step)
        init_file.write_text(init_content)
        created_files['init'] = init_file
        
        # Create implementation file
        impl_file = step_dir / f"{step.step_id}.py"
        if step.is_tui_form:
            impl_content = self._generate_tui_step_implementation(step)
        else:
            impl_content = self._generate_step_implementation(step)
        impl_file.write_text(impl_content)
        created_files['implementation'] = impl_file
        
        # Create TUI layout if needed
        if step.is_tui_form:
            layout_name = step.layout_file_name or f"{step.step_id}.layout.yml"
            layout_file = step_dir / layout_name
            layout_content = self._generate_tui_layout(step)
            layout_file.write_text(layout_content)
            created_files['layout'] = layout_file
            
            # Create defaults file if requested
            if step.use_defaults_file:
                defaults_name = step.defaults_file_name or f"{step.step_id}.defaults.yml"
                defaults_file = step_dir / defaults_name
                defaults_content = self._generate_tui_defaults(step)
                defaults_file.write_text(defaults_content)
                created_files['defaults'] = defaults_file
        
        # Create mock responses if requested
        if step.generate_mock_responses:
            mock_file = step_dir / "mock_responses.json"
            mock_content = self._generate_mock_responses(step)
            mock_file.write_text(mock_content)
            created_files['mock_responses'] = mock_file
        
        # Create README
        readme_file = step_dir / "README.md"
        readme_content = self._generate_step_readme(step)
        readme_file.write_text(readme_content)
        created_files['readme'] = readme_file
        
        print(f"✅ Created step scaffolding at {step_dir}")
        
        return created_files
    
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
    
    def _generate_tui_step_implementation(self, step: StepInsertion) -> str:
        """Generate implementation file for a TUI form step."""
        layout_name = step.layout_file_name or f"{step.step_id}.layout.yml"
        
        return f'''#!/usr/bin/env python3
"""
{step.name}
Status: {step.status.value}

{step.description}

This step uses TUI Form Engine for interactive user input.
"""

from pathlib import Path
from typing import Dict, Any
import logging
import sys

# Import TUI Form Engine
tui_path = Path(__file__).parent.parent.parent.parent.parent / 'tui-form-designer' / 'src'
sys.path.insert(0, str(tui_path))
from tui_form_engine.renderer import FormRenderer

logger = logging.getLogger(__name__)


def execute_{step.step_id}(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    {step.name}
    
    This step uses TUI Form Engine for interactive user input.
    
    Args:
        context: Execution context (may contain mock_responses)
        phase_dir: Phase directory path
        
    Returns:
        Dict containing:
        - User responses from the form
        - Any derived configuration
    """
    logger.info("=" * 70)
    logger.info("{step.name}")
    logger.info("=" * 70)
    
    # Path to TUI form layout
    layout_path = phase_dir / "step_{step.sequence}_{step.step_id}" / "{layout_name}"
    
    if not layout_path.exists():
        logger.error(f"❌ Layout file not found: {{layout_path}}")
        return _get_default_config()
    
    # Create TUI renderer
    renderer = FormRenderer()
    
    # Check for mock mode
    mock_responses = None
    if 'mock_responses' in context and '{step.step_id}' in context['mock_responses']:
        mock_responses = context['mock_responses']['{step.step_id}']
        logger.info("🤖 Running in MOCK mode")
    
    # Render the form
    try:
        response = renderer.render_flow(
            flow_path=str(layout_path),
            mock_responses=mock_responses,
            quiet=context.get('quiet', False)
        )
        
        responses = response.get('responses', {{}})
        
        logger.info(f"✅ Collected {{len(responses)}} responses")
        
        return {{
            'step': '{step.step_id}',
            'responses': responses,
            'status': 'completed'
        }}
        
    except KeyboardInterrupt:
        logger.warning("⚠️  User cancelled")
        raise
    except Exception as e:
        logger.error(f"❌ Error: {{e}}")
        return _get_default_config()


def _get_default_config() -> Dict[str, Any]:
    """Fallback configuration when form cannot be rendered."""
    return {{
        'step': '{step.step_id}',
        'status': 'fallback',
        'responses': {{}}
    }}


if __name__ == "__main__":
    # Test standalone
    import json
    logging.basicConfig(level=logging.INFO)
    
    # Load mock responses
    mock_file = Path(__file__).parent / "mock_responses.json"
    mock_data = {{}}
    if mock_file.exists():
        with open(mock_file) as f:
            mock_data = json.load(f)
    
    test_context = {{
        'test_mode': True,
        'mock_responses': {{'{step.step_id}': mock_data}}
    }}
    test_phase_dir = Path(__file__).parent.parent
    
    result = execute_{step.step_id}(test_context, test_phase_dir)
    print(f"\\nResult: {{json.dumps(result, indent=2)}}")
'''
    
    def _generate_tui_layout(self, step: StepInsertion) -> str:
        """Generate TUI layout YAML template."""
        return f'''flow_id: {step.step_id}
title: "{step.name}"
icon: "🔧"
description: "{step.description}"

metadata:
  id: {step.step_id}
  version: "1.0.0"
  estimated_time: "30 seconds"

# TODO: Add defaults_file if needed
# defaults_file: {step.step_id}.defaults.yml

steps:
  # TODO: Define form steps
  - id: example_input
    type: text
    message: "Enter a value:"
    instruction: "Provide configuration input"
    default: ""
'''
    
    def _generate_tui_defaults(self, step: StepInsertion) -> str:
        """Generate TUI defaults YAML template."""
        return f'''# Default values for {step.name}
# TODO: Add default values for form fields

example_input: ""
'''
    
    def _generate_mock_responses(self, step: StepInsertion) -> str:
        """Generate mock responses JSON."""
        if step.mock_responses:
            return json.dumps(step.mock_responses, indent=2)
        
        return json.dumps({
            "example_input": "test value"
        }, indent=2)
    
    def _generate_step_readme(self, step: StepInsertion) -> str:
        """Generate README for a step."""
        step_type_desc = {
            'interactive': 'This step interacts with the user to collect input.',
            'processing': 'This step processes data without user interaction.',
            'io': 'This step performs input/output operations.',
            'validation': 'This step validates data or configuration.'
        }.get(step.step_type, 'This step performs a specific operation.')
        
        # Build TUI section if applicable
        tui_section = ""
        if step.is_tui_form:
            layout_name = step.layout_file_name or f"{step.step_id}.layout.yml"
            tui_section = f'''
### TUI Form

This step uses the TUI Form Engine for interactive input.

- **Layout file**: `{layout_name}`
- **Mock responses**: `mock_responses.json` (for testing)
'''
        
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
{tui_section}

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
