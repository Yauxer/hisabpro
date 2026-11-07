import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const argent = v => v == null ? 'Inconnu' : `${montantDecimalExact(typeof v === 'number' ? String(v) : v)} MAD`

export default function BalancePreparationFinancement({ dossier, onConserve }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [erreur, setErreur] = useState(''), [attente, setAttente] = useState(false)
  const [brouillons, setBrouillons] = useState({}), [selection, setSelection] = useState('')
  const [confirme, setConfirme] = useState(false), [periode, setPeriode] = useState('n')
  const generation = useRef(0), vivant = useRef(true), cle = useRef(null)
  const token = getToken(), ecriture = peutEcrire()
  const actuel = n => vivant.current && n === generation.current && getToken() === token
  useEffect(() => {
    vivant.current = true
    if (ouvert) charger()
    return () => { vivant.current = false; generation.current += 1 }
  }, [ouvert])
  async function charger() {
    const n = ++generation.current
    setAttente(true); setErreur(''); setData(null); setConfirme(false); cle.current = null
    try {
      const d = await etatsAPI.preparationBalanceFinancement(dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d); setSelection(d.lignes[0]?.code || ''); setPeriode('n')
      setBrouillons(Object.fromEntries(d.lignes.map(r => [r.code, {
        code: r.code, n: r.n ?? '', n1: r.n1 ?? '', justification_n: r.justification_n, justification_n1: r.justification_n1,
      }])))
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  function modifier(k, v) {
    cle.current = null; setConfirme(false)
    setBrouillons(prev => ({ ...prev, [selection]: { ...prev[selection], [k]: v } }))
  }
  async function conserver(e) {
    e.preventDefault(); const n = ++generation.current
    setAttente(true); setErreur('')
    try {
      cle.current ||= cleIdempotence()
      const lignes = Object.values(brouillons).map(r => ({ ...r,
        n: r.n.trim().replace(',', '.') || null, n1: r.n1.trim().replace(',', '.') || null,
      }))
      const d = await etatsAPI.conserverBalanceFinancement(dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current, lignes,
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  const row = brouillons[selection], tf = data?.tableau
  const autorise = ecriture && !attente && data?.sources_disponibles && (periode === 'n' || data.comparatif_disponible)
  const tableau = (titre, rows, montant = 'montant') => <>
    <h4>{titre}</h4><div className={styles.tableWrap}><table className={styles.sources}>
      <thead><tr><th>Rubrique</th><th>N MAD</th><th>N-1 MAD</th></tr></thead>
      <tbody>{rows.map((r, i) => <tr key={i}><th>{r.libelle}</th><td>{argent(r[montant])}</td><td>{argent(r.n1)}</td></tr>)}</tbody>
    </table></div>
  </>
  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Préparer le tableau de financement depuis les balances</summary>
    {ouvert && <section aria-label="Financement documentaire de la préparation" className={styles.detail}>
      <h3>Financement documentaire — version {dossier.version}</h3>
      {attente && <p role="status">Chargement du financement…</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire le financement conservé</button>
      {data && <>
        <p>{data.note}</p>
        {data.motif_precision && <p role="note">{data.motif_precision}</p>}
        <p>Flux conservés : {data.flux_renseignes.n}/{data.lignes.length} en N et {data.flux_renseignes.n1}/{data.lignes.length} en N-1. Ces nombres ne prouvent pas la complétude fiscale.</p>
        <p>CAF issue de l’ESG conservé : N {argent(data.caf.n)} ; N-1 {argent(data.caf.n1)}.</p>
        {data.parent && <p>Version source {data.parent.version} · Conservé par {data.auteur.nom} le {data.conserve_le_utc}.</p>}
        {!data.sources_disponibles && <p>Sources détaillées absentes : réimporter explicitement la balance.</p>}
        {tf && <>
          {tableau('Synthèse des masses du bilan', tf.synthese, 'n')}
          {tableau('Ressources stables documentaires', tf.ressources)}
          {tableau('Emplois stables documentaires', tf.emplois)}
          <p>Total ressources N : {argent(tf.total_ressources)} · Total emplois N : {argent(tf.total_emplois)}.</p>
          <p>Total ressources N-1 : {argent(tf.total_ressources_n1)} · Total emplois N-1 : {argent(tf.total_emplois_n1)}.</p>
          <p>Variation du fonds de roulement : {argent(tf.variation_fonds_roulement)} · Écart de rapprochement N : {argent(tf.ecart_controle)}.</p>
          {!data.calcul_disponible.n && <p>Totaux N indisponibles : compléter tous les flux et fournir une balance permettant d’établir la CAF.</p>}
          {!data.comparatif_disponible && <p>Balance N-1 absente : variations et rapprochement comparatif indisponibles.</p>}
          {tf.ecart_controle != null && <p role="note">L’écart est un diagnostic ; aucun ajustement automatique n’est effectué pour l’annuler.</p>}
          {tf.avertissements.map((t, i) => <p key={i}>{t}</p>)}
        </>}
        <label className={styles.champ}>Flux à documenter<select aria-label="Flux à documenter" value={selection} disabled={attente} onChange={e => setSelection(e.target.value)}>
          {data.lignes.map(r => <option key={r.code} value={r.code}>{r.titre}</option>)}
        </select></label>
        <label className={styles.champ}>Période du flux<select aria-label="Période du flux" value={periode} disabled={attente} onChange={e => setPeriode(e.target.value)}><option value="n">N</option><option value="n1">N-1</option></select></label>
        {row && <form onSubmit={conserver} className={styles.detail}>
          <h4>{data.lignes.find(r => r.code === selection)?.titre} · {periode === 'n' ? 'N' : 'N-1'}</h4>
          <label className={styles.champ}>Montant du flux MAD<input aria-label="Montant du flux MAD" inputMode="decimal" placeholder="Inconnu" value={row[periode]} disabled={!autorise} onChange={e => modifier(periode, e.target.value)} /></label>
          <label className={styles.champ}>Justification du flux<textarea aria-label="Justification du flux" maxLength={2000} value={row['justification_' + periode]} disabled={!autorise} onChange={e => modifier('justification_' + periode, e.target.value)} /></label>
          {ecriture && data.sources_disponibles && <>
            <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme les flux renseignés et leurs sources ; les cellules vides restent inconnues.</label>
            <button className={styles.bouton} disabled={attente || !confirme}>Conserver le financement dans une nouvelle version</button>
            <p>Conserve tous les flux saisis, avec calcul après enregistrement. Aucune écriture créée. Les autres compléments sont préservés ; pièces propres à leur version.</p>
          </>}
        </form>}
      </>}
    </section>}
  </details>
}
