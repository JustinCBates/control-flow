"""
YAML Loader

Universal YAML file loading with error handling and validation.
Supports both safe_load and full_load modes.

Author: Control Flow Engine Libraries
Date: 2025-10-16
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path
import yaml


@dataclass
class LoadResult:
    """Result of a YAML load operation."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: list = None
    warnings: list = None
    file_path: Optional[Path] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def __repr__(self):
        if self.success:
            return f"✅ LOAD SUCCESS: Loaded {len(self.data or {})} top-level keys from {self.file_path}"
        else:
            return f"❌ LOAD FAILED: {', '.join(self.errors)}"


class LoadError(Exception):
    """Exception raised when YAML loading fails."""

    pass


class YAMLLoader:
    """
    Universal YAML file loader.

    Features:
    - Safe loading (default) or full loading
    - Comprehensive error handling
    - File existence validation
    - Encoding support

    Example:
        loader = YAMLLoader()
        result = loader.load(Path("config.yaml"))
        if result.success:
            data = result.data
    """

    def load(
        self, file_path: Path, safe: bool = True, encoding: str = "utf-8"
    ) -> LoadResult:
        """
        Load YAML from file.

        Args:
            file_path: Path to YAML file
            safe: If True, use yaml.safe_load (recommended)
            encoding: File encoding

        Returns:
            LoadResult with data or errors
        """
        file_path = Path(file_path)

        try:
            # Validate file exists
            if not file_path.exists():
                return LoadResult(
                    success=False,
                    errors=[f"File not found: {file_path}"],
                    file_path=file_path,
                )

            # Read file
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            # Parse YAML
            if safe:
                data = yaml.safe_load(content)
            else:
                data = yaml.load(content, Loader=yaml.FullLoader)

            # Handle empty files
            if data is None:
                return LoadResult(
                    success=True,
                    data={},
                    warnings=["File is empty or contains only comments"],
                    file_path=file_path,
                )

            return LoadResult(success=True, data=data, file_path=file_path)

        except yaml.YAMLError as e:
            return LoadResult(
                success=False,
                errors=[f"YAML parsing error: {str(e)}"],
                file_path=file_path,
            )
        except UnicodeDecodeError as e:
            return LoadResult(
                success=False,
                errors=[f"Encoding error: {str(e)}. Try different encoding."],
                file_path=file_path,
            )
        except Exception as e:
            return LoadResult(
                success=False,
                errors=[f"Unexpected error: {str(e)}"],
                file_path=file_path,
            )

    def load_from_string(self, yaml_string: str, safe: bool = True) -> LoadResult:
        """
        Load YAML from string.

        Args:
            yaml_string: YAML content as string
            safe: If True, use yaml.safe_load (recommended)

        Returns:
            LoadResult with data or errors
        """
        try:
            # Parse YAML
            if safe:
                data = yaml.safe_load(yaml_string)
            else:
                data = yaml.load(yaml_string, Loader=yaml.FullLoader)

            # Handle empty strings
            if data is None:
                return LoadResult(
                    success=True,
                    data={},
                    warnings=["String is empty or contains only comments"],
                )

            return LoadResult(success=True, data=data)

        except yaml.YAMLError as e:
            return LoadResult(success=False, errors=[f"YAML parsing error: {str(e)}"])
        except Exception as e:
            return LoadResult(success=False, errors=[f"Unexpected error: {str(e)}"])


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================


def demo_loader():
    """Demonstrate YAML loading functionality."""
    print("=" * 70)
    print("YAML LOADER LIBRARY - DEMO")
    print("=" * 70)

    loader = YAMLLoader()

    # Example 1: Load from string
    print("\n📝 Example 1: Load from YAML string")
    print("-" * 70)

    yaml_content = """
name: Test Config
version: 1.0
settings:
  enabled: true
  timeout: 30
items:
  - id: item1
    value: 100
  - id: item2
    value: 200
"""

    print("YAML content:")
    print(yaml_content)

    result = loader.load_from_string(yaml_content)
    print(f"\n{result}")

    if result.success:
        print("\nParsed data:")
        print(f"  Name: {result.data.get('name')}")
        print(f"  Version: {result.data.get('version')}")
        print(f"  Settings: {result.data.get('settings')}")
        print(f"  Items: {len(result.data.get('items', []))} items")

    # Example 2: Load invalid YAML
    print("\n\n📝 Example 2: Load invalid YAML (error handling)")
    print("-" * 70)

    invalid_yaml = """
name: Test
invalid:
  - item1
    - item2  # Invalid indentation
"""

    print("Invalid YAML content:")
    print(invalid_yaml)

    result = loader.load_from_string(invalid_yaml)
    print(f"\n{result}")

    if not result.success:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    # Example 3: Load empty YAML
    print("\n\n📝 Example 3: Load empty YAML (warning case)")
    print("-" * 70)

    empty_yaml = """
# Just a comment
# Nothing else
"""

    result = loader.load_from_string(empty_yaml)
    print(f"\n{result}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    # Example 4: Safe vs Full load
    print("\n\n📝 Example 4: Safe load (default - recommended)")
    print("-" * 70)

    yaml_with_tags = """
data: !!python/object:__main__.MyClass
  value: 123
"""

    print("YAML with Python tags (potentially dangerous):")
    print(yaml_with_tags)

    result_safe = loader.load_from_string(yaml_with_tags, safe=True)
    print(f"\nSafe load: {result_safe}")

    if not result_safe.success:
        print("  (This is good - safe_load protects against code injection)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_loader()
