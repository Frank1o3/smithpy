"""
banner.py - SmithPy CLI banner renderer

Provides a colorful, Minecraft-themed ASCII banner with 3D effects
and project information displayed on startup.
"""

import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama (safe to call multiple times)
init(autoreset=True)

# --- CONFIGURATION ---

# Resolve the icon file path relative to the project root
# Go up from banner.py to project root, then into src/resources
ICON_FILE_PATH = Path(__file__).parent.parent / "resources" / "icon.txt"

# Fixed width for the ASCII art section (adjust if you widen the art)
ART_WIDTH = 78  # Updated for the wider banner you're using now
SEPARATOR = "|SPLIT|"

# --- COLOR PALETTE ---

ART_PRIMARY = Fore.GREEN + Style.BRIGHT      # Main bright green
ART_SHADOW = Fore.GREEN + Style.DIM          # Dim green for ▒ and ░ shadows

TAG_COLOR = Fore.CYAN + Style.BRIGHT         # Labels like "App >"
INFO_COLOR = Fore.YELLOW + Style.BRIGHT      # Values like "SmithPy"
SEPARATOR_COLOR = Fore.MAGENTA + Style.BRIGHT


def _color_3d_line(line_content: str) -> str:
    """Apply 3D color effect: bright primary + dim shadows for ▒ and ░."""
    colored = ART_PRIMARY + line_content
    colored = colored.replace("▒", ART_SHADOW + "▒" + ART_PRIMARY)
    colored = colored.replace("░", ART_SHADOW + "░" + ART_PRIMARY)
    return colored


def print_banner(file_path: str | Path = ICON_FILE_PATH) -> None:
    """
    Print the full SmithPy startup banner with colors and alignment.

    Args:
        file_path: Path to the icon.txt file. Defaults to the bundled one.
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Error: Banner file not found at '{path}'.")
        print(f"Current working directory: {Path.cwd()}")
        print(f"Banner.py location: {Path(__file__).parent}")
        return

    try:
        lines = path.read_text(encoding="utf-8").splitlines()

        # --- Top section: Art + Info (usually first 7-8 lines) ---
        for line in lines[:8]:  # Adjust slice if your banner grows
            line = line.rstrip("\n")

            if SEPARATOR in line:
                art_part, info_part_raw = line.split(SEPARATOR, 1)

                # Color the ASCII art
                colored_art = _color_3d_line(art_part).ljust(ART_WIDTH + 10)  # Extra padding for color codes

                # Color the info block
                if ">" in info_part_raw:
                    tag, value = info_part_raw.split(">", 1)
                    colored_info = (
                        TAG_COLOR + tag.strip() +
                        Fore.WHITE + " > " +
                        INFO_COLOR + value.strip()
                    )
                else:
                    colored_info = info_part_raw

                sys.stdout.write(colored_art + "    " + colored_info + "\n")
            else:
                sys.stdout.write(_color_3d_line(line.rstrip()) + "\n")

        # --- Separator line ---
        if len(lines) > 8:
            sep_line = lines[8].rstrip("\n")
            if sep_line.strip():
                sys.stdout.write(SEPARATOR_COLOR + sep_line + Style.RESET_ALL + "\n")

        # --- Bottom title line ---
        if len(lines) > 9:
            bottom_line = lines[9].rstrip("\n")
            sys.stdout.write(ART_PRIMARY + bottom_line + Style.RESET_ALL + "\n")

        # Optional extra separator
        if len(lines) > 10 and lines[10].strip():
            sys.stdout.write(SEPARATOR_COLOR + lines[10].rstrip("\n") + Style.RESET_ALL + "\n")

    except Exception as e:
        print(f"Unexpected error rendering banner: {e}")


# Optional: Allow direct execution for testing
if __name__ == "__main__":
    print_banner()