"""
console.py - Styled terminal output utilities for SmithPy

Provides:
- Colored print functions (success, error, info, warning, highlight)
- Styled input functions (text, confirm, choice, multiselect)
- Dynamic colored progress bars (rich)
- Simple spinner
- Consistent color theme matching banner.py
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Any, Generator, Optional, List

from colorama import Fore, Style, init
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.theme import Theme
from rich.prompt import Prompt, Confirm

# Initialize colorama (for basic colored print)
init(autoreset=True)

# Rich console with SmithPy theme
smithpy_theme = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "cyan",
    "highlight": "bright_magenta",
    "primary": "bright_green",
    "dim": "dim green",
    "prompt": "bold bright_cyan",
})

console = Console(theme=smithpy_theme)


# === Basic Colored Print Functions ===
def print_success(text: str, **kwargs: Any) -> None:
    console.print(f"[success]✓ {text}[/success]", **kwargs)


def print_error(text: str, **kwargs: Any) -> None:
    console.print(f"[error]✖ {text}[/error]", **kwargs)


def print_warning(text: str, **kwargs: Any) -> None:
    console.print(f"[warning]! {text}[/warning]", **kwargs)


def print_info(text: str, **kwargs: Any) -> None:
    console.print(f"[info]ℹ {text}[/info]", **kwargs)


def print_highlight(text: str, **kwargs: Any) -> None:
    console.print(f"[highlight]★ {text}[/highlight]", **kwargs)


def print_primary(text: str, **kwargs: Any) -> None:
    console.print(f"[primary]{text}[/primary]", **kwargs)


def print_dim(text: str, **kwargs: Any) -> None:
    console.print(f"[dim]{text}[/dim]", **kwargs)


# === Colorama-based simple prints (fallback or for raw control) ===
def cprint(text: str, color: str = Fore.GREEN + Style.BRIGHT, end: str = "\n") -> None:
    """Simple colored print using colorama directly."""
    sys.stdout.write(color + text + Style.RESET_ALL + end)


# === Styled Input Functions ===

def input_text(
    prompt: str,
    default: Optional[str] = None,
    placeholder: Optional[str] = None,
    password: bool = False,
) -> str:
    """
    Prompt for text input with styling.
    
    Args:
        prompt: The question/prompt to display
        default: Default value if user presses Enter
        placeholder: Placeholder text shown in brackets
        password: If True, hide input (for passwords)
    
    Returns:
        User's input string
    
    Example:
        name = input_text("Enter your name", default="Player")
        password = input_text("Enter password", password=True)
    """
    prompt_kwargs = {"console": console}
    
    if default is not None:
        prompt_kwargs["default"] = default
    
    if password:
        return Prompt.ask(
            f"[prompt]🔒 {prompt}[/prompt]",
            password=True,
            **prompt_kwargs
        )
    
    # Add placeholder hint if provided
    display_prompt = f"[prompt]✎ {prompt}[/prompt]"
    if placeholder and not default:
        display_prompt += f" [dim]({placeholder})[/dim]"
    
    return Prompt.ask(display_prompt, **prompt_kwargs)


def input_confirm(
    prompt: str,
    default: bool = True,
) -> bool:
    """
    Prompt for yes/no confirmation.
    
    Args:
        prompt: The question to ask
        default: Default choice if user presses Enter (True=yes, False=no)
    
    Returns:
        True if user confirms, False otherwise
    
    Example:
        if input_confirm("Download this mod?"):
            download_mod()
    """
    icon = "❓" if default else "⚠"
    return Confirm.ask(
        f"[prompt]{icon} {prompt}[/prompt]",
        default=default,
        console=console,
    )


def input_choice(
    prompt: str,
    choices: List[str],
    default: Optional[str] = None,
    show_numbers: bool = True,
) -> str:
    """
    Prompt user to select from a list of choices.
    
    Args:
        prompt: The question to ask
        choices: List of valid choices
        default: Default choice if user presses Enter
        show_numbers: If True, show numbered list before prompt
    
    Returns:
        Selected choice (one of the items from choices list)
    
    Example:
        loader = input_choice(
            "Select mod loader",
            ["fabric", "forge", "quilt"],
            default="fabric"
        )
    """
    if show_numbers and len(choices) > 1:
        console.print(f"[prompt]📋 {prompt}[/prompt]")
        for i, choice in enumerate(choices, 1):
            prefix = "→" if choice == default else " "
            style = "bold green" if choice == default else "dim"
            console.print(f"  [{style}]{prefix} {i}. {choice}[/{style}]")
        console.print()
    
    # Accept number or text input
    while True:
        display_prompt = f"[prompt]▸ Choice[/prompt]"
        if default:
            display_prompt += f" [dim](default: {default})[/dim]"
        
        response = Prompt.ask(
            display_prompt,
            choices=choices + [str(i) for i in range(1, len(choices) + 1)],
            default=default,
            console=console,
            show_choices=not show_numbers,
        )
        
        # Convert number to choice
        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        elif response in choices:
            return response


def input_multiselect(
    prompt: str,
    choices: List[str],
    defaults: Optional[List[str]] = None,
    min_select: int = 0,
    max_select: Optional[int] = None,
) -> List[str]:
    """
    Prompt user to select multiple items from a list.
    
    Args:
        prompt: The question to ask
        choices: List of available choices
        defaults: List of pre-selected choices
        min_select: Minimum number of selections required
        max_select: Maximum number of selections allowed
    
    Returns:
        List of selected choices
    
    Example:
        versions = input_multiselect(
            "Select Minecraft versions to support",
            ["1.20.1", "1.20.4", "1.21", "1.21.1"],
            defaults=["1.21.1"]
        )
    """
    defaults = defaults or []
    selected = set(defaults)
    
    console.print(f"[prompt]☑ {prompt}[/prompt]")
    console.print(f"[dim]Use space to toggle, enter to confirm[/dim]")
    console.print()
    
    for i, choice in enumerate(choices, 1):
        is_selected = choice in selected
        checkbox = "[✓]" if is_selected else "[ ]"
        style = "bold green" if is_selected else "white"
        console.print(f"  [{style}]{checkbox} {i}. {choice}[/{style}]")
    
    console.print()
    
    # Simple input: comma-separated numbers or choices
    while True:
        hint_parts = []
        if min_select > 0:
            hint_parts.append(f"min {min_select}")
        if max_select:
            hint_parts.append(f"max {max_select}")
        hint = f" [{', '.join(hint_parts)}]" if hint_parts else ""
        
        console.print(f"[prompt]▸ Enter selections{hint}[/prompt] [dim](e.g., 1,3,4 or done)[/dim]")
        response = input().strip().lower()
        
        if response in ("done", ""):
            if len(selected) >= min_select:
                if max_select is None or len(selected) <= max_select:
                    return list(selected)
                else:
                    print_error(f"Maximum {max_select} selections allowed")
            else:
                print_error(f"Minimum {min_select} selections required")
            continue
        
        # Parse input
        try:
            selected.clear()
            for part in response.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(choices):
                        selected.add(choices[idx])
                elif part in choices:
                    selected.add(part)
            
            # Validate selection count
            if len(selected) < min_select:
                print_error(f"Please select at least {min_select} items")
                selected = set(defaults)
                continue
            if max_select and len(selected) > max_select:
                print_error(f"Please select at most {max_select} items")
                selected = set(defaults)
                continue
            
            return list(selected)
        except Exception as e:
            print_error(f"Invalid input: {e}")
            selected = set(defaults)


def input_number(
    prompt: str,
    default: Optional[float] = None,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    integer: bool = False,
) -> float | int:
    """
    Prompt for numeric input with validation.
    
    Args:
        prompt: The question to ask
        default: Default value if user presses Enter
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        integer: If True, only accept integers
    
    Returns:
        The numeric value entered by user
    
    Example:
        count = input_number("How many mods to download?", default=10, min_val=1, integer=True)
    """
    constraints = []
    if min_val is not None:
        constraints.append(f"min: {min_val}")
    if max_val is not None:
        constraints.append(f"max: {max_val}")
    
    constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
    
    while True:
        display_prompt = f"[prompt]🔢 {prompt}{constraint_str}[/prompt]"
        
        response = Prompt.ask(
            display_prompt,
            default=str(default) if default is not None else ...,
            console=console,
        )
        
        try:
            if integer:
                value = int(response)
            else:
                value = float(response)
            
            if min_val is not None and value < min_val:
                print_error(f"Value must be at least {min_val}")
                continue
            if max_val is not None and value > max_val:
                print_error(f"Value must be at most {max_val}")
                continue
            
            return value
        except ValueError:
            print_error("Please enter a valid number")


# === Progress Bars ===
@contextmanager
def progress_bar(total: Optional[int] = None, description: str = "Working") -> Generator[Progress, None, None]:
    """
    Context manager for a styled progress bar.

    Usage:
        with progress_bar(100, "Downloading mods") as progress:
            task = progress.add_task("Downloading...", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    progress = Progress(
        SpinnerColumn(style="green"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=None, complete_style="green", finished_style="bright_green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        yield progress


# === Simple Spinner ===
@contextmanager
def spinner(text: str = "Processing...") -> Generator[None, None, None]:
    """Simple animated spinner."""
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"[bold cyan]{text}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("")
        yield


# === Dynamic Colored Text (inline) ===
class Colors:
    """Namespace for raw color codes (useful for custom formatting)"""
    PRIMARY = Fore.GREEN + Style.BRIGHT
    DIM = Fore.GREEN + Style.DIM
    CYAN = Fore.CYAN + Style.BRIGHT
    YELLOW = Fore.YELLOW + Style.BRIGHT
    MAGENTA = Fore.MAGENTA + Style.BRIGHT
    RED = Fore.RED + Style.BRIGHT
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL


# Example usage (remove or keep for testing)
if __name__ == "__main__":
    print_primary("SmithPy Console Utilities Loaded!")
    print_success("Project initialized successfully")
    print_info("Searching for mods on Modrinth...")
    print_warning("Some files may be outdated")
    print_error("Failed to download sodium.jar")
    
    print()
    print_highlight("Testing Input Functions")
    print()
    
    # Test text input
    name = input_text("Enter project name", default="MyModpack", placeholder="e.g., SurvivalPlus")
    print_success(f"Project name set to: {name}")
    
    # Test confirm
    if input_confirm("Would you like to include OptiFine alternatives?"):
        print_info("Will include Sodium, Iris, and other performance mods")
    
    # Test choice
    loader = input_choice(
        "Select mod loader",
        ["fabric", "forge", "quilt", "neoforge"],
        default="fabric"
    )
    print_info(f"Selected loader: {loader}")
    
    # Test number input
    count = input_number("How many mods to download?", default=5, min_val=1, max_val=50, integer=True)
    print_info(f"Will download {count} mods")
    
    # Test multiselect
    versions = input_multiselect(
        "Select Minecraft versions to support",
        ["1.19.4", "1.20.1", "1.20.4", "1.21", "1.21.1"],
        defaults=["1.21.1"],
        min_select=1,
        max_select=3
    )
    print_info(f"Supporting versions: {', '.join(versions)}")
    
    print()
    print_highlight("Starting download sequence...")

    # Demo progress bar
    import time
    with progress_bar(100, description="Downloading mods") as progress:
        task = progress.add_task("Fetching files...", total=100)
        for _ in range(100):
            time.sleep(0.02)
            progress.update(task, advance=1)

    # Demo spinner
    with spinner("Validating modpack manifest"):
        time.sleep(2)

    print_success("All done! Your modpack is ready. ⛏")