async function startInstaller(ev){
  ev && ev.preventDefault();
  const payload = {};
  payload.telegram_token = document.getElementById('telegram_token').value;
  payload.llm_api_key = document.getElementById('llm_api_key').value;
  payload.use_cloudsql = document.getElementById('use_cloudsql').checked;
  payload.spreadsheet_id = document.getElementById('spreadsheet_id').value;
  payload.enable_inka = document.getElementById('enable_inka').checked;
  payload.set_webhook = document.getElementById('set_webhook').checked;
  payload.admin_ids = document.getElementById('admin_ids').value;
  payload.project = document.getElementById('project').value;
  payload.region = document.getElementById('region').value;
  payload.service = document.getElementById('service').value;

  const res = await fetch('/installer/start', {method:'POST', body: JSON.stringify(payload), headers:{'Content-Type':'application/json'}});
  if(!res.ok){
    const err = await res.json();
    alert('Installer error: ' + (err.detail || JSON.stringify(err)));
    return;
  }
  const j = await res.json();
  const jobId = j.job_id;
  document.getElementById('job-id').innerText = jobId;
  pollLogs(jobId, 0);
}

async function pollLogs(jobId, offset){
  const r = await fetch(`/installer/logs/${jobId}?offset=${offset}`);
  const j = await r.json();
  const logs = j.logs || '';
  const newOffset = j.offset || offset;
  if(logs){
    const el = document.getElementById('logs');
    el.textContent += logs;
    el.scrollTop = el.scrollHeight;
  }
  // check status
  const s = await fetch(`/installer/status/${jobId}`);
  const sj = await s.json();
  if(sj.status === 'running' || sj.status === 'queued'){
    setTimeout(()=>pollLogs(jobId, newOffset), 1500);
  } else {
    document.getElementById('job-id').innerText = `Job ${jobId} finished: ${sj.status}`;
    if(sj.result_url){
      const el = document.createElement('div');
      el.innerHTML = `Deployed URL: <a href="${sj.result_url}" target="_blank">${sj.result_url}</a>`;
      document.body.insertBefore(el, document.getElementById('logs'));
    }
  }
}

document.getElementById('installer-form').addEventListener('submit', startInstaller);
// wire up wizard nav
document.querySelectorAll('[data-next]').forEach(b=>b.addEventListener('click', (e)=>{const cur = e.target.closest('.step'); const nxt = document.querySelector(`.step[data-step="${parseInt(cur.dataset.step)+1}"]`); if(cur) cur.style.display='none'; if(nxt) nxt.style.display='block';}));
document.querySelectorAll('[data-prev]').forEach(b=>b.addEventListener('click', (e)=>{const cur = e.target.closest('.step'); const prv = document.querySelector(`.step[data-step="${parseInt(cur.dataset.step)-1}"]`); if(cur) cur.style.display='none'; if(prv) prv.style.display='block';}));
document.getElementById('start-install').addEventListener('click', startInstaller);
