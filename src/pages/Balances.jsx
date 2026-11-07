import React, { useState, useMemo, useEffect, useRef } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { formatMAD } from '../data/donnees.js'
import styles from './Balances.module.css'
import { API_BASE, comptabiliteAPI } from '../services/api.js'
import { exporterCSV } from '../services/exportCSV.js'
import { exporterBalanceExcel, exporterBalancePDF } from '../services/exportBalances.js'

// ── Helpers ───────────────────────────────────────────────────────────────────
function ExportsBalance({ nom, colonnes, lignes, titre, societe, periode, genre, annee, dateDebut, dateFin, typeTiers = 'client', totaux = [], synthese = [], disabled = false }) {
  const [occupation, setOccupation] = useState(false)
  const [erreurExport, setErreurExport] = useState('')
  async function lancer(format) {
    if (occupation || disabled || !societe?.id || !lignes.length) return
    setOccupation(true); setErreurExport('')
    try {
      if (format === 'excel') await exporterBalanceExcel(nom, colonnes, lignes, { titre, societe, periode, filtre: ['generale', 'resultat', 'comparative'].includes(genre) ? 'Écritures définitives · mouvements de la période' : typeTiers === 'client' ? 'Clients (3421)' : 'Fournisseurs (4411)', totaux, synthese })
      else if (format === 'pdf') await exporterBalancePDF({ genre, annee, dateDebut, dateFin, typeTiers })
      else exporterCSV(nom, colonnes, lignes)
    } catch (e) { setErreurExport(e.message) }
    finally { setOccupation(false) }
  }
  return <div><div className={styles.exportsActions}>{[['csv', 'CSV'], ['excel', 'Excel'], ['pdf', 'PDF']].map(([format, label]) => <button key={format} className={styles.exportBtn} disabled={occupation || disabled || !societe?.id || !lignes.length} onClick={() => lancer(format)}><i className="ti ti-download" aria-hidden="true" /> Exporter {label}</button>)}</div>{erreurExport && <div role="alert" className={styles.warningBox}>{erreurExport}</div>}</div>
}

function fmt(n) { return n === 0 ? '—' : formatMAD(n) }
function classeLabel(cl) {
  return { 1:'Financement Permanent', 2:'Actif Immobilisé', 3:'Actif Circulant', 4:'Passif Circulant', 5:'Trésorerie', 6:'Charges', 7:'Produits' }[cl] || `Classe ${cl}`
}

function decalerAnneeISO(iso, delta = -1) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  if (!y || !m || !d) return iso
  const cible = y + delta
  const dernierJour = new Date(Date.UTC(cible, m, 0)).getUTCDate()
  const jour = Math.min(d, dernierJour)
  return `${String(cible).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(jour).padStart(2, '0')}`
}

// Calcule les mouvements débit/crédit pour chaque compte
function calculerBalanceComptes(ecritures) {
  const map = {}
  ecritures.forEach(e => {
    e.lignes.forEach(l => {
      if (!l.compte) return
      if (!map[l.compte]) map[l.compte] = { compte: l.compte, libelle: l.libelle || 'Compte non référencé', debit: 0, credit: 0 }
      map[l.compte].debit  += l.debit  || 0
      map[l.compte].credit += l.credit || 0
    })
  })
  return map
}

