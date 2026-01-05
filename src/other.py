import asyncio
import aiohttp
import json
import os
import sys
import platform
import subprocess
import shutil  # Added for terminal size detection
from pathlib import Path
from dataclasses import dataclass, field
from packaging.version import Version
from tqdm.asyncio import tqdm
from colorama import Fore, Style, init
import pyfiglet

init(autoreset=True)

# ================= CONFIG =================

MODRINTH_API = "https://api.modrinth.com/v2"
DOWNLOAD_DIR = Path("mods")
DOWNLOAD_DIR.mkdir(exist_ok=True)

DEFAULT_FABRIC_MC = "1.21.10"
DEFAULT_FORGE_MC = "1.12.2"

FABRIC_DEFAULT = {
    "FerriteCore",
    "Entity Culling",
    "More Culling",
    "Dynamic FPS",
    "Krypton",
    "Cloth Config API",
    "Leafs Be Gone",
    "ModernFix-mVUS",
    "BadOptimizations",
    "Remove Reloading Screen",
    "Debugify",
    "Cull Leaves",
    "Chunky",
    "Let Me Despawn",
    "NoisiumForked",
}

FORGE_1122_DEFAULT = {
    "FoamFix",
    "AI Improvements",
    "Surge",
    "VanillaFix",
    "Universal Tweaks",
    "Particle Culling",
    "Alfheim Lighting Engine",
    "Raw Input",
}

# ================= UI HELPERS =================


def get_term_width():
    """Get terminal width, defaulting to 80 if undetectable."""
    return shutil.get_terminal_size((80, 20)).columns


def print_banner():
    width = get_term_width()

    # Generate ASCII art
    ascii_art = pyfiglet.figlet_format("ModFetch", font="slant")

    # Draw Top Line
    print(f"\n{Fore.CYAN}{'═' * width}")

    # Center and print ASCII art lines
    for line in ascii_art.split("\n"):
        if line.strip():
            # Center the art based on terminal width
            print(f"{Fore.GREEN}{line.center(width)}")

    print(f"{Fore.CYAN}{'═' * width}")

    # Dynamic Subtext
    line1 = "Automated Minecraft Mod Downloader from Modrinth"
    line2 = "Smart GPU Detection • Dependency Resolution"

    # Calculate inner width (width - 2 for the borders '║')
    inner_width = width - 2

    print(f"{Fore.CYAN}║{Fore.MAGENTA}{line1.center(inner_width)}{Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE}{line2.center(inner_width)}{Fore.CYAN}║")
    print(f"{Fore.CYAN}{'═' * width}{Style.RESET_ALL}\n")


def print_section(title):
    width = get_term_width()
    print(f"\n{Fore.CYAN}{'═' * width}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}  {title}")
    print(f"{Fore.CYAN}{'═' * width}{Style.RESET_ALL}\n")


def print_info(icon, message, color=Fore.WHITE):
    print(f"{color}{icon} {message} {Style.RESET_ALL}")


def print_success(message):
    print_info("✓", message, Fore.GREEN)


def print_error(message):
    print_info("✗", message, Fore.RED)


def print_warning(message):
    print_info("⚠", message, Fore.YELLOW)


def print_progress(message):
    print_info("→", message, Fore.CYAN)


def get_input(prompt, default=""):
    if default:
        display = f"{Fore.WHITE}{prompt} {Fore.CYAN}[{Fore.YELLOW}{default}{Fore.CYAN}]{Fore.WHITE}: {Style.RESET_ALL}"
    else:
        display = f"{Fore.WHITE}{prompt}{Fore.WHITE}: {Style.RESET_ALL}"

    result = input(display).strip()
    return result if result else default


# ================= PLATFORM DETECTION =================


def is_android():
    return (
        "ANDROID_ROOT" in os.environ
        or "ANDROID_DATA" in os.environ
        or platform.system().lower() == "android"
    )


