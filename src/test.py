"""
__main__.py - Entry point for the SmithPy CLI
"""
from pprint import pprint
from requests import get

from styles.banner import print_banner
from styles.console import input_text, input_choice
from api import api

def main() -> None:
    print_banner()  # Show the beautiful banner on startup
    print()
    mods: list[str] = []
    name = input_text("Enter a modpack name", default="MyModPack", placeholder="e.g., SurvivalPlus")
    loader = input_choice(
        "Select mod loader",
        ["fabric", "forge", "quilt", "neoforge"],
        default="fabric"
    )
    version = input_text("What Minecraft version", default="1.21.10", placeholder="e.g., 1.21.10")
    while True:
        mod = input_text("Enter a mod name (or 'done' to finish)", default="sodium", placeholder="e.g., sodium")
        if mod.lower() == "done":
            break
        mods.append(mod)

    print(name)
    print(version)
    print(loader)
    pprint(mods)

    for mod_name in mods:
        temp_url = api.search(mod_name, game_versions=[version], loaders=[loader], project_type="mod")
        res = get(temp_url)
        if res.status_code == 200:
            json = res.json()
            pprint(json)

if __name__ == "__main__":
    main()
