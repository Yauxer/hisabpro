import React, { useState, useEffect, useMemo } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { useFactures } from '../data/FacturesContext.jsx'
import { formatMAD as formatMADConnu, formatDate } from '../data/donnees.js'
import Modal from '../components/Modal.jsx'
import styles from './Effets.module.css'
import { API_BASE, formatErreurAPI } from '../services/api.js'
import { dateLocaleISO } from '../utils/formUtils.js'

const formatMAD = n => n == null || !Number.isFinite(Number(n)) ? 'À vérifier' : formatMADConnu(n)
const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Erreur' })); throw new Error(formatErreurAPI(e.detail)) }
  if (res.status === 204) return null
  return res.json()
}

const STATUT_BADGE = {
  portefeuille: { bg: '#FAEEDA', color: '#854F0B', label: 'En portefeuille' },
  encaissement: { bg: '#E6F1FB', color: '#185FA5', label: "À l'encaissement" },
  encaisse:     { bg: '#EAF3DE', color: '#3B6D11', label: 'Encaissé' },
  rejete:       { bg: '#FCEBEB', color: '#A32D2D', label: 'Rejeté / Impayé' },
  a_payer:      { bg: '#FAEEDA', color: '#854F0B', label: 'À payer' },
  paye:         { bg: '#EAF3DE', color: '#3B6D11', label: 'Payé' },
  complet:      { bg: '#EAF3DE', color: '#3B6D11', label: 'Réglé' },
}

function BadgeStatut({ statut }) {
  const b = STATUT_BADGE[statut] || STATUT_BADGE.complet
  return <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: b.bg, color: b.color, fontWeight: 500, whiteSpace: 'nowrap' }}>{b.label}</span>
}

