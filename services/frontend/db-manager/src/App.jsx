import React, {useEffect, useState} from 'react'
import axios from 'axios'
import Clients from './Clients'
import Services from './Services'

export default function App(){
  const [tables, setTables] = useState([])
  const [selected, setSelected] = useState('')
  const [rows, setRows] = useState([])
  const [view, setView] = useState('clients') // 'clients' or 'db'

  useEffect(()=>{
    axios.get('/api/db/tables', {headers: {'Authorization': 'Bearer admin_token_1'}}).then(r=>setTables(r.data.tables || [])).catch(()=>setTables([]))
  },[])

  async function load(){
    if(!selected) return
    const r = await axios.get(`/api/db/table/${selected}`, {headers: {'Authorization': 'Bearer admin_token_1'}})
    setRows(r.data.rows || [])
  }

  return (
    <div style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>DB Manager PoC (React)</h1>
      <div style={{display:'flex',gap:8,alignItems:'center', marginBottom:10}}>
        <button onClick={()=>setView('clients')}>Clients</button>
        <button onClick={()=>setView('db')}>DB Tables</button>
      </div>

      {view === 'clients' ? (
        <Clients />
      ) : view === 'services' ? (
        <Services />
      ) : (
        <div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <select value={selected} onChange={e=>setSelected(e.target.value)}>
              <option value="">Select table</option>
              {tables.map(t=> <option key={t} value={t}>{t}</option>)}
            </select>
            <button onClick={load}>Load</button>
          </div>
          <div style={{marginTop:16}}>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(rows.slice(0,20), null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  )
}
