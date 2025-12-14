#!/usr/bin/env python3
"""
Simple installer GUI using tkinter that wraps the existing CLI installer `tools/install_and_deploy.py`.

Note: tkinter is an OS package on many systems. On Debian/Ubuntu install `python3-tk`.
"""
import subprocess
import sys
import os
import json

# Try to import tkinter; if import fails or no DISPLAY/WAYLAND is set, we'll fall back to CLI mode
try:
    from tkinter import Tk, Label, Entry, Button, StringVar, IntVar, Checkbutton, messagebox
    TK_INTERACTIVE = True
except Exception:
    TK_INTERACTIVE = False

ROOT = os.path.dirname(os.path.dirname(__file__))
CLI = os.path.join(ROOT, 'tools', 'install_and_deploy.py')

if not os.path.exists(CLI):
    print('Installer CLI script not found:', CLI)


def run_installer(project, region, dry_run=True):
    args = [sys.executable, CLI, '--project', project, '--region', region]
    if dry_run:
        args.append('--dry-run')
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)
        out, err = proc.communicate()
        out_text = out.decode('utf-8', errors='ignore')
        err_text = err.decode('utf-8', errors='ignore')
        return proc.returncode, out_text, err_text
    except Exception as e:
        return 1, '', str(e)


def main():
    # If Tkinter import or display not available, fallback to CLI mode
    if not TK_INTERACTIVE or (not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY')):
        print('GUI mode not available in this environment. Falling back to CLI installer.')
        # Run CLI in dry-run mode by default
            project = os.environ.get('INSTALLER_PROJECT', '')
            region = os.environ.get('INSTALLER_REGION', 'europe-west1')
        # Prompt for project if not set
        if not project:
            project = input('GCP Project ID: ').strip()
            if not project:
                print('Project ID is required. Aborting.')
                sys.exit(1)
        dry = True
        code, out, err = run_installer(project, region or 'europe-west1', dry_run=dry)
        if code == 0:
            print('Installer completed successfully (CLI fallback).')
            print(out)
            sys.exit(0)
        else:
            print('Installer failed (CLI fallback):')
            print(err)
            print(out)
            sys.exit(code)

    root = Tk()
    root.title('INKA Installer GUI')

    Label(root, text='GCP Project ID').grid(row=0, column=0, sticky='w')
    project_var = StringVar()
    Entry(root, textvariable=project_var, width=40).grid(row=0, column=1)

    Label(root, text='Region').grid(row=1, column=0, sticky='w')
    region_var = StringVar(value='europe-west1')
    Entry(root, textvariable=region_var, width=40).grid(row=1, column=1)

    dry_run_var = IntVar(value=1)
    Checkbutton(root, text='Dry run (no changes)', variable=dry_run_var).grid(row=2, column=1, sticky='w')

    def on_run():
        project = project_var.get().strip()
        region = region_var.get().strip()
        dry = bool(dry_run_var.get())
        if not project:
            messagebox.showerror('Error', 'Project ID is required')
            return
        code, out, err = run_installer(project, region, dry_run=dry)
        if code == 0:
            messagebox.showinfo('Success', 'Installer finished\n' + out[:2000])
        else:
            messagebox.showerror('Failed', 'Installer failed with code {}\n{}\n{}'.format(code, err, out[:2000]))

    Button(root, text='Run Installer', command=on_run).grid(row=3, column=1, pady=10, sticky='e')

    root.mainloop()


if __name__ == '__main__':
    main()
