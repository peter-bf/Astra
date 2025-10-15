# 📦 Astra Distribution (dist)

This directory contains all build and packaging utilities for the Astra project.
It provides an automated, build pipeline that uses PyArmor for obfuscation
and PyInstaller for packaging executables.

---

## Contents

```
dist/
├── make.py               # Build script (PyArmor + PyInstaller)
├── ressources/           # Icons and other bundled assets
│   ├── Astra_Icon.ico
│   └── Whitelist_Icon.ico
├── builds/               # Output executables (created automatically)
├── _build/               # PyInstaller temporary files (auto-deleted)
├── _obf/                 # PyArmor obfuscation output (auto-deleted)
└── transform             # PyArmor transform folder (auto-deleted)
```

---

## Build Overview

The `make.py` script:
1. Recursively finds every `.py` file in the top-level `astra/` directory.
2. Obfuscates each file using PyArmor (`gen` command).
3. Packages each obfuscated script into a single executable using PyInstaller.
4. Cleans up all temporary folders (`_build`, `_obf`, and `transform`) after completion.

Each build is fully self-contained and placed in:

```
dist/builds/<script_name>/
```

---

## How to Build

From the project root (`AstraRepo/Astra`):

```bash
python dist/make.py
```

The builder automatically:
- Uses `Astra_Icon.ico` for all builds.
- Uses `Whitelist_Icon.ico` specifically for `getWhitelist.py`.
- Works on both Windows and Unix-like systems (Linux, macOS).

Example output:

```
[>] ASTRA PyArmor Builder (simplified)
[>] Building astra/main.py
[>] Done: main
[>] Building astra/whitelist/getWhitelist.py
[>] Done: getWhitelist
[>] Cleaning up build temp folder...
[>] Finished. Output in dist/builds
```

---

## Requirements

Before running the builder, ensure the following Python packages are installed:

```bash
pip install pyarmor pyinstaller
```

---

## Cleanup Behavior

After every successful build:
- `_build/`, `_obf/`, and `transform/` are deleted automatically.
- Only the compiled executables remain under `builds/`.

If you want to keep these folders for debugging, comment out the cleanup section near the end of `make.py`.

---