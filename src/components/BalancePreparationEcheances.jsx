import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const CHAMPS = [
  ['plus_un_an', 'Plus d’un an'], ['moins_un_an', 'Moins d’un an'], ['echues', 'Échues'],
  ['devises', 'En devises'], ['etat_organismes_publics', 'État / organismes publics'],
  ['entreprises_liees', 'Entreprises liées'], ['effets', 'Effets'],
]
const argent = v => v == null ? 'Inconnu' : `${montantDecimalExact(v)} MAD`
const identifiant = r => `${r.section}:${r.compte}`

export default function BalancePreparationEcheances({ dossier, onConserve }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [erreur, setErreur] = useState(''), [attente, setAttente] = useState(false)
  const [brouillons, setBrouillons] = useState({}), [selection, setSelection] = useState('')
  const [filtre, setFiltre] = useState(''), [confirme, setConfirme] = useState(false)
  const generation = useRef(0), vivant = useRef(true), cle = useRef(null)
  const token = getToken(), ecriture = peutEcrire()
  const actuel = n => vivant.current && n === generation.current && getToken() === token
  useEffect(() => () => { vivant.current = false; generation.current += 1 }, [])
  useEffect(() => {
    vivant.current = true
    if (ouvert) charger()
    return () => { generation.current += 1 }
  }, [ouvert])

  async function charger() {
    const n = ++generation.current
    setAttente(true); setErreur(''); setData(null); setConfirme(false); cle.current = null
    try {
      const d = await etatsAPI.preparationBalanceEcheances(dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d)
      setBrouillons(Object.fromEntries(d.lignes.map(r => [identifiant(r), {
        section: r.section, compte: r.compte,
        ...Object.fromEntries(CHAMPS.map(([k]) => [k, r[k] ?? ''])), justification: r.justification,
      }])))
      setSelection(d.lignes[0] ? identifiant(d.lignes[0]) : '')
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  const lignes = (data?.lignes || []).filter(r => r.compte.includes(filtre.trim()))
  const ligne = data?.lignes.find(r => identifiant(r) === selection)
  const brouillon = brouillons[selection]
  function modifier(k, v) {
    cle.current = null; setConfirme(false)
    setBrouillons(prev => ({ ...prev, [selection]: { ...prev[selection], [k]: v } }))
  }

  async function conserver(e) {
    e.preventDefault()
    const n = ++generation.current
    setAttente(true); setErreur('')
    try {
      cle.current ||= cleIdempotence()
      const rows = Object.values(brouillons).filter(r => data.lignes.some(s => identifiant(s) === identifiant(r) && s.ventilable))
        .filter(r => r.justification.trim() || CHAMPS.some(([k]) => r[k] !== ''))
        .map(r => ({ ...r, ...Object.fromEntries(CHAMPS.map(([k]) => [k, r[k].trim().replace(',', '.') || null])) }))
      if (!rows.length) throw new Error('Renseignez au moins un montant ou une justification pour conserver ce complément.')
      const d = await etatsAPI.conserverBalanceEcheances(dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current, lignes: rows,
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Compléter les échéances documentaires des balances</summary>
    {ouvert && <section aria-label="Échéances documentaires de la préparation" className={styles.detail}>
      <h3>Créances et dettes — version {dossier.version}</h3>
      {attente && <p role="status">Chargement des échéances documentaires…</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire les échéances conservées</button>
      {data && <>
        <p>{data.note}</p>
        {data.parent && <p>Complément issu de la version {data.parent.version} · Empreinte source : {data.parent.empreinte_sha256}</p>}
        {!data.sources_disponibles && <p>Sources détaillées absentes : réimporter explicitement la balance pour préparer des compléments.</p>}
        {data.sources_disponibles && !data.lignes.length && <p>Aucun solde de créance ou dette dans les comptes sélectionnés par cette préparation.</p>}
        {!!data.lignes.length && <>
          <div className={styles.outils}>
            <label className={styles.champ}>Filtrer les comptes à documenter<input aria-label="Filtrer les comptes à documenter" value={filtre} onChange={e => { setFiltre(e.target.value); setSelection('') }} disabled={attente} /></label>
            <label className={styles.champ}>Compte à documenter<select aria-label="Compte à documenter" value={selection} onChange={e => setSelection(e.target.value)} disabled={attente}>
              <option value="">Sélectionner un compte</option>
              {lignes.slice(0, 100).map(r => <option key={identifiant(r)} value={identifiant(r)}>{r.section} · {r.compte} · {argent(r.total)}</option>)}
            </select></label>
          </div>
          {lignes.length > 100 && <p>Premiers 100 comptes affichés : précisez le filtre pour atteindre les suivants.</p>}
          {!lignes.length && <p>Aucun compte correspondant au filtre.</p>}
          {ligne && brouillon && <form onSubmit={conserver} className={styles.detail}>
            <p>Solde N conservé : {argent(ligne.total)} · Ventilé par échéance : {argent(ligne.qualifie)} · Reliquat non qualifié : {argent(ligne.reliquat)}</p>
            <p>Ces totaux correspondent à la version conservée ; ils seront recalculés par le serveur lors de la conservation. Les champs vides restent inconnus. Les analyses complémentaires peuvent se recouper.</p>
            {!ligne.ventilable && <p role="note">Solde de sens inverse : conservé dans les sources, non ventilable dans cette préparation.</p>}
            {CHAMPS.map(([k, label]) => <label key={k} className={styles.champ}>{label} MAD<input aria-label={`${label} MAD`} inputMode="decimal" value={brouillon[k]} placeholder="Inconnu" disabled={!ecriture || attente || !ligne.ventilable} onChange={e => modifier(k, e.target.value)} /></label>)}
            <label className={styles.champ}>Justification / référence de source<textarea aria-label="Justification / référence de source" maxLength={2000} value={brouillon.justification} disabled={!ecriture || attente || !ligne.ventilable} onChange={e => modifier('justification', e.target.value)} /></label>
            {ecriture && ligne.ventilable && <>
              <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme les données documentaires renseignées. Les autres montants restent inconnus.</label>
              <button className={styles.bouton} disabled={attente || !confirme}>Conserver les compléments dans une nouvelle version</button>
              <p>Conserve tous les comptes renseignés dans ce formulaire. Aucune ancienne version ni écriture ne sera modifiée.</p>
            </>}
          </form>}
        </>}
      </>}
    </section>}
  </details>
}
