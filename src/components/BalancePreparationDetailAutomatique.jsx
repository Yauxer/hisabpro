import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

export default function BalancePreparationDetailAutomatique({ dossier, onConserve, configuration: c }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [attente, setAttente] = useState(false), [erreur, setErreur] = useState('')
  const [periode, setPeriode] = useState('n'), [confirme, setConfirme] = useState(false)
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
      const d = await etatsAPI[c.charger](dossier.id)
      if (!actuel(n)) return
      if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  async function conserver(e) {
    e.preventDefault(); const n = ++generation.current
    setAttente(true); setErreur('')
    try {
      cle.current ||= cleIdempotence()
      const d = await etatsAPI[c.conserver](dossier.id, {
        empreinte_parent: dossier.empreinte_sha256, cle: cle.current,
      })
      if (actuel(n)) onConserve(d)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }
  const vue = data?.vue, detail = vue?.periodes[periode]
  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>{c.resume}</summary>
    {ouvert && <section aria-label={c.region} className={styles.detail}>
      <h3>{c.titre} — version {dossier.version}</h3>
      {attente && <p role="status">{c.chargement}</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>{c.relire}</button>
      {data && <>
        <p>{vue?.note || data.note}</p>
        {!data.conserve && <p>{c.absent}</p>}
        {vue && <>
          <h4>{vue.code} · {vue.titre}</h4>
          {vue.informations_a_completer?.length > 0 && <p>Informations à documenter séparément : {vue.informations_a_completer.join(' ; ')}.</p>}
          <p>Version source {data.parent.version} · Conservé par {data.auteur.nom} le {data.conserve_le_utc}.</p>
          <label className={styles.champ}>{c.periode}<select aria-label={c.periode} value={periode} onChange={e => setPeriode(e.target.value)}>{(c.periodes || [['n', 'N'], ['n1', 'N-1']]).map(([cle, label]) => <option key={cle} value={cle}>{label}</option>)}</select></label>
          {detail.avertissements?.map(a => <p role="note" key={a}>{a}</p>)}
          {c.extraIndicateurs && <section aria-label="Déclarations extra-comptables C3" className={styles.detail}>
            <p>Valeurs explicitement déclarées, distinctes des montants comptables calculés.</p>
            {c.extraIndicateurs.map(([k,label,unite]) => <p key={k}>{label} : <strong>{detail[k] == null ? 'Indisponible' : `${montantDecimalExact(detail[k])} ${unite}`}</strong></p>)}
            <p>Référence : {detail.reference_extra_c3 || 'À documenter'}</p>
            <p>Décisions et affectations : {detail.affectations_justifiees || 'À documenter'}</p>
          </section>}
          {!detail.disponible ? <p role="note">{detail.motif}</p> : <>
            {c.indicateurs.map(([k, label, comparaison = true]) => <div key={k} className={styles.detail}>
              <h5>{label}</h5>
              <p>Total du détail : <strong>{argent(detail[k])}</strong>{comparaison && <> · {c.reference} : {argent(detail[c.prefixe + k])}</>}</p>
              {comparaison && <p>Écart détail moins {c.reference} : <strong>{argent(detail['ecart_' + k])}</strong></p>}
            </div>)}
            <div className={styles.tableWrap}><table className={styles.sources}>
              <thead><tr><th>Compte</th><th>Nature</th><th>Solde signé MAD</th></tr></thead>
              <tbody>{detail.lignes.map(r => <tr key={r.compte}><th>{r.compte}<small style={{ display: 'block' }}>Libellé non conservé</small></th><td>{r.nature}</td><td>{argent(r.montant)}</td></tr>)}</tbody>
            </table></div>
            {!detail.lignes.length && <p>{c.aucun}</p>}
          </>}
        </>}
        {ecriture && <form onSubmit={conserver}>
          <label><input type="checkbox" checked={confirme} disabled={attente} onChange={e => setConfirme(e.target.checked)} /> Je confirme la conservation du détail depuis les seules balances de cette version.</label>
          <button className={styles.bouton} disabled={attente || !confirme}>{c.bouton}</button>
          <p>Fige la méthode, les sources, les écarts et les indisponibilités. Aucune écriture créée. Les pièces restent propres à leur version.</p>
        </form>}
      </>}
    </section>}
  </details>
}
