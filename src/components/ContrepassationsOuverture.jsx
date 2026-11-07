import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { clotureContrepassationsAPI, getToken } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './ContrepassationsOuverture.module.css'

export default function ContrepassationsOuverture({ exercice }) {
  const navigate = useNavigate()
  const token = getToken()
  const [page, setPage] = useState(1)
  const [donnees, setDonnees] = useState(null)
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)
  const [actualisation, setActualisation] = useState(0)
  const generation = useRef(0)
  const cle = `${exercice}|${token}|${page}`
  const courante = useRef(cle)
  courante.current = cle
  const actuel = donnees?.cle === cle ? donnees.data : null
  useEffect(() => { setPage(1) }, [exercice, token])
  useEffect(() => {
    const id = ++generation.current
    setChargement(true); setErreur(''); setDonnees(null)
    clotureContrepassationsAPI.lister(exercice, page).then(data => {
      if (generation.current === id && courante.current === cle && getToken() === token) setDonnees({ cle, data })
    }).catch(e => {
      if (generation.current === id && courante.current === cle) setErreur(e.message)
    }).finally(() => { if (generation.current === id) setChargement(false) })
    return () => { generation.current += 1 }
  }, [cle, actualisation])

  return <section className={styles.card} aria-label="Contrepassations d’ouverture">
    <div className={styles.entete}>
      <h2>Contrepassations d’ouverture</h2>
      <button type="button" disabled={chargement} onClick={() => setActualisation(v => v + 1)}>Actualiser les contrepassations</button>
    </div>
    <p>Écritures liées aux ajustements d’inventaire et datées dans l’exercice {exercice}. Vérifiez la source et validez dans le Journal.</p>
    {chargement && <p role="status">Chargement des contrepassations…</p>}
    {erreur && <p role="alert">{erreur}</p>}
    {actuel && <>
      <p className={styles.totaux}>{actuel.total} liée(s) · {actuel.a_valider} à valider · {actuel.validees} validée(s)</p>
      {actuel.total === 0 && <p>Aucune contrepassation liée dans cet exercice.</p>}
      {actuel.items.map(e => <article className={styles.ligne} key={e.id}>
        <div className={styles.entete}><strong>{e.reference || e.numero || `Écriture ${e.id}`}</strong><span>{e.est_validee ? 'Validée' : 'À valider'}</span></div>
        <div>{e.date} · {e.journal} · {e.type.toUpperCase()}</div>
        <p>{e.libelle}</p>
        <div>Source {e.source_exercice} : {e.source_reference || e.source_numero || `Écriture ${e.source_id}`} · {e.source_date}</div>
        {!e.source_validee && <p className={styles.alerte}>Source encore en brouillon : à vérifier avant validation.</p>}
        <div>Débit {montantDecimalExact(e.debit)} MAD · Crédit {montantDecimalExact(e.credit)} MAD</div>
        {!e.equilibree && <p className={styles.alerte}>À vérifier : montants incomplets ou écriture déséquilibrée.</p>}
      </article>)}
      {actuel.total > 20 && <nav className={styles.entete} aria-label="Pages des contrepassations">
        <button type="button" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Précédentes</button>
        <span>Page {page} / {Math.ceil(actuel.total / 20)}</span>
        <button type="button" disabled={page * 20 >= actuel.total} onClick={() => setPage(p => p + 1)}>Suivantes</button>
      </nav>}
    </>}
    <button type="button" onClick={() => navigate('/journal')}>Ouvrir le Journal des contrepassations</button>
  </section>
}
