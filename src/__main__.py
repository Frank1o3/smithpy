"""
__main__.py - Entry point for the SmithPy CLI
"""

from styles.banner import print_banner
from styles.console import input_text, input_choice


def main() -> None:
    print_banner()  # Show the beautiful banner on startup
    print()
    mods: list[str] = []
    shaders: list[str] = []
    resource_packs: list[str] = []
    name = input_text("Enter a modpack name", default="MyModPack", placeholder="e.g., SurvivalPlus")
    loader = input_choice(
        "Select mod loader",
        ["fabric", "forge", "quilt", "neoforge"],
        default="fabric"
    )
    version = input_text("What Minecraft version: ")
    
    while True:
        mod = input_text("Enter a mod name (or 'done' to finish)", default="sodium", placeholder="e.g., sodium")
        if mod.lower() == "done":
            break
        mods.append(mod)

    while True:
        shader = input_text("Enter a shader name (or 'done' to finish)", default="iris", placeholder="e.g., iris")
        if shader.lower() == "done":
            break
        shaders.append(shader)

    while True:
        resource_pack = input_text("Enter a resource pack name (or 'done' to finish)", default="faithful", placeholder="e.g., faithful")
        if resource_pack.lower() == "done":
            break
        resource_packs.append(resource_pack)

    print(f"Modpack Name: {name}")
    print(f"Loader: {loader}")
    print(f"Version: {version}")
    print(f"Mods: {mods}")
    print(f"Shaders: {shaders}")
    print(f"Resource Packs: {resource_packs}")

if __name__ == "__main__":
    main()
