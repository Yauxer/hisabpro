import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getToken, peutEcrire, reprisesProvisionsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './ReprisesProvisions.module.css'

export default function ReprisesProvisions({ exercice }) {
  return <Panneau key={`${exercice}|${getToken()}`} exercice={exercice} />
}

function Panneau({ exercice }) {
  const navigate = useNavigate()
  const token = getToken()
  const vivant = useRef(true)
  const sequence = useRef(0)
  const faitsActuels = useRef('')
  const [ouvert, setOuvert] = useState(false)
  const [page, setPage] = useState(1)
  const [liste, setListe] = useState(null)
  const [selection, setSelection] = useState('')
  const [erreur, setErreur] = useState('')
  const [message, setMessage] = useState('')
  const [attente, setAttente] = useState(false)
  const [apercu, setApercu] = useState(null)
  const [verifie, setVerifie] = useState(false)
  const [cle, setCle] = useState(cleIdempotence)
  const [faits, setFaits] = useState({ date: '', montant: '', justification: '', reference: '', date_piece: '' })
  const [annulation, setAnnulation] = useState(null)
  const source = liste?.items.find(s => String(s.id) === selection)
  const signature = JSON.stringify([selection, faits])
  faitsActuels.current = signature
  const actuel = () => vivant.current && getToken() === token
  useEffect(() => {
    vivant.current = true
    return () => { vivant.current = false; sequence.current += 1 }
  }, [])

  async function charger(p = page) {
    const id = ++sequence.current
    setAttente(true); setErreur(''); setApercu(null); setVerifie(false)
    try {
      const data = await reprisesProvisionsAPI.lister(p)
      if (actuel() && id === sequence.current) setListe(data)
    } catch (e) { if (actuel() && id === sequence.current) setErreur(e.message) }
    finally { if (actuel() && id === sequence.current) setAttente(false) }
  }
  useEffect(() => { if (ouvert) charger(page) }, [ouvert, page])

  function modifier(nom, valeur) {
    setFaits(f => ({ ...f, [nom]: valeur })); setApercu(null); setVerifie(false)
    setCle(cleIdempotence()); setErreur(''); setMessage('')
  }
  const corps = () => ({ ...faits, reference: faits.reference || null, date_piece: faits.date_piece || null })
  async function verifier(e) {
    e.preventDefault()
    const s = signature; setAttente(true); setErreur(''); setMessage(''); setApercu(null)
    try {
      const data = await reprisesProvisionsAPI.apercu(selection, corps())
      if (actuel() && faitsActuels.current === s) setApercu({ ...data, signature: s })
    } catch (err) { if (actuel() && faitsActuels.current === s) setErreur(err.message) }
    finally { if (actuel()) setAttente(false) }
  }
  async function creer() {
    const s = signature
    if (!apercu || apercu.signature !== s || !verifie) return
    setAttente(true); setErreur(''); setMessage('')
    try {
      const data = await reprisesProvisionsAPI.creer(selection, { ...corps(), cle, empreinte: apercu.empreinte, mouvements_verifies: verifie })
      if (actuel() && faitsActuels.current === s) {
        setListe(l => ({ ...l, items: l.items.map(a => a.id === data.id ? data : a) }))
        setApercu(null); setVerifie(false); setFaits(f => ({ ...f, montant: '', justification: '' })); setCle(cleIdempotence())
        setMessage('Brouillon de reprise créé. Validez-le dans le Journal.')
      }
    } catch (err) { if (actuel() && faitsActuels.current === s) setErreur(err.message) }
    finally { if (actuel()) setAttente(false) }
  }
  async function annuler(e) {
    e.preventDefault(); const aid = selection
    setAttente(true); setErreur(''); setMessage('')
    try {
      const data = await reprisesProvisionsAPI.annuler(aid, annulation.id, { date: annulation.date, motif: annulation.motif })
      if (actuel()) {
        setListe(l => ({ ...l, items: l.items.map(a => a.id === data.id ? data : a) }))
        setAnnulation(null); setApercu(null); setVerifie(false)
        setMessage('Inverse créé en brouillon. La capacité sera libérée quand la reprise et son inverse seront tous deux validés.')
      }
    } catch (err) { if (actuel()) setErreur(err.message) }
    finally { if (actuel()) setAttente(false) }
  }

  async function exporter(format) {
    const aid = selection, s = signature
    setAttente(true); setErreur(''); setMessage('')
    try {
      const doc = await reprisesProvisionsAPI.preparation(aid)
      if (!actuel() || faitsActuels.current !== s) return
      setListe(l => ({ ...l, items: l.items.map(a => a.id === doc.source.id ? doc.source : a) }))
      setApercu(null); setVerifie(false)
      const r = await reprisesProvisionsAPI.exporter(aid, format, doc.empreinte_sha256)
      if (!r || !actuel() || faitsActuels.current !== s) return
      const url = URL.createObjectURL(r.blob), lien = document.createElement('a')
      lien.href = url; lien.download = r.filename; lien.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) { if (actuel() && faitsActuels.current === s) setErreur(err.message) }
    finally { if (actuel()) setAttente(false) }
  }

  return <details className={styles.card} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Reprises partielles de provisions</summary>
    {ouvert && <section aria-label="Reprises partielles de provisions">
      <p>Sélectionnez une dotation, y compris d’un exercice antérieur. La date saisie doit appartenir à une période ouverte. Exercice actif : {exercice}.</p>
      <div className={styles.actions}><button type="button" disabled={attente} onClick={() => charger()}>Actualiser les provisions</button>
        <button type="button" onClick={() => navigate('/journal')}>Ouvrir le Journal des reprises</button></div>
      {attente && <p role="status">Chargement…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {message && <p role="status">{message}</p>}
      {liste && <>
        <label className={styles.champ}>Dotation source
          <select aria-label="Dotation source" value={selection} disabled={attente} onChange={e => {
            setSelection(e.target.value); setApercu(null); setVerifie(false); setAnnulation(null); setErreur(''); setMessage(''); setCle(cleIdempotence())
          }}><option value="">Choisir une dotation</option>
            {liste.items.map(s => <option value={s.id} key={s.id}>{s.exercice} · {s.libelle} · {s.numero || 'Brouillon'} · {montantDecimalExact(s.dotation)} MAD</option>)}
          </select>
        </label>
        {liste.total > 20 && <nav className={styles.actions} aria-label="Pages des provisions">
          <button disabled={attente || page === 1} onClick={() => { setSelection(''); setPage(p => p - 1) }}>Précédentes</button>
          <span>Page {page} / {Math.ceil(liste.total / 20)}</span>
          <button disabled={attente || page * 20 >= liste.total} onClick={() => { setSelection(''); setPage(p => p + 1) }}>Suivantes</button>
        </nav>}
        {liste.total === 0 && <p>Aucune dotation de provision enregistrée.</p>}
      </>}
      {source && <>
        <p>Source {source.exercice} · {source.date} · {source.compte_dotation} / {source.compte_provision}</p>
        <dl className={styles.chiffres}>
          {[['Dotation initiale', source.dotation], ['Reprises validées actives', source.reprises_validees],
            ['Réservations en brouillon', source.reservations_brouillons], ['Disponible dans le registre lié', source.disponible]].map(([label, valeur]) =>
            <div key={label}><dt>{label}</dt><dd>{montantDecimalExact(valeur)} MAD</dd></div>)}
        </dl>
        <p>{source.note}</p>
        <div className={styles.actions}>
          <button type="button" disabled={attente} onClick={() => exporter('pdf')}>Télécharger le suivi PDF</button>
          <button type="button" disabled={attente} onClick={() => exporter('xlsx')}>Télécharger le suivi Excel</button>
        </div>
        {source.diagnostic && <p role="alert" className={styles.erreur}>{source.diagnostic}</p>}
        {peutEcrire() && !source.diagnostic && <form onSubmit={verifier}>
          <div className={styles.champs}>
            <label>Date de reprise<input type="date" required value={faits.date} onChange={e => modifier('date', e.target.value)} /></label>
            <label>Montant de reprise (MAD)<input type="number" step="0.01" min="0.01" required value={faits.montant} onChange={e => modifier('montant', e.target.value)} /></label>
            <label>Référence de pièce (facultative)<input maxLength={100} value={faits.reference} onChange={e => modifier('reference', e.target.value)} /></label>
            <label>Date de pièce (facultative)<input type="date" value={faits.date_piece} onChange={e => modifier('date_piece', e.target.value)} /></label>
          </div>
          <label className={styles.champ}>Justification de la reprise<textarea required maxLength={500} value={faits.justification} onChange={e => modifier('justification', e.target.value)} /></label>
          <div className={styles.actions}><button disabled={attente} type="submit">Vérifier la reprise</button></div>
          {apercu?.signature === signature && <div className={styles.resultat}>
            <p>OD · {apercu.faits.date} · Exercice {apercu.exercice}</p>
            <p>Capacité pour cette date, après réservations : {montantDecimalExact(apercu.capacite.disponible_pour_date)} MAD. Une annulation ultérieure ne finance pas une reprise antérieure.</p>
            {apercu.lignes.map(l => <p key={l.compte}>Compte {l.compte} — {l.libelle_compte} · Débit {montantDecimalExact(l.debit)} · Crédit {montantDecimalExact(l.credit)} MAD</p>)}
            <label className={styles.confirmation}><input type="checkbox" checked={verifie} onChange={e => setVerifie(e.target.checked)} />J’ai vérifié les mouvements du compte et les justificatifs de la reprise.</label>
            <div className={styles.actions}><button disabled={attente || !verifie} type="button" onClick={creer}>Créer le brouillon de reprise</button></div>
          </div>}
        </form>}
        {source.reprises.map(r => <article className={styles.reprise} key={r.id}>
          <strong>{r.numero_ecriture || `Brouillon ${r.ecriture_id}`} · {montantDecimalExact(r.montant)} MAD</strong>
          <p>{r.date} · Exercice {r.exercice} · {r.faits.faits.justification}</p>
          <p>{r.est_validee ? 'Reprise validée' : 'Reprise à valider'}{r.annulation_id ? ` · Inverse ${r.inverse_numero || r.inverse_id} ${r.inverse_validee ? 'validé' : 'à valider'}` : ''}</p>
          {r.annulation_id && <p>{r.inverse_date} · Exercice {r.inverse_exercice} · {r.motif} · {r.est_validee && r.inverse_validee ? 'Capacité libérée.' : 'Capacité maintenue jusqu’à validation des deux pièces.'}</p>}
          {peutEcrire() && !r.annulation_id && <div className={styles.actions}><button type="button" disabled={attente} onClick={() => setAnnulation({ id: r.id, date: '', motif: '' })}>Annuler la reprise {r.id}</button></div>}
        </article>)}
        {annulation && <form aria-label="Annulation de reprise" onSubmit={annuler}>
          <p>L’original sera conservé. Un inverse en brouillon sera créé ; validez les deux pièces pour libérer la capacité.</p>
          <div className={styles.champs}>
            <label>Date d’annulation<input type="date" required value={annulation.date} onChange={e => setAnnulation(a => ({ ...a, date: e.target.value }))} /></label>
            <label>Motif d’annulation<input required maxLength={500} value={annulation.motif} onChange={e => setAnnulation(a => ({ ...a, motif: e.target.value }))} /></label>
          </div>
          <div className={styles.actions}><button disabled={attente} type="submit">Créer l’inverse de reprise</button><button type="button" disabled={attente} onClick={() => setAnnulation(null)}>Fermer</button></div>
        </form>}
      </>}
    </section>}
  </details>
}
