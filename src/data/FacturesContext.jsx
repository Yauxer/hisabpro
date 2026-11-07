import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { useExercice } from './ExerciceContext.jsx'
import { useModules } from './ModulesContext.jsx'
import { API_BASE, facturesAPI } from '../services/api.js'

const FacturesContext = createContext(null)

export function FacturesProvider({ children }) {
  const { annee } = useExercice()
  const { societe } = useModules()
  const cle = `${societe?.id || ''}:${annee}`
  const cleCourante = useRef(cle)
  cleCourante.current = cle
  const [cleChargee, setCleChargee] = useState(null)
  const versionChargement = useRef(0)
  const [factures,   setFactures]   = useState([])
  const [chargement, setChargement] = useState(false)
  const [erreur,     setErreur]     = useState(null)

  const charger = useCallback(async () => {
    if (!societe?.id || cleCourante.current !== cle) return
    const version = ++versionChargement.current
    setChargement(true)
    setErreur(null)
    try {
      const data = await facturesAPI.listerTout(annee)
      if (version !== versionChargement.current) return
      setFactures(data)
      setCleChargee(cle)
    } catch (e) {
      if (version !== versionChargement.current) return
      setErreur(e.message)
      setFactures([])
      setCleChargee(cle)
    } finally {
      if (version === versionChargement.current) setChargement(false)
    }
  }, [annee, societe?.id, cle])

  useEffect(() => { charger(); return () => { versionChargement.current += 1 } }, [charger])

  async function ajouterFacture(facture) {
    const nouvelle = await facturesAPI.creer(facture)
    // La nouvelle lecture invalide les réponses commencées avant la mutation.
    await charger()
    return nouvelle
  }

  async function mettreAJourFacture(id, data) {
    await facturesAPI.mettreAJour(id, data)
    await charger()
  }


  async function validerFacture(id) {
    const token = localStorage.getItem('hisabpro_token')
    const res = await fetch(`${API_BASE}/api/factures/${id}/valider`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Impossible de valider la facture')
    await charger()
    return data
  }

  async function comptabiliserFacture(id) {
    const token = localStorage.getItem('hisabpro_token')
    const res = await fetch(`${API_BASE}/api/factures/${id}/comptabiliser`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Erreur' }))
      throw new Error(err.detail)
    }
    await charger()
    return res.json()
  }

  async function supprimerFacture(id) {
    await facturesAPI.supprimer(id)
    await charger()
  }

  return (
    <FacturesContext.Provider value={{
      factures: cleChargee === cle ? factures : [],
      chargement: chargement || cleChargee !== cle,
      erreur,
      ajouterFacture,
      mettreAJourFacture,
      supprimerFacture,
      validerFacture,
      comptabiliserFacture,
      recharger: charger,
    }}>
      {children}
    </FacturesContext.Provider>
  )
}

export function useFactures() {
  return useContext(FacturesContext)
}
