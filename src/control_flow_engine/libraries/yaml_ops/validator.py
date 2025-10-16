"""
YAML Validator

Universal YAML validation: structure checks, required fields, type validation.
Domain-agnostic validation framework.

Author: Control Flow Engine Libraries
Date: 2025-10-16
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


class ValidationType(Enum):
    """Types of validation checks."""
    REQUIRED_FIELD = "required_field"
    TYPE_CHECK = "type_check"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """A single validation rule."""
    name: str
    check_type: ValidationType
    field_path: str  # Dot-separated path, e.g., "settings.timeout"
    expected_type: Optional[type] = None  # For type checks
    custom_validator: Optional[Callable] = None  # For custom validation
    error_message: Optional[str] = None
    
    def __repr__(self):
        return f"Rule({self.name}: {self.field_path})"


@dataclass
class ValidationResult:
    """Result of YAML validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_performed: int = 0
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
    
    def __repr__(self):
        symbol = "✅" if self.valid else "❌"
        return f"{symbol} Validation: {'VALID' if self.valid else 'INVALID'} ({len(self.errors)} errors, {len(self.warnings)} warnings)"


class YAMLValidator:
    """
    Universal YAML validator.
    
    Features:
    - Required field validation
    - Type checking
    - Custom validation functions
    - Nested field access via dot notation
    
    Example:
        validator = YAMLValidator()
        validator.add_rule(ValidationRule(
            name="name_required",
            check_type=ValidationType.REQUIRED_FIELD,
            field_path="name"
        ))
        result = validator.validate(data)
    """
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule."""
        self.rules.append(rule)
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against all rules.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)
        
        for rule in self.rules:
            result.checks_performed += 1
            
            # Get field value using dot notation
            value, exists = self._get_nested_field(data, rule.field_path)
            
            if rule.check_type == ValidationType.REQUIRED_FIELD:
                if not exists:
                    msg = rule.error_message or f"Required field missing: '{rule.field_path}'"
                    result.add_error(msg)
            
            elif rule.check_type == ValidationType.TYPE_CHECK:
                if exists:
                    if not isinstance(value, rule.expected_type):
                        msg = rule.error_message or (
                            f"Field '{rule.field_path}' has wrong type: "
                            f"expected {rule.expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                        result.add_error(msg)
            
            elif rule.check_type == ValidationType.CUSTOM:
                if rule.custom_validator:
                    try:
                        is_valid, error_msg = rule.custom_validator(value, exists)
                        if not is_valid:
                            msg = rule.error_message or error_msg
                            result.add_error(msg)
                    except Exception as e:
                        result.add_error(f"Custom validator '{rule.name}' failed: {e}")
        
        return result
    
    def _get_nested_field(self, data: Dict[str, Any], path: str) -> tuple[Any, bool]:
        """
        Get nested field value using dot notation.
        
        Args:
            data: Dictionary to search
            path: Dot-separated field path (e.g., "settings.timeout")
            
        Returns:
            Tuple of (value, exists)
        """
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None, False
        
        return current, True


# ============================================================================
# DEMO: Standalone demonstration of the library
# ============================================================================

def demo_validator():
    """Demonstrate YAML validation functionality."""
    print("=" * 70)
    print("YAML VALIDATOR LIBRARY - DEMO")
    print("=" * 70)
    
    # Example 1: Required field validation
    print("\n📝 Example 1: Required field validation")
    print("-" * 70)
    
    validator = YAMLValidator()
    validator.add_rule(ValidationRule(
        name="name_required",
        check_type=ValidationType.REQUIRED_FIELD,
        field_path="name"
    ))
    validator.add_rule(ValidationRule(
        name="version_required",
        check_type=ValidationType.REQUIRED_FIELD,
        field_path="version"
    ))
    
    # Valid data
    valid_data = {"name": "MyApp", "version": "1.0"}
    result = validator.validate(valid_data)
    print(f"Valid data: {valid_data}")
    print(f"Result: {result}")
    
    # Invalid data (missing version)
    invalid_data = {"name": "MyApp"}
    result = validator.validate(invalid_data)
    print(f"\nInvalid data: {invalid_data}")
    print(f"Result: {result}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    # Example 2: Type checking
    print("\n\n📝 Example 2: Type checking")
    print("-" * 70)
    
    validator2 = YAMLValidator()
    validator2.add_rule(ValidationRule(
        name="timeout_is_int",
        check_type=ValidationType.TYPE_CHECK,
        field_path="settings.timeout",
        expected_type=int
    ))
    validator2.add_rule(ValidationRule(
        name="enabled_is_bool",
        check_type=ValidationType.TYPE_CHECK,
        field_path="settings.enabled",
        expected_type=bool
    ))
    
    # Valid data
    valid_data = {
        "settings": {
            "timeout": 30,
            "enabled": True
        }
    }
    result = validator2.validate(valid_data)
    print(f"Valid data: {valid_data}")
    print(f"Result: {result}")
    
    # Invalid data (wrong types)
    invalid_data = {
        "settings": {
            "timeout": "30",  # String instead of int
            "enabled": True
        }
    }
    result = validator2.validate(invalid_data)
    print(f"\nInvalid data: {invalid_data}")
    print(f"Result: {result}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    # Example 3: Custom validation
    print("\n\n📝 Example 3: Custom validation")
    print("-" * 70)
    
    def validate_port(value, exists):
        """Custom validator: check port is in valid range."""
        if not exists:
            return False, "Port field missing"
        if not isinstance(value, int):
            return False, "Port must be an integer"
        if value < 1 or value > 65535:
            return False, f"Port {value} out of range (1-65535)"
        return True, None
    
    validator3 = YAMLValidator()
    validator3.add_rule(ValidationRule(
        name="port_valid",
        check_type=ValidationType.CUSTOM,
        field_path="server.port",
        custom_validator=validate_port
    ))
    
    # Valid data
    valid_data = {"server": {"port": 8080}}
    result = validator3.validate(valid_data)
    print(f"Valid data: {valid_data}")
    print(f"Result: {result}")
    
    # Invalid data (port out of range)
    invalid_data = {"server": {"port": 99999}}
    result = validator3.validate(invalid_data)
    print(f"\nInvalid data: {invalid_data}")
    print(f"Result: {result}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    # Example 4: Nested field validation
    print("\n\n📝 Example 4: Nested field validation")
    print("-" * 70)
    
    validator4 = YAMLValidator()
    validator4.add_rule(ValidationRule(
        name="database_host_required",
        check_type=ValidationType.REQUIRED_FIELD,
        field_path="config.database.host"
    ))
    validator4.add_rule(ValidationRule(
        name="database_port_type",
        check_type=ValidationType.TYPE_CHECK,
        field_path="config.database.port",
        expected_type=int
    ))
    
    # Valid nested data
    valid_data = {
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }
    }
    result = validator4.validate(valid_data)
    print(f"Valid data with nesting:")
    print(f"  config.database.host = {valid_data['config']['database']['host']}")
    print(f"  config.database.port = {valid_data['config']['database']['port']}")
    print(f"Result: {result}")
    
    # Invalid nested data
    invalid_data = {
        "config": {
            "database": {
                # Missing 'host'
                "port": "5432"  # Wrong type
            }
        }
    }
    result = validator4.validate(invalid_data)
    print(f"\nInvalid nested data: Missing host, wrong port type")
    print(f"Result: {result}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_validator()
