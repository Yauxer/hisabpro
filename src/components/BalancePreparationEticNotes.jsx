import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './BalancePreparationDetail.module.css'

export default function BalancePreparationEticNotes({ dossier, onConserve }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [erreur, setErreur] = useState(''), [attente, setAttente] = useState(false)
  const [brouillons, setBrouillons] = useState({}), [selection, setSelection] = useState('')
  const [confirme, setConfirme] = useState(false)
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
      const d = await etatsAPI.preparationBalanceNotesEtic(dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d); setSelection(d.lignes[0]?.code || '')
      setBrouillons(Object.fromEntries(d.lignes.map(r => [r.code, {
        code: r.code, statut: r.statut, texte: r.texte, justification: r.justification,
      }])))
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
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
      const d = await etatsAPI.conserverBalanceNotesEtic(dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current, lignes: Object.values(brouillons),
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  const row = brouillons[selection]
  const rubrique = data?.lignes.find(r => r.code === selection)
  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Documenter les notes de préparation ETIC</summary>
    {ouvert && <section aria-label="Notes documentaires ETIC de la préparation" className={styles.detail}>
      <h3>Notes ETIC — version {dossier.version}</h3>
      {attente && <p role="status">Chargement des notes ETIC…</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire les notes conservées</button>
      {data && <>
        <p>{data.note}</p>
        <p>Notes de la version conservée : {data.comptage_notes.renseigne} renseignées ; {data.comptage_notes.non_applicable} déclarées non applicables ; {data.comptage_notes.a_completer} à compléter. Ces nombres ne mesurent pas la complétude de la liasse.</p>
        {data.auteur && <p>Conservées par {data.auteur.nom} · {data.conserve_le_utc} · Version source {data.parent.version}</p>}
        <label className={styles.champ}>Rubrique ETIC à documenter<select aria-label="Rubrique ETIC à documenter" value={selection} disabled={attente} onChange={e => setSelection(e.target.value)}>
          {data.lignes.map(r => <option key={r.code} value={r.code}>{r.code} · {r.titre}</option>)}
        </select></label>
        {row && <form onSubmit={conserver} className={styles.detail}>
          <h4>{rubrique.code} · {rubrique.titre}</h4>
          <label className={styles.champ}>État de la note<select aria-label="État de la note" value={row.statut} disabled={!ecriture || attente} onChange={e => modifier('statut', e.target.value)}>
            <option value="a_completer">À compléter</option><option value="renseigne">Note renseignée</option><option value="non_applicable">Non applicable — déclaré</option>
          </select></label>
          <label className={styles.champ}>Texte de préparation<textarea aria-label="Texte de préparation" maxLength={10000} value={row.texte} disabled={!ecriture || attente} onChange={e => modifier('texte', e.target.value)} /></label>
          <label className={styles.champ}>Référence ou justification ETIC<textarea aria-label="Référence ou justification ETIC" maxLength={2000} value={row.justification} disabled={!ecriture || attente} onChange={e => modifier('justification', e.target.value)} /></label>
          {ecriture && <>
            <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme les notes et les déclarations renseignées, sans valider une liasse complète.</label>
            <button className={styles.bouton} disabled={attente || !confirme}>Conserver les notes ETIC dans une nouvelle version</button>
            <p>Toutes les rubriques de ce formulaire sont conservées. Les autres compléments de la préparation sont préservés. Les pièces jointes restent attachées à leur version d’origine.</p>
          </>}
        </form>}
      </>}
    </section>}
  </details>
}