// ── Onglet 1 : Balance Générale Détaillée ────────────────────────────────────
function BalanceGenerale({ comptes, societe, dateDebut, dateFin, annee }) {
  const lignes = useMemo(() => (comptes || [])
    .map(c => {
      const debit = Number(c.debit || 0)
      const credit = Number(c.credit || 0)
      const soldeInitial = Number(c.solde_initial || 0)
      const soldeFinal = Number(c.solde_final ?? (soldeInitial + debit - credit))
      return {
        compte: c.compte,
        libelle: c.libelle || 'Compte non référencé',
        classe: parseInt(c.compte?.[0]) || 0,
        debit,
        credit,
        soldeInitial,
        initialD: Math.max(0, soldeInitial),
        initialC: Math.max(0, -soldeInitial),
        soldeFinal,
        soldeD: Math.max(0, soldeFinal),
        soldeC: Math.max(0, -soldeFinal),
      }
    })
    .sort((a, b) => a.compte.localeCompare(b.compte)), [comptes])

  const parClasse = useMemo(() => {
    const map = {}
    lignes.forEach(l => {
      if (!map[l.classe]) map[l.classe] = { initialD: 0, initialC: 0, debit: 0, credit: 0, soldeD: 0, soldeC: 0 }
      map[l.classe].initialD += l.initialD
      map[l.classe].initialC += l.initialC
      map[l.classe].debit += l.debit
      map[l.classe].credit += l.credit
      map[l.classe].soldeD += l.soldeD
      map[l.classe].soldeC += l.soldeC
    })
    return map
  }, [lignes])

  const totaux = useMemo(() => lignes.reduce((t, l) => ({
    initialD: t.initialD + l.initialD,
    initialC: t.initialC + l.initialC,
    debit: t.debit + l.debit,
    credit: t.credit + l.credit,
    soldeD: t.soldeD + l.soldeD,
    soldeC: t.soldeC + l.soldeC,
  }), { initialD: 0, initialC: 0, debit: 0, credit: 0, soldeD: 0, soldeC: 0 }), [lignes])

  const ecartOuverture = totaux.initialD - totaux.initialC
  const ecartMouvements = totaux.debit - totaux.credit
  const ecartFinal = totaux.soldeD - totaux.soldeC
  const equilibree = [ecartOuverture, ecartMouvements, ecartFinal].every(x => Math.abs(x) < 0.01)

  if (lignes.length === 0) return <div className={styles.vide}><i className="ti ti-inbox" /><span>Aucune écriture pour la période</span></div>

  let classeEnCours = null

  return (
    <div>
      <div className={styles.entete}>
        <div><strong>Raison Sociale :</strong> {societe?.raison_sociale || '—'}</div>
        <div><strong>Période :</strong> {dateDebut} – {dateFin}</div>
        <div><strong>Devise :</strong> MAD</div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <ExportsBalance nom={`balance_generale_${dateFin}`} titre="Balance générale" colonnes={[
          { label: 'Compte', get: l => l.compte },
          { label: 'Libellé', get: l => l.libelle },
          { label: 'Solde initial débiteur', get: l => l.initialD, type: 'nombre' },
          { label: 'Solde initial créditeur', get: l => l.initialC, type: 'nombre' },
          { label: 'Mouvement débit', get: l => l.debit, type: 'nombre' },
          { label: 'Mouvement crédit', get: l => l.credit, type: 'nombre' },
          { label: 'Solde final débiteur', get: l => l.soldeD, type: 'nombre' },
          { label: 'Solde final créditeur', get: l => l.soldeC, type: 'nombre' },
        ]} lignes={lignes} societe={societe} periode={`${dateDebut} au ${dateFin}`} genre="generale" annee={annee} dateDebut={dateDebut} dateFin={dateFin} totaux={['TOTAL GÉNÉRAL', '', totaux.initialD, totaux.initialC, totaux.debit, totaux.credit, totaux.soldeD, totaux.soldeC]} />
      </div>

      <div className={styles.tableWrapper}>
        <table className={`${styles.table} ${styles.tableLarge}`}>
          <thead>
            <tr className={styles.theadBleu}>
              <th>N° Compte</th>
              <th>Intitulé du Compte</th>
              <th style={{ textAlign: 'right' }}>Initial D</th>
              <th style={{ textAlign: 'right' }}>Initial C</th>
              <th style={{ textAlign: 'right' }}>Mvt Débit</th>
              <th style={{ textAlign: 'right' }}>Mvt Crédit</th>
              <th style={{ textAlign: 'right' }}>Final D</th>
              <th style={{ textAlign: 'right' }}>Final C</th>
            </tr>
          </thead>
          <tbody>
            {lignes.map((l, i) => {
              const nouvelleClasse = l.classe !== classeEnCours
              classeEnCours = l.classe
              return (
                <React.Fragment key={l.compte}>
                  {nouvelleClasse && (
                    <tr className={styles.rowClasse}>
                      <td colSpan={8}>COMPTES CLASSE {l.classe} — {classeLabel(l.classe).toUpperCase()}</td>
                    </tr>
                  )}
                  <tr className={i % 2 === 0 ? styles.rowPair : ''}>
                    <td><span className={styles.compteBadge}>{l.compte}</span></td>
                    <td>{l.libelle || <span style={{ color: 'var(--text-tertiary)' }}>Compte non référencé</span>}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(l.initialD)}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(l.initialC)}</td>
                    <td style={{ textAlign: 'right', color: 'var(--blue)' }}>{fmt(l.debit)}</td>
                    <td style={{ textAlign: 'right', color: '#854F0B' }}>{fmt(l.credit)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 500, color: l.soldeD > 0 ? 'var(--blue)' : 'var(--text-tertiary)' }}>{fmt(l.soldeD)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 500, color: l.soldeC > 0 ? 'var(--red)' : 'var(--text-tertiary)' }}>{fmt(l.soldeC)}</td>
                  </tr>
                  {(i === lignes.length - 1 || lignes[i + 1]?.classe !== l.classe) && parClasse[l.classe] && (
                    <tr className={styles.rowTotal}>
                      <td colSpan={2}>TOTAL CLASSE {l.classe}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].initialD)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].initialC)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].debit)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].credit)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].soldeD)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(parClasse[l.classe].soldeC)}</td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
          <tfoot>
            <tr className={styles.rowGrandTotal}>
              <td colSpan={2}>TOTAL GÉNÉRAL</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.initialD)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.initialC)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.debit)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.credit)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.soldeD)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.soldeC)}</td>
            </tr>
            <tr style={{ background: equilibree ? '#EAF3DE' : '#FCEBEB' }}>
              <td colSpan={8} style={{ textAlign: 'center', fontSize: 12, fontWeight: 500, padding: '6px 12px' }}>
                {equilibree
                  ? '✓ Balance équilibrée — ouverture, mouvements et solde final contrôlés'
                  : `⚠ Écarts — ouverture ${formatMAD(Math.abs(ecartOuverture))} · mouvements ${formatMAD(Math.abs(ecartMouvements))} · final ${formatMAD(Math.abs(ecartFinal))} MAD`}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

