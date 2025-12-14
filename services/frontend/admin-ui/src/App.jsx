import React, {useState} from 'react'
import ClientsPage from './pages/ClientsPage'
import ServicesPage from './pages/ServicesPage'

export default function App(){
  const [tab, setTab] = useState('clients')
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Tattoo Admin</h1>
        <nav>
          <button onClick={()=>setTab('clients')} className={tab==='clients'? 'active':''}>Clients</button>
          <button onClick={()=>setTab('services')} className={tab==='services'? 'active':''}>Services</button>
        </nav>
      </header>
      <main className="app-main">
        {tab==='clients' ? <ClientsPage /> : <ServicesPage />}
      </main>
    </div>
  )
}
