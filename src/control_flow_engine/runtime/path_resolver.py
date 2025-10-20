"""
Path Resolution Service for Control Flow Engine

Provides centralized path resolution for artifacts across phases and steps,
ensuring consistent behavior regardless of execution context (pipeline,
phase standalone, or step standalone).

Usage:
    # Auto-detect project root from current file
    resolver = PathResolver.from_execution_context(__file__)

    # Resolve artifact by ID from control_flows.yml
    config_path = resolver.resolve_artifact_path('user_configuration')

    # Resolve phase output directory
    output_dir = resolver.resolve_phase_output_dir('collection', create=True)
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
import logging

logger = logging.getLogger(__name__)


class PathResolutionError(Exception):
    """Raised when path cannot be resolved."""

    pass


class PathResolver:
    """
    Centralized path resolution service for control flow execution.

    Resolves artifact paths from control_flows.yml specification regardless
    of execution context (pipeline, phase standalone, step standalone).

    This eliminates hardcoded relative path calculations and ensures that
    moving/renaming phases only requires updating control_flows.yml.

    Example:
        >>> resolver = PathResolver.from_execution_context(__file__)
        >>> output_path = resolver.resolve_artifact_path(
        ...     phase_id='collection',
        ...     artifact_id='user_configuration'
        ... )
        >>> print(output_path)
        /opt/.../phases/phase_3_collection/outputs/collected_configuration.yml
    """

    def __init__(self, project_root: Path, control_flows_spec: Dict[str, Any]):
        """
        Initialize path resolver.

        Args:
            project_root: Absolute path to project root (contains phases/)
            control_flows_spec: Parsed control_flows.yml dictionary
        """
        self.project_root = Path(project_root).resolve()
        self.spec = control_flows_spec
        self._artifact_cache = {}
        self._phase_cache = {}
        self._build_indexes()

        logger.debug(f"PathResolver initialized with project_root: {self.project_root}")

    @classmethod
    def from_execution_context(cls, executing_file: Union[str, Path]) -> "PathResolver":
        """
        Create PathResolver by detecting project root from executing file.

        Searches upward from executing file for control_flows.yml or phases/ directory.

        Args:
            executing_file: __file__ from the calling script

        Returns:
            PathResolver instance

        Raises:
            PathResolutionError: If project root cannot be detected

        Example:
            >>> # From any phase or step file
            >>> resolver = PathResolver.from_execution_context(__file__)
        """
        current = Path(executing_file).resolve().parent

        # Search upward for project root markers
        max_depth = 10
        for depth in range(max_depth):
            logger.debug(f"Searching for project root at: {current} (depth {depth})")

            # Check for control_flows.yml (most reliable marker)
            spec_file = current / "design_specs" / "control_flows.yml"
            if spec_file.exists():
                logger.debug(f"Found control_flows.yml at: {spec_file}")
                try:
                    with open(spec_file) as f:
                        spec = yaml.safe_load(f)
                    return cls(project_root=current, control_flows_spec=spec)
                except Exception as e:
                    raise PathResolutionError(f"Failed to parse {spec_file}: {e}")

            # Check for phases directory (fallback)
            if (current / "phases").is_dir():
                logger.debug(f"Found phases/ directory at: {current}")
                # Try to find control_flows.yml nearby
                for candidate in [current, current.parent]:
                    spec_file = candidate / "design_specs" / "control_flows.yml"
                    if spec_file.exists():
                        logger.debug(f"Found control_flows.yml at: {spec_file}")
                        try:
                            with open(spec_file) as f:
                                spec = yaml.safe_load(f)
                            return cls(project_root=current, control_flows_spec=spec)
                        except Exception as e:
                            raise PathResolutionError(
                                f"Failed to parse {spec_file}: {e}"
                            )

            # Move up one level
            if current.parent == current:
                break
            current = current.parent

        raise PathResolutionError(
            f"Could not detect project root from {executing_file}.\n"
            f"Project root should contain 'design_specs/control_flows.yml' or 'phases/' directory.\n"
            f"Searched up to {depth} levels from {Path(executing_file).resolve().parent}"
        )

    def _build_indexes(self):
        """Build indexes of phases and artifacts from control_flows.yml for fast lookup."""
        self._artifact_cache = {}
        self._phase_cache = {}

        # Support both 'control_flows' and 'flows' keys for compatibility
        flows_data = self.spec.get("control_flows") or self.spec.get("flows") or {}

        # Handle both dict (single flow) and list (multiple flows) structures
        if isinstance(flows_data, dict):
            # Single flow or dict of flows
            if "flow_id" in flows_data:
                # Single flow case
                flows_list = [flows_data]
            else:
                # Dict of named flows
                flows_list = list(flows_data.values())
        elif isinstance(flows_data, list):
            # List of flows
            flows_list = flows_data
        else:
            flows_list = []

        for flow in flows_list:
            if not isinstance(flow, dict):
                continue

            flow_id = flow.get("flow_id", flow.get("description", "unknown"))

            for phase in flow.get("phases", []):
                phase_id = phase.get("phase_id")

                # Index phase information
                if phase_id:
                    self._phase_cache[phase_id] = {
                        "flow_id": flow_id,
                        "phase_data": phase,
                    }

                # Index artifacts produced by phase
                for side_effect in phase.get("implementation", {}).get(
                    "side_effects", []
                ):
                    if side_effect.get("action") == "writes":
                        artifact_id = side_effect.get("artifact")
                        location = side_effect.get("location")
                        note = side_effect.get("note", "")

                        if artifact_id and location:
                            self._artifact_cache[artifact_id] = {
                                "phase_id": phase_id,
                                "flow_id": flow_id,
                                "location": location,
                                "action": "writes",
                                "note": note,
                            }

                # Also index consumed artifacts for validation
                for side_effect in phase.get("implementation", {}).get(
                    "side_effects", []
                ):
                    if side_effect.get("action") == "reads":
                        artifact_id = side_effect.get("artifact")
                        location = side_effect.get("location")

                        if artifact_id and location:
                            # Don't overwrite if already exists from writes
                            if artifact_id not in self._artifact_cache:
                                self._artifact_cache[artifact_id] = {
                                    "phase_id": phase_id,
                                    "flow_id": flow_id,
                                    "location": location,
                                    "action": "reads",
                                }

        logger.debug(
            f"Indexed {len(self._artifact_cache)} artifacts from control_flows.yml"
        )
        logger.debug(f"Indexed {len(self._phase_cache)} phases from control_flows.yml")

    def resolve_artifact_path(
        self,
        artifact_id: str,
        phase_id: Optional[str] = None,
        ensure_exists: bool = False,
        create_parent: bool = False,
    ) -> Path:
        """
        Resolve artifact path from artifact ID.

        Args:
            artifact_id: Artifact identifier from control_flows.yml
            phase_id: Optional phase context for disambiguation
            ensure_exists: If True, raise error if path doesn't exist
            create_parent: If True, create parent directories

        Returns:
            Absolute Path to artifact

        Raises:
            PathResolutionError: If artifact cannot be resolved

        Example:
            >>> resolver.resolve_artifact_path('user_configuration', create_parent=True)
            PosixPath('/opt/.../phases/phase_3_collection/outputs/collected_configuration.yml')
        """
        # Look up artifact in index
        if artifact_id not in self._artifact_cache:
            available = list(self._artifact_cache.keys())
            raise PathResolutionError(
                f"Artifact '{artifact_id}' not found in control_flows.yml.\n"
                f"Available artifacts: {available[:10]}{'...' if len(available) > 10 else ''}\n"
                f"Total artifacts: {len(available)}"
            )

        artifact_info = self._artifact_cache[artifact_id]
        relative_path = artifact_info["location"]

        # Resolve to absolute path
        absolute_path = (self.project_root / relative_path).resolve()

        logger.debug(f"Resolved artifact '{artifact_id}' to: {absolute_path}")

        # Validate or create
        if ensure_exists and not absolute_path.exists():
            raise PathResolutionError(
                f"Artifact '{artifact_id}' path does not exist: {absolute_path}\n"
                f"Expected by phase '{artifact_info['phase_id']}' in flow '{artifact_info['flow_id']}'\n"
                f"Action: {artifact_info['action']}"
            )

        if create_parent:
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created parent directory: {absolute_path.parent}")

        return absolute_path

    def resolve_phase_output_dir(self, phase_id: str, create: bool = False) -> Path:
        """
        Resolve output directory for a phase.

        Args:
            phase_id: Phase identifier (e.g., 'discovery', 'collection')
            create: If True, create directory if it doesn't exist

        Returns:
            Absolute Path to phase output directory

        Raises:
            PathResolutionError: If phase not found

        Example:
            >>> resolver.resolve_phase_output_dir('collection', create=True)
            PosixPath('/opt/.../phases/phase_3_collection/outputs')
        """
        # Look up phase in cache
        if phase_id not in self._phase_cache:
            available = list(self._phase_cache.keys())
            raise PathResolutionError(
                f"Phase '{phase_id}' not found in control_flows.yml.\n"
                f"Available phases: {available}"
            )

        phase_data = self._phase_cache[phase_id]["phase_data"]
        phase_dir = phase_data.get("implementation", {}).get("phase_directory")

        if not phase_dir:
            raise PathResolutionError(
                f"Phase '{phase_id}' has no phase_directory in control_flows.yml"
            )

        output_dir = self.project_root / phase_dir / "outputs"

        if create:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")

        logger.debug(f"Resolved phase '{phase_id}' output dir to: {output_dir}")
        return output_dir

    def resolve_phase_directory(self, phase_id: str) -> Path:
        """
        Resolve the directory path for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Absolute Path to phase directory

        Raises:
            PathResolutionError: If phase not found
        """
        if phase_id not in self._phase_cache:
            available = list(self._phase_cache.keys())
            raise PathResolutionError(
                f"Phase '{phase_id}' not found in control_flows.yml.\n"
                f"Available phases: {available}"
            )

        phase_data = self._phase_cache[phase_id]["phase_data"]
        phase_dir = phase_data.get("implementation", {}).get("phase_directory")

        if not phase_dir:
            raise PathResolutionError(
                f"Phase '{phase_id}' has no phase_directory in control_flows.yml"
            )

        absolute_path = (self.project_root / phase_dir).resolve()
        logger.debug(f"Resolved phase '{phase_id}' directory to: {absolute_path}")
        return absolute_path

    def get_project_root(self) -> Path:
        """
        Get absolute path to project root.

        Returns:
            Absolute Path to project root
        """
        return self.project_root

    def validate_artifact_accessible(
        self, artifact_id: str, mode: str = "read"
    ) -> bool:
        """
        Validate artifact is accessible for read or write.

        Args:
            artifact_id: Artifact identifier
            mode: 'read' or 'write'

        Returns:
            True if accessible, False otherwise
        """
        try:
            path = self.resolve_artifact_path(
                artifact_id, ensure_exists=(mode == "read")
            )

            if mode == "read":
                accessible = path.exists() and path.is_file()
            elif mode == "write":
                # Check if parent directory exists or can be created
                accessible = path.parent.exists() or path.parent.parent.exists()
            else:
                accessible = False

            logger.debug(
                f"Artifact '{artifact_id}' accessible for {mode}: {accessible}"
            )
            return accessible

        except PathResolutionError as e:
            logger.debug(f"Artifact '{artifact_id}' not accessible: {e}")
            return False

    def get_artifact_info(self, artifact_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an artifact.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Dict with artifact metadata

        Raises:
            PathResolutionError: If artifact not found
        """
        if artifact_id not in self._artifact_cache:
            available = list(self._artifact_cache.keys())
            raise PathResolutionError(
                f"Artifact '{artifact_id}' not found.\n"
                f"Available: {available[:10]}{'...' if len(available) > 10 else ''}"
            )

        return self._artifact_cache[artifact_id].copy()

    def get_phase_info(self, phase_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Dict with phase metadata

        Raises:
            PathResolutionError: If phase not found
        """
        if phase_id not in self._phase_cache:
            available = list(self._phase_cache.keys())
            raise PathResolutionError(
                f"Phase '{phase_id}' not found.\n" f"Available: {available}"
            )

        return self._phase_cache[phase_id].copy()

    def list_artifacts(
        self, phase_id: Optional[str] = None, action: Optional[str] = None
    ) -> list:
        """
        List all artifacts, optionally filtered by phase or action.

        Args:
            phase_id: Filter by phase (optional)
            action: Filter by action ('reads' or 'writes', optional)

        Returns:
            List of artifact IDs
        """
        artifacts = []

        for artifact_id, info in self._artifact_cache.items():
            if phase_id and info["phase_id"] != phase_id:
                continue
            if action and info["action"] != action:
                continue
            artifacts.append(artifact_id)

        return sorted(artifacts)

    def list_phases(self) -> list:
        """
        List all phase IDs.

        Returns:
            List of phase IDs
        """
        return sorted(self._phase_cache.keys())
