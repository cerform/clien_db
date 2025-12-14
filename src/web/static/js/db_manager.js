document.addEventListener('DOMContentLoaded', async function(){
  const select = document.getElementById('db-tables-select')
  const loadBtn = document.getElementById('load-table')
  const refreshBtn = document.getElementById('refresh-tables')
  const exportBtn = document.getElementById('export-table')
  const tableDiv = document.getElementById('db-table')
  let table = null
  let currentTable = null
  let currentRows = []

  async function refreshTables(){
    select.innerHTML = '<option>Loading...</option>'
    try{
      const res = await fetch('/api/db/tables')
      const j = await res.json()
      if (!j.ok) { select.innerHTML = '<option>Error</option>'; app.showAlert('Failed to load tables', 'error'); return }
      select.innerHTML = ''
      j.tables.forEach(t => { const opt = document.createElement('option'); opt.value = t; opt.innerText = t; select.appendChild(opt) })
    }catch(e){ select.innerHTML = '<option>Error</option>'; app.showAlert('Network error loading tables', 'error') }
  }

  async function loadTable(name){
    if (!name) return
    currentTable = name
    tableDiv.innerHTML = 'Loading...'
    try{
      const res = await fetch(`/api/db/table/${name}?limit=200&offset=0`)
      const j = await res.json()
      if (!j.ok) { tableDiv.innerText = 'Failed: ' + (j.detail || 'unknown'); app.showAlert('Failed to load table', 'error'); return }
      currentRows = j.rows || []
      const cols = []
      if (currentRows.length>0){
        Object.keys(currentRows[0]).forEach(k => cols.push({title:k, field:k, editor:'input'}))
      }
      cols.push({title:'Actions', field:'actions', formatter:function(){return '<button class="btn edit-row">Edit</button>'}, hozAlign:'center', headerSort:false, width:120})
      if (table) table.destroy()
      table = new Tabulator(tableDiv, {data: currentRows, layout:'fitDataTable', columns: cols, selectable: true})

      table.on('cellClick', function(e, cell){
        if (cell.getColumn().getField() === 'actions'){
          const row = cell.getRow().getData()
          const text = JSON.stringify(row, null, 2)
          // Simple read-only viewer
          alert(text)
        }
      })

    }catch(e){ tableDiv.innerText = 'Error loading table'; app.showAlert('Network error loading table', 'error') }
  }

  loadBtn.addEventListener('click', ()=> loadTable(select.value))
  refreshBtn.addEventListener('click', refreshTables)
  exportBtn.addEventListener('click', ()=>{ if (!table) return app.showAlert('No table loaded','warning'); table.download('csv', `${select.value || 'table'}.csv`) })
  exportBtn.addEventListener('click', async ()=>{
    if (!select.value) return app.showAlert('No table selected','warning')
    try{
      const res = await fetch(`/api/db/table/${select.value}/export`, {headers: {'Accept': 'text/csv'}})
      if (!res.ok) { app.showAlert('Export failed', 'error'); return }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${select.value}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      app.showAlert('Export started', 'success')
    }catch(e){ app.showAlert('Network error during export', 'error') }
  })

  // initial load
  await refreshTables()
})
