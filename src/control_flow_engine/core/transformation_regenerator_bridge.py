#!/usr/bin/env python3
"""
Transformation-Regenerator Integration Bridge

This module bridges the transformation system with the orchestrator regenerator,
enabling automatic code generation after YAML transformations.

Key Features:
1. Detect which orchestrators are affected by a transformation
2. Automatically regenerate affected orchestrator files
3. Report regeneration results
4. Handle errors gracefully

Usage:
    from transformation_regenerator_bridge import regenerate_after_transformation

    # After applying a transformation
    result = regenerate_after_transformation(
        plan=transformation_plan,
        spec_file=Path("specs/my_phase.yaml"),
        project_base_path=Path("project")
    )
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RegenerationBridge:
    """Bridge between transformation system and orchestrator regenerator."""

    def __init__(self, project_base_path: Path, spec_file: Path):
        """
        Initialize bridge.

        Args:
            project_base_path: Root directory of the project
            spec_file: Path to the control flow YAML spec
        """
        self.project_base_path = Path(project_base_path)
        self.spec_file = Path(spec_file)
        self.results = {"regenerated": [], "failed": [], "skipped": []}

    def regenerate_after_transformation(
        self, plan: "TransformationPlan", flow_name: str = "main_config_flow"
    ) -> Dict[str, Any]:
        """
        Regenerate orchestrators affected by a transformation.

        Args:
            plan: The transformation plan that was applied
            flow_name: Name of the flow being transformed

        Returns:
            Dict with regeneration results:
                - regenerated: List of successfully regenerated files
                - failed: List of failed regenerations
                - skipped: List of skipped files
                - success: Overall success boolean
        """
        logger.info(
            f"Starting orchestrator regeneration after {plan.transformation_type.value}"
        )

        # Detect affected orchestrators based on transformation type
        affected = self._detect_affected_orchestrators(plan, flow_name)

        logger.info(f"Detected {len(affected)} affected orchestrator(s)")

        # Regenerate each affected orchestrator
        for orchestrator_info in affected:
            self._regenerate_orchestrator(orchestrator_info, flow_name)

        # Compile results
        self.results["success"] = len(self.results["failed"]) == 0

        logger.info(
            f"Regeneration complete: {len(self.results['regenerated'])} succeeded, "
            f"{len(self.results['failed'])} failed, {len(self.results['skipped'])} skipped"
        )

        return self.results

    def _detect_affected_orchestrators(
        self, plan: "TransformationPlan", flow_name: str
    ) -> List[Dict[str, Any]]:
        """
        Detect which orchestrators need to be regenerated.

        Args:
            plan: Transformation plan
            flow_name: Flow name

        Returns:
            List of orchestrator info dicts
        """
        affected = []

        # Analyze transformation mappings
        for mapping in plan.mappings:
            if mapping.element_type == "phase":
                # Phase-level change affects:
                # 1. Global orchestrator (if sequence changed or phase added/deleted)
                # 2. Phase orchestrator (if steps changed)

                if mapping.operation in ["insert", "delete", "renumber"]:
                    # Global orchestrator needs update
                    global_orch = (
                        self.project_base_path / "phases" / "phases_orchestrator.py"
                    )
                    if global_orch not in [a["file"] for a in affected]:
                        affected.append(
                            {
                                "file": global_orch,
                                "type": "global",
                                "flow_name": flow_name,
                            }
                        )

                # If phase orchestrator exists, mark for update
                if mapping.element_id:
                    phase_orch = self._find_phase_orchestrator(mapping.element_id)
                    if phase_orch and phase_orch not in [a["file"] for a in affected]:
                        affected.append(
                            {
                                "file": phase_orch,
                                "type": "phase",
                                "phase_id": mapping.element_id,
                                "flow_name": flow_name,
                            }
                        )

            elif mapping.element_type == "step":
                # Step-level change affects phase orchestrator
                phase_id = mapping.old_parent or mapping.new_parent
                if phase_id:
                    phase_orch = self._find_phase_orchestrator(phase_id)
                    if phase_orch and phase_orch not in [a["file"] for a in affected]:
                        affected.append(
                            {
                                "file": phase_orch,
                                "type": "phase",
                                "phase_id": phase_id,
                                "flow_name": flow_name,
                            }
                        )

        return affected

    def _find_phase_orchestrator(self, phase_id: str) -> Optional[Path]:
        """
        Find the orchestrator file for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Path to orchestrator file, or None if not found
        """
        # Search for phase directory
        phases_dir = self.project_base_path / "phases"
        if not phases_dir.exists():
            return None

        # Look for phase_*_{phase_id} directory
        for phase_dir in phases_dir.glob(f"phase_*_{phase_id}"):
            # Check for orchestrator file
            orch_file = phase_dir / f"orchestrator_{phase_id}.py"
            if orch_file.exists():
                return orch_file

        return None

    def _regenerate_orchestrator(
        self, orchestrator_info: Dict[str, Any], flow_name: str
    ) -> bool:
        """
        Regenerate a single orchestrator file.

        Args:
            orchestrator_info: Dict with orchestrator information
            flow_name: Flow name

        Returns:
            True if successful
        """
        orch_file = orchestrator_info["file"]
        orch_type = orchestrator_info["type"]

        logger.info(f"Regenerating {orch_type} orchestrator: {orch_file}")

        # Check if file exists
        if not orch_file.exists():
            logger.warning(f"Orchestrator file not found: {orch_file}")
            self.results["skipped"].append(str(orch_file))
            return False

        try:
            # Import regenerator (lazy import to avoid circular dependencies)
            from .orchestrator_regenerator import OrchestratorRegenerator

            # Create regenerator
            regenerator = OrchestratorRegenerator(self.spec_file)

            # Regenerate based on type
            if orch_type == "global":
                success = regenerator.regenerate_global_orchestrator(
                    orchestrator_file=orch_file, flow_name=flow_name
                )
            elif orch_type == "phase":
                phase_id = orchestrator_info["phase_id"]
                success = regenerator.regenerate_phase_orchestrator(
                    orchestrator_file=orch_file, phase_id=phase_id, flow_name=flow_name
                )
            else:
                logger.error(f"Unknown orchestrator type: {orch_type}")
                success = False

            if success:
                logger.info(f"✅ Successfully regenerated {orch_file}")
                self.results["regenerated"].append(str(orch_file))
            else:
                logger.error(f"❌ Failed to regenerate {orch_file}")
                self.results["failed"].append(str(orch_file))

            return success

        except Exception as e:
            logger.error(f"❌ Error regenerating {orch_file}: {e}")
            self.results["failed"].append(str(orch_file))
            return False


def regenerate_after_transformation(
    plan: "TransformationPlan",
    spec_file: Path,
    project_base_path: Path,
    flow_name: str = "main_config_flow",
) -> Dict[str, Any]:
    """
    Convenience function to regenerate orchestrators after a transformation.

    Args:
        plan: The transformation plan that was applied
        spec_file: Path to the control flow YAML spec
        project_base_path: Root directory of the project
        flow_name: Name of the flow being transformed

    Returns:
        Dict with regeneration results

    Example:
        result = regenerate_after_transformation(
            plan=transformation_plan,
            spec_file=Path("specs/my_phase.yaml"),
            project_base_path=Path("project")
        )

        if result['success']:
            print(f"Regenerated {len(result['regenerated'])} file(s)")
        else:
            print(f"Failed to regenerate {len(result['failed'])} file(s)")
    """
    bridge = RegenerationBridge(project_base_path, spec_file)
    return bridge.regenerate_after_transformation(plan, flow_name)


# Export public API
__all__ = ["RegenerationBridge", "regenerate_after_transformation"]
