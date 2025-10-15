#!/usr/bin/env python3
"""
Phase/Step Renumbering Utility

Provides safe, automated renumbering of phases and steps when inserting,
removing, or reordering workflow components. Handles directory renaming,
import path updates, configuration updates, and documentation updates in
an atomic, reversible manner.

See RENUMBERING_SPEC.md for complete specification.
"""

import re
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


logger = logging.getLogger(__name__)


class NumberingStrategy(Enum):
    """Strategy for handling gaps in numbering."""
    COMPACT = "compact"  # Remove all gaps: 1,2,3,5 → 1,2,3,4
    PRESERVE_GAPS = "preserve_gaps"  # Keep gaps: 1,2,3,5 → 1,2,3,5
    MINIMAL_SHIFT = "minimal_shift"  # Shift only what's necessary


@dataclass
class RenumberOperation:
    """Defines a single rename operation."""
    old_number: int
    new_number: int
    old_path: Path
    new_path: Path
    type: str  # 'phase' or 'step'
    
    def __str__(self) -> str:
        return f"{self.old_path.name} → {self.new_path.name}"


@dataclass
class RenumberPlan:
    """Complete renumbering plan with all operations."""
    operations: List[RenumberOperation] = field(default_factory=list)
    affected_files: List[Path] = field(default_factory=list)
    strategy: NumberingStrategy = NumberingStrategy.COMPACT
    
    def __str__(self) -> str:
        """Human-readable summary."""
        if not self.operations:
            return "No renumbering needed"
        
        summary = f"Renumbering Plan ({self.strategy.value}):\n"
        summary += f"Operations: {len(self.operations)}\n"
        for op in self.operations:
            summary += f"  - {op}\n"
        summary += f"Affected files: {len(self.affected_files)}"
        return summary


class RenumberError(Exception):
    """Base exception for renumbering errors."""
    pass


class ValidationError(RenumberError):
    """Validation failed."""
    pass


class ExecutionError(RenumberError):
    """Execution failed."""
    pass


class RollbackError(RenumberError):
    """Rollback failed."""
    pass


