import React, {useState,useEffect} from 'react'
import axios from 'axios'
import Modal from '../components/Modal'
import Toast from '../components/Toast'

function validateService(s){
  if(!s.name || s.name.trim().length<2) return 'Name required'
  return null
}

export default function ServicesPage(){
  const [items,setItems] = useState([])
  const [loading,setLoading] = useState(false)
  const [modal,setModal] = useState(null)
  const [toast,setToast] = useState('')
  const [saving,setSaving] = useState(false)

  useEffect(()=>{ load() }, [])
  async function load(){
    setLoading(true)
    try{ const r = await axios.get('/api/services', {headers: {'Authorization': 'Bearer admin_token_1'}}); setItems(r.data || []) }catch(e){ setToast('Failed to load') }finally{ setLoading(false) }
  }

  function open(s){ setModal({...s}) }

  async function save(){
    const err = validateService(modal)
    if(err){ setToast(err); return }
    setSaving(true)
    try{ await axios.put(`/api/services/${modal.id}`, modal, {headers: {'Authorization': 'Bearer admin_token_1'}}); setItems(prev => prev.map(x => x.id===modal.id? {...x,...modal}: x)); setModal(null); setToast('Saved') }catch(e){ setToast('Save failed') }finally{ setSaving(false) }
  }

  async function del(){ if(!confirm('Delete service?')) return; setSaving(true); try{ await axios.delete(`/api/services/${modal.id}`, {headers: {'Authorization': 'Bearer admin_token_1'}}); setItems(prev => prev.filter(x => x.id !== modal.id)); setModal(null); setToast('Deleted') }catch(e){ setToast('Delete failed') }finally{ setSaving(false) } }

  return (
    <div className="container">
      <h2>Services</h2>
      {loading && <div className="spinner" />}
      <div className="grid">
        {items.map(s=> (
          <div className="card" key={s.id} onClick={()=>open(s)}>
            <div style={{fontWeight:700}}>{s.name || '—'}</div>
            <div style={{fontSize:12,color:'#9aa3ad'}}>{s.description || ''}</div>
            <div style={{fontSize:12,color:'#9aa3ad'}}>{s.price_from || ''}–{s.price_to || ''} ₽</div>
          </div>
        ))}
      </div>
      {modal && (
        <Modal onClose={()=>setModal(null)}>
          <h3>Edit service</h3>
          <div style={{display:'grid',gap:8}}>
            <input className="input" value={modal.name||''} onChange={e=>setModal({...modal,name:e.target.value})} placeholder="Name" />
            <input className="input" value={modal.description||''} onChange={e=>setModal({...modal,description:e.target.value})} placeholder="Description" />
            <div style={{display:'flex',gap:8}}>
              <input className="input" value={modal.price_from||''} onChange={e=>setModal({...modal,price_from:e.target.value})} placeholder="Price from" />
              <input className="input" value={modal.price_to||''} onChange={e=>setModal({...modal,price_to:e.target.value})} placeholder="Price to" />
            </div>
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
