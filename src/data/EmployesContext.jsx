import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { API_BASE, getToken, formatErreurAPI } from '../services/api.js'
import { useExercice } from './ExerciceContext.jsx'
import { useModules } from './ModulesContext.jsx'

const EmployesContext = createContext(null)

async function requete(path, method = 'GET', body) {
  const token = getToken()
  if (!token) throw new Error('Session expirée : reconnectez-vous.')
  const response = await fetch(`${API_BASE}/api/employes${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(formatErreurAPI(data.detail || `Erreur HTTP ${response.status}`))
  }
  return response.status === 204 ? null : response.json()
}

export function EmployesProvider({ children }) {
  const { annee } = useExercice()
  const { societe } = useModules()
  const [mois, setMois] = useState(new Date().getMonth() + 1)
  const [employes, setEmployes] = useState([])
  const [chargement, setChargement] = useState(false)
  const [cotisations, setCotisations] = useState(null)
  const [erreur, setErreur] = useState('')
  const [erreurCalcul, setErreurCalcul] = useState('')
  const [conges, setConges] = useState([])
  const [erreurConges, setErreurConges] = useState('')
  const [referentiel, setReferentiel] = useState(null)
  const [erreurReferentiel, setErreurReferentiel] = useState('')
  const [accesPersonnel, setAccesPersonnel] = useState(null)
  const [erreurAcces, setErreurAcces] = useState('')
  const generation = useRef(0)
  const societeId = societe?.id
  const scopeReferentiel = `${societeId}:${annee}`
  const scopeReferentielCourant = useRef(scopeReferentiel)
  scopeReferentielCourant.current = scopeReferentiel

  const charger = useCallback(async () => {
    const numero = ++generation.current
    setEmployes([])
    setCotisations(null)
    setErreur('')
    setErreurCalcul('')
    setConges([])
    setErreurConges('')
    setReferentiel(null)
    setErreurReferentiel('')
    setAccesPersonnel(null)
    setErreurAcces('')
    if (!societeId) { setChargement(false); return }
    setChargement(true)
    const resultats = await Promise.allSettled([
      requete('?inclure_archives=true'),
      requete(`/cotisations?annee=${annee}&mois=${mois}`),
      requete('/conges'),
      requete(`/referentiel?annee=${annee}`),
      requete('/securite/acces'),
    ])
    if (numero !== generation.current) return
    if (resultats[0].status === 'fulfilled') setEmployes(resultats[0].value)
    else setErreur(resultats[0].reason.message)
    if (resultats[1].status === 'fulfilled') setCotisations(resultats[1].value)
    else setErreurCalcul(resultats[1].reason.message)
    if (resultats[2].status === 'fulfilled') setConges(resultats[2].value)
    else setErreurConges(resultats[2].reason.message)
    if (resultats[3].status === 'fulfilled') setReferentiel(resultats[3].value)
    else setErreurReferentiel(resultats[3].reason.message)
    if (resultats[4].status === 'fulfilled') setAccesPersonnel(resultats[4].value)
    else setErreurAcces(resultats[4].reason.message)
    setChargement(false)
  }, [societeId, annee, mois])

  useEffect(() => {
    scopeReferentielCourant.current = scopeReferentiel
    charger()
    return () => { generation.current += 1; scopeReferentielCourant.current = null }
  }, [charger])

  async function ajouterEmploye(employe) {
    const nouvel = await requete('', 'POST', employe)
    await charger()
    return nouvel
  }
  async function modifierEmploye(id, employe) {
    const resultat = await requete(`/${id}`, 'PUT', employe)
    await charger()
    return resultat
  }
  async function supprimerEmploye(id) {
    await requete(`/${id}`, 'DELETE')
    await charger()
  }
  async function demanderConge(donnees) {
    const resultat = await requete('/conges', 'POST', donnees)
    await charger()
    return resultat
  }
  async function deciderConge(id, donnees) {
    const resultat = await requete(`/conges/${id}`, 'PATCH', donnees)
    await charger()
    return resultat
  }

  async function consignerReferentiel(donnees) {
    if (scopeReferentiel !== scopeReferentielCourant.current) return null
    const numero = generation.current
    const resultat = await requete(`/referentiel?annee=${annee}`, 'POST', donnees)
    if (numero !== generation.current || scopeReferentiel !== scopeReferentielCourant.current) return null
    setReferentiel(resultat)
    setErreurReferentiel('')
    return resultat
  }

  return <EmployesContext.Provider value={{ employes, cotisations, chargement, erreur,
    erreurCalcul, mois, setMois, annee, ajouterEmploye, modifierEmploye,
    supprimerEmploye, conges, erreurConges, demanderConge, deciderConge,
    referentiel, erreurReferentiel, consignerReferentiel, accesPersonnel, erreurAcces,
    recharger: charger }}>{children}</EmployesContext.Provider>
}

export function useEmployes() { return useContext(EmployesContext) }
