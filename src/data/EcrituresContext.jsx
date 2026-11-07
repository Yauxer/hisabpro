import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { useExercice } from './ExerciceContext.jsx'
import { useModules } from './ModulesContext.jsx'
import { ecrituresAPI } from '../services/api.js'

const EcrituresContext = createContext(null)

export function EcrituresProvider({ children }) {
  const { annee } = useExercice()
  const { societe } = useModules()
  const cle = `${societe?.id || ''}:${annee}`
  const cleCourante = useRef(cle)
  cleCourante.current = cle
  const versionChargement = useRef(0)
  const [cleChargee, setCleChargee] = useState(null)
  const [ecritures,  setEcritures]  = useState([])
  const [chargement, setChargement] = useState(false)
  const [erreur,     setErreur]     = useState(null)

  // Charge les écritures depuis l'API à chaque changement d'exercice
  const charger = useCallback(async () => {
    if (!societe?.id || cleCourante.current !== cle) return
    const version = ++versionChargement.current
    setChargement(true)
    setErreur(null)
    try {
      const data = await ecrituresAPI.lister(annee)
      if (version !== versionChargement.current) return
      setEcritures(data)
      setCleChargee(cle)
    } catch (e) {
      if (version !== versionChargement.current) return
      setErreur(e.message)
      setEcritures([])
      setCleChargee(cle)
    } finally {
      if (version === versionChargement.current) setChargement(false)
    }
  }, [annee, societe?.id, cle])

  useEffect(() => { charger(); return () => { versionChargement.current += 1 } }, [charger])

  async function ajouterEcriture(ecriture) {
    const nouvelle = await ecrituresAPI.creer({
      date:          ecriture.date,
      date_piece:    ecriture.date_piece || ecriture.date,
      journal:       ecriture.journal,
      libelle:       ecriture.libelle,
      reference:     ecriture.reference || '',
      est_validee:   Boolean(ecriture.est_validee),
      lignes:        ecriture.lignes.map(l => ({
        compte:   l.compte,
        libelle:  l.libelle || '',
        tiers_id: l.tiers_id || null,
        debit:    parseFloat(l.debit)  || 0,
        credit:   parseFloat(l.credit) || 0,
      })),
    })
    // Invalider les lectures commencées avant la mutation.
    await charger()
    return nouvelle
  }

  async function modifierEcriture(id, ecriture) {
    const maj = await ecrituresAPI.modifier(id, {
      date:          ecriture.date,
      date_piece:    ecriture.date_piece || ecriture.date,
      journal:       ecriture.journal,
      libelle:       ecriture.libelle,
      reference:     ecriture.reference || '',
      lignes:        ecriture.lignes.map(l => ({
        compte:   l.compte,
        libelle:  l.libelle || '',
        tiers_id: l.tiers_id || null,
        debit:    parseFloat(l.debit)  || 0,
        credit:   parseFloat(l.credit) || 0,
      })),
    })
    await charger()
    return maj
  }

  async function validerEcriture(id) {
    const r = await ecrituresAPI.valider(id)
    await charger()
    return r
  }

  async function contrepasserEcriture(id, payload = {}) {
    const r = await ecrituresAPI.contrepasser(id, payload)
    await charger()
    return r
  }

  async function validerLot(ids) {
    const r = await ecrituresAPI.validerLot(ids)
    await charger()
    return r
  }

  async function supprimerEcriture(id) {
    await ecrituresAPI.supprimer(id)
    await charger()
  }

  return (
    <EcrituresContext.Provider value={{
      ecritures: cleChargee === cle ? ecritures : [],
      chargement: chargement || cleChargee !== cle,
      erreur,
      ajouterEcriture,
      modifierEcriture,
      validerEcriture,
      contrepasserEcriture,
      validerLot,
      supprimerEcriture,
      recharger: charger,
    }}>
      {children}
    </EcrituresContext.Provider>
  )
}

export function useEcritures() {
  return useContext(EcrituresContext)
}
