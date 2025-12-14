import React, {useEffect, useState} from 'react'
import axios from 'axios'

export default function Services(){
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({name:'', description:'', price_from:0, price_to:0, duration_min:60, category:'tattoo', active:'yes'})
  const [error, setError] = useState(null)

  async function load(){
    setLoading(true)
    try{
      const r = await axios.get('/api/services', {headers: {'Authorization': 'Bearer admin_token_1'}})
      setItems(r.data || [])
    }catch(e){ setError(e.message) }
    finally{ setLoading(false) }
  }

  useEffect(()=>{ load() }, [])

  function openEdit(s){
    setSelected(s)
    setForm({name: s.name || '', description: s.description || '', price_from: s.price_from || 0, price_to: s.price_to || 0, duration_min: s.duration_min || 60, category: s.category || 'tattoo', active: s.active || 'yes'})
    (async ()=>{
      try{
        const r = await axios.get(`/api/services/${s.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
        const fresh = r.data || {}
        setForm({name: fresh.name || '', description: fresh.description || '', price_from: fresh.price_from || 0, price_to: fresh.price_to || 0, duration_min: fresh.duration_min || 60, category: fresh.category || 'tattoo', active: fresh.active || 'yes'})
      }catch(e){ }
    })()
  }

  async function save(){
    if(!selected) return
    try{
      await axios.put(`/api/services/${selected.id}`, form, {headers: {'Authorization': 'Bearer admin_token_1'}})
      setItems(prev => prev.map(x => x.id === selected.id ? {...x, ...form} : x))
      setSelected(null)
    }catch(e){ setError(e.message) }
  }

  async function remove(){
    if(!selected) return
    if(!confirm('Delete service?')) return
    try{
      await axios.delete(`/api/services/${selected.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
      setItems(prev => prev.filter(x => x.id !== selected.id))
      setSelected(null)
    }catch(e){ setError(e.message) }
  }

  return (
    <div>
      <h2>Services</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{color:'red'}}>{error}</div>}
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(240px,1fr))',gap:12}}>
        {items.map(s=> (
          <div key={s.id} className="card" onClick={()=>openEdit(s)} style={{cursor:'pointer'}}>
            <div style={{fontWeight:700}}>{s.name || '—'}</div>
            <div style={{fontSize:12,color:'#888'}}>{s.id}</div>
            <div style={{marginTop:8}}><small>{s.description || ''}</small></div>
            <div style={{marginTop:6, fontSize:12}}>{s.price_from || 0}–{s.price_to || 0} ₽ • {s.duration_min || 60}m</div>
          </div>
        ))}
      </div>

      {selected && (
        <div className="modal">
          <div className="modal-content">
            <h3>Edit service</h3>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
              <label>Name<input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} /></label>
              <label>Category<input value={form.category} onChange={e=>setForm({...form,category:e.target.value})} /></label>
              <label>Price From<input value={form.price_from} onChange={e=>setForm({...form,price_from:e.target.value})} /></label>
              <label>Price To<input value={form.price_to} onChange={e=>setForm({...form,price_to:e.target.value})} /></label>
              <label>Duration (min)<input value={form.duration_min} onChange={e=>setForm({...form,duration_min:e.target.value})} /></label>
              <label>Active<select value={form.active} onChange={e=>setForm({...form,active:e.target.value})}><option value="yes">yes</option><option value="no">no</option></select></label>
            </div>
            <div style={{marginTop:8}}>
              <label>Description<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} /></label>
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
