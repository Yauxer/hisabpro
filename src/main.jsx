import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import PersonnelApp from './PersonnelApp.jsx'
import Login from './pages/Login.jsx'
import { ExerciceProvider }  from './data/ExerciceContext.jsx'
import { ModulesProvider }   from './data/ModulesContext.jsx'
import { EcrituresProvider } from './data/EcrituresContext.jsx'
import { FacturesProvider }  from './data/FacturesContext.jsx'
import { EmployesProvider }  from './data/EmployesContext.jsx'
import { PersonnelAccesProvider } from './data/PersonnelAccesContext.jsx'
import { isConnecte,authAPI } from './services/api.js'
import ErrorBoundary         from './components/ErrorBoundary.jsx'
import Notifications         from './components/Notifications.jsx'
import './styles/global.css'
import './styles/forms.css'

function Root() {
  const [connecte, setConnecte] = useState(isConnecte())
  const [profil,setProfil]=useState(null),[erreur,setErreur]=useState(''),[revision,setRevision]=useState(0)
  useEffect(()=>{
    if(!connecte)return
    let actif=true
    setProfil(null);setErreur('')
    const relu=e=>{if(actif&&e.detail?.role)setProfil(e.detail.role)}
    window.addEventListener('hisabpro-profil-relu',relu)
    authAPI.me().then(u=>{if(actif)setProfil(u.role)}).catch(e=>{if(actif)setErreur(e.message)})
    return()=>{actif=false;window.removeEventListener('hisabpro-profil-relu',relu)}
  },[connecte,revision])

  if (!connecte) {
    return <Login onConnecte={() => setConnecte(true)} />
  }

  if(!profil)return <div style={{padding:24}}>{erreur?<><p role="alert">{erreur}</p><button onClick={()=>setRevision(v=>v+1)}>Réessayer</button><button onClick={()=>authAPI.logout()}>Déconnexion</button></>:<p role="status">Chargement du profil…</p>}</div>
  if(profil==='personnel')return <ModulesProvider personnelSeul><PersonnelAccesProvider><PersonnelApp/></PersonnelAccesProvider></ModulesProvider>

  return (
    <ExerciceProvider>
      <ModulesProvider>
        <EcrituresProvider>
          <FacturesProvider>
            <EmployesProvider>
              <PersonnelAccesProvider><App /></PersonnelAccesProvider>
            </EmployesProvider>
          </FacturesProvider>
        </EcrituresProvider>
      </ModulesProvider>
    </ExerciceProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <Root />
      <Notifications />
    </ErrorBoundary>
  </React.StrictMode>
)
