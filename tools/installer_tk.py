#!/usr/bin/env python3
"""
Simple Tkinter GUI installer for Cloud Run service + Secret Manager

Features:
- Prompt for Project ID, Service Name, Region, Secret name and token, Admin IDs, Image
- Create/add secret version in Secret Manager
- Add Secret IAM binding for Cloud Run service account
- Update Cloud Run service to reference secret (via --set-secrets)
- Deploy image to Cloud Run
- Show command output in a log view

Security note: Do NOT paste secrets into chats. This tool runs locally and stores nothing by
default (it only calls gcloud). Use files if preferred.
"""
import json
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def run_cmd(cmd, capture=True):
    """Run a shell command and return (returncode, stdout+stderr)"""
    try:
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        out = (res.stdout or '') + (res.stderr or '')
        return res.returncode, out
    except Exception as e:
        return 1, str(e)


class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Cloud Run Installer (Tk)')
        self.geometry('820x640')

        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=8, pady=8)

        # Inputs
        left = ttk.Frame(frame)
        left.pack(side='left', fill='y', padx=8, pady=8)

        def labeled(parent, label_text, **kw):
            lbl = ttk.Label(parent, text=label_text)
            lbl.pack(anchor='w', pady=(8, 0))
            ent = ttk.Entry(parent, **kw)
            ent.pack(fill='x')
            return ent

        self.project_entry = labeled(left, 'GCP Project ID:')
        self.service_entry = labeled(left, 'Cloud Run service name:',)
        self.region_entry = labeled(left, 'Region (e.g. europe-west1):')
        self.image_entry = labeled(left, 'Image (gcr.io/... or leave for existing):')
        self.secret_entry = labeled(left, 'Secret name (Secret Manager):')
        self.admins_entry = labeled(left, 'Admin IDs (comma separated):')

        ttk.Label(left, text='Bot token (hidden):').pack(anchor='w', pady=(8, 0))
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(left, textvariable=self.token_var, show='*')
        self.token_entry.pack(fill='x')

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill='x', pady=8)

        ttk.Button(btn_frame, text='Load token from file', command=self.load_token_file).pack(side='left')
        ttk.Button(btn_frame, text='Validate gcloud', command=self.validate_gcloud).pack(side='left', padx=8)

        # Action buttons
        actions = ttk.Frame(left)
        actions.pack(fill='x', pady=8)

        ttk.Button(actions, text='Create/Add secret', command=self.wrap(self.create_add_secret)).pack(fill='x')
        ttk.Button(actions, text='Grant secret access to service SA', command=self.wrap(self.grant_secret_access)).pack(fill='x')
        ttk.Button(actions, text='Set secret & deploy service', command=self.wrap(self.set_secret_and_deploy)).pack(fill='x')
        ttk.Button(actions, text='Full: create+grant+deploy', command=self.wrap(self.full_run)).pack(fill='x', pady=(8,0))

        # Right: logs
        right = ttk.Frame(frame)
        right.pack(side='right', fill='both', expand=True)
        ttk.Label(right, text='Output / Logs').pack(anchor='w')
        self.log = tk.Text(right, height=40, wrap='none')
        self.log.pack(fill='both', expand=True)

    def log_write(self, text):
        self.log.insert('end', text + '\n')
        self.log.see('end')

    def load_token_file(self):
        path = filedialog.askopenfilename(title='Token file', filetypes=[('Text files','*.txt'),('All','*')])
        if path:
            with open(path, 'r') as f:
                self.token_var.set(f.read().strip())
            self.log_write('Loaded token from file (len=%d)' % len(self.token_var.get()))

    def validate_gcloud(self):
        self.log_write('Checking gcloud installation...')
        code, out = run_cmd('gcloud --version')
        self.log_write(out.strip())
        if code == 0:
            self.log_write('gcloud available')
        else:
            self.log_write('gcloud not available or error')

    def wrap(self, fn):
        def inner():
            t = threading.Thread(target=fn)
            t.daemon = True
            t.start()
        return inner

    def create_add_secret(self):
        project = self.project_entry.get().strip()
        secret = self.secret_entry.get().strip() or 'TELEGRAM_BOT_TOKEN'
        token = self.token_var.get().strip()
        if not project or not token:
            messagebox.showerror('Missing', 'Project and token are required')
            return
        self.log_write('Adding new version to secret %s in project %s' % (secret, project))
        cmd = f"echo -n '{token}' | gcloud secrets versions add {secret} --data-file=- --project={project}"
        code, out = run_cmd(cmd)
        self.log_write(out)
        if code != 0:
            self.log_write('Failed to add secret version')
        else:
            self.log_write('Secret version added')

    def grant_secret_access(self):
        project = self.project_entry.get().strip()
        secret = self.secret_entry.get().strip() or 'TELEGRAM_BOT_TOKEN'
        sa = f"tattoo-bot@{project}.iam.gserviceaccount.com"
        self.log_write('Granting secretAccessor to %s on secret %s' % (sa, secret))
        cmd = f"gcloud secrets add-iam-policy-binding {secret} --member='serviceAccount:{sa}' --role='roles/secretmanager.secretAccessor' --project={project}"
        code, out = run_cmd(cmd)
        self.log_write(out)
        if code != 0:
            self.log_write('Failed to add IAM binding')
        else:
            self.log_write('IAM binding added')

    def set_secret_and_deploy(self):
        project = self.project_entry.get().strip()
        region = self.region_entry.get().strip() or 'europe-west1'
        service = self.service_entry.get().strip() or 'tattoo-bot'
        secret = self.secret_entry.get().strip() or 'TELEGRAM_BOT_TOKEN'
        image = self.image_entry.get().strip()

        self.log_write(f'Updating Cloud Run service {service} in {region} to use secret {secret}...')
        cmd = f"gcloud run services update {service} --region={region} --project={project} --set-secrets BOT_TOKEN={secret}:latest"
        code, out = run_cmd(cmd)
        self.log_write(out)
        if code != 0:
            self.log_write('Failed to set secret')
            return
        self.log_write('Secret set. If image provided, deploying image (else skip)')
        if image:
            cmd2 = f"gcloud run deploy {service} --image {image} --region={region} --project={project} --allow-unauthenticated"
            code2, out2 = run_cmd(cmd2)
            self.log_write(out2)
            if code2 != 0:
                self.log_write('Deploy failed')
            else:
                self.log_write('Deploy succeeded')

    def full_run(self):
        self.create_add_secret()
        self.grant_secret_access()
        self.set_secret_and_deploy()


def main():
    if shutil.which('gcloud') is None:
        print('gcloud CLI is required - install and authenticate before using this tool')
        return
    app = InstallerApp()
    app.mainloop()


if __name__ == '__main__':
    main()
