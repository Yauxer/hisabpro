import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE, getToken, formatErreurAPI } from '../services/api.js'

const ExerciceContext = createContext(null)
const STORAGE_KEY = 'hisabpro_exercice'

export function ExerciceProvider({ children }) {
  const [exercices, setExercices] = useState([])
  const [annee, setAnneeState] = useState(() => {
    const memorisee = Number(localStorage.getItem(STORAGE_KEY))
    return Number.isInteger(memorisee) && memorisee > 1900 ? memorisee : new Date().getFullYear()
  })
  const [chargementExercices, setChargementExercices] = useState(true)
  const [erreurExercices, setErreurExercices] = useState('')
  const generation = useRef(0)

  const rechargerExercices = useCallback(async (anneePreferee = null) => {
    const token = getToken()
    const version = ++generation.current
    const courant = () => version === generation.current && token === getToken()
    if (!token) { setExercices([]); setChargementExercices(false); return }
    setChargementExercices(true)
    setErreurExercices('')
    try {
      const res = await fetch(`${API_BASE}/api/exercices`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!courant()) return
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail ? formatErreurAPI(body.detail) : `Impossible de charger les exercices (HTTP ${res.status}).`)
      }
      const rows = await res.json()
      if (!courant()) return
      setExercices(rows)
      setAnneeState(ancienne => {
        const preferee = Number(anneePreferee)
        const selection = Number.isInteger(preferee) && rows.some(x => x.annee === preferee)
          ? preferee
          : rows.some(x => x.annee === ancienne)
            ? ancienne
            : (rows.find(x => x.date_debut <= new Date().toISOString().slice(0, 10)
                && x.date_fin >= new Date().toISOString().slice(0, 10))
              || [...rows].reverse().find(x => x.statut === 'ouvert')
              || rows[rows.length - 1])?.annee ?? ancienne
        localStorage.setItem(STORAGE_KEY, String(selection))
        return selection
      })
    } catch (e) {
      if (!courant()) return
      setExercices([])
      setErreurExercices(e.message || 'Impossible de charger les exercices.')
      throw e
    } finally {
      if (courant()) setChargementExercices(false)
    }
  }, [])

  useEffect(() => {
    // L'erreur reste exposée par le contexte ; le chargement initial ne doit
    // pas laisser une promesse rejetée sans gestionnaire.
    rechargerExercices().catch(() => {})
    return () => { generation.current += 1 }
  }, [rechargerExercices])

  function setAnnee(valeur) {
    const n = Number(valeur)
    if (!Number.isInteger(n)) return
    setAnneeState(n)
    localStorage.setItem(STORAGE_KEY, String(n))
  }

  const exercice = useMemo(
    () => exercices.find(x => x.annee === annee) || null,
    [exercices, annee]
  )

  const triees = useMemo(() => [...exercices].sort((a, b) => a.annee - b.annee), [exercices])
  const index = triees.findIndex(x => x.annee === annee)
  const exercicePrecedent = index > 0 ? triees[index - 1] : null
  const exerciceSuivant = index >= 0 && index < triees.length - 1 ? triees[index + 1] : null

  return (
    <ExerciceContext.Provider value={{
      annee,
      setAnnee,
      exercice,
      exercices: triees,
      chargementExercices,
      erreurExercices,
      rechargerExercices,
      exercicePrecedent,
      exerciceSuivant,
    }}>
      {children}
    </ExerciceContext.Provider>
  )
}

export function useExercice() {
  return useContext(ExerciceContext)
}
