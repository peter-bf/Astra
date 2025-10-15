#!/usr/bin/env python3
"""
ASTRA builder: PyArmor (gen) + PyInstaller
- Recursively finds entry scripts under ./astra
- Obfuscates each entry with PyArmor `gen`
- Packages obfuscated entry with PyInstaller (onefile)
- Outputs to ./dist/builds/<script_name>
- PyInstaller work/spec to ./dist/_build/<script_name>
- Icons from ./dist/ressources; special-case icon for getWhitelist.py

Usage:
    python dist/make.py
"""

from pathlib import Path
import subprocess
import sys
import shutil

DIST = Path(__file__).resolve().parent
ROOT = DIST.parent
ASTRA = ROOT / "astra"

BUILDS = DIST / "builds"
BUILD_TMP = DIST / "_build"
OBF = DIST / "_obf"
RES = DIST / "ressources"
TRANSFORM = BUILDS / "pytransform"

DEFAULT_ICON = RES / "Astra_Icon.ico"
WHITELIST_ICON = RES / "Whitelist_Icon.ico"

PYARMOR = "pyarmor"
PYINSTALLER = "pyinstaller"

def clean(p: Path):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]):
    subprocess.run(cmd, check=True)

def build(entry: Path):
    name = entry.stem
    print(f"[>] Building {entry.relative_to(ROOT)}")

    dist = BUILDS / name
    work = BUILD_TMP / name / "work"
    spec = BUILD_TMP / name / "spec"
    obf = OBF / name

    clean(dist)
    clean(work)
    clean(spec)
    clean(obf)

    # Obfuscate
    try:
        run([PYARMOR, "gen", "--recursive", "--output", str(obf), str(entry)])
    except subprocess.CalledProcessError:
        print(f"[!] PyArmor failed for {name}")
        return 1

    obf_entry = obf / entry.name
    if not obf_entry.exists():
        matches = list(obf.rglob(entry.name))
        if matches:
            obf_entry = matches[0]
        else:
            print(f"[!] Obfuscated entry not found for {name}")
            return 1

    # Select icon
    icon = WHITELIST_ICON if name.lower() == "getwhitelist" and WHITELIST_ICON.exists() else DEFAULT_ICON if DEFAULT_ICON.exists() else None

    # Build executable
    cmd = [
        PYINSTALLER, "--onefile",
        "--distpath", str(dist),
        "--workpath", str(work),
        "--specpath", str(spec),
        "--noconsole",
    ]
    if icon:
        cmd += ["--icon", str(icon)]
    cmd.append(str(obf_entry))

    try:
        run(cmd)
        print(f"[>] Done: {name}")
        return 0
    except subprocess.CalledProcessError:
        print(f"[!] PyInstaller failed for {name}")
        return 1

def main():
    print("[>] ASTRA PyArmor Builder (simplified)")
    if not ASTRA.exists():
        print("[!] astra folder not found")
        sys.exit(1)

    BUILDS.mkdir(parents=True, exist_ok=True)
    BUILD_TMP.mkdir(parents=True, exist_ok=True)
    OBF.mkdir(parents=True, exist_ok=True)

    entries = sorted(ASTRA.rglob("*.py"))
    if not entries:
        print("[!] No .py files found under astra/")
        sys.exit(0)

    fails = 0
    for e in entries:
        fails += build(e)

    print("[>] Cleaning up build temp folder...")
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)
    if OBF.exists():
        shutil.rmtree(OBF)
    if TRANSFORM.exists():
        shutil.rmtree(TRANSFORM)

    print("[>] Finished. Output in dist/builds")
    if fails:
        print(f"[!] {fails} build(s) failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
