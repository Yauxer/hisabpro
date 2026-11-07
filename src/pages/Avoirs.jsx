import React, { useState, useEffect, useMemo } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { formatMAD, formatDate } from '../data/donnees.js'
import Modal from '../components/Modal.jsx'
import styles from './Avoirs.module.css'
import { API_BASE, peutEcrire } from '../services/api.js'
import { telechargerDocumentPDF, preparerEmailDocument } from '../services/documentsCommerciaux.js'
import { dateLocaleISO, nombreOuDefaut } from '../utils/formUtils.js'
import { notifier } from '../services/notifications.js'

const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Erreur' })); throw new Error(e.detail) }
  if (res.status === 204) return null
  return res.json()
}

const STATUT_BADGE = {
  emis:      { bg: '#FAEEDA', color: '#854F0B', label: 'Émis' },
  utilise:   { bg: '#E6F1FB', color: '#185FA5', label: 'Utilisé' },
  rembourse: { bg: '#EAF3DE', color: '#3B6D11', label: 'Remboursé' },
  annule:    { bg: '#F3F4F6', color: '#6B7280', label: 'Annulé' },
}

function BadgeStatut({ statut }) {
  const b = STATUT_BADGE[statut] || STATUT_BADGE.emis
  return (
    <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: b.bg, color: b.color, fontWeight: 500 }}>
      {b.label}
    </span>
  )
}

function BadgeType({ type }) {
  return (
    <span style={{
      fontSize: 10, padding: '2px 8px', borderRadius: 4,
      background: type === 'vente' ? '#E6F1FB' : '#EAF3DE',
      color: type === 'vente' ? '#185FA5' : '#3B6D11',
    }}>
      {type === 'vente' ? 'Vente' : 'Achat'}
    </span>
  )
}

const NATURE_LABEL = {
  retour_annulation: 'Retour / annulation',
  rrr: 'RRR après facture',
  correction_prix: 'Correction de prix',
  autre: 'Autre avoir',
}
const MODES_PAIEMENT = { virement: 'Virement', cheque: 'Chèque', especes: 'Espèces', effet: 'Effet', carte: 'Carte', prelevement: 'Prélèvement', autre: 'Autre' }

