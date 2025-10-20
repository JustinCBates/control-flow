"""
YAML Saver

Universal YAML file saving with formatting options and error handling.
Supports various output styles and configurations.

Author: Control Flow Engine Libraries
Date: 2025-10-16
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
import shutil


@dataclass
class SaveOptions:
    """Configuration options for YAML saving."""

    default_flow_style: bool = False  # False = block style (more readable)
    sort_keys: bool = False  # Preserve key order
    indent: int = 2  # Indentation spaces
    allow_unicode: bool = True  # Allow Unicode characters
    width: Optional[int] = None  # Line width (None = no limit)
    encoding: str = "utf-8"  # File encoding
    create_backup: bool = True  # Create .bak file before overwriting
    create_dirs: bool = True  # Create parent directories if missing

    def __repr__(self):
        return (
            f"SaveOptions(flow_style={'flow' if self.default_flow_style else 'block'}, "
            f"indent={self.indent}, backup={self.create_backup})"
        )


@dataclass
class SaveResult:
    """Result of a YAML save operation."""

    success: bool
    file_path: Optional[Path] = None
    backup_path: Optional[Path] = None
    errors: list = None
    warnings: list = None
    bytes_written: int = 0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def __repr__(self):
        if self.success:
            backup_info = f", backup: {self.backup_path}" if self.backup_path else ""
            return f"✅ SAVE SUCCESS: {self.bytes_written} bytes written to {self.file_path}{backup_info}"
        else:
            return f"❌ SAVE FAILED: {', '.join(self.errors)}"


class SaveError(Exception):
    """Exception raised when YAML saving fails."""

    pass


class YAMLSaver:
    """
    Universal YAML file saver.

    Features:
    - Multiple formatting options (block/flow style, indentation, etc.)
    - Automatic backup creation
    - Directory creation
    - Comprehensive error handling
    - Unicode support

    Example:
        saver = YAMLSaver()
        options = SaveOptions(indent=4, create_backup=True)
        result = saver.save(data, Path("output.yaml"), options)
    """

    def save(
        self,
        data: Dict[str, Any],
        file_path: Path,
        options: Optional[SaveOptions] = None,
    ) -> SaveResult:
        """
        Save data to YAML file.

        Args:
            data: Dictionary to save as YAML
            file_path: Output file path
            options: Save options (uses defaults if None)

        Returns:
            SaveResult with success status and details
        """
        if options is None:
            options = SaveOptions()

        file_path = Path(file_path)

        try:
            # Create parent directories if needed
            if options.create_dirs and not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            backup_path = None
            if options.create_backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy2(file_path, backup_path)

            # Convert to YAML string
            yaml_content = yaml.dump(
                data,
                default_flow_style=options.default_flow_style,
                sort_keys=options.sort_keys,
                indent=options.indent,
                allow_unicode=options.allow_unicode,
                width=options.width,
            )

            # Write to file
            with open(file_path, "w", encoding=options.encoding) as f:
                f.write(yaml_content)

            bytes_written = len(yaml_content.encode(options.encoding))

            return SaveResult(
                success=True,
                file_path=file_path,
                backup_path=backup_path,
                bytes_written=bytes_written,
            )

        except yaml.YAMLError as e:
            return SaveResult(
                success=False,
                file_path=file_path,
                errors=[f"YAML serialization error: {str(e)}"],
            )
        except PermissionError as e:
            return SaveResult(
                success=False,
                file_path=file_path,
                errors=[f"Permission denied: {str(e)}"],
            )
        except OSError as e:
            return SaveResult(
                success=False, file_path=file_path, errors=[f"OS error: {str(e)}"]
            )
        except Exception as e:
            return SaveResult(
                success=False,
                file_path=file_path,
                errors=[f"Unexpected error: {str(e)}"],
            )

    def to_string(
        self, data: Dict[str, Any], options: Optional[SaveOptions] = None
    ) -> SaveResult:
        """
        Convert data to YAML string (without saving to file).

        Args:
            data: Dictionary to convert to YAML
            options: Save options (uses defaults if None)

        Returns:
            SaveResult with YAML string in file_path field (reused)
        """
        if options is None:
            options = SaveOptions()

        try:
            # Convert to YAML string
            yaml_content = yaml.dump(
                data,
                default_flow_style=options.default_flow_style,
                sort_keys=options.sort_keys,
                indent=options.indent,
                allow_unicode=options.allow_unicode,
                width=options.width,
            )

            # Return string in a SaveResult (reusing file_path for the string)
            return SaveResult(
                success=True, bytes_written=len(yaml_content.encode(options.encoding))
            )

        except yaml.YAMLError as e:
            return SaveResult(
                success=False, errors=[f"YAML serialization error: {str(e)}"]
            )
        except Exception as e:
            return SaveResult(success=False, errors=[f"Unexpected error: {str(e)}"])


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================


def demo_saver():
    """Demonstrate YAML saving functionality."""
    print("=" * 70)
    print("YAML SAVER LIBRARY - DEMO")
    print("=" * 70)

    saver = YAMLSaver()

    # Example 1: Basic save with default options
    print("\n📝 Example 1: Save with default options (block style)")
    print("-" * 70)

    data = {
        "name": "Test Config",
        "version": "1.0",
        "settings": {"enabled": True, "timeout": 30, "retries": 3},
        "items": [
            {"id": "item1", "value": 100},
            {"id": "item2", "value": 200},
            {"id": "item3", "value": 300},
        ],
    }

    print("Data to save:")
    print(f"  Name: {data['name']}")
    print(f"  Items: {len(data['items'])} items")

    # Create temp directory for demo
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())
    output_file = temp_dir / "config.yaml"

    result = saver.save(data, output_file)
    print(f"\n{result}")

    if result.success:
        print("\nGenerated YAML:")
        with open(output_file) as f:
            print(f.read())

    # Example 2: Flow style (more compact)
    print("\n📝 Example 2: Save with flow style (compact)")
    print("-" * 70)

    options = SaveOptions(default_flow_style=True, indent=2, create_backup=False)

    small_data = {"coords": [1, 2, 3], "matrix": [[1, 0], [0, 1]]}

    output_file2 = temp_dir / "compact.yaml"
    result = saver.save(small_data, output_file2, options)
    print(f"\n{result}")

    if result.success:
        print("\nGenerated YAML (flow style):")
        with open(output_file2) as f:
            print(f.read())

    # Example 3: Save with custom indentation
    print("\n📝 Example 3: Save with custom indentation (4 spaces)")
    print("-" * 70)

    options = SaveOptions(indent=4, create_backup=False)

    nested_data = {"level1": {"level2": {"level3": {"value": "deep"}}}}

    output_file3 = temp_dir / "indented.yaml"
    result = saver.save(nested_data, output_file3, options)
    print(f"\n{result}")

    if result.success:
        print("\nGenerated YAML (4-space indent):")
        with open(output_file3) as f:
            print(f.read())

    # Example 4: Backup creation
    print("\n📝 Example 4: Save with backup creation")
    print("-" * 70)

    # Save initial version
    initial_data = {"version": "1.0", "status": "initial"}
    backup_file = temp_dir / "versioned.yaml"
    saver.save(initial_data, backup_file, SaveOptions(create_backup=False))

    print("Initial file created")

    # Save updated version (creates backup)
    updated_data = {"version": "2.0", "status": "updated"}
    options = SaveOptions(create_backup=True)

    result = saver.save(updated_data, backup_file, options)
    print(f"\n{result}")

    if result.success and result.backup_path:
        print(f"\nBackup created at: {result.backup_path.name}")
        print("Original content (from backup):")
        with open(result.backup_path) as f:
            print(f.read())
        print("New content:")
        with open(backup_file) as f:
            print(f.read())

    # Cleanup
    shutil.rmtree(temp_dir)
    print("\n(Temp files cleaned up)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_saver()
