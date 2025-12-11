"""
__main__.py - Entry point for the SmithPy CLI
"""

from styles.banner import print_banner
from styles.console import input_text


def main() -> None:
    print_banner()  # Show the beautiful banner on startup
    print()
    modpack_name = input_text("Enter a modpack name:", default="MyModPack")
    

if __name__ == "__main__":
    main()
