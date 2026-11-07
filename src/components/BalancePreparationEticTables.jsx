import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './BalancePreparationDetail.module.css'

const CONFIG = {
  resume: 'Documenter les tableaux ETIC B8 et B9',
  titre: 'Sûretés et engagements',
  region: 'Tableaux documentaires ETIC de la préparation',
  lire: etatsAPI.preparationBalanceTablesEtic,
  conserver: etatsAPI.conserverBalanceTablesEtic,
}

export default function BalancePreparationEticTables({ dossier, onConserve, configuration = CONFIG }) {
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
      const d = await configuration.lire(dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d); setSelection(d.tables[0]?.code || '')
      setBrouillons(Object.fromEntries(d.tables.map(r => [r.code, {
        code: r.code, statut: r.statut, justification: r.justification, lignes: r.lignes,
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
      const d = await configuration.conserver(dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current, tables: Object.values(brouillons),
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  function modifierLigne(index, champ, valeur) {
    modifier('lignes', brouillons[selection].lignes.map((r, i) => i === index ? { ...r, [champ]: valeur } : r))
  }
  const row = brouillons[selection]
  const rubrique = data?.tables.find(r => r.code === selection)
  const autorise = ecriture && !attente && (configuration.autorise?.(data, selection) ?? true)
  const libelleSelection = configuration.libelleSelection || 'Tableau ETIC à documenter'
  const maxLignes = typeof configuration.maxLignes === 'function' ? configuration.maxLignes(selection) : (configuration.maxLignes ?? 100)
  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>{configuration.resume}</summary>
    {ouvert && <section aria-label={configuration.region} className={styles.detail}>
      <h3>{configuration.titre} — version {dossier.version}</h3>
      {attente && <p role="status">{configuration.libelleChargement || 'Chargement des tableaux ETIC…'}</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire les tableaux conservés</button>
      {data && <>
        <p>{data.note}</p>
        {data.alertes.map(a => <p role="status" key={a}>{a}</p>)}
        {data.auteur && <p>Conservés par {data.auteur.nom} · {data.conserve_le_utc} · Version source {data.parent.version}</p>}
        <label className={styles.champ}>{libelleSelection}<select aria-label={libelleSelection} value={selection} disabled={attente} onChange={e => setSelection(e.target.value)}>
          {data.tables.map(r => <option key={r.code} value={r.code}>{r.code} · {r.titre}</option>)}
        </select></label>
        {row && <form onSubmit={conserver} className={styles.detail}>
          <h4>{rubrique.code} · {rubrique.titre}</h4>
          {configuration.complement?.(data, selection)}
          <label className={styles.champ}>Déclaration du tableau<select aria-label="Déclaration du tableau" value={row.statut} disabled={!autorise} onChange={e => modifier('statut', e.target.value)}>
            <option value="a_completer">À compléter</option><option value="documente">Saisie documentée — à revoir</option><option value="neant_declare">Néant — déclaré et justifié</option>
          </select></label>
          <label className={styles.champ}>Justification du tableau<textarea aria-label="Justification du tableau" maxLength={2000} value={row.justification} disabled={!autorise} onChange={e => modifier('justification', e.target.value)} /></label>
          <p>{row.lignes.length} ligne(s). Les montants vides restent inconnus. Un zéro doit être saisi explicitement. {configuration.noteNombres || 'Les montants sont positifs ou nuls, avec deux décimales maximum.'}</p>
          {row.lignes.map((ligne, index) => <fieldset key={index} className={styles.detail} disabled={!autorise}>
            <legend>Ligne {index + 1}</legend>
            {rubrique.colonnes_saisie.map(c => <label key={c.cle} className={styles.champ}>{c.label}{c.type === 'number' ? ` (${c.unite || 'MAD'})` : ''}
              {configuration.options?.(data, selection, c) ? <select aria-label={`${c.label} ligne ${index + 1}`} value={ligne[c.cle] ?? ''} onChange={e => modifierLigne(index, c.cle, e.target.value)}><option value="">{configuration.placeholder?.(c) || 'Choisir un compte source'}</option>{configuration.options(data, selection, c).map(v => <option key={v} value={v}>{v}</option>)}</select> : <input aria-label={`${c.label} ligne ${index + 1}`} type={c.type === 'date' ? 'date' : 'text'} inputMode={c.type === 'number' ? 'decimal' : 'text'} maxLength={c.type === 'number' ? 40 : 2000}
                value={ligne[c.cle] ?? ''} onChange={e => modifierLigne(index, c.cle, e.target.value)} />}
            </label>)}
            <label className={styles.champ}>Référence de source de la ligne<textarea aria-label={`Référence de source ligne ${index + 1}`} maxLength={2000} value={ligne.reference_source || ''} onChange={e => modifierLigne(index, 'reference_source', e.target.value)} /></label>
            {ecriture && <button type="button" className={styles.bouton} disabled={attente} onClick={() => modifier('lignes', row.lignes.filter((_, i) => i !== index))}>Retirer la ligne {index + 1} du brouillon</button>}
          </fieldset>)}
          {ecriture && <>
            <button type="button" className={styles.bouton} disabled={!autorise || row.lignes.length >= maxLignes} onClick={() => modifier('lignes', [...row.lignes, {}])}>Ajouter une ligne au tableau</button>
            <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme les données et déclarations saisies, sans valider une liasse complète.</label>
            <button className={styles.bouton} disabled={attente || !confirme}>{configuration.libelleConserver || 'Conserver les tableaux ETIC dans une nouvelle version'}</button>
            <p>Les tableaux de ce formulaire sont conservés ensemble. Les notes et autres compléments sont préservés ; une éventuelle contradiction reste à revoir. Les pièces jointes restent attachées à leur version d’origine.</p>
          </>}
        </form>}
      </>}
    </section>}
  </details>
}
