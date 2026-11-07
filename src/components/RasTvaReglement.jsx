import { useEffect, useId, useRef, useState } from 'react'
import { API_BASE, formatErreurAPI, getToken } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import RasTvaAssistant from './RasTvaAssistant.jsx'
import styles from './RasTvaAssistant.module.css'

async function api(chemin, token, donnees) {
  const r = await fetch(`${API_BASE}${chemin}`, {
    method: donnees ? 'POST' : 'GET',
    headers: { Authorization: `Bearer ${token}`, ...(donnees ? { 'Content-Type': 'application/json' } : {}) },
    ...(donnees ? { body: JSON.stringify(donnees) } : {}),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(formatErreurAPI(data.detail || `Erreur HTTP ${r.status}`))
  return data
}

export default function RasTvaReglement({ reglement, comptes = [], consultation = false, onSuccess, onOccupation }) {
  const [etat, setEtat] = useState(null)
  const [erreur, setErreur] = useState('')
  const [simulation, setSimulation] = useState(null)
  const [form, setForm] = useState({ justification_quote_part: '', reference: '', compte_destination: '' })
  const [apercu, setApercu] = useState(null)
  const [confirme, setConfirme] = useState(false)
  const [chargement, setChargement] = useState('')
  const generation = useRef(0)
  const monte = useRef(false)
  const id = useId()
  const token = getToken()
  const signature = JSON.stringify([simulation?.simulation, form, reglement.id, token])
  const courante = useRef(signature)
  courante.current = signature
  const courant = apercu?.signature === signature ? apercu : null
  useEffect(() => {
    monte.current = true
    let annule = false
    setEtat(null); setErreur('')
    api(`/api/reglements/${reglement.id}/ras-tva`, token)
      .then(data => { if (!annule && getToken() === token) setEtat(data) })
      .catch(e => { if (!annule && getToken() === token) setErreur(e.message) })
    return () => { annule = true; monte.current = false; generation.current += 1 }
  }, [reglement.id, token])
  useEffect(() => {
    generation.current += 1
    setConfirme(false); setChargement(''); setErreur('')
  }, [signature])
  const changer = (cle, valeur) => setForm(f => ({ ...f, [cle]: valeur }))

  async function preparer(e) {
    e.preventDefault()
    if (simulation?.resultat.statut !== 'calcule') return
    const numero = ++generation.current, cle = signature
    setChargement('apercu'); setErreur(''); setApercu(null); setConfirme(false)
    try {
      const data = await api(`/api/reglements/${reglement.id}/ras-tva/apercu`, token, {
        simulation: simulation.simulation, justification_quote_part: form.justification_quote_part,
      })
      if (monte.current && getToken() === token && numero === generation.current && cle === courante.current) setApercu({ ...data, signature: cle })
    } catch (e) {
      if (monte.current && getToken() === token && numero === generation.current && cle === courante.current) setErreur(e.message)
    } finally { if (monte.current && numero === generation.current) setChargement('') }
  }

  async function capturer() {
    if (!courant || !confirme || chargement || getToken() !== token) return
    setChargement('capture'); setErreur('')
    onOccupation?.(true)
    try {
      await api(`/api/reglements/${reglement.id}/ras-tva`, token, {
        ...form, simulation: simulation.simulation,
        empreinte_apercu: courant.empreinte_apercu, pieces_verifiees: true,
      })
      if (monte.current && getToken() === token) onSuccess?.()
    } catch (e) {
      if (monte.current && getToken() === token) { setErreur(e.message); setApercu(null); setConfirme(false) }
    } finally {
      if (getToken() === token) onOccupation?.(false)
      if (monte.current && getToken() === token) setChargement('')
    }
  }

  const dossier = etat?.dossier
  return <fieldset disabled={chargement === 'capture'} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}><section aria-label="Raccordement RAS TVA au règlement" style={{ display: 'grid', gap: 14, minWidth: 0 }}>
    {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
    {!etat && !erreur && <p>Chargement du dossier RAS TVA…</p>}
    {etat && !etat.disponible && !consultation && <p role="alert">RAS TVA guidée indisponible : migration {etat.migration_requise} à appliquer par votre administrateur. Cet écran n’exécute aucune migration.</p>}
    {dossier && <section aria-label="Dossier RAS TVA conservé" className={styles.resultat}>
      <strong>Dossier RAS TVA conservé</strong>
      <p>Faits déclarés sur pièces · {dossier.faits.date_paiement} · CGI 2026, article 117-V-b</p>
      <dl className={styles.chiffres}>
        <dt>Quote-part TTC avant retenue</dt><dd>{montantDecimalExact(dossier.faits.montant_paiement_ttc)} MAD</dd>
        <dt>TVA de la quote-part</dt><dd>{montantDecimalExact(dossier.faits.tva_paiement)} MAD</dd>
        <dt>RAS TVA · {dossier.simulation.taux_retenue_tva} %</dt><dd>{montantDecimalExact(dossier.simulation.retenue_tva)} MAD</dd>
        <dt>Net du règlement</dt><dd>{montantDecimalExact(dossier.simulation.net_apres_cette_ras_tva)} MAD</dd>
      </dl>
      <p>Ventilation : {dossier.justification_quote_part}</p>
      {dossier.faits.attestation === 'presentee' && <p>Attestation déclarée : {dossier.faits.reference_attestation} · {dossier.faits.date_attestation}</p>}
      <p>Historique conservé même après annulation. Le statut de la capture et de son OD figure ci-dessus.</p>
    </section>}
    {etat?.disponible && !dossier && !consultation && <>
      <p className={styles.aide}>Règlement réel : {montantDecimalExact(String(reglement.montant))} MAD, daté du {reglement.date}. Renseignez les faits fiscaux et la quote-part avant retenue ; le net doit correspondre à ce règlement.</p>
      <RasTvaAssistant key={reglement.id} annee={Number(reglement.date.slice(0, 4))} datePaiement={reglement.date} onSimulation={setSimulation} />
      <form onSubmit={preparer} style={{ display: 'grid', gap: 14 }}>
        <fieldset disabled={chargement === 'capture'} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
          <div className={styles.grille}>
            <div className={styles.champ}><label htmlFor={`${id}-justification`}>Justificatif de ventilation TVA</label><input id={`${id}-justification`} required maxLength={200} value={form.justification_quote_part} onChange={e => changer('justification_quote_part', e.target.value)} /></div>
            <div className={styles.champ}><label htmlFor={`${id}-reference`}>Référence RAS TVA</label><input id={`${id}-reference`} required maxLength={100} value={form.reference} onChange={e => changer('reference', e.target.value)} /></div>
            <div className={styles.champ}><label htmlFor={`${id}-compte`}>Compte destination RAS TVA</label><select id={`${id}-compte`} required value={form.compte_destination} onChange={e => changer('compte_destination', e.target.value)}>
              <option value="">Choisir explicitement un compte justifié</option>
              {comptes.map(c => <option key={c.numero} value={c.numero}>{c.numero} — {c.libelle}</option>)}
            </select></div>
          </div>
        </fieldset>
        <button className={styles.bouton} type="submit" disabled={simulation?.resultat.statut !== 'calcule' || Boolean(chargement)}>{chargement === 'apercu' ? 'Vérification…' : 'Vérifier le règlement et afficher l’aperçu'}</button>
      </form>
      {courant && <section aria-label="Aperçu de la capture RAS TVA" className={styles.resultat}>
        <strong>Rapprochement vérifié sur le règlement</strong>
        <p>RAS TVA : {montantDecimalExact(courant.dossier.simulation.retenue_tva)} MAD · net : {montantDecimalExact(courant.dossier.simulation.net_apres_cette_ras_tva)} MAD</p>
        <p>OD à contrôler puis valider dans le Journal. Compte choisi : {form.compte_destination}. Aucun reversement ni déclaration généré.</p>
        <label style={{ display: 'flex', gap: 8, alignItems: 'start', marginBottom: 12 }}><input type="checkbox" checked={confirme} disabled={Boolean(chargement)} onChange={e => setConfirme(e.target.checked)} />J’ai vérifié les pièces, les parties, les exclusions et la ventilation de TVA.</label>
        <button className={styles.bouton} type="button" disabled={!confirme || Boolean(chargement)} onClick={capturer}>{chargement === 'capture' ? 'Préparation…' : 'Préparer la capture RAS TVA et son OD'}</button>
      </section>}
      <p className={styles.aide}>La déclaration TVA automatique des périodes et reports concernés reste à compléter : l’imputation et le reversement des retenues ne sont pas encore automatisés. La RAS HT, les avoirs/acomptes et les paiements antérieurs non ventilés restent hors de ce raccordement.</p>
    </>}
  </section></fieldset>
}
