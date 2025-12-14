# Windows EXE Installer (Tkinter)

This folder contains a simple Tkinter-based installer GUI that can be bundled into a Windows EXE using PyInstaller.

Files:
- `installer_gui.py` — Tkinter GUI script. It copies the project files into a chosen target dir, creates a venv, and installs requirements.
- `build_installer.py` — Helper script to call PyInstaller with sensible defaults.
- `build_installer.sh` — Shell script wrapper.

How to build an EXE on Windows
1. Install Python 3.10+ and pip.
2. Optional: create a virtualenv for the build.
3. Install PyInstaller and optionally Tkinter (Tkinter usually installed with Python on Windows):
   - `pip install pyinstaller`
4. From this folder run:
    ```bash
    python build_installer.py
    # or
    pyinstaller --onefile --add-data "../src;src" --add-data "../requirements.txt;." installer_gui.py
    ```
5. Output exe will be in `dist/installer_gui.exe`.

Building a Windows EXE on Linux
- PyInstaller generally builds native binaries and should be run on the target OS. To build a Windows EXE from Linux you can use a Windows Python environment executed with Wine, or use a Windows build machine.
- Using Wine: install Wine, then use a Windows Python installation under wine and run pyinstaller from there.

Notes and limitations
- The generated EXE is a single-file (if `--onefile`). The installer itself runs the Python interpreter inside the EXE.
- This installer is intentionally simple; it copies repo files and creates a virtualenv to host them. If you need shortcuts, registry entries, or a deeper Windows installer experience, consider NSIS, Inno Setup, or WiX.
 - Starting with this change, the installer creates 2 small `.bat` helper files in the installed folder and attempts to write them to the user's Desktop when run on Windows:
     - `run_bot.bat` — runs the bot using the created venv
     - `uninstall.bat` — deletes the installed folder (simple removal)
 - If you want proper Start Menu and Desktop shortcuts or an uninstall entry, we can add pywin32 or use a dedicated installer like NSIS.

Example: Quick test on Linux (non-Windows exe, but you can test functionality)
1. Run the installer GUI directly with Python on Linux for testing:
    ```bash
    python installer_gui.py
    ```
2. Choose a target folder and run install. It will copy files and create a local venv there.

If you want, I can help adapt this script to:
- Add desktop/start menu shortcuts on Windows
- Create an Uninstaller
- Include specific files from `src` only instead of whole repo
- More advanced package signing (requires Windows tooling)
