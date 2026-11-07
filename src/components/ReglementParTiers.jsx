import { useEffect, useMemo, useRef, useState } from 'react'
import Modal from './Modal.jsx'
import { API_BASE, getToken, facturesAPI, formatErreurAPI } from '../services/api.js'
import { dateLocaleISO } from '../utils/formUtils.js'
import { formatMAD } from '../data/donnees.js'
import styles from '../pages/Commercial.module.css'

// getRandomValues reste disponible pour une installation locale en réseau.
function nouvelleOperation() {
  const b = crypto.getRandomValues(new Uint8Array(16))
  b[6] = (b[6] & 15) | 64
  b[8] = (b[8] & 63) | 128
  const h = [...b].map(v => v.toString(16).padStart(2, '0')).join('')
  return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`
}

// Un montant saisi est un nombre entier de centimes, sans arrondi silencieux.
function centimes(texte) {
  if (texte === '') return 0
  const valeur = String(texte).replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(valeur)) return null
  const [entier, fraction = ''] = valeur.split('.')
  const n = Number(entier)*100 + Number(fraction.padEnd(2, '0'))
  return Number.isSafeInteger(n) ? n : null
}

export default function ReglementParTiers({ annee, typeForce, onFermer, onSuccess }) {
  const [factures, setFactures] = useState([])
  const [tiersId, setTiersId] = useState('')
  const [situations, setSituations] = useState({})
  const [ventilations, setVentilations] = useState({})
  const [chargement, setChargement] = useState(true)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const [form, setForm] = useState({ date: dateLocaleISO(), montant: '', mode: 'virement', reference: '', banque: '', notes: '' })
  const [banques, setBanques] = useState([])
  const operation = useRef(nouvelleOperation())
  const token = useRef(getToken())

  async function requete(url, body) {
    if (getToken() !== token.current) throw new Error('La société active a changé. Fermez et rouvrez le formulaire.')
    const r = await fetch(API_BASE+url, {
      method: body ? 'POST' : 'GET',
      headers: { Authorization: `Bearer ${token.current}`, 'Content-Type': 'application/json' },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
    if (getToken() !== token.current) throw new Error('La société active a changé. Rechargez les données.')
    const data = await r.json()
    if (!r.ok) throw new Error(formatErreurAPI(data.detail))
    return data
  }

  useEffect(() => {
    let ferme = false
    Promise.all([facturesAPI.listerTout(annee), requete('/api/banques')])
      .then(([f, b]) => { if (!ferme) { setFactures(f); setBanques(b) } })
      .catch(e => { if (!ferme) setErreur(e.message) })
      .finally(() => { if (!ferme) setChargement(false) })
    return () => { ferme = true }
  }, [annee])

  const admissibles = useMemo(() => factures.filter(f => f.type === typeForce && f.est_validee
    && !f.est_proforma && f.tiers_id && f.montants_valides !== false && f.statut !== 'payee'), [factures, typeForce])
  const tiers = useMemo(() => [...new Map(admissibles.map(f => [String(f.tiers_id), f.tiers])).entries()], [admissibles])
  const ouvertes = useMemo(() => admissibles.filter(f => String(f.tiers_id) === tiersId), [admissibles, tiersId])

  useEffect(() => {
    let ferme = false
    setVentilations({}); setSituations({}); setErreur('')
    operation.current = nouvelleOperation()
    if (!tiersId) return
    setChargement(true)
    Promise.all(ouvertes.map(async f => [f.id, await requete(`/api/factures/${f.id}/reglements`)]))
      .then(rows => { if (!ferme) setSituations(Object.fromEntries(rows)) })
      .catch(e => { if (!ferme) setErreur(e.message) })
      .finally(() => { if (!ferme) setChargement(false) })
    return () => { ferme = true }
  }, [tiersId, ouvertes])

  function modifier(champ, valeur) {
    operation.current = nouvelleOperation()
    setForm(p => ({ ...p, [champ]: valeur }))
  }
  const lignes = ouvertes.filter(f => situations[f.id]?.solde_restant > 0)
  const montants = lignes.map(f => centimes(ventilations[f.id] || ''))
  const total = centimes(form.montant)
  const somme = montants.some(m => m === null) ? null : montants.reduce((s, m) => s+m, 0)
  const selection = lignes.filter((f, i) => montants[i] > 0)
  const depasse = lignes.some((f, i) => montants[i] > Math.round(situations[f.id].solde_restant*100))
  const inconnu = ouvertes.some(f => !Number.isFinite(situations[f.id]?.solde_restant))
  const possible = !chargement && !envoi && !inconnu && !depasse && total > 0 && somme === total && selection.length > 0 && selection.length <= 50

  async function enregistrer(e) {
    e.preventDefault()
    if (!possible) return
    setEnvoi(true); setErreur('')
    try {
      await requete('/api/reglements/par-tiers', {
        operation_id: operation.current, tiers_id: Number(tiersId), date: form.date,
        montant: total/100, mode: form.mode, reference: form.reference || null,
        banque: form.banque || null, notes: form.notes || null,
        ventilations: selection.map(f => ({ facture_id: f.id, montant: centimes(ventilations[f.id])/100 })),
      })
      onSuccess(); onFermer()
    } catch (err) { setErreur(err.message) }
    finally { setEnvoi(false) }
  }

  return <Modal titre="Règlement par tiers" icone="ti-coin" largeur="lg" onFermer={() => { if (!envoi) onFermer() }}>
    <form className={styles.formContenu} onSubmit={enregistrer}>
      <p>Répartissez un paiement entre les factures du même {typeForce === 'vente' ? 'client' : 'fournisseur'}. Chaque montant conserve son règlement et son écriture. Les lignes partagent la référence du paiement.</p>
      <p>Chèques et effets : utilisez le règlement individuel et son cycle de suivi.</p>
      {erreur && <div className={styles.erreurForm} role="alert">{erreur}</div>}
      {factures.some(f => f.type === typeForce && f.montants_valides === false) && <p role="status">Les factures dont les montants sont à vérifier ne sont pas proposées.</p>}
      <label className={styles.label}>{typeForce === 'vente' ? 'Client' : 'Fournisseur'}
        <select className={styles.input} value={tiersId} onChange={e => setTiersId(e.target.value)} disabled={envoi} required>
          <option value="">Choisir un tiers</option>
          {tiers.map(([id, nom]) => <option key={id} value={id}>{nom}</option>)}
        </select>
      </label>
      <div className={styles.formRow}>
        <label className={styles.label}>Date du paiement<input className={styles.input} type="date" value={form.date} disabled={envoi} onChange={e => modifier('date', e.target.value)} required /></label>
        <label className={styles.label}>Montant du paiement (MAD)<input className={styles.input} type="number" step="0.01" min="0.01" value={form.montant} disabled={envoi} onChange={e => modifier('montant', e.target.value)} required /></label>
      </div>
      <div className={styles.formRow}>
        <label className={styles.label}>Mode<select className={styles.input} value={form.mode} disabled={envoi} onChange={e => modifier('mode', e.target.value)}>
          {Object.entries({ virement: 'Virement', especes: 'Espèces', carte: 'Carte', prelevement: 'Prélèvement', autre: 'Autre' }).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select></label>
        <label className={styles.label}>Banque<select className={styles.input} value={form.banque} disabled={envoi} onChange={e => modifier('banque', e.target.value)}>
          <option value="">Compte de trésorerie par défaut</option>
          {banques.filter(b => b.actif !== false).map(b => <option key={b.id} value={b.banque}>{b.banque}</option>)}
        </select></label>
      </div>
      <label className={styles.label}>Référence du paiement<input className={styles.input} maxLength={100} value={form.reference} disabled={envoi} onChange={e => modifier('reference', e.target.value)} /></label>
      {chargement && <p role="status">Chargement des soldes…</p>}
      {!chargement && tiersId && lignes.length === 0 && <p>Aucune facture à régler pour ce tiers.</p>}
      {lignes.map(f => <label key={f.id} className={styles.label} style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{f.numero} — reste {formatMAD(situations[f.id].solde_restant)} MAD</span>
        <input aria-label={`Montant pour ${f.numero}`} className={styles.input} style={{ width: 150, maxWidth: '100%' }} type="number" step="0.01" min="0" max={situations[f.id].solde_restant} disabled={envoi} value={ventilations[f.id] || ''} onChange={e => { operation.current = nouvelleOperation(); setVentilations(v => ({ ...v, [f.id]: e.target.value })) }} />
      </label>)}
      <p role="status">Total ventilé : {somme === null ? 'À vérifier' : formatMAD(somme/100)} MAD. Reste à ventiler : {total === null || somme === null ? 'À vérifier' : formatMAD((total-somme)/100)} MAD.</p>
      {depasse && <p role="alert">Une ventilation dépasse le solde de sa facture.</p>}
      {selection.length > 50 && <p role="alert">Sélectionnez au maximum50factures par opération.</p>}
      <label className={styles.label}>Notes<textarea className={styles.input} value={form.notes} disabled={envoi} onChange={e => modifier('notes', e.target.value)} /></label>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'wrap' }}>
        <button className={styles.btnSec} type="button" disabled={envoi} onClick={onFermer}>Fermer</button>
        <button className={styles.btnPrim} type="submit" disabled={!possible}>{envoi ? 'Enregistrement…' : 'Enregistrer la ventilation'}</button>
      </div>
    </form>
  </Modal>
}
