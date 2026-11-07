import { useEffect, useRef, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { etatsAPI, getToken } from '../services/api.js'
import styles from '../pages/LiasseFiscale.module.css'

const montant = v => v == null ? 'À vérifier' : v.replace('.', ',')

export default function VentesPreparation() {
  const { annee } = useExercice()
  const { societe, chargement } = useModules()
  const [lecture, setLecture] = useState(null)
  const [exportEnCours,setExportEnCours]=useState(false)
  const version = useRef(0)
  const token = getToken()
  const cle = `${societe?.id || ''}:${annee}:${token || ''}`
  const scope = useRef(cle); scope.current = cle
  useEffect(() => { version.current += 1; setLecture(null);setExportEnCours(false); return () => { version.current += 1 } }, [cle])
  const courant = lecture?.cle === cle ? lecture : null
  const data = courant?.data

  async function charger() {
    const id = ++version.current; const capture = cle
    setLecture({ cle: capture, loading: true })
    try {
      const resultat = await etatsAPI.ventesPreparation(annee)
      if (version.current === id && scope.current === capture && getToken() === token) {
        setLecture({ cle: capture, data: resultat })
      }
    } catch (e) {
      if (version.current === id && scope.current === capture && getToken() === token) setLecture({ cle: capture, erreur: e.message })
    }
  }

  function exporter() {
    if (!data || scope.current !== cle || getToken() !== token) return
    const blob = new Blob(['\uFEFF'+data.csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = `VENTES_PREPARATION_INTERNE_${data.exercice}.csv`; a.click(); URL.revokeObjectURL(url)
  }

  async function exporterFormat(format) {
    if(!data || courant?.loading || getToken()!==token)return
    const id=version.current;const capture=cle
    setExportEnCours(true)
    try {
      const fichier=await etatsAPI.ventesPreparationExport(data.exercice,format,data.empreinte_sha256)
      if(!fichier || version.current!==id || scope.current!==capture || getToken()!==token)return
      const url=URL.createObjectURL(fichier.blob);const a=document.createElement('a')
      a.href=url;a.download=fichier.filename;a.click();URL.revokeObjectURL(url)
    } catch(e) {
      if(version.current===id && scope.current===capture && getToken()===token)setLecture(prev=>({...prev,erreur:e.message}))
    } finally {
      if(version.current===id && scope.current===capture)setExportEnCours(false)
    }
  }

  return <section className={styles.card} aria-label="Préparation annuelle des ventes">
    <div className={styles.cardHeader}>
      <div><h2>État des ventes — préparation interne</h2><span>Exercice {annee} · Factures et avoirs de vente</span></div>
      <div className={styles.actionsTop}>
        <button className={styles.btnSec} disabled={chargement || !societe?.id || courant?.loading || exportEnCours} onClick={charger}>
          {courant?.loading ? 'Chargement…' : data ? 'Actualiser les ventes' : 'Préparer les ventes'}
        </button>
        <button className={styles.btnSec} disabled={!data || courant?.loading} onClick={exporter}>Exporter les ventes CSV</button>
        <button className={styles.btnSec} disabled={!data || courant?.loading || exportEnCours} onClick={()=>exporterFormat('xlsx')}>Exporter les ventes Excel</button>
        <button className={styles.btnSec} disabled={!data || courant?.loading || exportEnCours} onClick={()=>exporterFormat('pdf')}>Exporter les ventes PDF</button>
      </div>
    </div>
    <p className={styles.ediNote}>Préparation interne des pièces de vente, extérieure à l’archive de liasse. Le format de déclaration DGI reste à qualifier.</p>
    {courant?.erreur && <div className={styles.error} role="alert">{courant.erreur}</div>}
    {data && <>
      <div className={styles.ediNote}><details><summary>Périmètre et méthode de calcul</summary><p>{data.note}</p></details></div>
      <div className={styles.kpis}>
        <div><span>Période</span><strong>{data.date_debut} → {data.date_fin}</strong></div>
        <div><span>Pièces retenues</span><strong>{data.documents.length}</strong></div>
        <div><span>HT commercial signé</span><strong>{montant(data.totaux?.ht)} MAD</strong></div>
        <div><span>TTC signé</span><strong>{montant(data.totaux?.ttc)} MAD</strong></div>
      </div>
      {data.nb_montants_inconnus > 0 && <div className={styles.error} role="alert">
        {data.nb_montants_inconnus} pièce(s) aux montants inconnus. Total complet à vérifier. Partie connue uniquement : HT {montant(data.totaux_partie_connue.ht)} MAD.
      </div>}
      {data.comptabilite && <section aria-label="Raccordement comptable des ventes" style={{ padding: 14, margin: '12px 0', border: '1px solid var(--border-light)', borderRadius: 8 }}>
        <h3 style={{ fontSize: 13, margin: '0 0 10px' }}>Raccordement avec la comptabilité</h3>
        <div className={styles.kpis}>
          <div><span>CA comptes 711/712 validés</span><strong>{montant(data.comptabilite.ca_net)} MAD</strong></div>
          <div><span>HT documentaire signé</span><strong>{montant(data.totaux?.ht)} MAD</strong></div>
          <div><span>Écart CA moins HT documentaire</span><strong>{montant(data.comptabilite.ecart_ca_moins_ht)} MAD</strong></div>
        </div>
        <p className={styles.ediNote}>{data.comptabilite.note}</p>
        <p className={styles.ediNote}>{data.comptabilite.brouillons_exclus} écriture(s) brouillon exclue(s) du CA. Le détail des mouvements comptables est disponible dans les exports Excel et CSV.</p>
        {data.comptabilite.avertissements.map(m => <p key={m} className={styles.error}>{m}</p>)}
        <details><summary>Détail par compte et origine technique</summary>
          {data.comptabilite.comptes.map(c => <p key={c.compte} className={styles.ediNote}>
            <strong>{c.compte}</strong> · Débit {montant(c.debit)} · Crédit {montant(c.credit)} · CA net {montant(c.ca_net)} MAD
          </p>)}
          {data.comptabilite.origines.map(o => <p key={o.source} className={styles.ediNote}>
            Origine {o.source} · {o.nb_lignes} ligne(s) · {montant(o.ca_net)} MAD
          </p>)}
        </details>
      </section>}
      <div className={styles.tableWrap}><table className={styles.table}>
        <thead><tr>{['Pièce / source', 'Date', 'Client figé', 'ICE / IF figés', 'HT commercial signé', 'TVA signée', 'TTC signé', 'Contrôles'].map(h => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{data.documents.map(r => <tr key={`${r.nature}-${r.id}`}>
          <td>{r.nature === 'avoir' ? 'Avoir' : 'Facture'} {r.numero || `#${r.id}`}<br />ID {r.id} · Facture source {r.facture_id}</td>
          <td style={{ whiteSpace: 'nowrap' }}>{r.date}</td><td>{r.tiers}</td><td>{r.ice || 'À compléter'}<br />{r.identifiant_fiscal || 'À compléter'}</td>
          {['ht', 'tva', 'ttc'].map(k => <td className={styles.num} key={k}>{montant(r[k])}</td>)}
          <td>{r.diagnostics.length ? r.diagnostics.join(' ') : 'Source disponible'}</td>
        </tr>)}</tbody>
      </table></div>
      {!data.documents.length && <div className={styles.empty}>Aucune pièce de vente définitive dans cette période.</div>}
      <p className={styles.ediNote} style={{ overflowWrap: 'anywhere' }}>Exclus : {data.exclusions.brouillons} brouillon(s), {data.exclusions.proformas} proforma(s), {data.exclusions.annules} pièce(s) annulée(s). Constaté le {data.constate_le}. Empreinte : {data.empreinte_sha256}</p>
    </>}
  </section>
}
