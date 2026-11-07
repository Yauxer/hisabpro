import { useEffect, useRef, useState } from 'react'
import { avancesSalariesAPI } from '../services/api.js'
import { formatMAD, formatDate } from '../data/donnees.js'
import { InlineNotice } from './FormUX.jsx'
import styles from '../pages/CNSS.module.css'

export default function AvancesSalaries({ employes, writable }) {
  const [data, setData] = useState(null)
  const [erreur, setErreur] = useState('')
  const [charge, setCharge] = useState(true)
  const [occupe, setOccupe] = useState(false)
  const [selection, setSelection] = useState(null)
  const [employe, setEmploye] = useState('')
  const [motif, setMotif] = useState('')
  const [message, setMessage] = useState('')
  const version = useRef(0)
  const alive = useRef(false)
  async function charger() {
    const id = ++version.current
    setCharge(true); setErreur(''); setData(null)
    try { const r = await avancesSalariesAPI.lister(); if (alive.current && id === version.current) setData(r) }
    catch (e) { if (alive.current && id === version.current) setErreur(e.message) }
    finally { if (alive.current && id === version.current) setCharge(false) }
  }
  useEffect(() => { alive.current = true; charger(); return () => { alive.current = false; version.current += 1 } }, [])
  function ouvrir(row, annulation = false) {
    setSelection({ ...row, annulation }); setEmploye(''); setMotif(''); setErreur(''); setMessage('')
  }
  async function enregistrer(e) {
    e.preventDefault()
    if (occupe || !writable) return
    setOccupe(true); setErreur(''); setMessage('')
    try {
      if (selection.annulation) await avancesSalariesAPI.annuler(selection.affectation_id, motif)
      else await avancesSalariesAPI.affecter({ ligne_id: selection.ligne_id, employe_id: Number(employe), motif })
      if (!alive.current) return
      setSelection(null); setMessage('Registre mis à jour ; écriture comptable conservée.'); await charger()
    } catch (err) { if (alive.current) setErreur(err.message) }
    finally { if (alive.current) setOccupe(false) }
  }
  const candidats = selection ? employes.filter(p => p.actif || Number(selection.credit) > 0) : []
  return <section aria-label="Avances des salariés" className={styles.card}>
    <div className={styles.cardHeader}><div><h2>Avances des salariés</h2><p>Rattachement des écritures définitives du compte 3431 · Tous exercices</p></div>
      <button className={styles.btnSec} disabled={charge || occupe} onClick={charger}>Actualiser les avances</button></div>
    <div className={styles.sourceBody}>
      <InlineNotice>Les soldes concernent uniquement les mouvements affectés. Aucune retenue sur salaire ni écriture supplémentaire n’est générée. Les contrepassations doivent également être affectées explicitement.</InlineNotice>
      {erreur && <div role="alert"><InlineNotice tone="danger">{erreur}</InlineNotice></div>}
      {message && <p role="status">{message}</p>}
      {charge && <p role="status">Chargement des avances…</p>}
      {selection && <form onSubmit={enregistrer} className={styles.proofForm} aria-label={selection.annulation ? 'Annuler une affectation' : 'Affecter un mouvement'}>
        <h3>{selection.annulation ? 'Annuler une affectation' : 'Affecter un mouvement'} · {selection.numero_ecriture || `Écriture ${selection.ecriture_id}`}</h3>
        <p>{selection.libelle} · {formatDate(selection.date)} · {Number(selection.debit) > 0 ? 'Versement' : 'Récupération / remboursement'} : {formatMAD(Number(selection.debit) + Number(selection.credit))} MAD</p>
        {!selection.annulation && <div className={styles.formGroup}><label htmlFor="avance-employe">Salarié bénéficiaire</label><select id="avance-employe" required value={employe} onChange={e => setEmploye(e.target.value)} disabled={occupe}>
          <option value="">Choisir un salarié</option>{candidats.map(p => <option key={p.id} value={p.id}>{p.nom}{p.actif ? '' : ' (archivé)'}</option>)}</select></div>}
        <div className={styles.formGroup}><label htmlFor="avance-motif">Motif du rattachement ou de l’annulation</label><textarea id="avance-motif" required maxLength={500} value={motif} onChange={e => setMotif(e.target.value)} disabled={occupe} /></div>
        <div className={styles.actions}><button type="submit" className={styles.btnPrim} disabled={occupe || !motif.trim() || (!selection.annulation && !employe)}>Confirmer {selection.annulation ? 'l’annulation' : 'l’affectation'}</button>
          <button type="button" className={styles.btnSec} disabled={occupe} onClick={() => setSelection(null)}>Fermer</button></div>
      </form>}
      {data && !charge && <>
        <p><strong>{data.non_affectes} mouvement(s) non affecté(s)</strong> : leur bénéficiaire reste à justifier. Les soldes individuels peuvent être incomplets.</p>
        <h3>Soldes des mouvements affectés</h3>
        <div className={styles.tableWrapper}><table className={styles.table} aria-label="Soldes des avances"><thead><tr><th>Salarié</th><th>Versé</th><th>Récupéré / remboursé</th><th>Reste à récupérer</th></tr></thead><tbody>
          {data.soldes.map(p => <tr key={p.employe_id}><td>{p.nom}</td><td className={styles.numeric}>{formatMAD(Number(p.debit))}</td><td className={styles.numeric}>{formatMAD(Number(p.credit))}</td><td className={styles.numeric}>{formatMAD(Number(p.solde))} MAD</td></tr>)}
          {!data.soldes.length && <tr><td colSpan={4}>Aucun mouvement affecté.</td></tr>}
        </tbody></table></div>
        <h3>Mouvements comptables 3431</h3>
        <div className={styles.tableWrapper}><table className={styles.table} aria-label="Mouvements des avances"><thead><tr><th>Date / pièce</th><th>Libellé</th><th>Débit</th><th>Crédit</th><th>Salarié</th><th>Action</th></tr></thead><tbody>
          {data.mouvements.map(r => <tr key={r.ligne_id}><td>{formatDate(r.date)}<small>{r.numero_ecriture || `Écriture ${r.ecriture_id}`} · Ligne {r.ligne_id}</small></td><td>{r.libelle}{r.contrepassation_de_id && <small>Contrepassation de l’écriture {r.contrepassation_de_id}</small>}</td>
            <td className={styles.numeric}>{formatMAD(Number(r.debit))}</td><td className={styles.numeric}>{formatMAD(Number(r.credit))}</td><td>{r.nom_employe || 'À affecter'}</td>
            <td>{writable && <button className={styles.btnSec} disabled={occupe} onClick={() => ouvrir(r, !!r.affectation_id)}>{r.affectation_id ? 'Annuler le rattachement' : 'Affecter'}</button>}</td></tr>)}
          {!data.mouvements.length && <tr><td colSpan={6}>Aucune ligne 3431 définitive.</td></tr>}
        </tbody></table></div>
        <details className={styles.proofHistory}><summary>Historique des affectations ({data.historique.length})</summary><ul>{data.historique.map(a => <li key={a.id}>
          Ligne {a.ligne_id} · {a.nom_employe} · {a.motif} · Auteur {a.created_by} · {formatDate(a.created_at)}
          {a.annule_at && <p>Annulée par {a.annule_par} le {formatDate(a.annule_at)} : {a.motif_annulation}</p>}
        </li>)}</ul></details>
      </>}
    </div>
  </section>
}
