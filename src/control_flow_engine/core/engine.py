#!/usr/bin/env python3
"""
Design-First Control Flow Manager
Supports iterative development with flow specifications that can be modified before implementation.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .transformation import (
    ControlFlowTransformation,
    TransformationPlan,
    ValidationResult,
    TransformationType,
)


class ImplementationStatus(Enum):
    """Status values for control flow elements (lowercase for YAML)."""

    IMPLEMENTED = "implemented"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    TODO = "todo"


@dataclass
class FlowStep:
    step_id: str
    name: str
    status: ImplementationStatus
    description: str
    sub_flows: List[str] = None
    decision_point: Optional[str] = None

    def __post_init__(self):
        if self.sub_flows is None:
            self.sub_flows = []


@dataclass
class FlowInsertion:
    step_id: str
    name: str
    status: ImplementationStatus
    description: str
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class ControlFlowManager:
    """Manages design-first control flow specifications."""

    def __init__(self, spec_file: Path):
        self.spec_file = spec_file
        self.spec = {}  # Holds the complete spec structure
        self.flows = {}
        self.entry_points = {}
        self.decision_points = {}
        self.external_interfaces = {}
        self.transformer: Optional[ControlFlowTransformation] = None

    def load_specification(self):
        """Load the YAML-based flow specification."""
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {self.spec_file}")

        with open(self.spec_file, "r") as f:
            content = f.read()

        # Check if this is a pure YAML file or markdown with YAML blocks
        if self.spec_file.suffix in [".yml", ".yaml"]:
            # Pure YAML file - load directly
            self.spec = yaml.safe_load(content)
            self.entry_points = self.spec.get("entry_points", {})
            self.flows = self.spec.get("flows", {})
            self.decision_points = self.spec.get("decision_points", {})
            self.external_interfaces = self.spec.get("external_interfaces", {})
        else:
            # Markdown file with YAML blocks
            sections = self._parse_yaml_sections(content)

            if "Entry Points" in sections:
                self.entry_points = sections["Entry Points"]
            if "Flow Implementations" in sections:
                self.flows = sections["Flow Implementations"]
            if "Decision Points" in sections:
                self.decision_points = sections["Decision Points"]
            if "External Interfaces" in sections:
                self.external_interfaces = sections["External Interfaces"]

            # Build complete spec structure
            self.spec = {
                "entry_points": self.entry_points,
                "flows": self.flows,
                "decision_points": self.decision_points,
                "external_interfaces": self.external_interfaces,
            }

        # Initialize transformer with loaded spec
        self.transformer = ControlFlowTransformation(self.spec, self.spec_file)

    def get_specification(self) -> Dict[str, Any]:
        """
        Get the loaded specification.

        Returns:
            The complete specification dictionary
        """
        if not self.spec:
            self.load_specification()
        return self.spec

    def _parse_yaml_sections(self, content: str) -> Dict[str, Any]:
        """Parse YAML sections from markdown content."""
        sections = {}

        # Extract YAML blocks
        yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)

        for block in yaml_blocks:
            try:
                data = yaml.safe_load(block)
                if data:
                    # Determine section based on content structure
                    if any(key in data for key in ["cli", "configure", "update"]):
                        sections["Entry Points"] = data
                    elif any(
                        "flow_steps" in str(v)
                        for v in data.values()
                        if isinstance(v, dict)
                    ):
                        sections["Flow Implementations"] = data
                    elif any(
                        "type" in str(v) for v in data.values() if isinstance(v, dict)
                    ):
                        sections["Decision Points"] = data
                    elif "outbound_calls" in data or "inbound_calls" in data:
                        sections["External Interfaces"] = data
            except yaml.YAMLError:
                continue

        return sections

    def insert_flow_step(self, flow_name: str, insertion: FlowInsertion) -> bool:
        """Insert a new step into an existing flow."""
        if flow_name not in self.flows:
            print(f"❌ Flow '{flow_name}' not found")
            return False

        flow = self.flows[flow_name]
        if "flow_steps" not in flow:
            print(f"❌ Flow '{flow_name}' has no flow_steps")
            return False

        steps = flow["flow_steps"]

        # Find insertion point
        insert_index = None

        if insertion.insert_after:
            for i, step in enumerate(steps):
                if step.get("step_id") == insertion.insert_after:
                    insert_index = i + 1
                    break

        elif insertion.insert_before:
            for i, step in enumerate(steps):
                if step.get("step_id") == insertion.insert_before:
                    insert_index = i
                    break

        if insert_index is None:
            print(
                f"❌ Insertion point not found for {insertion.insert_before or insertion.insert_after}"
            )
            return False

        # Create new step
        new_step = {
            "step_id": insertion.step_id,
            "name": insertion.name,
            "status": insertion.status.value,
            "description": insertion.description,
        }

        # Insert step
        steps.insert(insert_index, new_step)

        print(
            f"✅ Inserted step '{insertion.step_id}' in flow '{flow_name}' at position {insert_index}"
        )
        return True

    def apply_planned_insertions(self, flow_name: str) -> int:
        """Apply all planned insertions for a flow."""
        if flow_name not in self.flows:
            return 0

        flow = self.flows[flow_name]
        if "planned_insertions" not in flow:
            return 0

        insertions = flow["planned_insertions"]
        applied = 0

        for insertion_data in insertions:
            insertion = FlowInsertion(
                step_id=insertion_data["step_id"],
                name=insertion_data["name"],
                status=ImplementationStatus(insertion_data["status"]),
                description=insertion_data["description"],
                insert_before=insertion_data.get("insert_before"),
                insert_after=insertion_data.get("insert_after"),
            )

            if self.insert_flow_step(flow_name, insertion):
                applied += 1

        # Remove applied insertions
        if applied > 0:
            flow["planned_insertions"] = []

        return applied

    def insert_step_into_phase(
        self,
        flow_name: str,
        phase_id: str,
        step_data: Dict[str, Any],
        insert_before: Optional[str] = None,
        insert_after: Optional[str] = None,
    ) -> bool:
        """
        Insert a new step into a specific phase's steps array.

        Args:
            flow_name: Name of the flow containing the phase
            phase_id: ID of the phase to insert step into
            step_data: Complete step definition dict
            insert_before: Step ID to insert before
            insert_after: Step ID to insert after

        Returns:
            True if insertion succeeded, False otherwise
        """
        # Support dict-based flows (standard format)
        flow = None
        if isinstance(self.spec.get("flows"), dict):
            flow = self.spec["flows"].get(flow_name)

        if not flow:
            print(f"❌ Flow '{flow_name}' not found")
            return False

        # Support both flow_steps and phases structure
        if "phases" in flow:
            # Find the target phase
            target_phase = None
            for phase in flow["phases"]:
                if phase.get("phase_id") == phase_id:
                    target_phase = phase
                    break

            if not target_phase:
                print(f"❌ Phase '{phase_id}' not found in flow '{flow_name}'")
                return False

            # Ensure phase has steps array
            if "steps" not in target_phase:
                target_phase["steps"] = []

            steps = target_phase["steps"]

        elif "flow_steps" in flow:
            # Legacy structure - treat as single phase
            steps = flow["flow_steps"]
        else:
            print(f"❌ Flow '{flow_name}' has neither 'phases' nor 'flow_steps'")
            return False

        # Find insertion point
        insert_index = None

        if insert_after:
            for i, step in enumerate(steps):
                if step.get("step_id") == insert_after:
                    insert_index = i + 1
                    break
        elif insert_before:
            for i, step in enumerate(steps):
                if step.get("step_id") == insert_before:
                    insert_index = i
                    break
        else:
            # If no position specified, append to end
            insert_index = len(steps)

        if insert_index is None:
            print(f"❌ Insertion point not found for {insert_before or insert_after}")
            return False

        # Insert step
        steps.insert(insert_index, step_data)

        print(
            f"✅ Inserted step '{step_data.get('step_id')}' into phase '{phase_id}' at position {insert_index}"
        )
        return True

    def get_phase(self, flow_name: str, phase_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a phase from a flow.

        Args:
            flow_name: Name of the flow (key in spec.flows dict)
            phase_id: ID of the phase

        Returns:
            Phase dictionary or None if not found
        """
        # Support dict-based flows (standard format)
        if isinstance(self.spec.get("flows"), dict):
            flow = self.spec["flows"].get(flow_name)
            if flow:
                for phase in flow.get("phases", []):
                    if phase.get("phase_id") == phase_id:
                        return phase

        return None

    def update_phase(
        self, flow_name: str, phase_id: str, updates: Dict[str, Any]
    ) -> bool:
        """
        Update a phase's properties.

        Args:
            flow_name: Name of the flow
            phase_id: ID of the phase to update
            updates: Dictionary of properties to update

        Returns:
            True if update succeeded, False otherwise
        """
        phase = self.get_phase(flow_name, phase_id)

        if not phase:
            print(f"❌ Phase '{phase_id}' not found in flow '{flow_name}'")
            return False

        # Update phase properties
        phase.update(updates)

        print(f"✅ Updated phase '{phase_id}' in flow '{flow_name}'")
        return True

        return applied

    def generate_implementation_tasks(self) -> List[Dict[str, str]]:
        """Generate list of implementation tasks from the specification."""
        tasks = []

        for flow_name, flow_data in self.flows.items():
            if "flow_steps" not in flow_data:
                continue

            for step in flow_data["flow_steps"]:
                status = step.get("status", "TODO")
                if status in ["PLANNED", "TODO"]:
                    tasks.append(
                        {
                            "flow": flow_name,
                            "step_id": step["step_id"],
                            "name": step["name"],
                            "description": step["description"],
                            "status": status,
                            "type": "implementation",
                        }
                    )

        # Add decision points
        for decision_name, decision_data in self.decision_points.items():
            if not decision_data.get("implemented", False):
                tasks.append(
                    {
                        "flow": "decision_points",
                        "step_id": decision_name,
                        "name": decision_name,
                        "description": decision_data.get(
                            "prompt", "Decision point implementation"
                        ),
                        "status": "TODO",
                        "type": "decision_point",
                    }
                )

        return tasks

    def generate_mock_code(self, flow_name: str, step_id: str) -> str:
        """Generate mock code for a planned step."""
        if flow_name not in self.flows:
            return f"# Flow '{flow_name}' not found"

        flow = self.flows[flow_name]
        if "flow_steps" not in flow:
            return f"# Flow '{flow_name}' has no steps"

        step_data = None
        for step in flow["flow_steps"]:
            if step.get("step_id") == step_id:
                step_data = step
                break

        if not step_data:
            return f"# Step '{step_id}' not found in flow '{flow_name}'"

        # Generate mock implementation
        step_name = step_data["name"]
        description = step_data["description"]

        mock_code = f'''def {step_id}(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    {step_name}
    
    {description}
    
    Args:
        context: Current execution context
        
    Returns:
        Updated context with step results
    """
    # TODO: Implement {step_name.lower()}
    self.ui.show_step("{step_name}")
    
    # Mock implementation
    result = {{
        "step_id": "{step_id}",
        "status": "completed",
        "data": {{}},
        "messages": []
    }}
    
    context.update(result)
    return context
'''

        return mock_code

    def generate_unit_test(self, flow_name: str, step_id: str) -> str:
        """Generate unit test for a planned step."""
        if flow_name not in self.flows:
            return f"# Flow '{flow_name}' not found"

        flow = self.flows[flow_name]
        if "flow_steps" not in flow:
            return f"# Flow '{flow_name}' has no steps"

        step_data = None
        for step in flow["flow_steps"]:
            if step.get("step_id") == step_id:
                step_data = step
                break

        if not step_data:
            return f"# Step '{step_id}' not found in flow '{flow_name}'"

        step_name = step_data["name"]
        description = step_data["description"]

        test_code = f'''def test_{step_id}(self):
    """Test {step_name}."""
    # Arrange
    manager = ConfigurationManager()
    context = {{
        "test_mode": True,
        "flow": "{flow_name}",
        "previous_steps": []
    }}
    
    # Act
    result = manager.{step_id}(context)
    
    # Assert
    assert result is not None
    assert result.get("step_id") == "{step_id}"
    assert result.get("status") == "completed"
    
    # Verify specific behavior for {description.lower()}
    # TODO: Add specific assertions based on step requirements
    
def test_{step_id}_error_handling(self):
    """Test {step_name} error handling."""
    # Arrange
    manager = ConfigurationManager()
    invalid_context = {{}}  # Invalid context to trigger error
    
    # Act & Assert
    with pytest.raises(ValueError):
        manager.{step_id}(invalid_context)
'''

        return test_code

    def save_specification(self, output_path: Optional[Path] = None):
        """
        Save the current specification to YAML file.

        Args:
            output_path: Path to save YAML file. If None, uses spec_file with .yml extension
        """
        if output_path is None:
            # Convert .md to .yml if needed
            if self.spec_file.suffix == ".md":
                output_path = self.spec_file.with_suffix(".yml")
            else:
                output_path = self.spec_file

        # Use self.spec if available (new format), otherwise build from old format
        if self.spec:
            spec_data = self.spec
        else:
            # Build from old format
            spec_data = {}
            if self.entry_points:
                spec_data["entry_points"] = self.entry_points
            if self.flows:
                spec_data["flows"] = self.flows
            if self.decision_points:
                spec_data["decision_points"] = self.decision_points
            if self.external_interfaces:
                spec_data["external_interfaces"] = self.external_interfaces

        # Write YAML with proper formatting
        with open(output_path, "w") as f:
            yaml.dump(
                spec_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                allow_unicode=True,
            )

        print(f"✅ Saved specification to {output_path}")

    def get_development_prompt_suggestions(self) -> List[str]:
        """Get suggestions for development prompts."""
        suggestions = []

        tasks = self.generate_implementation_tasks()

        for task in tasks[:5]:  # Top 5 tasks
            if task["type"] == "implementation":
                suggestions.append(
                    f"Implement {task['name']} step in {task['flow']} flow: {task['description']}"
                )
            elif task["type"] == "decision_point":
                suggestions.append(
                    f"Add decision point '{task['name']}' with user confirmation"
                )

        return suggestions

    # ========================================================================
    # TRANSFORMATION API - Safe, Validated Flow Modifications
    # ========================================================================

    def create_transformation(
        self, transformation_type: str, flow_name: str, **kwargs
    ) -> TransformationPlan:
        """
        Create a transformation plan for modifying the control flow.

        This is the primary API for all flow modifications. It creates a plan
        that can be validated and previewed before applying.

        Args:
            transformation_type: "renumber", "insert", "delete", "move", "update", "mock"
            flow_name: Name of the flow to modify
            **kwargs: Type-specific parameters

        Returns:
            TransformationPlan ready for validation

        Example:
            # Renumber sequences
            plan = manager.create_transformation(
                "renumber",
                flow_name="main_config_flow",
                phase_id="discovery",
                start_from=1
            )

            # Insert a new step
            plan = manager.create_transformation(
                "insert",
                flow_name="main_config_flow",
                phase_id="discovery",
                new_element={...},
                insert_after="env_discovery"
            )
        """
        if not self.transformer:
            raise RuntimeError(
                "Transformer not initialized. Call load_specification() first."
            )

        ttype = transformation_type.lower()

        if ttype == "renumber":
            return self.transformer.plan_renumber(
                flow_name=flow_name,
                phase_id=kwargs.get("phase_id"),
                start_from=kwargs.get("start_from", 1),
                strategy=kwargs.get("strategy", "compact"),
            )

        elif ttype == "insert":
            return self.transformer.plan_insert(
                flow_name=flow_name,
                phase_id=kwargs.get("phase_id"),
                new_element=kwargs["new_element"],
                insert_after=kwargs.get("insert_after"),
                insert_before=kwargs.get("insert_before"),
                cascade_renumber=kwargs.get("cascade_renumber", True),
            )

        elif ttype == "delete":
            return self.transformer.plan_delete(
                flow_name=flow_name,
                element_id=kwargs["element_id"],
                phase_id=kwargs.get("phase_id"),
                cascade_renumber=kwargs.get("cascade_renumber", True),
            )

        else:
            raise ValueError(
                f"Unknown transformation type: {transformation_type}. "
                f"Valid types: renumber, insert, delete, move, update, mock"
            )

    def validate_transformation(self, plan: TransformationPlan) -> ValidationResult:
        """
        Validate a transformation plan.

        Args:
            plan: The transformation plan to validate

        Returns:
            ValidationResult with status and any errors/warnings
        """
        if not self.transformer:
            raise RuntimeError(
                "Transformer not initialized. Call load_specification() first."
            )

        return self.transformer.validate(plan)

    def preview_transformation(self, plan: TransformationPlan) -> str:
        """
        Generate a preview of what the transformation will do.

        Args:
            plan: The transformation plan

        Returns:
            Human-readable preview text
        """
        if not self.transformer:
            raise RuntimeError(
                "Transformer not initialized. Call load_specification() first."
            )

        return self.transformer.preview(plan)

    def apply_transformation(
        self,
        plan: TransformationPlan,
        auto_validate: bool = True,
        save: bool = True,
        sync_directories: bool = False,
        project_base_path: Optional[Path] = None,
        dry_run_sync: bool = False,
        update_code_paths: bool = False,
    ) -> Dict[str, Any]:
        """
        Apply a validated transformation plan.

        Args:
            plan: The transformation plan to apply
            auto_validate: Automatically validate if not already done
            save: Whether to save the new spec to file
            sync_directories: Whether to synchronize directory structure
            project_base_path: Base path for directory sync (auto-detected if None)
            dry_run_sync: If True, preview directory ops without executing
            update_code_paths: If True, update Python imports and config paths after directory sync

        Returns:
            The new specification with transformations applied

        Raises:
            ValueError: If plan is invalid
        """
        if not self.transformer:
            raise RuntimeError(
                "Transformer not initialized. Call load_specification() first."
            )

        # Auto-validate if needed
        if auto_validate and plan.validation_result is None:
            validation = self.transformer.validate(plan)
            if not validation.valid:
                raise ValueError(
                    f"Transformation plan is invalid. Errors: {validation.errors}"
                )

        # Apply transformation with directory sync and code path updates
        new_spec = self.transformer.apply(
            plan,
            save=save,
            sync_directories=sync_directories,
            project_base_path=project_base_path,
            dry_run_sync=dry_run_sync,
            update_code_paths=update_code_paths,
        )

        # Update manager state
        self.spec = new_spec
        self.flows = new_spec.get("flows", {})
        self.entry_points = new_spec.get("entry_points", {})
        self.decision_points = new_spec.get("decision_points", {})
        self.external_interfaces = new_spec.get("external_interfaces", {})

        return new_spec

    def transform_and_apply(
        self,
        transformation_type: str,
        flow_name: str,
        dry_run: bool = False,
        sync_directories: bool = False,
        project_base_path: Optional[Path] = None,
        update_code_paths: bool = False,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience method: create, validate, and apply transformation in one call.

        Args:
            transformation_type: Type of transformation
            flow_name: Flow to modify
            dry_run: If True, only show preview without applying
            sync_directories: Whether to synchronize directory structure
            project_base_path: Base path for directory sync
            update_code_paths: If True, update Python imports and config paths after directory sync
            **kwargs: Transformation-specific parameters

        Returns:
            New specification if applied, None if dry_run
        """
        # Create plan
        plan = self.create_transformation(transformation_type, flow_name, **kwargs)

        # Validate
        validation = self.validate_transformation(plan)

        # Show preview
        print(self.preview_transformation(plan))

        if not validation.valid:
            print("\n❌ Cannot apply transformation due to validation errors")
            return None

        if dry_run:
            print("\n🔍 DRY RUN - No changes applied")
            return None

        # Apply with directory sync and code path updates
        return self.apply_transformation(
            plan,
            auto_validate=False,
            sync_directories=sync_directories,
            project_base_path=project_base_path,
            update_code_paths=update_code_paths,
        )

    # ========================================================================
    # LEGACY DIRECT MODIFICATION METHODS (DEPRECATED)
    # ========================================================================
    # The methods below directly modify the spec without validation.
    # Prefer using the transformation API above for safer modifications.
    # ========================================================================

    def renumber_sequences(
        self,
        flow_name: Optional[str] = None,
        start_from: int = 1,
        strategy: str = "compact",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Renumber phase and step sequences in the control flow specification.

        This method fixes sequence numbering issues like:
        - Steps numbered 0,1,2,3 → 1,2,3,4
        - Phase gaps 1,2,3,5 → 1,2,3,4

        Args:
            flow_name: Specific flow to renumber (None = all flows)
            start_from: Starting sequence number (default: 1)
            strategy: "compact" (remove all gaps) or "minimal" (preserve existing gaps)
            dry_run: If True, show changes without applying them

        Returns:
            Dict with renumbering report:
            {
                'flows_affected': int,
                'phases_renumbered': int,
                'steps_renumbered': int,
                'changes': [{'flow': str, 'old': int, 'new': int, 'type': str}]
            }
        """
        report = {
            "flows_affected": 0,
            "phases_renumbered": 0,
            "steps_renumbered": 0,
            "changes": [],
        }

        # Determine which flows to process
        flows_to_process = {}
        if flow_name:
            if flow_name not in self.flows:
                raise ValueError(f"Flow '{flow_name}' not found")
            flows_to_process[flow_name] = self.flows[flow_name]
        else:
            flows_to_process = self.flows

        # Process each flow
        for fname, flow_data in flows_to_process.items():
            flow_changed = False

            # Renumber phases if they exist
            if "phases" in flow_data:
                phases = flow_data["phases"]
                old_sequences = [p.get("sequence", 0) for p in phases]

                # Sort by current sequence
                sorted_phases = sorted(phases, key=lambda p: p.get("sequence", 0))

                # Apply renumbering
                for idx, phase in enumerate(sorted_phases):
                    old_seq = phase.get("sequence", 0)

                    if strategy == "compact":
                        new_seq = start_from + idx
                    else:  # minimal - only fix gaps
                        new_seq = old_seq if old_seq >= start_from else start_from + idx

                    if old_seq != new_seq:
                        change = {
                            "flow": fname,
                            "type": "phase",
                            "phase_id": phase.get("phase_id", "unknown"),
                            "old_sequence": old_seq,
                            "new_sequence": new_seq,
                        }
                        report["changes"].append(change)

                        if not dry_run:
                            phase["sequence"] = new_seq

                        flow_changed = True
                        report["phases_renumbered"] += 1

                    # Renumber steps within this phase
                    if "steps" in phase:
                        steps = phase["steps"]
                        sorted_steps = sorted(steps, key=lambda s: s.get("sequence", 0))

                        for step_idx, step in enumerate(sorted_steps):
                            old_step_seq = step.get("sequence", 0)

                            if strategy == "compact":
                                new_step_seq = start_from + step_idx
                            else:
                                new_step_seq = (
                                    old_step_seq
                                    if old_step_seq >= start_from
                                    else start_from + step_idx
                                )

                            if old_step_seq != new_step_seq:
                                change = {
                                    "flow": fname,
                                    "type": "step",
                                    "phase_id": phase.get("phase_id", "unknown"),
                                    "step_id": step.get("step_id", "unknown"),
                                    "old_sequence": old_step_seq,
                                    "new_sequence": new_step_seq,
                                }
                                report["changes"].append(change)

                                if not dry_run:
                                    step["sequence"] = new_step_seq

                                flow_changed = True
                                report["steps_renumbered"] += 1

            # Handle flows with direct steps (no phases)
            elif "flow_steps" in flow_data:
                steps = flow_data["flow_steps"]
                sorted_steps = sorted(steps, key=lambda s: s.get("sequence", 0))

                for step_idx, step in enumerate(sorted_steps):
                    old_step_seq = step.get("sequence", 0)

                    if strategy == "compact":
                        new_step_seq = start_from + step_idx
                    else:
                        new_step_seq = (
                            old_step_seq
                            if old_step_seq >= start_from
                            else start_from + step_idx
                        )

                    if old_step_seq != new_step_seq:
                        change = {
                            "flow": fname,
                            "type": "flow_step",
                            "step_id": step.get("step_id", "unknown"),
                            "old_sequence": old_step_seq,
                            "new_sequence": new_step_seq,
                        }
                        report["changes"].append(change)

                        if not dry_run:
                            step["sequence"] = new_step_seq

                        flow_changed = True
                        report["steps_renumbered"] += 1

            if flow_changed:
                report["flows_affected"] += 1

        # Print report
        if dry_run:
            print("🔍 DRY RUN - No changes applied")
        else:
            print("✅ Renumbering complete")

        print(f"\n📊 Renumbering Report:")
        print(f"  Flows affected: {report['flows_affected']}")
        print(f"  Phases renumbered: {report['phases_renumbered']}")
        print(f"  Steps renumbered: {report['steps_renumbered']}")

        if report["changes"]:
            print(f"\n📝 Changes ({len(report['changes'])}):")
            for change in report["changes"][:10]:  # Show first 10
                if change["type"] == "phase":
                    print(
                        f"  Phase '{change['phase_id']}': seq {change['old_sequence']} → {change['new_sequence']}"
                    )
                elif change["type"] == "step":
                    print(
                        f"  Step '{change['step_id']}' in phase '{change['phase_id']}': seq {change['old_sequence']} → {change['new_sequence']}"
                    )
                else:
                    print(
                        f"  Flow step '{change['step_id']}': seq {change['old_sequence']} → {change['new_sequence']}"
                    )

            if len(report["changes"]) > 10:
                print(f"  ... and {len(report['changes']) - 10} more")

        return report


def main():
    """Demo the design-first control flow manager."""
    print("🎯 Design-First Control Flow Manager")
    print("=" * 40)

    spec_file = Path(
        "/opt/openproject/external/config-manager/control_flows/CONTROL_FLOWS_SPEC.md"
    )
    manager = ControlFlowManager(spec_file)

    try:
        manager.load_specification()
        print("✅ Loaded flow specification")

        # Show current flows
        print(f"\\n📊 Found {len(manager.flows)} flows:")
        for flow_name in manager.flows.keys():
            print(f"  - {flow_name}")

        # Apply planned insertions
        print("\\n🔄 Applying planned insertions...")
        for flow_name in manager.flows.keys():
            applied = manager.apply_planned_insertions(flow_name)
            if applied > 0:
                print(f"  ✅ Applied {applied} insertions to {flow_name}")

        # Show implementation tasks
        tasks = manager.generate_implementation_tasks()
        if tasks:
            print(f"\\n📋 Implementation Tasks ({len(tasks)}):")
            for task in tasks[:3]:  # Show first 3
                print(f"  - {task['name']} ({task['status']})")

        # Show development suggestions
        suggestions = manager.get_development_prompt_suggestions()
        if suggestions:
            print("\\n💡 Development Prompt Suggestions:")
            for suggestion in suggestions[:2]:  # Show first 2
                print(f"  • {suggestion}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