// ── Onglet 2 : Balance Âgée ───────────────────────────────────────────────────
function BalanceAgee({ societe, dateRef, annee }) {
  const [typeClient, setTypeClient] = useState('client')
  const [situation, setSituation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const connu = value => typeof value === 'number' && Number.isFinite(value)
  const afficher = value => connu(value) ? formatMAD(value) : 'À vérifier'
  const tranche = value => connu(value) ? (value ? formatMAD(value) : '—') : 'À vérifier'

  // Une seule source de vérité : le moteur serveur de recouvrement tient compte
  // des règlements actifs, avoirs, utilisations de crédits, imputations d'acomptes
  // annulées/actives, RAS et échéanciers contractuels.
  useEffect(() => {
    let annule = false
    async function charger() {
      setLoading(true); setErreur(''); setSituation(null)
      try {
        const token = localStorage.getItem('hisabpro_token')
        const headers = { Authorization: `Bearer ${token}` }
        const qs = new URLSearchParams({ exercice: String(annee), date_reference: dateRef })
        const res = await fetch(`${API_BASE}/api/recouvrement/situation?${qs.toString()}`, { headers })
        if (!res.ok) {
          let message = 'Erreur de chargement de la balance âgée'
          try { const body = await res.json(); message = body.detail || message } catch (_) {}
          throw new Error(message)
        }
        const data = await res.json()
        if (!annule) setSituation(data)
      } catch (e) {
        if (!annule) setErreur(e.message)
      } finally {
        if (!annule) setLoading(false)
      }
    }
    charger()
    return () => { annule = true }
  }, [annee, dateRef, societe?.id])

  const typeFacture = typeClient === 'client' ? 'vente' : 'achat'
  const lignes = useMemo(() => {
    const parTiers = {}
    const rows = (situation?.factures || []).filter(f => f.type === typeFacture && (!connu(f.reste_du) || f.reste_du > 0.01))
    rows.forEach(f => {
      const indetermine = !connu(f.reste_du)
      const tr = { nonEchu: indetermine ? null : 0, t1: indetermine ? null : 0, t2: indetermine ? null : 0, t3: indetermine ? null : 0, t4: indetermine ? null : 0 }
      const correspondance = { non_echu: 'nonEchu', '1_30': 't1', '31_60': 't2', '61_90': 't3', plus_90: 't4' }
      const echeances = Array.isArray(f.echeances) ? f.echeances.filter(e => connu(e.reste_du) && e.reste_du > 0.01) : []
      if (!indetermine && echeances.length) {
        echeances.forEach(e => {
          const cle = correspondance[e.tranche_age] || 'nonEchu'
          tr[cle] += e.reste_du
        })
      } else if (!indetermine) {
        const cle = correspondance[f.tranche_age] || 'nonEchu'
        tr[cle] = f.reste_du
      }
      const tiers = f.tiers || 'Tiers non renseigné'
      if (!parTiers[tiers]) parTiers[tiers] = { tiers, factures: [] }
      parTiers[tiers].factures.push({
        id: f.id,
        ref: f.numero,
        date: f.date,
        echeance: f.date_echeance || '—',
        montant: indetermine ? null : f.reste_du,
        diagnostic: indetermine ? (f.ras_anomalie || 'Solde indéterminable : vérifier les données de la facture.') : '',
        tranches: tr,
      })
    })
    return Object.values(parTiers)
  }, [situation, typeFacture])

  const totaux = useMemo(() => {
    const t = { total: 0, nonEchu: 0, t1: 0, t2: 0, t3: 0, t4: 0 }
    if (lignes.some(l => l.factures.some(f => !connu(f.montant)))) return Object.fromEntries(Object.keys(t).map(k => [k, null]))
    lignes.forEach(l => l.factures.forEach(f => {
      t.total += f.montant
      Object.keys(f.tranches).forEach(k => { t[k] += f.tranches[k] || 0 })
    }))
    return t
  }, [lignes])
  const incomplet = !connu(totaux.total)
  const pourcentage = value => incomplet ? 'À vérifier' : `${totaux.total > 0 ? (value / totaux.total * 100).toFixed(1) : 0}%`

  return (
    <div>
      <div className={styles.entete}>
        <div><strong>Raison Sociale :</strong> {societe?.raison_sociale || '—'}</div>
        <div><strong>Date d'arrêté :</strong> {dateRef}</div>
        <div><strong>Devise :</strong> MAD</div>
      </div>

      {incomplet && <div role="alert" className={styles.warningBox}>Balance âgée {typeClient === 'client' ? 'clients' : 'fournisseurs'} incomplète : montants et totaux à vérifier. Les factures indéterminables restent visibles.</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[{ val: 'client', label: 'Clients (3421)' }, { val: 'fournisseur', label: 'Fournisseurs (4411)' }].map(t => (
          <button key={t.val}
            className={`${styles.filtreBtn} ${typeClient === t.val ? styles.filtreBtnActif : ''}`}
            onClick={() => setTypeClient(t.val)}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <ExportsBalance nom={`balance_agee_${typeClient}_${dateRef}`} titre="Balance âgée" colonnes={[
            { label: 'Tiers',       get: l => l.tiers },
            { label: 'Facture',     get: l => l.ref },
            { label: 'Date',        get: l => l.date },
            { label: 'Échéance',    get: l => l.echeance },
            { label: 'Reste dû',    get: l => l.montant, type: 'nombre' },
            { label: 'Non échu',    get: l => l.tranches.nonEchu, type: 'nombre' },
            { label: '1-30 j',      get: l => l.tranches.t1, type: 'nombre' },
            { label: '31-60 j',     get: l => l.tranches.t2, type: 'nombre' },
            { label: '61-90 j',     get: l => l.tranches.t3, type: 'nombre' },
            { label: '+90 j',       get: l => l.tranches.t4, type: 'nombre' },
            ...(incomplet ? [{ label: 'Diagnostic', get: l => l.diagnostic }] : []),
          ]} lignes={lignes.flatMap(t => t.factures.map(f => ({ tiers: t.tiers, ...f })))} societe={societe} periode={`Arrêté au ${dateRef}`} genre="agee" annee={annee} dateDebut={`${annee}-01-01`} dateFin={dateRef} typeTiers={typeClient} disabled={loading || !!erreur} totaux={['TOTAL GÉNÉRAL', '', '', '', totaux.total, totaux.nonEchu, totaux.t1, totaux.t2, totaux.t3, totaux.t4, ...(incomplet ? ['Total indéterminé : à vérifier'] : [])]} />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-tertiary)' }}>Chargement...</div>
      ) : erreur ? (
        <div style={{ textAlign: 'center', padding: 32, color: '#A32D2D' }}>{erreur}</div>
      ) : (
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr className={styles.theadBleu}>
              <th>Tiers</th>
              <th>Référence</th>
              <th>Date</th>
              <th>Échéance</th>
              <th style={{ textAlign: 'right' }}>Reste à payer</th>
              <th style={{ textAlign: 'right', background: '#1a5276' }}>Non Échu</th>
              <th style={{ textAlign: 'right', background: '#2471a3' }}>1-30 j</th>
              <th style={{ textAlign: 'right', background: '#e67e22' }}>31-60 j</th>
              <th style={{ textAlign: 'right', background: '#e74c3c' }}>61-90 j</th>
              <th style={{ textAlign: 'right', background: '#922b21' }}>&gt; 90 j</th>
            </tr>
          </thead>
          <tbody>
            {lignes.length === 0 ? (
              <tr><td colSpan={10} style={{ textAlign: 'center', padding: 32, color: 'var(--text-tertiary)' }}>
                Aucune {typeClient === 'client' ? 'créance' : 'dette'} ouverte pour la période
              </td></tr>
            ) : lignes.map(l => l.factures.map((f, i) => (
              <tr key={f.id || `${l.tiers}-${i}`} className={i % 2 === 0 ? styles.rowPair : ''}>
                <td>{i === 0 ? <strong>{l.tiers}</strong> : ''}</td>
                <td style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{f.ref}{f.diagnostic && <div style={{ color: 'var(--red)' }}>{f.diagnostic}</div>}</td>
                <td style={{ fontSize: 11 }}>{f.date}</td>
                <td style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{f.echeance}</td>
                <td style={{ textAlign: 'right', fontWeight: 500 }}>{afficher(f.montant)}</td>
                <td style={{ textAlign: 'right', color: '#1a5276' }}>{tranche(f.tranches.nonEchu)}</td>
                <td style={{ textAlign: 'right', color: '#2471a3' }}>{tranche(f.tranches.t1)}</td>
                <td style={{ textAlign: 'right', color: '#e67e22' }}>{tranche(f.tranches.t2)}</td>
                <td style={{ textAlign: 'right', color: '#e74c3c' }}>{tranche(f.tranches.t3)}</td>
                <td style={{ textAlign: 'right', color: '#922b21', fontWeight: f.tranches.t4 ? 700 : 400 }}>{tranche(f.tranches.t4)}</td>
              </tr>
            )))}
          </tbody>
          <tfoot>
            <tr className={styles.rowGrandTotal}>
              <td colSpan={4}>TOTAL GÉNÉRAL</td>
              <td style={{ textAlign: 'right' }}>{afficher(totaux.total)}{incomplet ? '' : ' MAD'}</td>
              <td style={{ textAlign: 'right' }}>{afficher(totaux.nonEchu)}</td>
              <td style={{ textAlign: 'right' }}>{afficher(totaux.t1)}</td>
              <td style={{ textAlign: 'right', color: '#e67e22' }}>{afficher(totaux.t2)}</td>
              <td style={{ textAlign: 'right', color: '#e74c3c' }}>{afficher(totaux.t3)}</td>
              <td style={{ textAlign: 'right', color: '#922b21' }}>{afficher(totaux.t4)}</td>
            </tr>
            <tr style={{ background: 'var(--bg-secondary)' }}>
              <td colSpan={4} style={{ textAlign: 'right', fontSize: 11, color: 'var(--text-tertiary)', padding: '4px 12px' }}>% du Total</td>
              <td style={{ textAlign: 'right', fontSize: 11 }}>{incomplet ? 'À vérifier' : '100%'}</td>
              <td style={{ textAlign: 'right', fontSize: 11 }}>{pourcentage(totaux.nonEchu)}</td>
              <td style={{ textAlign: 'right', fontSize: 11 }}>{pourcentage(totaux.t1)}</td>
              <td style={{ textAlign: 'right', fontSize: 11, color: '#e67e22' }}>{pourcentage(totaux.t2)}</td>
              <td style={{ textAlign: 'right', fontSize: 11, color: '#e74c3c' }}>{pourcentage(totaux.t3)}</td>
              <td style={{ textAlign: 'right', fontSize: 11, color: '#922b21' }}>{pourcentage(totaux.t4)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
      )}
    </div>
  )
}


// ── Onglet 3 : Balance Auxiliaire ─────────────────────────────────────────────
function BalanceAuxiliaire({ auxiliaire, societe, dateDebut, dateFin, annee }) {
  const [typeTiers, setTypeTiers] = useState('client')
  const prefixe = typeTiers === 'client' ? '3421' : '4411'

  const lignes = useMemo(() => (auxiliaire?.[prefixe] || []).map((t, i) => {
    const soldeInitial = Number(t.solde_initial || 0)
    const debit = Number(t.debit || 0)
    const credit = Number(t.credit || 0)
    const soldeFinal = Number(t.solde_final ?? (soldeInitial + debit - credit))
    return {
      ...t,
      _key: t.tiers_id ? `tiers-${t.tiers_id}` : `${t.compte_auxiliaire || prefixe}-${t.tiers}-${i}`,
      soldeInitial,
      debit,
      credit,
      initialD: Math.max(0, soldeInitial),
      initialC: Math.max(0, -soldeInitial),
      soldeFinal,
      soldeD: Math.max(0, soldeFinal),
      soldeC: Math.max(0, -soldeFinal),
    }
  }), [auxiliaire, prefixe])

  const totaux = useMemo(() => lignes.reduce((t, l) => ({
    initialD: t.initialD + l.initialD,
    initialC: t.initialC + l.initialC,
    debit: t.debit + l.debit,
    credit: t.credit + l.credit,
    soldeD: t.soldeD + l.soldeD,
    soldeC: t.soldeC + l.soldeC,
  }), { initialD: 0, initialC: 0, debit: 0, credit: 0, soldeD: 0, soldeC: 0 }), [lignes])

  const nonIdentifies = lignes.filter(l => l.identifie === false).length

  return (
    <div>
      <div className={styles.entete}>
        <div><strong>Raison Sociale :</strong> {societe?.raison_sociale || '—'}</div>
        <div><strong>Période :</strong> {dateDebut} – {dateFin}</div>
        <div><strong>Compte général :</strong> {prefixe} – {typeTiers === 'client' ? 'Clients' : 'Fournisseurs'}</div>
        <div><strong>Devise :</strong> MAD</div>
      </div>

      <div className={styles.balanceToolbar}>
        <div style={{ display: 'flex', gap: 8 }}>
          {[{ val: 'client', label: 'Clients (3421)' }, { val: 'fournisseur', label: 'Fournisseurs (4411)' }].map(t => (
            <button key={t.val}
              className={`${styles.filtreBtn} ${typeTiers === t.val ? styles.filtreBtnActif : ''}`}
              onClick={() => setTypeTiers(t.val)}>
              {t.label}
            </button>
          ))}
        </div>
        <ExportsBalance nom={`balance_auxiliaire_${typeTiers}_${dateFin}`} titre="Balance auxiliaire" colonnes={[
          { label: 'Tiers', get: l => l.tiers },
          { label: 'Identifié', get: l => l.identifie === false ? 'Non' : 'Oui' },
          { label: 'Compte auxiliaire', get: l => l.compte_auxiliaire || '' },
          { label: 'Solde initial débiteur', get: l => l.initialD, type: 'nombre' },
          { label: 'Solde initial créditeur', get: l => l.initialC, type: 'nombre' },
          { label: 'Mouvement débit', get: l => l.debit, type: 'nombre' },
          { label: 'Mouvement crédit', get: l => l.credit, type: 'nombre' },
          { label: 'Solde final débiteur', get: l => l.soldeD, type: 'nombre' },
          { label: 'Solde final créditeur', get: l => l.soldeC, type: 'nombre' },
        ]} lignes={lignes} societe={societe} periode={`${dateDebut} au ${dateFin}`} genre="auxiliaire" annee={annee} dateDebut={dateDebut} dateFin={dateFin} typeTiers={typeTiers} totaux={['TOTAL GÉNÉRAL', '', '', totaux.initialD, totaux.initialC, totaux.debit, totaux.credit, totaux.soldeD, totaux.soldeC]} />
      </div>

      {nonIdentifies > 0 && (
        <div className={styles.warningBox}>
          <i className="ti ti-alert-triangle" /> {nonIdentifies} auxiliaire{nonIdentifies > 1 ? 's' : ''} non identifié{nonIdentifies > 1 ? 's' : ''} automatiquement. Le libellé comptable est affiché sans créer de rattachement artificiel à une fiche tiers.
        </div>
      )}

      <div className={styles.tableWrapper}>
        <table className={`${styles.table} ${styles.tableXLarge}`}>
          <thead>
            <tr className={typeTiers === 'client' ? styles.theadBleu : styles.theadBrun}>
              <th>Nom / Raison Sociale</th>
              <th>Compte aux.</th>
              <th style={{ textAlign: 'right' }}>Initial D</th>
              <th style={{ textAlign: 'right' }}>Initial C</th>
              <th style={{ textAlign: 'right' }}>Mvt Débit</th>
              <th style={{ textAlign: 'right' }}>Mvt Crédit</th>
              <th style={{ textAlign: 'right' }}>Final D</th>
              <th style={{ textAlign: 'right' }}>Final C</th>
            </tr>
          </thead>
          <tbody>
            {lignes.length === 0 ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: 'var(--text-tertiary)' }}>Aucune écriture sur ce compte</td></tr>
            ) : lignes.map((l, i) => (
              <tr key={l._key} className={i % 2 === 0 ? styles.rowPair : ''}>
                <td style={{ fontWeight: 500 }}>
                  {l.tiers}
                  {l.identifie === false && <span className={styles.badgeWarning}>Non identifié</span>}
                </td>
                <td>{l.compte_auxiliaire ? <span className={styles.compteBadge}>{l.compte_auxiliaire}</span> : '—'}</td>
                <td style={{ textAlign: 'right' }}>{fmt(l.initialD)}</td>
                <td style={{ textAlign: 'right' }}>{fmt(l.initialC)}</td>
                <td style={{ textAlign: 'right', color: 'var(--blue)' }}>{fmt(l.debit)}</td>
                <td style={{ textAlign: 'right', color: '#854F0B' }}>{fmt(l.credit)}</td>
                <td style={{ textAlign: 'right', fontWeight: 500, color: l.soldeD > 0 ? 'var(--blue)' : 'var(--text-tertiary)' }}>{fmt(l.soldeD)}</td>
                <td style={{ textAlign: 'right', fontWeight: 500, color: l.soldeC > 0 ? 'var(--red)' : 'var(--text-tertiary)' }}>{fmt(l.soldeC)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className={styles.rowGrandTotal}>
              <td colSpan={2}>TOTAL GÉNÉRAL</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.initialD)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.initialC)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.debit)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.credit)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.soldeD)}</td>
              <td style={{ textAlign: 'right' }}>{formatMAD(totaux.soldeC)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

// ── Onglet 4 : Balance Résultat ───────────────────────────────────────────────
function BalanceResultat({ ecritures, societe, dateDebut, dateFin, annee }) {
  const mouvements = useMemo(() => calculerBalanceComptes(ecritures), [ecritures])

  const charges = useMemo(() =>
    Object.values(mouvements)
      .filter(m => m.compte.startsWith('6'))
      .map(m => ({ ...m, libelle: m.libelle, solde: m.debit - m.credit }))
      .sort((a, b) => a.compte.localeCompare(b.compte))
  , [mouvements])

  const produits = useMemo(() =>
    Object.values(mouvements)
      .filter(m => m.compte.startsWith('7'))
      .map(m => ({ ...m, libelle: m.libelle, solde: m.credit - m.debit }))
      .sort((a, b) => a.compte.localeCompare(b.compte))
  , [mouvements])

  const totalCharges  = charges.reduce((s, l) => s + l.solde, 0)
  const totalProduits = produits.reduce((s, l) => s + l.solde, 0)
  const resultat      = totalProduits - totalCharges

  return (
    <div>
      <div className={styles.entete}>
        <div><strong>Raison Sociale :</strong> {societe?.raison_sociale || '—'}</div>
        <div><strong>Exercice :</strong> {dateDebut} – {dateFin}</div>
        <div><strong>Devise :</strong> MAD</div>
      </div>

      <ExportsBalance nom={`balance_resultat_${dateFin}`} titre="Balance résultat" colonnes={[
        { label: 'Compte', get: l => l.compte }, { label: 'Libellé', get: l => l.libelle },
        { label: 'Charges', get: l => l.charge, type: 'nombre' }, { label: 'Produits', get: l => l.produit, type: 'nombre' },
      ]} lignes={[...charges.map(l => ({ ...l, charge: l.solde, produit: 0 })), ...produits.map(l => ({ ...l, charge: 0, produit: l.solde }))]} societe={societe} periode={`${dateDebut} au ${dateFin}`} genre="resultat" annee={annee} dateDebut={dateDebut} dateFin={dateFin} totaux={['TOTAL', '', totalCharges, totalProduits]} synthese={[[resultat >= 0 ? 'Bénéfice' : 'Perte', Math.abs(resultat)], ['Résultat net signé', resultat]]} />

      {/* KPI résultat */}
      <div className={styles.resultatKpis}>
        {[
          { label: 'Total Charges', val: totalCharges, couleur: '#e74c3c', icon: 'ti-trending-down' },
          { label: 'Total Produits', val: totalProduits, couleur: '#3B6D11', icon: 'ti-trending-up' },
          { label: resultat >= 0 ? 'Bénéfice' : 'Perte', val: Math.abs(resultat), couleur: resultat >= 0 ? '#3B6D11' : '#e74c3c', icon: resultat >= 0 ? 'ti-circle-check' : 'ti-circle-x' },
        ].map(k => (
          <div key={k.label} className={styles.kpiCard} style={{ borderColor: k.couleur + '44' }}>
            <div className={styles.kpiLabel}>
              <i className={`ti ${k.icon}`} style={{ color: k.couleur }} /> {k.label}
            </div>
            <div className={styles.kpiValeur} style={{ color: k.couleur }}>
              {formatMAD(k.val)} <span style={{ fontSize: 13 }}>MAD</span>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.resultatGrille}>
        {/* Charges */}
        <div className={styles.resultatPanneau}>
          <div className={styles.sectionTitre} style={{ background: '#e74c3c' }}>CHARGES (Classe 6)</div>
          <table className={`${styles.table} ${styles.resultatTable}`}>
            <thead>
              <tr className={styles.theadRouge}>
                <th>N° Compte</th><th>Intitulé</th><th style={{ textAlign: 'right' }}>Montant</th>
              </tr>
            </thead>
            <tbody>
              {charges.map((l, i) => (
                <tr key={l.compte} className={i % 2 === 0 ? styles.rowPair : ''}>
                  <td><span className={styles.compteBadge}>{l.compte}</span></td>
                  <td>{l.libelle}</td>
                  <td style={{ textAlign: 'right', color: '#e74c3c', fontWeight: 500 }}>{fmt(l.solde)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className={styles.rowTotal}>
                <td colSpan={2}>TOTAL CHARGES</td>
                <td style={{ textAlign: 'right' }}>{formatMAD(totalCharges)} MAD</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Produits */}
        <div className={styles.resultatPanneau}>
          <div className={styles.sectionTitre} style={{ background: '#3B6D11' }}>PRODUITS (Classe 7)</div>
          <table className={`${styles.table} ${styles.resultatTable}`}>
            <thead>
              <tr className={styles.theadVert}>
                <th>N° Compte</th><th>Intitulé</th><th style={{ textAlign: 'right' }}>Montant</th>
              </tr>
            </thead>
            <tbody>
              {produits.map((l, i) => (
                <tr key={l.compte} className={i % 2 === 0 ? styles.rowPair : ''}>
                  <td><span className={styles.compteBadge}>{l.compte}</span></td>
                  <td>{l.libelle}</td>
                  <td style={{ textAlign: 'right', color: '#3B6D11', fontWeight: 500 }}>{fmt(l.solde)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className={styles.rowTotal}>
                <td colSpan={2}>TOTAL PRODUITS</td>
                <td style={{ textAlign: 'right' }}>{formatMAD(totalProduits)} MAD</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Résultat net */}
      <div style={{
        marginTop: 16, padding: '14px 20px', borderRadius: 8, textAlign: 'center',
        background: resultat >= 0 ? '#EAF3DE' : '#FCEBEB',
        border: `1px solid ${resultat >= 0 ? '#A7D87A' : '#F5BEBE'}`,
        fontSize: 15, fontWeight: 700, color: resultat >= 0 ? '#3B6D11' : '#e74c3c',
      }}>
        {resultat >= 0 ? '✓ Résultat comptable : bénéfice' : '✗ Résultat comptable : perte'} : {formatMAD(Math.abs(resultat))} MAD
      </div>
    </div>
  )
}

// ── Onglet 5 : Balance Comparative ────────────────────────────────────────────
function BalanceComparative({ ecritures, ecrituresN1, societe, annee, dateDebut, dateFin, dateDebutN1, dateFinN1 }) {
  const mvtN  = useMemo(() => calculerBalanceComptes(ecritures), [ecritures])
  const mvtN1 = useMemo(() => calculerBalanceComptes(ecrituresN1), [ecrituresN1])

  const comptes = useMemo(() => {
    const tous = new Set([...Object.keys(mvtN), ...Object.keys(mvtN1)])
    return [...tous].sort().map(compte => {
      const n  = mvtN[compte]  || { debit: 0, credit: 0 }
      const n1 = mvtN1[compte] || { debit: 0, credit: 0 }
      const soldeN  = n.debit  - n.credit
      const soldeN1 = n1.debit - n1.credit
      const variation = soldeN1 !== 0 ? ((soldeN - soldeN1) / Math.abs(soldeN1) * 100) : null
      return { compte, libelle: mvtN[compte]?.libelle || mvtN1[compte]?.libelle || 'Compte non référencé', soldeN, soldeN1, variation }
    })
  }, [mvtN, mvtN1])

  return (
    <div>
      <div className={styles.entete}>
        <div><strong>Raison Sociale :</strong> {societe?.raison_sociale || '—'}</div>
        <div><strong>Comparaison :</strong> {dateDebut} – {dateFin} vs {dateDebutN1} – {dateFinN1}</div>
        <div><strong>Devise :</strong> MAD</div>
      </div>

      <ExportsBalance nom={`balance_comparative_${dateFin}`} titre="Balance comparative des mouvements" colonnes={[
        { label: 'Compte', get: l => l.compte }, { label: 'Libellé', get: l => l.libelle },
        { label: `Solde ${annee - 1}`, get: l => l.soldeN1, type: 'nombre' },
        { label: `Solde ${annee}`, get: l => l.soldeN, type: 'nombre' },
        { label: 'Variation MAD', get: l => l.soldeN - l.soldeN1, type: 'nombre' },
        { label: 'Variation (%)', get: l => l.variation, type: 'variation' },
      ]} lignes={comptes} societe={societe} periode={`${dateDebut} au ${dateFin} comparé au ${dateDebutN1} au ${dateFinN1}`} genre="comparative" annee={annee} dateDebut={dateDebut} dateFin={dateFin} />

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr className={styles.theadBleu}>
              <th>N° Compte</th>
              <th>Intitulé</th>
              <th style={{ textAlign: 'right' }}>Solde {annee - 1}</th>
              <th style={{ textAlign: 'right' }}>Solde {annee}</th>
              <th style={{ textAlign: 'right' }}>Variation</th>
              <th style={{ textAlign: 'right' }}>Variation %</th>
            </tr>
          </thead>
          <tbody>
            {comptes.map((l, i) => {
              const variation = l.soldeN - l.soldeN1
              return (
                <tr key={l.compte} className={i % 2 === 0 ? styles.rowPair : ''}>
                  <td><span className={styles.compteBadge}>{l.compte}</span></td>
                  <td>{l.libelle}</td>
                  <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{fmt(l.soldeN1)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 500 }}>{fmt(l.soldeN)}</td>
                  <td style={{ textAlign: 'right', color: variation >= 0 ? '#3B6D11' : '#e74c3c', fontWeight: 500 }}>
                    {variation >= 0 ? '+' : ''}{fmt(variation)}
                  </td>
                  <td style={{ textAlign: 'right', fontSize: 11, color: l.variation === null ? 'var(--text-tertiary)' : l.variation >= 0 ? '#3B6D11' : '#e74c3c' }}>
                    {l.variation === null ? 'N/A' : `${l.variation >= 0 ? '+' : ''}${l.variation.toFixed(1)}%`}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Page principale ────────────────────────────────────────────────────────────
export default function Balances() {
  const { annee, exercice } = useExercice()
  const { societe } = useModules()
  const [onglet, setOnglet] = useState('generale')
  const [dateDebut, setDateDebut] = useState(() => exercice?.date_debut || `${annee}-01-01`)
  const [dateFin, setDateFin] = useState(() => exercice?.date_fin || `${annee}-12-31`)
  const [rapport, setRapport] = useState({ comptes: [], auxiliaire: { '3421': [], '4411': [] }, nb_ecritures: 0 })
  const [rapportN1, setRapportN1] = useState({ comptes: [], nb_ecritures: 0 })
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const periodeContexte = useRef({ annee, societeId: societe?.id ?? null, saisie: false })

  useEffect(() => {
    const precedent = periodeContexte.current
    const societeId = societe?.id ?? null
    const changement = precedent.annee !== annee
      || (precedent.societeId !== null && societeId !== null && precedent.societeId !== societeId)
    const saisie = changement ? false : precedent.saisie
    periodeContexte.current = { annee, societeId: societeId ?? precedent.societeId, saisie }
    // Le contexte peut arriver après la saisie d'un filtre : il ne doit pas
    // remplacer ce choix pour la même société et le même exercice.
    if (!saisie) {
      setDateDebut(exercice?.date_debut || `${annee}-01-01`)
      setDateFin(exercice?.date_fin || `${annee}-12-31`)
    }
  }, [annee, societe?.id, exercice?.date_debut, exercice?.date_fin])

  const dateDebutN1 = useMemo(() => decalerAnneeISO(dateDebut, -1), [dateDebut])
  const dateFinN1 = useMemo(() => decalerAnneeISO(dateFin, -1), [dateFin])

  useEffect(() => {
    let annule = false
    if (dateDebut && dateFin && dateDebut > dateFin) {
      setChargement(false)
      setErreur('La date de début doit être antérieure ou égale à la date de fin.')
      return () => { annule = true }
    }

    setChargement(true); setErreur('')
    Promise.all([
      comptabiliteAPI.balance(annee, { dateFrom: dateDebut, dateTo: dateFin }),
      comptabiliteAPI.balance(annee - 1, { dateFrom: dateDebutN1, dateTo: dateFinN1 }),
    ])
      .then(([n, n1]) => {
        if (!annule) {
          setRapport(n || { comptes: [], auxiliaire: { '3421': [], '4411': [] }, nb_ecritures: 0 })
          setRapportN1(n1 || { comptes: [], nb_ecritures: 0 })
        }
      })
      .catch(e => { if (!annule) setErreur(e.message) })
      .finally(() => { if (!annule) setChargement(false) })
    return () => { annule = true }
  }, [annee, societe?.id, dateDebut, dateFin, dateDebutN1, dateFinN1])

  // Les vues Résultat et Comparative travaillent sur les seuls mouvements de la
  // période. La Balance générale et l'auxiliaire utilisent directement les
  // soldes d'ouverture/final calculés par le serveur.
  const ecrituresFiltrees = useMemo(() => [{
    id: 'balance-serveur', date: dateFin,
    lignes: (rapport.comptes || []).map(c => ({ compte: c.compte, libelle: c.libelle, debit: Number(c.debit || 0), credit: Number(c.credit || 0) })),
  }], [rapport, dateFin])

  const ecrituresN1 = useMemo(() => [{
    id: 'balance-n1-serveur', date: dateFinN1,
    lignes: (rapportN1.comptes || []).map(c => ({ compte: c.compte, libelle: c.libelle, debit: Number(c.debit || 0), credit: Number(c.credit || 0) })),
  }], [rapportN1, dateFinN1])

  const ONGLETS = [
    { id: 'generale', label: 'Balance Générale', icon: 'ti-list-tree' },
    { id: 'agee', label: 'Balance Âgée', icon: 'ti-clock-hour-4' },
    { id: 'auxiliaire', label: 'Balance Auxiliaire', icon: 'ti-users' },
    { id: 'resultat', label: 'Balance Résultat', icon: 'ti-trending-up' },
    { id: 'comparative', label: 'Balance Comparative', icon: 'ti-arrows-left-right' },
  ]

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Balances comptables</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <label style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Du</label>
            <input className={styles.inputDate} type="date" value={dateDebut} onChange={e => { periodeContexte.current.saisie = true; setDateDebut(e.target.value) }} />
            <label style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Au</label>
            <input className={styles.inputDate} type="date" value={dateFin} onChange={e => { periodeContexte.current.saisie = true; setDateFin(e.target.value) }} />
          </div>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.onglets}>
          {ONGLETS.map(o => (
            <button key={o.id}
              className={`${styles.ongletBtn} ${onglet === o.id ? styles.ongletBtnActif : ''}`}
              onClick={() => setOnglet(o.id)}>
              <i className={`ti ${o.icon}`} /> {o.label}
            </button>
          ))}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.cardTitle}>{ONGLETS.find(o => o.id === onglet)?.label}</span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              {rapport.nb_ecritures || 0} écriture{(rapport.nb_ecritures || 0) > 1 ? 's' : ''} définitive(s) — {dateDebut} au {dateFin}
            </span>
          </div>
          <div style={{ padding: 16 }}>
            {chargement ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-tertiary)' }}>Chargement des balances définitives…</div>
            ) : erreur ? (
              <div style={{ textAlign: 'center', padding: 32, color: '#A32D2D' }}>{erreur}</div>
            ) : (
              <>
                {onglet === 'generale' && <BalanceGenerale annee={annee} comptes={rapport.comptes} societe={societe} dateDebut={dateDebut} dateFin={dateFin} />}
                {onglet === 'agee' && <BalanceAgee annee={annee} societe={societe} dateRef={dateFin} />}
                {onglet === 'auxiliaire' && <BalanceAuxiliaire annee={annee} auxiliaire={rapport.auxiliaire} societe={societe} dateDebut={dateDebut} dateFin={dateFin} />}
                {onglet === 'resultat' && <BalanceResultat annee={annee} ecritures={ecrituresFiltrees} societe={societe} dateDebut={dateDebut} dateFin={dateFin} />}
                {onglet === 'comparative' && <BalanceComparative ecritures={ecrituresFiltrees} ecrituresN1={ecrituresN1} societe={societe} annee={annee} dateDebut={dateDebut} dateFin={dateFin} dateDebutN1={dateDebutN1} dateFinN1={dateFinN1} />}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