def get_gpu_renderer():
    system = platform.system()
    try:
        if is_android():
            gpu = (
                subprocess.check_output("getprop ro.hardware.egl", shell=True)
                .decode()
                .strip()
            )
            if not gpu:
                out = subprocess.check_output(
                    "dumpsys SurfaceFlinger | grep GLES", shell=True
                ).decode()
                gpu = out.split(":")[-1].strip()
            return gpu.lower()

        elif system == "Windows":
            out = subprocess.check_output(
                "wmic path win32_VideoController get name", shell=True
            ).decode()
            return out.split("\n")[1].strip().lower()

        elif system == "Linux":
            out = subprocess.check_output("lspci | grep -i vga", shell=True).decode()
            return out.split(":")[-1].strip().lower()

    except Exception:
        return ""
    return ""


def is_snapdragon_gpu():
    gpu = get_gpu_renderer()
    return any(x in gpu for x in ("adreno", "snapdragon", "qualcomm"))


IS_MOBILE = is_android()
IS_SNAPDRAGON = is_snapdragon_gpu()
GPU_NAME = get_gpu_renderer()

# ================= DATA MODELS =================


@dataclass
class ModFile:
    url: str
    filename: str
    dependencies: list[str] = field(default_factory=list)
    channel: str = "release"


# ================= HTTP HELPERS =================


async def get_json(session, url, params=None):
    async with session.get(url, params=params) as r:
        r.raise_for_status()
        return await r.json()


# ================= SEARCH RESOLUTION =================


async def search_project(session, name, mc_version, loader):
    data = await get_json(
        session,
        f"{MODRINTH_API}/search",
        params={
            "query": name,
            "limit": 20,
            "facets": json.dumps([["project_type:mod"], [f"categories:{loader}"]]),
        },
    )

    best = None
    for hit in data.get("hits", []):
        if mc_version not in hit.get("versions", []):
            continue
        if loader not in hit.get("categories", []):
            continue
        if best is None or hit["downloads"] > best["downloads"]:
            best = hit

    return best


# ================= VERSION SELECTION =================


async def fetch_best_version(session, project_id, mc_version, loader):
    versions = await get_json(session, f"{MODRINTH_API}/project/{project_id}/version")
    for v in versions:
        if mc_version in v["game_versions"] and loader in v["loaders"]:
            deps = [
                d["project_id"]
                for d in v.get("dependencies", [])
                if d["dependency_type"] in ("required", "optional")
            ]
            return ModFile(
                url=v["files"][0]["url"],
                filename=v["files"][0]["filename"],
                dependencies=deps,
                channel=v["version_type"],
            )
    return None


async def get_project_name(session, project_id):
    data = await get_json(session, f"{MODRINTH_API}/project/{project_id}")
    return data["title"]


# ================= POLICIES =================


def expand_policies(requested):
    out = set(requested)
    conflicts = {
        "Sodium",
        "GPUTape",
        "Iris",
        "Sodium Extra",
        "Reese's Sodium Options",
        "ImmediatelyFast",
        "GPUBooster",
    }

    if IS_SNAPDRAGON:
        print_section("GPU OPTIMIZATION DETECTED")
        print_info("🎮", f"Graphics Card: {Fore.MAGENTA}{GPU_NAME}", Fore.CYAN)
        print()
        print(f"{Fore.YELLOW}  Select Rendering Path:{Style.RESET_ALL}")
        print(
            f"  {Fore.GREEN}[1]{Fore.WHITE} Vulkan {Fore.CYAN}(Best FPS for Snapdragon)"
        )
        print(
            f"  {Fore.MAGENTA}[2]{Fore.WHITE} OpenGL {Fore.CYAN}(Sodium + Shaders Support)"
        )
        print()

        choice = get_input("Your choice", "1")

        if choice == "1":
            out.add("VulkanMod")
            out.add("VulkanMod Extra")
            out -= conflicts
            print()
            print_success("Vulkan mode selected - Sodium conflicts removed")
        else:
            out.add("Sodium")
            if "VulkanMod" in out:
                out.remove("VulkanMod")
            print()
            print_success("OpenGL mode selected - Sodium optimizations enabled")

    if "Sodium" in out:
        out.update(conflicts)
        if IS_MOBILE:
            out.add("Podium")
            print_info("📱", "Mobile platform detected - Adding Podium", Fore.CYAN)

    return out


