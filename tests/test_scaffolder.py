#!/usr/bin/env python3
"""
Unit tests for ScaffoldGenerator

Tests the scaffolding functionality including:
- Phase scaffolding creation
- Step scaffolding creation
- Safety features (existence checks, force parameter)
- File generation (init, implementation, orchestrator, README)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile
import shutil
from control_flow_engine.core.scaffolder import (
    ScaffoldGenerator,
    PhaseInsertion,
    StepInsertion,
    ImplementationStatus
)


def create_test_project(root: Path) -> Path:
    """Create a test project structure."""
    (root / "phases").mkdir()
    return root


class TestScaffoldGenerator:
    """Test suite for ScaffoldGenerator."""
    
    @staticmethod
    def test_create_phase_scaffolding():
        """Test creating phase scaffolding."""
        print("\n" + "=" * 70)
        print("TEST: Create Phase Scaffolding")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            generator = ScaffoldGenerator(project)
            
            phase = PhaseInsertion(
                phase_id="phase_1_test",
                name="Test Phase",
                sequence=1,
                description="A test phase",
                status=ImplementationStatus.PLANNED
            )
            
            result = generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=False
            )
            
            # Verify directory created
            phase_dir = project / "phases" / "phase_1_test"
            assert phase_dir.exists(), "Phase directory not created"
            
            # Verify files created
            assert (phase_dir / "__init__.py").exists(), "__init__.py not created"
            assert (phase_dir / "orchestrator_test.py").exists(), "Orchestrator not created"
            assert (phase_dir / "README.md").exists(), "README.md not created"
            
            # Verify result
            assert result is not None, "Result should not be None"
            assert 'directory' in result, "Result should contain directory"
            assert 'init' in result, "Result should contain init"
            assert 'orchestrator' in result, "Result should contain orchestrator"
            assert 'readme' in result, "Result should contain readme"
            
            print("✅ PASS: Phase scaffolding created successfully")
    
    @staticmethod
    def test_create_step_scaffolding():
        """Test creating step scaffolding."""
        print("\n" + "=" * 70)
        print("TEST: Create Step Scaffolding")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            
            # Create phase first
            phase_dir = project / "phases" / "phase_1_test"
            phase_dir.mkdir()
            
            generator = ScaffoldGenerator(project)
            
            step = StepInsertion(
                step_id="test_step",
                name="Test Step",
                sequence=1,
                description="A test step",
                status=ImplementationStatus.PLANNED,
                step_type="processing",
                phase_id="phase_1_test",
                phase_sequence=1
            )
            
            result = generator.create_step_scaffolding(
                step=step,
                base_path=phase_dir,
                force=False
            )
            
            # Verify directory created
            step_dir = phase_dir / "step_1_test_step"
            assert step_dir.exists(), "Step directory not created"
            
            # Verify files created
            assert (step_dir / "__init__.py").exists(), "__init__.py not created"
            assert (step_dir / "test_step.py").exists(), "Implementation file not created"
            assert (step_dir / "README.md").exists(), "README.md not created"
            
            # Verify result
            assert result is not None, "Result should not be None"
            assert 'directory' in result, "Result should contain directory"
            assert 'init' in result, "Result should contain init"
            assert 'implementation' in result, "Result should contain implementation"
            assert 'readme' in result, "Result should contain readme"
            
            print("✅ PASS: Step scaffolding created successfully")
    
    @staticmethod
    def test_phase_exists_without_force():
        """Test that existing phase is not overwritten without force."""
        print("\n" + "=" * 70)
        print("TEST: Phase Exists Without Force")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            generator = ScaffoldGenerator(project)
            
            phase = PhaseInsertion(
                phase_id="phase_1_test",
                name="Test Phase",
                sequence=1,
                description="A test phase",
                status=ImplementationStatus.PLANNED
            )
            
            # Create phase first time
            result1 = generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=False
            )
            assert result1 is not None, "First creation should succeed"
            
            # Try to create again without force
            result2 = generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=False
            )
            assert result2 is None, "Second creation should be blocked"
            
            print("✅ PASS: Existing phase protected without force")
    
    @staticmethod
    def test_phase_overwrite_with_force():
        """Test that existing phase can be overwritten with force=True."""
        print("\n" + "=" * 70)
        print("TEST: Phase Overwrite With Force")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            generator = ScaffoldGenerator(project)
            
            phase = PhaseInsertion(
                phase_id="phase_1_test",
                name="Test Phase",
                sequence=1,
                description="A test phase",
                status=ImplementationStatus.PLANNED
            )
            
            # Create phase first time
            result1 = generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=False
            )
            assert result1 is not None, "First creation should succeed"
            
            # Modify a file
            readme = project / "phases" / "phase_1_test" / "README.md"
            readme.write_text("Modified content")
            
            # Recreate with force
            result2 = generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=True
            )
            assert result2 is not None, "Recreation with force should succeed"
            
            # Verify file was overwritten
            content = readme.read_text()
            assert "Modified content" not in content, "File should be overwritten"
            assert "Test Phase" in content, "New content should be present"
            
            print("✅ PASS: Existing phase overwritten with force")
    
    @staticmethod
    def test_step_exists_without_force():
        """Test that existing step is not overwritten without force."""
        print("\n" + "=" * 70)
        print("TEST: Step Exists Without Force")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            phase_dir = project / "phases" / "phase_1_test"
            phase_dir.mkdir()
            
            generator = ScaffoldGenerator(project)
            
            step = StepInsertion(
                step_id="test_step",
                name="Test Step",
                sequence=1,
                description="A test step",
                status=ImplementationStatus.PLANNED,
                step_type="processing",
                phase_id="phase_1_test",
                phase_sequence=1
            )
            
            # Create step first time
            result1 = generator.create_step_scaffolding(
                step=step,
                base_path=phase_dir,
                force=False
            )
            assert result1 is not None, "First creation should succeed"
            
            # Try to create again without force
            result2 = generator.create_step_scaffolding(
                step=step,
                base_path=phase_dir,
                force=False
            )
            assert result2 is None, "Second creation should be blocked"
            
            print("✅ PASS: Existing step protected without force")
    
    @staticmethod
    def test_generated_content():
        """Test that generated files contain expected content."""
        print("\n" + "=" * 70)
        print("TEST: Generated Content Quality")
        print("=" * 70)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_test_project(Path(tmpdir))
            generator = ScaffoldGenerator(project)
            
            phase = PhaseInsertion(
                phase_id="phase_2_analysis",
                name="Data Analysis",
                sequence=2,
                description="Analyze the data thoroughly",
                status=ImplementationStatus.IN_PROGRESS,
                orchestrator_class_name="DataAnalysisOrchestrator"
            )
            
            generator.create_phase_scaffolding(
                phase=phase,
                base_path=project / "phases",
                force=False
            )
            
            # Check init file
            init_content = (project / "phases" / "phase_2_analysis" / "__init__.py").read_text()
            assert "Phase 2 - Data Analysis" in init_content, "Init missing phase info"
            assert "DataAnalysisOrchestrator" in init_content, "Init missing orchestrator import"
            
            # Check orchestrator file
            orch_content = (project / "phases" / "phase_2_analysis" / "orchestrator_analysis.py").read_text()
            assert "DataAnalysisOrchestrator" in orch_content, "Orchestrator missing class name"
            assert "Analyze the data thoroughly" in orch_content, "Orchestrator missing description"
            
            # Check README
            readme_content = (project / "phases" / "phase_2_analysis" / "README.md").read_text()
            assert "# Phase 2: Data Analysis" in readme_content, "README missing title"
            assert "Analyze the data thoroughly" in readme_content, "README missing description"
            assert "IN_PROGRESS" in readme_content, "README missing status"
            
            print("✅ PASS: Generated content contains expected information")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ScaffoldGenerator Test Suite")
    print("=" * 70)
    
    tests = [
        TestScaffoldGenerator.test_create_phase_scaffolding,
        TestScaffoldGenerator.test_create_step_scaffolding,
        TestScaffoldGenerator.test_phase_exists_without_force,
        TestScaffoldGenerator.test_phase_overwrite_with_force,
        TestScaffoldGenerator.test_step_exists_without_force,
        TestScaffoldGenerator.test_generated_content,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
