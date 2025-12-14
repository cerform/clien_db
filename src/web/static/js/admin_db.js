document.addEventListener('DOMContentLoaded', function () {
  const sheetSelect = document.getElementById('sheet-select')
  const reloadBtn = document.getElementById('reload')
  const addRowBtn = document.getElementById('add-row')
  const tableDiv = document.getElementById('table')
  let table = null

  async function loadSheet(name) {
    tableDiv.innerHTML = '<div class="loading">Loading...</div>'
    try {
      const res = await fetch(`/api/admin/db/${name}`)
      const data = await res.json()
      if (!data.ok) {
        tableDiv.innerText = 'Error: ' + (data.error || 'unknown')
        app.showAlert('Failed to load sheet: ' + (data.error || 'unknown'), 'error')
        return
      }
    const rows = data.rows || []
    // compute columns from headers
    const cols = []
    if (rows.length > 0) {
      Object.keys(rows[0]).forEach(k => {
        cols.push({title: k, field: k, editor: 'input'})
      })
    } else {
      cols.push({title: 'id', field: 'id'})
    }
    // Add actions column
    cols.push({title: 'Actions', field: 'actions', formatter: function(cell){ return `<button class="btn edit-row">Edit</button> <button class="btn btn-danger delete-row">Delete</button>` }, hozAlign: 'center', headerSort:false, width:160})

    if (table) table.destroy()
    table = new Tabulator(tableDiv, {
      data: rows,
      layout: 'fitDataTable',
      columns: cols,
      selectable: true,
      cellEdited: async function (cell) {
        const row = cell.getRow().getData()
        const id = row.id
        const body = row
        try {
          const res = await fetch(`/api/admin/db/${name}/${id}`, {method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)})
          if (!res.ok) app.showAlert('Failed to save row', 'error')
        } catch (err) {
          app.showAlert('Network error while saving row', 'error')
        }
      }
    })

    // Handle action buttons in cells
    table.on('cellClick', async function(e, cell){
      try {
        if (cell.getColumn().getField() !== 'actions') return
        const row = cell.getRow().getData()
        const id = row.id
        if (e.target.closest('.delete-row')) {
          if (!confirm('Delete row?')) return
          try {
            const res = await fetch(`/api/admin/db/${name}/${id}`, {method: 'DELETE'})
            const j = await res.json()
            if (j.ok) { app.showAlert('Row deleted', 'success'); loadSheet(name) } else { app.showAlert('Failed to delete row: ' + (j.error||'unknown'), 'error') }
          } catch (err) { app.showAlert('Network error while deleting', 'error') }
        }
        if (e.target.closest('.edit-row')) {
          // Simple JSON edit prompt (PoC)
          try {
            const r = await fetch(`/api/admin/db/${name}/${id}`)
            const j = await r.json()
            if (!j.ok) return app.showAlert('Failed to fetch row for edit', 'error')
            const jsonText = JSON.stringify(j.row, null, 2)
            const edited = prompt('Edit row as JSON', jsonText)
            if (!edited) return
            let parsed
            try { parsed = JSON.parse(edited) } catch(e){ return app.showAlert('Invalid JSON', 'error') }
            const put = await fetch(`/api/admin/db/${name}/${id}`, {method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(parsed)})
            const putJ = await put.json()
            if (putJ.ok) { app.showAlert('Row updated', 'success'); loadSheet(name) } else { app.showAlert('Update failed: ' + (putJ.error||'unknown'), 'error') }
          } catch (err) { app.showAlert('Network error while editing', 'error') }
        }
      } catch (e) {
        console.error(e)
      }
    })
      // Add context menu for audit/rollback
      table.on('rowClick', function(e, row){
        // show small context actions
        // noop for now
      })
  }

  reloadBtn.addEventListener('click', () => loadSheet(sheetSelect.value))
  addRowBtn.addEventListener('click', async () => {
    const name = sheetSelect.value
    const res = await fetch(`/api/admin/db/${name}`, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({id: Date.now()})})
    const data = await res.json()
    if (data.ok) {
      loadSheet(name)
    } else {
      alert('Failed to add row: ' + (data.error || 'unknown'))
    }
  })

  document.getElementById('sync-admins').addEventListener('click', async () => {
    if (!confirm('Sync admins from Cloud SQL into the sheet config?')) return
    const res = await fetch('/api/admin/sync-admins', {method: 'POST'})
    const j = await res.json()
    alert('Sync result: ' + JSON.stringify(j))
  })

  // Export buttons
  const exportCSV = document.createElement('button')
  exportCSV.innerText = 'Export CSV'
  exportCSV.addEventListener('click', () => { table.download('csv', `${sheetSelect.value}.csv`) })
  document.querySelector('.container').appendChild(exportCSV)

  const exportJSON = document.createElement('button')
  exportJSON.innerText = 'Export JSON'
  exportJSON.addEventListener('click', () => { table.download('json', `${sheetSelect.value}.json`) })
  document.querySelector('.container').appendChild(exportJSON)

  // Bulk delete
  const bulkDelete = document.createElement('button')
  bulkDelete.innerText = 'Bulk Delete Selected'
  bulkDelete.addEventListener('click', async () => {
    const selected = table.getSelectedData()
    if (!selected || !selected.length) return app.showAlert('No rows selected', 'warning')
    if (!confirm(`Delete ${selected.length} rows?`)) return
    try {
      for (const r of selected) {
        const res = await fetch(`/api/admin/db/${sheetSelect.value}/${r.id}`, {method: 'DELETE'})
        const j = await res.json().catch(()=>({ok:false}))
        if (!j.ok) app.showAlert('Failed to delete some rows', 'error')
      }
      app.showAlert('Selected rows deleted', 'success')
      loadSheet(sheetSelect.value)
    } catch (err) {
      app.showAlert('Network error while deleting rows', 'error')
    }
  })
  document.querySelector('.container').appendChild(bulkDelete)

  // Search filter
  const searchInput = document.getElementById('admin-db-search')
  if (searchInput) {
    let debounce = null
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase()
      clearTimeout(debounce)
      debounce = setTimeout(() => {
        if (!q) { table.clearFilter(true) } else {
          table.setFilter((data, params) => {
            return Object.values(data).some(v => String(v || '').toLowerCase().includes(params.q))
          }, {q})
        }
      }, 250)
    })
  }

        if (e.target.closest('.edit-row')) {
          // Open modal-based JSON editor
          try {
            const r = await fetch(`/api/admin/db/${name}/${id}`)
            const j = await r.json()
            if (!j.ok) return app.showAlert('Failed to fetch row for edit', 'error')
            const jsonText = JSON.stringify(j.row, null, 2)
            document.getElementById('admin-edit-json').value = jsonText
            // store current sheet/name/id on modal element for save handler
            const modal = document.getElementById('adminEditModal')
            modal.dataset.sheet = name
            modal.dataset.rowId = id
            app.openModal('adminEditModal')
          } catch (err) { app.showAlert('Network error while editing', 'error') }
        }
  let currentAuditName = null
  let currentAuditRow = null
  let auditTable = null

  async function loadAudit(sheet, row) {
    currentAuditName = sheet
    currentAuditRow = row
    auditSheetSpan.innerText = sheet
    auditRowSpan.innerText = row
    const res = await fetch(`/api/admin/db/${sheet}/${row}/audit?page=${auditPage}&page_size=${auditPageSize}`)
    const j = await res.json()
    if (!j.ok) return alert('Failed to load audit: ' + (j.error || 'unknown'))
    const items = j.items || []
    if (auditTable) auditTable.destroy()
    auditTable = new Tabulator(auditTableDiv, {
      data: items,
      layout: 'fitColumns',
      columns: [
        {title: 'timestamp', field: 'timestamp'},
        {title: 'user', field: 'user_name'},
        {title: 'action', field: 'action'},
        {title: 'before', field: 'before'},
        {title: 'after', field: 'after'}
      ],
      selectable: 1
    })
    auditModal.style.display = 'block'
  }

  auditPrev.addEventListener('click', () => { if (auditPage>1) { auditPage--; loadAudit(currentAuditName, currentAuditRow) } })
  auditNext.addEventListener('click', () => { auditPage++; loadAudit(currentAuditName, currentAuditRow) })
  auditExport.addEventListener('click', () => { window.open(`/api/admin/db/${currentAuditName}/${currentAuditRow}/audit?format=csv&page=${auditPage}&page_size=${auditPageSize}`) })
  auditClose.addEventListener('click', () => { auditModal.style.display = 'none' })
  rollbackBtn.addEventListener('click', async () => {
    const sel = auditTable.getSelectedData()
    if (!sel || !sel.length) return alert('Select an audit entry to rollback to')
    const ts = sel[0].timestamp
    if (!confirm(`Rollback to ${ts}?`)) return
    const res = await fetch('/api/admin/db/rollback', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({sheet: currentAuditName, row_id: currentAuditRow, timestamp: ts})})
    const j = await res.json()
    if (j.ok) {
      alert('Rollback succeeded')
      auditModal.style.display = 'none'
      loadSheet(currentAuditName)
    } else {
      alert('Rollback failed: ' + (j.error || 'unknown'))
    }
  })

  // Edit modal handlers (field-based editor)
  const editModal = document.getElementById('adminEditModal')
  const editFields = document.getElementById('admin-edit-fields')
  const editErrors = document.getElementById('admin-edit-errors')

  function clearEditForm() {
    editFields.innerHTML = ''
    editErrors.innerText = ''
    delete editModal.dataset.sheet
    delete editModal.dataset.rowId
  }

  function makeField(name, value) {
    const wrapper = document.createElement('div')
    wrapper.className = 'form-group'
    const label = document.createElement('label')
    label.className = 'form-label'
    label.innerText = name
    let input

    const lname = name.toLowerCase()
    if (lname.includes('email')) {
      input = document.createElement('input'); input.type = 'email'
    } else if (lname.includes('date') || lname.includes('day')) {
      input = document.createElement('input'); input.type = 'date'
    } else if (lname.includes('time') || lname.includes('slot')) {
      input = document.createElement('input'); input.type = 'time'
    } else if (lname.includes('phone') || lname.includes('tel')) {
      input = document.createElement('input'); input.type = 'tel'
      input.pattern = '^\\+?[0-9\-\s]{6,20}$'
    } else {
      input = document.createElement('input'); input.type = 'text'
    }
    input.className = 'form-input'
    input.name = name
    input.value = value === null || value === undefined ? '' : String(value)

    wrapper.appendChild(label)
    wrapper.appendChild(input)
    return wrapper
  }

  document.getElementById('admin-edit-cancel').addEventListener('click', () => { app.closeModal(editModal); clearEditForm() })

  document.getElementById('admin-edit-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const sheet = editModal.dataset.sheet
    const rowId = editModal.dataset.rowId
    if (!sheet || !rowId) { app.showAlert('Missing context', 'error'); return }

    // collect fields
    const inputs = Array.from(editFields.querySelectorAll('[name]'))
    const payload = {}
    const errors = []
    for (const inp of inputs) {
      const name = inp.name
      let val = inp.value
      if (inp.type === 'number') {
        val = val ? Number(val) : null
      }
      // basic validation
      const lname = name.toLowerCase()
      if ((lname.includes('phone') || lname.includes('tel')) && val) {
        const phoneRe = /^\+?[0-9\-\s]{6,20}$/
        if (!phoneRe.test(val)) errors.push(`${name}: invalid phone`)
      }
      if ((lname.includes('email')) && val) {
        const emailRe = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
        if (!emailRe.test(val)) errors.push(`${name}: invalid email`)
      }
      // date format check for type=date
      if (inp.type === 'date' && val) {
        // basic YYYY-MM-DD check
        if (!/^\d{4}-\d{2}-\d{2}$/.test(val)) errors.push(`${name}: invalid date`)
      }
      payload[name] = val
    }
    if (errors.length) { editErrors.innerText = errors.join('; '); app.showAlert('Validation failed', 'error'); return }

    try {
      const res = await fetch(`/api/admin/db/${sheet}/${rowId}`, {method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)})
      const j = await res.json()
      if (j.ok) {
        app.showAlert('Row updated', 'success')
        app.closeModal(editModal)
        clearEditForm()
        loadSheet(sheet)
      } else {
        editErrors.innerText = j.error || 'Update failed'
        app.showAlert('Update failed', 'error')
      }
    } catch (err) { app.showAlert('Network error while saving', 'error') }
  })

  // Show audit modal on row double click
  document.addEventListener('dblclick', function (e) {
    const r = table.getSelectedData()[0]
    if (r && r.id) {
      auditPage = 1
      loadAudit(sheetSelect.value, r.id)
    }
  })
})