# ================= DOWNLOAD =================


async def download_file(session, mod_file, name):
    path = DOWNLOAD_DIR / mod_file.filename
    if path.exists():
        print_warning(f"Skipped (exists): {name}")
        return

    async with session.get(mod_file.url) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))

        with open(path, "wb") as f:
            with tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc=f"{Fore.CYAN}↓ {name[:40]}{Style.RESET_ALL}",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]",
                colour="cyan",
            ) as bar:
                async for chunk in r.content.iter_chunked(8192):
                    f.write(chunk)
                    bar.update(len(chunk))

    print_success(f"Downloaded: {name}")


# ================= MAIN =================


async def main():
    print_banner()

    print_section("CONFIGURATION")

    loader = get_input("Mod Loader", "fabric")
    mc_version = get_input(
        "Minecraft Version",
        DEFAULT_FABRIC_MC if loader == "fabric" else DEFAULT_FORGE_MC,
    )

    print_section("MOD SELECTION")

    print(f"{Fore.WHITE}Enter mod names one per line")
    print(
        f"{Fore.CYAN}  • Press {Fore.YELLOW}Enter{Fore.CYAN} on empty line to use default mod set"
    )
    print(
        f"{Fore.CYAN}  • Type {Fore.YELLOW}'x'{Fore.CYAN} when done entering custom mods{Style.RESET_ALL}\n"
    )

    mods = []
    mod_count = 1
    while True:
        m = input(f"{Fore.GREEN}[{mod_count}]{Fore.WHITE} > {Style.RESET_ALL}").strip()
        if m.lower() == "x":
            break
        if not m:
            mods = (
                list(FABRIC_DEFAULT) if loader == "fabric" else list(FORGE_1122_DEFAULT)
            )
            print()
            print_success(f"Using default {loader} mod set ({len(mods)} mods)")
            break
        mods.append(m)
        mod_count += 1

    if Version(mc_version) > Version("1.20.1"):
        mods = expand_policies(mods)

    print_section("RESOLVING DEPENDENCIES")

    async with aiohttp.ClientSession() as session:
        to_download = {}
        queue = []

        for name in mods:
            print_progress(f"Searching: {name}")
            project = await search_project(session, name, mc_version, loader)
            if not project:
                print_error(f"Not found: {name}")
                continue

            mod = await fetch_best_version(
                session, project["project_id"], mc_version, loader
            )
            if not mod:
                print_error(f"No compatible version: {name}")
                continue

            to_download[project["project_id"]] = mod
            queue.extend(mod.dependencies)
            print_success(f"Resolved: {name}")

        print()
        if queue:
            print_info("🔗", f"Processing {len(queue)} dependencies...", Fore.MAGENTA)
            print()

        while queue:
            dep_id = queue.pop()
            if dep_id in to_download:
                continue
            dep_mod = await fetch_best_version(session, dep_id, mc_version, loader)
            if dep_mod:
                name = await get_project_name(session, dep_id)
                print_info("  +", f"Dependency: {name}", Fore.MAGENTA)
                to_download[dep_id] = dep_mod
                queue.extend(dep_mod.dependencies)

        print_section("DOWNLOADING MODS")
        print_info(
            "📦", f"Total mods to download: {Fore.YELLOW}{len(to_download)}", Fore.CYAN
        )
        print_info(
            "📁",
            f"Download directory: {Fore.YELLOW}{DOWNLOAD_DIR.absolute()}",
            Fore.CYAN,
        )
        print()

        for pid, mod_file in to_download.items():
            name = await get_project_name(session, pid)
            await download_file(session, mod_file, name)

    print_section("COMPLETE")
    print_success(f"Successfully processed {len(to_download)} mods!")
    print_info(
        "🎮",
        f"Your mods are ready in: {Fore.YELLOW}{DOWNLOAD_DIR.absolute()}",
        Fore.GREEN,
    )
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠ Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}✗ Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)
