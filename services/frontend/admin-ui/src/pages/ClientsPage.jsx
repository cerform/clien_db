import React, {useEffect, useState} from 'react'
import axios from 'axios'
import Modal from '../components/Modal'
import Toast from '../components/Toast'

function validateClient(c){
  if(!c.name || c.name.trim().length < 2) return 'Name should be at least 2 characters'
  if(c.phone && !/^\+?[0-9\-\s]{5,20}$/.test(c.phone)) return 'Phone looks invalid'
  if(c.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(c.email)) return 'Email looks invalid'
  return null
}

export default function ClientsPage(){
  const [clients,setClients] = useState([])
  const [loading,setLoading] = useState(false)
  const [modal,setModal] = useState(null)
  const [toast,setToast] = useState('')
  const [saving,setSaving] = useState(false)

  useEffect(()=>{ load() }, [])

  async function load(){
    setLoading(true)
    try{
      const r = await axios.get('/api/clients', {headers: {'Authorization': 'Bearer admin_token_1'}})
      setClients(r.data || [])
    }catch(e){ setToast('Failed to load clients') }
    finally{ setLoading(false) }
  }

  function open(c){
    setModal({...c})
  }

  async function save(){
    const err = validateClient(modal)
    if(err){ setToast(err); return }
    setSaving(true)
    try{
      await axios.put(`/api/clients/${modal.id}`, modal, {headers: {'Authorization': 'Bearer admin_token_1'}})
      setClients(prev => prev.map(x => x.id===modal.id? {...x, ...modal}: x))
      setModal(null)
      setToast('Saved')
    }catch(e){ setToast('Save failed') }
    finally{ setSaving(false) }
  }

  async function del(){
    if(!confirm('Delete client?')) return
    setSaving(true)
    try{
      await axios.delete(`/api/clients/${modal.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
      setClients(prev => prev.filter(x => x.id !== modal.id))
      setModal(null)
      setToast('Deleted')
    }catch(e){ setToast('Delete failed') }
    finally{ setSaving(false) }
  }

  return (
    <div className="container">
      <h2>Clients</h2>
      {loading && <div className="spinner" />}
      <div className="grid">
        {clients.map(c=> (
          <div className="card" key={c.id} onClick={()=>open(c)}>
            <div style={{fontWeight:700}}>{c.name || '—'}</div>
            <div style={{fontSize:12,color:'#9aa3ad'}}>{c.phone || ''}</div>
            <div style={{fontSize:12,color:'#9aa3ad'}}>{c.email || ''}</div>
          </div>
        ))}
      </div>

      {modal && (
        <Modal onClose={()=>setModal(null)}>
          <h3>Edit client</h3>
          <div style={{display:'grid',gap:8}}>
            <input className="input" value={modal.name||''} onChange={e=>setModal({...modal,name:e.target.value})} placeholder="Name" />
            <input className="input" value={modal.phone||''} onChange={e=>setModal({...modal,phone:e.target.value})} placeholder="Phone" />
            <input className="input" value={modal.email||''} onChange={e=>setModal({...modal,email:e.target.value})} placeholder="Email" />
            <textarea className="input" value={modal.notes||''} onChange={e=>setModal({...modal,notes:e.target.value})} placeholder="Notes" />
          </div>
          <div className="toolbar">
            <button onClick={save} disabled={saving}>{saving? <span className="spinner" /> : 'Save'}</button>
            <button onClick={del} style={{background:'#e5533d',color:'#fff'}} disabled={saving}>{saving? <span className="spinner" /> : 'Delete'}</button>
            <button onClick={()=>setModal(null)}>Close</button>
          </div>
        </Modal>
      )}

      <Toast msg={toast} />
    </div>
  )
}
