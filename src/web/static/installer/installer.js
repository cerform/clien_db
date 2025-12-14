async function startInstaller(ev){
  ev && ev.preventDefault();
  const f = document.getElementById('installer-form');
  const data = new FormData(f);
  const payload = {};
  for(const [k,v] of data.entries()) payload[k] = v;
  payload.set_webhook = !!data.get('set_webhook');
  const res = await fetch('/installer/start', {method:'POST', body: JSON.stringify(payload), headers:{'Content-Type':'application/json'}});
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
