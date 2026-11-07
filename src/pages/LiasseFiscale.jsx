import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as XLSX from 'xlsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { etatsAPI, peutEcrire } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from './LiasseFiscale.module.css'
import ImportBalanceLiasse from '../components/ImportBalanceLiasse.jsx'
import VentesPreparation from '../components/VentesPreparation.jsx'
import RasTvaRegistre from '../components/RasTvaRegistre.jsx'
import { numeroTableau, referenceEtic, NOTE_NUMEROTATION } from '../utils/liassePresentation.js'
import { telechargerXlsxAvecLogo } from '../services/exportXlsxLogo.js'

function montant(v) {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  return Number.isFinite(n) ? (n < 0 ? `(${formatMAD(Math.abs(n))})` : formatMAD(n)) : '—'
}

function Badge({ statut }) {
  const map = {
    finalisee: ['Finalisée', 'ok'], prete: ['Prête à finaliser', 'ready'], brouillon: ['À compléter', 'warn'],
  }
  const [label, cls] = map[statut] || [statut || 'Brouillon', 'warn']
  return <span className={`${styles.badge} ${styles[cls]}`}>{label}</span>
}

function Controle({ item }) {
  return (
    <div className={`${styles.controlRow} ${item.ok ? styles.controlOk : (item.bloquant ? styles.controlBad : styles.controlWarn)}`}>
      <i className={`ti ${item.ok ? 'ti-circle-check' : item.bloquant ? 'ti-alert-circle' : 'ti-alert-triangle'}`} />
      <div><strong>{item.libelle}</strong>{item.details && <span>{item.details}</span>}</div>
      <span className={styles.controlType}>{item.ok ? 'OK' : item.bloquant ? 'Bloquant' : 'Alerte'}</span>
    </div>
  )
}

