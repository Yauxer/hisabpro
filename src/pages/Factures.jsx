import { statutPaiementAffiche } from '../utils/statutPaiement.js'
import React, { useState, useMemo, useRef, useEffect } from 'react'
import PiecesJointes from '../components/PiecesJointes.jsx'
import FactureConservation from '../components/FactureConservation.jsx'
import FactureLiee from '../components/FactureLiee.jsx'
import { useFactures } from '../data/FacturesContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { API_BASE, tiersAPI, formatErreurAPI, peutEcrire } from '../services/api.js'
import { dansPeriode, periodeInversee, facturePubliee, avoirPublie, totauxFacturation, ventilationCA } from '../utils/facturesPeriod.js'
import { exporterCSV } from '../services/exportCSV.js'
import { preparerEmailDocument } from '../services/documentsCommerciaux.js'
import { formatMAD as formatMADBase, formatDate } from '../data/donnees.js'
import Modal from '../components/Modal.jsx'
import TiersPicker from '../components/TiersPicker.jsx'
import { FormSection, AdvancedSection, InlineNotice, ActionBar } from '../components/FormUX.jsx'
import { useLocation } from 'react-router-dom'
import styles from './Factures.module.css'
import { dateLocaleISO, entierOuDefaut, nombreOuDefaut } from '../utils/formUtils.js'
import { factureEnRetard, dateEcheanceAffichee, joursCalendairesAvant } from '../utils/echeancesFactures.js'
import { QUALIFICATIONS_TVA, tauxTVAPourDate, tauxTVAAvecHistorique, tvaEffective, qualificationParDefautPourTaux } from '../utils/tvaUtils.js'
import { nombreArticleSaisie, nombreSaisieConnu, qualificationArticle, montantLignesSaisies } from '../utils/articlesNombres.js'
import { notifier } from '../services/notifications.js'

const MODES_REGLEMENT_PREVUS = [
  ['','— Non précisé —'], ['virement','Virement'], ['cheque','Chèque'], ['especes','Espèces'],
  ['effet','Effet de commerce'], ['carte','Carte'], ['prelevement','Prélèvement'], ['autre','Autre'],
]

const formatMAD = valeur => typeof valeur === 'number' && Number.isFinite(valeur) ? formatMADBase(valeur) : 'À vérifier'

function DetailFactureHistorique({ facture, onFermer }) {
  return <Modal titre={facture.numero ? `Facture ${facture.numero}` : `Brouillon #${facture.id}`} icone="ti-file-text" onFermer={onFermer} largeur="md">
    <div style={{ display: 'grid', gap: 12, minWidth: 0, overflowWrap: 'anywhere' }}>
      <p><strong>{facture.tiers}</strong> · {formatDate(facture.date)}</p>
      <div role="alert"><strong>Montants à vérifier.</strong> Les données sources sont conservées. Les opérations financières et le PDF sont indisponibles pour cette facture.</div>
      <ul>{(facture.anomalies_montants || []).map((message, i) => <li key={i}>{message}</li>)}</ul>
      {(facture.lignes || []).map(l => <div key={l.id} className={styles.detailLigne} style={{ display: 'block', overflowWrap: 'anywhere' }}>
        <strong>{l.description}</strong>
        <p>Quantité : {l.quantite ?? 'À vérifier'} · Prix unitaire : {formatMAD(l.prix_unitaire)} MAD</p>
        <p>HT : {formatMAD(l.montant_ht)} MAD · TVA : {formatMAD(l.montant_tva)} MAD · TTC : {formatMAD(l.montant_ttc)} MAD</p>
      </div>)}
      <p>Total HT : {formatMAD(facture.total_ht)} MAD · Total TTC : {formatMAD(facture.total_ttc)} MAD</p>
      {(facture.echeances || []).map((e, i) => <p key={e.id ?? i}>Échéance {formatDate(e.date_echeance)} : {formatMAD(e.montant)} MAD</p>)}
    </div>
  </Modal>
}

async function lireSituationReglement(response) {
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Situation de paiement indisponible.')
  return data
}

export function ResumeRASSituation({ situation }) {
  if (!situation) return null
  const estime = situation.montant_ras_estime
  const impute = situation.montant_ras_impute
  const montant = valeur => typeof valeur === 'number' && Number.isFinite(valeur) ? `${formatMAD(valeur)} MAD` : 'À vérifier'
  return <div style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }}>
    {(estime == null || estime > 0) && <span>RAS estimée : {montant(estime)} · ne constitue pas un règlement.</span>}
    {impute > 0 && <span>{situation.ras_origine === 'capture_reglement' ? 'RAS déclarée sur règlement' : 'RAS historiquement comptabilisée'} : {montant(impute)} · ne constitue pas une attestation.</span>}
    {situation.ras_anomalie && <span role="alert" style={{ color: 'var(--red)' }}>{situation.ras_anomalie}</span>}
  </div>
}

// Calcule la date d'échéance
function dateEcheance(dateFacture, delaiJours = 60) {
  if (!dateFacture || delaiJours === null || delaiJours === undefined) return null
  const d = new Date(`${dateFacture}T12:00:00`)
  d.setDate(d.getDate() + Number(delaiJours || 0))
  return d
}

// Badge délai de paiement
function BadgeEcheance({ facture }) {
  if (facture.statut === 'payee' || facture.statut === 'annulee') return null
  const date = dateEcheanceAffichee(facture)
  const joursRestants = joursCalendairesAvant(date)
  if (joursRestants === null) return null
  const echeance = new Date(`${date}T12:00:00`)
  const dateStr = echeance.toLocaleDateString('fr-MA', { day: '2-digit', month: '2-digit', year: '2-digit' })

  if (joursRestants < 0) {
    return <span className={styles.badgeRetard}>
      <i className="ti ti-clock-exclamation" aria-hidden="true" /> {dateStr} ({Math.abs(joursRestants)}j retard)
    </span>
  }
  if (joursRestants <= 7) {
    return <span className={styles.badgeUrgent}>
      <i className="ti ti-clock" aria-hidden="true" /> {dateStr} ({joursRestants}j)
    </span>
  }
  return <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{dateStr}</span>
}


function BadgeStatut({ facture }) {
  const statut = statutPaiementAffiche(facture)
  const config = {
    reglement_en_cours: { label: 'Règlement en cours', bg: '#E6F1FB', color: '#185FA5' },
    payee:                { label: 'Payée',        bg: '#EAF3DE', color: '#3B6D11' },
    partiellement_payee:  { label: 'Part. payée',  bg: '#E6F1FB', color: '#185FA5' },
    en_attente:           { label: 'En attente',   bg: '#FAEEDA', color: '#854F0B' },
    retard:               { label: 'En retard',    bg: '#FCEBEB', color: '#A32D2D' },
    annulee:              { label: 'Annulée',      bg: '#F0EFED', color: '#5A5955' },
  }
  const c = config[statut] || config.en_attente
  return <span className={styles.badge} style={{ background: c.bg, color: c.color }}>{c.label}</span>
}

function BadgeCompta({ estComptabilisee }) {
  if (!estComptabilisee) return null
  return (
    <span className={styles.badgeCompta}>
      <i className="ti ti-check" aria-hidden="true" /> Compta
    </span>
  )
}

function BadgeType({ type }) {
  return (
    <span className={styles.badge} style={type === 'vente'
      ? { background: '#E6F1FB', color: '#185FA5' }
      : { background: '#EEEDFE', color: '#534AB7' }}>
      {type === 'vente' ? 'Vente' : 'Achat'}
    </span>
  )
}

function lignesActivesCompte(lignes, articles, type) {
  return lignes
    .filter(l => (l.description || '').trim())
    .map(l => articles.find(a => a.id === l.article_id))
    .filter(Boolean)
    .map(a => {
      if (type === 'vente') return a.compte_vente || a.famille?.compte_vente || '7111'
      return a.compte_achat || a.famille?.compte_achat || '6111'
    })
}

