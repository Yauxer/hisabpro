import { cloneElement, useEffect, useId, useRef, useState } from 'react'
import { API_BASE, formatErreurAPI, getToken } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './RasTvaAssistant.module.css'

const initial = {
  date_paiement: '', payeur: 'a_qualifier', prestataire: 'a_qualifier',
  prestation_liste_b: '', exclusion: 'a_qualifier', reference_exclusion: '',
  attestation: 'a_qualifier', date_attestation: '', reference_attestation: '',
  montant_paiement_ttc: '', tva_paiement: '',
}
const exclusions = [
  ['a_qualifier', 'À examiner sur les justificatifs'],
  ['aucune_apres_controle', 'Aucune exclusion applicable après contrôle'],
  ['energie_eau_reseaux', 'Énergie électrique / eau livrée aux réseaux publics'],
  ['assainissement_compteurs', 'Assainissement / location de compteurs concernés'],
  ['telecommunications', 'Opérateur de télécommunication'],
  ['courtier_assurances', 'Agent démarcheur ou courtier d’assurances'],
  ['petites_prestations_justifiees', 'Petites prestations : exclusion justifiée et cumul mensuel contrôlé'],
]

export default function RasTvaAssistant({ annee, datePaiement = null, onSimulation }) {
  const [form, setForm] = useState(() => ({ ...initial, date_paiement: datePaiement || '' }))
  const [resultat, setResultat] = useState(null)
  const [erreur, setErreur] = useState('')
  const [calcul, setCalcul] = useState(false)
  const generation = useRef(0)
  const signature = JSON.stringify([form, getToken()])
  const courante = useRef(signature)
  courante.current = signature
  const courant = resultat?.signature === signature ? resultat : null
  useEffect(() => {
    generation.current += 1
    setCalcul(false); setErreur('')
    onSimulation?.(null)
    return () => { generation.current += 1 }
  }, [signature, onSimulation])
  const champ = (cle, valeur) => setForm(f => ({ ...f, [cle]: valeur }))

  async function simuler(e) {
    e.preventDefault()
    const id = ++generation.current
    const cle = signature
    setCalcul(true); setErreur(''); setResultat(null)
    onSimulation?.(null)
    const payload = {
      ...form,
      date_paiement: form.date_paiement || null,
      prestation_liste_b: form.prestation_liste_b === '' ? null : form.prestation_liste_b === 'oui',
      date_attestation: form.attestation === 'presentee' ? form.date_attestation || null : null,
      reference_attestation: form.attestation === 'presentee' ? form.reference_attestation || null : null,
      montant_paiement_ttc: form.montant_paiement_ttc || null,
      tva_paiement: form.tva_paiement || null,
    }
    try {
      const r = await fetch(`${API_BASE}/api/tva/ras/simulation`, {
        method: 'POST', headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await r.json()
      if (!r.ok) throw new Error(formatErreurAPI(data.detail || `Erreur HTTP ${r.status}`))
      if (id !== generation.current || cle !== courante.current) return
      setResultat({ ...data, signature: cle })
      onSimulation?.({ simulation: payload, resultat: data })
    } catch (err) {
      if (id === generation.current && cle === courante.current) setErreur(err.message)
    } finally { if (id === generation.current) setCalcul(false) }
  }

  return <details className={styles.panel}>
    <summary>Assistant RAS TVA · 2026</summary>
    <div className={styles.contenu}>
      <p>Calcul de préparation pour un payeur privé assujetti et un prestataire personne physique assujettie, service relevant de la liste B (article 117-V-b).</p>
      {annee !== 2026 ? <p>Ce calcul couvre les paiements de 2026. Sélectionnez un exercice comprenant cette année pour l’utiliser.</p> : <form onSubmit={simuler}>
        <div className={styles.grille}>
          <Champ label="Date réelle du paiement"><input type="date" min="2026-01-01" max="2026-12-31" value={form.date_paiement} disabled={Boolean(datePaiement)} onChange={e => champ('date_paiement', e.target.value)} /></Champ>
          <Champ label="Situation du payeur"><select value={form.payeur} onChange={e => champ('payeur', e.target.value)}>
            <option value="a_qualifier">À qualifier</option><option value="pm_privee_assujettie">Personne morale privée assujettie</option>
            <option value="pp_rnr_rns_assujettie">Personne physique RNR/RNS assujettie</option><option value="autre">Autre situation</option>
          </select></Champ>
          <Champ label="Situation du prestataire"><select value={form.prestataire} onChange={e => champ('prestataire', e.target.value)}>
            <option value="a_qualifier">À qualifier</option><option value="pp_assujettie">Personne physique assujettie</option><option value="autre">Autre situation</option>
          </select></Champ>
          <Champ label="Service relevant de la liste B"><select value={form.prestation_liste_b} onChange={e => champ('prestation_liste_b', e.target.value)}>
            <option value="">À qualifier sur la prestation réelle</option><option value="oui">Oui, appartenance vérifiée</option><option value="non">Non</option>
          </select></Champ>
          <Champ label="Exclusions de l’article 117"><select value={form.exclusion} onChange={e => champ('exclusion', e.target.value)}>
            {exclusions.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select></Champ>
          {form.exclusion !== 'a_qualifier' && form.exclusion !== 'aucune_apres_controle' && <Champ label="Justificatif de l’exclusion"><input maxLength={200} value={form.reference_exclusion} onChange={e => champ('reference_exclusion', e.target.value)} placeholder="Référence du contrôle et des pièces" /></Champ>}
          <Champ label="Attestation de régularité fiscale"><select value={form.attestation} onChange={e => champ('attestation', e.target.value)}>
            <option value="a_qualifier">À vérifier</option><option value="presentee">Présentée au payeur</option><option value="absente">Absente</option>
          </select></Champ>
          {form.attestation === 'presentee' && <>
            <Champ label="Date de délivrance de l’attestation"><input type="date" value={form.date_attestation} onChange={e => champ('date_attestation', e.target.value)} /></Champ>
            <Champ label="Référence de l’attestation"><input maxLength={200} value={form.reference_attestation} onChange={e => champ('reference_attestation', e.target.value)} /></Champ>
          </>}
          <Champ label="Quote-part TTC payée avant retenues (MAD)"><input type="number" min="0" step="0.01" value={form.montant_paiement_ttc} onChange={e => champ('montant_paiement_ttc', e.target.value)} /></Champ>
          <Champ label="TVA correspondant à cette quote-part (MAD)"><input type="number" min="0" step="0.01" value={form.tva_paiement} onChange={e => champ('tva_paiement', e.target.value)} /></Champ>
        </div>
        <p className={styles.aide}>Pour un paiement partiel, renseignez seulement sa quote-part de TVA. Les exclusions de faible montant nécessitent aussi le contrôle du cumul mensuel du fournisseur ; elles ne sont pas déterminées automatiquement.</p>
        <button className={styles.bouton} type="submit" disabled={calcul}>{calcul ? 'Calcul…' : 'Simuler la RAS TVA'}</button>
      </form>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {courant && <section aria-label="Résultat de la simulation RAS TVA" className={styles.resultat}>
        <strong>{({ calcule: 'Calcul de préparation', exclu: 'Exclusion renseignée', a_completer: 'Informations à compléter', non_couvert: 'Situation à examiner séparément' })[courant.statut]}</strong>
        {courant.motifs.map(m => <p key={m}>{m}</p>)}
        {courant.retenue_tva !== null && <dl className={styles.chiffres}>
          {courant.base_tva !== null && <><dt>TVA de la quote-part</dt><dd>{montantDecimalExact(courant.base_tva)} MAD</dd></>}
          <dt>Part de TVA retenue</dt><dd>{courant.taux_retenue_tva} %</dd>
          <dt>RAS TVA</dt><dd>{montantDecimalExact(courant.retenue_tva)} MAD</dd>
          {courant.net_apres_cette_ras_tva !== null && <><dt>Net après cette seule RAS TVA</dt><dd>{montantDecimalExact(courant.net_apres_cette_ras_tva)} MAD</dd></>}
          {courant.mois_reversement && <><dt>Mois de reversement</dt><dd>{courant.mois_reversement}</dd></>}
        </dl>}
        <p className={styles.aide}>Ce résultat ne crée ni règlement, ni écriture, ni déclaration. La RAS sur le HT et les autres retenues restent distinctes.</p>
        <a href={courant.source} target="_blank" rel="noreferrer">Source : CGI 2026, article 117-V-b et liste B</a>
      </section>}
    </div>
  </details>
}

function Champ({ label, children }) {
  const id = useId()
  return <div className={styles.champ}><label htmlFor={id}>{label}</label>{cloneElement(children, { id })}</div>
}
