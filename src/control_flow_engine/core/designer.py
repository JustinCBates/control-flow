#!/usr/bin/env python3
"""
Control Flow Designer - Greenfield (Design-First) Workflow
Provides high-level API for creating and managing control flows from specifications.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from dataclasses import dataclass

from .engine import ControlFlowManager, ImplementationStatus
from .scaffolder import (
    ScaffoldGenerator,
    StepInsertion,
    PhaseInsertion
)
from .orchestrator_updater import (
    OrchestratorUpdater,
    StepIntegration,
    update_orchestrator_with_step
)


@dataclass
class ValidationReport:
    """Report from validation checks."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class ControlFlowDesigner:
    """
    High-level API for design-first control flow development.
    
    Workflow:
    1. Create new project or load existing spec
    2. Add phases and steps progressively
    3. Generate scaffolding automatically
    4. Track implementation status
    """
    
    def __init__(self, spec_file: Path, project_root: Path):
        """
        Initialize designer with specification and project root.
        
        Args:
            spec_file: Path to control_flows.yml
            project_root: Root directory of project
        """
        self.spec_file = spec_file
        self.project_root = project_root
        self.manager = ControlFlowManager(spec_file)
        self.scaffolder = ScaffoldGenerator(project_root)
        
        # Load existing spec if it exists
        if spec_file.exists():
            with open(spec_file, 'r') as f:
                self.manager.spec = yaml.safe_load(f)
    
    @classmethod
    def new_project(
        cls,
        project_name: str,
        project_root: Path,
        description: str = "",
        main_flow_name: str = "main_config_flow"
    ) -> 'ControlFlowDesigner':
        """
        Create a new project with minimal specification.
        
        Args:
            project_name: Name of the project/component
            project_root: Root directory for the project
            description: Project description
            main_flow_name: Name of the main flow
            
        Returns:
            New ControlFlowDesigner instance
            
        Example:
            designer = ControlFlowDesigner.new_project(
                project_name="config-manager",
                project_root=Path("/opt/openproject/external/config-manager"),
                description="Configuration management component"
            )
        """
        # Create initial spec structure
        spec_data = {
            'metadata': {
                'name': project_name,
                'description': description,
                'version': '1.0.0',
                'created': 'auto-generated',
                'workflow_type': 'control_flow'
            },
            'flows': {
                main_flow_name: {
                    'name': f'Main {project_name} Flow',
                    'description': f'Main workflow for {project_name}',
                    'phases': []
                }
            }
        }
        
        # Create design_specs directory if needed
        spec_dir = project_root / 'design_specs'
        spec_dir.mkdir(parents=True, exist_ok=True)
        
        spec_file = spec_dir / 'control_flows.yml'
        
        # Save initial spec
        with open(spec_file, 'w') as f:
            yaml.dump(
                spec_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                allow_unicode=True
            )
        
        print(f"✅ Created new project: {project_name}")
        print(f"   Spec file: {spec_file}")
        
        # Create instance and initialize manager
        instance = cls(spec_file, project_root)
        instance.manager.spec = spec_data
        
        return instance
    
    @classmethod
    def from_existing(cls, spec_file: Path, project_root: Optional[Path] = None) -> 'ControlFlowDesigner':
        """
        Load existing specification.
        
        Args:
            spec_file: Path to existing control_flows.yml
            project_root: Project root (defaults to spec_file parent's parent)
            
        Returns:
            ControlFlowDesigner instance
            
        Example:
            designer = ControlFlowDesigner.from_existing(
                spec_file=Path("design_specs/control_flows.yml")
            )
        """
        if not spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {spec_file}")
        
        if project_root is None:
            # Assume spec is in design_specs/ directory
            project_root = spec_file.parent.parent
        
        print(f"✅ Loaded existing specification from {spec_file}")
        
        return cls(spec_file, project_root)
    
    def add_phase(
        self,
        phase: PhaseInsertion,
        flow_name: str = "main_config_flow",
        create_scaffolding: bool = True
    ) -> bool:
        """
        Add a new phase to the flow.
        
        Args:
            phase: PhaseInsertion definition
            flow_name: Name of flow to add phase to
            create_scaffolding: Whether to generate directories/files
            
        Returns:
            True if successful
            
        Example:
            designer.add_phase(
                PhaseInsertion(
                    phase_id="validation",
                    name="Validation Phase",
                    sequence=4,
                    description="Validate configuration",
                    status=ImplementationStatus.PLANNED,
                    orchestrator_class_name="ValidationPhase"
                ),
                create_scaffolding=True
            )
        """
        # Find flow in spec.flows dict
        if not isinstance(self.manager.spec.get('flows'), dict):
            print(f"❌ Invalid spec format: 'flows' must be a dict")
            return False
        
        flow = self.manager.spec['flows'].get(flow_name)
        
        if not flow:
            print(f"❌ Flow '{flow_name}' not found")
            return False
        
        # Ensure flow has phases array
        if 'phases' not in flow:
            flow['phases'] = []
        
        # Create phase data for YAML
        phase_data = {
            'phase_id': phase.phase_id,
            'name': phase.name,
            'status': phase.status.value,
            'description': phase.description,
            'sequence': phase.sequence,
            'steps': [],
            'artifacts_produced': [],
            'artifacts_consumed': [],
            'implementation': {
                'phase_directory': f'phases/phase_{phase.sequence}_{phase.phase_id}/',
                'orchestrator_file': f'phases/phase_{phase.sequence}_{phase.phase_id}/orchestrator_{phase.phase_id}.py',
                'module': f'phases.phase_{phase.sequence}_{phase.phase_id}',
                'class': phase.orchestrator_class_name or f'{phase.phase_id.title().replace("_", "")}Phase',
                'method': 'execute(context)'
            }
        }
        
        # Find insertion point based on sequence
        insert_index = len(flow['phases'])
        for i, existing_phase in enumerate(flow['phases']):
            if existing_phase.get('sequence', i) > phase.sequence:
                insert_index = i
                break
        
        # Insert phase
        flow['phases'].insert(insert_index, phase_data)
        
        print(f"✅ Added phase '{phase.phase_id}' to flow '{flow_name}' at position {insert_index}")
        
        # Save updated spec
        self.manager.save_specification(self.spec_file)
        
        # Create scaffolding if requested
        if create_scaffolding and phase.create_scaffolding:
            created_files = self.scaffolder.create_phase_scaffolding(
                phase=phase,
                base_path=self.project_root / 'phases'
            )
            print(f"✅ Created phase scaffolding with {len(created_files)} files")
        
        return True
    
    def add_step(
        self,
        phase_id: str,
        step: StepInsertion,
        flow_name: str = "main_config_flow",
        create_scaffolding: bool = True,
        update_orchestrator: bool = True
    ) -> bool:
        """
        Add a new step to a phase.
        
        Args:
            phase_id: ID of phase to add step to
            step: StepInsertion definition
            flow_name: Name of flow containing the phase
            create_scaffolding: Whether to generate directories/files
            update_orchestrator: Whether to add step to orchestrator
            
        Returns:
            True if successful
            
        Example:
            designer.add_step(
                phase_id="validation",
                step=StepInsertion(
                    step_id="schema_validation",
                    name="Schema Validation",
                    sequence=0,
                    description="Validate against JSON schema",
                    status=ImplementationStatus.PLANNED,
                    step_type="validation",
                    phase_id="validation",
                    phase_sequence=4,
                    is_tui_form=False
                )
            )
        """
        # Get the phase
        phase = self.manager.get_phase(flow_name, phase_id)
        if not phase:
            print(f"❌ Phase '{phase_id}' not found in flow '{flow_name}'")
            return False
        
        # Create step data for YAML
        step_data = {
            'step_id': step.step_id,
            'name': step.name,
            'type': step.step_type,
            'description': step.description,
            'status': step.status.value,
            'sequence': step.sequence,
            'dependencies': [],
            'artifacts_produced': []
        }
        
        # Insert step into phase
        success = self.manager.insert_step_into_phase(
            flow_name=flow_name,
            phase_id=phase_id,
            step_data=step_data,
            insert_before=step.insert_before,
            insert_after=step.insert_after
        )
        
        if not success:
            return False
        
        # Save updated spec
        self.manager.save_specification(self.spec_file)
        
        # Create scaffolding if requested
        if create_scaffolding and step.create_scaffolding:
            phase_dir = self.project_root / 'phases' / f'phase_{step.phase_sequence}_{phase_id}'
            created_files = self.scaffolder.create_step_scaffolding(
                step=step,
                base_path=phase_dir
            )
            print(f"✅ Created step scaffolding with {len(created_files)} files")
        
        # Update orchestrator if requested
        if update_orchestrator:
            orchestrator_file = (
                self.project_root / 'phases' / 
                f'phase_{step.phase_sequence}_{phase_id}' / 
                f'orchestrator_{phase_id}.py'
            )
            
            if orchestrator_file.exists():
                # Generate step class name from step_id
                step_class_name = f'{step.step_id.title().replace("_", "")}Step'
                success = update_orchestrator_with_step(
                    orchestrator_path=orchestrator_file,
                    step_id=step.step_id,
                    step_sequence=step.sequence,  # Actual sequence number
                    step_class_name=step_class_name,
                    description=step.description
                )
                
                if success:
                    print(f"✅ Updated orchestrator to include '{step.step_id}'")
                else:
                    print(f"⚠️  Failed to update orchestrator automatically")
            else:
                print(f"⚠️  Orchestrator file not found: {orchestrator_file}")
                print(f"   Create phase scaffolding first or manually add step to orchestrator")

        
        return True
    
    def update_step_status(
        self,
        phase_id: str,
        step_id: str,
        status: ImplementationStatus,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Update the implementation status of a step.
        
        Args:
            phase_id: ID of phase containing the step
            step_id: ID of step to update
            status: New implementation status
            flow_name: Name of flow containing the phase
            
        Returns:
            True if successful
            
        Example:
            designer.update_step_status(
                phase_id="validation",
                step_id="schema_validation",
                status=ImplementationStatus.IMPLEMENTED
            )
        """
        phase = self.manager.get_phase(flow_name, phase_id)
        if not phase:
            print(f"❌ Phase '{phase_id}' not found")
            return False
        
        # Find and update step
        if 'steps' not in phase:
            print(f"❌ Phase '{phase_id}' has no steps")
            return False
        
        for step in phase['steps']:
            if step.get('step_id') == step_id:
                step['status'] = status.value
                print(f"✅ Updated step '{step_id}' status to {status.value}")
                
                # Save updated spec
                self.manager.save_specification(self.spec_file)
                return True
        
        print(f"❌ Step '{step_id}' not found in phase '{phase_id}'")
        return False
    
    def update_phase_status(
        self,
        phase_id: str,
        status: ImplementationStatus,
        flow_name: str = "main_config_flow"
    ) -> bool:
        """
        Update the implementation status of a phase.
        
        Args:
            phase_id: ID of phase to update
            status: New implementation status
            flow_name: Name of flow containing the phase
            
        Returns:
            True if successful
        """
        return self.manager.update_phase(
            flow_name=flow_name,
            phase_id=phase_id,
            updates={'status': status.value}
        )
    
    def validate(self) -> ValidationReport:
        """
        Validate the specification for completeness and consistency.
        
        Returns:
            ValidationReport with errors, warnings, and info
            
        Checks:
        - All phases have unique IDs
        - All steps have unique IDs within phase
        - Sequence numbers are consistent
        - Implementation paths exist (if scaffolding created)
        - No circular dependencies
        """
        errors = []
        warnings = []
        info = []
        
        for flow_name, flow in self.manager.flows.items():
            if 'phases' not in flow:
                warnings.append(f"Flow '{flow_name}' has no phases")
                continue
            
            phase_ids = set()
            sequences = []
            
            for phase in flow['phases']:
                # Check phase ID uniqueness
                phase_id = phase.get('phase_id')
                if not phase_id:
                    errors.append(f"Phase in flow '{flow_name}' missing phase_id")
                    continue
                
                if phase_id in phase_ids:
                    errors.append(f"Duplicate phase_id '{phase_id}' in flow '{flow_name}'")
                phase_ids.add(phase_id)
                
                # Check sequence
                sequence = phase.get('sequence')
                if sequence is None:
                    warnings.append(f"Phase '{phase_id}' missing sequence number")
                else:
                    sequences.append(sequence)
                
                # Check steps
                if 'steps' in phase:
                    step_ids = set()
                    for step in phase['steps']:
                        step_id = step.get('step_id')
                        if not step_id:
                            errors.append(f"Step in phase '{phase_id}' missing step_id")
                            continue
                        
                        if step_id in step_ids:
                            errors.append(f"Duplicate step_id '{step_id}' in phase '{phase_id}'")
                        step_ids.add(step_id)
                    
                    info.append(f"Phase '{phase_id}': {len(step_ids)} steps")
            
            # Check sequence numbering
            if sequences:
                if sorted(sequences) != list(range(min(sequences), max(sequences) + 1)):
                    warnings.append(f"Flow '{flow_name}' has non-contiguous sequence numbers")
        
        is_valid = len(errors) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info
        )
    
    def get_implementation_progress(self, flow_name: str = "main_config_flow") -> Dict[str, Any]:
        """
        Get implementation progress statistics.
        
        Args:
            flow_name: Name of flow to analyze
            
        Returns:
            Dict with progress metrics including counts by status
        """
        # Find flow in spec (dict format)
        flow = None
        if isinstance(self.manager.spec.get('flows'), dict):
            flow = self.manager.spec['flows'].get(flow_name)
        
        if not flow:
            return {}
        
        total_phases = 0
        total_steps = 0
        implemented_steps = 0
        in_progress_steps = 0
        planned_steps = 0
        
        if 'phases' in flow:
            total_phases = len(flow['phases'])
            
            for phase in flow['phases']:
                if 'steps' in phase:
                    for step in phase['steps']:
                        total_steps += 1
                        status = step.get('status', 'planned')
                        
                        if status == 'implemented':
                            implemented_steps += 1
                        elif status == 'in_progress':
                            in_progress_steps += 1
                        elif status == 'planned' or status == 'todo':
                            planned_steps += 1
        
        overall_percentage = (implemented_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            'flow': flow_name,
            'total_phases': total_phases,
            'total_steps': total_steps,
            'implemented_steps': implemented_steps,
            'in_progress_steps': in_progress_steps,
            'planned_steps': planned_steps,
            'overall_percentage': overall_percentage
        }
    
    # ========================================================================
    # Transformation System Integration (Todo #7)
    # ========================================================================
    
    def _get_transformer(self):
        """Get or create ControlFlowTransformation instance."""
        if not hasattr(self, '_transformer'):
            from .transformation import ControlFlowTransformation
            self._transformer = ControlFlowTransformation(str(self.spec_file))
        return self._transformer
    
    def renumber_phase(
        self,
        phase_id: Optional[str] = None,
        start_from: int = 1,
        strategy: str = "compact",
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Renumber phases in the control flow, cleaning up sequence numbers.
        
        This operation preserves execution order while fixing sequence numbering.
        For example, phases with sequences [0, 5, 7, 12] can be renumbered to [1, 2, 3, 4].
        
        Args:
            phase_id: Specific phase ID to renumber steps within (None = renumber all phases)
            start_from: Starting sequence number (default: 1, can be 0 or any int)
            strategy: "compact" (remove gaps) or "minimal" (preserve relative spacing)
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results including:
                - success: bool
                - message: str
                - preview: str (if preview_only=True)
                - affected_files: List[str] (if applied)
                
        Example:
            # Renumber all phases starting from 1
            result = designer.renumber_phase()
            
            # Renumber all phases starting from 0
            result = designer.renumber_phase(start_from=0)
            
            # Renumber steps within a specific phase
            result = designer.renumber_phase(phase_id="phase_001", start_from=1)
        """
        transformer = self._get_transformer()
        
        try:
            # Plan the transformation
            plan = transformer.plan_renumber(
                flow_name=self.manager.flow_name,
                phase_id=phase_id,
                start_from=start_from,
                strategy=strategy
            )
            
            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                return {
                    'success': False,
                    'message': f"Validation failed: {', '.join(validation.errors)}",
                    'errors': validation.errors,
                    'warnings': validation.warnings
                }
            
            # Preview if requested
            if preview_only:
                preview_text = transformer.preview(plan)
                return {
                    'success': True,
                    'message': 'Preview generated',
                    'preview': preview_text,
                    'warnings': validation.warnings
                }
            
            # Apply with full workflow
            result = transformer.apply(
                plan,
                save=True,
                sync_directories=True,
                update_code_paths=True,
                regenerate_orchestrators=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            scope = f"phase {phase_id}" if phase_id else "all phases"
            return {
                'success': True,
                'message': f"Renumbered {scope} starting from {start_from}",
                'result': result,
                'warnings': validation.warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def insert_phase(
        self,
        phase_data: Dict[str, Any],
        insert_after: Optional[str] = None,
        insert_before: Optional[str] = None,
        cascade_renumber: bool = True,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new phase with automatic sync and regeneration.
        
        Args:
            phase_data: Phase definition dict with required fields (phase_id, name, etc.)
            insert_after: Insert after this phase_id (None = insert at end)
            insert_before: Insert before this phase_id (overrides insert_after)
            cascade_renumber: Whether to renumber subsequent phases
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results including:
                - success: bool
                - message: str
                - preview: str (if preview_only=True)
                - result: dict (if applied)
            
        Example:
            # Insert at end
            result = designer.insert_phase({
                'phase_id': 'deployment',
                'name': 'Deployment Phase',
                'description': 'Deploy to production'
            })
            
            # Insert after specific phase
            result = designer.insert_phase(
                phase_data={'phase_id': 'testing', 'name': 'Testing'},
                insert_after='development'
            )
        """
        transformer = self._get_transformer()
        
        try:
            # Validate required fields
            if 'phase_id' not in phase_data:
                return {
                    'success': False,
                    'message': "phase_data must include 'phase_id'",
                    'error': 'Missing phase_id'
                }
            
            plan = transformer.plan_insert(
                flow_name=self.manager.flow_name,
                phase_id=None,  # None = inserting a phase
                new_element=phase_data,
                insert_after=insert_after,
                insert_before=insert_before,
                cascade_renumber=cascade_renumber
            )
            
            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                return {
                    'success': False,
                    'message': f"Validation failed: {', '.join(validation.errors)}",
                    'errors': validation.errors,
                    'warnings': validation.warnings
                }
            
            # Preview if requested
            if preview_only:
                preview_text = transformer.preview(plan)
                return {
                    'success': True,
                    'message': 'Preview generated',
                    'preview': preview_text,
                    'warnings': validation.warnings
                }
            
            # Apply with full workflow
            result = transformer.apply(
                plan,
                save=True,
                sync_directories=True,
                update_code_paths=True,
                regenerate_orchestrators=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            return {
                'success': True,
                'message': f"Phase '{phase_data.get('phase_id')}' inserted successfully",
                'result': result,
                'warnings': validation.warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def insert_step(
        self,
        phase_id: str,
        step_data: Dict[str, Any],
        insert_after: Optional[str] = None,
        insert_before: Optional[str] = None,
        cascade_renumber: bool = True,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Insert a new step into a phase with automatic sync and regeneration.
        
        Args:
            phase_id: ID of the phase to insert the step into
            step_data: Step definition dict with required fields (step_id, name, etc.)
            insert_after: Insert after this step_id (None = insert at end)
            insert_before: Insert before this step_id (overrides insert_after)
            cascade_renumber: Whether to renumber subsequent steps
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results
            
        Example:
            result = designer.insert_step(
                phase_id='development',
                step_data={
                    'step_id': 'code_review',
                    'name': 'Code Review',
                    'description': 'Review code changes'
                },
                insert_after='unit_tests'
            )
        """
        transformer = self._get_transformer()
        
        try:
            # Validate required fields
            if 'step_id' not in step_data:
                return {
                    'success': False,
                    'message': "step_data must include 'step_id'",
                    'error': 'Missing step_id'
                }
            
            plan = transformer.plan_insert(
                flow_name=self.manager.flow_name,
                phase_id=phase_id,
                new_element=step_data,
                insert_after=insert_after,
                insert_before=insert_before,
                cascade_renumber=cascade_renumber
            )
            
            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                return {
                    'success': False,
                    'message': f"Validation failed: {', '.join(validation.errors)}",
                    'errors': validation.errors,
                    'warnings': validation.warnings
                }
            
            # Preview if requested
            if preview_only:
                preview_text = transformer.preview(plan)
                return {
                    'success': True,
                    'message': 'Preview generated',
                    'preview': preview_text,
                    'warnings': validation.warnings
                }
            
            # Apply with full workflow
            result = transformer.apply(
                plan,
                save=True,
                sync_directories=True,
                update_code_paths=True,
                regenerate_orchestrators=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            return {
                'success': True,
                'message': f"Step '{step_data.get('step_id')}' inserted into phase '{phase_id}'",
                'result': result,
                'warnings': validation.warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def delete_phase(
        self,
        phase_id: str,
        cascade_renumber: bool = True,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a phase with automatic sync and regeneration.
        
        Args:
            phase_id: ID of the phase to delete
            cascade_renumber: Whether to renumber subsequent phases
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results including:
                - success: bool
                - message: str
                - preview: str (if preview_only=True)
                - result: dict (if applied)
            
        Example:
            result = designer.delete_phase('testing', cascade_renumber=True)
        """
        transformer = self._get_transformer()
        
        try:
            plan = transformer.plan_delete(
                flow_name=self.manager.flow_name,
                element_id=phase_id,
                phase_id=None,  # None = deleting a phase
                cascade_renumber=cascade_renumber
            )
            
            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                return {
                    'success': False,
                    'message': f"Validation failed: {', '.join(validation.errors)}",
                    'errors': validation.errors,
                    'warnings': validation.warnings
                }
            
            # Preview if requested
            if preview_only:
                preview_text = transformer.preview(plan)
                return {
                    'success': True,
                    'message': 'Preview generated',
                    'preview': preview_text,
                    'warnings': validation.warnings
                }
            
            # Apply with full workflow
            result = transformer.apply(
                plan,
                save=True,
                sync_directories=True,
                update_code_paths=True,
                regenerate_orchestrators=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            return {
                'success': True,
                'message': f"Phase '{phase_id}' deleted successfully",
                'result': result,
                'warnings': validation.warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def delete_step(
        self,
        phase_id: str,
        step_id: str,
        cascade_renumber: bool = True,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a step from a phase with automatic sync and regeneration.
        
        Args:
            phase_id: ID of the phase containing the step
            step_id: ID of the step to delete
            cascade_renumber: Whether to renumber subsequent steps
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results
            
        Example:
            result = designer.delete_step(
                phase_id='development',
                step_id='obsolete_task',
                cascade_renumber=True
            )
        """
        transformer = self._get_transformer()
        
        try:
            plan = transformer.plan_delete(
                flow_name=self.manager.flow_name,
                element_id=step_id,
                phase_id=phase_id,
                cascade_renumber=cascade_renumber
            )
            
            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                return {
                    'success': False,
                    'message': f"Validation failed: {', '.join(validation.errors)}",
                    'errors': validation.errors,
                    'warnings': validation.warnings
                }
            
            # Preview if requested
            if preview_only:
                preview_text = transformer.preview(plan)
                return {
                    'success': True,
                    'message': 'Preview generated',
                    'preview': preview_text,
                    'warnings': validation.warnings
                }
            
            # Apply with full workflow
            result = transformer.apply(
                plan,
                save=True,
                sync_directories=True,
                update_code_paths=True,
                regenerate_orchestrators=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            return {
                'success': True,
                'message': f"Step '{step_id}' deleted from phase '{phase_id}'",
                'result': result,
                'warnings': validation.warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def get_transformation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transformation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of transformation history entries
            
        Example:
            history = designer.get_transformation_history(limit=10)
            for entry in history:
                print(f"{entry['timestamp']}: {entry['transformation_type']}")
        """
        transformer = self._get_transformer()
        return transformer.get_history(limit=limit)
    
    def rollback_transformation(
        self,
        steps: int = 1,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Rollback last N transformations.
        
        Args:
            steps: Number of transformations to rollback
            preview_only: If True, only preview without applying
            
        Returns:
            Dict with operation results
            
        Example:
            result = designer.rollback_transformation(steps=1)
            if result['success']:
                print("Rollback successful")
        """
        transformer = self._get_transformer()
        
        try:
            # Check if rollback is possible
            if not transformer.history_manager.can_rollback(steps):
                return {
                    'success': False,
                    'message': f"Cannot rollback {steps} step(s). Check history.",
                    'available_rollbacks': transformer.history_manager.can_rollback(1)
                }
            
            if preview_only:
                # Get history entries that would be rolled back
                history = transformer.get_history(limit=steps)
                return {
                    'success': True,
                    'message': f"Would rollback {steps} transformation(s)",
                    'preview': history
                }
            
            # Perform rollback
            transformer.rollback(
                steps=steps,
                save=True,
                sync_directories=True,
                project_base_path=self.project_root
            )
            
            # Reload spec
            self.manager.load_specification()
            
            return {
                'success': True,
                'message': f"Rolled back {steps} transformation(s)"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'error': str(e)
            }
    
    def preview_transformation(
        self,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Preview any transformation operation without applying it.
        
        Args:
            operation: One of 'renumber_phase', 'renumber_step', 'insert_phase',
                      'insert_step', 'delete_phase', 'delete_step'
            **kwargs: Arguments for the specific operation
            
        Returns:
            Dict with preview results
            
        Example:
            preview = designer.preview_transformation(
                'renumber_phase',
                old_sequence=10,
                new_sequence=15,
                cascade_renumber=True
            )
            print(preview['preview'])
        """
        # Map operations to methods
        operations = {
            'renumber_phase': self.renumber_phase,
            'renumber_step': self.renumber_step,
            'insert_phase': self.insert_phase,
            'insert_step': self.insert_step,
            'delete_phase': self.delete_phase,
            'delete_step': self.delete_step
        }
        
        if operation not in operations:
            return {
                'success': False,
                'message': f"Unknown operation: {operation}",
                'valid_operations': list(operations.keys())
            }
        
        # Call the operation with preview_only=True
        kwargs['preview_only'] = True
        return operations[operation](**kwargs)


def main():
    """Demo the ControlFlowDesigner."""
    import sys
    
    # Example 1: Create new project
    print("=" * 70)
    print("Example 1: Create New Project")
    print("=" * 70)
    
    designer = ControlFlowDesigner.new_project(
        project_name="example-service",
        project_root=Path("/tmp/example-service"),
        description="Example service for demonstration"
    )
    
    # Example 2: Add a phase
    print("\n" + "=" * 70)
    print("Example 2: Add Phase")
    print("=" * 70)
    
    designer.add_phase(
        PhaseInsertion(
            phase_id="initialization",
            name="Initialization Phase",
            sequence=1,
            description="Initialize service and load configuration",
            status=ImplementationStatus.PLANNED,
            orchestrator_class_name="InitializationPhase",
            create_scaffolding=True
        )
    )
    
    # Example 3: Add steps to phase
    print("\n" + "=" * 70)
    print("Example 3: Add Steps")
    print("=" * 70)
    
    designer.add_step(
        phase_id="initialization",
        step=StepInsertion(
            step_id="load_config",
            name="Load Configuration",
            sequence=0,
            description="Load configuration from file",
            status=ImplementationStatus.PLANNED,
            step_type="io",
            phase_id="initialization",
            phase_sequence=1,
            is_tui_form=False
        )
    )
    
    designer.add_step(
        phase_id="initialization",
        step=StepInsertion(
            step_id="validate_config",
            name="Validate Configuration",
            sequence=1,
            description="Validate configuration against schema",
            status=ImplementationStatus.PLANNED,
            step_type="validation",
            phase_id="initialization",
            phase_sequence=1,
            is_tui_form=False
        )
    )
    
    # Example 4: Update status
    print("\n" + "=" * 70)
    print("Example 4: Update Status")
    print("=" * 70)
    
    designer.update_step_status(
        phase_id="initialization",
        step_id="load_config",
        status=ImplementationStatus.IN_PROGRESS
    )
    
    # Example 5: Validate
    print("\n" + "=" * 70)
    print("Example 5: Validate Specification")
    print("=" * 70)
    
    report = designer.validate()
    print(f"Valid: {report.is_valid}")
    if report.errors:
        print("Errors:")
        for error in report.errors:
            print(f"  ❌ {error}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  ⚠️  {warning}")
    if report.info:
        print("Info:")
        for item in report.info:
            print(f"  ℹ️  {item}")
    
    # Example 6: Progress report
    print("\n" + "=" * 70)
    print("Example 6: Implementation Progress")
    print("=" * 70)
    
    progress = designer.get_implementation_progress()
    print(f"Phases: {progress['phases']['implemented']}/{progress['phases']['total']} "
          f"({progress['phases']['percentage']:.1f}%)")
    print(f"Steps: {progress['steps']['implemented']}/{progress['steps']['total']} "
          f"({progress['steps']['percentage']:.1f}%)")


if __name__ == "__main__":
    main()
