import React, {useEffect, useState} from 'react'
import axios from 'axios'

export default function Clients(){
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({name:'', phone:'', email:'', notes:''})
  const [error, setError] = useState(null)

  async function load(){
    setLoading(true)
    try{
      const r = await axios.get('/api/clients', {headers: {'Authorization': 'Bearer admin_token_1'}})
      setClients(r.data || [])
    }catch(e){
      setError(e.message)
    }finally{ setLoading(false) }
  }

  useEffect(()=>{ load() }, [])

  function openEdit(c){
    // Open edit modal and request fresh data from server if available
    setSelected(c)
    setForm({name: c.name || '', phone: c.phone || '', email: c.email || '', notes: c.notes || ''})
    // Try to fetch latest client data
    (async ()=>{
      try{
        const r = await axios.get(`/api/clients/${c.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
        const fresh = r.data || {}
        setForm({name: fresh.name || '', phone: fresh.phone || '', email: fresh.email || '', notes: fresh.notes || ''})
      }catch(e){
        // ignore; we already have fallback values
      }
    })()
  }

  async function save(){
    if(!selected) return
    try{
      await axios.put(`/api/clients/${selected.id}`, form, {headers: {'Authorization': 'Bearer admin_token_1'}})
      // update local list item in-place
      setClients(prev => prev.map(x => x.id === selected.id ? {...x, ...form} : x))
      setSelected(null)
    }catch(e){
      setError(e.message)
    }
  }

  async function remove(){
    if(!selected) return
    if(!confirm('Delete client?')) return
    try{
      await axios.delete(`/api/clients/${selected.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
      // remove locally
      setClients(prev => prev.filter(x => x.id !== selected.id))
      setSelected(null)
    }catch(e){ setError(e.message) }
  }

  return (
    <div>
      <h2>Clients</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{color:'red'}}>{error}</div>}
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(220px,1fr))',gap:12}}>
        {clients.map(c=> (
          <div key={c.id} className="card" onClick={()=>openEdit(c)} style={{cursor:'pointer'}}>
            <div style={{fontWeight:700}}>{c.name || '—'}</div>
            <div style={{fontSize:12,color:'#888'}}>{c.id}</div>
            <div style={{marginTop:8}}><strong>Email:</strong> {c.email || '—'}</div>
            <div><strong>Phone:</strong> {c.phone || '—'}</div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {selected && (
        <div className="modal">
          <div className="modal-content">
            <h3>Edit client</h3>
            <div style={{display:'flex',flexDirection:'column',gap:8}}>
              <label>Name<input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} /></label>
              <label>Phone<input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} /></label>
              <label>Email<input value={form.email} onChange={e=>setForm({...form,email:e.target.value})} /></label>
              <label>Notes<textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} /></label>
            </div>
            <div style={{marginTop:12,display:'flex',gap:8}}>
              <button onClick={save}>Save</button>
              <button onClick={remove} style={{background:'#e5533d',color:'#fff'}}>Delete</button>
              <button onClick={()=>setSelected(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
