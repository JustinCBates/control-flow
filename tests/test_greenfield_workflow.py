#!/usr/bin/env python3
"""
End-to-End Test for Greenfield (Design-First) Workflow

Tests the complete workflow:
1. Create new project spec
2. Add phases with scaffolding
3. Add steps with orchestrator integration
4. Verify YAML structure
5. Verify file structure
6. Verify orchestrator updates
"""

import tempfile
import shutil
from pathlib import Path

from control_flow_engine.core.designer import ControlFlowDesigner
from control_flow_engine.core.scaffolder import StepInsertion, PhaseInsertion
from control_flow_engine.core.engine import ImplementationStatus

# Only import pytest if available (for IDE/pytest compatibility)
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock fixture decorator for standalone execution
    class MockPytest:
        @staticmethod
        def fixture(func):
            return func
    pytest = MockPytest()


class TestGreenfieldWorkflow:
    """Test complete greenfield workflow."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_complete_greenfield_workflow(self, temp_project):
        """
        Test complete workflow from scratch to implemented phases.
        
        Steps:
        1. Create new project
        2. Add phase with scaffolding
        3. Add steps with orchestrator integration
        4. Verify all files created correctly
        5. Verify YAML structure
        6. Verify orchestrator updated
        """
        # Step 1: Create new project
        designer = ControlFlowDesigner.new_project(
            project_name="Test Greenfield Project",
            project_root=temp_project,
            description="End-to-end test of greenfield workflow"
        )
        
        spec_file = temp_project / "design_specs" / "control_flows.yml"
        
        assert spec_file.exists(), "Spec file should be created"
        
        # Verify initial structure
        spec_content = designer.manager.spec
        assert 'metadata' in spec_content
        assert spec_content['metadata']['name'] == "Test Greenfield Project"
        assert isinstance(spec_content['flows'], dict), "Flows should be a dict"
        assert len(spec_content['flows']) == 1
        assert 'main_config_flow' in spec_content['flows']
        assert len(spec_content['flows']['main_config_flow']['phases']) == 0
        
        print("✅ Step 1: New project created")
        
        # Step 2: Add phase with scaffolding
        phase = PhaseInsertion(
            phase_id="initialization",
            name="Initialization Phase",
            sequence=1,
            description="Initialize project and load configuration",
            status=ImplementationStatus.PLANNED,
            orchestrator_class_name="InitializationPhase",
            create_scaffolding=True
        )
        
        success = designer.add_phase(phase, create_scaffolding=True)
        assert success, "Phase should be added successfully"
        
        # Verify phase in YAML
        spec_content = designer.manager.spec
        main_flow = spec_content['flows']['main_config_flow']
        assert len(main_flow['phases']) == 1
        phase_data = main_flow['phases'][0]
        assert phase_data['phase_id'] == 'initialization'
        assert phase_data['name'] == 'Initialization Phase'
        assert phase_data['sequence'] == 1
        
        # Verify phase directory structure
        phase_dir = temp_project / 'phases' / 'phase_1_initialization'
        assert phase_dir.exists(), "Phase directory should exist"
        assert (phase_dir / '__init__.py').exists(), "Phase __init__.py should exist"
        assert (phase_dir / 'orchestrator_initialization.py').exists(), "Orchestrator should exist"
        assert (phase_dir / 'outputs').exists(), "Outputs directory should exist"
        assert (phase_dir / 'README.md').exists(), "README should exist"
        
        # Verify orchestrator content
        orchestrator_content = (phase_dir / 'orchestrator_initialization.py').read_text()
        assert 'class InitializationPhase' in orchestrator_content
        assert 'def execute(self, context: Dict[str, Any])' in orchestrator_content
        assert 'TODO: Implement phase logic' in orchestrator_content
        
        print("✅ Step 2: Phase added with complete scaffolding")
        
        # Step 3: Add first step
        step1 = StepInsertion(
            step_id="load_config",
            name="Load Configuration",
            sequence=0,
            description="Load configuration from file",
            status=ImplementationStatus.PLANNED,
            step_type="config",
            phase_id="initialization",
            phase_sequence=1,
            is_tui_form=False,
            create_scaffolding=True
        )
        
        success = designer.add_step(
            phase_id="initialization",
            step=step1,
            create_scaffolding=True,
            update_orchestrator=True
        )
        assert success, "Step should be added successfully"
        
        # Verify step in YAML
        spec_content = designer.manager.spec
        main_flow = spec_content['flows']['main_config_flow']
        phase_data = main_flow['phases'][0]
        assert len(phase_data['steps']) == 1
        step_data = phase_data['steps'][0]
        assert step_data['step_id'] == 'load_config'
        assert step_data['name'] == 'Load Configuration'
        
        # Verify step directory
        step_dir = phase_dir / f'step_{step1.sequence}_load_config'
        assert step_dir.exists(), f"Step directory should exist: {step_dir}"
        assert (step_dir / '__init__.py').exists()
        assert (step_dir / 'load_config.py').exists()  # Implementation file is named {step_id}.py
        assert (step_dir / 'README.md').exists()
        
        # Verify orchestrator updated
        orchestrator_content = (phase_dir / 'orchestrator_initialization.py').read_text()
        # Module path: .step_{seq}_{id}.{id}
        assert 'from .step_0_load_config.load_config import LoadConfigStep' in orchestrator_content
        assert 'LoadConfigStep(self.project_root, self.ui)' in orchestrator_content
        # Display uses 1-indexed numbers
        assert 'Step 1: Load configuration from file' in orchestrator_content
        
        print("✅ Step 3: First step added with orchestrator integration")
        
        # Step 4: Add second step
        step2 = StepInsertion(
            step_id="validate_config",
            name="Validate Configuration",
            sequence=1,
            description="Validate configuration schema",
            status=ImplementationStatus.PLANNED,
            step_type="validation",
            phase_id="initialization",
            phase_sequence=1,
            is_tui_form=False,
            create_scaffolding=True,
            insert_after="load_config"
        )
        
        success = designer.add_step(
            phase_id="initialization",
            step=step2,
            create_scaffolding=True,
            update_orchestrator=True
        )
        assert success, "Second step should be added successfully"
        
        # Verify second step
        spec_content = designer.manager.spec
        main_flow = spec_content['flows']['main_config_flow']
        phase_data = main_flow['phases'][0]
        assert len(phase_data['steps']) == 2
        
        step_dir2 = phase_dir / f'step_{step2.sequence}_validate_config'
        assert step_dir2.exists(), f"Second step directory should exist: {step_dir2}"
        
        # Verify orchestrator has both steps
        orchestrator_content = (phase_dir / 'orchestrator_initialization.py').read_text()
        assert 'from .step_0_load_config.load_config import LoadConfigStep' in orchestrator_content
        assert 'from .step_1_validate_config.validate_config import ValidateConfigStep' in orchestrator_content
        assert 'Step 1: Load configuration from file' in orchestrator_content
        assert 'Step 2: Validate configuration schema' in orchestrator_content
        
        print("✅ Step 4: Second step added, orchestrator has both steps")
        
        # Step 5: Update step status
        success = designer.update_step_status(
            phase_id="initialization",
            step_id="load_config",
            status=ImplementationStatus.IMPLEMENTED
        )
        assert success, "Step status should be updated"
        
        # Verify status in YAML
        spec_content = designer.manager.spec
        main_flow = spec_content['flows']['main_config_flow']
        phase_data = main_flow['phases'][0]
        step_data = phase_data['steps'][0]
        assert step_data['status'] == 'implemented'
        
        print("✅ Step 5: Step status updated to IMPLEMENTED")
        
        # Step 6: Validate spec
        report = designer.validate()
        assert report.is_valid, f"Spec should be valid. Errors: {report.errors}"
        
        print("✅ Step 6: Specification validated successfully")
        
        # Step 7: Check implementation progress
        progress = designer.get_implementation_progress()
        
        assert progress['total_phases'] == 1
        assert progress['total_steps'] == 2
        assert progress['implemented_steps'] == 1
        assert progress['planned_steps'] == 1
        assert progress['in_progress_steps'] == 0
        assert progress['overall_percentage'] == 50.0
        
        print("✅ Step 7: Implementation progress tracking works")
        print(f"\nProgress Report:")
        print(f"  Total Phases: {progress['total_phases']}")
        print(f"  Total Steps: {progress['total_steps']}")
        print(f"  Implemented: {progress['implemented_steps']} (50%)")
        
        # Final verification: Print directory structure
        print("\n" + "=" * 70)
        print("FINAL DIRECTORY STRUCTURE:")
        print("=" * 70)
        self._print_tree(temp_project, prefix="", max_depth=4)
        
        print("\n" + "=" * 70)
        print("ORCHESTRATOR CONTENT:")
        print("=" * 70)
        print(orchestrator_content)
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Greenfield workflow complete!")
        print("=" * 70)
    
    def test_add_multiple_phases(self, temp_project):
        """Test adding multiple phases in sequence."""
        designer = ControlFlowDesigner.new_project(
            project_name="Multi-Phase Project",
            project_root=temp_project
        )
        
        # Add 3 phases
        for i, phase_id in enumerate(['init', 'process', 'cleanup'], start=1):
            phase = PhaseInsertion(
                phase_id=phase_id,
                name=f"Phase {i}: {phase_id.title()}",
                sequence=i,
                description=f"Phase {i} description",
                status=ImplementationStatus.PLANNED,
                create_scaffolding=True
            )
            
            success = designer.add_phase(phase, create_scaffolding=True)
            assert success
        
        # Verify all phases exist
        spec_content = designer.manager.spec
        main_flow = spec_content['flows']['main_config_flow']
        assert len(main_flow['phases']) == 3
        
        # Verify directories
        for i, phase_id in enumerate(['init', 'process', 'cleanup'], start=1):
            phase_dir = temp_project / 'phases' / f'phase_{i}_{phase_id}'
            assert phase_dir.exists()
            assert (phase_dir / f'orchestrator_{phase_id}.py').exists()
        
        print("✅ Multiple phases added successfully")
    
    def test_validation_catches_errors(self, temp_project):
        """Test that validation catches errors."""
        designer = ControlFlowDesigner.new_project(
            project_name="Validation Test",
            project_root=temp_project
        )
        
        # Initial validation should pass
        report = designer.validate()
        assert report.is_valid
        
        # Manually corrupt spec to test validation
        main_flow = designer.manager.spec['flows']['main_config_flow']
        main_flow['phases'] = [
            {
                'phase_id': 'test1',
                'sequence': 1,
                # Missing required fields
            },
            {
                'phase_id': 'test2',
                'sequence': 1,  # Duplicate sequence
                'name': 'Test 2',
                'description': 'Test'
            }
        ]
        
        report = designer.validate()
        # Should catch missing fields and duplicate sequences
        assert len(report.errors) > 0 or len(report.warnings) > 0
        
        print(f"✅ Validation caught {len(report.errors)} errors and {len(report.warnings)} warnings")
    
    def _print_tree(self, path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """Print directory tree structure."""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                self._print_tree(item, prefix + extension, max_depth, current_depth + 1)


if __name__ == "__main__":
    # Run tests manually
    import sys
    
    test = TestGreenfieldWorkflow()
    
    # Create temp directory
    import tempfile
    import shutil
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        print("Running End-to-End Greenfield Workflow Test")
        print("=" * 70)
        test.test_complete_greenfield_workflow(temp_dir)
        print("\n" + "=" * 70)
        print("✅ All tests completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
