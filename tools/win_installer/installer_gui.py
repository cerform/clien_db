"""
Simple Tkinter installer GUI that copies the current project into a target directory,
creates a virtualenv there, and installs required packages.
This script is meant to be bundled into a Windows EXE via PyInstaller.

Basic features:
- Choose install directory
- Create venv in the install dir and install requirements
- Copy project files
- Display progress and status

Limitations:
- Creating shortcuts is platform-specific; this script creates a basic .bat shortcut if on Windows.
- Packaging into an EXE should be done on the target OS (Windows) or via Wine on Linux.

Usage to build an EXE on Windows:
    python -m pip install pyinstaller
    pyinstaller --onefile --add-data "../src;src" --add-data "../requirements.txt;." installer_gui.py

"""

import os
import sys
import shutil
import threading
import subprocess
import tempfile
import time
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception:
    # Fallback to Python's builtin import; PyInstaller bundling should supply Tkinter on Windows
    raise

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_DIR = Path.home() / 'clien_db_installed'

class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Clien DB Installer')
        self.geometry('560x260')
        self.resizable(False, False)

        self.install_dir_var = tk.StringVar(value=str(DEFAULT_TARGET_DIR))
        self.create_venv_var = tk.BooleanVar(value=True)
        self.copy_all_var = tk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text='Install directory:').grid(row=0, column=0, sticky='w')
        entry = ttk.Entry(frame, textvariable=self.install_dir_var, width=50)
        entry.grid(row=0, column=1, padx=(6, 6), sticky='w')
        ttk.Button(frame, text='Browse', command=self.browse_dir).grid(row=0, column=2)

        ttk.Checkbutton(frame, text='Create virtual environment and install requirements', variable=self.create_venv_var).grid(row=1, column=0, columnspan=3, sticky='w', pady=(6, 0))
        ttk.Checkbutton(frame, text='Copy project files (recommended)', variable=self.copy_all_var).grid(row=2, column=0, columnspan=3, sticky='w')

        self.progress = ttk.Progressbar(frame, orient='horizontal', mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(12, 6))

        self.status_lbl = ttk.Label(frame, text='Ready')
        self.status_lbl.grid(row=4, column=0, columnspan=3, sticky='w')

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(12, 0), sticky='e')

        ttk.Button(btn_frame, text='Install', command=self.start_install).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btn_frame, text='Exit', command=self.quit).grid(row=0, column=1)

    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=str(Path.home()))
        if d:
            self.install_dir_var.set(d)

    def start_install(self):
        target = Path(self.install_dir_var.get()).expanduser().resolve()
        if target.exists():
            if not messagebox.askyesno('Overwrite?', f"Target path {target} already exists. Overwrite?"):
                return

        self.progress['value'] = 0
        self.progress['maximum'] = 100
        self.status_lbl.config(text='Starting installation...')
        # Run work in thread to avoid freezing GUI
        threading.Thread(target=self._install_worker, args=(target,), daemon=True).start()

    def _install_worker(self, target: Path):
        try:
            steps = []
            if self.copy_all_var.get():
                steps.append(('copy', 'Copy files'))
            if self.create_venv_var.get():
                steps.append(('venv', 'Create virtualenv'))
                steps.append(('pip', 'Install requirements'))

            total_steps = len(steps)
            if total_steps == 0:
                self._set_status('Nothing to do')
                return

            step_index = 0
            if self.copy_all_var.get():
                self._set_status('Copying project files...')
                self._copy_project(target)
                step_index += 1
                self._progress(step_index, total_steps)

            if self.create_venv_var.get():
                self._set_status('Creating virtual environment...')
                venv_dir = target / 'venv'
                self._create_venv(venv_dir)
                step_index += 1
                self._progress(step_index, total_steps)

                self._set_status('Installing requirements...')
                self._install_requirements(venv_dir, target)
                step_index += 1
                self._progress(step_index, total_steps)

            self._set_status('Installation complete')
            # Create Windows shortcuts if applicable
            if os.name == 'nt':
                try:
                    self._set_status('Creating shortcuts')
                    self._create_windows_shortcuts(target)
                except Exception as e:
                    print('Failed to create shortcuts', e)
            messagebox.showinfo('Success', 'Installation finished successfully')
        except Exception as e:
            self._set_status('Error: ' + str(e))
            messagebox.showerror('Installer error', str(e))

    def _copy_project(self, target: Path):
        # Copy project files into target; exclude venvs and .git folder
        if target.exists():
            shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

        ignore = shutil.ignore_patterns('.git', '.venv', '__pycache__', 'htmlcov', '*.pyc', '*.pyo', '*.pyd')
        # Copy main repo files
        src = PROJECT_ROOT
        for item in src.iterdir():
            if item.name == 'tools' and item.parts[-1] == 'win_installer':
                # Do not copy our installer directory into the installed project
                continue
            if item.name.startswith('.'):
                continue
            try:
                if item.is_dir():
                    shutil.copytree(item, target / item.name, ignore=ignore)
                else:
                    shutil.copy2(item, target / item.name)
            except Exception as e:
                print('copy skip', item, e)

    def _create_venv(self, venv_dir: Path):
        import venv
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)

    def _create_windows_shortcuts(self, target: Path):
        """Create simple .bat files on Desktop and inside install dir to run/uninstall the application.
        Uses simple batch files so no extra dependencies are required in the installer.
        """
        desktop = Path(os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'))
        if not desktop.exists():
            desktop = None

        # Create run bat
        run_bat_content = f"@echo off\nREM Run the bot from the installed folder\n\"%~dp0\\venv\\Scripts\\python.exe\" \"%~dp0\\run.py\" %*\n"
        uninstall_bat_content = (
            f"@echo off\nREM Uninstall the installed files\n"
            f"echo Removing installed folder: {str(target)}\n"
            f"rmdir /S /Q \"{str(target)}\"\n"
            f"pause\n"
        )

        try:
            # Write inside install target
            run_path = target / 'run_bot.bat'
            uninstall_path = target / 'uninstall.bat'
            run_path.write_text(run_bat_content)
            uninstall_path.write_text(uninstall_bat_content)
            # Optionally create on Desktop
            if desktop is not None:
                desktop_run = desktop / f"Run_Clien_DB.bat"
                desktop_uninstall = desktop / f"Uninstall_Clien_DB.bat"
                desktop_run.write_text(f"@echo off\ncd /d \"{str(target)}\"\ncall \"{str(target / 'venv' / 'Scripts' / 'activate') }\" & python run.py\n")
                desktop_uninstall.write_text(uninstall_bat_content)
        except Exception as ex:
            print('Failed to create windows shortcuts:', ex)

    def _install_requirements(self, venv_dir: Path, install_target: Path):
        # Find pip inside venv
        pip_path = venv_dir / ('Scripts' if os.name == 'nt' else 'bin') / ('pip.exe' if os.name == 'nt' else 'pip')
        requirements_file = install_target / 'requirements.txt'
        if not requirements_file.exists():
            # Try project root
            requirements_file = PROJECT_ROOT / 'requirements.txt'
            if not requirements_file.exists():
                self._set_status('No requirements.txt found; skipping pip install')
                return

        cmd = [str(pip_path), 'install', '-r', str(requirements_file)]
        self._set_status('Running: ' + ' '.join(cmd))
        subprocess.check_call(cmd)

    def _progress(self, step, total):
        perc = int(step / total * 100)
        self.progress['value'] = perc

    def _set_status(self, text):
        self.status_lbl.config(text=text)
        # Update the GUI from the main thread
        try:
            self.update_idletasks()
        except Exception:
            pass


if __name__ == '__main__':
    app = InstallerGUI()
    app.mainloop()
