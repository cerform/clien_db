"""
Helper script to build Windows EXE via PyInstaller.

Usage:
    python build_installer.py [--onefile] [--noconsole]

Note: PyInstaller must be installed in the environment. On Windows:
    python -m pip install pyinstaller

On Linux, to build a Windows exe, either run this script under Wine/Python for Windows, or run PyInstaller on a Windows system.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
INSTALLER_SCRIPT = TOOLS_DIR / 'installer_gui.py'

def build(onefile=True, noconsole=True):
    # Base command
    cmd = ['pyinstaller']
    if onefile:
        cmd.append('--onefile')
    if noconsole:
        cmd.append('--noconsole')

    # Add specific data from src (this is relative to build folder; use ; on Windows and : on POSIX)
    if os.name == 'nt':
        add_data = f"{PROJECT_ROOT / 'src'};src"
    else:
        # For cross-platform building we still pass ; as Windows will expect it; PyInstaller on linux uses ':' separators,
        # but specifying paths here is environment-specific. We'll pass the simpler set for typical Windows builds.
        add_data = f"{PROJECT_ROOT / 'src'}{os.pathsep}src"

    cmd += ['--add-data', str(add_data)]
    # Include requirements file for the installer to use
    cmd += ['--add-data', str(PROJECT_ROOT / 'requirements.txt') + os.pathsep + '.']

    cmd.append(str(INSTALLER_SCRIPT))

    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)

if __name__ == '__main__':
    build()
