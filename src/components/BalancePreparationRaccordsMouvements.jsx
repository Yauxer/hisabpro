import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

export default function BalancePreparationRaccordsMouvements({ dossier, onConserve }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [attente, setAttente] = useState(false), [erreur, setErreur] = useState('')
  const [selection, setSelection] = useState('B2'), [choix, setChoix] = useState({}), [confirme, setConfirme] = useState(false)
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
      const d = await etatsAPI.preparationBalanceRaccordsMouvements(dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d); setSelection(d.courant[0]?.code || 'B2')
      setChoix(Object.fromEntries(d.courant.map(t => [t.code, Object.fromEntries(t.lignes.map(r => [r.ligne, r.compte]))])))
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  function modifier(ligne, compte) {
    cle.current = null; setConfirme(false)
    setChoix(prev => ({ ...prev, [selection]: { ...prev[selection], [ligne]: compte } }))
  }
  async function conserver(e) {
    e.preventDefault(); const n = ++generation.current
    setAttente(true); setErreur('')
    try {
      cle.current ||= cleIdempotence()
      const d = await etatsAPI.conserverBalanceRaccordsMouvements(dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current,
        tables: data.courant.map(t => ({ code: t.code, lignes: t.lignes.map(r => ({ ligne: r.ligne, compte: choix[t.code][r.ligne] || '' })) })),
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  const table = data?.courant.find(t => t.code === selection), snap = data?.snapshot
  const controle = snap?.controle_raccords.tableaux[selection]
  const anciens = snap?.catalogue.find(t => t.code === selection)?.lignes || []
  const liens = Object.fromEntries((snap?.tables.find(t => t.code === selection)?.lignes || []).map(r => [r.ligne, r.compte]))
  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Raccorder les clôtures de mouvements aux comptes sources</summary>
    {ouvert && <section aria-label="Rattachements des mouvements de la préparation" className={styles.detail} style={{ overflowWrap: 'anywhere' }}>
      <h3>Rattachements des clôtures — version {dossier.version}</h3>
      {attente && <p role="status">Chargement des rattachements…</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire les rattachements conservés</button>
      {data && <>
        <p>{data.note}</p>
        {!data.courant.length && <p>Conserver d’abord les mouvements documentaires B2/B2bis/B5.</p>}
        {!data.sources.disponible && <p>Source N détaillée absente ou incomplète : comptes indisponibles, aucun solde nul fabriqué.</p>}
        {data.courant.length > 0 && <>
          <label className={styles.champ}>Tableau de rattachement<select aria-label="Tableau de rattachement" value={selection} disabled={attente} onChange={e => setSelection(e.target.value)}>
            {data.courant.map(t => <option key={t.code} value={t.code}>{t.code} · {t.titre}</option>)}
          </select></label>
          <section aria-label="Contrôles des rattachements conservés" className={styles.detail}>
            {!snap ? <p>Aucun rattachement conservé.</p> : <>
              <p>Ces contrôles concernent la version conservée, pas les choix du brouillon.</p>
              {!data.actuel && <p role="status">Le contrôle conservé porte sur d’autres mouvements ou sources. Il doit être refait pour la préparation actuelle. Les nouveaux choix restent non rattachés.</p>}
              <p>Version source {snap.parent.version} · Conservé par {snap.auteur.nom} le {snap.conserve_le_utc}.</p>
              <p style={{ overflowWrap: 'anywhere' }}>Empreinte des mouvements contrôlés : {snap.empreinte_mouvements}</p>
              {!snap.controle_raccords.source_disponible && <p>Source du contrôle indisponible ; aucun montant reconstitué.</p>}
              {controle?.comptes.map(r => <div key={r.compte} className={styles.detail}><h4>Compte {r.compte} · {r.lignes} ligne(s) rattachée(s)</h4>
                <p>Libellé de compte non conservé dans la balance source.</p>
                <p>Solde source : <strong>{argent(r.solde_source)}</strong></p>
                <p>Somme des clôtures déclarées : <strong>{argent(r.somme_clotures_declarees)}</strong></p>
                <p>Écart déclaré moins source : <strong>{argent(r.ecart)}</strong></p>
              </div>)}
              <p>Lignes non rattachées du contrôle conservé : {controle?.non_rattachees.join(', ') || 'aucune'}.</p>
              <h4>Lignes du contrôle conservé</h4>
              {anciens.map(r => <p key={r.ligne}>Ligne {r.ligne} · {r.nature || 'Nature à compléter'} · Clôture : {argent(r.fin)} · Compte : {liens[r.ligne] || 'Non rattachée'} · Source : {r.reference_source || 'À compléter'}</p>)}
            </>}
          </section>
          {table && <form onSubmit={conserver} className={styles.detail}>
            <h4>Choix du brouillon pour les mouvements actuels</h4>
            {table.lignes.map(r => <fieldset className={styles.detail} style={{ minWidth: 0 }} key={r.ligne} disabled={!ecriture || attente || !data.sources.disponible}>
              <legend>Ligne {r.ligne} · {r.nature || 'Nature à compléter'}</legend>
              <p>Clôture déclarée actuelle : {argent(r.fin)} · Source : {r.reference_source || 'À compléter'}</p>
              <label className={styles.champ}>Compte source<select aria-label={`Compte source ${selection} ligne ${r.ligne}`} value={choix[selection]?.[r.ligne] || ''} onChange={e => modifier(r.ligne, e.target.value)}>
                <option value="">Non rattachée</option>{data.sources.comptes[selection].map(c => <option key={c} value={c}>{c}</option>)}
              </select></label>
            </fieldset>)}
            {!table.lignes.length && <p>Aucune ligne déclarée dans les mouvements actuels de ce tableau.</p>}
            {ecriture && <>
              <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme les rattachements explicites, sans valider une liasse complète.</label>
              <button className={styles.bouton} disabled={attente || !confirme}>Conserver les rattachements dans une nouvelle version</button>
              <p>Les trois tableaux sont conservés ensemble. Les mouvements déclarés restent inchangés ; les lignes non rattachées restent visibles.</p>
            </>}
          </form>}
        </>}
      </>}
    </section>}
  </details>
}
