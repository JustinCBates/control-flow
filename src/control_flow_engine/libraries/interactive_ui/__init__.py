"""
Interactive UI Library - Terminal Compatibility and Menu Systems

This library provides universal terminal UI components that work across
different terminal environments, solving the "arrow keys don't work in
VS Code terminal" issue.

Components:
- UniversalMenu: Adaptive menu system (questionary or numbered fallback)
- TerminalCapabilities: Terminal capability detection
- MenuChoice: Menu choice representation

Features:
- Automatic terminal capability detection
- Falls back to numbered menus when arrow keys unavailable
- Works in VS Code integrated terminal
- Works in standard terminals with questionary
- Consistent API across terminal types
- Custom styling support (when available)

This solves the critical bug: "Flow-Editor: Arrow Keys Don't Work in VS Code Terminal"

Example Usage:
    ```python
    from control_flow_engine.libraries.interactive_ui import UniversalMenu

    # Create menu (auto-detects terminal capabilities)
    menu = UniversalMenu()

    # Print capability info (optional)
    menu.print_info()

    # Select from choices
    result = menu.select(
        "Choose an option:",
        choices=[
            {'name': 'Option A', 'value': 'a'},
            {'name': 'Option B', 'value': 'b'},
            {'name': 'Option C', 'value': 'c'}
        ]
    )

    # Confirm action
    confirmed = menu.confirm("Are you sure?", default=False)

    # Text input with validation
    name = menu.text(
        "Enter name:",
        validate=lambda x: len(x) > 0 or "Name required"
    )

    # The menu automatically uses:
    # - Questionary (arrow keys) in full terminals
    # - Numbered menu (text input) in VS Code and limited terminals
    ```

Terminal Detection:
    The library detects:
    - VS Code integrated terminal (TERM_PROGRAM, VSCODE_INJECTION)
    - Limited terminals (TERM=dumb, TERM=linux, etc.)
    - TTY availability
    - Questionary library availability

    And automatically chooses the best UI mode:
    - 'questionary': Full arrow-key navigation (standard terminals)
    - 'numbered': Numbered text menus (VS Code, limited terminals)
    - 'basic': Minimal input/output (non-TTY)

Force Specific Mode:
    ```python
    # Force numbered menu (testing, or if you prefer it)
    menu = UniversalMenu(force_mode='numbered')

    # Force questionary (if you know terminal supports it)
    menu = UniversalMenu(force_mode='questionary')
    ```

Migration from Direct Questionary:
    Old code:
    ```python
    import questionary
    result = questionary.select("Choose:", choices=[...]).ask()
    ```

    New code:
    ```python
    from control_flow_engine.libraries.interactive_ui import UniversalMenu
    menu = UniversalMenu()
    result = menu.select("Choose:", choices=[...])
    ```

    The API is nearly identical, but now it works everywhere!
"""

from .universal_menu import UniversalMenu, TerminalCapabilities, MenuChoice

__all__ = ["UniversalMenu", "TerminalCapabilities", "MenuChoice"]
