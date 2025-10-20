"""
YAML Operations Library

Universal library for YAML file operations: load, save, validate.
Works with any YAML content without domain coupling.

Author: Control Flow Engine Libraries
Date: 2025-10-16
"""

from .loader import YAMLLoader, LoadResult
from .saver import YAMLSaver, SaveResult, SaveOptions
from .validator import YAMLValidator, ValidationResult as YAMLValidationResult

__all__ = [
    "YAMLLoader",
    "LoadResult",
    "YAMLSaver",
    "SaveResult",
    "SaveOptions",
    "YAMLValidator",
    "YAMLValidationResult",
]

__version__ = "1.0.0"
