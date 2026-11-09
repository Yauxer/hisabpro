import {useState,useRef,useCallback} from 'react'
import {BrowserRouter,Routes,Route,Navigate,Outlet,Link} from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import SelecteurSociete from './components/SelecteurSociete.jsx'
import CompteSecurite from './components/CompteSecurite.jsx'
import Personnel from './pages/Personnel.jsx'
import PaieElements from './pages/PaieElements.jsx'
import PaieChargesSociales from './pages/PaieChargesSociales.jsx'
import PaieFiscalite from './pages/PaieFiscalite.jsx'
import PaieTraitement from './pages/PaieTraitement.jsx'
import PaieCloture from './pages/PaieCloture.jsx'
import PaieDuMois from './pages/PaieDuMois.jsx'
import {useModules} from './data/ModulesContext.jsx'
import s from './components/Layout.module.css'

function EspacePersonnel(){
  const {societe,chargement,erreur,recharger}=useModules(),[menu,setMenu]=useState(false),bouton=useRef(null)
  const fermer=useCallback(()=>{setMenu(false);bouton.current?.focus()},[])
  if(chargement)return <p role="status" style={{padding:24}}>Chargement de la société…</p>
  if(erreur)return <div style={{padding:24}}><p role="alert">{erreur}</p><button onClick={recharger}>Réessayer le contexte Personnel</button></div>
  return <div className={s.layout}><Sidebar mobileOuvert={menu} onFermer={fermer}/>
    {menu&&<button className={s.voileNavigation} aria-label="Fermer la navigation" onClick={fermer}/>}
    <div className={s.main}><div className={s.topbar}>
      <button ref={bouton} className={s.menuMobile} aria-label="Ouvrir la navigation" aria-controls="navigation-principale" aria-expanded={menu} onClick={()=>setMenu(v=>!v)}><i className="ti ti-menu-2" aria-hidden="true"/></button>
      <Link to="/personnel-paie/compte" style={{fontSize:12,whiteSpace:'nowrap'}}>Mon compte</Link><SelecteurSociete societeActuelle={societe?.raison_sociale} peutCreer={false}/>
    </div><main className={s.content}><Outlet/></main></div>
  </div>
}
export default function PersonnelApp(){return <BrowserRouter basename={import.meta.env.BASE_URL}><Routes><Route path="/" element={<EspacePersonnel/>}>
  <Route index element={<Navigate to="/personnel-paie/personnel" replace/>}/>
  <Route path="personnel-paie/compte" element={<div style={{padding:20}}><CompteSecurite/></div>}/>
  <Route path="personnel-paie/personnel" element={<Personnel/>}/>
  <Route path="personnel-paie/personnel/:employeId" element={<Personnel/>}/>
  <Route path="personnel-paie/demandes" element={<Personnel/>}/>
  <Route path="personnel-paie/elements" element={<PaieElements/>}/>
  <Route path="personnel-paie/charges-sociales" element={<PaieChargesSociales/>}/>
  <Route path="personnel-paie/fiscalite" element={<PaieFiscalite/>}/>
  <Route path="personnel-paie/charges-sociales/simulations" element={<PaieChargesSociales/>}/>
  <Route path="personnel-paie/elements/variables" element={<PaieElements/>}/>
  <Route path="personnel-paie/traitement" element={<PaieTraitement/>}/>
  <Route path="personnel-paie/paie-du-mois" element={<PaieDuMois/>}/>
  <Route path="personnel-paie/bulletins" element={<PaieCloture section="bulletins"/>}/>
  <Route path="personnel-paie/avances" element={<PaieCloture section="avances"/>}/>
  <Route path="personnel-paie/paiements" element={<PaieCloture section="paiements"/>}/>
  <Route path="personnel-paie/comptabilisation" element={<PaieCloture section="comptabilisation"/>}/>
  <Route path="personnel-paie/etats" element={<PaieCloture section="etats"/>}/>
  <Route path="personnel-paie/*" element={<Personnel indisponible/>}/>
  <Route path="*" element={<Navigate to="/personnel-paie/personnel" replace/>}/>
</Route></Routes></BrowserRouter>}
