import { useEffect, useRef, useState } from 'react'
import { getToken, peutEcrire, rasRapprochementsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './RasTvaRegistre.module.css'

const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

export default function RasTvaRapprochement({ captureId }) {
  const token = getToken(), vivant = useRef(true), sequence = useRef(0), cle = useRef(null)
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [options, setOptions] = useState(null), [erreur, setErreur] = useState(''), [attente, setAttente] = useState(false)
  const [recherche, setRecherche] = useState(''), [piece, setPiece] = useState(''), [montant, setMontant] = useState('')
  const [confirme, setConfirme] = useState(false), [retrait, setRetrait] = useState(null), [motif, setMotif] = useState('')
  const ecriture = peutEcrire()
  const actuel = n => vivant.current && sequence.current === n && getToken() === token
  useEffect(() => { vivant.current = true; return () => { vivant.current = false; sequence.current += 1 } }, [])
  useEffect(() => {
    if (ouvert) charger()
    return () => { sequence.current += 1 }
  }, [ouvert])

  async function charger() {
    const n = ++sequence.current
    setAttente(true); setErreur(''); setData(null); setOptions(null)
    try {
      const [d, choix] = await Promise.all([rasRapprochementsAPI.lire(captureId),
        ecriture ? rasRapprochementsAPI.options(captureId, recherche) : Promise.resolve(null)])
      if (actuel(n)) { setData(d); setOptions(choix) }
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function chercher(page = 1) {
    const n = ++sequence.current
    setAttente(true); setErreur(''); setOptions(null); setPiece(''); cle.current = null
    try { const d = await rasRapprochementsAPI.options(captureId, recherche, page); if (actuel(n)) setOptions(d) }
    catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function creer(e) {
    e.preventDefault()
    const n = ++sequence.current
    setAttente(true); setErreur('')
    try {
      cle.current ||= cleIdempotence()
      const d = await rasRapprochementsAPI.creer(captureId, { ecriture_id: Number(piece),
        montant: montant.trim().replace(',', '.'), cle: cle.current, rapprochement_verifie: confirme })
      if (!actuel(n)) return
      setData(d); setMontant(''); setPiece(''); setConfirme(false); cle.current = null
      const choix = await rasRapprochementsAPI.options(captureId, recherche)
      if (actuel(n)) setOptions(choix)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function retirer(e) {
    e.preventDefault()
    const n = ++sequence.current
    setAttente(true); setErreur('')
    try {
      const d = await rasRapprochementsAPI.retirer(captureId, retrait, motif)
      if (!actuel(n)) return
      setData(d); setRetrait(null); setMotif('')
      const choix = await rasRapprochementsAPI.options(captureId, recherche)
      if (actuel(n)) setOptions(choix)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function exporter() {
    const n = ++sequence.current
    setAttente(true); setErreur('')
    try {
      const fichier = await rasRapprochementsAPI.pdf(captureId)
      if (!fichier || !actuel(n)) return
      const url = URL.createObjectURL(fichier.blob)
      const lien = document.createElement('a'); lien.href = url; lien.download = fichier.filename; lien.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  return <details className={styles.documents} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Rapprochement comptable d’un versement</summary>
    {ouvert && <section aria-label={`Rapprochements de la capture ${captureId}`}>
      <div className={styles.actions}><button type="button" disabled={attente} onClick={charger}>Actualiser les rapprochements</button></div>
      {attente && <p role="status">Chargement du rapprochement…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {data && <>
        <p>{data.note}</p>
        <p>Les exports annuels du registre n’intègrent pas ces rapprochements. Leur état documentaire se télécharge séparément.</p>
        <div className={styles.actions}><button type="button" disabled={attente} onClick={exporter}>PDF des rapprochements documentaires</button></div>
        {data.capture_annulee && <p role="alert">Capture annulée : rapprochez les pièces et retirez les liens devenus incorrects. Aucun retrait automatique.</p>}
        <p>Montant rapproché : {argent(data.total_rapproche)} · Capacité documentaire non rapprochée : {argent(data.capacite_documentaire)}</p>
        <ul className={styles.rapprochements}>{data.items.map(r => <li key={r.id}>
          <strong>{r.retire_le ? 'Retiré' : 'Actif'} · {argent(r.montant)}</strong>
          <p>Pièce {r.faits.piece.numero_ecriture || `#${r.ecriture_id}`} · {r.faits.piece.reference || 'Sans référence'} · date comptable {r.faits.piece.date}</p>
          <p>Compte rapproché : {r.faits.capture.compte_destination} · créé le {r.created_at.slice(0, 10)} par l’utilisateur #{r.created_by}</p>
          <p className={styles.empreinte}>Empreinte du rapprochement : {r.empreinte_sha256}</p>
          {r.diagnostics.map(d => <p role="alert" key={d}>{d}</p>)}
          {r.retire_le && <p>Retrait du {r.retire_le.slice(0, 10)} par l’utilisateur #{r.retire_par} : {r.motif_retrait}</p>}
          {ecriture && !r.retire_le && <div className={styles.actions}><button type="button" disabled={attente} onClick={() => { setRetrait(r.id); setMotif('') }}>Retirer le rapprochement #{r.id}</button></div>}
        </li>)}</ul>
        {!data.items.length && <p>Aucun rapprochement documentaire enregistré.</p>}
        {ecriture && retrait && <form onSubmit={retirer} className={styles.formRapprochement}>
          <label>Motif du retrait<input aria-label="Motif du retrait" required maxLength={500} value={motif} onChange={e => setMotif(e.target.value)} disabled={attente} /></label>
          <div className={styles.actions}><button disabled={attente || !motif.trim()}>Confirmer le retrait documentaire</button><button type="button" disabled={attente} onClick={() => setRetrait(null)}>Conserver le rapprochement</button></div>
        </form>}
        {ecriture && !data.capture_annulee && data.od_validee && <>
          <p>Choisir une pièce déjà validée avec débit du compte {data.compte_destination} et crédit de trésorerie. Créez et validez d’abord la pièce dans le Journal si elle n’existe pas. Sa date comptable n’est pas présumée être la date effective du versement.</p>
          <div className={styles.actions}>
            <label>Référence de la pièce à chercher<input aria-label="Référence de la pièce à chercher" maxLength={100} value={recherche} onChange={e => setRecherche(e.target.value)} disabled={attente} /></label>
            <button type="button" disabled={attente} onClick={() => chercher()}>Chercher une pièce validée</button>
          </div>
          {options && <>
            <form onSubmit={creer} className={styles.formRapprochement}>
              <label>Pièce comptable validée<select aria-label="Pièce comptable validée" value={piece} required disabled={attente} onChange={e => { setPiece(e.target.value); cle.current = null; setConfirme(false) }}>
                <option value="">Sélectionner une pièce</option>
                {options.items.map(o => <option key={o.id} value={o.id} disabled={o.disponible === '0.00'}>{o.date_comptable} · {o.numero_ecriture || `#${o.id}`} · {o.reference || 'Sans référence'} · disponible {argent(o.disponible)}</option>)}
              </select></label>
              {!options.items.length && <p>Aucune pièce correspondant à cette recherche.</p>}
              <label>Montant à rapprocher MAD<input aria-label="Montant à rapprocher MAD" inputMode="decimal" required value={montant} disabled={attente} onChange={e => { setMontant(e.target.value); cle.current = null; setConfirme(false) }} /></label>
              <label className={styles.confirmation}><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} />Je confirme ce rapprochement documentaire de la pièce sélectionnée, sans présumer de validation fiscale.</label>
              <div className={styles.actions}><button disabled={attente || !piece || !montant || !confirme}>Enregistrer le rapprochement documentaire</button></div>
            </form>
            <div className={styles.actions}>
              <button type="button" disabled={attente || options.page === 1} onClick={() => chercher(options.page - 1)}>Pièces précédentes</button>
              <span>Page {options.page}</span>
              <button type="button" disabled={attente || !options.suivante} onClick={() => chercher(options.page + 1)}>Pièces suivantes</button>
            </div>
          </>}
        </>}
      </>}
    </section>}
  </details>
}
