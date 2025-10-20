"""
Interactive UI Library - Terminal Compatibility Layer

This library provides a universal terminal UI abstraction that works
across different terminal environments, including VS Code integrated terminal
where arrow keys don't work with questionary.

Key Features:
- Automatic terminal capability detection
- Fallback to numbered menus when arrow keys unavailable
- Questionary wrapper with compatibility layer
- Custom styling support
- Consistent API across terminal types

This solves the "arrow keys don't work in VS Code terminal" bug.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class MenuChoice:
    """Represents a menu choice."""

    name: str
    value: Any
    disabled: bool = False
    description: Optional[str] = None


class TerminalCapabilities:
    """
    Detects terminal capabilities and determines best UI mode.

    Checks:
    - Terminal type (TERM environment variable)
    - TTY availability
    - VS Code integrated terminal detection
    - Questionary availability
    """

    def __init__(self):
        self.term_type = os.environ.get("TERM", "")
        self.term_program = os.environ.get("TERM_PROGRAM", "")
        self.vscode_injection = os.environ.get("VSCODE_INJECTION", "")
        self.is_tty = sys.stdin.isatty() and sys.stdout.isatty()

        # Check if questionary is available
        try:
            import questionary

            self.has_questionary = True
        except ImportError:
            self.has_questionary = False

        # Detect capabilities
        self._detect_capabilities()

    def _detect_capabilities(self):
        """Detect what the terminal can do."""
        # VS Code integrated terminal detection
        self.is_vscode = (
            "vscode" in self.term_program.lower()
            or self.vscode_injection != ""
            or "vscode" in os.environ.get("TERM_PROGRAM_VERSION", "").lower()
        )

        # Check for limited terminals
        limited_terms = ["dumb", "unknown", "linux"]
        self.is_limited = (
            self.term_type in limited_terms
            or not self.is_tty
            or self.is_vscode  # VS Code terminal has arrow key issues with questionary
        )

        # Arrow key support
        self.supports_arrow_keys = (
            self.has_questionary and not self.is_limited and self.is_tty
        )

    def should_use_questionary(self) -> bool:
        """Determine if questionary should be used."""
        return self.supports_arrow_keys and self.has_questionary

    def get_ui_mode(self) -> str:
        """
        Get recommended UI mode.

        Returns:
            'questionary' - Use questionary with arrow keys
            'numbered' - Use numbered text menu
            'basic' - Use basic input/output
        """
        if self.should_use_questionary():
            return "questionary"
        elif self.is_tty:
            return "numbered"
        else:
            return "basic"

    def __repr__(self):
        return (
            f"TerminalCapabilities("
            f"mode={self.get_ui_mode()}, "
            f"term={self.term_type}, "
            f"vscode={self.is_vscode}, "
            f"tty={self.is_tty})"
        )


class UniversalMenu:
    """
    Universal menu system that adapts to terminal capabilities.

    Automatically uses questionary when available, falls back to
    numbered menus in limited terminals (like VS Code integrated terminal).
    """

    def __init__(self, auto_detect: bool = True, force_mode: Optional[str] = None):
        """
        Initialize universal menu.

        Args:
            auto_detect: Automatically detect terminal capabilities
            force_mode: Force specific mode ('questionary', 'numbered', 'basic')
        """
        self.capabilities = TerminalCapabilities() if auto_detect else None
        self.force_mode = force_mode

        # Determine UI mode
        if force_mode:
            self.ui_mode = force_mode
        elif self.capabilities:
            self.ui_mode = self.capabilities.get_ui_mode()
        else:
            self.ui_mode = "numbered"

        # Try to import questionary if needed
        self.questionary = None
        if self.ui_mode == "questionary":
            try:
                import questionary

                self.questionary = questionary
            except ImportError:
                print("⚠️  Questionary not available, falling back to numbered menu")
                self.ui_mode = "numbered"

    def select(
        self, message: str, choices: List[Dict[str, Any]], style: Optional[Any] = None
    ) -> Any:
        """
        Display a selection menu.

        Args:
            message: Question/prompt to display
            choices: List of choice dicts with 'name' and 'value' keys
            style: Optional questionary Style (ignored in numbered mode)

        Returns:
            The selected value

        Example:
            >>> menu = UniversalMenu()
            >>> result = menu.select(
            ...     "Choose option:",
            ...     [{'name': 'Option A', 'value': 'a'},
            ...      {'name': 'Option B', 'value': 'b'}]
            ... )
        """
        if self.ui_mode == "questionary" and self.questionary:
            return self._select_questionary(message, choices, style)
        else:
            return self._select_numbered(message, choices)

    def _select_questionary(
        self, message: str, choices: List[Dict[str, Any]], style: Optional[Any] = None
    ) -> Any:
        """Use questionary for selection."""
        result = self.questionary.select(message, choices=choices, style=style).ask()
        return result

    def _select_numbered(self, message: str, choices: List[Dict[str, Any]]) -> Any:
        """Use numbered menu for selection."""
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60)

        # Build choice map (number -> value)
        choice_map = {}
        valid_numbers = []

        for i, choice in enumerate(choices, 1):
            name = choice.get("name", str(choice.get("value", f"Option {i}")))
            value = choice.get("value")
            disabled = choice.get("disabled", False)

            if disabled:
                print(f"  {i}. {name} (disabled)")
            else:
                print(f"  {i}. {name}")
                choice_map[i] = value
                valid_numbers.append(i)

        print()

        # Get user input
        while True:
            try:
                user_input = input(f"Select option (1-{len(choices)}): ").strip()

                if not user_input:
                    print("⚠️  Please enter a number")
                    continue

                number = int(user_input)

                if number in choice_map:
                    return choice_map[number]
                else:
                    print(
                        f"⚠️  Invalid choice. Please enter a number from {min(valid_numbers)} to {max(valid_numbers)}"
                    )
            except ValueError:
                print("⚠️  Please enter a valid number")
            except (KeyboardInterrupt, EOFError):
                print("\n⚠️  Cancelled")
                return None

    def confirm(
        self, message: str, default: bool = False, style: Optional[Any] = None
    ) -> bool:
        """
        Ask for confirmation.

        Args:
            message: Question to display
            default: Default answer
            style: Optional questionary Style (ignored in numbered mode)

        Returns:
            True if confirmed, False otherwise
        """
        if self.ui_mode == "questionary" and self.questionary:
            return self._confirm_questionary(message, default, style)
        else:
            return self._confirm_numbered(message, default)

    def _confirm_questionary(
        self, message: str, default: bool = False, style: Optional[Any] = None
    ) -> bool:
        """Use questionary for confirmation."""
        result = self.questionary.confirm(message, default=default, style=style).ask()
        return result if result is not None else default

    def _confirm_numbered(self, message: str, default: bool = False) -> bool:
        """Use numbered confirmation."""
        default_str = "Y/n" if default else "y/N"

        while True:
            try:
                user_input = input(f"{message} ({default_str}): ").strip().lower()

                if not user_input:
                    return default

                if user_input in ["y", "yes"]:
                    return True
                elif user_input in ["n", "no"]:
                    return False
                else:
                    print("⚠️  Please enter 'y' or 'n'")
            except (KeyboardInterrupt, EOFError):
                print("\n⚠️  Cancelled")
                return False

    def text(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], bool]] = None,
        style: Optional[Any] = None,
    ) -> str:
        """
        Ask for text input.

        Args:
            message: Question to display
            default: Default value
            validate: Optional validation function
            style: Optional questionary Style (ignored in numbered mode)

        Returns:
            User's text input
        """
        if self.ui_mode == "questionary" and self.questionary:
            return self._text_questionary(message, default, validate, style)
        else:
            return self._text_numbered(message, default, validate)

    def _text_questionary(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], bool]] = None,
        style: Optional[Any] = None,
    ) -> str:
        """Use questionary for text input."""
        kwargs = {"style": style} if style else {}

        if validate:
            kwargs["validate"] = validate

        result = self.questionary.text(message, default=default, **kwargs).ask()

        return result if result is not None else default

    def _text_numbered(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], bool]] = None,
    ) -> str:
        """Use basic input for text."""
        while True:
            try:
                prompt = f"{message}"
                if default:
                    prompt += f" [{default}]"
                prompt += ": "

                user_input = input(prompt).strip()

                if not user_input and default:
                    return default

                # Validate if function provided
                if validate:
                    # Handle both callable and questionary validator
                    if callable(validate):
                        try:
                            if validate(user_input):
                                return user_input
                            else:
                                print("⚠️  Invalid input, please try again")
                        except Exception as e:
                            print(f"⚠️  Invalid input: {e}")
                    else:
                        return user_input
                else:
                    return user_input

            except (KeyboardInterrupt, EOFError):
                print("\n⚠️  Cancelled")
                return default

    def print_info(self):
        """Print terminal capability information."""
        if self.capabilities:
            print("\n" + "=" * 60)
            print("TERMINAL CAPABILITIES")
            print("=" * 60)
            print(f"UI Mode: {self.ui_mode}")
            print(f"Terminal Type: {self.capabilities.term_type}")
            print(f"Is TTY: {self.capabilities.is_tty}")
            print(f"VS Code: {self.capabilities.is_vscode}")
            print(f"Questionary Available: {self.capabilities.has_questionary}")
            print(f"Arrow Keys Supported: {self.capabilities.supports_arrow_keys}")
            print("=" * 60 + "\n")
