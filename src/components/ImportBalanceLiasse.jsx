import BalancePreparationLiquidationIS from './BalancePreparationLiquidationIS.jsx'
import BalancePreparationAcomptesIS from './BalancePreparationAcomptesIS.jsx'
import BalancePreparationTaxeProfessionnelle from './BalancePreparationTaxeProfessionnelle.jsx'
import BalancePreparationRemunerationsTiers from './BalancePreparationRemunerationsTiers.jsx'
import BalancePreparationCreditsIS from './BalancePreparationCreditsIS.jsx'
import BalancePreparationCSS from './BalancePreparationCSS.jsx'
import BalancePreparationCotisationMinimale from './BalancePreparationCotisationMinimale.jsx'
import BalancePreparationContexteFiscal from './BalancePreparationContexteFiscal.jsx'
import BalancePreparationC3Extra from './BalancePreparationC3Extra.jsx'
import BalancePreparationComparatifN2 from './BalancePreparationComparatifN2.jsx'
import BalancePreparationTva from './BalancePreparationTva.jsx'
import BalancePreparationPassageFiscal from './BalancePreparationPassageFiscal.jsx'
import BalancePreparationIndicateurs from './BalancePreparationIndicateurs.jsx'
import BalancePreparationResultatCourant from './BalancePreparationResultatCourant.jsx'
import BalancePreparationRaccordsMouvements from './BalancePreparationRaccordsMouvements.jsx'
import BalancePreparationMouvements from './BalancePreparationMouvements.jsx'
import BalancePreparationCessions from './BalancePreparationCessions.jsx'
import BalancePreparationEmetteurs from './BalancePreparationEmetteurs.jsx'
import BalancePreparationParticipations from './BalancePreparationParticipations.jsx'
import BalancePreparationNonValeurs from './BalancePreparationNonValeurs.jsx'
import BalancePreparationCpcDetail from './BalancePreparationCpcDetail.jsx'
import { useEffect, useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { etatsAPI, peutEcrire, getToken } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from '../pages/LiasseFiscale.module.css'
import { useModules } from '../data/ModulesContext.jsx'
import { telechargerXlsxAvecLogo } from '../services/exportXlsxLogo.js'
import BalancePreparationDetail from './BalancePreparationDetail.jsx'
import BalancePreparationEcheances from './BalancePreparationEcheances.jsx'
import BalancePreparationDocuments from './BalancePreparationDocuments.jsx'
import BalancePreparationEticAnnexes from './BalancePreparationEticAnnexes.jsx'
import BalancePreparationEticTables from './BalancePreparationEticTables.jsx'
import BalancePreparationEticNotes from './BalancePreparationEticNotes.jsx'
import BalancePreparationFinancement from './BalancePreparationFinancement.jsx'

export function lireBalance(workbook) {
  if (workbook.SheetNames.length !== 1) throw new Error('Fournir un fichier avec une seule feuille de balance.')
  const rows = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]], { header: 1, defval: '', raw: true })
  const head = (rows.shift() || []).map(v => String(v).trim().toLowerCase())
  if (new Set(head).size !== head.length || head.some(c => !['compte', 'debit', 'credit', 'intitule'].includes(c)) || !['compte', 'debit', 'credit'].every(c => head.includes(c))) {
    throw new Error('En-têtes requis : compte, debit, credit ; intitule facultatif. Un compte par ligne.')
  }
  const index = Object.fromEntries(head.map((h, i) => [h, i]))
  const result = rows.filter(r => r.some(v => v !== '')).map(r => ({
    compte: String(r[index.compte]).trim(), debit: r[index.debit], credit: r[index.credit],
  }))
  if (!result.length || result.length > 10000) throw new Error('Entre 1 et 10 000 comptes requis.')
  return result
}

function excelPreparation(data, exercice, societe) {
  const wb = XLSX.utils.book_new()
  const add = (name, rows) => XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), name)
  add('Limites', [['Préparation depuis balances importées', exercice], ['Statut', 'À compléter — aucune archive fiscale'],
    ...data.avertissements.map(x => [x]), ...data.a_completer.map(x => ['À compléter', x])])
  for (const [suffix, source] of [['N', data.etats], ['N-1', data.etats_n1]]) {
    if (!source) continue
    for (const code of ['cpc', 'esg']) add(`${code.toUpperCase()} ${suffix}`, source[code].disponible === false
      ? [['Indisponible', source[code].motif]]
      : [['Libellé', 'Montant MAD'], ...source[code].lignes.filter(r => r.montant !== null).map(r => [r.libelle, r.montant])])
    const b = source.bilan
    add(`Bilan ${suffix}`, [['Actif', 'Net MAD'], ...['immobilise', 'circulant', 'tresorerie'].flatMap(k => b.actif[k].map(r => [r.libelle, r.net])),
      ['Total actif', b.actif.total.net], [], ['Passif', 'Montant MAD'],
      ...['capitaux_propres', 'financement_permanent', 'passif_circulant', 'tresorerie'].flatMap(k => b.passif[k].map(r => [r.libelle, r.montant])),
      ['Total passif', b.passif.total]])
  }
  telechargerXlsxAvecLogo(XLSX, wb, `HisabPro_Preparation_Balances_${exercice}.xlsx`, societe)
}

