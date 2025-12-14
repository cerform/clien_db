from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.templating import Jinja2Templates
import uuid
import threading
import subprocess
import tempfile
import os
import time
import logging

router = APIRouter(prefix="/installer", tags=["installer"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

logger = logging.getLogger("web.installer")

# Simple in-memory job store. For production use a persistent store.
_JOBS = {}


def _run_install_subprocess(job_id: str, args: dict):
    job = _JOBS[job_id]
    logfile = job["logfile"]
    cmd = [
        os.environ.get("PYTHON_EXECUTABLE", "python"),
        os.path.join(os.getcwd(), "tools", "install_and_deploy.py"),
        "--project",
        args.get("project", ""),
        "--region",
        args.get("region", "europe-west1"),
        "--service",
        args.get("service", "inka-bot"),
        "--telegram-token",
        args.get("telegram_token", ""),
    ]
    if args.get("set_webhook"):
        cmd.append("--set-webhook")

    job["status"] = "running"
    job["started_at"] = time.time()
    logger.info("Starting install job %s: %s", job_id, " ".join(cmd))
    try:
        with open(logfile, "ab") as lf:
            process = subprocess.Popen(cmd, stdout=lf, stderr=lf)
            ret = process.wait()
        job["exit_code"] = ret
        job["status"] = "succeeded" if ret == 0 else "failed"
    except Exception as e:
        logger.exception("Installer job failed: %s", e)
        job["status"] = "failed"
        with open(logfile, "ab") as lf:
            lf.write((f"\nException: {e}\n").encode())
    finally:
        job["ended_at"] = time.time()


@router.get("/", response_class=HTMLResponse)
async def installer_index(request: Request):
    # Render minimal installer UI
    templates_env = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
    return templates_env.TemplateResponse("installer/index.html", {"request": request})


@router.post("/start")
async def installer_start(payload: dict):
    # payload should include keys: project, region, service, telegram_token, set_webhook
    job_id = str(uuid.uuid4())
    fd, logfile = tempfile.mkstemp(prefix=f"installer_{job_id}_", suffix=".log")
    os.close(fd)
    _JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "logfile": logfile,
        "created_at": time.time(),
    }

    # Start background thread to run the installer subprocess
    t = threading.Thread(target=_run_install_subprocess, args=(job_id, payload), daemon=True)
    _JOBS[job_id]["thread"] = t
    t.start()
    return JSONResponse({"job_id": job_id})


@router.get("/status/{job_id}")
async def installer_status(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse({
        "job_id": job_id,
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "ended_at": job.get("ended_at"),
        "exit_code": job.get("exit_code"),
    })


@router.get("/logs/{job_id}")
async def installer_logs(job_id: str, offset: int = 0):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    logfile = job.get("logfile")
    if not logfile or not os.path.exists(logfile):
        return JSONResponse({"logs": ""})
    with open(logfile, "rb") as lf:
        lf.seek(offset)
        data = lf.read()
    return JSONResponse({"logs": data.decode(errors="replace"), "offset": offset + len(data)})


@router.get("/complete", response_class=HTMLResponse)
async def installer_complete(request: Request):
    return templates.TemplateResponse("installer/complete.html", {"request": request})


# Expose name expected by src.web.app
installer_router = router
# Stub for installer_router
installer_router = None
