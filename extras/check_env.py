#!/usr/bin/env python3
"""
Armory Environment Checker

This small script helps contributors and users verify whether their
system meets the basic build requirements for Armory. It checks for:
- Python 2.x/3.x versions
- GCC / g++ availability
- SWIG installation
- Qt4 development tools
"""

import subprocess
import sys
import shutil

def check(cmd):
    return shutil.which(cmd) is not None

def main():
    print("🔍 Checking Armory build environment...\n")

    print(f"Python version: {sys.version.split()[0]}")
    print("✔️ Python OK" if sys.version_info >= (2, 6) else "❌ Python 2.6+ required")

    for tool in ["gcc", "g++", "swig", "qmake"]:
        status = "✔️ Found" if check(tool) else "❌ Missing"
        print(f"{tool:8} : {status}")

    print("\n✅ Environment check complete.")
    print("If any tools are missing, please install them before building Armory.")

if __name__ == "__main__":
    main()
