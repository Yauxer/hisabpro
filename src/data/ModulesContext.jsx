import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { API_BASE, getToken, formatErreurAPI,personnelAPI } from '../services/api.js'

const ModulesContext = createContext(null)

const BASE_URL = API_BASE

async function fetchAvecAuth(path) {
  const token = getToken()
  if (!token) return null
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) return null
  return res.json()
}

async function patchAvecAuth(path, body) {
  const token = getToken()
  if (!token) throw new Error('Session expirée : reconnectez-vous.')
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: `Erreur HTTP ${res.status}` }))
    throw new Error(formatErreurAPI(error.detail))
  }
  return res.json()
}

export function ModulesProvider({ children, personnelSeul=false }) {
  const [modules,  setModules]  = useState({
    facturation:  true,
    comptabilite: true,
    paie_grh:     true,
  })
  const [societe,  setSociete]  = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur,setErreur]=useState('')

  const charger = useCallback(async () => {
    setChargement(true)
    setErreur('')
    try {
      if(personnelSeul){
        const ctx=await personnelAPI.contexte()
        if(!ctx)throw new Error('Contexte Personnel indisponible.')
        setSociete(ctx.societe);setModules({facturation:false,comptabilite:false,paie_grh:ctx.module_actif});return
      }
      const [mods, soc] = await Promise.all([
        fetchAvecAuth('/api/societe/modules'),
        fetchAvecAuth('/api/societe/moi'),
      ])
      if (mods) {
        const etat = {}
        Object.entries(mods).forEach(([k, v]) => { etat[k] = v.actif })
        setModules(etat)
      }
      if (soc) setSociete(soc)
    } catch (e) {
      setErreur(e.message||'Contexte de la société indisponible.')
      if(personnelSeul){setSociete(null);setModules({facturation:false,comptabilite:false,paie_grh:false})}
      console.error('Erreur chargement modules', e)
    } finally {
      setChargement(false)
    }
  }, [personnelSeul])

  useEffect(() => { charger() }, [charger])

  async function toggleModule(module, actif) {
    const res = await patchAvecAuth('/api/societe/modules', { module, actif })
    if (res) setModules(prev => ({ ...prev, [module]: actif }))
  }

  async function mettreAJourSociete(data) {
    const res = await patchAvecAuth('/api/societe/moi', data)
    if (res) setSociete(res)
    return res
  }

  // Helpers pratiques
  const aFacturation  = modules.facturation  === true
  const aComptabilite = modules.comptabilite === true
  const aGRH          = modules.paie_grh     === true
  const aLienFacCompta = aFacturation && aComptabilite

  return (
    <ModulesContext.Provider value={{
      modules, societe, chargement,erreur,
      aFacturation, aComptabilite, aGRH, aLienFacCompta,
      toggleModule, mettreAJourSociete, recharger: charger,
    }}>
      {children}
    </ModulesContext.Provider>
  )
}

export function useModules() {
  return useContext(ModulesContext)
}