function ModalUtiliserCredit({ avoir, typeUtilisation, onFermer, onSuccess }) {
  const [montant, setMontant] = useState(String(Number(avoir.montant_disponible || 0).toFixed(2)))
  const [date, setDate] = useState(dateLocaleISO())
  const [factures, setFactures] = useState([])
  const [factureId, setFactureId] = useState('')
  const [mode, setMode] = useState('virement')
  const [reference, setReference] = useState('')
  const [compensationSignee, setCompensationSignee] = useState(false)
  const [banques, setBanques] = useState([])
  const [compteBancaireId, setCompteBancaireId] = useState('')
  const [busy, setBusy] = useState(false)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    if (typeUtilisation === 'imputation') {
      apiFetch(`/api/avoirs/${avoir.id}/factures-imputables`).then(setFactures).catch(e => setErreur(e.message))
    } else {
      apiFetch('/api/banques').then(setBanques).catch(() => setBanques([]))
    }
  }, [avoir.id, typeUtilisation])

  const cible = factures.find(f => String(f.id) === String(factureId))
  const max = Math.min(Number(avoir.montant_disponible || 0), cible ? Number(cible.solde_restant || 0) : Number(avoir.montant_disponible || 0))

  async function valider() {
    const value = nombreOuDefaut(montant, 0)
    if (!(value > 0)) { setErreur('Le montant doit être strictement positif.'); return }
    if (value > max + 0.01) { setErreur(`Le maximum disponible est de ${formatMAD(max)} MAD.`); return }
    if (typeUtilisation === 'imputation' && !factureId) { setErreur('Choisissez la facture cible.'); return }
    if (typeUtilisation === 'imputation' && compensationSignee && !reference.trim()) { setErreur('Renseignez la référence de l’accord signé.'); return }
    setBusy(true); setErreur('')
    try {
      const banque = banques.find(b => String(b.id) === String(compteBancaireId))
      await apiFetch(`/api/avoirs/${avoir.id}/utiliser`, {
        method: 'POST', body: JSON.stringify({
          type_utilisation: typeUtilisation, montant: value, date_utilisation: date,
          facture_id: typeUtilisation === 'imputation' ? Number(factureId) : null,
          date_acceptation_compensation: typeUtilisation === 'imputation' && compensationSignee ? date : null,
          mode: typeUtilisation === 'remboursement' ? mode : null,
          compte_bancaire_id: typeUtilisation === 'remboursement' && compteBancaireId ? Number(compteBancaireId) : null,
          banque: typeUtilisation === 'remboursement' ? (banque?.banque || null) : null,
          reference: typeUtilisation === 'remboursement' || compensationSignee ? (reference.trim() || null) : null,
        }),
      })
      onSuccess?.(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setBusy(false) }
  }

  return <Modal titre={typeUtilisation === 'imputation' ? `Imputer le crédit — ${avoir.numero}` : `Rembourser le crédit — ${avoir.numero}`} icone={typeUtilisation === 'imputation' ? 'ti-arrow-merge' : 'ti-cash-banknote'} onFermer={onFermer} largeur="sm">
    <div className="hp-form-stack">
      {erreur && <div style={{ padding: 10, borderRadius: 6, background: '#FCEBEB', color: '#A32D2D', fontSize: 12 }}>{erreur}</div>}
      <div style={{ padding: 10, borderRadius: 8, background: 'var(--bg-secondary)', fontSize: 12 }}>
        Crédit libre disponible : <strong>{formatMAD(avoir.montant_disponible)} MAD</strong>
      </div>
      {typeUtilisation === 'imputation' && <div className="hp-field"><label>Facture cible</label><select value={factureId} onChange={e => { setFactureId(e.target.value); const f = factures.find(x => String(x.id) === e.target.value); if (f) setMontant(String(Math.min(Number(avoir.montant_disponible || 0), Number(f.solde_restant || 0)).toFixed(2))) }}><option value="">— Choisir —</option>{factures.map(f => <option key={f.id} value={f.id}>{f.numero} — reste {formatMAD(f.solde_restant)} MAD — {f.exercice}</option>)}</select></div>}
      <div className="hp-form-grid hp-form-grid--2">
        <div className="hp-field"><label>Montant (MAD)</label><input type="number" min="0.01" step="0.01" max={max} value={montant} onChange={e => setMontant(e.target.value)} /></div>
        <div className="hp-field"><label>Date</label><input type="date" value={date} onChange={e => setDate(e.target.value)} /></div>
      </div>
      {typeUtilisation === 'imputation' && <>
        <label style={{ display: 'flex', gap: 8, alignItems: 'start', fontSize: 12 }}><input type="checkbox" checked={compensationSignee} onChange={e => setCompensationSignee(e.target.checked)} />Accord de compensation signé par les parties à la date indiquée</label>
        {compensationSignee
          ? <div className="hp-field"><label htmlFor="accord-compensation-reference">Référence de l’accord signé</label><input id="accord-compensation-reference" maxLength={100} value={reference} onChange={e => setReference(e.target.value)} /></div>
          : <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>Sans confirmation de signature, l’imputation reste possible ; son traitement TVA sera signalé comme à qualifier.</p>}
      </>}
      {typeUtilisation === 'remboursement' && <>
        <div className="hp-form-grid hp-form-grid--2">
          <div className="hp-field"><label>Mode</label><select value={mode} onChange={e => setMode(e.target.value)}>{Object.entries(MODES_PAIEMENT).map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select></div>
          <div className="hp-field"><label>Référence</label><input value={reference} onChange={e => setReference(e.target.value)} placeholder="N° virement, chèque..." /></div>
        </div>
        {mode !== 'especes' && banques.length > 0 && <div className="hp-field"><label>Compte bancaire</label><select value={compteBancaireId} onChange={e => setCompteBancaireId(e.target.value)}><option value="">— Compte par défaut —</option>{banques.map(b => <option key={b.id} value={b.id}>{b.banque}{b.agence ? ` — ${b.agence}` : ''} · {b.compte_comptable || '5141'}</option>)}</select></div>}
      </>}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button><button className="hp-btn-primary" type="button" disabled={busy || !(nombreOuDefaut(montant,0) > 0) || (typeUtilisation === 'imputation' && !factureId)} onClick={valider}>{busy ? 'Enregistrement...' : (typeUtilisation === 'imputation' ? 'Imputer le crédit' : 'Enregistrer le remboursement')}</button></div>
    </div>
  </Modal>
}

export default function Avoirs() {
  const peutModifier = peutEcrire()
  const { annee } = useExercice()
  const { recharger: rechargerEcritures } = useEcritures() || {}

  const [avoirs, setAvoirs]   = useState([])
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur]   = useState('')

  const [filtreType, setFiltreType]     = useState('tous')     // tous | vente | achat
  const [filtreStatut, setFiltreStatut] = useState('tous')
  const [recherche, setRecherche]       = useState('')

  const [selectionne, setSelectionne] = useState(null) // avoir ouvert dans le panneau détail
  const [busy, setBusy]     = useState(false)
  const [msg, setMsg]       = useState('')
  const [utiliserCredit, setUtiliserCredit] = useState(null)

  function charger() {
    setLoading(true); setErreur('')
    apiFetch(`/api/avoirs?exercice=${annee}`)
      .then(data => setAvoirs(data))
      .catch(e => setErreur(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { charger() }, [annee])

  // Garder le panneau détail synchronisé avec la liste après refresh
  useEffect(() => {
    if (!selectionne) return
    const maj = avoirs.find(a => a.id === selectionne.id)
    if (maj) setSelectionne(maj)
  }, [avoirs]) // eslint-disable-line react-hooks/exhaustive-deps

  const avoirsFiltres = useMemo(() => {
    return avoirs.filter(a => {
      if (filtreType !== 'tous' && a.type !== filtreType) return false
      if (filtreStatut !== 'tous' && a.statut !== filtreStatut) return false
      if (recherche) {
        const r = recherche.toLowerCase()
        if (!a.numero?.toLowerCase().includes(r) &&
            !a.tiers?.toLowerCase().includes(r) &&
            !a.facture_numero?.toLowerCase().includes(r) &&
            !a.motif?.toLowerCase().includes(r)) return false
      }
      return true
    }).sort((a, b) => b.date.localeCompare(a.date))
  }, [avoirs, filtreType, filtreStatut, recherche])

  const stats = useMemo(() => {
    const nonComptabilises = avoirs.filter(a => !a.est_comptabilisee && a.statut !== 'annule').length
    const totalTTC = avoirs.filter(a => a.statut !== 'annule').reduce((s, a) => s + Number(a.total_ttc || 0), 0)
    const creditDisponible = avoirs.filter(a => a.statut !== 'annule').reduce((s, a) => s + Number(a.montant_disponible || 0), 0)
    return { total: avoirs.length, nonComptabilises, totalTTC, creditDisponible }
  }, [avoirs])

  async function comptabiliser(avoir) {
    if (!confirm(`Comptabiliser l'avoir ${avoir.numero} (${formatMAD(avoir.total_ttc)} MAD) ?\nUne écriture inverse de la facture d'origine sera générée dans le journal AV.`)) return
    setBusy(true); setMsg('')
    try {
      await apiFetch(`/api/avoirs/${avoir.id}/comptabiliser`, { method: 'POST' })
      setMsg(`✓ Avoir ${avoir.numero} comptabilisé`)
      charger()
      // L'écriture est créée côté backend en dehors du contexte Écritures global
      // (utilisé par la page Journal) : on force son rechargement pour qu'elle
      // apparaisse immédiatement sans nécessiter un F5.
      if (rechargerEcritures) rechargerEcritures()
    } catch (e) {
      setMsg(`✗ ${e.message}`)
    } finally {
      setBusy(false)
      setTimeout(() => setMsg(''), 4000)
    }
  }

  async function annuler(avoir) {
    if (!confirm(`Annuler l'avoir ${avoir.numero} ?\nUne écriture inverse sera générée si nécessaire et tout retour stock sera compensé. Les quantités redeviendront disponibles sur la facture d'origine.`)) return
    setBusy(true); setMsg('')
    try {
      await apiFetch(`/api/avoirs/${avoir.id}/annuler`, { method: 'POST' })
      setMsg(`✓ Avoir ${avoir.numero} annulé`)
      charger()
    } catch (e) {
      setMsg(`✗ ${e.message}`)
    } finally {
      setBusy(false)
      setTimeout(() => setMsg(''), 4000)
    }
  }


  async function annulerUtilisation(avoir, utilisation) {
    if (!confirm(`Annuler cette ${utilisation.type_utilisation === 'imputation' ? 'imputation' : 'opération de remboursement'} de ${formatMAD(utilisation.montant)} MAD ?`)) return
    setBusy(true); setMsg('')
    try {
      await apiFetch(`/api/avoirs/${avoir.id}/utilisations/${utilisation.id}/annuler`, { method: 'POST' })
      setMsg('✓ Utilisation du crédit annulée et contrepassée si nécessaire')
      charger(); if (rechargerEcritures) rechargerEcritures()
    } catch (e) { setMsg(`✗ ${e.message}`) }
    finally { setBusy(false); setTimeout(() => setMsg(''), 4000) }
  }



  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Avoirs</h1>
          <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Notes de crédit émises sur factures de vente et d'achat
          </p>
        </div>
      </div>

      <div className={styles.content}>

        {/* Stats */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
              {stats.total} avoir(s)
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: stats.nonComptabilises > 0 ? '#FAEEDA' : '#EAF3DE', color: stats.nonComptabilises > 0 ? '#854F0B' : '#3B6D11' }}>
              {stats.nonComptabilises} non comptabilisé(s)
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#E6F1FB', color: '#185FA5' }}>
              Crédit libre : <strong>{formatMAD(stats.creditDisponible)} MAD</strong>
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: 'var(--bg-secondary)', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
              Total avoirs (actifs) : <strong>{formatMAD(stats.totalTTC)} MAD</strong>
            </span>
          </div>
        </div>

        {/* Filtres */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Type</label>
              <select value={filtreType} onChange={e => setFiltreType(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13, background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
                <option value="tous">Tous les types</option>
                <option value="vente">Vente</option>
                <option value="achat">Achat</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Statut</label>
              <select value={filtreStatut} onChange={e => setFiltreStatut(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13, background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
                <option value="tous">Tous les statuts</option>
                <option value="emis">Émis</option>
                <option value="utilise">Utilisé</option>
                <option value="rembourse">Remboursé</option>
                <option value="annule">Annulé</option>
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Recherche</label>
              <input value={recherche} onChange={e => setRecherche(e.target.value)}
                placeholder="N° avoir, tiers, facture, motif..."
                style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13, background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
            </div>
          </div>
        </div>

        {msg && (
          <div style={{ fontSize: 12, padding: '8px 14px', borderRadius: 6,
            background: msg.startsWith('✓') ? '#EAF3DE' : '#FCEBEB',
            color: msg.startsWith('✓') ? '#3B6D11' : '#A32D2D' }}>
            {msg}
          </div>
        )}

        <div className={styles.listeZone}>
          {/* Tableau */}
          <div className={`${styles.card} ${styles.cardMain}`}>
            {loading ? (
              <div className={styles.vide}><i className="ti ti-loader-2" /><span>Chargement...</span></div>
            ) : erreur ? (
              <div className={styles.vide}><i className="ti ti-alert-circle" /><span>{erreur}</span></div>
            ) : avoirsFiltres.length === 0 ? (
              <div className={styles.vide}>
                <i className="ti ti-receipt-refund" />
                <span>Aucun avoir {filtreType !== 'tous' || filtreStatut !== 'tous' || recherche ? 'ne correspond aux filtres' : 'pour cet exercice'}</span>
                {!recherche && filtreType === 'tous' && filtreStatut === 'tous' && (
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    Un avoir se crée depuis le détail d'une facture, via le bouton « Créer un avoir »
                  </span>
                )}
              </div>
            ) : (
              <div className={styles.tableWrapper}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)', borderBottom: '0.5px solid var(--border-medium)' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>N° Avoir</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Date</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Type</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Nature</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Tiers</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Facture d'origine</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500 }}>Total TTC</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Statut</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Compta</th>
                    <th style={{ width: 90 }} />
                  </tr>
                </thead>
                <tbody>
                  {avoirsFiltres.map((a, i) => (
                    <tr key={a.id}
                      onClick={() => setSelectionne(a)}
                      style={{
                        borderBottom: '0.5px solid var(--border-light)',
                        background: selectionne?.id === a.id ? '#EFF6FF' : i % 2 === 0 ? '' : 'var(--bg-secondary)',
                        cursor: 'pointer',
                        opacity: a.statut === 'annule' ? 0.55 : 1,
                      }}>
                      <td data-label="N° Avoir" style={{ padding: '8px 12px', fontWeight: 600 }}>{a.numero}</td>
                      <td data-label="Date" style={{ padding: '8px 12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{formatDate(a.date)}</td>
                      <td data-label="Type" style={{ padding: '8px 12px', textAlign: 'center' }}><BadgeType type={a.type} /></td>
                      <td data-label="Nature" style={{ padding: '8px 12px', fontSize: 10.5, color: 'var(--text-secondary)' }}>{NATURE_LABEL[a.nature_avoir] || a.nature_avoir || '—'}</td>
                      <td data-label="Tiers" style={{ padding: '8px 12px' }}>{a.tiers}</td>
                      <td data-label="Facture d’origine" style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>{a.facture_numero || '—'}</td>
                      <td data-label="Total TTC" style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600 }}>{formatMAD(a.total_ttc)} MAD</td>
                      <td data-label="Statut" style={{ padding: '8px 12px', textAlign: 'center' }}><BadgeStatut statut={a.statut} /></td>
                      <td data-label="Comptabilité" style={{ padding: '8px 12px', textAlign: 'center' }}>
                        {a.est_comptabilisee
                          ? <i className="ti ti-circle-check" style={{ color: '#3B6D11', fontSize: 14 }} title="Comptabilisé" />
                          : <i className="ti ti-circle-dashed" style={{ color: 'var(--text-tertiary)', fontSize: 14 }} title="Non comptabilisé" />}
                      </td>
                      <td data-label="Actions" style={{ padding: '8px 6px', textAlign: 'center' }}>
                        <button
                          onClick={e => { e.stopPropagation(); telechargerDocumentPDF(`/api/avoirs/${a.id}/pdf`, `avoir_${a.numero}.pdf`).catch(err => notifier.erreur(err.message)) }}
                          title="Télécharger PDF"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#DC2626', fontSize: 14 }}><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                        {peutModifier && !a.est_comptabilisee && a.statut !== 'annule' && (
                          <button
                            onClick={e => { e.stopPropagation(); comptabiliser(a) }}
                            disabled={busy}
                            title="Comptabiliser"
                            style={{ background: 'none', border: 'none', cursor: busy ? 'default' : 'pointer', color: 'var(--blue)', fontSize: 14 }}><i className="ti ti-calculator" /><span className="libelle-action" aria-hidden="true">Comptabiliser</span></button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
          </div>

          {/* Fiche en fenêtre : la liste conserve toujours toute sa largeur. */}
          {selectionne && (
            <Modal titre={`Avoir ${selectionne.numero}`} icone="ti-receipt-refund" onFermer={() => setSelectionne(null)} largeur="lg">
              <div className={styles.detailModal}>
                <div className={styles.detailOrigine}>Sur facture {selectionne.facture_numero || '—'}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <BadgeType type={selectionne.type} />
                  <BadgeStatut statut={selectionne.statut} />
                  <span style={{
                    fontSize: 10, padding: '2px 8px', borderRadius: 4,
                    background: selectionne.est_comptabilisee ? '#EAF3DE' : '#F3F4F6',
                    color: selectionne.est_comptabilisee ? '#3B6D11' : '#6B7280',
                  }}>
                    {selectionne.est_comptabilisee ? 'Comptabilisé' : 'Non comptabilisé'}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 12 }}>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>Tiers</span><div style={{ fontWeight: 500 }}>{selectionne.tiers}</div></div>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>Date</span><div style={{ fontWeight: 500 }}>{formatDate(selectionne.date)}</div></div>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>Nature</span><div style={{ fontWeight: 500 }}>{NATURE_LABEL[selectionne.nature_avoir] || selectionne.nature_avoir}</div></div>
                  <div><span style={{ color: 'var(--text-tertiary)' }}>Stock</span><div style={{ fontWeight: 500 }}>{selectionne.retour_stock ? 'Retour physique prévu' : 'Aucun mouvement'}</div></div>
                  {selectionne.motif && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <span style={{ color: 'var(--text-tertiary)' }}>Motif</span>
                      <div style={{ fontWeight: 500 }}>{selectionne.motif}</div>
                    </div>
                  )}
                </div>

                <div className={styles.detailLignesAvoir} role="list" aria-label="Lignes de l'avoir">
                  {(selectionne.lignes || []).map((l, idx) => (
                    <div className={styles.detailLigneAvoir} role="listitem" key={l.id ?? idx}>
                      <div className={styles.detailDescriptionAvoir}>
                        <span className={styles.detailLabelAvoir}>Article</span>
                        <strong>{l.description}</strong>
                        <small>{l.mode_calcul === 'rrr_pourcentage' ? `RRR ${l.taux_rrr}%` : l.mode_calcul === 'rrr_montant' ? 'RRR montant fixe' : l.mode_calcul === 'correction_prix' ? `Nouveau PU ${formatMAD(l.nouveau_prix_unitaire)} MAD` : l.mode_calcul === 'autre_montant' ? 'Montant financier' : 'Quantité / retour'}</small>
                      </div>
                      <div className={styles.detailValeurAvoir}><span className={styles.detailLabelAvoir}>Quantité</span>{l.quantite}</div>
                      <div className={styles.detailValeurAvoir}><span className={styles.detailLabelAvoir}>Montant TTC</span>{formatMAD(l.montant_ttc)} MAD</div>
                    </div>
                  ))}
                </div>

                <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}><span>Total HT</span><span>{formatMAD(selectionne.total_ht)} MAD</span></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}><span>Total TVA</span><span>{formatMAD(selectionne.total_tva)} MAD</span></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}><span>Total TTC</span><span>{formatMAD(selectionne.total_ttc)} MAD</span></div>
                </div>

                {selectionne.est_comptabilisee && selectionne.statut !== 'annule' && (
                  <div style={{ background: '#F7FAFC', border: '0.5px solid var(--border-light)', borderRadius: 8, padding: '10px 12px', fontSize: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}><span>Crédit excédentaire</span><span>{formatMAD(selectionne.credit_excedentaire || 0)} MAD</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 3 }}><span>Déjà utilisé/remboursé</span><span>{formatMAD(selectionne.montant_utilise || 0)} MAD</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 5, paddingTop: 5, borderTop: '0.5px solid var(--border-light)', fontWeight: 700 }}><span>Crédit libre</span><span>{formatMAD(selectionne.montant_disponible || 0)} MAD</span></div>
                    {peutModifier && Number(selectionne.montant_disponible || 0) > 0.01 && <div style={{ display: 'flex', gap: 6, marginTop: 9, flexWrap: 'wrap' }}>
                      <button className="hp-btn-primary" type="button" onClick={() => setUtiliserCredit({ avoir: selectionne, type: 'imputation' })}><i className="ti ti-arrow-merge" /> Imputer sur une facture</button>
                      <button className="hp-btn-secondary" type="button" onClick={() => setUtiliserCredit({ avoir: selectionne, type: 'remboursement' })}><i className="ti ti-cash-banknote" /> Rembourser</button>
                    </div>}
                  </div>
                )}

                {(selectionne.utilisations || []).length > 0 && <div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 5 }}>Historique du crédit</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>{selectionne.utilisations.map(u => <div key={u.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 8, alignItems: 'center', padding: '7px 9px', borderRadius: 6, background: 'var(--bg-secondary)', opacity: u.statut === 'annulee' ? 0.55 : 1 }}>
                    <div><strong>{u.type_utilisation === 'imputation' ? `Imputation ${u.facture_numero || ''}` : 'Remboursement'}</strong><div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{formatDate(u.date_utilisation)}{u.reference ? ` · ${u.reference}` : ''}{u.type_utilisation === 'imputation' && (u.date_acceptation_compensation ? ` · Accord signé le ${formatDate(u.date_acceptation_compensation)}` : ' · Accord à qualifier pour la TVA')}</div></div>
                    <span>{formatMAD(u.montant)} MAD</span>
                    {u.statut !== 'annulee' ? (peutModifier && <button type="button" title="Annuler cette utilisation" disabled={busy} onClick={() => annulerUtilisation(selectionne, u)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#A32D2D' }}><i className="ti ti-arrow-back-up" /><span className="libelle-action" aria-hidden="true">Annuler cette utilisation</span></button>) : <span style={{ fontSize: 9.5 }}>Annulée</span>}
                  </div>)}</div>
                </div>}

                {selectionne.notes && (
                  <div style={{ fontSize: 12 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>Notes</span>
                    <div>{selectionne.notes}</div>
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', paddingTop: 10, borderTop: '0.5px solid var(--border-light)' }}>
                  <button onClick={() => telechargerDocumentPDF(`/api/avoirs/${selectionne.id}/pdf`, `avoir_${selectionne.numero}.pdf`).catch(err => notifier.erreur(err.message))}
                    style={{ padding: '7px 14px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <i className="ti ti-file-type-pdf" style={{ color: '#DC2626' }} /> PDF
                  </button>
                  <button onClick={() => preparerEmailDocument({ endpoint: `/api/avoirs/${selectionne.id}/pdf`, nomFichier: `avoir_${selectionne.numero}.pdf`, typeDocument: 'Avoir', numero: selectionne.numero, tiers: selectionne.tiers, tiersId: selectionne.tiers_id }).catch(err => notifier.erreur(err.message))}
                    style={{ padding: '7px 14px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <i className="ti ti-mail-forward" /> Préparer e-mail
                  </button>
                  {peutModifier && !selectionne.est_comptabilisee && selectionne.statut !== 'annule' && (
                    <button onClick={() => comptabiliser(selectionne)} disabled={busy}
                      style={{
                        padding: '7px 14px', borderRadius: 6, border: 'none',
                        background: 'var(--blue)', color: '#fff', cursor: busy ? 'default' : 'pointer',
                        fontSize: 12, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5,
                      }}>
                      <i className="ti ti-calculator" /> Comptabiliser
                    </button>
                  )}
                  {peutModifier && selectionne.statut !== 'annule' && !(selectionne.utilisations || []).some(u => u.statut !== 'annulee') && (
                    <button onClick={() => annuler(selectionne)} disabled={busy}
                      style={{
                        padding: '7px 14px', borderRadius: 6, border: '0.5px solid var(--border-medium)',
                        background: 'none', color: 'var(--text-secondary)', cursor: busy ? 'default' : 'pointer',
                        fontSize: 12, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5,
                      }}>
                      <i className="ti ti-ban" /> Annuler l'avoir
                    </button>
                  )}
                </div>
                {peutModifier && (selectionne.utilisations || []).some(u => u.statut !== 'annulee') && <div style={{ fontSize: 11, color: '#8A5A00' }}><i className="ti ti-info-circle" /> Annulez d’abord les imputations/remboursements actifs avant d’annuler cet avoir.</div>}
                {peutModifier && selectionne.est_comptabilisee && (
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 5 }}>
                    <i className="ti ti-info-circle" />
                    Un avoir comptabilisé ne peut plus être supprimé — utilisez « Annuler l'avoir » si besoin.
                  </div>
                )}
              </div>
            </Modal>
          )}
        </div>
      </div>
      {peutModifier && utiliserCredit && <ModalUtiliserCredit avoir={utiliserCredit.avoir} typeUtilisation={utiliserCredit.type} onFermer={() => setUtiliserCredit(null)} onSuccess={() => { charger(); if (rechargerEcritures) rechargerEcritures() }} />}
    </div>
  )
}