function TableMontants({ headers, rows, empty = 'Aucune donnée.' }) {
  if (!rows?.length) return <div className={styles.empty}>{empty}</div>
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead><tr>{headers.map(h => <th key={h.key} className={h.num ? styles.num : ''}>{h.label}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={i} className={r.type === 'total' ? styles.totalRow : r.type === 'titre' ? styles.titleRow : r.type === 'detail' ? styles.detailRow : ''}>
            {headers.map(h => {
              const v = r[h.key]
              return <td key={h.key} className={h.num ? styles.num : h.key === 'libelle' && r.type === 'detail' ? styles.detailLabel : ''}>{h.num && (r.type === 'detail' || (v !== null && v !== undefined)) ? montant(v) : (v ?? '')}</td>
            })}
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function flattenBilan(data, side) {
  const detail = data?.etats?.bilan?.detail?.[side]
  if (Array.isArray(detail) && detail.length) return detail.map(r => {
    const keys = side === 'actif' ? ['brut', 'amort_prov', 'net', 'net_n1'] : ['montant', 'n1']
    return { type: r.type, code: r.numero || '', libelle: r.label,
      niveau: r.niveau || 0, ...Object.fromEntries(keys.map((key, i) => [key, r.valeurs?.[i] ?? null])) }
  })
  // Archives anciennes : lecture de leurs seules rubriques figées.
  const src = data?.etats?.bilan?.[side] || {}
  const sections = side === 'actif'
    ? [['immobilise', 'ACTIF IMMOBILISÉ'], ['circulant', 'ACTIF CIRCULANT'], ['tresorerie', 'TRÉSORERIE-ACTIF']]
    : [['capitaux_propres', 'CAPITAUX PROPRES'], ['financement_permanent', 'FINANCEMENT PERMANENT'], ['passif_circulant', 'PASSIF CIRCULANT'], ['tresorerie', 'TRÉSORERIE-PASSIF']]
  const out = []
  for (const [key, label] of sections) {
    out.push({ type: 'titre', code: '', libelle: label })
    for (const r of src[key] || []) out.push(r)
  }
  return out
}

function exporterExcel(data) {
  const wb = XLSX.utils.book_new()
  const add = (name, rows) => {
    const ws = XLSX.utils.aoa_to_sheet(rows)
    ws['!cols'] = rows[0]?.map((_, i) => ({ wch: i === 1 ? 42 : 18 })) || []
    XLSX.utils.book_append_sheet(wb, ws, name.slice(0, 31))
  }
  const s = data.societe || {}; const e = data.exercice_comptable || {}
  add('Synthese', [
    ['Liasse fiscale HisabPro', `Exercice ${data.exercice}`],
    ['Raison sociale', s.raison_sociale || ''], ['IF', s.identifiant_fiscal || ''], ['ICE', s.ice || ''], ['RC', s.rc || ''],
    ['Période', `${e.date_debut || ''} au ${e.date_fin || ''}`], ['Statut', data.statut],
    ['Repérage des tableaux', NOTE_NUMEROTATION],
    ...(data.archive ? [['Version archive', data.archive.version], ['Empreinte SHA-256', data.archive.empreinte_sha256]] : []), [],
    ['Contrôle', 'État', 'Détail'],
    ...(data.controles?.items || []).map(c => [c.libelle, c.ok ? 'OK' : (c.bloquant ? 'BLOQUANT' : 'ALERTE'), c.details || '']),
  ])
  const actif = flattenBilan(data, 'actif').filter(r => r.type !== 'titre')
  add(`${numeroTableau('BILAN')} Bilan Actif`, [['Réf.', 'Libellé', 'Brut N', 'Amort./Prov.', 'Net N', 'Net N-1'], ...actif.map(r => [r.code, `${r.type === 'detail' ? '    ' : ''}${r.libelle}`, r.brut, r.amort_prov, r.net, r.net_n1])])
  const passif = flattenBilan(data, 'passif').filter(r => r.type !== 'titre')
  add(`${numeroTableau('BILAN')} Bilan Passif`, [['Réf.', 'Libellé', 'N', 'N-1'], ...passif.map(r => [r.code, r.libelle, r.montant, r.n1])])
  add(`${numeroTableau('CPC')} CPC`, [['Réf.', 'Libellé', 'N', 'N-1'], ...(data.etats?.cpc?.lignes || []).filter(r => r.type !== 'titre').map(r => [r.code, r.libelle, r.montant, r.n1])])
  add('ESG', [['Réf.', 'Libellé', 'N', 'N-1'], ...(data.etats?.esg?.lignes || []).map(r => [r.code, r.libelle, r.montant, r.n1])])
  const tf = data.etats?.tableau_financement || {}
  if (tf.applicable === false) {
    add('Financement', [['Tableau de financement'], ['Non applicable', tf.motif_non_applicable || 'Comparatif N-1 indisponible.']])
  } else {
    add('Financement', [['Masse', 'N', 'N-1', 'Emploi', 'Ressource'], ...(tf.synthese || []).map(r => [r.libelle, r.n, r.n1, r.emploi, r.ressource]), [], ['Ressources', 'Montant'], ...(tf.ressources || []).map(r => [r.libelle, r.montant]), [], ['Emplois', 'Montant'], ...(tf.emplois || []).map(r => [r.libelle, r.montant])])
  }
  const fiscal = data.fiscal?.situation || {}
  add('Fiscal', [['Passage résultat comptable -> fiscal', 'Montant'], ...(data.fiscal?.passage_resultat_fiscal || []).map(r => [r.rubrique, r.montant]), [], ['IS théorique', fiscal.liquidation?.is_theorique || 0], ['CM exigible', fiscal.liquidation?.cm_exigible || 0], ['Impôt dû avant acomptes', fiscal.liquidation?.impot_du_avant_acomptes || 0], ['Solde à payer', fiscal.liquidation?.solde_a_payer || 0], ['Excédent total', fiscal.liquidation?.excedent_total || 0]])
  add('Detail CPC', [['Compte', 'Intitulé', 'Nature', 'Montant'], ...(data.etats?.detail_cpc || []).map(r => [r.compte, r.intitule, r.nature, r.montant])])
  const eticRows = [['ETIC — État des Informations Complémentaires', `Exercice ${data.exercice}`]]
  for (const sec of data.etic?.sections || []) {
    eticRows.push([], [referenceEtic(sec.code), sec.titre, sec.mode, sec.complete ? 'Complet' : 'À compléter'])
    const auto = sec.automatique || {}
    const cols = auto.colonnes || []
    const lignes = auto.lignes || []
    if (cols.length && lignes.length) {
      eticRows.push(cols)
      for (const ligne of lignes) eticRows.push(cols.map(c => ligne?.[c] ?? ''))
    }
    if (auto.avertissement) eticRows.push(['Contrôle', auto.avertissement])
    if (sec.code === 'B6' || sec.code === 'B7') {
      const keys = ['compte', 'intitule', 'total', 'plus_un_an', 'moins_un_an', 'echues', 'devises', 'etat_organismes_publics', 'entreprises_liees', 'effets']
      eticRows.push(['Ventilation par échéance et analyses complémentaires'],
        ['Compte', 'Intitulé', 'Total', '+ 1 an', '- 1 an', sec.code === 'B6' ? 'Échues non recouvrées' : 'Échues non payées', 'Devises', 'État / organismes publics', 'Entreprises liées', 'Effets'])
      for (const row of sec.ventilation || []) eticRows.push(keys.map(key => row?.[key] ?? 'À compléter'))
      for (const erreur of sec.erreurs_ventilation || []) eticRows.push(['Contrôle de ventilation', erreur])
      for (const ligne of lignes) {
        if (ligne.echeance_auto_total !== undefined && ligne.echeance_auto_total !== null) {
          eticRows.push(['Rapprochement', ligne.compte, 'Solde comptable', ligne.montant, 'Source factures', ligne.echeance_auto_total, 'Écart', ligne.echeance_auto_ecart, 'Source non qualifiée', ligne.echeance_auto_non_qualifie ?? 0])
        }
        for (const anomalie of ligne.echeance_auto_anomalies_sources || []) {
          eticRows.push(['Source à vérifier', ligne.compte, anomalie.numero || anomalie.facture_id, anomalie.reste_du, (anomalie.motifs || []).join(' ')])
        }
        for (const source of ligne.echeance_auto_sources_hors_solde || []) {
          eticRows.push(['Compte source absent des soldes', source.compte, source.total_source, 'À vérifier sans reclassification automatique'])
          for (const anomalie of source.anomalies_sources || []) {
            eticRows.push(['Source à vérifier', source.compte, anomalie.numero || anomalie.facture_id, anomalie.reste_du, (anomalie.motifs || []).join(' ')])
          }
        }
      }
    }
    const contenu = sec.contenu || {}
    if (contenu.neant) eticRows.push(['Complément', 'Néant pour l’exercice'])
    if (contenu.texte) eticRows.push(['Texte', contenu.texte])
    if (contenu.notes) eticRows.push(['Notes', contenu.notes])
    if (Array.isArray(contenu.lignes) && contenu.lignes.length) {
      const keys = []
      for (const ligne of contenu.lignes) for (const key of Object.keys(ligne || {})) if (!keys.includes(key)) keys.push(key)
      if (keys.length) {
        eticRows.push(keys)
        for (const ligne of contenu.lignes) eticRows.push(keys.map(k => ligne?.[k] ?? ''))
      }
    }
  }
  add('ETIC', eticRows)
  telechargerXlsxAvecLogo(XLSX, wb, `${(s.ice || 'HISABPRO').replace(/\s/g, '')}_LIASSE_${data.exercice}_${data.archive ? 'FINAL' : 'PROVISOIRE'}.xlsx`, s)
}

export default function LiasseFiscale() {
  const { annee } = useExercice(); const navigate = useNavigate()
  const [data, setData] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  const [tab, setTab] = useState('SYNTHESE'); const [busy, setBusy] = useState(false); const [message, setMessage] = useState('')
  const [anneeRegistre, setAnneeRegistre] = useState(null)

  async function charger() {
    setLoading(true); setError('')
    try { setData(await etatsAPI.liasse(annee)) } catch (e) { setError(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { charger() }, [annee])
  useEffect(() => { setAnneeRegistre(null) }, [annee])

  async function pdf() {
    setBusy(true); setMessage('')
    try {
      const f = await etatsAPI.telechargerLiassePDF(annee, Boolean(data?.archive))
      if (!f) return
      const url = URL.createObjectURL(f.blob); const a = document.createElement('a'); a.href = url; a.download = f.filename; a.click(); URL.revokeObjectURL(url)
    } catch (e) { setMessage(e.message) } finally { setBusy(false) }
  }

  async function finaliser() {
    if (!window.confirm(`Finaliser et archiver la liasse fiscale ${annee} ? Cette version deviendra immuable.`)) return
    setBusy(true); setMessage('')
    try { const r = await etatsAPI.finaliserLiasse(annee); setMessage(`Liasse finalisée — empreinte ${r.empreinte_sha256.slice(0, 12)}…`); await charger() }
    catch (e) { setMessage(e.message) } finally { setBusy(false) }
  }

  const tabs = [
    ['SYNTHESE', 'Synthèse'], ['BILAN', `${numeroTableau('BILAN')} · Bilan`], ['CPC', `${numeroTableau('CPC')} · CPC`], ['FISCAL', 'Fiscal'], ['ESG', 'ESG'], ['TF', 'Financement'], ['ETIC', 'T3–T25 · ETIC'], ['VENTES', 'Préparation ventes'], ['RAS_TVA', 'Retenues TVA'],
  ]
  const actif = useMemo(() => flattenBilan(data, 'actif'), [data]); const passif = useMemo(() => flattenBilan(data, 'passif'), [data])
  const fiscal = data?.fiscal?.situation || {}
  const debutCivil = Number(data?.exercice_comptable?.date_debut?.slice(0, 4)) || annee
  const finCivil = Number(data?.exercice_comptable?.date_fin?.slice(0, 4)) || annee
  const anneesCiviles = Number.isInteger(debutCivil) && Number.isInteger(finCivil) && finCivil >= debutCivil && finCivil <= 9999
    ? Array.from({ length: finCivil - debutCivil + 1 }, (_, i) => debutCivil + i) : [annee]
  const anneeCivileRegistre = anneesCiviles.includes(anneeRegistre) ? anneeRegistre : anneesCiviles[0]

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div><div className={styles.titleLine}><h1>Liasse fiscale</h1>{data && <Badge statut={data.statut} />}</div><p>Dossier de contrôle · Modèle normal · Exercice {annee}</p></div>
        <div className={styles.actionsTop}>
          <button className={styles.btnSec} disabled={!data || busy} onClick={() => exporterExcel(data)}><i className="ti ti-file-spreadsheet" /> Excel</button>
          <button className={styles.btnSec} disabled={!data || busy} onClick={pdf}><i className="ti ti-file-type-pdf" /> PDF</button>
          {!data?.archive && peutEcrire() && <button className={styles.btnPrim} disabled={!data?.controles?.pret_a_finaliser || busy} onClick={finaliser}><i className="ti ti-lock-check" /> Finaliser</button>}
          <button className={styles.btnDisabled} disabled title="Activation après validation du format EDI/XML SIMPL-IS courant"><i className="ti ti-cloud-upload" /> EDI SIMPL-IS</button>
        </div>
      </div>

      <div className={styles.content}>
        <ImportBalanceLiasse key={annee} exercice={annee} />
        {loading && <div className={styles.loading}>Construction de la liasse…</div>}
        {error && <div className={styles.error}>{error}</div>}
        {!loading && data && <>
          <div className={styles.identity}>
            <div><span>Raison sociale</span><strong>{data.societe?.raison_sociale || '—'}</strong></div>
            <div><span>IF</span><strong>{data.societe?.identifiant_fiscal || '—'}</strong></div>
            <div><span>ICE</span><strong>{data.societe?.ice || '—'}</strong></div>
            <div><span>Exercice</span><strong>{data.exercice_comptable?.date_debut} → {data.exercice_comptable?.date_fin}</strong></div>
          </div>
          {data.archive && <div className={styles.archiveBanner}><i className="ti ti-shield-check" /><div><strong>Archive fiscale immuable — version {data.archive.version}</strong><span>Empreinte SHA-256 : {data.archive.empreinte_sha256}</span></div></div>}
          {message && <div className={styles.info}>{message}</div>}
          <div className={styles.ediNote}><i className="ti ti-info-circle" /><span>{NOTE_NUMEROTATION}</span></div>
          <div className={styles.tabs}>{tabs.map(([id, label]) => <button key={id} onClick={() => setTab(id)} className={tab === id ? styles.activeTab : ''}>{label}</button>)}</div>

          {tab === 'VENTES' && <VentesPreparation />}

          {tab === 'RAS_TVA' && <>
            <div className={styles.info}>Suivi interne à la date de consultation, distinct des tableaux T1–T25. Le registre couvre l’année civile entière choisie, même si l’exercice est décalé. Ses téléchargements ne sont pas inclus dans les exports ni dans l’archive immuable de la liasse.</div>
            <label>Année civile du registre{' '}
              <select aria-label="Année civile du registre" value={anneeCivileRegistre} onChange={e => setAnneeRegistre(Number(e.target.value))}>
                {anneesCiviles.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </label>
            <RasTvaRegistre key={`${annee}:${anneeCivileRegistre}`} annee={anneeCivileRegistre} />
          </>}

          {tab === 'SYNTHESE' && <div className={styles.grid2}>
            <section className={styles.card}>
              <div className={styles.cardHeader}><h2>Contrôles de finalisation</h2><span>{data.controles.nb_bloquants} bloquant(s)</span></div>
              <div className={styles.controls}>{data.controles.items.map(c => <Controle key={c.code} item={c} />)}</div>
            </section>
            <section className={styles.card}>
              <div className={styles.cardHeader}><h2>Chiffres clés</h2></div>
              <div className={styles.kpis}>
                <div><span>Total actif</span><strong>{montant(data.etats?.bilan?.actif?.total?.net)} MAD</strong></div>
                <div><span>Résultat net</span><strong>{montant(data.etats?.cpc?.resultat_net)} MAD</strong></div>
                <div><span>Bénéfice fiscal imposable</span><strong>{montant(fiscal.calcul?.benefice_fiscal_imposable)} MAD</strong></div>
                <div><span>Impôt dû avant acomptes</span><strong>{montant(fiscal.liquidation?.impot_du_avant_acomptes)} MAD</strong></div>
                <div><span>ETIC</span><strong>{data.etic?.progression?.completes}/{data.etic?.progression?.total}</strong></div>
                <div><span>Écritures validées</span><strong>{data.source?.n?.source?.ecritures_validees_incluses || 0}</strong></div>
              </div>
              <div className={styles.ediNote}><i className="ti ti-info-circle" /><span>L'export PDF/Excel est disponible. L'envoi EDI direct reste désactivé tant que le schéma XML SIMPL-IS applicable n'a pas été vérifié auprès d'une source officielle.</span></div>
            </section>
          </div>}

          {tab === 'BILAN' && <div className={styles.grid2}>
            {data.etats?.bilan?.detail && <div className={`${styles.info} ${styles.full}`}>Sous-postes pour mémoire : ils ne s'ajoutent pas aux rubriques ni aux totaux. Les amortissements et nets non ventilés restent « — ».</div>}
            <section className={styles.card}><div className={styles.cardHeader}><h2>{numeroTableau('BILAN')} · Bilan — Actif</h2></div><TableMontants headers={[{key:'code',label:'Réf.'},{key:'libelle',label:'Libellé'},{key:'brut',label:'Brut N',num:true},{key:'amort_prov',label:'Amort./Prov.',num:true},{key:'net',label:'Net N',num:true},{key:'net_n1',label:'Net N-1',num:true}]} rows={actif} /></section>
            <section className={styles.card}><div className={styles.cardHeader}><h2>{numeroTableau('BILAN')} · Bilan — Passif</h2></div><TableMontants headers={[{key:'code',label:'Réf.'},{key:'libelle',label:'Libellé'},{key:'montant',label:'N',num:true},{key:'n1',label:'N-1',num:true}]} rows={passif} /></section>
          </div>}

          {tab === 'CPC' && <section className={styles.card}><div className={styles.cardHeader}><h2>{numeroTableau('CPC')} · Compte de Produits et Charges</h2></div><TableMontants headers={[{key:'code',label:'Réf.'},{key:'libelle',label:'Libellé'},{key:'montant',label:'N',num:true},{key:'n1',label:'N-1',num:true}]} rows={data.etats?.cpc?.lignes || []} /></section>}

          {tab === 'FISCAL' && <div className={styles.grid2}>
            <section className={styles.card}><div className={styles.cardHeader}><h2>Passage résultat comptable → fiscal</h2></div><TableMontants headers={[{key:'rubrique',label:'Rubrique'},{key:'montant',label:'Montant',num:true}]} rows={data.fiscal?.passage_resultat_fiscal || []} /></section>
            <section className={styles.card}><div className={styles.cardHeader}><h2>IS / CM / liquidation</h2></div><div className={`${styles.kpis} ${styles.vertical}`}>
              <div><span>IS théorique</span><strong>{montant(fiscal.liquidation?.is_theorique)} MAD</strong></div>
              <div><span>CM exigible</span><strong>{montant(fiscal.liquidation?.cm_exigible)} MAD</strong></div>
              <div><span>Impôt dû</span><strong>{montant(fiscal.liquidation?.impot_du_avant_acomptes)} MAD</strong></div>
              <div><span>Solde à payer</span><strong>{montant(fiscal.liquidation?.solde_a_payer)} MAD</strong></div>
              <div><span>Liquidation</span><strong>{fiscal.liquidation?.confirmee ? 'Confirmée' : 'À confirmer'}</strong></div>
            </div></section>
            <section className={`${styles.card} ${styles.full}`}><div className={styles.cardHeader}><h2>Détail du CPC par compte</h2></div><TableMontants headers={[{key:'compte',label:'Compte'},{key:'intitule',label:'Intitulé'},{key:'nature',label:'Nature'},{key:'montant',label:'Montant',num:true}]} rows={data.etats?.detail_cpc || []} /></section>
          </div>}

          {tab === 'ESG' && <section className={styles.card}><div className={styles.cardHeader}><h2>État des Soldes de Gestion</h2></div><TableMontants headers={[{key:'code',label:'Réf.'},{key:'libelle',label:'Libellé'},{key:'montant',label:'N',num:true},{key:'n1',label:'N-1',num:true}]} rows={data.etats?.esg?.lignes || []} /></section>}

          {tab === 'TF' && (data.etats?.tableau_financement?.applicable === false ? (
            <section className={styles.card}>
              <div className={styles.cardHeader}><h2>Tableau de financement</h2></div>
              <div className={styles.empty}>
                {data.etats?.tableau_financement?.motif_non_applicable || 'Comparatif N-1 indisponible : le tableau de financement ne peut pas être établi.'}
              </div>
            </section>
          ) : <div className={styles.grid2}>
            <section className={`${styles.card} ${styles.full}`}><div className={styles.cardHeader}><h2>Tableau de financement — synthèse</h2></div><TableMontants headers={[{key:'libelle',label:'Masse'},{key:'n',label:'N',num:true},{key:'n1',label:'N-1',num:true},{key:'emploi',label:'Emploi',num:true},{key:'ressource',label:'Ressource',num:true}]} rows={data.etats?.tableau_financement?.synthese || []} /></section>
            <section className={styles.card}><div className={styles.cardHeader}><h2>Ressources stables</h2></div><TableMontants headers={[{key:'libelle',label:'Libellé'},{key:'montant',label:'Montant',num:true}]} rows={data.etats?.tableau_financement?.ressources || []} /></section>
            <section className={styles.card}><div className={styles.cardHeader}><h2>Emplois stables</h2></div><TableMontants headers={[{key:'libelle',label:'Libellé'},{key:'montant',label:'Montant',num:true}]} rows={data.etats?.tableau_financement?.emplois || []} /></section>
          </div>)}

          {tab === 'ETIC' && <section className={styles.card}>
            <div className={styles.cardHeader}><div><h2>T3–T25 · ETIC</h2><span>{data.etic?.progression?.completes}/{data.etic?.progression?.total} sections complètes</span></div><button className={styles.btnSec} onClick={() => navigate('/etic')}>Ouvrir l'ETIC</button></div>
            <div className={styles.eticGrid}>{(data.etic?.sections || []).map(s => <div key={s.code} className={`${styles.eticItem} ${s.complete ? styles.eticOk : styles.eticTodo}`}><strong>{numeroTableau(s.code)}</strong><span>{s.code} — {s.titre}</span><em>{s.complete ? 'Complet' : 'À compléter'}</em></div>)}</div>
          </section>}
        </>}
      </div>
    </div>
  )
}