// ─── Autocomplete article avec famille + création rapide ──────────────────────
function ChampArticle({ value, articles, familles, onChange, onSelect, type, onFamilleCreee, filtreFamilleId, dateDoc }) {
  const [ouvert,        setOuvert]        = useState(false)
  const [showMiniForm,  setShowMiniForm]  = useState(false)
  const [familleId,     setFamilleId]     = useState('')
  const [nouvelleFam,   setNouvelleFam]   = useState(false)
  const [nomFamille,    setNomFamille]    = useState('')
  const [tvafamille,    setTvaFamille]    = useState(20)
  const [tvaArticleExplicite, setTvaArticleExplicite] = useState('')
  const [erreurCreation, setErreurCreation] = useState('')
  const [loading,       setLoading]       = useState(false)
  const ref = useRef(null)
  const familleChoisie = familles.find(f => f.id === parseInt(familleId))
  const familleTVAInconnue = !nouvelleFam && familleChoisie && !nombreSaisieConnu(familleChoisie.tva_defaut)

  const suggestions = useMemo(() => {
    const base = articles.filter(a => !filtreFamilleId || a.famille_id === parseInt(filtreFamilleId))
    // Champ vide : liste complète triée (vraie liste déroulante au clic)
    if (!value || !value.trim()) {
      return [...base].sort((a, b) => a.designation.localeCompare(b.designation, 'fr')).slice(0, 30)
    }
    const q = value.toLowerCase()
    return base.filter(a =>
      a.designation.toLowerCase().includes(q) || a.code.toLowerCase().includes(q)
    ).slice(0, 30)
  }, [value, articles, filtreFamilleId])

  // Article exact trouvé
  const articleExact = articles.find(a =>
    a.designation.toLowerCase() === value.toLowerCase()
  )

  const estNouveau = value.length > 2 && !articleExact && suggestions.length === 0

  useEffect(() => {
    function clickDehors(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOuvert(false)
        // Ne ferme pas showMiniForm car il est en position fixed hors du ref
      }
    }
    document.addEventListener('mousedown', clickDehors)
    return () => document.removeEventListener('mousedown', clickDehors)
  }, [])

  async function creerArticle() {
    if (!value.trim()) return
    setLoading(true)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

      let famId = familleId ? parseInt(familleId) : null
      let famille = familles.find(f => f.id === famId) || null
      if (!nouvelleFam && famille && !nombreSaisieConnu(famille.tva_defaut) && !nombreSaisieConnu(tvaArticleExplicite)) {
        setErreurCreation('La TVA de cette famille est inconnue : choisissez une valeur explicite pour cet article.'); return
      }

      // Crée la nouvelle famille si demandé
      if (nouvelleFam && nomFamille.trim()) {
        const resFam = await fetch(API_BASE + '/api/familles', {
          method: 'POST', headers,
          body: JSON.stringify({
            code:         nomFamille.toUpperCase().replace(/\s+/g, '_').substring(0, 20),
            libelle:      nomFamille,
            tva_defaut:   nombreOuDefaut(tvafamille, 20),
            compte_vente: '7111',
            compte_achat: '6111',
          }),
        })
        if (resFam.ok) {
          famille = await resFam.json()
          famId   = famille.id
          onFamilleCreee?.(famille) // notifie le parent pour mettre à jour la liste
        } else {
          const erreur = await resFam.json().catch(() => ({ detail: 'Création de la famille refusée.' }))
          throw new Error(formatErreurAPI(erreur.detail))
        }
      }

      const res = await fetch(API_BASE + '/api/articles', {
        method: 'POST', headers,
        body: JSON.stringify({
          code:          value.substring(0, 20).toUpperCase().replace(/\s+/g, '-'),
          designation:   value,
          famille_id:    famId,
          tva:           famille ? (nombreSaisieConnu(famille.tva_defaut) ? Number(famille.tva_defaut) : Number(tvaArticleExplicite)) : 20,
          prix_vente_ht: 0,
          prix_achat_ht: 0,
          unite:         'unité',
        }),
      })
      if (res.ok) {
        const nouvelArticle = await res.json()
        onSelect({ ...nouvelArticle, famille })
        setShowMiniForm(false)
        setOuvert(false)
        setNomFamille('')
        setNouvelleFam(false)
        setTvaArticleExplicite('')
        setErreurCreation('')
      } else {
        const erreur = await res.json().catch(() => ({ detail: "Création de l'article refusée." }))
        throw new Error(formatErreurAPI(erreur.detail))
      }
    } catch (erreur) { setErreurCreation(erreur.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ position: 'relative', flex: 1 }} ref={ref}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <input className={styles.inputSm} type="text"
          placeholder="Description ou article..."
          value={value}
          onChange={e => { onChange(e.target.value); setOuvert(true); setShowMiniForm(false) }}
          onFocus={() => setOuvert(true)}
          style={{ flex: 1 }} />
        {/* Badge famille si article connu */}
        {articleExact?.famille && (
          <span style={{
            fontSize: 10, whiteSpace: 'nowrap', padding: '2px 7px', borderRadius: 4,
            background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
          }}>
            {articleExact.famille.libelle}
          </span>
        )}
        {/* Bouton créer si nouvel article */}
        {estNouveau && !showMiniForm && (
          <button
            onClick={e => { e.stopPropagation(); setShowMiniForm(true); setOuvert(false); setTvaArticleExplicite(''); setErreurCreation('') }}
            style={{
              width: 24, height: 24, borderRadius: 4, background: 'var(--blue)',
              color: '#fff', border: 'none', cursor: 'pointer', fontSize: 14,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}
            title="Créer cet article"><i className="ti ti-plus" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Créer cet article</span></button>
        )}
      </div>

      {/* Dropdown suggestions */}
      {ouvert && suggestions.length > 0 && (
        <ul style={{
          position: 'absolute', top: 'calc(100% + 2px)', left: 0, minWidth: 300,
          background: 'var(--bg-primary)', border: '0.5px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)', zIndex: 300, listStyle: 'none',
          boxShadow: '0 6px 20px rgba(0,0,0,0.12)', maxHeight: 260, overflowY: 'auto',
        }}>
          {suggestions.map(a => (
            <li key={a.id}
              onMouseDown={() => { onSelect(a); setOuvert(false) }}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', cursor: 'pointer', fontSize: 12 }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-secondary)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}>
              <span style={{ fontFamily: 'monospace', fontSize: 10, color: 'var(--blue)', background: 'var(--blue-light)', padding: '1px 5px', borderRadius: 3, flexShrink: 0 }}>
                {a.code}
              </span>
              <span style={{ flex: 1 }}>{a.designation}</span>
              {a.famille && (
                <span style={{ fontSize: 10, background: 'var(--bg-secondary)', color: 'var(--text-tertiary)', padding: '1px 5px', borderRadius: 3, flexShrink: 0 }}>
                  {a.famille.libelle}
                </span>
              )}
              {/* TVA masquée — portée par l'article, pas affichée ici */}
              {a.stock_actuel !== undefined && a.stock_actuel !== null && (
                <span style={{
                  fontSize: 10, padding: '1px 5px', borderRadius: 3, flexShrink: 0,
                  background: a.stock_actuel <= 0 ? '#FCEBEB' : a.stock_actuel < 5 ? '#FFFBF0' : '#EAF3DE',
                  color: a.stock_actuel <= 0 ? 'var(--red)' : a.stock_actuel < 5 ? 'var(--amber)' : 'var(--green)',
                }}>
                  {a.stock_actuel <= 0 ? 'Rupture' : `${a.stock_actuel} ${a.unite || ''}`}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {showMiniForm && (
        <div style={{
          position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          background: 'var(--bg-primary)', border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)', boxShadow: '0 12px 40px rgba(0,0,0,0.2)',
          zIndex: 3000, padding: 16, width: 340, display: 'flex', flexDirection: 'column', gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, color: 'var(--blue)', paddingBottom: 8, borderBottom: '0.5px solid var(--border-light)' }}>
            <i className="ti ti-package-plus" aria-hidden="true" />
            Créer l'article "{value}"
          </div>

          {/* Sélecteur famille */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 500 }}>Famille</label>
            {!nouvelleFam ? (
              <div style={{ display: 'flex', gap: 6 }}>
                <select
                  style={{ flex: 1, padding: '7px 10px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 12, fontFamily: 'var(--font)' }}
                  value={familleId}
                  onChange={e => { setFamilleId(e.target.value); setTvaArticleExplicite(''); setErreurCreation('') }}>
                  <option value="">— Sans famille —</option>
                  {familles.map(f => (
                    <option key={f.id} value={f.id}>{f.libelle} ({nombreSaisieConnu(f.tva_defaut) ? `${f.tva_defaut}%` : 'TVA à vérifier'})</option>
                  ))}
                </select>
                <button onClick={() => { setNouvelleFam(true); setTvaArticleExplicite(''); setErreurCreation('') }}
                  style={{ fontSize: 11, padding: '6px 10px', borderRadius: 'var(--radius-sm)', background: 'var(--blue-light)', color: 'var(--blue)', border: '0.5px solid #B5D4F4', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  + Nouvelle
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: 10, background: 'var(--blue-light)', borderRadius: 'var(--radius-md)', border: '0.5px solid #B5D4F4' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--blue)' }}>Nouvelle famille</span>
                  <button onClick={() => { setNouvelleFam(false); setTvaArticleExplicite(''); setErreurCreation('') }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 12 }}>✕</button>
                </div>
                <input placeholder="Nom de la famille *"
                  value={nomFamille}
                  onChange={e => setNomFamille(e.target.value)}
                  style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', fontSize: 12, fontFamily: 'var(--font)' }} />
                <div style={{ display: 'flex', align: 'center', gap: 6 }}>
                  <label style={{ fontSize: 11, color: 'var(--text-tertiary)', alignSelf: 'center' }}>TVA</label>
                  <select value={tvafamille} onChange={e => setTvaFamille(e.target.value)}
                    style={{ flex: 1, padding: '5px 8px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', fontSize: 12 }}>
                    {tauxTVAAvecHistorique(dateDoc, tvafamille).map(t => <option key={t} value={t}>{t}%</option>)}
                  </select>
                </div>
              </div>
            )}
          </div>

          {familleTVAInconnue && <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 500 }}>TVA proposée pour cet article
              <select aria-label="TVA proposée pour cet article" value={tvaArticleExplicite}
                onChange={e => { setTvaArticleExplicite(e.target.value); setErreurCreation('') }}
                style={{ display: 'block', width: '100%', marginTop: 5, padding: '7px 10px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
                <option value="">À renseigner</option>
                {tauxTVAAvecHistorique(dateDoc, tvaArticleExplicite).map(t => <option key={t} value={t}>{t}%</option>)}
              </select>
            </label>
            <span style={{ fontSize: 11, color: 'var(--amber)' }}>La TVA de cette famille est inconnue. Ce choix concerne uniquement cet article ; le motif éventuel du 0 % reste à préciser sur la pièce.</span>
          </div>}
          {erreurCreation && <div role="alert" style={{ fontSize: 12, color: 'var(--red)' }}>{erreurCreation}</div>}

          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Tu pourras modifier le prix dans la page Articles.
          </div>

          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
            <button onClick={() => { setShowMiniForm(false); setNouvelleFam(false); setNomFamille(''); setTvaArticleExplicite(''); setErreurCreation('') }}
              style={{ fontSize: 12, padding: '6px 12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-primary)', border: '0.5px solid var(--border-medium)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              Annuler
            </button>
            <button onClick={creerArticle} disabled={loading || (nouvelleFam && !nomFamille.trim())}
              style={{ fontSize: 12, padding: '6px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--blue)', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 500 }}>
              {loading ? '...' : 'Créer'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Autocomplete tiers ───────────────────────────────────────────────────────
function ChampTiers({ value, onChange, type, onTiersSelect }) {
  const typeRecherche = type === 'vente' ? 'client' : type === 'achat' ? 'fournisseur' : type

  async function creerRapide(nom) {
    return tiersAPI.creer({
      nom,
      type: typeRecherche === 'fournisseur' ? 'fournisseur' : 'client',
      compte_client: '3421',
      compte_fournisseur: '4411',
      assujetti_tva: true,
      delai_paiement: 60,
    })
  }

  return (
    <TiersPicker
      value={value}
      onChange={onChange}
      onSelect={onTiersSelect}
      type={typeRecherche}
      allowCreate
      onCreate={creerRapide}
      placeholder={typeRecherche === 'fournisseur'
        ? 'Rechercher un fournisseur : nom, ICE, compte…'
        : 'Rechercher un client : nom, ICE, compte…'}
    />
  )
}

// ─── Formulaire nouvelle facture ──────────────────────────────────────────────
export function FormulaireFacture({ onFermer, onSuccess, initialData = null }) {
  const { ajouterFacture, validerFacture, comptabiliserFacture } = useFactures()
  const ecrituresCtx = useEcritures()
  const { aComptabilite } = useModules()
  const [type,          setType]          = useState(initialData?.type || 'vente')
  const [numero,        setNumero]        = useState(initialData?.numero || '')
  const [date,          setDate]          = useState(initialData?.date || dateLocaleISO())
  const [estProforma,   setEstProforma]   = useState(false)
  const [ristourne,     setRistourne]     = useState(0)
  const [reducOuverte,  setReducOuverte]  = useState(null)

  // Net d'une ligne : remise 1, puis remise 2 EN CASCADE, puis rabais par unité.
  // Reproduit exactement le calcul du serveur (8 % puis 3 % ≠ 11 %).
  function netLigne(l) {
    const q  = parseFloat(l.quantite) || 0
    const pu = parseFloat(l.prix_unitaire) || 0
    const r1 = parseFloat(l.remise)  || 0
    const r2 = parseFloat(l.remise2) || 0
    const rb = parseFloat(l.rabais)  || 0
    const net = q * pu * (1 - r1 / 100) * (1 - r2 / 100) - rb * q
    return net > 0 ? net : 0
  }

  // Numérotation automatique : propose le prochain numéro séquentiel si le champ est vide.
  useEffect(() => {
    const exercice = (date || '').slice(0, 4) || new Date().getFullYear()
    const token = localStorage.getItem('hisabpro_token')
    const typeDoc = estProforma ? 'proforma' : 'facture'
    fetch(`${API_BASE}/api/societe/prochain-numero?type_doc=${typeDoc}&exercice=${exercice}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        // À la bascule proforma/définitive, on remplace le numéro auto généré
        if (data?.numero) setNumero(data.numero)
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date?.slice(0, 4), estProforma])
  const [tiers,         setTiers]         = useState(initialData?.tiers || '')
  const [tiersId,       setTiersId]       = useState(initialData?.tiers_id || null)
  const [delaiAuto,     setDelaiAuto]     = useState(true)
  const [delaiPaiement, setDelaiPaiement] = useState(initialData?.delai_paiement ?? 60)
  const [dateEcheanceContractuelle, setDateEcheanceContractuelle] = useState(initialData?.date_echeance || '')
  const [modeReglementPrevu, setModeReglementPrevu] = useState(initialData?.mode_reglement_prevu || '')
  const [referenceReglementPrevue, setReferenceReglementPrevue] = useState(initialData?.reference_reglement_prevue || '')
  const [echeanceManuelle, setEcheanceManuelle] = useState(!!initialData?.date_echeance)
  const echeancesInitiales = (initialData?.echeances || []).filter(e => e?.id || (initialData?.echeances || []).length > 1)
  const [echeancierMultiple, setEcheancierMultiple] = useState(echeancesInitiales.length > 1)
  const [echeances, setEcheances] = useState(
    echeancesInitiales.length > 1
      ? echeancesInitiales.map(e => ({ date_echeance: String(e.date_echeance || '').slice(0, 10), pourcentage: '' , montantInitial: Number(e.montant || 0) }))
      : []
  )
  const [delaiTiers,    setDelaiTiers]    = useState(null)
  const [tiersSelectionne, setTiersSelectionne] = useState(null)
  const [reference,      setReference]     = useState(initialData?.reference || '')
  const [escompte,       setEscompte]       = useState(initialData?.escompte || 0)
  const [avecTransport,  setAvecTransport]  = useState((initialData?.frais_transport_ht || 0) > 0)
  const [transportHT,    setTransportHT]    = useState(initialData?.frais_transport_ht || 0)
  const [transportTVA,   setTransportTVA]   = useState(initialData?.frais_transport_tva ?? 20)
  const [transportMode, setTransportMode] = useState(initialData?.frais_transport_mode || 'accessoire')
  const [transportQualification, setTransportQualification] = useState(initialData?.frais_transport_qualification_tva || 'taxable')
  const [avecEmballage,  setAvecEmballage]  = useState((initialData?.frais_emballage_ht || 0) > 0)
  const [emballageHT,    setEmballageHT]    = useState(initialData?.frais_emballage_ht || 0)
  const [emballageTVA,   setEmballageTVA]   = useState(initialData?.frais_emballage_tva ?? 20)
  const [emballageMode, setEmballageMode] = useState(initialData?.frais_emballage_mode || 'perdu')
  const [emballageQualification, setEmballageQualification] = useState(initialData?.frais_emballage_qualification_tva || 'taxable')
  const [rasTaux,        setRasTaux]        = useState(initialData?.ras_taux || 0)
  const [natureTVAAchat, setNatureTVAAchat] = useState(initialData?.nature_tva_achat || 'charge')
  const [tvaDeductiblePct, setTvaDeductiblePct] = useState(initialData?.tva_deductible_pct ?? 100)
  const [comptabiliser, setComptabiliser] = useState(true)
  const [ecritureGeneree, setEcritureGeneree] = useState(true)
  const [lignes,        setLignes]        = useState(
    initialData?.lignes?.length
      ? initialData.lignes.map(l => ({
          description: l.description,
          quantite: l.quantite,
          prix_unitaire: l.prix_unitaire,
          tva: l.tva ?? 20,
          qualification_tva: l.qualification_tva || (Number(l.tva) === 0 ? 'exonere_sans_deduction' : 'taxable'),
          remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
          famille_id: '', famille_libelle: null, article_id: l.article_id || null, source_ligne_devis_id: l.source_ligne_devis_id || null, source_ligne_bc_id: l.source_ligne_bc_id || null, source_ligne_bl_id: l.source_ligne_bl_id || null, stock_actuel: null, unite: 'unité',
        }))
      : [{ description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, famille_id: '', famille_libelle: null, article_id: null, stock_actuel: null, unite: 'unité' }]
  )
  const [loading,           setLoading]           = useState(false)
  const [erreur,            setErreur]            = useState('')
  const [saved,             setSaved]             = useState(false)
  const [fieldErrors,       setFieldErrors]       = useState({})

  // Réappliquer initialData si il arrive après le montage
  useEffect(() => {
    if (initialData) {
      if (initialData.type)      setType(initialData.type)
      if (initialData.tiers)     setTiers(initialData.tiers)
      if (initialData.tiers_id)  setTiersId(initialData.tiers_id)
      // Une nouvelle source doit également pouvoir effacer l'ancienne référence.
      // Le BC d'achat n'est pas le numéro de facture du fournisseur.
      setReference(initialData.type === 'achat' && initialData.bc_id ? '' : (initialData.reference || ''))
      if (initialData.lignes?.length) {
        setLignes(initialData.lignes.map(l => ({
          description:   l.description,
          quantite:      l.quantite,
          prix_unitaire: l.prix_unitaire,
          tva:           l.tva ?? 20,
          qualification_tva: l.qualification_tva || (Number(l.tva) === 0 ? 'exonere_sans_deduction' : 'taxable'),
          remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
          famille_id: '', famille_libelle: null, article_id: l.article_id || null, source_ligne_devis_id: l.source_ligne_devis_id || null, source_ligne_bc_id: l.source_ligne_bc_id || null, source_ligne_bl_id: l.source_ligne_bl_id || null, stock_actuel: null, unite: 'unité',
        })))
      }
    }
  }, [initialData])

  // Lors d'une conversion Devis/BC/BL → facture, récupérer le vrai tiers afin
  // d'appliquer immédiatement ses conditions de paiement, sa RAS et ses comptes.
  useEffect(() => {
    if (!initialData?.tiers_id) return
    const token = localStorage.getItem('hisabpro_token')
    fetch(`${API_BASE}/api/tiers/${initialData.tiers_id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('Tiers introuvable')))
      .then(handleTiersSelect)
      .catch(() => {})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialData?.tiers_id])

  // Délai effectif = délai du tiers si mode auto, sinon délai manuel
  const delaiEffectif = delaiAuto && delaiTiers !== null && delaiTiers !== undefined
    ? Number(delaiTiers)
    : entierOuDefaut(delaiPaiement, 60)

  useEffect(() => {
    if (echeanceManuelle || !date) return
    setDateEcheanceContractuelle(dateLocaleISO(dateEcheance(date, delaiEffectif)))
  }, [date, delaiEffectif, echeanceManuelle])

  const [articles, setArticles] = useState([])
  const [familles, setFamilles] = useState([])

  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch(API_BASE + '/api/articles', { headers }).then(r => r.json()),
      fetch(API_BASE + '/api/familles', { headers }).then(r => r.json()),
    ]).then(([arts, fams]) => {
      setArticles(arts)
      setFamilles(fams)
    }).catch(() => {})
  }, [])

  function choisirArticle(i, article) {
    setLignes(prev => prev.map((l, idx) => idx === i ? {
      ...l,
      description:     article.designation,
      prix_unitaire:   nombreArticleSaisie(type === 'achat' ? article.prix_achat_ht : article.prix_vente_ht),
      tva:             nombreArticleSaisie(article.tva),
      qualification_tva: qualificationArticle(article.tva),
      article_id:      article.id,
      stock_actuel:    article.stock_actuel ?? null,
      unite:           article.unite || 'unité',
      famille_libelle: article.famille?.libelle || null,
      famille_id:      article.famille_id || '',
    } : l))
  }

  function majLigne(i, champ, val) {
    setLignes(prev => prev.map((l, idx) => idx === i ? { ...l, [champ]: val } : l))
  }

  function handleTiersSelect(tiersObj) {
    setTiersId(tiersObj?.id ?? null)
    setTiersSelectionne(tiersObj || null)
    const delai = tiersObj?.delai_paiement
    setDelaiTiers(delai ?? null)
    setDelaiPaiement(delai ?? 60)
    setDelaiAuto(delai !== null && delai !== undefined)
    if (tiersObj?.taux_ras !== null && tiersObj?.taux_ras !== undefined) setRasTaux(tiersObj.taux_ras)
    setFieldErrors(p => ({ ...p, tiers: '' }))
  }

  const totaux = useMemo(() => {
    const coefRist = 1 - ((parseFloat(ristourne) || 0) / 100)
    const basesLignes = lignes.map(l => ({
      base: netLigne(l) * coefRist,
      taux: tvaEffective(l),
    }))
    const htLignes = basesLignes.reduce((acc, l) => acc + l.base, 0)
    const tvaLignes = basesLignes.reduce((acc, l) => acc + l.base * l.taux / 100, 0)
    const poidsTotal = basesLignes.reduce((acc, l) => acc + l.base, 0)
    const tauxMoyen = poidsTotal > 0 ? (tvaLignes / poidsTotal) : 0

    const transportHtVal = avecTransport ? (parseFloat(transportHT) || 0) : 0
    const transportTaux = transportMode === 'accessoire'
      ? tauxMoyen
      : (transportQualification === 'taxable' ? (parseFloat(transportTVA) || 0) : 0)
    const transportTvaVal = transportHtVal * transportTaux / 100

    const emballageHtVal = avecEmballage ? (parseFloat(emballageHT) || 0) : 0
    const emballageTaux = emballageMode === 'perdu'
      ? tauxMoyen
      : emballageMode === 'consigne'
        ? 0
        : (emballageQualification === 'taxable' ? (parseFloat(emballageTVA) || 0) : 0)
    const emballageTvaVal = emballageHtVal * emballageTaux / 100

    const consigne = emballageMode === 'consigne' ? emballageHtVal : 0
    const baseEligibleEscompte = htLignes + transportHtVal + (emballageMode === 'consigne' ? 0 : emballageHtVal)
    const tvaEligibleEscompte = tvaLignes + transportTvaVal + emballageTvaVal
    const esc = parseFloat(escompte) || 0
    const coefEsc = 1 - esc / 100
    const htApresEsc = baseEligibleEscompte * coefEsc
    const tvaApresEsc = tvaEligibleEscompte * coefEsc
    const ttcNet = htApresEsc + tvaApresEsc + consigne
    const htAffiche = htLignes + transportHtVal + emballageHtVal
    const ras = htApresEsc * ((parseFloat(rasTaux) || 0) / 100)
    return {
      ht: htAffiche, tva: tvaApresEsc, htRG: htApresEsc, tvaRG: tvaApresEsc,
      ttcBrut: baseEligibleEscompte + tvaEligibleEscompte + consigne,
      ttc: ttcNet, rg: 0, esc, ras, netAPayer: ttcNet - ras, consigne,
    }
  }, [lignes, escompte, ristourne, avecTransport, transportHT, transportTVA, transportMode, transportQualification, avecEmballage, emballageHT, emballageTVA, emballageMode, emballageQualification, rasTaux])

  useEffect(() => {
    if (!echeancierMultiple || echeances.length === 0 || !totaux.ttc) return
    // Pour un échéancier chargé depuis une facture existante, dériver les % du TTC
    // une seule fois si seuls les montants historiques sont connus.
    if (echeances.some(e => e.pourcentage === '' && e.montantInitial != null)) {
      setEcheances(prev => prev.map(e => ({
        ...e,
        pourcentage: e.pourcentage === '' && e.montantInitial != null
          ? ((Number(e.montantInitial || 0) / Number(totaux.ttc || 1)) * 100).toFixed(2)
          : e.pourcentage,
        montantInitial: undefined,
      })))
    }
  }, [echeancierMultiple, totaux.ttc])

  const echeancesCalculees = useMemo(() => {
    if (!echeancierMultiple) return []
    let cumule = 0
    return echeances.map((e, idx) => {
      const pct = Math.max(0, Number(e.pourcentage || 0))
      let montant = Math.round((Number(totaux.ttc || 0) * pct / 100) * 100) / 100
      if (idx === echeances.length - 1) montant = Math.round((Number(totaux.ttc || 0) - cumule) * 100) / 100
      cumule += montant
      return { ...e, pourcentage: pct, montant }
    })
  }, [echeancierMultiple, echeances, totaux.ttc])

  const totalPourcentageEcheancier = useMemo(() =>
    echeances.reduce((sum, e) => sum + Number(e.pourcentage || 0), 0), [echeances])

  function presetEcheancier(pcts) {
    const depart = dateEcheanceContractuelle || date || dateLocaleISO()
    const base = new Date(`${depart}T12:00:00`)
    setEcheancierMultiple(true)
    setEcheances(pcts.map((pct, idx) => {
      const d = new Date(base)
      if (idx > 0) d.setDate(d.getDate() + 30 * idx)
      return { date_echeance: dateLocaleISO(d), pourcentage: pct }
    }))
  }

  function majEcheance(idx, champ, valeur) {
    setEcheances(prev => prev.map((e, i) => i === idx ? { ...e, [champ]: valeur } : e))
  }

  const dateEch = useMemo(() => {
    if (!dateEcheanceContractuelle) return null
    return new Date(`${dateEcheanceContractuelle}T12:00:00`).toLocaleDateString('fr-MA', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }, [dateEcheanceContractuelle])

  function changerType(nouveauType) {
    if (nouveauType === type) return
    setType(nouveauType)
    setTiers('')
    setTiersId(null)
    setTiersSelectionne(null)
    setDelaiTiers(null)
    setDelaiAuto(true)
    setReference('')
    setRasTaux(0)
    setFieldErrors({})
    setLignes(prev => prev.map(l => {
      const article = l.article_id ? articles.find(a => a.id === l.article_id) : null
      return article ? { ...l, prix_unitaire: nombreArticleSaisie(nouveauType === 'achat' ? article.prix_achat_ht : article.prix_vente_ht) } : l
    }))
  }

  function validerFormulaire() {
    const e = {}
    if (!date) e.date = 'La date est obligatoire.'
    if (!tiers.trim()) e.tiers = `Le ${type === 'vente' ? 'client' : 'fournisseur'} est obligatoire.`
    if (delaiEffectif < 0) e.delai = 'Le délai de paiement ne peut pas être négatif.'
    if (date && dateEcheanceContractuelle && dateEcheanceContractuelle < date) e.echeance = 'L’échéance ne peut pas précéder la facture.'
    if (echeancierMultiple) {
      if (echeances.length < 2) e.echeancier = 'Ajoutez au moins deux échéances ou repassez en paiement unique.'
      else if (Math.abs(totalPourcentageEcheancier - 100) > 0.01) e.echeancier = `La répartition doit totaliser 100 % (actuellement ${totalPourcentageEcheancier.toFixed(2)} %).`
      else if (echeances.some(x => !x.date_echeance)) e.echeancier = 'Chaque échéance doit avoir une date.'
      else if (echeances.some(x => x.date_echeance < date)) e.echeancier = 'Une échéance ne peut pas précéder la date de facture.'
      else if (echeances.some(x => Number(x.pourcentage || 0) <= 0)) e.echeancier = 'Chaque échéance doit avoir un pourcentage strictement positif.'
    }
    if (comptabiliser && type === 'achat' && !estProforma && !reference.trim()) e.reference = 'Le N° de facture fournisseur est obligatoire pour valider.'

    const lignesActives = lignes.filter(l => (l.description || '').trim())
    if (lignesActives.length === 0) e.lignes = 'Ajoutez au moins une ligne de facturation.'
    lignesActives.forEach((l, idx) => {
      const q = nombreOuDefaut(l.quantite, 0)
      const pu = nombreOuDefaut(l.prix_unitaire, -1)
      const tva = nombreOuDefaut(l.tva, -1)
      const r1 = nombreOuDefaut(l.remise, 0)
      const r2 = nombreOuDefaut(l.remise2, 0)
      const rabais = nombreOuDefaut(l.rabais, 0)
      if (q <= 0) e.lignes = `Ligne ${idx + 1} : la quantité doit être strictement positive.`
      else if (l.prix_unitaire === '' || l.prix_unitaire == null) e.lignes = `Ligne ${idx + 1} : prix unitaire inconnu, renseignez une valeur explicite.`
      else if (l.tva === '' || l.tva == null) e.lignes = `Ligne ${idx + 1} : TVA inconnue, renseignez un taux explicite.`
      else if (pu < 0) e.lignes = `Ligne ${idx + 1} : le prix unitaire ne peut pas être négatif.`
      else if (tva < 0 || tva > 100) e.lignes = `Ligne ${idx + 1} : taux de TVA invalide.`
      else if (tva === 0 && (!l.qualification_tva || l.qualification_tva === 'taxable')) e.lignes = `Ligne ${idx + 1} : précisez pourquoi la TVA est à 0 %.`
      else if (tva > 0 && l.qualification_tva && l.qualification_tva !== 'taxable') e.lignes = `Ligne ${idx + 1} : une opération exonérée/hors champ doit être à 0 %.`
      else if (!tauxTVAPourDate(date).includes(Number(tva))) e.lignes = `Ligne ${idx + 1} : taux de TVA incompatible avec la date.`
      else if (r1 < 0 || r1 > 100 || r2 < 0 || r2 > 100) e.lignes = `Ligne ${idx + 1} : remise invalide.`
      else if (rabais < 0) e.lignes = `Ligne ${idx + 1} : rabais invalide.`
    })
    setFieldErrors(e)
    return { ok: Object.keys(e).length === 0, lignesActives }
  }

  async function handleSave() {
    const validation = validerFormulaire()
    if (!validation.ok) { setErreur('Vérifiez les champs signalés avant de continuer.'); return }
    const lignesActives = validation.lignesActives

    // Le stock n'est contrôlé de façon bloquante que si l'utilisateur finalise
    // immédiatement. Un simple brouillon peut être préparé à l'avance.
    if (comptabiliser && type === 'vente') {
      const lignesEnRupture = lignesActives.filter(l =>
        l.article_id && l.stock_actuel !== null && l.stock_actuel !== undefined &&
        (parseFloat(l.quantite) || 0) > l.stock_actuel
      )
      if (lignesEnRupture.length > 0) {
        const detail = lignesEnRupture
          .map(l => `« ${l.description} » : demandé ${l.quantite}, stock disponible ${l.stock_actuel}`)
          .join('\n')
        setErreur(`Stock insuffisant pour continuer :\n${detail}`)
        return
      }
    }

    setLoading(true); setErreur('')
    try {
      const facture = await ajouterFacture({
        numero: estProforma ? numero : null, type, date, tiers, tiers_id: tiersId, reference,
        statut: 'en_attente',
        delai_paiement: delaiEffectif,
        date_echeance: dateEcheanceContractuelle || null,
        mode_reglement_prevu: modeReglementPrevu || null,
        reference_reglement_prevue: referenceReglementPrevue.trim() || null,
        echeances: echeancierMultiple ? echeancesCalculees.map((e, idx) => ({
          date_echeance: e.date_echeance,
          montant: e.montant,
          libelle: `Échéance ${idx + 1}/${echeancesCalculees.length}`,
        })) : null,
        remise_globale: 0,
        ristourne:      parseFloat(ristourne)     || 0,
        escompte:       parseFloat(escompte)      || 0,
        frais_transport_ht:  avecTransport ? (parseFloat(transportHT) || 0) : 0,
        frais_transport_tva: avecTransport ? (parseFloat(transportTVA) || 0) : 20,
        frais_transport_mode: transportMode,
        frais_transport_qualification_tva: transportMode === 'distinct' ? transportQualification : 'taxable',
        frais_emballage_ht:  avecEmballage ? (parseFloat(emballageHT) || 0) : 0,
        frais_emballage_tva: avecEmballage ? (parseFloat(emballageTVA) || 0) : 20,
        frais_emballage_mode: emballageMode,
        frais_emballage_qualification_tva: emballageMode === 'vente_distincte' ? emballageQualification : 'taxable',
        ras_taux:            parseFloat(rasTaux) || 0,
        nature_tva_achat:    type === 'achat' ? natureTVAAchat : 'charge',
        tva_deductible_pct:  type === 'achat'
          ? (natureTVAAchat === 'non_deductible' ? 0 : Math.max(0, Math.min(100, parseFloat(tvaDeductiblePct) || 0)))
          : 100,
        est_proforma:        estProforma,
        lignes: lignesActives.map(l => ({
          article_id: l.article_id || null,
          source_ligne_devis_id: l.source_ligne_devis_id || null,
          source_ligne_bc_id: l.source_ligne_bc_id || null,
          source_ligne_bl_id: l.source_ligne_bl_id || null,
          description:   l.description,
          quantite:      nombreOuDefaut(l.quantite, 0),
          prix_unitaire: nombreOuDefaut(l.prix_unitaire, 0),
          tva:           nombreOuDefaut(l.tva, 20),
          qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva),
          remise:        nombreOuDefaut(l.remise, 0),
          remise2:       nombreOuDefaut(l.remise2, 0),
          rabais:        nombreOuDefaut(l.rabais, 0),
        })),
      })

      // Les liens amont sont portés par les lignes source (devis/BC/BL).
      // On ne force pas le statut de la pièce source tant que la facture n'est
      // qu'un brouillon : supprimer/corriger ce brouillon doit libérer la source.

      // FACT.4 : la finalisation attribue d'abord le numéro définitif et fige
      // la facture. La comptabilisation vient seulement ensuite.
      let compteOK = true
      let avertissementsMentions = []
      if (comptabiliser && facture?.id && !estProforma) {
        try {
          const validation = await validerFacture(facture.id)
          avertissementsMentions = validation?.avertissements_mentions || []
          if (aComptabilite) {
            await comptabiliserFacture(facture.id)
            if (ecrituresCtx?.recharger) await ecrituresCtx.recharger()
          }
        } catch (e) {
          compteOK = false
          notifier(
            `Le brouillon a bien été enregistré, mais la finalisation n'a pas pu aboutir :\n\n${e.message}\n\n` +
            `Corrigez le brouillon puis validez-le depuis la liste des factures.`
          )
        }
      }
      setEcritureGeneree(compteOK)
      setSaved(true)
      setTimeout(() => { onSuccess?.(avertissementsMentions); onFermer() }, 700)
    } catch (e) {
      setErreur(e.message)
    } finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouvelle facture" icone="ti-file-plus" onFermer={onFermer} largeur="lg">
      {saved ? (
        <div className={styles.successMsg}>
          <i className="ti ti-circle-check" aria-hidden="true" />
          {estProforma ? 'Proforma enregistrée !' : (comptabiliser && ecritureGeneree
            ? (aComptabilite ? 'Facture validée & comptabilisée !' : 'Facture validée !')
            : 'Brouillon enregistré !')}
        </div>
      ) : (
        <div className={styles.formContenu}>
          <FormSection icon="ti-file-invoice" title="Document & tiers" description="Les informations essentielles de la facture. Les paramètres du tiers sont repris automatiquement.">
          {initialData?.source_document_numero && (
            <div className={styles.sourceInfo} role="note">
              <i className="ti ti-link" aria-hidden="true" />
              {initialData.type === 'achat' ? 'Commande fournisseur d’origine' : 'Commande d’origine'} :
              <strong>{initialData.source_document_numero}</strong>
              {initialData.type === 'achat' && <span>— indiquez séparément le numéro figurant sur la facture du fournisseur.</span>}
            </div>
          )}
          {/* 1. Date + Type */}
          <div className={styles.formGrid4}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Date *</label>
              <input className={`${styles.input} ${fieldErrors.date ? styles.inputError : ''}`} type="date"
                value={date} onChange={e => { setDate(e.target.value); setFieldErrors(p => ({ ...p, date: '' })) }} />
              {fieldErrors.date && <span className={styles.fieldError}>{fieldErrors.date}</span>}
            </div>
            <div className={styles.formGroup} style={{ gridColumn: 'span 3' }}>
              <label className={styles.label}>Type</label>
              <div className={styles.typeToggle}>
                <button className={`${styles.typeBtn} ${type === 'vente' ? styles.typeBtnActif : ''}`} onClick={() => changerType('vente')}>
                  <i className="ti ti-arrow-up-right" aria-hidden="true" /> Vente
                </button>
                <button className={`${styles.typeBtn} ${type === 'achat' ? styles.typeBtnActif : ''}`} onClick={() => changerType('achat')}>
                  <i className="ti ti-arrow-down-left" aria-hidden="true" /> Achat
                </button>
              </div>
            </div>
          </div>

          {/* 2. Client/Fournisseur — recherche unifiée nom / ICE / compte */}
          <div className={styles.formGroup}>
            <label className={styles.label}>{type === 'vente' ? 'Client *' : 'Fournisseur *'}</label>
            <ChampTiers
              value={tiers}
              onChange={val => { setTiers(val); setFieldErrors(p => ({ ...p, tiers: '' })) }}
              type={type}
              onTiersSelect={handleTiersSelect}
            />
            <span className={styles.fieldHint}>Recherche par nom, ICE, compte comptable ou ville.</span>
            {fieldErrors.tiers && <span className={styles.fieldError}>{fieldErrors.tiers}</span>}
            {tiersSelectionne && (
              <span className={styles.selectionHint}>
                <i className="ti ti-circle-check" /> {tiersSelectionne.nom}
                {' · '}{type === 'vente' ? (tiersSelectionne.compte_client || '3421') : (tiersSelectionne.compte_fournisseur || '4411')}
                {tiersSelectionne.delai_paiement === 0 ? ' · comptant' : (tiersSelectionne.delai_paiement != null ? ` · ${tiersSelectionne.delai_paiement} j` : '')}
              </span>
            )}
          </div>

          {/* 3. Numérotation + référence */}
          <div className={styles.formGrid4}>
            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
              <label className={styles.label}>{estProforma ? 'N° Proforma' : 'N° facture interne'}</label>
              <input className={styles.input} type="text" readOnly
                value={numero ? `${numero}${estProforma ? '' : ' (prévision)'}` : 'Attribué à la validation'} />
              {!estProforma && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>La prévision n’est pas réservée. Le numéro définitif est attribué à la validation.</span>}
            </div>
            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
              <label className={styles.label}>
                {type === 'achat' ? 'N° facture fournisseur' : 'Référence / N° commande'}
                {type === 'achat' && comptabiliser && !estProforma ? ' *' : ''}
              </label>
              <input className={`${styles.input} ${fieldErrors.reference ? styles.inputError : ''}`} type="text"
                placeholder={type === 'achat' ? 'N° porté sur la facture du fournisseur' : 'N° BC, bon de commande...'}
                value={reference} onChange={e => { setReference(e.target.value); setFieldErrors(p => ({ ...p, reference: '' })) }} />
              {fieldErrors.reference && <span className={styles.fieldError}>{fieldErrors.reference}</span>}
            </div>
          </div>

          <div className={styles.formGrid4}>
            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
              <label className={styles.label}>Délai de paiement</label>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input className={`${styles.input} ${fieldErrors.delai ? styles.inputError : ''}`} type="number" min="0" step="1" value={delaiEffectif}
                  aria-label="Délai de paiement de la nouvelle facture"
                  onChange={e => { setDelaiPaiement(e.target.value); setDelaiAuto(false); setEcheanceManuelle(false) }} />
                {!delaiAuto && delaiTiers !== null && delaiTiers !== undefined && <button type="button" className={styles.btnSec} style={{ padding: '7px 9px', fontSize: 10 }}
                  title="Reprendre le délai du tiers" onClick={() => { setDelaiPaiement(delaiTiers); setDelaiAuto(true); setEcheanceManuelle(false) }}>Tiers</button>}
              </div>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{delaiEffectif === 0 ? 'Paiement comptant' : `${delaiEffectif} jour${delaiEffectif > 1 ? 's' : ''}`}</span>
              {fieldErrors.delai && <span className={styles.fieldError}>{fieldErrors.delai}</span>}
            </div>
            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
              <label className={styles.label}>Échéance</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input aria-label="Échéance de la nouvelle facture" className={`${styles.input} ${fieldErrors.echeance ? styles.inputError : ''}`} type="date" value={dateEcheanceContractuelle}
                  min={date || undefined}
                  onChange={e => { setDateEcheanceContractuelle(e.target.value); setEcheanceManuelle(true); setFieldErrors(p => ({ ...p, echeance: '' })) }} />
                {echeanceManuelle && <button type="button" className={styles.btnSec} style={{ padding: '7px 9px', fontSize: 10 }}
                  onClick={() => setEcheanceManuelle(false)}>Auto</button>}
              </div>
              {dateEch && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Échéance retenue : {dateEch}</span>}
              {fieldErrors.echeance && <span className={styles.fieldError}>{fieldErrors.echeance}</span>}
            </div>
          </div>

          {!estProforma && (
            <div className={styles.formGrid4} style={{ marginTop: 10 }}>
              <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                <label className={styles.label}>Mode de règlement convenu</label>
                <select className={styles.input} value={modeReglementPrevu} onChange={e => setModeReglementPrevu(e.target.value)}>
                  {MODES_REGLEMENT_PREVUS.map(([v,l]) => <option key={v || 'none'} value={v}>{l}</option>)}
                </select>
              </div>
              <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                <label className={styles.label}>Référence de règlement prévue</label>
                <input className={styles.input} value={referenceReglementPrevue} onChange={e => setReferenceReglementPrevue(e.target.value)} placeholder="Optionnel : réf. virement, effet, commande…" />
              </div>
              {delaiEffectif > 120 && <div style={{ gridColumn: 'span 4' }}>
                <InlineNotice type="warning">Délai supérieur à 120 jours : vérifiez la convention ou la dérogation sectorielle applicable.</InlineNotice>
              </div>}
            </div>
          )}

          {!estProforma && (
            <div className={styles.echeancierBox}>
              <div className={styles.echeancierHead}>
                <div>
                  <strong>Conditions de paiement</strong>
                  <span>Une ou plusieurs échéances contractuelles.</span>
                </div>
                <div className={styles.echeancierToggle}>
                  <button type="button" className={!echeancierMultiple ? styles.echeancierModeActif : ''}
                    onClick={() => { setEcheancierMultiple(false); setEcheances([]) }}>Paiement unique</button>
                  <button type="button" className={echeancierMultiple ? styles.echeancierModeActif : ''}
                    onClick={() => echeances.length >= 2 ? setEcheancierMultiple(true) : presetEcheancier([50, 50])}>Échéancier</button>
                </div>
              </div>
              {echeancierMultiple && (
                <>
                  <div className={styles.echeancierPresets}>
                    <span>Répartition rapide :</span>
                    <button type="button" onClick={() => presetEcheancier([50, 50])}>50 / 50</button>
                    <button type="button" onClick={() => presetEcheancier([30, 40, 30])}>30 / 40 / 30</button>
                    <button type="button" onClick={() => presetEcheancier([25, 25, 25, 25])}>4 × 25 %</button>
                  </div>
                  <div className={styles.echeancierRows}>
                    {echeancesCalculees.map((e, idx) => (
                      <div className={styles.echeancierRow} key={idx}>
                        <span className={styles.echeancierNumero}>{idx + 1}</span>
                        <input className={styles.input} type="date" min={date || undefined} value={e.date_echeance || ''}
                          onChange={ev => majEcheance(idx, 'date_echeance', ev.target.value)} />
                        <div className={styles.echeancierPct}>
                          <input className={styles.input} type="number" min="0.01" max="100" step="0.01" value={e.pourcentage}
                            onChange={ev => majEcheance(idx, 'pourcentage', ev.target.value)} />
                          <span>%</span>
                        </div>
                        <strong>{formatMAD(e.montant)} MAD</strong>
                        <button type="button" className={styles.echeancierRemove} title="Supprimer l’échéance"
                          onClick={() => setEcheances(prev => prev.filter((_, i) => i !== idx))}><i className="ti ti-x" /><span className="libelle-action" aria-hidden="true">Supprimer l’échéance</span></button>
                      </div>
                    ))}
                  </div>
                  <div className={styles.echeancierFooter}>
                    <button type="button" className={styles.btnSec} onClick={() => setEcheances(prev => [...prev, { date_echeance: dateEcheanceContractuelle || date, pourcentage: 0 }])}>
                      <i className="ti ti-plus" /> Ajouter une échéance
                    </button>
                    <span className={Math.abs(totalPourcentageEcheancier - 100) <= 0.01 ? styles.echeancierOk : styles.echeancierKo}>
                      Total : {totalPourcentageEcheancier.toFixed(2)} % · {montantLignesSaisies(totaux.ttc, lignes, formatMAD)} MAD
                    </span>
                  </div>
                  {fieldErrors.echeancier && <span className={styles.fieldError}>{fieldErrors.echeancier}</span>}
                </>
              )}
            </div>
          )}

          </FormSection>

          <FormSection icon="ti-list-details" title="Lignes de facturation" description="Ajoutez les articles ou services à facturer. Les prix, TVA et comptes sont proposés depuis les fiches articles." action={<button type="button" className={styles.btnAjout} onClick={() => setLignes(p => [...p, { description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, famille_id: '', famille_libelle: null, article_id: null, stock_actuel: null, unite: 'unité' }])}><i className="ti ti-plus" /> Ajouter une ligne</button>}>
          {/* Lignes */}
          <div className="hp-invoice-line-editor">
          <div className={styles.lignesHeader}>
            <span className={styles.lignesTitle}>Détail</span>
            <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)' }}>{lignes.length} ligne{lignes.length > 1 ? 's' : ''}</span>
          </div>
          <div className={styles.lignesColHeaders}>
            <span>Famille → Article</span>
            <span style={{ textAlign: 'right' }}>Qté</span>
            <span style={{ textAlign: 'right' }}>P.U. HT</span>
            <span style={{ textAlign: 'right' }}>Remise%</span>
            <span style={{ textAlign: 'right' }}>TVA</span>
            <span style={{ textAlign: 'right' }}>Total HT</span>
            <span />
          </div>
          {lignes.map((l, i) => (
            <div key={i} className={styles.ligneFactRow}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {/* Champ article filtré par famille */}
                <ChampArticle
                  dateDoc={date}
                  value={l.description}
                  articles={articles}
                  familles={familles}
                  type={type}
                  filtreFamilleId={l.famille_id}
                  onChange={val => majLigne(i, 'description', val)}
                  onFamilleCreee={fam => setFamilles(prev => [...prev, fam])}
                  onSelect={art => {
                    choisirArticle(i, art)
                    if (!articles.find(a => a.id === art.id)) {
                      setArticles(prev => [...prev, art])
                    }
                  }}
                />
                {/* Stock sous le champ article */}
                {type === 'vente' && l.stock_actuel !== null && l.stock_actuel !== undefined && (
                  <span style={{
                    fontSize: 10,
                    color: l.stock_actuel <= 0 ? 'var(--red)' : parseFloat(l.quantite) > l.stock_actuel ? 'var(--amber)' : 'var(--text-tertiary)',
                    display: 'flex', alignItems: 'center', gap: 3,
                  }}>
                    {l.stock_actuel <= 0
                      ? <><i className="ti ti-alert-circle" style={{ fontSize: 10 }} /> Rupture de stock</>
                      : parseFloat(l.quantite) > l.stock_actuel
                        ? <><i className="ti ti-alert-triangle" style={{ fontSize: 10 }} /> Stock: {l.stock_actuel} {l.unite || ''}</>
                        : <>Stock dispo: {l.stock_actuel} {l.unite || ''}</>
                    }
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <input className={`${styles.inputSm} ${styles.num}`} type="number" min="0.0001" step="0.01"
                  value={l.quantite} onChange={e => majLigne(i, 'quantite', e.target.value)}
                  style={type === 'vente' && l.stock_actuel !== null && parseFloat(l.quantite) > l.stock_actuel
                    ? { borderColor: 'var(--amber)', background: '#FFFBF0' } : {}} />
                {type === 'vente' && l.stock_actuel !== null && (
                  <span style={{
                    fontSize: 10, textAlign: 'right', whiteSpace: 'nowrap',
                    color: parseFloat(l.quantite) > l.stock_actuel ? 'var(--amber)' : 'var(--text-tertiary)',
                  }}>
                    {parseFloat(l.quantite) > l.stock_actuel
                      ? `⚠ stock: ${l.stock_actuel} ${l.unite || ''}`
                      : `En stock: ${l.stock_actuel} ${l.unite || ''}`}
                  </span>
                )}
              </div>
              <label className={styles.ligneChampMobile}>
                <span>Prix unitaire HT</span>
                <input className={`${styles.inputSm} ${styles.num}`} type="number" min="0"
                  value={l.prix_unitaire} onChange={e => majLigne(i, 'prix_unitaire', e.target.value)} />
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input className={`${styles.inputSm} ${styles.num}`} type="number" min="0" max="100" step="0.1"
                  value={l.remise || 0} onChange={e => majLigne(i, 'remise', e.target.value)}
                  placeholder="0"
                  style={{ paddingRight: 18 }} />
                <span style={{ position: 'absolute', right: 6, fontSize: 10, color: 'var(--text-tertiary)', pointerEvents: 'none' }}>%</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <select className={styles.inputSm} value={l.tva}
                  onChange={e => {
                    const taux = Number(e.target.value)
                    majLigne(i, 'tva', e.target.value)
                    majLigne(i, 'qualification_tva', e.target.value === '' ? '' : qualificationParDefautPourTaux(taux, l.qualification_tva))
                  }}>
                  <option value="">À vérifier</option>
                  {tauxTVAAvecHistorique(date, l.tva).map(t => <option key={t} value={t}>{t}%</option>)}
                </select>
                {nombreSaisieConnu(l.tva) && Number(l.tva) === 0 && (
                  <select className={styles.inputSm} value={l.qualification_tva || 'exonere_sans_deduction'}
                    onChange={e => majLigne(i, 'qualification_tva', e.target.value)} title="Qualification du taux 0 %">
                    {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => (
                      <option key={q.value} value={q.value}>{q.label}</option>
                    ))}
                  </select>
                )}
              </div>
              <span className={`${styles.inputSm} ${styles.num}`}
                style={{ border: 'none', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: 500 }}>
                {montantLignesSaisies(netLigne(l), [l], formatMAD)}
              </span>
              <button className={styles.btnSuppr} disabled={lignes.length <= 1}
                onClick={() => setLignes(p => p.filter((_, idx) => idx !== i))}>
                <i className="ti ti-trash" aria-hidden="true" />
              </button>

              {/* Réductions avancées : 2e remise (en cascade) et rabais (montant par unité).
                  Repliées par défaut pour ne pas alourdir la saisie courante. */}
              <div className={styles.reducLigne}>
                <button type="button" className={styles.reducToggle}
                  onClick={() => setReducOuverte(reducOuverte === i ? null : i)}>
                  <i className={`ti ti-chevron-${reducOuverte === i ? 'down' : 'right'}`} />
                  Réductions
                  {(parseFloat(l.remise2) > 0 || parseFloat(l.rabais) > 0) && (
                    <span className={styles.reducBadge}>
                      {parseFloat(l.remise2) > 0 && `−${l.remise2}%`}
                      {parseFloat(l.remise2) > 0 && parseFloat(l.rabais) > 0 && ' · '}
                      {parseFloat(l.rabais) > 0 && `−${l.rabais} MAD/u`}
                    </span>
                  )}
                </button>
                {reducOuverte === i && (
                  <div className={styles.reducChamps}>
                    <label>
                      <span>Remise 2 (%)</span>
                      <input className={styles.inputSm} type="number" min="0" max="100" step="0.1"
                        value={l.remise2 || 0}
                        onChange={e => majLigne(i, 'remise2', e.target.value)} />
                      <em>Appliquée après la remise 1, en cascade</em>
                    </label>
                    <label>
                      <span>Rabais (MAD / unité)</span>
                      <input className={styles.inputSm} type="number" min="0" step="0.01"
                        value={l.rabais || 0}
                        onChange={e => majLigne(i, 'rabais', e.target.value)} />
                      <em>Réduction exceptionnelle (défaut, retard)</em>
                    </label>
                  </div>
                )}
              </div>
            </div>
          ))}

          </div>
          {fieldErrors.lignes && <div className={styles.inlineError}><i className="ti ti-alert-circle" /> {fieldErrors.lignes}</div>}
          </FormSection>

          <FormSection icon="ti-calculator" title="Montants & options" description="Le résumé reste simple ; les ajustements fiscaux ou commerciaux avancés sont regroupés dans un seul bloc.">
          <div className={styles.totauxFacture}>
            <div className={styles.totauxLigne}><span>Total HT lignes</span><span>{montantLignesSaisies(lignes.reduce((s, l) => s + netLigne(l), 0), lignes, formatMAD)} MAD</span></div>

            <AdvancedSection title="Options commerciales & fiscales" icon="ti-adjustments-horizontal">
            {/* Transport */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', background: estProforma ? '#FFFBEB' : 'transparent', borderRadius: 6 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: estProforma ? '#854F0B' : 'var(--text-secondary)', flex: 1, cursor: 'pointer', padding: estProforma ? '0 8px' : 0 }}>
                <input type="checkbox" checked={estProforma} onChange={e => setEstProforma(e.target.checked)} />
                <span><strong>Proforma</strong> — sans valeur comptable, ne touche ni stock ni compta (numérotation PF)</span>
              </label>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', flex: 1, cursor: 'pointer' }}>
                <input type="checkbox" checked={avecTransport} onChange={e => setAvecTransport(e.target.checked)} />
                <i className="ti ti-truck" style={{ color: 'var(--blue)' }} />Frais de transport
              </label>
              {avecTransport && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <input type="number" min="0" step="0.01" placeholder="Montant HT"
                    value={transportHT} onChange={e => setTransportHT(e.target.value)}
                    style={{ width: 90, padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12, background: 'var(--bg-primary)' }} />
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>MAD HT</span>
                  <select value={transportMode} onChange={e => setTransportMode(e.target.value)}
                    title="Traitement TVA du transport"
                    style={{ padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                    <option value="accessoire">Accessoire — TVA des lignes</option>
                    <option value="distinct">Prestation distincte</option>
                  </select>
                  {transportMode === 'distinct' && <>
                    <select value={transportTVA} onChange={e => {
                      const taux = Number(e.target.value)
                      setTransportTVA(e.target.value)
                      setTransportQualification(qualificationParDefautPourTaux(taux, transportQualification))
                    }} style={{ padding: '3px 4px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                      {tauxTVAAvecHistorique(date, transportTVA).map(t => <option key={t} value={t}>{t}%</option>)}
                    </select>
                    {Number(transportTVA) === 0 && (
                      <select value={transportQualification} onChange={e => setTransportQualification(e.target.value)}
                        title="Qualification TVA du transport"
                        style={{ padding: '3px 4px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                        {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                      </select>
                    )}
                  </>}
                </div>
              )}
            </div>

            {/* Emballage */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', flex: 1, cursor: 'pointer' }}>
                <input type="checkbox" checked={avecEmballage} onChange={e => setAvecEmballage(e.target.checked)} />
                <i className="ti ti-package" style={{ color: 'var(--blue)' }} />Frais d'emballage
              </label>
              {avecEmballage && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <input type="number" min="0" step="0.01" placeholder="Montant HT"
                    value={emballageHT} onChange={e => setEmballageHT(e.target.value)}
                    style={{ width: 90, padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12, background: 'var(--bg-primary)' }} />
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>MAD</span>
                  <select value={emballageMode} onChange={e => setEmballageMode(e.target.value)}
                    title="Nature de l'emballage"
                    style={{ padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                    <option value="perdu">Perdu — TVA des lignes</option>
                    <option value="consigne">Consigné / récupérable</option>
                    <option value="vente_distincte">Vendu distinctement</option>
                  </select>
                  {emballageMode === 'vente_distincte' && <>
                    <select value={emballageTVA} onChange={e => {
                      const taux = Number(e.target.value)
                      setEmballageTVA(e.target.value)
                      setEmballageQualification(qualificationParDefautPourTaux(taux, emballageQualification))
                    }} style={{ padding: '3px 4px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                      {tauxTVAAvecHistorique(date, emballageTVA).map(t => <option key={t} value={t}>{t}%</option>)}
                    </select>
                    {Number(emballageTVA) === 0 && (
                      <select value={emballageQualification} onChange={e => setEmballageQualification(e.target.value)}
                        title="Qualification TVA de l'emballage"
                        style={{ padding: '3px 4px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                        {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                      </select>
                    )}
                  </>}
                  {emballageMode === 'consigne' && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Hors base TVA jusqu'à non-restitution.</span>}
                </div>
              )}
            </div>

            {/* Ristourne : réduction sur le volume d'affaires, en pied de facture */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>
                <i className="ti ti-discount-2" style={{ marginRight: 4, color: 'var(--green)' }} />
                Remise globale de pied
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <input type="number" min="0" max="100" step="0.1"
                  value={ristourne} onChange={e => setRistourne(e.target.value)}
                  style={{ width: 60, padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12, background: 'var(--bg-primary)' }} />
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>%</span>
              </div>
            </div>
            <div className={styles.totauxLigne}><span>Total HT</span><span>{montantLignesSaisies(totaux.ht, lignes, formatMAD)} MAD</span></div>
            <div className={styles.totauxLigne}><span>Total TVA</span><span>{montantLignesSaisies(totaux.tva, lignes, formatMAD)} MAD</span></div>
            {totaux.consigne > 0 && <div className={styles.totauxLigne}><span>Consigne emballage (hors TVA)</span><span>{montantLignesSaisies(totaux.consigne, lignes, formatMAD)} MAD</span></div>}
            {/* Escompte */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>
                <i className="ti ti-clock-bolt" style={{ marginRight: 4, color: 'var(--amber)' }} />Escompte de règlement
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <input type="number" min="0" max="100" step="0.1"
                  value={escompte} onChange={e => setEscompte(e.target.value)}
                  style={{ width: 60, padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12, background: 'var(--bg-primary)' }} />
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>%</span>
                {totaux.esc > 0 && <span style={{ fontSize: 11, color: 'var(--red)' }}>-{formatMAD(totaux.ttcBrut - totaux.ttc)} MAD</span>}
              </div>
            </div>
            {type === 'achat' && (
              <div style={{ padding: '8px 0', borderTop: '0.5px solid var(--border-light)', marginTop: 4 }}>
                <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 7 }}>
                  Qualification TVA de l’achat
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px', gap: 8 }}>
                  <select value={natureTVAAchat} onChange={e => {
                    setNatureTVAAchat(e.target.value)
                    if (e.target.value === 'non_deductible') setTvaDeductiblePct(0)
                    else if (Number(tvaDeductiblePct) === 0) setTvaDeductiblePct(100)
                  }}
                    style={{ padding: '6px 8px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                    <option value="charge">Charge / achat courant</option>
                    <option value="non_deductible">TVA non déductible</option>
                  </select>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-secondary)' }}>
                    Déductible
                    <input type="number" min="0" max="100" step="0.01" value={tvaDeductiblePct}
                      disabled={natureTVAAchat === 'non_deductible'}
                      onChange={e => setTvaDeductiblePct(e.target.value)}
                      style={{ width: 62, padding: '5px 6px', borderRadius: 5, border: '0.5px solid var(--border-medium)', textAlign: 'right', background: 'var(--bg-primary)' }} />
                    %
                  </label>
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 5 }}>
                  Cette qualification pilote la déclaration et l’écriture comptable. Les immobilisations se saisissent dans le module Immobilisations.
                </div>
              </div>
            )}
            {/* Retenue à la source */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>
                <i className="ti ti-receipt-tax" style={{ marginRight: 4, color: 'var(--blue)' }} />Retenue à la source (sur HT)
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <select value={rasTaux} onChange={e => setRasTaux(e.target.value)}
                  style={{ padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)' }}>
                  <option value="0">Aucune</option>
                  <option value="5">5% — prestations (personnes morales IS)</option>
                  <option value="10">10% — IR (avec justificatif)</option>
                  <option value="20">20% — IR (sans justificatif)</option>
                  <option value="15">15% — produits des actions</option>
                </select>
                {totaux.ras > 0 && <span style={{ fontSize: 11, color: 'var(--red)' }}>-{montantLignesSaisies(totaux.ras, lignes, formatMAD)} MAD</span>}
              </div>
            </div>
            </AdvancedSection>
            <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC net</span><span>{montantLignesSaisies(totaux.ttc, lignes, formatMAD)} MAD</span></div>
            {totaux.ras > 0 && (
              <div className={`${styles.totauxLigne} ${styles.totauxTTC}`} style={{ color: 'var(--blue)' }}>
                <span>NET ESTIMÉ APRÈS RAS (TTC − RAS)</span><span>{montantLignesSaisies(totaux.netAPayer, lignes, formatMAD)} MAD</span>
              </div>
            )}
          </div>

          {!estProforma && tiersSelectionne && (
            <div className={styles.comptaPreview}>
              <i className="ti ti-book-2" />
              <span>
                <strong>Aperçu comptable :</strong> tiers {type === 'vente' ? (tiersSelectionne.compte_client || '3421') : (tiersSelectionne.compte_fournisseur || '4411')}
                {' · '}comptes articles {Array.from(new Set(lignesActivesCompte(lignes, articles, type))).join(', ') || (type === 'vente' ? '7111' : '6111')}
                {' · '}TVA automatique
              </span>
            </div>
          )}

          {/* Validation / comptabilisation */}
          {!estProforma && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 650, color: 'var(--text-secondary)', marginBottom: 7 }}>Que souhaitez-vous faire ?</div>
              <div className="hp-choice-cards" style={{ gridTemplateColumns: 'repeat(2,minmax(0,1fr))' }}>
                <button type="button" className={`hp-choice-card ${!comptabiliser ? 'is-active' : ''}`} onClick={() => setComptabiliser(false)}>
                  <i className="ti ti-pencil" />
                  <span><strong style={{ display: 'block' }}>Enregistrer en brouillon</strong><small style={{ fontWeight: 400 }}>Modifiable, sans numéro définitif</small></span>
                </button>
                <button type="button" className={`hp-choice-card ${comptabiliser ? 'is-active' : ''}`} onClick={() => setComptabiliser(true)}>
                  <i className="ti ti-circle-check" />
                  <span><strong style={{ display: 'block' }}>{aComptabilite ? 'Valider & comptabiliser immédiatement' : 'Valider la facture'}</strong><small style={{ fontWeight: 400 }}>Numéro définitif et facture figée</small></span>
                </button>
              </div>
            </div>
          )}

          </FormSection>

          {erreur && (
            <div className={styles.erreurMsg}>
              <i className="ti ti-alert-circle" aria-hidden="true" /> {erreur}
            </div>
          )}

          <ActionBar hint={estProforma ? 'La proforma ne génère ni écriture ni mouvement de stock.' : (comptabiliser ? 'La validation attribue le numéro définitif et fige la pièce.' : 'Le brouillon reste entièrement modifiable.')}>
            <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
            <button className="hp-btn-primary" type="button" onClick={handleSave} disabled={!tiers.trim() || loading}>
              {loading ? 'Enregistrement...' : (
                <><i className="ti ti-device-floppy" />{estProforma ? ' Enregistrer la proforma' : (comptabiliser ? (aComptabilite ? ' Valider & comptabiliser' : ' Valider la facture') : ' Enregistrer le brouillon')}</>
              )}
            </button>
          </ActionBar>
        </div>
      )}
    </Modal>
  )
}

// ─── Détail facture ───────────────────────────────────────────────────────────
// ─── Mini formulaire règlement partiel ───────────────────────────────────────
function FormulaireReglementPartiel({ facture, totalRegle, soldeEffectif = null, onFermer, onSuccess }) {
  const [banques, setBanques] = useState([])
  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    fetch(API_BASE + '/api/banques', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : [])
      .then(setBanques)
      .catch(() => {})
  }, [])
  // Seule la situation serveur détermine le solde disponible ; inconnu reste inconnu.
  const solde = typeof soldeEffectif === 'number' && Number.isFinite(soldeEffectif) ? soldeEffectif : null
  const [form, setForm] = useState({
    montant: solde === null ? '' : solde.toFixed(2),
    mode: 'virement',
    date: dateLocaleISO(),
    reference: '',
    banque: '',
    date_echeance: '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  async function handleSave() {
    if (solde === null) { setErreur('Situation de paiement indisponible. Aucun règlement ne peut être enregistré.'); return }
    const montant = parseFloat(form.montant)
    if (!montant || montant <= 0) { setErreur('Le montant doit être positif'); return }
    if (montant > solde + 0.01) { setErreur(`Le montant dépasse le solde restant (${formatMAD(solde)} MAD)`); return }
    if (form.mode === 'effet' && !form.date_echeance) { setErreur("L'échéance est obligatoire pour un effet de commerce"); return }
    setLoading(true); setErreur('')
    try {
      const token = localStorage.getItem('hisabpro_token')
      const res = await fetch(API_BASE + '/api/reglements', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          facture_id: facture.id,
          tiers: facture.tiers,
          date: form.date,
          montant,
          mode: form.mode,
          reference: form.reference || null,
          banque: form.banque || null,
          ...(form.date_echeance && (form.mode === 'cheque' || form.mode === 'effet')
            ? { date_echeance: form.date_echeance } : {}),
        }),
      })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
      // Le règlement crée aussi une écriture dans le contexte comptable.
      // Attendre l'actualisation avant de fermer le formulaire : sinon le
      // journal reste sur son ancienne liste jusqu'au prochain F5.
      await onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  const MODES = ['virement', 'cheque', 'especes', 'effet', 'autre']
  const estSolde = parseFloat(form.montant) >= solde - 0.01

  return (
    <div style={{ background: 'var(--bg-secondary)', border: '0.5px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 13, fontWeight: 500 }}>
          <i className="ti ti-coin" style={{ marginRight: 6, color: 'var(--green)' }} />
          Enregistrer un règlement
        </span>
        <button onClick={onFermer} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16 }}>✕</button>
      </div>

      {/* Solde restant */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, background: 'var(--bg-primary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-light)' }}>
        <span style={{ color: 'var(--text-secondary)' }}>Total TTC</span>
        <span style={{ fontWeight: 500 }}>{formatMAD(facture.total_ttc)} MAD</span>
      </div>
      {totalRegle > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, background: 'var(--bg-primary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '0.5px solid var(--border-light)' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Déjà réglé</span>
          <span style={{ color: 'var(--green)', fontWeight: 500 }}>— {formatMAD(totalRegle)} MAD</span>
        </div>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600, background: solde <= 0.01 ? '#EAF3DE' : '#FFFBF0', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: `0.5px solid ${solde <= 0.01 ? '#A7D87A' : '#FCD34D'}` }}>
        <span>Solde restant</span>
        <span style={{ color: solde !== null && solde <= 0.01 ? 'var(--green)' : 'var(--amber)' }}>{solde === null ? 'À vérifier' : `${formatMAD(Math.max(0, solde))} MAD`}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>Montant *</label>
          <input className={styles.input} type="number" min="0" step="0.01"
            value={form.montant} onChange={e => setForm(p => ({ ...p, montant: e.target.value }))} />
          {estSolde && <span style={{ fontSize: 10, color: 'var(--green)' }}>✓ Solde intégral</span>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>Date *</label>
          <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>Mode</label>
          <select className={styles.input} value={form.mode} onChange={e => setForm(p => ({ ...p, mode: e.target.value }))}>
            {MODES.map(m => <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>Référence</label>
          <input className={styles.input} type="text" placeholder="N° chèque, virement..."
            value={form.reference} onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} />
        </div>
        {['virement', 'cheque', 'effet'].includes(form.mode) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>Banque</label>
            {banques.length > 0 ? (
              <select className={styles.input} value={form.banque}
                onChange={e => setForm(p => ({ ...p, banque: e.target.value }))}>
                <option value="">— Choisir une banque —</option>
                {banques.map(b => (
                  <option key={b.id} value={b.banque}>{b.banque}{b.agence ? ` — ${b.agence}` : ''}</option>
                ))}
              </select>
            ) : (
              <input className={styles.input} type="text" placeholder="Nom de la banque..."
                value={form.banque} onChange={e => setForm(p => ({ ...p, banque: e.target.value }))} />
            )}
          </div>
        )}
        {(form.mode === 'cheque' || form.mode === 'effet') && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>
              Échéance {form.mode === 'effet' ? '*' : '(chèque postdaté)'}
            </label>
            <input className={styles.input} type="date" value={form.date_echeance}
              onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
          </div>
        )}
      </div>

      {(form.mode === 'cheque' || form.mode === 'effet') && facture.type !== 'achat' && (
        <div style={{ fontSize: 11, color: '#854F0B', background: '#FFFBEB', padding: '8px 12px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <i className="ti ti-wallet" />
          Ce {form.mode === 'cheque' ? 'chèque' : 'effet'} entrera en <strong>portefeuille</strong> : gère sa remise en banque,
          son encaissement ou son rejet depuis la page Effets &amp; Chèques.
        </div>
      )}

      {erreur && <div className={styles.erreurMsg}><i className="ti ti-alert-circle" /> {erreur}</div>}

      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
        <button className={styles.btnPrim} onClick={handleSave} disabled={solde === null || !form.montant || loading}
          style={{ background: 'var(--green)', borderColor: 'var(--green)' }}>
          <i className="ti ti-check" /> {loading ? '...' : 'Enregistrer'}
        </button>
      </div>
    </div>
  )
}


// ─── Formulaire création Avoir depuis une facture ─────────────────────────────
export function FormulaireAvoir({ facture, avoirsExistants, onFermer, onSuccess, quantitesRetour = null, motifDefaut = '' }) {
  // FACT-G : quantités physiques et corrections financières sont traitées séparément.
  const dejaAvoire = {}
  avoirsExistants.filter(a => a.statut !== 'annule').forEach(a => {
    (a.lignes || []).forEach(l => {
      if ((l.mode_calcul || 'quantite') !== 'quantite') return
      const key = l.facture_ligne_id ? `id:${l.facture_ligne_id}` : `desc:${l.description}`
      dejaAvoire[key] = (dejaAvoire[key] || 0) + Number(l.quantite || 0)
    })
  })

  const [motif, setMotif] = useState(motifDefaut)
  const [date, setDate] = useState(dateLocaleISO())
  const [notes, setNotes] = useState('')
  const [natureAvoir, setNatureAvoir] = useState('retour_annulation')
  const [modeRrr, setModeRrr] = useState('rrr_pourcentage')
  const [retourStock, setRetourStock] = useState(Boolean(quantitesRetour))
  const [lignes, setLignes] = useState(
    (facture.lignes || []).map(l => {
      const keyId = `id:${l.id}`
      const keyDesc = `desc:${l.description}`
      const deja = dejaAvoire[keyId] ?? dejaAvoire[keyDesc] ?? 0
      const dispoRetour = Math.max(0, Number(l.quantite || 0) - deja)
      const quantiteRetour = quantitesRetour ? Number(quantitesRetour[l.id] ?? quantitesRetour[l.description] ?? 0) : 0
      const quantiteInitiale = quantitesRetour ? Math.min(dispoRetour, quantiteRetour) : 0
      return {
        facture_ligne_id: l.id,
        article_id: l.article_id || null,
        description: l.description,
        quantite_facturee: Number(l.quantite || 0),
        quantite_deja_avoiree: deja,
        quantite_max_retour: dispoRetour,
        quantite: quantiteInitiale,
        prix_unitaire: Number(l.prix_unitaire || 0),
        tva: Number(l.tva || 0),
        qualification_tva: l.qualification_tva || (Number(l.tva) === 0 ? 'exonere_sans_deduction' : 'taxable'),
        remise: Number(l.remise || 0), remise2: Number(l.remise2 || 0), rabais: Number(l.rabais || 0),
        taux_rrr: '', montant_ht_avoir: '', nouveau_prix_unitaire: '',
        selectionnee: quantiteInitiale > 0,
      }
    })
  )
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  function majLigne(i, patch) {
    setLignes(prev => prev.map((l, idx) => idx === i ? { ...l, ...patch } : l))
  }
  function toggleLigne(i) {
    setLignes(prev => prev.map((l, idx) => idx === i ? { ...l, selectionnee: !l.selectionnee } : l))
  }

  function maxQuantite(l) {
    return natureAvoir === 'retour_annulation' ? l.quantite_max_retour : l.quantite_facturee
  }

  function baseFinaleSource(l, q) {
    let net = q * l.prix_unitaire
    net *= 1 - l.remise / 100
    net *= 1 - l.remise2 / 100
    net -= l.rabais * q
    net = Math.max(0, net)
    net *= 1 - (Number(facture.remise_globale || 0) / 100)
    net *= 1 - (Number(facture.ristourne || 0) / 100)
    net *= 1 - (Number(facture.escompte || 0) / 100)
    return Math.max(0, net)
  }

  function montantFinalLigne(l) {
    if (!l.selectionnee) return 0
    const q = Number(l.quantite || 0)
    if (!(q > 0)) return 0
    if (natureAvoir === 'retour_annulation') return baseFinaleSource(l, q)
    if (natureAvoir === 'rrr') {
      return modeRrr === 'rrr_pourcentage'
        ? baseFinaleSource(l, q) * (Number(l.taux_rrr || 0) / 100)
        : Math.max(0, Number(l.montant_ht_avoir || 0))
    }
    if (natureAvoir === 'correction_prix') {
      const nouveau = Number(l.nouveau_prix_unitaire)
      if (!Number.isFinite(nouveau) || nouveau < 0 || nouveau >= l.prix_unitaire) return 0
      let delta = (l.prix_unitaire - nouveau) * q
      delta *= 1 - l.remise / 100
      delta *= 1 - l.remise2 / 100
      delta *= 1 - (Number(facture.remise_globale || 0) / 100)
      delta *= 1 - (Number(facture.ristourne || 0) / 100)
      delta *= 1 - (Number(facture.escompte || 0) / 100)
      return Math.max(0, delta)
    }
    return Math.max(0, Number(l.montant_ht_avoir || 0))
  }

  const lignesActives = lignes.filter(l => l.selectionnee && Number(l.quantite || 0) > 0)
  const totaux = useMemo(() => {
    let ht = 0, tva = 0, ttc = 0
    lignes.filter(l => l.selectionnee).forEach(l => {
      const base = montantFinalLigne(l)
      const ltva = base * (tvaEffective(l) / 100)
      ht += base; tva += ltva; ttc += base + ltva
    })
    return { ht, tva, ttc }
  }, [lignes, natureAvoir, modeRrr, facture.remise_globale, facture.ristourne, facture.escompte])

  function changerNature(value) {
    setNatureAvoir(value)
    if (value !== 'retour_annulation') setRetourStock(false)
    setErreur('')
  }

  async function handleSave() {
    if (!date) { setErreur("La date de l'avoir est obligatoire."); return }
    if (lignesActives.length === 0) { setErreur('Sélectionnez au moins une ligne et une quantité concernée.'); return }
    for (const l of lignesActives) {
      const q = Number(l.quantite || 0)
      if (q > maxQuantite(l) + 0.000001) { setErreur(`La quantité dépasse le maximum autorisé pour « ${l.description} ».`); return }
      if (natureAvoir === 'rrr' && modeRrr === 'rrr_pourcentage' && (!(Number(l.taux_rrr) > 0) || Number(l.taux_rrr) > 100)) {
        setErreur(`Renseignez un pourcentage de RRR entre 0 et 100 % pour « ${l.description} ».`); return
      }
      if ((natureAvoir === 'rrr' && modeRrr === 'rrr_montant') || natureAvoir === 'autre') {
        if (!(Number(l.montant_ht_avoir) > 0)) { setErreur(`Renseignez un montant HT positif pour « ${l.description} ».`); return }
      }
      if (natureAvoir === 'correction_prix') {
        const np = Number(l.nouveau_prix_unitaire)
        if (!Number.isFinite(np) || np < 0 || np >= l.prix_unitaire) { setErreur(`Le nouveau prix de « ${l.description} » doit être inférieur au prix facturé.`); return }
      }
    }
    setLoading(true); setErreur('')
    try {
      const token = localStorage.getItem('hisabpro_token')
      const res = await fetch(API_BASE + '/api/avoirs', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          facture_id: facture.id, date, motif: motif || null, notes: notes || null,
          nature_avoir: natureAvoir, retour_stock: natureAvoir === 'retour_annulation' && retourStock,
          lignes: lignesActives.map(l => ({
            facture_ligne_id: l.facture_ligne_id,
            quantite: Number(l.quantite),
            mode_calcul: natureAvoir === 'rrr' ? modeRrr : natureAvoir === 'correction_prix' ? 'correction_prix' : natureAvoir === 'autre' ? 'autre_montant' : 'quantite',
            taux_rrr: natureAvoir === 'rrr' && modeRrr === 'rrr_pourcentage' ? Number(l.taux_rrr) : null,
            montant_ht_avoir: ((natureAvoir === 'rrr' && modeRrr === 'rrr_montant') || natureAvoir === 'autre') ? Number(l.montant_ht_avoir) : null,
            nouveau_prix_unitaire: natureAvoir === 'correction_prix' ? Number(l.nouveau_prix_unitaire) : null,
          })),
        }),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Erreur') }
      onSuccess(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  const colonneValeur = natureAvoir === 'rrr'
    ? (modeRrr === 'rrr_pourcentage' ? 'RRR %' : 'Montant HT')
    : natureAvoir === 'correction_prix' ? 'Nouveau prix' : natureAvoir === 'autre' ? 'Montant HT' : null

  return (
    <Modal titre={`Créer un avoir — ${facture.numero}`} icone="ti-receipt-refund" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>
        <div className={styles.sourceInfo}><i className="ti ti-link" /> Facture d'origine <strong>{facture.numero}</strong> — {facture.tiers}</div>
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}><label className={styles.label}>Date de l'avoir *</label><input className={styles.input} type="date" value={date} onChange={e => setDate(e.target.value)} /></div>
          <div className={styles.formGroup}><label className={styles.label}>Motif</label><input className={styles.input} placeholder="Retour marchandise, remise après facture..." value={motif} onChange={e => setMotif(e.target.value)} /></div>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>Nature de l'avoir</label>
          <select className={styles.input} value={natureAvoir} onChange={e => changerNature(e.target.value)}>
            <option value="retour_annulation">Retour / annulation de vente ou d'achat</option>
            <option value="rrr">Rabais, remise ou ristourne après facture</option>
            <option value="correction_prix">Correction de prix</option>
            <option value="autre">Autre avoir financier</option>
          </select>
          <span className="hp-field__hint">Chaque nature applique désormais son vrai calcul. Les RRR et corrections de prix ne créent aucun mouvement de stock.</span>
        </div>

        {natureAvoir === 'rrr' && <div className={styles.formGroup}>
          <label className={styles.label}>Calcul du RRR</label>
          <select className={styles.input} value={modeRrr} onChange={e => setModeRrr(e.target.value)}>
            <option value="rrr_pourcentage">Pourcentage sur la base HT nette concernée</option>
            <option value="rrr_montant">Montant HT fixe</option>
          </select>
        </div>}

        {natureAvoir === 'retour_annulation' && <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, padding: '9px 11px', borderRadius: 6, background: 'var(--bg-secondary)' }}>
          <input type="checkbox" checked={retourStock} onChange={e => setRetourStock(e.target.checked)} />
          <span><strong>Retour physique de marchandise</strong> — appliquer le mouvement inverse au stock lors de la comptabilisation.</span>
        </label>}

        <div className={`${styles.lignesTable} hp-line-editor`}>
          <table className={styles.tableLignes}>
            <thead><tr>
              <th style={{ width: 32 }} /><th>Article</th><th style={{ textAlign: 'center' }}>Qté facturée</th>
              <th style={{ textAlign: 'center' }}>Qté concernée</th>{colonneValeur && <th style={{ textAlign: 'center' }}>{colonneValeur}</th>}
              <th style={{ textAlign: 'right' }}>Avoir HT net</th>
            </tr></thead>
            <tbody>{lignes.map((l, i) => {
              const max = maxQuantite(l)
              return <tr key={l.facture_ligne_id || i} style={{ opacity: max <= 0 && natureAvoir === 'retour_annulation' ? 0.4 : 1 }}>
                <td data-label="Sélection" style={{ textAlign: 'center' }}><input type="checkbox" checked={l.selectionnee} disabled={max <= 0} onChange={() => toggleLigne(i)} /></td>
                <td data-label="Article" style={{ padding: '6px 8px', fontSize: 13 }}>{l.description}<div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{formatMAD(l.prix_unitaire)} MAD / unité</div></td>
                <td data-label="Quantité facturée" style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-secondary)' }}>{l.quantite_facturee}{natureAvoir === 'retour_annulation' && l.quantite_deja_avoiree > 0 && <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{l.quantite_deja_avoiree} déjà retournée/créditée</div>}</td>
                <td data-label="Quantité concernée"><input className={styles.inputLigne} type="number" min="0" max={max} step="0.01" value={l.quantite} disabled={!l.selectionnee} onChange={e => majLigne(i, { quantite: e.target.value })} style={{ textAlign: 'center', fontWeight: 600 }} /></td>
                {natureAvoir === 'rrr' && modeRrr === 'rrr_pourcentage' && <td data-label="RRR %"><input className={styles.inputLigne} type="number" min="0.01" max="100" step="0.01" placeholder="%" value={l.taux_rrr} disabled={!l.selectionnee} onChange={e => majLigne(i, { taux_rrr: e.target.value })} style={{ textAlign: 'center' }} /></td>}
                {natureAvoir === 'rrr' && modeRrr === 'rrr_montant' && <td data-label="Montant HT"><input className={styles.inputLigne} type="number" min="0.01" step="0.01" placeholder="MAD HT" value={l.montant_ht_avoir} disabled={!l.selectionnee} onChange={e => majLigne(i, { montant_ht_avoir: e.target.value })} style={{ textAlign: 'center' }} /></td>}
                {natureAvoir === 'correction_prix' && <td data-label="Nouveau prix"><input className={styles.inputLigne} type="number" min="0" max={Math.max(0, l.prix_unitaire - 0.01)} step="0.01" placeholder="Nouveau PU" value={l.nouveau_prix_unitaire} disabled={!l.selectionnee} onChange={e => majLigne(i, { nouveau_prix_unitaire: e.target.value })} style={{ textAlign: 'center' }} /></td>}
                {natureAvoir === 'autre' && <td data-label="Montant HT"><input className={styles.inputLigne} type="number" min="0.01" step="0.01" placeholder="MAD HT" value={l.montant_ht_avoir} disabled={!l.selectionnee} onChange={e => majLigne(i, { montant_ht_avoir: e.target.value })} style={{ textAlign: 'center' }} /></td>}
                <td data-label="Avoir HT net" style={{ textAlign: 'right', fontSize: 12, fontWeight: 600 }}>{l.selectionnee ? `${formatMAD(montantFinalLigne(l))} MAD` : '—'}</td>
              </tr>
            })}</tbody>
          </table>
        </div>

        <div className={styles.formGroup}><label className={styles.label}>Notes</label><textarea className={styles.textarea} rows={2} value={notes} onChange={e => setNotes(e.target.value)} /></div>
        <div className={styles.totauxFacture}>
          <div className={styles.totauxLigne}><span>Total HT net à créditer</span><span>{formatMAD(totaux.ht)} MAD</span></div>
          <div className={styles.totauxLigne}><span>Total TVA</span><span>{formatMAD(totaux.tva)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total avoir TTC</span><span>{formatMAD(totaux.ttc)} MAD</span></div>
        </div>
        {erreur && <div className={styles.erreurMsg}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={loading || lignesActives.length === 0 || !(totaux.ttc > 0)} style={{ background: 'var(--red)', borderColor: 'var(--red)' }}>
            <i className="ti ti-receipt-refund" /> {loading ? 'Enregistrement...' : `Créer l'avoir (${formatMAD(totaux.ttc)} MAD)`}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Détail facture ───────────────────────────────────────────────────────────
// Les bons de réception sont aussi stockés dans la table des bons de livraison.
// La traçabilité de la facture ne doit pas afficher un même BR comme un BL.
function construireTracabiliteFacture(facture, bcs, bls, brs) {
  const idFacture = Number(facture.id)
  const estLie = document => Number(document.facture_id) === idFacture
  const livraisons = (Array.isArray(bls) ? bls : []).filter(bl => bl.type === 'vente')
  const receptions = (Array.isArray(brs) ? brs : []).filter(br => br.type === 'achat')
  const blDirects = livraisons.filter(estLie)
  const brDirects = receptions.filter(estLie)
  const commandes = Array.isArray(bcs) ? bcs : []
  const bcDirect = commandes.find(estLie)
  const idsBcSources = [...blDirects, ...brDirects]
    .map(doc => Number(doc.bon_commande_id))
    .filter(id => Number.isFinite(id) && id > 0)
  const bcLie = bcDirect || commandes.find(bc => idsBcSources.includes(Number(bc.id))) || null
  // Une facture directement issue du BC peut ne pas encore avoir de BL/BR lié.
  const blLies = bcDirect
    ? livraisons.filter(bl => estLie(bl) || Number(bl.bon_commande_id) === Number(bcDirect.id))
    : blDirects
  const brLies = bcDirect
    ? receptions.filter(br => estLie(br) || Number(br.bon_commande_id) === Number(bcDirect.id))
    : brDirects
  return { bc: bcLie, bls: blLies, brs: brLies }
}

function DetailFacture({ facture, onFermer, onStatutChange }) {
  const peutModifier = peutEcrire()
  const { mettreAJourFacture } = useFactures()
  const [loading, setLoading] = useState(false)
  const [loadingPdf, setLoadingPdf] = useState(false)
  const [showReglement, setShowReglement] = useState(false)
  const [reglements, setReglements] = useState([])
  const [soldeApiDetail, setSoldeApiDetail] = useState(null)
  const [situationDetail, setSituationDetail] = useState(null)
  const [erreurSituationDetail, setErreurSituationDetail] = useState('')
  const [tracabilite, setTracabilite] = useState(null)
  const [avoirs, setAvoirs] = useState([])
  const [showAvoir, setShowAvoir] = useState(false)
  const [echeancierDetail, setEcheancierDetail] = useState(null)

  // Charger les règlements existants de cette facture + le solde effectif
  // (endpoint enrichi : déduit règlements, avoirs actifs et acomptes imputés)
  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    const annee = new Date(facture.date).getFullYear()
    let annule = false
    setSoldeApiDetail(null); setSituationDetail(null); setErreurSituationDetail('')
    fetch(`${API_BASE}/api/reglements?exercice=${annee}&facture_id=${facture.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setReglements)
      .catch(() => {})
    fetch(`${API_BASE}/api/factures/${facture.id}/reglements`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(lireSituationReglement)
      .then(data => {
        if (annule) return
        setSituationDetail(data)
        setSoldeApiDetail(typeof data.solde_restant === 'number' && Number.isFinite(data.solde_restant) ? data.solde_restant : null)
      })
      .catch(e => { if (!annule) setErreurSituationDetail(e.message) })
    fetch(`${API_BASE}/api/factures/${facture.id}/echeancier`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(setEcheancierDetail)
      .catch(() => setEcheancierDetail(null))
    return () => { annule = true }
  }, [facture.id])

  // Charger la traçabilité (BC, BL, BR liés)
  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    const annee = new Date(facture.date).getFullYear()
    Promise.all([
      fetch(`${API_BASE}/api/bons-commande?exercice=${annee}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
      fetch(`${API_BASE}/api/bons-livraison?exercice=${annee}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
      fetch(`${API_BASE}/api/bons-reception?exercice=${annee}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
    ]).then(([bcs, bls, brs]) => {
      setTracabilite(construireTracabiliteFacture(facture, bcs, bls, brs))
    })
  }, [facture.id])

  // Charger les avoirs déjà émis sur cette facture
  function chargerAvoirs() {
    const token = localStorage.getItem('hisabpro_token')
    const annee = new Date(facture.date).getFullYear()
    fetch(`${API_BASE}/api/avoirs?exercice=${annee}&facture_id=${facture.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(r => r.json()).then(setAvoirs).catch(() => setAvoirs([]))
  }
  useEffect(() => { chargerAvoirs() }, [facture.id])

  const totalRegle = reglements.filter(r => !['rejete', 'annule'].includes(r.statut)).reduce((s, r) => s + r.montant, 0)
  const soldeRestant = soldeApiDetail
  const estSolde = soldeRestant !== null && soldeRestant <= 0.01

  async function telechargerPDF() {
    setLoadingPdf(true)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const res = await fetch(`${API_BASE}/api/factures/${facture.id}/pdf`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Erreur PDF')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `facture_${facture.numero}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
    finally { setLoadingPdf(false) }
  }

  return (
    <Modal titre={facture.numero ? `Facture ${facture.numero}` : `Brouillon #${facture.id}`} icone="ti-file-text" onFermer={onFermer} largeur="md">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className={styles.detailMeta}>
          <div><span className={styles.metaLabel}>Type</span><BadgeType type={facture.type} /></div>
          <div><span className={styles.metaLabel}>Date</span><span>{formatDate(facture.date)}</span></div>
          <div><span className={styles.metaLabel}>Tiers</span><strong>{facture.tiers}</strong></div>
          <div><span className={styles.metaLabel}>{facture.type === 'achat' ? 'N° fournisseur' : 'Réf.'}</span><span>{facture.reference || (facture.type === 'achat' && !facture.est_validee ? 'À renseigner avant validation' : '—')}</span></div>
          <div><span className={styles.metaLabel}>Validation</span><span>{facture.est_validee ? 'Validée' : 'Brouillon'}</span></div>
          <div>
            <span className={styles.metaLabel}>Paiement</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <BadgeStatut facture={facture} />
              {facture.statut_credit && facture.statut_credit !== 'aucun' && (
                <span style={{
                  fontSize: 10, padding: '2px 7px', borderRadius: 100,
                  background: facture.statut_credit === 'totalement_creditee' ? '#FCEBEB' : '#FAEEDA',
                  color: facture.statut_credit === 'totalement_creditee' ? '#A32D2D' : '#854F0B',
                  whiteSpace: 'nowrap',
                }}>
                  {facture.statut_credit === 'totalement_creditee' ? 'Totalement créditée' : 'Partiellement créditée'}
                </span>
              )}
            </div>
          </div>
          <div><span className={styles.metaLabel}>Comptabilité</span><span>{facture.est_comptabilisee ? 'Comptabilisée' : 'À comptabiliser'}</span></div>
          <div>
            <span className={styles.metaLabel}>Échéance</span>
            <BadgeEcheance facture={facture} />
          </div>
        </div>

        {echeancierDetail?.echeances?.length > 1 && (
          <div className={styles.detailEcheancier}>
            <div className={styles.detailEcheancierTitle}>
              <span><i className="ti ti-calendar-dollar" /> Échéancier de paiement</span>
              <small>{echeancierDetail.nb_ouvertes} échéance{echeancierDetail.nb_ouvertes > 1 ? 's' : ''} ouverte{echeancierDetail.nb_ouvertes > 1 ? 's' : ''}</small>
            </div>
            <div className={styles.detailEcheancierRows}>
              {echeancierDetail.echeances.map(e => (
                <div className={styles.detailEcheancierRow} key={e.id || e.ordre}>
                  <span>{e.ordre}</span>
                  <div><strong>{formatDate(e.date_echeance)}</strong><small>{e.libelle || `Échéance ${e.ordre}`}</small></div>
                  <div><strong>{formatMAD(e.montant)} MAD</strong><small>{formatMAD(e.reste_du)} MAD restant</small></div>
                  <span className={`${styles.echeanceMiniBadge} ${e.jours_retard > 0 ? styles.echeanceMiniRetard : ''}`}>{e.reste_du <= 0.01 ? 'Réglée' : e.jours_retard > 0 ? `${e.jours_retard} j retard` : 'À venir'}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Traçabilité — documents liés */}
        {tracabilite && (tracabilite.bc || tracabilite.bls.length > 0 || tracabilite.brs.length > 0 || avoirs.length > 0) && (
          <div style={{
            background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)',
            padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 6,
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
              <i className="ti ti-git-branch" style={{ fontSize: 12 }} /> Documents liés
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
              {tracabilite.bc && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 100,
                    background: '#EEEDFE', color: '#534AB7', display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <i className="ti ti-clipboard-list" style={{ fontSize: 11 }} />
                    BC {tracabilite.bc.numero}
                    <span style={{ opacity: 0.6, fontSize: 10 }}>· {tracabilite.bc.tiers}</span>
                  </span>
                  <i className="ti ti-arrow-right" style={{ fontSize: 10, color: 'var(--text-tertiary)' }} />
                </div>
              )}
              {tracabilite.bls.map(bl => (
                <div key={bl.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <i className="ti ti-arrow-right" style={{ fontSize: 10, color: 'var(--text-tertiary)' }} />
                  <span style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 100,
                    background: '#EAF3DE', color: '#3B6D11', display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <i className="ti ti-truck" style={{ fontSize: 11 }} />
                    BL {bl.numero}
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: bl.statut === 'livre' ? '#D1FAE5' : '#FEF3C7',
                      color: bl.statut === 'livre' ? '#065F46' : '#92400E',
                    }}>
                      {bl.statut === 'livre' ? 'Livré' : bl.statut === 'expedie' ? 'Expédié' : 'En préparation'}
                    </span>
                  </span>
                </div>
              ))}
              {tracabilite.brs.map(br => (
                <div key={br.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <i className="ti ti-arrow-right" style={{ fontSize: 10, color: 'var(--text-tertiary)' }} />
                  <span style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 100,
                    background: '#F5F3FF', color: '#7C3AED', display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <i className="ti ti-package-import" style={{ fontSize: 11 }} />
                    BR {br.numero}
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: br.statut === 'livre' ? '#D1FAE5' : '#FEF3C7',
                      color: br.statut === 'livre' ? '#065F46' : '#92400E',
                    }}>
                      {br.statut === 'livre' ? 'Réceptionné' : 'En cours'}
                    </span>
                  </span>
                </div>
              ))}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <i className="ti ti-arrow-right" style={{ fontSize: 10, color: 'var(--text-tertiary)' }} />
                <span style={{
                  fontSize: 11, padding: '3px 10px', borderRadius: 100,
                  background: 'var(--blue-light)', color: 'var(--blue)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5,
                }}>
                  <i className="ti ti-file-invoice" style={{ fontSize: 11 }} />
                  {facture.numero || `Brouillon #${facture.id}`} ← ici
                </span>
              </div>
              {avoirs.map(av => (
                <div key={av.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <i className="ti ti-arrow-right" style={{ fontSize: 10, color: 'var(--text-tertiary)' }} />
                  <span style={{
                    fontSize: 11, padding: '3px 10px', borderRadius: 100,
                    background: '#FCEBEB', color: '#A32D2D', display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <i className="ti ti-receipt-refund" style={{ fontSize: 11 }} />
                    {av.numero}
                    <span style={{ opacity: 0.7, fontSize: 10 }}>· {formatMAD(av.total_ttc)} MAD</span>
                    <span style={{
                      fontSize: 9, padding: '1px 5px', borderRadius: 3,
                      background: av.statut === 'rembourse' ? '#D1FAE5' : av.statut === 'annule' ? '#F3F4F6' : '#FEF3C7',
                      color: av.statut === 'rembourse' ? '#065F46' : av.statut === 'annule' ? '#6B7280' : '#92400E',
                    }}>
                      {av.statut === 'emis' ? 'Émis' : av.statut === 'utilise' ? 'Utilisé' : av.statut === 'rembourse' ? 'Remboursé' : 'Annulé'}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 066 : la consultation est une liste de fiches, pas un tableau à 5
            colonnes qui déborde de la modale de 700 px. Toutes les valeurs restent visibles. */}
        <div className={styles.detailLignes} role="list" aria-label="Lignes de la facture">
          {(facture.lignes || []).map((l, i) => (
            <div className={styles.detailLigne} role="listitem" key={l.id ?? i}>
              <div className={`${styles.detailLigneChamp} ${styles.detailLigneDescription}`}>
                <span className={styles.detailLigneLabel}>Description</span>
                <strong className={styles.detailLigneValeur}>{l.description}</strong>
              </div>
              <div className={styles.detailLigneChamp}>
                <span className={styles.detailLigneLabel}>Quantité</span>
                <span className={styles.detailLigneValeur}>{l.quantite}</span>
              </div>
              <div className={styles.detailLigneChamp}>
                <span className={styles.detailLigneLabel}>Prix unitaire HT</span>
                <span className={styles.detailLigneValeur}>{formatMAD(l.prix_unitaire)} MAD</span>
              </div>
              <div className={styles.detailLigneChamp}>
                <span className={styles.detailLigneLabel}>TVA</span>
                <span className={styles.detailLigneValeur}>{l.tva}%</span>
              </div>
              <div className={styles.detailLigneChamp}>
                <span className={styles.detailLigneLabel}>Montant HT</span>
                <strong className={styles.detailLigneValeur}>{formatMAD(l.montant_ht)} MAD</strong>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.totauxFacture}>
          {(facture.frais_transport_ht > 0 || facture.frais_emballage_ht > 0) && (
            <>
              <div className={styles.totauxLigne}>
                <span>Total HT lignes</span>
                <span>{formatMAD(facture.total_ht - (facture.frais_transport_ht || 0) - (facture.frais_emballage_ht || 0))} MAD</span>
              </div>
              {facture.frais_transport_ht > 0 && (
                <div className={styles.totauxLigne}>
                  <span><i className="ti ti-truck" style={{ marginRight: 4, color: 'var(--blue)' }} />Frais de transport ({facture.frais_transport_tva}% TVA)</span>
                  <span>{formatMAD(facture.frais_transport_ht)} MAD</span>
                </div>
              )}
              {facture.frais_emballage_ht > 0 && (
                <div className={styles.totauxLigne}>
                  <span><i className="ti ti-package" style={{ marginRight: 4, color: 'var(--blue)' }} />Frais d'emballage ({facture.frais_emballage_tva}% TVA)</span>
                  <span>{formatMAD(facture.frais_emballage_ht)} MAD</span>
                </div>
              )}
            </>
          )}
          <div className={styles.totauxLigne}><span>Total HT</span><span>{formatMAD(facture.total_ht)} MAD</span></div>
          <div className={styles.totauxLigne}><span>Total TVA</span><span>{formatMAD(facture.total_tva)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC</span><span>{formatMAD(facture.total_ttc)} MAD</span></div>
          {facture.ras_anomalie && <p role="alert" style={{ color: 'var(--red)', fontSize: 12 }}>{facture.ras_anomalie} Retenue et net à payer indisponibles jusqu’à vérification.</p>}
          {(facture.montant_ras || 0) > 0 && (
            <>
              <div className={styles.totauxLigne}>
                <span><i className="ti ti-receipt-tax" style={{ marginRight: 4, color: 'var(--blue)' }} />RAS estimée ({facture.ras_taux}% du HT)</span>
                <span style={{ color: 'var(--red)' }}>-{formatMAD(facture.montant_ras)} MAD</span>
              </div>
              <div className={`${styles.totauxLigne} ${styles.totauxTTC}`} style={{ color: 'var(--blue)' }}>
                <span>NET ESTIMÉ APRÈS RAS</span><span>{formatMAD(facture.net_a_payer)} MAD</span>
              </div>
            </>
          )}
        </div>

        <ResumeRASSituation situation={situationDetail} />
        {erreurSituationDetail && <InlineNotice tone="danger">{erreurSituationDetail}</InlineNotice>}
        <FactureLiee facture={facture} />

        {/* Règlements existants */}
        {reglements.length > 0 && (
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>Règlements enregistrés</div>
            {reglements.map((r, i) => {
              const estRejete = r.statut === 'rejete'
              const estAnnule = r.statut === 'annule'
              const estInactif = estRejete || estAnnule
              const enCours = ['portefeuille', 'encaissement', 'a_payer'].includes(r.statut)
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, padding: '4px 0', borderBottom: i < reglements.length - 1 ? '0.5px solid var(--border-light)' : 'none' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{r.date} — {r.mode}{r.reference ? ` ${r.reference}` : ''}</span>
                  {estInactif && (
                    <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: '#FCEBEB', color: '#A32D2D', fontWeight: 600 }}>
                      {estAnnule ? 'ANNULÉ — contrepassé' : 'REJETÉ — non compté'}
                    </span>
                  )}
                  {enCours && (
                    <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: '#FAEEDA', color: '#854F0B', fontWeight: 600 }}>
                      {r.statut === 'portefeuille' ? 'En portefeuille' : r.statut === 'encaissement' ? "À l'encaissement" : 'À payer'}
                    </span>
                  )}
                  <span style={{ marginLeft: 'auto', fontWeight: 500,
                    textDecoration: estInactif ? 'line-through' : 'none',
                    color: estInactif ? 'var(--text-tertiary)' : 'var(--green)' }}>
                    {formatMAD(r.montant)} MAD
                  </span>
                </div>
              )
            })}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600, marginTop: 8, paddingTop: 8, borderTop: '0.5px solid var(--border-medium)' }}>
              <span>Solde restant</span>
              <span style={{ color: estSolde ? 'var(--green)' : 'var(--amber)' }}>{soldeRestant === null ? 'À vérifier' : `${formatMAD(Math.max(0, soldeRestant))} MAD`}</span>
            </div>
          </div>
        )}

        {/* Formulaire règlement partiel */}
        {peutModifier && showReglement ? (
          <FormulaireReglementPartiel
            facture={facture}
            totalRegle={totalRegle}
            soldeEffectif={soldeRestant}
            onFermer={() => setShowReglement(false)}
            onSuccess={async () => {
              setShowReglement(false)
              // Le parent recharge la facture et le journal, puis ferme le détail.
              await onStatutChange?.()
            }}
          />
        ) : (
          <>
            {peutModifier && !estSolde && (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 5 }}>
                <i className="ti ti-info-circle" />
                Utilisez l'icône <i className="ti ti-cash" style={{ color: 'var(--green)', margin: '0 3px' }} /> dans la liste pour enregistrer un règlement
              </div>
            )}
          </>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 8, borderTop: '0.5px solid var(--border-light)' }}>
          {peutModifier && (facture.est_validee && !facture.est_proforma ? (
            <button className={styles.btnSec} onClick={() => setShowAvoir(true)}
              style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--red)', borderColor: '#F5BEBE' }}>
              <i className="ti ti-receipt-refund" aria-hidden="true" />
              Créer un avoir
            </button>
          ) : <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Validez la facture pour émettre le document définitif et créer un avoir.</span>)}
          {(facture.est_validee || facture.est_proforma) && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <button className={styles.btnSec} onClick={telechargerPDF} disabled={loadingPdf}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <i className="ti ti-file-type-pdf" style={{ color: '#DC2626' }} aria-hidden="true" />
                {loadingPdf ? 'Génération...' : (facture.est_proforma ? 'Télécharger la proforma' : 'Télécharger PDF')}
              </button>
              <button className={styles.btnSec} disabled={loadingPdf}
                onClick={() => preparerEmailDocument({
                  endpoint: `/api/factures/${facture.id}/pdf`,
                  nomFichier: `facture_${facture.numero}.pdf`,
                  typeDocument: facture.est_proforma ? 'Facture proforma' : (facture.type === 'achat' ? "Facture d'achat" : 'Facture'),
                  numero: facture.numero, tiers: facture.tiers, tiersId: facture.tiers_id,
                }).catch(e => notifier.erreur(e.message))}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <i className="ti ti-mail-forward" aria-hidden="true" /> Préparer e-mail
              </button>
            </div>
          )}
        </div>

        {facture.est_validee && !facture.est_proforma && facture.type === 'vente' && <FactureConservation key={facture.id} facture={facture} peutModifier={peutModifier}/>}

        {peutModifier && showAvoir && (
          <FormulaireAvoir
            facture={facture}
            avoirsExistants={avoirs}
            onFermer={() => setShowAvoir(false)}
            onSuccess={() => { setShowAvoir(false); chargerAvoirs() }}
          />
        )}
      </div>
    </Modal>
  )
}


// ─── Formulaire édition facture ───────────────────────────────────────────────
function FormulaireEditionFacture({ facture, onFermer, onSuccess }) {
  const { mettreAJourFacture } = useFactures()
  const natureAchatConnue = ['charge', 'non_deductible', 'immobilisation'].includes(facture.nature_tva_achat)
  const pctAchatConnu = facture.tva_deductible_pct != null && Number.isFinite(Number(facture.tva_deductible_pct)) && Number(facture.tva_deductible_pct) >= 0 && Number(facture.tva_deductible_pct) <= 100
  const [natureTVAAchatEdit, setNatureTVAAchatEdit] = useState(natureAchatConnue ? facture.nature_tva_achat : '')
  const [tvaDeductiblePctEdit, setTvaDeductiblePctEdit] = useState(pctAchatConnu ? facture.tva_deductible_pct : '')
  const [qualificationAchatChoisie, setQualificationAchatChoisie] = useState(false)
  const [date,          setDate]          = useState(facture.date || '')
  const [tiers,         setTiers]         = useState(facture.tiers || '')
  const [tiersId,       setTiersId]       = useState(facture.tiers_id || null)
  const [numero,        setNumero]        = useState(facture.numero || '')
  const [reference,     setReference]     = useState(facture.reference || '')
  const [delaiPaiement, setDelaiPaiement] = useState(facture.delai_paiement ?? 60)
  const [dateEcheanceEdit, setDateEcheanceEdit] = useState(facture.date_echeance || '')
  const [echeanceEditManuelle, setEcheanceEditManuelle] = useState(Boolean(facture.date_echeance))
  const [modeReglementPrevu, setModeReglementPrevu] = useState(facture.mode_reglement_prevu || '')
  const [referenceReglementPrevue, setReferenceReglementPrevue] = useState(facture.reference_reglement_prevue || '')
  const [statut]                         = useState(facture.statut || 'en_attente')
  const [avecTransport,  setAvecTransport]  = useState((facture.frais_transport_ht || 0) > 0)
  const [transportHT,    setTransportHT]    = useState(facture.frais_transport_ht || 0)
  const [transportTVA,   setTransportTVA]   = useState(facture.frais_transport_tva ?? 20)
  const [transportMode, setTransportMode] = useState(facture.frais_transport_mode || 'accessoire')
  const [transportQualification, setTransportQualification] = useState(facture.frais_transport_qualification_tva || 'taxable')
  const [avecEmballage,  setAvecEmballage]  = useState((facture.frais_emballage_ht || 0) > 0)
  const [emballageHT,    setEmballageHT]    = useState(facture.frais_emballage_ht || 0)
  const [emballageTVA,   setEmballageTVA]   = useState(facture.frais_emballage_tva ?? 20)
  const [emballageMode, setEmballageMode] = useState(facture.frais_emballage_mode || 'perdu')
  const [emballageQualification, setEmballageQualification] = useState(facture.frais_emballage_qualification_tva || 'taxable')
  const rasInitialInvalide = Boolean(facture.ras_anomalie) || facture.ras_taux == null || !Number.isFinite(Number(facture.ras_taux)) || Number(facture.ras_taux) < 0 || Number(facture.ras_taux) > 100
  const [rasTaux,        setRasTaux]        = useState(rasInitialInvalide ? '' : facture.ras_taux)
  const [rasChoisi, setRasChoisi] = useState(false)
  const [lignes,        setLignes]        = useState(
    (facture.lignes || []).map(l => ({
      article_id: l.article_id || null, source_ligne_devis_id: l.source_ligne_devis_id || null, source_ligne_bc_id: l.source_ligne_bc_id || null, source_ligne_bl_id: l.source_ligne_bl_id || null,
      description:   l.description   || '',
      quantite:      l.quantite       || 1,
      prix_unitaire: l.prix_unitaire  || 0,
      tva:           l.tva            ?? 20,
      qualification_tva: l.qualification_tva || (Number(l.tva) === 0 ? 'exonere_sans_deduction' : 'taxable'),
      remise:        l.remise         || 0,
      remise2:       l.remise2        || 0,
      rabais:        l.rabais         || 0,
    }))
  )
  const verrouille = !!facture.est_validee && !facture.est_proforma
  useEffect(() => {
    if (verrouille || echeanceEditManuelle || !date) return
    setDateEcheanceEdit(dateLocaleISO(dateEcheance(date, entierOuDefaut(delaiPaiement, 60))))
  }, [date, delaiPaiement, echeanceEditManuelle, verrouille])
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')

  const totaux = useMemo(() => {
    const baseLignes = lignes.map(l => {
      const q = parseFloat(l.quantite) || 0, pu = parseFloat(l.prix_unitaire) || 0
      const r1 = parseFloat(l.remise) || 0, r2 = parseFloat(l.remise2) || 0, rb = parseFloat(l.rabais) || 0
      return { base: Math.max(0, q*pu*(1-r1/100)*(1-r2/100)-rb*q), taux: tvaEffective(l) }
    })
    const htLignes = baseLignes.reduce((a,l)=>a+l.base,0)
    const tvaLignes = baseLignes.reduce((a,l)=>a+l.base*l.taux/100,0)
    const tauxMoyen = htLignes > 0 ? tvaLignes/htLignes : 0
    const th = avecTransport ? (parseFloat(transportHT)||0) : 0
    const tt = transportMode === 'accessoire' ? tauxMoyen : (transportQualification === 'taxable' ? (parseFloat(transportTVA)||0) : 0)
    const eh = avecEmballage ? (parseFloat(emballageHT)||0) : 0
    const et = emballageMode === 'perdu' ? tauxMoyen : emballageMode === 'consigne' ? 0 : (emballageQualification === 'taxable' ? (parseFloat(emballageTVA)||0) : 0)
    const ht = htLignes + th + eh, tva = tvaLignes + th*tt/100 + eh*et/100
    return { ht, tva, ttc: ht+tva }
  }, [lignes, avecTransport, transportHT, transportTVA, transportMode, transportQualification, avecEmballage, emballageHT, emballageTVA, emballageMode, emballageQualification])

  function majLigne(i, champ, val) {
    setLignes(prev => prev.map((l, idx) => idx === i ? { ...l, [champ]: val } : l))
  }

  async function handleSave() {
    if (!tiers.trim()) { setErreur('Tiers requis'); return }
    const pctAchat = Number(tvaDeductiblePctEdit)
    if (facture.type === 'achat' && !verrouille && qualificationAchatChoisie && (
      !['charge', 'non_deductible'].includes(natureTVAAchatEdit) || String(tvaDeductiblePctEdit).trim() === '' ||
      !Number.isFinite(pctAchat) || pctAchat < 0 || pctAchat > 100
    )) {
      setErreur('Choisissez la qualification TVA de l’achat et un pourcentage fini entre 0 et 100.')
      return
    }
    const tauxRas = Number(rasTaux)
    if (String(rasTaux).trim() === '' || !Number.isFinite(tauxRas) || tauxRas < 0 || tauxRas > 100 || (rasInitialInvalide && (!rasChoisi || verrouille))) {
      setErreur(verrouille ? 'RAS historique invalide : une correction contrôlée distincte est nécessaire pour cette facture validée.' : 'Choisissez explicitement une retenue à la source valide avant de sauvegarder ce brouillon.')
      return
    }
    setLoading(true); setErreur('')
    try {
      const token = localStorage.getItem('hisabpro_token')
      const payload = {
        date, tiers, tiers_id: tiersId, reference,
        delai_paiement: entierOuDefaut(delaiPaiement, 60),
        date_echeance: dateEcheanceEdit || null,
        mode_reglement_prevu: modeReglementPrevu || null,
        reference_reglement_prevue: referenceReglementPrevue.trim() || null,
      }
      if (!verrouille) {
        if (facture.type === 'achat' && qualificationAchatChoisie) {
          payload.nature_tva_achat = natureTVAAchatEdit
          payload.tva_deductible_pct = natureTVAAchatEdit === 'non_deductible' ? 0 : pctAchat
        }
        payload.frais_transport_ht  = avecTransport ? (parseFloat(transportHT) || 0) : 0
        payload.frais_transport_tva = avecTransport ? (parseFloat(transportTVA) || 0) : 20
        payload.frais_transport_mode = transportMode
        payload.frais_transport_qualification_tva = transportMode === 'distinct' ? transportQualification : 'taxable'
        payload.frais_emballage_ht  = avecEmballage ? (parseFloat(emballageHT) || 0) : 0
        payload.frais_emballage_tva = avecEmballage ? (parseFloat(emballageTVA) || 0) : 20
        payload.frais_emballage_mode = emballageMode
        payload.frais_emballage_qualification_tva = emballageMode === 'vente_distincte' ? emballageQualification : 'taxable'
        payload.ras_taux            = tauxRas
        payload.lignes = lignes.map(l => ({
          article_id: l.article_id || null,
          source_ligne_devis_id: l.source_ligne_devis_id || null,
          source_ligne_bc_id: l.source_ligne_bc_id || null,
          source_ligne_bl_id: l.source_ligne_bl_id || null,
          description:   l.description,
          quantite:      parseFloat(l.quantite)      || 1,
          prix_unitaire: parseFloat(l.prix_unitaire) || 0,
          tva:           nombreOuDefaut(l.tva, 20),
          qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva),
          remise:        parseFloat(l.remise)        || 0,
          remise2:       parseFloat(l.remise2)       || 0,
          rabais:        parseFloat(l.rabais)        || 0,
        }))
      }
      const res = await fetch(`${API_BASE}/api/factures/${facture.id}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Erreur') }
      await onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={`Modifier — ${facture.numero || `Brouillon #${facture.id}`}`} icone="ti-pencil" onFermer={onFermer} largeur="xl">
      <div className={`${styles.formContenu} hp-document-editor`}>
        {verrouille && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#FFFBEB', color: '#854F0B', padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
            <i className="ti ti-lock" />
            Facture validée : les données de facturation sont figées. Utilisez un avoir ou un document correctif pour toute correction.
          </div>
        )}
        <FormSection icon="ti-file-invoice" title="Informations de la facture" description="Document, tiers et références.">
          <div className={styles.editFields}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Date *</label>
              <input className={styles.input} type="date" value={date} disabled={verrouille} onChange={e => setDate(e.target.value)} />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Statut</label>
              <select className={styles.input} value={statut} disabled title="Statut calculé automatiquement à partir des règlements et avoirs">
                <option value="en_attente">En attente</option>
                <option value="partiellement_payee">Part. payée</option>
                <option value="payee">Payée</option>
                <option value="retard">En retard</option>
                <option value="annulee">Annulée</option>
              </select>
            </div>
            <div className={`${styles.formGroup} ${styles.editFullField}`}>
              <label className={styles.label}>Tiers *</label>
              <ChampTiers value={tiers} onChange={setTiers} type={facture.type} onTiersSelect={t => setTiersId(t?.id || null)} />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>N° facture interne</label>
              <input className={styles.input} value={numero || `Brouillon #${facture.id}`} readOnly />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>{facture.type === 'achat' ? 'N° facture fournisseur' : 'Référence'}</label>
              <input className={styles.input} value={reference} onChange={e => setReference(e.target.value)} />
            </div>
          </div>
        </FormSection>

        {facture.type === 'achat' && (
          <FormSection icon="ti-receipt-tax" title="TVA de l’achat" description="Qualification et part déductible propres à cette facture.">
            {(!natureAchatConnue || !pctAchatConnu) && <InlineNotice tone="warning">
              Qualification historique inconnue : les valeurs sont conservées tant qu’aucun choix explicite n’est enregistré.
            </InlineNotice>}
            <div className={styles.editFields}>
              <label className={styles.formGroup}>
                <span className={styles.label}>Qualification TVA de l’achat</span>
                <select aria-label="Qualification TVA de l’achat" className={styles.input} value={natureTVAAchatEdit} disabled={verrouille}
                  onChange={e => {
                    setNatureTVAAchatEdit(e.target.value); setQualificationAchatChoisie(true)
                    if (e.target.value === 'non_deductible') setTvaDeductiblePctEdit(0)
                  }}>
                  <option value="" disabled>À renseigner</option>
                  <option value="charge">Charge / achat courant</option>
                  <option value="non_deductible">TVA non déductible</option>
                  {facture.nature_tva_achat === 'immobilisation' && <option value="immobilisation" disabled>Immobilisation — valeur historique</option>}
                </select>
              </label>
              <label className={styles.formGroup}>
                <span className={styles.label}>TVA déductible (%)</span>
                <input aria-label="TVA déductible (%)" className={styles.input} type="number" min="0" max="100" step="0.01"
                  value={tvaDeductiblePctEdit} disabled={verrouille || natureTVAAchatEdit === 'non_deductible'}
                  onChange={e => { setTvaDeductiblePctEdit(e.target.value); setQualificationAchatChoisie(true) }} />
              </label>
            </div>
            <span className={styles.label}>Cette qualification pilote la déclaration et l’écriture comptable. Les immobilisations se saisissent dans le module Immobilisations.</span>
          </FormSection>
        )}

        <FormSection icon="ti-calendar-due" title="Conditions de règlement" description="Échéance et informations de paiement convenues.">
          <div className={styles.editFields}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Délai de paiement (jours)</label>
              <input aria-label="Délai de paiement de la facture" className={styles.input} type="number" min="0" step="1" disabled={verrouille} value={delaiPaiement} onChange={e => { setDelaiPaiement(e.target.value); setEcheanceEditManuelle(false) }} />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Échéance</label>
              <input aria-label="Échéance de la facture" className={styles.input} type="date" value={dateEcheanceEdit} min={date || undefined} disabled={verrouille}
                onChange={e => { setDateEcheanceEdit(e.target.value); setEcheanceEditManuelle(true) }} />
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{echeanceEditManuelle ? 'Échéance conservée ; modifier le délai la recalculera.' : 'Échéance calculée depuis la date et le délai de paiement.'}</span>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Mode de règlement convenu</label>
              <select className={styles.input} value={modeReglementPrevu} disabled={verrouille} onChange={e => setModeReglementPrevu(e.target.value)}>
                {MODES_REGLEMENT_PREVUS.map(([v,l]) => <option key={v || 'none'} value={v}>{l}</option>)}
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Référence prévue</label>
              <input className={styles.input} value={referenceReglementPrevue} disabled={verrouille} onChange={e => setReferenceReglementPrevue(e.target.value)} />
            </div>
            {Number(delaiPaiement || 0) > 120 && <div className={styles.editFullField}>
              <InlineNotice tone="warning">Délai supérieur à 120 jours : vérifiez la convention ou la dérogation sectorielle applicable.</InlineNotice>
            </div>}
          </div>
        </FormSection>

        {/* Les colonnes deviennent des fiches selon la largeur effective de la modale. */}
        <FormSection icon="ti-list-details" title="Lignes de facture" description="Désignation, quantité, prix et TVA de chaque ligne.">
        <div className={`${styles.lignesTable} hp-line-editor`}>
          <table className={styles.tableLignes}>
            <thead>
              <tr>
                <th style={{ width: '40%' }}>Désignation</th>
                <th style={{ width: '10%', textAlign: 'center' }}>Qté</th>
                <th style={{ width: '18%', textAlign: 'right' }}>Prix HT</th>
                <th style={{ width: '10%', textAlign: 'center' }}>TVA %</th>
                <th style={{ width: '18%', textAlign: 'right' }}>Total HT</th>
                <th style={{ width: 32 }} />
              </tr>
            </thead>
            <tbody>
              {lignes.map((l, i) => (
                <tr key={i}>
                  <td data-label="Désignation"><input className={styles.inputLigne} value={l.description} disabled={verrouille}
                    onChange={e => majLigne(i, 'description', e.target.value)} /></td>
                  <td data-label="Quantité"><input className={styles.inputLigne} type="number" value={l.quantite} disabled={verrouille}
                    onChange={e => majLigne(i, 'quantite', e.target.value)} style={{ textAlign: 'center' }} /></td>
                  <td data-label="Prix HT"><input className={styles.inputLigne} type="number" value={l.prix_unitaire} disabled={verrouille}
                    onChange={e => majLigne(i, 'prix_unitaire', e.target.value)} style={{ textAlign: 'right' }} /></td>
                  <td data-label="TVA">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <select className={styles.inputLigne} value={l.tva} disabled={verrouille} onChange={e => {
                      const taux = Number(e.target.value); majLigne(i, 'tva', e.target.value)
                      majLigne(i, 'qualification_tva', qualificationParDefautPourTaux(taux, l.qualification_tva))
                    }}>
                      {tauxTVAAvecHistorique(date, l.tva).map(t => <option key={t} value={t}>{t}%</option>)}
                    </select>
                    {Number(l.tva) === 0 && <select className={styles.inputLigne} value={l.qualification_tva || 'exonere_sans_deduction'} disabled={verrouille} onChange={e => majLigne(i, 'qualification_tva', e.target.value)}>
                      {QUALIFICATIONS_TVA.filter(q=>q.value!=='taxable').map(q=><option key={q.value} value={q.value}>{q.label}</option>)}
                    </select>}
                    </div>
                  </td>
                  <td data-label="Total HT" style={{ textAlign: 'right', padding: '0 8px', fontSize: 12, fontWeight: 500 }}>
                    {formatMAD((parseFloat(l.quantite)||0) * (parseFloat(l.prix_unitaire)||0) * (1 - (parseFloat(l.remise)||0)/100))}
                  </td>
                  <td data-label="Supprimer">
                    {lignes.length > 1 && !verrouille && (
                      <button onClick={() => setLignes(prev => prev.filter((_,idx) => idx !== i))}
                        className={styles.btnSuppr}>
                        <i className="ti ti-x" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className={styles.btnAjouterLigne} disabled={verrouille}
            onClick={() => setLignes(prev => [...prev, { description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, remise2: 0, rabais: 0 }])}>
            <i className="ti ti-plus" /> Ajouter une ligne
          </button>
        </div>
        </FormSection>

        <FormSection icon="ti-adjustments" title="Frais et retenues" description="Options applicables à cette facture.">
        {/* Frais transport / emballage */}
        <div className={styles.editExtras}>
          <div className={styles.editOption}>
            <label className={styles.editOptionLabel}>
              <input type="checkbox" checked={avecTransport} disabled={verrouille} onChange={e => setAvecTransport(e.target.checked)} />
              <i className="ti ti-truck" style={{ color: 'var(--blue)' }} />Transport
            </label>
            {avecTransport && <>
              <input type="number" min="0" step="0.01" placeholder="Montant HT" disabled={verrouille}
                value={transportHT} onChange={e => setTransportHT(e.target.value)}
                style={{ width: 100, padding: '4px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12 }} />
              <select value={transportMode} disabled={verrouille} onChange={e => setTransportMode(e.target.value)} className={styles.inputSm}>
                <option value="accessoire">Accessoire — TVA des lignes</option>
                <option value="distinct">Prestation distincte</option>
              </select>
              {transportMode === 'distinct' && <>
                <select value={transportTVA} disabled={verrouille} onChange={e => {
                  setTransportTVA(e.target.value)
                  setTransportQualification(qualificationParDefautPourTaux(Number(e.target.value), transportQualification))
                }} className={styles.inputSm}>
                  {tauxTVAAvecHistorique(date, transportTVA).map(t => <option key={t} value={t}>{t}%</option>)}
                </select>
                {Number(transportTVA) === 0 && <select value={transportQualification} disabled={verrouille} onChange={e => setTransportQualification(e.target.value)} className={styles.inputSm}>
                  {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                </select>}
              </>}
            </>}
          </div>
          <div className={styles.editOption}>
            <label className={styles.editOptionLabel}>
              <input type="checkbox" checked={avecEmballage} disabled={verrouille} onChange={e => setAvecEmballage(e.target.checked)} />
              <i className="ti ti-package" style={{ color: 'var(--blue)' }} />Emballage
            </label>
            {avecEmballage && <>
              <input type="number" min="0" step="0.01" placeholder="Montant" disabled={verrouille}
                value={emballageHT} onChange={e => setEmballageHT(e.target.value)}
                style={{ width: 100, padding: '4px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12 }} />
              <select value={emballageMode} disabled={verrouille} onChange={e => setEmballageMode(e.target.value)} className={styles.inputSm}>
                <option value="perdu">Perdu — TVA des lignes</option>
                <option value="consigne">Consigné / récupérable</option>
                <option value="vente_distincte">Vendu distinctement</option>
              </select>
              {emballageMode === 'vente_distincte' && <>
                <select value={emballageTVA} disabled={verrouille} onChange={e => {
                  setEmballageTVA(e.target.value)
                  setEmballageQualification(qualificationParDefautPourTaux(Number(e.target.value), emballageQualification))
                }} className={styles.inputSm}>
                  {tauxTVAAvecHistorique(date, emballageTVA).map(t => <option key={t} value={t}>{t}%</option>)}
                </select>
                {Number(emballageTVA) === 0 && <select value={emballageQualification} disabled={verrouille} onChange={e => setEmballageQualification(e.target.value)} className={styles.inputSm}>
                  {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                </select>}
              </>}
              {emballageMode === 'consigne' && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Hors base TVA jusqu'à non-restitution.</span>}
            </>}
          </div>
          <div className={styles.editRetenue}>
            <label className={styles.editOptionLabel}>
              <i className="ti ti-receipt-tax" style={{ marginRight: 4, color: 'var(--blue)' }} />Retenue à la source (sur HT)
            </label>
            <select aria-label="Retenue à la source de la facture" value={rasTaux} disabled={verrouille} onChange={e => { setRasTaux(e.target.value); setRasChoisi(true) }} className={styles.inputSm}>
              {rasInitialInvalide && <option value="" disabled>À vérifier — choisir explicitement</option>}
              {!rasInitialInvalide && ![0, 5, 10, 15, 20].includes(Number(facture.ras_taux)) && <option value={facture.ras_taux}>{facture.ras_taux}% (taux existant)</option>}
              <option value="0">Aucune</option><option value="5">5%</option><option value="10">10%</option><option value="15">15%</option><option value="20">20%</option>
            </select>
            {rasInitialInvalide && <p role="alert" style={{ color: 'var(--red)', fontSize: 12 }}>
              {facture.ras_anomalie || 'Le taux de retenue à la source est manquant ou invalide.'} {verrouille ? 'Facture validée : correction contrôlée distincte nécessaire.' : 'Aucun taux ne sera remplacé automatiquement. Choisissez explicitement le taux applicable au brouillon.'}
            </p>}
          </div>
        </div>

        </FormSection>

        {/* Montants et actions toujours lisibles. */}
        <div className={styles.totauxZone}>
          <div className={styles.editSummaryIntro}>
            <strong>Récapitulatif</strong>
            <span>Montants calculés à partir des lignes et options.</span>
          </div>
          <div className={styles.totauxGrid}>
            <span>Total HT</span><span>{formatMAD(totaux.ht)} MAD</span>
            <span>TVA</span><span>{formatMAD(totaux.tva)} MAD</span>
            <span className={styles.totalTTCLabel}>Total TTC</span>
            <span className={styles.totalTTCValeur}>{formatMAD(totaux.ttc)} MAD</span>
          </div>
        </div>

        {erreur && <div className={styles.erreurMsg}>{erreur}</div>}
        <ActionBar>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : 'Enregistrer les modifications'}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )
}

// ─── Page Factures ────────────────────────────────────────────────────────────

// ─── Modal Encaissement rapide depuis la liste ────────────────────────────────
function ModalEncaissementRapide({ facture, onFermer, onSuccess }) {
  const [totalRegle, setTotalRegle]     = useState(0)
  const [totalAvoirs, setTotalAvoirs]   = useState(0)
  const [totalAcomptes, setTotalAcomptes] = useState(0)
  const [situationRas, setSituationRas] = useState(null)
  const [erreurSituation, setErreurSituation] = useState('')
  const [listeReglements, setListeReglements] = useState([])
  const [soldeApi, setSoldeApi]         = useState(null)
  const [loading,    setLoading]        = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    let annule = false
    setLoading(true); setSoldeApi(null); setSituationRas(null); setErreurSituation('')
    // Endpoint enrichi : le solde restant tient compte des règlements,
    // des avoirs actifs ET des acomptes imputés.
    fetch(`${API_BASE}/api/factures/${facture.id}/reglements`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(lireSituationReglement)
      .then(data => {
        if (annule) return
        setTotalRegle(data.total_regle || 0)
        setTotalAvoirs(data.total_avoirs || 0)
        setTotalAcomptes(data.total_acomptes || 0)
        setSituationRas(data)
        setListeReglements(data.reglements || [])
        setSoldeApi(typeof data.solde_restant === 'number' && Number.isFinite(data.solde_restant) ? data.solde_restant : null)
      })
      .catch(e => { if (!annule) setErreurSituation(e.message) })
      .finally(() => { if (!annule) setLoading(false) })
    return () => { annule = true }
  }, [facture.id])

  const solde = soldeApi

  return (
    <Modal titre={`${facture.type === 'achat' ? 'Payer' : 'Encaisser'} — ${facture.numero}`} icone="ti-cash" onFermer={onFermer} largeur="md">
      <div className={styles.formContenu}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-tertiary)' }}>Chargement...</div>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 14px' }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>{facture.tiers}</strong> · Total TTC {formatMAD(facture.total_ttc)} MAD
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, color: solde > 0 ? 'var(--amber)' : 'var(--green)' }}>
                Reste : {solde === null ? 'À vérifier' : `${formatMAD(solde)} MAD`}
              </span>
            </div>
            <ResumeRASSituation situation={situationRas} />
            {erreurSituation && <InlineNotice tone="danger">{erreurSituation}</InlineNotice>}
            {solde === null && !erreurSituation && <InlineNotice tone="danger">Situation de paiement indisponible : vérifiez les données avant tout règlement.</InlineNotice>}
            {(totalRegle > 0 || totalAvoirs > 0 || totalAcomptes > 0) && (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', gap: 12, justifyContent: 'flex-end', padding: '0 4px' }}>
                {totalRegle > 0 && <span>Réglé : −{formatMAD(totalRegle)}</span>}
                {totalAvoirs > 0 && <span>Avoirs : −{formatMAD(totalAvoirs)}</span>}
                {totalAcomptes > 0 && <span>Acomptes imputés : −{formatMAD(totalAcomptes)}</span>}
              </div>
            )}
            {listeReglements.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, background: 'var(--bg-primary)', border: '0.5px solid var(--border-light)', borderRadius: 8, padding: '8px 12px' }}>
                <span style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.3, color: 'var(--text-tertiary)' }}>Historique des règlements</span>
                {listeReglements.map(r => {
                  const estRejete = r.statut === 'rejete'
                  const estAnnule = r.statut === 'annule'
                  const estInactif = estRejete || estAnnule
                  const enCours = ['portefeuille', 'encaissement', 'a_payer'].includes(r.statut)
                  return (
                    <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                      <span style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{formatDate(r.date)}</span>
                      <span style={{ color: 'var(--text-tertiary)' }}>{r.mode}{r.reference ? ` ${r.reference}` : ''}</span>
                      <span style={{ marginLeft: 'auto', fontWeight: 600, textDecoration: estInactif ? 'line-through' : 'none', color: estInactif ? 'var(--text-tertiary)' : 'var(--text-primary)' }}>
                        {formatMAD(r.montant)} MAD
                      </span>
                      {estInactif && (
                        <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: '#FCEBEB', color: '#A32D2D', fontWeight: 600 }}>
                          {estAnnule ? 'ANNULÉ — contrepassé' : 'REJETÉ — non compté'}
                        </span>
                      )}
                      {enCours && (
                        <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: '#FAEEDA', color: '#854F0B', fontWeight: 600 }}>
                          {r.statut === 'portefeuille' ? 'En portefeuille' : r.statut === 'encaissement' ? "À l'encaissement" : 'À payer'}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center', margin: '2px 0' }}>
              Montant pré-rempli avec le solde — modifiez-le pour un règlement partiel
            </div>
            <FormulaireReglementPartiel
              facture={facture}
              totalRegle={totalRegle}
              soldeEffectif={solde}
              onFermer={onFermer}
              onSuccess={onSuccess}
            />
          </>
        )}
      </div>
    </Modal>
  )
}

function ModalDateLivraison({ facture, onFermer, onConfirmer }) {
  const [date, setDate] = useState(dateLocaleISO())
  return (
    <Modal titre={`Bon de livraison — ${facture.numero}`} icone="ti-truck-delivery" onFermer={onFermer} largeur="sm">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
          Choisis la date de livraison effective. Par défaut, la date du jour — elle n'est plus
          calquée automatiquement sur la date de la facture.
        </p>
        <div>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
            Date de livraison
          </label>
          <input type="date" value={date} onChange={e => setDate(e.target.value)}
            style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }} />
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', paddingTop: 4 }}>
          <button onClick={onFermer}
            style={{ padding: '7px 14px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12 }}>
            Annuler
          </button>
          <button onClick={() => onConfirmer(date)}
            style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: 'var(--blue)', color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 500 }}>
            <i className="ti ti-truck-delivery" style={{ marginRight: 5 }} /> Créer le BL
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default function Factures() {
  const peutModifier = peutEcrire()
  const { factures, chargement, erreur: erreurFactures, supprimerFacture, recharger, validerFacture, comptabiliserFacture } = useFactures()
  const ecrituresCtx = useEcritures()
  const [comptaEnCours, setComptaEnCours] = useState(null)
  const [avertissementsMentions, setAvertissementsMentions] = useState([])

  // Comptabilise a posteriori une facture qui n'a pas d'écriture
  // (échec au moment de la création, ou toggle décoché).
  async function comptabiliserMaintenant(f) {
    if (!confirm(`Générer l'écriture comptable de la facture ${f.numero} ?`)) return
    setComptaEnCours(f.id)
    try {
      await comptabiliserFacture(f.id)
      // Le journal partage un contexte distinct de celui des factures :
      // sa liste doit être rechargée avant que l'utilisateur y navigue.
      if (ecrituresCtx?.recharger) await ecrituresCtx.recharger()
      await recharger()
    } catch (e) {
      notifier.erreur(`Impossible de comptabiliser cette facture :\n\n${e.message}`)
    } finally { setComptaEnCours(null) }
  }
  const { annee } = useExercice()
  const { societe: societeCourante } = useModules()
  const [avoirsExercice, setAvoirsExercice] = useState([])
  const [chargementAvoirs, setChargementAvoirs] = useState(true)
  const [erreurAvoirs, setErreurAvoirs] = useState('')
  const [showForm,     setShowForm]     = useState(false)
  const [factureOuv,   setFactureOuv]   = useState(null)
  const [showDrilldown, setShowDrilldown] = useState(false)
  const [filtreType,   setFiltreType]   = useState('TOUS')
  const [filtreStatut, setFiltreStatut] = useState('TOUS')
  const [recherche,    setRecherche]    = useState('')
  const [initialFacture, setInitialFacture] = useState(null)
  const [factureEdit,   setFactureEdit]   = useState(null)
  const [filtreDateDu,  setFiltreDateDu]  = useState('')
  const [filtreDateAu,  setFiltreDateAu]  = useState('')
  const rechercheRef = useRef(null)
  const filtresActifs = !!(recherche || filtreType !== 'TOUS' || filtreStatut !== 'TOUS' || filtreDateDu || filtreDateAu)
  function reinitialiserFiltres() {
    setRecherche(''); setFiltreType('TOUS'); setFiltreStatut('TOUS')
    setFiltreDateDu(''); setFiltreDateAu('')
    rechercheRef.current?.focus()
  }
  const [pjOuverte,      setPjOuverte]      = useState(null)
  const [factureEncaisser, setFactureEncaisser] = useState(null)
  const [creationBL, setCreationBL] = useState(null) // id de la facture en cours de création BL
  const [blDateModal, setBlDateModal] = useState(null) // facture pour laquelle on choisit la date de livraison

  async function creerBL(f, dateLivraison) {
    setCreationBL(f.id)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const res = await fetch(`${API_BASE}/api/factures/${f.id}/convertir-bl`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: dateLivraison || null }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur lors de la création du bon de livraison')
      }
      const bl = await res.json()
      notifier(`Bon de livraison ${bl.numero} créé avec succès.`)
    } catch (e) {
      notifier.erreur(e.message)
    } finally {
      setCreationBL(null)
    }
  }
  const location = useLocation()

  // Les avoirs sont datés sur leur propre période, même lorsque leur
  // facture source est antérieure à la fenêtre sélectionnée.
  useEffect(() => {
    const controller = new AbortController()
    setChargementAvoirs(true); setErreurAvoirs(''); setAvoirsExercice([])
    fetch(`${API_BASE}/api/avoirs?exercice=${annee}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('hisabpro_token')}` }, signal: controller.signal,
    }).then(async response => {
      if (!response.ok) throw new Error('Les avoirs sont indisponibles. Rechargez la page.')
      const data = await response.json()
      if (!Array.isArray(data)) throw new Error('Liste des avoirs indisponible.')
      if (!controller.signal.aborted) setAvoirsExercice(data)
    }).catch(error => {
      if (!controller.signal.aborted) setErreurAvoirs(error.message)
    }).finally(() => {
      if (!controller.signal.aborted) setChargementAvoirs(false)
    })
    return () => controller.abort()
  }, [annee, societeCourante?.id, factures])

  useEffect(() => {
    if (location.state?.nouvelleFacture) {
      setInitialFacture(location.state.nouvelleFacture)
      setShowForm(true)
    }
  }, [location.state])

  const periodeErreur = periodeInversee(filtreDateDu, filtreDateAu)
  const facturesPeriode = useMemo(() => factures.filter(f => dansPeriode(f, filtreDateDu, filtreDateAu)), [factures, filtreDateDu, filtreDateAu])
  const documentsPublies = useMemo(() => facturesPeriode.filter(facturePubliee), [facturesPeriode])
  const avoirsPeriode = useMemo(() => avoirsExercice.filter(a => avoirPublie(a) && dansPeriode(a, filtreDateDu, filtreDateAu)), [avoirsExercice, filtreDateDu, filtreDateAu])
  const avoirsVente = useMemo(() => avoirsPeriode.filter(a => a.type === 'vente'), [avoirsPeriode])
  const montantsInconnus = facturesPeriode.some(f => f.montants_valides === false)
  const indicateursDisponibles = !chargement && !chargementAvoirs && !erreurFactures && !erreurAvoirs && !periodeErreur && !montantsInconnus
  const facturesFiltrees = useMemo(() => {
    return facturesPeriode.filter(f => {
      if (filtreType   !== 'TOUS' && f.type   !== filtreType)   return false
      if (filtreStatut === 'retard' ? !factureEnRetard(f) : filtreStatut !== 'TOUS' && f.statut !== filtreStatut) return false
      if (recherche) {
        const q = recherche.toLowerCase()
        return (f.numero || '').toLowerCase().includes(q) || (f.tiers || '').toLowerCase().includes(q)
      }
      return true
    })
  }, [facturesPeriode, filtreType, filtreStatut, recherche])

  const drilldownCA = useMemo(() => {
    // Construire une map des prix d'achat depuis les factures achat
    const prixAchatMap = {}
    factures
      .filter(f => f.type === 'achat' && f.statut !== 'annulee')
      .forEach(f => {
        ;(f.lignes || []).forEach(l => {
          if (!prixAchatMap[l.description]) prixAchatMap[l.description] = []
          prixAchatMap[l.description].push(parseFloat(l.prix_unitaire) || 0)
        })
      })
    // Prix achat moyen par article
    const prixAchatMoyen = {}
    Object.keys(prixAchatMap).forEach(k => {
      const arr = prixAchatMap[k]
      prixAchatMoyen[k] = arr.reduce((s, v) => s + v, 0) / arr.length
    })

    return ventilationCA(documentsPublies, avoirsVente, prixAchatMoyen)
  }, [factures, documentsPublies, avoirsVente])

  const stats = useMemo(() => ({
    ...totauxFacturation(documentsPublies, avoirsPeriode),
    enAttente: facturesPeriode.filter(f => f.statut === 'en_attente').length,
    retard: facturesPeriode.filter(f => factureEnRetard(f)).length,
  }), [documentsPublies, avoirsPeriode, facturesPeriode])

  const panneauDroit = factureOuv
    ? factureOuv.montants_valides === false
      ? <DetailFactureHistorique facture={factureOuv} onFermer={() => setFactureOuv(null)} />
      : <DetailFacture facture={factureOuv} onFermer={() => setFactureOuv(null)} onStatutChange={async () => {
        await Promise.all([recharger(), ecrituresCtx?.recharger?.()])
        setFactureOuv(null)
      }} />
    : null

  // Compte les factures en retard de paiement
  const nbRetardPaiement = useMemo(() => {
    return facturesPeriode.filter(f => factureEnRetard(f)).length
  }, [facturesPeriode])

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Factures</h1>
        {nbRetardPaiement > 0 && (
          <div className={styles.alerteTopbar}>
            <i className="ti ti-clock-exclamation" aria-hidden="true" />
            {nbRetardPaiement} facture{nbRetardPaiement > 1 ? 's' : ''} en retard de paiement
          </div>
        )}
        <div className={styles.topbarRight}>
          <button className={styles.btnSec}
            disabled={chargement || !!erreurFactures || facturesFiltrees.some(f => f.montants_valides === false)}
            onClick={() => exporterCSV(`factures_${annee}`, [
              { label: 'Numéro',        get: f => f.numero },
              { label: 'Date',          get: f => f.date },
              { label: 'Type',          get: f => f.type === 'vente' ? 'Vente' : 'Achat' },
              { label: 'Tiers',         get: f => f.tiers },
              { label: 'Référence',     get: f => f.reference || '' },
              { label: 'Statut',        get: f => f.est_proforma ? 'Proforma' : (f.statut || '').replace(/_/g, ' ') },
              { label: 'Total HT',      get: f => f.total_ht,  type: 'nombre' },
              { label: 'Total TVA',     get: f => f.total_tva, type: 'nombre' },
              { label: 'Total TTC',     get: f => f.total_ttc, type: 'nombre' },
              { label: 'RAS estimée',           get: f => f.montant_ras, type: 'nombre' },
              { label: 'Net estimé après RAS',   get: f => f.net_a_payer, type: 'nombre' },
              { label: 'Comptabilisée', get: f => f.est_comptabilisee ? 'Oui' : 'Non' },
            ], facturesFiltrees)}>
            <i className="ti ti-download" aria-hidden="true" /> Exporter CSV
          </button>
          <button className={styles.btnPrim} onClick={() => setShowForm(true)}
            disabled={!peutModifier} title={!peutModifier ? 'Compte en consultation seule' : undefined}>
            <i className="ti ti-plus" aria-hidden="true" /> Nouvelle facture
          </button>
        </div>
      </div>

      {avertissementsMentions.length > 0 && (
        <div role="status" style={{ margin: '12px 20px', padding: '10px 14px', background: '#FFF7E6', border: '1px solid #E7BE75', borderRadius: 8, fontSize: 12 }}>
          <strong>Facture validée — mentions à compléter avant envoi :</strong>{' '}
          {avertissementsMentions.join(', ')}. Vérifiez la fiche société et la fiche client.
          <button type="button" onClick={() => setAvertissementsMentions([])}
            style={{ marginLeft: 12, cursor: 'pointer', border: 'none', background: 'transparent', textDecoration: 'underline' }}>
            Masquer
          </button>
        </div>
      )}

      {peutModifier && showForm && (
        <FormulaireFacture
          onFermer={() => { setShowForm(false); setInitialFacture(null) }}
          onSuccess={(mentions = []) => { setShowForm(false); setInitialFacture(null); setAvertissementsMentions(mentions) }}
          initialData={initialFacture}
        />
      )}

      {peutModifier && factureEncaisser && (
        <ModalEncaissementRapide
          facture={factureEncaisser}
          onFermer={() => setFactureEncaisser(null)}
          onSuccess={async () => {
            await Promise.all([recharger(), ecrituresCtx?.recharger?.()])
            setFactureEncaisser(null)
          }}
        />
      )}

      {peutModifier && blDateModal && (
        <ModalDateLivraison
          facture={blDateModal}
          onFermer={() => setBlDateModal(null)}
          onConfirmer={(dateChoisie) => { setBlDateModal(null); creerBL(blDateModal, dateChoisie) }}
        />
      )}

      {peutModifier && factureEdit && (
        <FormulaireEditionFacture
          facture={factureEdit}
          onFermer={() => setFactureEdit(null)}
          onSuccess={async () => { await recharger(); setFactureEdit(null) }}
        />
      )}

      {factureOuv && (
        factureOuv.montants_valides === false
        ? <DetailFactureHistorique facture={factureOuv} onFermer={() => setFactureOuv(null)} />
        : <DetailFacture
          facture={factures.find(f => f.id === factureOuv.id) || factureOuv}
          onFermer={() => setFactureOuv(null)}
          onStatutChange={async () => {
            await Promise.all([recharger(), ecrituresCtx?.recharger?.()])
            setFactureOuv(null)
          }}
        />
      )}

      <div className={styles.content}>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Indicateurs de facturation sur la période sélectionnée, factures validées hors proformas et annulations, nets des avoirs datés sur cette période. HT après remises, avant escompte. Coûts moyens indicatifs ; ne remplace pas le CA comptable.</p>
        {periodeErreur && <p role="alert" style={{ color: 'var(--red)' }}>La date de fin doit être supérieure ou égale à la date de début.</p>}
        {(erreurFactures || erreurAvoirs) && <p role="alert" style={{ color: 'var(--red)' }}>{erreurFactures || erreurAvoirs} Les indicateurs ne sont pas calculés sur un chargement incomplet.</p>}
        {montantsInconnus && <div role="alert" style={{ color: 'var(--red)' }}>Montants historiques à vérifier. Les factures restent visibles. Les indicateurs ne sont pas calculés sur des montants inconnus. <button className={styles.btnSec} onClick={recharger}>Réessayer</button></div>}
        {/* KPIs */}
        <div className={styles.kpiGrid} style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <div className={styles.kpiCard} data-testid="facturation-nette-ht">
            <div className={styles.kpiLabel}>Facturation nette HT</div>
            <div className={styles.kpiValeur}>{indicateursDisponibles ? formatMAD(stats.caNetHT) : '—'}<span className={styles.kpiDevise}> MAD</span></div>
          </div>
          <div className={styles.kpiCard} data-testid="ventes-nettes-ttc"
            onClick={() => setShowDrilldown(p => !p)}
            style={{ cursor: 'pointer', border: showDrilldown ? '1px solid var(--blue)' : '0.5px solid var(--border-light)', transition: 'border 0.15s' }}>
            <div className={styles.kpiLabel}>
              <i className="ti ti-arrow-up-right" style={{ color: 'var(--blue)' }} aria-hidden="true" />
              Ventes nettes TTC
              <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--blue)', opacity: 0.7 }}>
                {showDrilldown ? '▲' : '▼ détail'}
              </span>
            </div>
            <div className={styles.kpiValeur}>{indicateursDisponibles ? formatMAD(stats.ventesNettesTTC) : '—'}<span className={styles.kpiDevise}> MAD</span></div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-arrow-down-left" style={{ color: '#534AB7' }} aria-hidden="true" />Achats nets TTC</div>
            <div className={styles.kpiValeur}>{indicateursDisponibles ? formatMAD(stats.achatsNetsTTC) : '—'}<span className={styles.kpiDevise}> MAD</span></div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-clock" style={{ color: 'var(--amber)' }} aria-hidden="true" />En attente</div>
            <div className={styles.kpiValeur} style={{ color: stats.enAttente > 0 ? 'var(--amber)' : 'var(--text-primary)' }}>
              {indicateursDisponibles ? stats.enAttente : '—'}<span className={styles.kpiDevise}> facture{stats.enAttente !== 1 ? 's' : ''}</span>
            </div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-alert-circle" style={{ color: 'var(--red)' }} aria-hidden="true" />En retard</div>
            <div className={styles.kpiValeur} style={{ color: stats.retard > 0 ? 'var(--red)' : 'var(--text-primary)' }}>
              {indicateursDisponibles ? stats.retard : '—'}<span className={styles.kpiDevise}> facture{stats.retard !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>

        {/* Drill-down CA par article */}
        {showDrilldown && indicateursDisponibles && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-chart-bar" style={{ color: 'var(--blue)', marginRight: 6 }} />
                Facturation par article — Ventes
                <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--text-tertiary)', marginLeft: 8 }}>
                  (net des avoirs{avoirsVente.length > 0 ? ` — ${avoirsVente.length} appliqué(s)` : ''})
                </span>
              </span>
              <button onClick={() => setShowDrilldown(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16 }}>✕</button>
            </div>
            {drilldownCA.filter(x => x.hors_article).map(x => <p key={x.designation} style={{ fontSize: 12, padding: '0 16px', color: 'var(--text-secondary)' }}>{x.designation} : {formatMAD(x.ca_ttc)} MAD (hors articles, inclus dans les totaux documentaires).</p>)}
            {drilldownCA.filter(x => !x.hors_article).length === 0 ? (
              <div className={styles.vide}><i className="ti ti-chart-bar" /><span>Aucune vente</span></div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Article</th>
                      <th style={{ textAlign: 'right' }}>Qté</th>
                      <th style={{ textAlign: 'right' }}>Net HT</th>
                      <th style={{ textAlign: 'right' }}>Net TTC</th>
                      <th style={{ textAlign: 'right' }}>Coût achat</th>
                      <th style={{ textAlign: 'right' }}>Marge HT</th>
                      <th style={{ width: 130 }}>Part du net HT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {drilldownCA.filter(x => !x.hors_article).map((x, i) => (
                      <tr key={i}>
                        <td><strong>{x.designation}</strong></td>
                        <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{x.quantite}</td>
                        <td style={{ textAlign: 'right', fontWeight: 500 }}>{formatMAD(x.ca_ht)} MAD</td>
                        <td style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 11 }}>{formatMAD(x.ca_ttc)} MAD</td>
                        <td style={{ textAlign: 'right', color: 'var(--text-tertiary)', fontSize: 11 }}>
                          {x.cout > 0 ? `${formatMAD(x.cout)} MAD` : '—'}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {x.cout > 0 ? (
                            <span style={{ fontWeight: 600, color: x.marge >= 0 ? '#3B6D11' : '#A32D2D' }}>
                              {formatMAD(x.marge)} MAD
                              <span style={{ fontSize: 10, marginLeft: 4, opacity: 0.8 }}>
                                ({x.taux_marge !== null ? x.taux_marge.toFixed(1) : 0}%)
                              </span>
                            </span>
                          ) : <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>— (pas d'achat)</span>}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ flex: 1, height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
                              <div style={{ width: `${Math.max(0, Math.min(100, x.pct))}%`, height: '100%', background: 'var(--blue)', borderRadius: 3 }} />
                            </div>
                            <span style={{ fontSize: 11, color: 'var(--text-secondary)', minWidth: 36, textAlign: 'right' }}>
                              {x.pct.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Filtres */}
        <div className={styles.filtres}>
          <div className={styles.recherche}>
            <i className="ti ti-search" aria-hidden="true" />
            <input ref={rechercheRef} type="text" role="searchbox" aria-label="Rechercher une facture par numéro ou tiers" placeholder="Rechercher numéro, tiers..."
              value={recherche} onChange={e => setRecherche(e.target.value)}
              className={styles.inputRecherche} />
            {recherche && <button type="button" className={styles.clearBtn} aria-label="Effacer la recherche" title="Effacer la recherche" onClick={() => { setRecherche(''); rechercheRef.current?.focus() }}><i className="ti ti-x" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Effacer la recherche</span></button>}
          </div>
          <div className={styles.filtresBarre}>
            {[['TOUS','Tous'], ['vente','Ventes'], ['achat','Achats']].map(([val, label]) => (
              <button key={val} className={`${styles.filtreBtn} ${filtreType === val ? styles.filtreBtnActif : ''}`}
                type="button" aria-pressed={filtreType === val}
                onClick={() => setFiltreType(val)}>{label}</button>
            ))}
            <div className={styles.separateur} />
            {[['TOUS','Tous statuts'], ['payee','Payées'], ['partiellement_payee','Part. payées'], ['en_attente','En attente'], ['retard','En retard']].map(([val, label]) => (
              <button key={val} className={`${styles.filtreBtn} ${filtreStatut === val ? styles.filtreBtnActif : ''}`}
                type="button" aria-pressed={filtreStatut === val}
                onClick={() => setFiltreStatut(val)}>{label}</button>
            ))}
            <div className={styles.separateur} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Du</span>
              <input type="date" aria-label="Date de début des factures et indicateurs" value={filtreDateDu} onChange={e => setFiltreDateDu(e.target.value)}
                style={{ padding: '4px 8px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>au</span>
              <input type="date" aria-label="Date de fin des factures et indicateurs" value={filtreDateAu} onChange={e => setFiltreDateAu(e.target.value)}
                style={{ padding: '4px 8px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
              {(filtreDateDu || filtreDateAu) && (
                <button aria-label="Effacer la période" onClick={() => { setFiltreDateDu(''); setFiltreDateAu('') }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 14 }}>✕</button>
              )}
            </div>
            {filtresActifs && <button type="button" className={styles.btnSec} onClick={reinitialiserFiltres}>
              <i className="ti ti-filter-off" aria-hidden="true" /> Réinitialiser les filtres
            </button>}
          </div>
        </div>

        <div className={!chargement && !erreurFactures && facturesFiltrees.length === 0 ? styles.listeVideWrap : styles.fullWidth}>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle} role="status" aria-live="polite" aria-atomic="true">{chargement ? 'Chargement des factures…' : erreurFactures ? 'Liste des factures indisponible' : `${facturesFiltrees.length} facture${facturesFiltrees.length !== 1 ? 's' : ''}`}</span>
            </div>
            {chargement ? (
              <div className={styles.vide}>
                <i className="ti ti-loader-2" aria-hidden="true" />
                <span>Chargement...</span>
              </div>
            ) : erreurFactures ? (
              <div className={styles.vide}>
                <span>Chargement impossible des factures.</span>
                <button className={styles.btnSec} onClick={recharger}>Réessayer</button>
              </div>
            ) : facturesFiltrees.length === 0 ? (
              <div className={styles.vide}>
                <i className="ti ti-file-off" aria-hidden="true" />
                <span>Aucune facture trouvée</span>
                <p className={styles.aideListeVide}>{factures.length === 0
                  ? 'Aucune facture enregistrée pour cet exercice.'
                  : 'Aucune facture ne correspond aux critères sélectionnés. Modifiez la recherche, le type, le statut ou la période.'}</p>
                {filtresActifs
                  ? <button type="button" className={styles.btnSec} onClick={reinitialiserFiltres}>Afficher toutes les factures de cet exercice</button>
                  : peutModifier && factures.length === 0 && <button type="button" className={styles.btnPrim} onClick={() => setShowForm(true)}>Créer une première facture</button>}
              </div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>N° Facture</th>
                      <th>Type</th>
                      <th>Date</th>
                      <th>Tiers</th>
                      <th>Articles</th>
                      <th style={{ textAlign: 'right' }}>HT</th>
                      <th style={{ textAlign: 'right' }}>TVA</th>
                      <th style={{ textAlign: 'right' }}>TTC</th>
                      <th>Statut</th>
                      <th>Échéance</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {facturesFiltrees.map(f => (<React.Fragment key={f.id}>
                      <tr
                        className={factureOuv?.id === f.id ? styles.rowSelected : ''}
                        onClick={() => setFactureOuv(factureOuv?.id === f.id ? null : f)}>
                        <td>
                          <span className={styles.numFact}>{f.numero || `Brouillon #${f.id}`}</span>
                          {f.est_proforma && (
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 3,
                              background: '#FFFBEB', color: '#854F0B', marginLeft: 6, letterSpacing: 0.3 }}>
                              PROFORMA
                            </span>
                          )}
                          {!f.est_proforma && !f.est_validee && (
                            <span style={{ fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 3,
                              background: '#E6F1FB', color: '#185FA5', marginLeft: 6, letterSpacing: 0.3 }}>
                              BROUILLON
                            </span>
                          )}
                        </td>
                        <td><BadgeType type={f.type} /></td>
                        <td className={styles.tdDate}>{formatDate(f.date)}</td>
                        <td><strong>{f.tiers}</strong>{f.montants_valides === false ? <div style={{ color: 'var(--red)', fontSize: 11 }}>Montants à vérifier</div> : f.ras_anomalie && <div style={{ color: 'var(--red)', fontSize: 11 }} title={f.ras_anomalie}>RAS à vérifier</div>}</td>
                        <td>
                          <div className={styles.articlesCell}>
                            {(f.lignes || []).slice(0, 2).map((l, i) => (
                              <span key={i} className={styles.articleTag}>
                                <span style={{ fontWeight: 600, color: 'var(--blue)', marginRight: 3 }}>
                                  {l.quantite == null ? 'À vérifier' : parseFloat(l.quantite) % 1 === 0 ? parseInt(l.quantite) : l.quantite}×
                                </span>
                                {l.description}
                              </span>
                            ))}
                            {(f.lignes || []).length > 2 && (
                              <span className={styles.articleMore}>
                                +{f.lignes.length - 2} article{f.lignes.length - 2 > 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                        </td>
                        <td style={{ textAlign: 'right' }}>{formatMAD(f.total_ht)}</td>
                        <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>{formatMAD(f.total_tva)}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatMAD(f.total_ttc)}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
                              <span className={styles.badge} style={f.est_validee
                                ? { background: '#EAF3DE', color: '#3B6D11' }
                                : { background: '#F0EFED', color: '#5A5955' }}
                                title="État de validation">{f.est_validee ? 'Validée' : 'Brouillon'}</span>
                              <span title="État de paiement"><BadgeStatut facture={f} /></span>
                              {f.statut === 'payee' && Number(f.total_reglement_en_cours || 0) > 0 && (
                                <span title={`${formatMAD(f.total_reglement_en_cours)} MAD réglés par chèque/effet non encore encaissé`} style={{
                                  fontSize: 9, padding: '2px 6px', borderRadius: 100, background: '#E6F1FB', color: '#185FA5'
                                }}>Encaissement en cours</span>
                              )}
                              {f.statut_credit && f.statut_credit !== 'aucun' && (
                                <span title={`${formatMAD(f.total_avoirs || 0)} MAD d'avoirs actifs`} style={{
                                  fontSize: 9, padding: '2px 6px', borderRadius: 100,
                                  background: f.statut_credit === 'totalement_creditee' ? '#FCEBEB' : '#FAEEDA',
                                  color: f.statut_credit === 'totalement_creditee' ? '#A32D2D' : '#854F0B',
                                }}>
                                  {f.statut_credit === 'totalement_creditee' ? 'Créditée' : 'Crédit partiel'}
                                </span>
                              )}
                            </div>
                            <BadgeCompta estComptabilisee={f.est_comptabilisee} />
                          </div>
                        </td>
                        <td><BadgeEcheance facture={f} /></td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            {f.type === 'achat' && (
                              <button className={styles.btnAction}
                                onClick={e => { e.stopPropagation(); setPjOuverte(pjOuverte === f.id ? null : f.id) }}
                                title="Pièces jointes"
                                style={{ color: pjOuverte === f.id ? 'var(--blue)' : '' }}><i className="ti ti-paperclip" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Pièces jointes</span></button>
                            )}
                            {peutModifier && <>
                            {f.type === 'vente' && f.est_validee && (
                              <button className={styles.btnAction}
                                onClick={e => { e.stopPropagation(); setBlDateModal(f) }}
                                title="Créer bon de livraison"
                                disabled={creationBL === f.id || f.montants_valides === false}
                                style={{ color: 'var(--blue)' }}>
                                <i className={`ti ${creationBL === f.id ? 'ti-loader-2 ti-spin' : 'ti-truck-delivery'}`} aria-hidden="true" />
                              </button>
                            )}
                            {f.statut !== 'payee' && f.statut !== 'annulee' && !f.est_proforma && f.est_validee && (
                              <button className={styles.btnAction}
                                onClick={e => { e.stopPropagation(); setFactureEncaisser(f) }}
                                title={f.type === 'achat' ? 'Payer le fournisseur' : 'Encaisser le client'}
                                disabled={f.montants_valides === false}
                                style={{ color: 'var(--green)' }}><i className="ti ti-cash" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">{f.type === 'achat' ? 'Payer le fournisseur' : 'Encaisser le client'}</span></button>
                            )}
                            {f.est_proforma && (
                              <button className={styles.btnAction} style={{ color: 'var(--green)' }}
                                onClick={async e => {
                                  e.stopPropagation()
                                  if (!confirm(`Convertir la proforma ${f.numero} en facture définitive ?\nUn numéro définitif sera attribué et le stock sera mouvementé.`)) return
                                  try {
                                    const token = localStorage.getItem('hisabpro_token')
                                    const res = await fetch(`${API_BASE}/api/factures/${f.id}/convertir-definitive`, {
                                      method: 'POST', headers: { Authorization: `Bearer ${token}` },
                                    })
                                    const data = await res.json()
                                    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Erreur')
                                    notifier(data.message)
                                    recharger()
                                  } catch (err) { notifier.erreur(err.message) }
                                }}
                                disabled={f.montants_valides === false}
                                title="Convertir en facture définitive"><i className="ti ti-file-check" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Convertir en facture définitive</span></button>
                            )}
                            <button className={styles.btnAction}
                              onClick={e => {
                                e.stopPropagation()
                                // Duplication : mêmes données, nouveau numéro (auto), date du jour
                                setInitialFacture({
                                  type: f.type,
                                  tiers: f.tiers,
                                  reference: f.reference || '',
                                  escompte: f.escompte || 0,
                                  frais_transport_ht: f.frais_transport_ht || 0,
                                  frais_transport_tva: f.frais_transport_tva ?? 20,
                                  frais_emballage_ht: f.frais_emballage_ht || 0,
                                  frais_emballage_tva: f.frais_emballage_tva ?? 20,
                                  ras_taux: f.ras_taux || 0,
                                  lignes: (f.lignes || []).map(l => ({
                                    description: l.description, quantite: l.quantite,
                                    prix_unitaire: l.prix_unitaire, tva: l.tva, remise: l.remise || 0,
                                  })),
                                })
                                setShowForm(true)
                              }}
                              disabled={Boolean(f.ras_anomalie) || f.montants_valides === false}
                              title={f.ras_anomalie ? 'RAS historique invalide : vérifier avant duplication' : 'Dupliquer la facture'}><i className="ti ti-copy" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Dupliquer</span></button>
                            {(!f.est_validee || f.est_proforma) && (
                              <button className={styles.btnAction}
                                onClick={e => { e.stopPropagation(); setFactureEdit(f) }}
                                disabled={f.montants_valides === false}
                                title={f.est_proforma ? 'Modifier la proforma' : 'Modifier le brouillon'}><i className="ti ti-pencil" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">{f.est_proforma ? 'Modifier la proforma' : 'Modifier le brouillon'}</span></button>
                            )}
                            {!f.est_proforma && !f.est_validee && (
                              <button className={styles.btnAction}
                                onClick={async e => {
                                  e.stopPropagation()
                                  if (!confirm(`Valider définitivement le brouillon #${f.id} ?\nLe numéro sera attribué et la facture deviendra non modifiable.`)) return
                                  try {
                                    const validation = await validerFacture(f.id)
                                    setAvertissementsMentions(validation?.avertissements_mentions || [])
                                    await recharger()
                                  } catch (err) { notifier.erreur(err.message) }
                                }}
                                disabled={f.montants_valides === false}
                                title="Valider définitivement" style={{ color: 'var(--green)' }}><i className="ti ti-circle-check" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Valider définitivement</span></button>
                            )}
                            {!f.est_comptabilisee && !f.est_proforma && f.est_validee && (
                              <button className={styles.btnAction}
                                onClick={e => { e.stopPropagation(); comptabiliserMaintenant(f) }}
                                disabled={comptaEnCours === f.id || f.montants_valides === false}
                                title="Générer l'écriture comptable de cette facture"
                                style={{ color: 'var(--blue)' }}><i className="ti ti-book-upload" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Générer l'écriture comptable de cette facture</span></button>
                            )}
                            {(f.est_validee && !f.est_proforma) ? (
                              <button className={styles.btnTrash} disabled
                                title="Facture validée : correction uniquement par avoir/document correctif"
                                style={{ opacity: 0.3, cursor: 'not-allowed' }}
                                onClick={e => e.stopPropagation()}
                                aria-label="Suppression impossible (validée)"><i className="ti ti-trash-off" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Facture validée</span></button>
                            ) : (
                              <button className={styles.btnTrash}
                                onClick={e => {
                                  e.stopPropagation()
                                  if (!confirm(`Supprimer ${f.numero || `le brouillon #${f.id}`} ?`)) return
                                  supprimerFacture(f.id).catch(err => notifier.erreur(err.message))
                                }}
                                aria-label="Supprimer">
                                <i className="ti ti-trash" aria-hidden="true" />
                              </button>
                            )}
                            </>}
                          </div>
                        </td>
                      </tr>
                      {pjOuverte === f.id && (
                        <tr>
                          <td colSpan={11} style={{ background: '#FAFAFA', padding: '12px 20px', borderBottom: '0.5px solid var(--border-light)' }}>
                            <PiecesJointes docType="facture" docId={f.id} readOnly={!peutModifier} />
                          </td>
                        </tr>
                      )}
                      </React.Fragment>))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