// ── Modale de transition avec frais optionnels ────────────────────────────────
function ModalTransition({ reglement, action, onFermer, onSuccess }) {
  const [frais, setFrais] = useState('')
  const [dateEffective, setDateEffective] = useState(() => dateLocaleISO())
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  const CONF = {
    remettre: {
      titre: "Remettre à l'encaissement", icone: 'ti-building-bank', couleur: 'var(--blue)',
      texte: `Le ${reglement.mode === 'cheque' ? 'chèque' : "l'effet"} de ${formatMAD(reglement.montant)} MAD est remis en banque. Saisissez la date réelle du bordereau de remise.`,
      labelFrais: null,
      noteFrais: null,
    },
    encaisser: {
      titre: 'Confirmer l\'encaissement', icone: 'ti-cash', couleur: 'var(--green)',
      texte: `L'avis de crédit est reçu pour un montant brut de ${formatMAD(reglement.montant)} MAD. Le montant crédité en banque correspond au brut moins les frais renseignés ci-dessous.`,
      labelFrais: 'Frais bancaires retenus (optionnel)',
      noteFrais: 'Si la banque a prélevé des frais/commissions, le net crédité sera Banque = montant − frais, et les frais passés en charge (61472). Les frais ne peuvent pas dépasser le montant du règlement.',
    },
    rejeter: {
      titre: 'Déclarer l\'impayé', icone: 'ti-alert-triangle', couleur: '#A32D2D',
      texte: reglement.statut === 'encaisse'
        ? `Le ${reglement.mode === 'cheque' ? 'chèque' : 'l\'effet'} de ${formatMAD(reglement.montant)} MAD déjà crédité revient impayé. La banque est débitée, la créance client est ré-ouverte et la TVA sur encaissements est régularisée à la date du rejet.`
        : `Le ${reglement.mode === 'cheque' ? 'chèque' : 'l\'effet'} de ${formatMAD(reglement.montant)} MAD est rejeté. La créance client sera ré-ouverte : la facture redevient due.`,
      labelFrais: 'Frais de rejet refacturés au client (optionnel)',
      noteFrais: reglement.statut === 'encaisse'
        ? 'Frais débités par la banque : charge 6147, refacturés au client (3421) en produits accessoires (7127).'
        : 'Ces frais seront ajoutés à la créance ré-ouverte du client (3421) et constatés en produits accessoires (7127).',
    },
    payer: {
      titre: 'Confirmer le paiement', icone: 'ti-cash', couleur: 'var(--green)',
      texte: `L'effet fournisseur de ${formatMAD(reglement.montant)} MAD a été effectivement payé.`,
      labelFrais: null,
      noteFrais: null,
    },
  }[action]

  async function confirmer() {
    if (['encaisser', 'payer'].includes(action) && !dateEffective) {
      setErreur('La date effective est obligatoire.')
      return
    }
    const fraisNum = Number(frais || 0)
    if (!Number.isFinite(fraisNum) || fraisNum < 0) {
      setErreur('Les frais doivent être un montant positif ou nul.')
      return
    }
    if (fraisNum > Number(reglement.montant || 0)) {
      setErreur('Les frais ne peuvent pas dépasser le montant du règlement.')
      return
    }
    setLoading(true); setErreur('')
    try {
      await apiFetch(`/api/reglements/${reglement.id}/transition`, {
        method: 'POST',
        body: JSON.stringify({
          action,
          frais: fraisNum,
          ...(dateEffective ? { date_effective: dateEffective } : {}),
        }),
      })
      onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={CONF.titre} icone={CONF.icone} onFermer={onFermer} largeur="sm">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {erreur && <div role="alert" style={{ fontSize: 12, padding: '8px 14px', borderRadius: 6, background: '#FCEBEB', color: '#A32D2D' }}>{erreur}</div>}
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>{CONF.texte}</p>
        {['remettre', 'rejeter', 'encaisser', 'payer'].includes(action) && (
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Date réelle de l'opération</label>
            <input type="date" value={dateEffective} min={reglement.date || undefined} max={dateLocaleISO()}
              onChange={e => setDateEffective(e.target.value)}
              style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }} />
            <p style={{ fontSize: 10, color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>
              Date figurant sur le bordereau de remise, l'avis bancaire ou le paiement. À défaut, la date du jour est utilisée.
            </p>
          </div>
        )}
        {CONF.labelFrais && (
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>{CONF.labelFrais}</label>
            <input type="number" min="0" max={reglement.montant || undefined} step="0.01" value={frais} placeholder="0.00"
              onChange={e => setFrais(e.target.value)}
              style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13, textAlign: 'right' }} />
            <p style={{ fontSize: 10, color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>{CONF.noteFrais}</p>
          </div>
        )}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={onFermer}
            style={{ padding: '7px 14px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12 }}>
            Annuler
          </button>
          <button onClick={confirmer} disabled={loading}
            style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: CONF.couleur, color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 500 }}>
            {loading ? '...' : CONF.titre}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ── Page principale ───────────────────────────────────────────────────────────
export default function Effets() {
  const { annee } = useExercice()
  const { recharger: rechargerEcritures } = useEcritures() || {}
  const { recharger: rechargerFactures } = useFactures() || {}

  function rafraichirTout() {
    charger()
    if (rechargerEcritures) rechargerEcritures()
    if (rechargerFactures) rechargerFactures()
  }

  const [reglements, setReglements] = useState([])
  const [facturesMap, setFacturesMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const [filtreMode, setFiltreMode] = useState('tous')
  const [filtreStatut, setFiltreStatut] = useState('actifs')
  const [recherche, setRecherche] = useState('')
  const [transition, setTransition] = useState(null) // { reglement, action }
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  function charger() {
    setLoading(true); setErreur('')
    Promise.all([
      apiFetch(`/api/reglements?exercice=${annee}`),
      apiFetch(`/api/factures?exercice=${annee}`).catch(() => []),
    ])
      .then(([regls, factures]) => {
        // Seuls les chèques et effets ont un cycle de vie à suivre ici
        setReglements(regls.filter(r => r.mode === 'cheque' || r.mode === 'effet'))
        const map = {}
        factures.forEach(f => { map[f.id] = f })
        setFacturesMap(map)
      })
      .catch(e => setErreur(e.message))
      .finally(() => setLoading(false))
  }
  useEffect(() => { charger() }, [annee])

  const filtres = useMemo(() => reglements.filter(r => {
    if (filtreMode !== 'tous' && r.mode !== filtreMode) return false
    if (filtreStatut === 'actifs' && !['portefeuille', 'encaissement', 'a_payer'].includes(r.statut)) return false
    if (filtreStatut !== 'tous' && filtreStatut !== 'actifs' && r.statut !== filtreStatut) return false
    if (recherche) {
      const q = recherche.toLowerCase()
      const fact = facturesMap[r.facture_id]
      if (!r.tiers?.toLowerCase().includes(q) && !r.reference?.toLowerCase().includes(q) &&
          !fact?.numero?.toLowerCase().includes(q)) return false
    }
    return true
  }), [reglements, filtreMode, filtreStatut, recherche, facturesMap])

  const stats = useMemo(() => {
    const portefeuille = reglements.filter(r => r.statut === 'portefeuille')
    const encaissement = reglements.filter(r => r.statut === 'encaissement')
    const rejetes      = reglements.filter(r => r.statut === 'rejete')
    const echus = reglements.filter(r =>
      ['portefeuille', 'encaissement', 'a_payer'].includes(r.statut) &&
      r.date_echeance && new Date(r.date_echeance) <= new Date())
    const totalQualifie = lignes => {
      if (lignes.some(r => r.montant_valide === false || r.montant == null || !Number.isFinite(r.montant))) return null
      const total = lignes.reduce((s, r) => s + r.montant, 0)
      return Number.isFinite(total) ? total : null
    }
    return {
      portefeuille: totalQualifie(portefeuille),
      nbPortefeuille: portefeuille.length,
      encaissement: totalQualifie(encaissement),
      nbEncaissement: encaissement.length,
      nbRejetes: rejetes.length,
      nbEchus: echus.length,
    }
  }, [reglements])

  function estEchu(r) {
    return ['portefeuille', 'encaissement', 'a_payer'].includes(r.statut) &&
      r.date_echeance && new Date(r.date_echeance) <= new Date()
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Effets &amp; Chèques</h1>
          <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Portefeuille de valeurs : remise en banque, encaissement, impayés
          </p>
        </div>
      </div>

      <div className={styles.content}>
        {reglements.some(r => r.montant_valide === false) && <div role="alert" style={{ color: 'var(--red)' }}>
          Montants historiques à vérifier : les opérations des pièces concernées sont indisponibles.
        </div>}
        {/* Stats */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#FAEEDA', color: '#854F0B' }}>
              Portefeuille : <strong>{stats.nbPortefeuille}</strong> — {formatMAD(stats.portefeuille)} MAD
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#E6F1FB', color: '#185FA5' }}>
              À l'encaissement : <strong>{stats.nbEncaissement}</strong> — {formatMAD(stats.encaissement)} MAD
            </span>
            {stats.nbEchus > 0 && (
              <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#FFFBEB', color: '#854F0B' }}>
                <i className="ti ti-clock-exclamation" style={{ marginRight: 3 }} />{stats.nbEchus} échu(s)
              </span>
            )}
            {stats.nbRejetes > 0 && (
              <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#FCEBEB', color: '#A32D2D' }}>
                {stats.nbRejetes} impayé(s)
              </span>
            )}
          </div>
        </div>

        {/* Filtres */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Mode</label>
              <select value={filtreMode} onChange={e => setFiltreMode(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }}>
                <option value="tous">Tous</option>
                <option value="cheque">Chèques</option>
                <option value="effet">Effets</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Statut</label>
              <select value={filtreStatut} onChange={e => setFiltreStatut(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }}>
                <option value="actifs">En cours (portefeuille, encaissement, à payer)</option>
                <option value="tous">Tous</option>
                <option value="portefeuille">En portefeuille</option>
                <option value="encaissement">À l'encaissement</option>
                <option value="encaisse">Encaissés</option>
                <option value="rejete">Rejetés / impayés</option>
                <option value="a_payer">Effets à payer (fournisseurs)</option>
                <option value="paye">Payés</option>
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Recherche</label>
              <input value={recherche} onChange={e => setRecherche(e.target.value)}
                placeholder="Tiers, référence, facture..."
                style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }} />
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

        {/* Tableau */}
        <div className={`${styles.card} ${styles.cardMain}`}>
          {loading ? (
            <div className={styles.vide}><i className="ti ti-loader-2" /><span>Chargement...</span></div>
          ) : erreur ? (
            <div className={styles.vide}><i className="ti ti-alert-circle" /><span>{erreur}</span></div>
          ) : filtres.length === 0 ? (
            <div className={styles.vide}>
              <i className="ti ti-wallet" />
              <span>Aucun chèque ou effet {filtreStatut === 'actifs' ? 'en cours' : 'ne correspond aux filtres'}</span>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                Les chèques et effets sont créés depuis l'encaissement d'une facture (mode Chèque ou Effet)
              </span>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '0.5px solid var(--border-medium)' }}>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Date</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Mode</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Tiers</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Référence</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Facture</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500 }}>Montant</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Échéance</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Statut</th>
                  <th style={{ width: 140 }} />
                </tr>
              </thead>
              <tbody>
                {filtres.map((r, i) => {
                  const fact = facturesMap[r.facture_id]
                  const echu = estEchu(r)
                  return (
                    <tr key={r.id} style={{
                      borderBottom: '0.5px solid var(--border-light)',
                      background: i % 2 === 0 ? '' : 'var(--bg-secondary)',
                    }}>
                      <td style={{ padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>{formatDate(r.date)}</td>
                      <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                        <i className={`ti ${r.mode === 'cheque' ? 'ti-file-check' : 'ti-file-certificate'}`}
                          style={{ marginRight: 4, color: 'var(--text-tertiary)' }} />
                        {r.mode === 'cheque' ? 'Chèque' : 'Effet'}
                      </td>
                      <td style={{ padding: '8px 12px', fontWeight: 500 }}>{r.tiers}</td>
                      <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>{r.reference || '—'}</td>
                      <td style={{ padding: '8px 12px' }}>
                        {fact
                          ? <span style={{ fontSize: 10, fontFamily: 'monospace', background: '#E6F1FB', color: 'var(--blue)', padding: '2px 6px', borderRadius: 3 }}>{fact.numero}</span>
                          : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600 }}>{formatMAD(r.montant)} MAD
                        {r.montant_valide === false && <div style={{ color: 'var(--red)', fontSize: 11, fontWeight: 400, maxWidth: 220 }}>{r.montant_anomalie}</div>}
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'center', whiteSpace: 'nowrap' }}>
                        {r.date_echeance ? (
                          <span style={{ color: echu ? '#A32D2D' : 'var(--text-secondary)', fontWeight: echu ? 600 : 400 }}>
                            {echu && <i className="ti ti-clock-exclamation" style={{ marginRight: 3 }} />}
                            {formatDate(r.date_echeance)}
                          </span>
                        ) : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'center' }}><BadgeStatut statut={r.statut} /></td>
                      <td style={{ padding: '8px 6px' }}>
                        <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                          {r.statut === 'portefeuille' && (
                            <button onClick={() => setTransition({ reglement: r, action: 'remettre' })} disabled={busy || r.montant_valide === false} title="Remettre à l'encaissement"
                              style={{ background: 'none', border: '0.5px solid var(--border-medium)', borderRadius: 4, padding: '3px 8px', cursor: 'pointer', color: 'var(--blue)', fontSize: 11 }}>
                              <i className="ti ti-building-bank" style={{ marginRight: 3 }} />Remettre
                            </button>
                          )}
                          {['portefeuille', 'encaissement'].includes(r.statut) && (() => {
                            // Un effet n'est encaissable qu'à partir de sa date d'échéance
                            const bloqueAvantEcheance = r.mode === 'effet' && r.date_echeance &&
                              r.date_echeance > dateLocaleISO()
                            return (
                            <>
                              <button
                                onClick={() => setTransition({ reglement: r, action: 'encaisser' })}
                                disabled={busy || r.montant_valide === false || bloqueAvantEcheance}
                                title={bloqueAvantEcheance
                                  ? `Encaissable à partir du ${r.date_echeance.split('-').reverse().join('/')}`
                                  : "Confirmer l'encaissement"}
                                style={{ background: 'none', border: '0.5px solid var(--border-medium)', borderRadius: 4, padding: '3px 8px',
                                  cursor: bloqueAvantEcheance ? 'not-allowed' : 'pointer',
                                  color: bloqueAvantEcheance ? 'var(--text-tertiary)' : 'var(--green)',
                                  opacity: bloqueAvantEcheance ? 0.5 : 1, fontSize: 11 }}><i className="ti ti-check" /><span className="libelle-action" aria-hidden="true">Encaisser</span></button>
                              <button onClick={() => setTransition({ reglement: r, action: 'rejeter' })} disabled={busy || r.montant_valide === false} title="Déclarer impayé"
                                style={{ background: 'none', border: '0.5px solid var(--border-medium)', borderRadius: 4, padding: '3px 8px', cursor: 'pointer', color: '#A32D2D', fontSize: 11 }}><i className="ti ti-x" /><span className="libelle-action" aria-hidden="true">Déclarer impayé</span></button>
                            </>
                            )
                          })()}
                          {r.statut === 'encaisse' && ['cheque', 'effet'].includes(r.mode) && (
                            <button onClick={() => setTransition({ reglement: r, action: 'rejeter' })} disabled={busy || r.montant_valide === false} title="Déclarer impayé après encaissement"
                              style={{ background: 'none', border: '0.5px solid var(--border-medium)', borderRadius: 4, padding: '3px 8px', cursor: 'pointer', color: '#A32D2D', fontSize: 11 }}><i className="ti ti-x" /><span className="libelle-action" aria-hidden="true">Déclarer impayé après encaissement</span></button>
                          )}
                          {r.statut === 'a_payer' && (() => {
                            const bloqueAvantEcheance = r.mode === 'effet' && r.date_echeance &&
                              new Date(r.date_echeance) > new Date()
                            return (
                            <button onClick={() => setTransition({ reglement: r, action: 'payer' })} disabled={busy || r.montant_valide === false || bloqueAvantEcheance}
                              title={bloqueAvantEcheance
                                ? `Payable à partir du ${new Date(r.date_echeance).toLocaleDateString('fr-MA')}`
                                : "Payer l'effet"}
                              style={{ background: 'none', border: '0.5px solid var(--border-medium)', borderRadius: 4, padding: '3px 8px',
                                cursor: bloqueAvantEcheance ? 'not-allowed' : 'pointer',
                                color: bloqueAvantEcheance ? 'var(--text-tertiary)' : 'var(--green)',
                                opacity: bloqueAvantEcheance ? 0.5 : 1, fontSize: 11 }}>
                              <i className="ti ti-cash" style={{ marginRight: 3 }} />Payer
                            </button>
                            )
                          })()}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </div>

      {transition && (
        <ModalTransition
          reglement={transition.reglement}
          action={transition.action}
          onFermer={() => setTransition(null)}
          onSuccess={() => { rafraichirTout() }}
        />
      )}
    </div>
  )
}