export default function ImportBalanceLiasse({ exercice }) {
  const { societe } = useModules()
  const [files, setFiles] = useState({ n: null, n1: null })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const sourceVersion = useRef(0)
  const vivant = useRef(true)
  useEffect(() => { vivant.current = true; return () => { vivant.current = false; sourceVersion.current += 1 } }, [])
  const [sourceRows, setSourceRows] = useState(null)
  const [dossiers, setDossiers] = useState([])
  const [saved, setSaved] = useState(null)
  const writable = peutEcrire()
  const affichage = value => value == null ? 'Indisponible' : formatMAD(value)
  useEffect(() => {
    let active = true
    etatsAPI.preparationsBalance(exercice).then(rows => { if (active) setDossiers(rows) })
      .catch(e => { if (active) setError(e.message) })
    return () => { active = false }
  }, [exercice])
  async function importer() {
    const version = sourceVersion.current
    setError(''); setResult(null); setBusy(true)
    try {
      async function parse(file) {
        if (!file || file.size > 5000000) throw new Error('Fichier requis, limité à 5 Mo.')
        if (!/\.(csv|xlsx)$/i.test(file.name)) throw new Error('Format CSV ou XLSX requis.')
        const buffer = await file.arrayBuffer()
        return lireBalance(XLSX.read(buffer, { type: 'array', raw: true }))
      }
      const n = await parse(files.n)
      const n1 = files.n1 ? await parse(files.n1) : null
      if (version !== sourceVersion.current) return
      const data = await etatsAPI.preparerBalance(n, n1)
      if (version === sourceVersion.current) { setResult(data); setSourceRows({ lignes_n: n, lignes_n1: n1 }); setSaved(null) }
    } catch (e) {
      if (version === sourceVersion.current) setError(e.message)
    } finally { setBusy(false) }
  }
  const change = (key, file) => { sourceVersion.current += 1; setFiles(prev => ({ ...prev, [key]: file })); setResult(null); setSourceRows(null); setSaved(null); setError('') }
  async function conserver() {
    const version = sourceVersion.current
    setBusy(true); setError('')
    try {
      const row = await etatsAPI.conserverBalance({ exercice, ...sourceRows,
        fichier_n: files.n?.name || null, fichier_n1: files.n1?.name || null })
      if (version !== sourceVersion.current) return
      setSaved(row); setSourceRows(null)
      setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev])
    } catch (e) { if (version === sourceVersion.current) setError(e.message) }
    finally { setBusy(false) }
  }
  async function ouvrir(id) {
    const version = ++sourceVersion.current
    setBusy(true); setError(''); setResult(null); setSourceRows(null); setSaved(null)
    try {
      const row = await etatsAPI.preparationBalance(id)
      if (version === sourceVersion.current) { setResult(row.contenu.preparation); setSaved(row) }
    } catch (e) { if (version === sourceVersion.current) setError(e.message) }
    finally { setBusy(false) }
  }
  async function exporterVersion(format) {
    const version = sourceVersion.current, token = getToken()
    const actif = () => vivant.current && sourceVersion.current === version && getToken() === token
    setBusy(true); setError('')
    try {
      const file = await (format === 'zip' ? etatsAPI.preparationBalanceDossier(saved.id) : format === 'xlsx' ? etatsAPI.preparationBalanceExcel(saved.id) : etatsAPI.preparationBalancePDF(saved.id))
      if (!file || !actif()) return
      const url = URL.createObjectURL(file.blob)
      const a = document.createElement('a'); a.href = url; a.download = file.filename; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) { if (actif()) setError(e.message) } finally { if (actif()) setBusy(false) }
  }
  return <section className={styles.card} style={{ marginBottom: 20 }}>
    <div className={styles.cardHeader}><h2>Préparer depuis des balances externes</h2>
      <button className={styles.btnSec} onClick={() => setExpanded(!expanded)}>{expanded ? 'Masquer' : writable ? 'Importer N / N-1' : 'Consulter les préparations'}</button></div>
    {expanded && <div style={{ padding: 18, display: 'grid', gap: 14, minWidth: 0 }}>
      {dossiers.length > 0 && <div><label htmlFor="balance-preparation-version">Préparations conservées</label>
        <select id="balance-preparation-version" value={saved?.id || ''} disabled={busy} onChange={e => { if (e.target.value) ouvrir(e.target.value) }}>
          <option value="">Sélectionner une version</option>
          {dossiers.map(r => <option key={r.id} value={r.id}>Version {r.version} · {r.created_at?.slice(0, 10)}</option>)}
        </select></div>}
      {writable && <>
      <p>Balance avant clôture technique, un compte du plan de la société par ligne. En-têtes : compte, debit, credit. Montants positifs ou nuls en MAD. CSV ou XLSX, une feuille.</p>
      <label>Balance N<input aria-label="Balance N" type="file" accept=".csv,.xlsx" onChange={e => change('n', e.target.files[0])} style={{ maxWidth: '100%' }} /></label>
      <label>Balance N-1 facultative<input aria-label="Balance N-1 facultative" type="file" accept=".csv,.xlsx" onChange={e => change('n1', e.target.files[0])} style={{ maxWidth: '100%' }} /></label>
      <button className={styles.btnPrim} disabled={!files.n || busy} onClick={importer}>{busy ? 'Contrôle…' : 'Contrôler et préparer'}</button>
      </>}
      {!writable && dossiers.length === 0 && <p>Aucune préparation conservée pour cet exercice.</p>}
      {error && <div role="alert" className={styles.error}>{error}</div>}
      {result && <>
        <div role="status" className={styles.info}>Balances contrôlées — préparation à compléter. Aucune écriture créée.</div>
        <p>{result.balance_n.nb_comptes} comptes · Débit = crédit : {formatMAD(result.balance_n.total_debit)} MAD</p>
        <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th>Contrôle</th><th>N</th><th>N-1</th></tr></thead>
          <tbody>{[['Total actif', 'bilan', e => e.actif.total.net], ['Total passif', 'bilan', e => e.passif.total],
            ['Résultat net CPC', 'cpc', e => e.resultat_net], ['CAF', 'esg', e => e.caf]].map(([label, key, get]) =>
            <tr key={label}><td>{label}</td><td>{affichage(get(result.etats[key]))}</td><td>{result.etats_n1 ? affichage(get(result.etats_n1[key])) : 'Indisponible'}</td></tr>)}</tbody></table></div>
        {[result.etats.cpc, result.etats_n1?.cpc].filter(e => e?.disponible === false).map((e, i) => <p key={i}>{e.motif}</p>)}
        {result.avertissements.map(x => <p key={x}>{x}</p>)}
        <p>À compléter : {result.a_completer.join(' ; ')}.</p>
        {writable && sourceRows && <button className={styles.btnPrim} disabled={busy} onClick={conserver}>Conserver une nouvelle version</button>}
        {saved && <p style={{ overflowWrap: 'anywhere' }}>Version {saved.version} conservée · Empreinte des données normalisées : {saved.empreinte_sha256}</p>}
        {saved?.contenu?.sources?.noms_fichiers && <p>Sources déclarées : {Object.values(saved.contenu.sources.noms_fichiers).join(' ; ')}</p>}
        {saved && <BalancePreparationDetail dossier={saved} />}
        {saved && <BalancePreparationRaccordsMouvements key={`raccords-mouvements:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationMouvements key={`mouvements:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationCessions key={`cessions:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationEmetteurs key={`emetteurs:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationC3Extra key={`c3-extra:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationComparatifN2 key={`comparatif-n2:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationIndicateurs key={`indicateurs-c3:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationTva key={`tva-documentaire:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationPassageFiscal key={`passage-fiscal:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationContexteFiscal key={`contexte-fiscal:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationCotisationMinimale key={`cotisation-minimale:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationCSS key={`css-documentaire:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationTaxeProfessionnelle key={`taxe-professionnelle:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationRemunerationsTiers key={`remunerations-tiers:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationCreditsIS key={`credits-is:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationAcomptesIS key={`acomptes-is:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationLiquidationIS key={`liquidation-is:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationResultatCourant key={`resultat-courant:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationParticipations key={`participations:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationNonValeurs key={`nv:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationCpcDetail key={`cpc:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationFinancement key={`tf:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationEticTables key={`tables:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationEticAnnexes key={`annexes:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationEticNotes key={`etic:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        {saved && <BalancePreparationDocuments key={`docs:${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} />}
        {saved && <BalancePreparationEcheances key={`${saved.id}:${saved.empreinte_sha256}:${getToken()}`} dossier={saved} onConserve={row => {
          sourceVersion.current += 1
          setSaved(row); setResult(row.contenu.preparation); setSourceRows(null)
          setDossiers(prev => [{ id: row.id, version: row.version, created_at: row.created_at }, ...prev.filter(r => r.id !== row.id)])
        }} />}
        <button className={styles.btnSec} disabled={busy || !societe?.id} onClick={() => {
          if (saved) exporterVersion('xlsx')
          else { try { excelPreparation(result, exercice, societe) } catch (e) { setError(e.message) } }
        }}>Exporter la préparation Excel</button>
        {saved && <>
          <button className={styles.btnSec} disabled={busy} onClick={() => exporterVersion('pdf')}>Exporter la préparation PDF</button>
          <button className={styles.btnSec} disabled={busy} onClick={() => exporterVersion('zip')}>Télécharger le dossier de préparation ZIP</button>
          <p>Le ZIP regroupe cette version, PDF/XLSX avec logo actuel, sources normalisées et manifeste SHA-256. Dossier interne à compléter, sans archive fiscale définitive ni EDI officiel.</p>
          <p>Exports de la version conservée : bilan détaillé, comptes sources et empreinte. Les sous-postes sont pour mémoire ; les amortissements ne sont pas ventilés arbitrairement. L’identité et le logo actuels restent hors empreinte.</p>
        </>}
      </>}
    </div>}
  </section>
}