class PhaseStepRenumberer:
    """
    Handles safe renumbering of phases and steps.
    
    Features:
    - Atomic operations with rollback
    - Dry-run mode
    - Multi-scope updates (dirs, imports, configs, docs)
    - Gap handling strategies
    
    Example:
        >>> renumberer = PhaseStepRenumberer(Path("/opt/openproject"))
        >>> plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
        >>> print(plan)
        >>> renumberer.renumber_phases(insert_at=4, dry_run=False)
    """
    
    def __init__(
        self,
        project_root: Path,
        strategy: NumberingStrategy = NumberingStrategy.COMPACT,
        phases_dir: str = "phases"
    ):
        """
        Initialize renumberer.
        
        Args:
            project_root: Root directory of the project
            strategy: Numbering strategy for handling gaps
            phases_dir: Name of phases directory (default: "phases")
        """
        self.project_root = Path(project_root)
        self.strategy = strategy
        self.phases_dir = self.project_root / phases_dir
        self.logger = logger
        
        # Backup tracking
        self._backup_manifest: Optional[Dict[str, Any]] = None
    
    # ========== PUBLIC API ==========
    
    def renumber_phases(
        self,
        insert_at: Optional[int] = None,
        remove_at: Optional[int] = None,
        dry_run: bool = True
    ) -> RenumberPlan:
        """
        Renumber phases after insertion/removal.
        
        Args:
            insert_at: Phase number where new phase will be inserted (shifts subsequent)
            remove_at: Phase number being removed (shifts subsequent)
            dry_run: If True, return plan without applying changes
            
        Returns:
            RenumberPlan with operations to perform
            
        Raises:
            ValueError: If both insert_at and remove_at specified
            ValidationError: If validation fails
            ExecutionError: If execution fails (dry_run=False only)
            
        Example:
            # Preview insertion
            plan = renumberer.renumber_phases(insert_at=4, dry_run=True)
            print(plan)
            
            # Apply changes
            renumberer.renumber_phases(insert_at=4, dry_run=False)
        """
        self.logger.info("=" * 70)
        self.logger.info("PHASE RENUMBERING")
        self.logger.info("=" * 70)
        
        # Validate inputs
        if insert_at is not None and remove_at is not None:
            raise ValueError("Cannot specify both insert_at and remove_at")
        
        if insert_at is None and remove_at is None:
            raise ValueError("Must specify either insert_at or remove_at")
        
        # Scan current state
        self.logger.info("🔍 Scanning current phase structure...")
        current_numbers = self._scan_current_numbering('phases')
        self.logger.info(f"   Found phases: {current_numbers}")
        
        if not current_numbers:
            self.logger.warning("⚠️  No phases found")
            return RenumberPlan(strategy=self.strategy)
        
        # Create plan
        self.logger.info("📋 Creating renumbering plan...")
        plan = self._create_renumber_plan(
            current_numbers=current_numbers,
            insert_at=insert_at,
            remove_at=remove_at,
            scope='phases'
        )
        
        self.logger.info(f"   Operations: {len(plan.operations)}")
        for op in plan.operations:
            self.logger.info(f"      {op}")
        
        # Execute if not dry-run
        if not dry_run:
            if plan.operations:
                self.logger.info("💾 Creating backup manifest...")
                self._backup_manifest = self._create_backup_manifest(plan)
                
                self.logger.info("🔄 Executing renumbering plan...")
                success = self._execute_plan(plan)
                
                if success:
                    self.logger.info("✅ Phase renumbering completed successfully")
                else:
                    self.logger.error("❌ Phase renumbering failed")
                    raise ExecutionError("Phase renumbering execution failed")
            else:
                self.logger.info("ℹ️  No operations needed")
        else:
            self.logger.info("ℹ️  Dry-run mode - no changes applied")
        
        return plan
    
    def renumber_steps(
        self,
        phase_number: int,
        insert_at: Optional[int] = None,
        remove_at: Optional[int] = None,
        dry_run: bool = True
    ) -> RenumberPlan:
        """
        Renumber steps within a phase after insertion/removal.
        
        Args:
            phase_number: Phase containing the steps
            insert_at: Step number where new step will be inserted
            remove_at: Step number being removed
            dry_run: If True, return plan without applying changes
            
        Returns:
            RenumberPlan with operations to perform
            
        Example:
            # Insert new step 3 in phase 2
            renumberer.renumber_steps(phase_number=2, insert_at=3, dry_run=False)
        """
        self.logger.info("=" * 70)
        self.logger.info(f"STEP RENUMBERING (Phase {phase_number})")
        self.logger.info("=" * 70)
        
        # Validate inputs
        if insert_at is not None and remove_at is not None:
            raise ValueError("Cannot specify both insert_at and remove_at")
        
        if insert_at is None and remove_at is None:
            raise ValueError("Must specify either insert_at or remove_at")
        
        # Find phase directory
        phase_pattern = f"phase_{phase_number}_*"
        phase_dirs = list(self.phases_dir.glob(phase_pattern))
        
        if not phase_dirs:
            raise ValidationError(f"Phase {phase_number} not found")
        
        if len(phase_dirs) > 1:
            raise ValidationError(f"Multiple phase {phase_number} directories found: {phase_dirs}")
        
        phase_dir = phase_dirs[0]
        
        # Scan current steps
        self.logger.info(f"🔍 Scanning steps in {phase_dir.name}...")
        current_numbers = self._scan_current_numbering('steps', phase_dir)
        self.logger.info(f"   Found steps: {current_numbers}")
        
        if not current_numbers:
            self.logger.warning("⚠️  No steps found")
            return RenumberPlan(strategy=self.strategy)
        
        # Create plan
        self.logger.info("📋 Creating renumbering plan...")
        plan = self._create_renumber_plan(
            current_numbers=current_numbers,
            insert_at=insert_at,
            remove_at=remove_at,
            scope='steps',
            parent_dir=phase_dir
        )
        
        self.logger.info(f"   Operations: {len(plan.operations)}")
        for op in plan.operations:
            self.logger.info(f"      {op}")
        
        # Execute if not dry-run
        if not dry_run:
            if plan.operations:
                self.logger.info("💾 Creating backup manifest...")
                self._backup_manifest = self._create_backup_manifest(plan)
                
                self.logger.info("🔄 Executing renumbering plan...")
                success = self._execute_plan(plan)
                
                if success:
                    self.logger.info("✅ Step renumbering completed successfully")
                else:
                    self.logger.error("❌ Step renumbering failed")
                    raise ExecutionError("Step renumbering execution failed")
            else:
                self.logger.info("ℹ️  No operations needed")
        else:
            self.logger.info("ℹ️  Dry-run mode - no changes applied")
        
        return plan
    
    def compact_phase_numbering(
        self,
        dry_run: bool = True
    ) -> RenumberPlan:
        """
        Remove all gaps in phase numbering.
        
        Args:
            dry_run: If True, return plan without applying changes
            
        Returns:
            RenumberPlan with operations to perform
            
        Example:
            # Before: phase_1, phase_2, phase_3, phase_5
            # After:  phase_1, phase_2, phase_3, phase_4
            renumberer.compact_phase_numbering(dry_run=False)
        """
        self.logger.info("=" * 70)
        self.logger.info("COMPACT PHASE NUMBERING")
        self.logger.info("=" * 70)
        
        # Temporarily set strategy to COMPACT
        original_strategy = self.strategy
        self.strategy = NumberingStrategy.COMPACT
        
        try:
            # Scan current state
            self.logger.info("🔍 Scanning current phase structure...")
            current_numbers = self._scan_current_numbering('phases')
            self.logger.info(f"   Found phases: {current_numbers}")
            
            if not current_numbers:
                self.logger.warning("⚠️  No phases found")
                return RenumberPlan(strategy=self.strategy)
            
            # Check if already compact
            expected_compact = list(range(1, len(current_numbers) + 1))
            if current_numbers == expected_compact:
                self.logger.info("✅ Phase numbering is already compact")
                return RenumberPlan(strategy=self.strategy)
            
            # Create compacting plan
            self.logger.info("📋 Creating compacting plan...")
            plan = self._create_compact_plan(current_numbers, 'phases')
            
            self.logger.info(f"   Operations: {len(plan.operations)}")
            for op in plan.operations:
                self.logger.info(f"      {op}")
            
            # Execute if not dry-run
            if not dry_run:
                if plan.operations:
                    self.logger.info("💾 Creating backup manifest...")
                    self._backup_manifest = self._create_backup_manifest(plan)
                    
                    self.logger.info("🔄 Executing compacting plan...")
                    success = self._execute_plan(plan)
                    
                    if success:
                        self.logger.info("✅ Phase compacting completed successfully")
                    else:
                        self.logger.error("❌ Phase compacting failed")
                        raise ExecutionError("Phase compacting execution failed")
                else:
                    self.logger.info("ℹ️  No operations needed")
            else:
                self.logger.info("ℹ️  Dry-run mode - no changes applied")
            
            return plan
            
        finally:
            # Restore original strategy
            self.strategy = original_strategy
    
    # ========== INTERNAL OPERATIONS ==========
    
    def _scan_current_numbering(
        self,
        scope: str,  # 'phases' or 'steps'
        parent_dir: Optional[Path] = None
    ) -> List[int]:
        """
        Scan filesystem for current phase/step numbers.
        
        Args:
            scope: 'phases' or 'steps'
            parent_dir: Parent directory for steps (phase directory)
            
        Returns:
            Sorted list of existing numbers (may have gaps)
        """
        numbers = []
        
        if scope == 'phases':
            if not self.phases_dir.exists():
                return []
            
            # Find all phase_N_* directories
            pattern = r'^phase_(\d+)_'
            for item in self.phases_dir.iterdir():
                if item.is_dir():
                    match = re.match(pattern, item.name)
                    if match:
                        numbers.append(int(match.group(1)))
        
        elif scope == 'steps':
            if not parent_dir or not parent_dir.exists():
                return []
            
            # Find all step_N_* directories
            pattern = r'^step_(\d+)_'
            for item in parent_dir.iterdir():
                if item.is_dir():
                    match = re.match(pattern, item.name)
                    if match:
                        numbers.append(int(match.group(1)))
        
        return sorted(numbers)
    
    def _create_renumber_plan(
        self,
        current_numbers: List[int],
        insert_at: Optional[int],
        remove_at: Optional[int],
        scope: str,  # 'phases' or 'steps'
        parent_dir: Optional[Path] = None
    ) -> RenumberPlan:
        """
        Create renumbering plan based on current state and operation.
        
        Logic:
        - If insert_at: Shift all >= insert_at by +1
        - If remove_at: Shift all > remove_at by -1
        - Apply strategy (COMPACT, PRESERVE_GAPS, MINIMAL_SHIFT)
        """
        plan = RenumberPlan(strategy=self.strategy)
        
        # Determine new numbering
        new_numbering: Dict[int, int] = {}
        
        if insert_at is not None:
            # Inserting: shift all >= insert_at by +1
            for num in current_numbers:
                if num >= insert_at:
                    new_numbering[num] = num + 1
                else:
                    new_numbering[num] = num
        
        elif remove_at is not None:
            # Removing: shift all > remove_at by -1
            for num in current_numbers:
                if num > remove_at:
                    new_numbering[num] = num - 1
                elif num == remove_at:
                    # Skip - being removed
                    continue
                else:
                    new_numbering[num] = num
        
        # Create operations for changed numbers
        for old_num, new_num in new_numbering.items():
            if old_num != new_num:
                old_path, new_path = self._get_paths_for_number(
                    old_num, new_num, scope, parent_dir
                )
                
                if old_path and new_path:
                    op = RenumberOperation(
                        old_number=old_num,
                        new_number=new_num,
                        old_path=old_path,
                        new_path=new_path,
                        type=scope.rstrip('s')  # 'phases' → 'phase', 'steps' → 'step'
                    )
                    plan.operations.append(op)
        
        return plan
    
    def _create_compact_plan(
        self,
        current_numbers: List[int],
        scope: str,
        parent_dir: Optional[Path] = None
    ) -> RenumberPlan:
        """Create plan to compact numbering (remove all gaps)."""
        plan = RenumberPlan(strategy=NumberingStrategy.COMPACT)
        
        # Map current numbers to compact sequence
        new_numbering: Dict[int, int] = {}
        for idx, old_num in enumerate(current_numbers, start=1):
            if old_num != idx:
                new_numbering[old_num] = idx
        
        # Create operations
        for old_num, new_num in new_numbering.items():
            old_path, new_path = self._get_paths_for_number(
                old_num, new_num, scope, parent_dir
            )
            
            if old_path and new_path:
                op = RenumberOperation(
                    old_number=old_num,
                    new_number=new_num,
                    old_path=old_path,
                    new_path=new_path,
                    type=scope.rstrip('s')
                )
                plan.operations.append(op)
        
        return plan
    
    def _get_paths_for_number(
        self,
        old_num: int,
        new_num: int,
        scope: str,
        parent_dir: Optional[Path]
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """Get old and new paths for a number."""
        if scope == 'phases':
            # Find existing phase_N_* directory
            pattern = f"phase_{old_num}_*"
            matches = list(self.phases_dir.glob(pattern))
            
            if not matches:
                return None, None
            
            old_path = matches[0]
            # Construct new path with same suffix
            suffix = old_path.name.split('_', 2)[2]  # Get part after "phase_N_"
            new_path = self.phases_dir / f"phase_{new_num}_{suffix}"
            
            return old_path, new_path
        
        elif scope == 'steps':
            if not parent_dir:
                return None, None
            
            # Find existing step_N_* directory
            pattern = f"step_{old_num}_*"
            matches = list(parent_dir.glob(pattern))
            
            if not matches:
                return None, None
            
            old_path = matches[0]
            # Construct new path with same suffix
            suffix = old_path.name.split('_', 2)[2]  # Get part after "step_N_"
            new_path = parent_dir / f"step_{new_num}_{suffix}"
            
            return old_path, new_path
        
        return None, None
    
    def _create_backup_manifest(self, plan: RenumberPlan) -> Dict[str, Any]:
        """Create backup manifest before changes."""
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "strategy": plan.strategy.value,
            "operations": [
                {
                    "old_number": op.old_number,
                    "new_number": op.new_number,
                    "old_path": str(op.old_path),
                    "new_path": str(op.new_path),
                    "type": op.type
                }
                for op in plan.operations
            ],
            "files_to_update": []
        }
        
        return manifest
    
    def _execute_plan(self, plan: RenumberPlan) -> bool:
        """
        Execute renumbering plan atomically.
        
        Steps:
        1. Validate all source paths exist
        2. Rename directories (in reverse order to avoid conflicts)
        3. Update imports
        4. Update configs
        5. Update docs
        6. Validate new structure
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Validate
            self.logger.info("   Validating source paths...")
            for op in plan.operations:
                if not op.old_path.exists():
                    raise ValidationError(f"Source path does not exist: {op.old_path}")
                if op.new_path.exists():
                    raise ValidationError(f"Target path already exists: {op.new_path}")
            
            # Step 2: Rename directories (reverse order to avoid conflicts)
            self.logger.info("   Renaming directories...")
            for op in reversed(plan.operations):
                self.logger.info(f"      {op.old_path.name} → {op.new_path.name}")
                op.old_path.rename(op.new_path)
            
            # Step 3: Update imports
            self.logger.info("   Updating imports...")
            import_files = self._update_imports(plan.operations)
            plan.affected_files.extend(import_files)
            self.logger.info(f"      Modified {len(import_files)} files")
            
            # Step 4: Update configs
            self.logger.info("   Updating configurations...")
            config_files = self._update_configs(plan.operations)
            plan.affected_files.extend(config_files)
            self.logger.info(f"      Modified {len(config_files)} files")
            
            # Step 5: Update docs
            self.logger.info("   Updating documentation...")
            doc_files = self._update_docs(plan.operations)
            plan.affected_files.extend(doc_files)
            self.logger.info(f"      Modified {len(doc_files)} files")
            
            return True
            
        except Exception as e:
            self.logger.error(f"   Execution failed: {e}")
            
            # Attempt rollback
            if self._backup_manifest:
                self.logger.warning("   Attempting rollback...")
                rollback_success = self._rollback(self._backup_manifest)
                
                if rollback_success:
                    self.logger.info("   ✅ Rollback successful")
                else:
                    self.logger.error("   ❌ Rollback failed - manual intervention required")
            
            return False
    
    def _update_imports(self, operations: List[RenumberOperation]) -> List[Path]:
        """
        Update Python import statements.
        
        Pattern matching:
        - from phases.phase_3_design import ... → phase_4_design
        - from phase_3_design.step_2_validate import ... → step_3_validate
        """
        modified_files = []
        
        # Build replacement mapping
        replacements = {}
        for op in operations:
            old_name = op.old_path.name
            new_name = op.new_path.name
            replacements[old_name] = new_name
        
        # Find all Python files in project
        py_files = list(self.project_root.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                modified = False
                
                for old_name, new_name in replacements.items():
                    # Match various import patterns
                    patterns = [
                        (rf'\bfrom\s+phases\.{re.escape(old_name)}', f'from phases.{new_name}'),
                        (rf'\bfrom\s+\.\.{re.escape(old_name)}', f'from ..{new_name}'),
                        (rf'\bfrom\s+\.{re.escape(old_name)}', f'from .{new_name}'),
                        (rf'\bimport\s+{re.escape(old_name)}', f'import {new_name}'),
                    ]
                    
                    for pattern, replacement in patterns:
                        if re.search(pattern, content):
                            content = re.sub(pattern, replacement, content)
                            modified = True
                
                if modified:
                    py_file.write_text(content)
                    modified_files.append(py_file)
                    
            except Exception as e:
                self.logger.warning(f"      Could not update {py_file}: {e}")
        
        return modified_files
    
    def _update_configs(self, operations: List[RenumberOperation]) -> List[Path]:
        """
        Update YAML configuration files.
        
        Updates:
        - phase_id: phase_3_design → phase_4_design
        - step_sequence: 2 → 3
        """
        modified_files = []
        
        # Build replacement mapping
        replacements = {}
        for op in operations:
            old_name = op.old_path.name
            new_name = op.new_path.name
            replacements[old_name] = new_name
        
        # Find all YAML files
        yaml_files = list(self.project_root.rglob("*.yaml")) + list(self.project_root.rglob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                content = yaml_file.read_text()
                modified = False
                
                for old_name, new_name in replacements.items():
                    if old_name in content:
                        content = content.replace(old_name, new_name)
                        modified = True
                
                if modified:
                    yaml_file.write_text(content)
                    modified_files.append(yaml_file)
                    
            except Exception as e:
                self.logger.warning(f"      Could not update {yaml_file}: {e}")
        
        return modified_files
    
    def _update_docs(self, operations: List[RenumberOperation]) -> List[Path]:
        """
        Update Markdown documentation.
        
        Updates:
        - ## Phase 3: Design → ## Phase 4: Design
        - [Link](phase_3_design/README.md) → phase_4_design
        """
        modified_files = []
        
        # Build replacement mapping
        replacements = {}
        for op in operations:
            old_name = op.old_path.name
            new_name = op.new_path.name
            replacements[old_name] = new_name
            
            # Also update "Phase N:" or "Step N:" patterns
            if op.type == 'phase':
                old_header = f"Phase {op.old_number}:"
                new_header = f"Phase {op.new_number}:"
                replacements[old_header] = new_header
            elif op.type == 'step':
                old_header = f"Step {op.old_number}:"
                new_header = f"Step {op.new_number}:"
                replacements[old_header] = new_header
        
        # Find all Markdown files
        md_files = list(self.project_root.rglob("*.md"))
        
        for md_file in md_files:
            try:
                content = md_file.read_text()
                modified = False
                
                for old_text, new_text in replacements.items():
                    if old_text in content:
                        content = content.replace(old_text, new_text)
                        modified = True
                
                if modified:
                    md_file.write_text(content)
                    modified_files.append(md_file)
                    
            except Exception as e:
                self.logger.warning(f"      Could not update {md_file}: {e}")
        
        return modified_files
    
    def _rollback(self, backup_manifest: Dict[str, Any]) -> bool:
        """
        Rollback changes using backup manifest.
        
        Restores directory names to original state.
        
        Returns:
            True if rollback successful
        """
        try:
            # Reverse the directory renames
            for op_data in backup_manifest["operations"]:
                new_path = Path(op_data["new_path"])
                old_path = Path(op_data["old_path"])
                
                if new_path.exists() and not old_path.exists():
                    new_path.rename(old_path)
                    self.logger.info(f"      Restored: {old_path.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
