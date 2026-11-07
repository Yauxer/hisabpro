import { statutPaiementAffiche } from '../utils/statutPaiement.js'
import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import PiecesJointes from '../components/PiecesJointes.jsx'
import ReglementParTiers from '../components/ReglementParTiers.jsx'
import RasTvaReglement from '../components/RasTvaReglement.jsx'
import { useNavigate } from 'react-router-dom'
import { formatMAD as formatMADBase, formatDate } from '../data/donnees.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useFactures } from '../data/FacturesContext.jsx'
import Modal from '../components/Modal.jsx'
import TiersPicker from '../components/TiersPicker.jsx'
import { FormSection, AdvancedSection, InlineNotice, ActionBar } from '../components/FormUX.jsx'
import { FormulaireAvoir, ResumeRASSituation } from './Factures.jsx'
import styles from './Commercial.module.css'
import { API_BASE, peutEcrire, facturesAPI } from '../services/api.js'
import { telechargerDocumentPDF, preparerEmailDocument } from '../services/documentsCommerciaux.js'
import { dateLocaleISO, entierOuDefaut, nombreOuDefaut } from '../utils/formUtils.js'
import { QUALIFICATIONS_TVA, tauxTVAAvecHistorique, tvaEffective, qualificationParDefautPourTaux } from '../utils/tvaUtils.js'
import { nombreArticleSaisie, nombreSaisieConnu, qualificationArticle, montantArticle, montantLignesSaisies } from '../utils/articlesNombres.js'
import { notifier } from '../services/notifications.js'

const API = API_BASE
const formatMAD = valeur => valeur != null && valeur !== '' && Number.isFinite(Number(valeur)) ? formatMADBase(valeur) : 'À vérifier'
const TOKEN = () => localStorage.getItem('hisabpro_token')

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: {
      Authorization: `Bearer ${TOKEN()}`,
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Erreur' }))
    const detail = err.detail
    const msg = Array.isArray(detail)
      ? detail.map(e => e.msg || JSON.stringify(e)).join(', ')
      : (typeof detail === 'string' ? detail : 'Erreur')
    throw new Error(msg)
  }
  if (res.status === 204) return null
  return res.json()
}

// Une erreur de lecture n'est pas un dossier vide. Les réponses d'un ancien
// exercice, cycle ou jeton ne doivent pas remplacer la liste courante.
function useListeCommerciale(url, typeForce = null, urlAssociee = null) {
  const jeton = TOKEN()
  const cle = JSON.stringify([url, typeForce, urlAssociee, jeton])
  const generation = useRef(0)
  const actif = useRef(false)
  const [etat, setEtat] = useState({ cle: null, lignes: [], associees: [], loading: true, erreur: '' })
  const charger = useCallback(async () => {
    if (!actif.current || TOKEN() !== jeton) return
    const requete = ++generation.current
    const courant = () => actif.current && generation.current === requete && TOKEN() === jeton
    setEtat({ cle, lignes: [], associees: [], loading: true, erreur: '' })
    try {
      const lire = chemin => chemin.startsWith('/api/factures?')
        ? facturesAPI.listerTout(new URLSearchParams(chemin.split('?')[1]).get('exercice'))
        : apiFetch(chemin)
      const [lignes, associees] = await Promise.all([
        lire(url), urlAssociee ? lire(urlAssociee) : Promise.resolve([]),
      ])
      if (courant()) setEtat({ cle,
        lignes: typeForce ? lignes.filter(ligne => ligne.type === typeForce) : lignes,
        associees, loading: false, erreur: '' })
    } catch {
      if (courant()) setEtat({ cle, lignes: [], associees: [], loading: false,
        erreur: 'Chargement impossible. La liste est indisponible ; réessayez après rétablissement du service.' })
    }
  }, [url, typeForce, urlAssociee, jeton, cle])
  useEffect(() => {
    actif.current = true
    charger()
    return () => { actif.current = false; generation.current++ }
  }, [charger])
  return { lignes: etat.cle === cle ? etat.lignes : [],
    associees: etat.cle === cle ? etat.associees : [],
    loading: etat.cle !== cle || etat.loading,
    erreurLecture: etat.cle === cle ? etat.erreur : '', charger }
}

function ErreurListeCommerciale({ message, charger }) {
  return <div className={styles.vide} role="alert">
    <InlineNotice tone="danger">{message}</InlineNotice>
    <button type="button" className={styles.btnSec} onClick={charger}>Réessayer</button>
  </div>
}

async function telechargerPDF(url, nomFichier) {
  return telechargerDocumentPDF(url, nomFichier)
}

const MODES_REGLEMENT = ['virement', 'cheque', 'especes', 'effet', 'carte', 'prelevement', 'autre']

// ── Badges ────────────────────────────────────────────────────────────────────

const STATUT_DEVIS = {
  brouillon: { label: 'Brouillon', bg: '#F0EFED', color: '#5A5955' },
  envoye:    { label: 'Envoyé',    bg: '#FAEEDA', color: '#854F0B' },
  accepte:   { label: 'Accepté',  bg: '#EAF3DE', color: '#3B6D11' },
  converti:  { label: 'Converti', bg: '#E6F1FB', color: '#185FA5' },
  refuse:    { label: 'Refusé',   bg: '#FCEBEB', color: '#A32D2D' },
  expire:    { label: 'Expiré',   bg: '#F0EFED', color: '#888' },
}

const STATUT_BC = {
  en_attente: { label: 'En attente', bg: '#FAEEDA', color: '#854F0B' },
  confirme:   { label: 'Confirmé',   bg: '#EAF3DE', color: '#3B6D11' },
  partiel:    { label: 'Partiel',    bg: '#FFF4CC', color: '#854F0B' },
  livre:      { label: 'Livré',      bg: '#E6F1FB', color: '#185FA5' },
  facture:    { label: 'Facturé',    bg: '#EAF3DE', color: '#185FA5' },
  annule:     { label: 'Annulé',     bg: '#FCEBEB', color: '#A32D2D' },
}

const STATUT_BR = {
  en_preparation: { label: 'En attente',    bg: '#FAEEDA', color: '#854F0B' },
  expedie:        { label: 'En cours',       bg: '#E6F1FB', color: '#185FA5' },
  livre:          { label: 'Réceptionné',    bg: '#EAF3DE', color: '#3B6D11' },
  retourne:       { label: 'Retour fournisseur', bg: '#FCEBEB', color: '#A32D2D' },
}

const STATUT_BL = {
  en_preparation: { label: 'En préparation', bg: '#FAEEDA', color: '#854F0B' },
  expedie:        { label: 'Expédié',         bg: '#E6F1FB', color: '#185FA5' },
  livre:          { label: 'Livré',           bg: '#EAF3DE', color: '#3B6D11' },
  retourne:       { label: 'Retourné',        bg: '#FCEBEB', color: '#A32D2D' },
}

// ── Calcul retard livraison BC ────────────────────────────────────────────────
function infosRetardLivraison(bc) {
  if (!bc.date_livraison) return null
  const dateLivraison = new Date(bc.date_livraison + 'T00:00:00')
  const aujourd_hui = new Date(); aujourd_hui.setHours(0,0,0,0)
  const joursEcart = Math.floor((aujourd_hui - dateLivraison) / (1000 * 60 * 60 * 24))
  return { dateLivraison, joursEcart } // positif = en retard, négatif = pas encore échu
}

function Badge({ statut, map }) {
  const c = map[statut] || { label: statut, bg: '#eee', color: '#666' }
  return (
    <span style={{
      fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 100,
      background: c.bg, color: c.color,
    }}>
      {c.label}
    </span>
  )
}

// Un devis brouillon/envoyé dont la date de validité est dépassée est "en réalité"
// expiré, même si personne n'a cliqué sur le statut "Expiré" pour l'acter.
function estDevisDepasse(d) {
  if (!d || (d.statut !== 'brouillon' && d.statut !== 'envoye')) return false
  if (!d.date) return false
  const [y, m, j] = d.date.split('-').map(Number)
  const exp = new Date(y, m - 1, j)
  exp.setDate(exp.getDate() + (d.validite_jours || 30))
  return exp < new Date()
}

// ── Autocomplete tiers ────────────────────────────────────────────────────────

function ChampTiers({ value, onChange, onSelect, placeholder = 'Client ou fournisseur...', type = 'tous' }) {
  return (
    <TiersPicker
      value={value}
      onChange={onChange}
      onSelect={onSelect}
      placeholder={placeholder}
      type={type}
    />
  )
}

// ── Autocomplete articles ────────────────────────────────────────────────────

function ChampArticle({ value, onChange, onSelect, typeDoc = 'vente' }) {
  const [ouvert, setOuvert] = useState(false)
  const jeton = TOKEN()
  const [etat, setEtat] = useState({ jeton: null, liste: [], loading: true, erreur: '' })
  const generation = useRef(0), actif = useRef(false)
  const ref = useRef(null)

  const charger = useCallback(async () => {
    if (!actif.current || TOKEN() !== jeton) return
    const n = ++generation.current
    const courant = () => actif.current && generation.current === n && TOKEN() === jeton
    setEtat({ jeton, liste: [], loading: true, erreur: '' })
    try {
      const liste = await apiFetch('/api/articles')
      if (!Array.isArray(liste)) throw new Error('Catalogue illisible')
      if (courant()) setEtat({ jeton, liste, loading: false, erreur: '' })
    } catch {
      if (courant()) setEtat({ jeton, liste: [], loading: false,
        erreur: 'Catalogue indisponible. La saisie libre reste possible.' })
    }
  }, [jeton])
  useEffect(() => {
    actif.current = true
    charger()
    return () => { actif.current = false; generation.current++ }
  }, [charger])

  useEffect(() => {
    function clickDehors(e) {
      if (ref.current && !ref.current.contains(e.target)) setOuvert(false)
    }
    document.addEventListener('mousedown', clickDehors)
    return () => document.removeEventListener('mousedown', clickDehors)
  }, [])

  const loading = etat.jeton !== jeton || etat.loading
  const erreur = etat.jeton === jeton ? etat.erreur : ''
  const liste = etat.jeton === jeton ? etat.liste : []
  const affich = useMemo(() => {
    const q = (value || '').trim().toLowerCase()
    return liste.filter(a => a.designation.toLowerCase().includes(q) || a.code.toLowerCase().includes(q))
      .sort((a, b) => a.designation.localeCompare(b.designation, 'fr'))
  }, [liste, value])

  function handleChange(val) {
    onChange(val)
    setOuvert(true)
  }

  function handleFocus() {
    setOuvert(true)
  }

  function choisir(article) {
    if (TOKEN() !== jeton || loading || erreur) return
    onChange(article.designation)
    onSelect(article)
    setOuvert(false)
  }

  return (
    <div style={{ position: 'relative' }} ref={ref}>
      <input className={styles.inputSm} type="text" placeholder="Article ou description..."
        value={value}
        onChange={e => handleChange(e.target.value)}
        onFocus={handleFocus} />
      {ouvert && (loading || erreur || affich.length === 0) && <div style={{
        position: 'absolute', top: 'calc(100% + 2px)', left: 0, right: 0, minWidth: 260,
        background: 'var(--bg-primary)', border: '0.5px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)', zIndex: 300, padding: 12, fontSize: 12,
        boxShadow: '0 6px 20px rgba(0,0,0,0.12)',
      }}>
        {loading ? <p role="status">Chargement du catalogue…</p> : erreur ? <div role="alert">
          <p>{erreur}</p>
          <button type="button" className={styles.btnSec} onClick={charger}>Réessayer le catalogue</button>
        </div> : <p role="status">{liste.length === 0 ? 'Aucun article disponible.' : 'Aucun article ne correspond à la recherche.'} Vous pouvez saisir une description libre.</p>}
      </div>}
      {ouvert && !loading && !erreur && affich.length > 0 && (
        <ul style={{
          position: 'absolute', top: 'calc(100% + 2px)', left: 0, right: 0, minWidth: 260,
          background: 'var(--bg-primary)', border: '0.5px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)', zIndex: 300, listStyle: 'none',
          boxShadow: '0 6px 20px rgba(0,0,0,0.12)',
          maxHeight: 280, overflowY: 'auto',
        }}>
          {affich.map(a => (
            <li key={a.id}
              onMouseDown={() => choisir(a)}
              style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 12, display: 'flex', gap: 8, alignItems: 'center' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-secondary)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}>
              <span style={{ flex: 1 }}>{a.designation}</span>
              {a.famille && (
                <span style={{ fontSize: 10, background: 'var(--bg-secondary)', color: 'var(--text-tertiary)', padding: '1px 5px', borderRadius: 3 }}>
                  {a.famille.libelle}
                </span>
              )}
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--blue)', flexShrink: 0 }}>
                {montantArticle(typeDoc === 'achat' ? a.prix_achat_ht : a.prix_vente_ht, formatMAD)} MAD
              </span>
              {a.is_stockable === true && a.stock_actuel !== null && a.stock_actuel !== undefined && (
                <span style={{
                  fontSize: 10, padding: '1px 5px', borderRadius: 3, flexShrink: 0,
                  background: a.stock_actuel <= 0 ? '#FCEBEB' : '#EAF3DE',
                  color: a.stock_actuel <= 0 ? 'var(--red)' : 'var(--green)',
                }}>
                  {a.stock_actuel <= 0 ? 'Rupture' : `${a.stock_actuel} ${a.unite || ''}`}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Lignes génériques ─────────────────────────────────────────────────────────

function TableLignes({ lignes, onChange, avecTVA = false, typeDoc = 'vente', dateDoc = dateLocaleISO() }) {
  function majLigne(i, champ, val) {
    onChange(lignes.map((l, idx) => idx === i ? { ...l, [champ]: val } : l))
  }
  function ajouterLigne() {
    onChange([...lignes, { description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, remise2: 0, rabais: 0, article_id: null, stock_actuel: null, unite: 'unité' }])
  }
  function supprimerLigne(i) {
    if (lignes.length <= 1) return
    onChange(lignes.filter((_, idx) => idx !== i))
  }

  return (
    <div className="hp-commercial-line-editor">
      <div className={styles.lignesHeader}>
        <span className={styles.lignesTitle}>Lignes</span>
        <button className={styles.btnAjout} onClick={ajouterLigne}>
          <i className="ti ti-plus" /> Ajouter
        </button>
      </div>
      <div className={styles.lignesColHeaders} style={{
        gridTemplateColumns: avecTVA ? '1fr 70px 100px 70px 90px 28px' : '1fr 70px 100px 90px 28px'
      }}>
        <span>Description</span>
        <span style={{ textAlign: 'right' }}>Qté</span>
        <span style={{ textAlign: 'right' }}>P.U. HT</span>
        {avecTVA && <span style={{ textAlign: 'right' }}>TVA</span>}
        <span style={{ textAlign: 'right' }}>Total HT</span>
        <span />
      </div>
      {lignes.map((l, i) => (
        <div key={i} className={`${styles.ligneRow} ${avecTVA ? styles.ligneAvecTVA : ''}`} style={{
          gridTemplateColumns: avecTVA ? '1fr 70px 100px 70px 90px 28px' : '1fr 70px 100px 90px 28px'
        }}>
          <ChampArticle
            value={l.description}
            typeDoc={typeDoc}
            onChange={val => onChange(lignes.map((lg, idx) => idx === i ? { ...lg, description: val, article_id: null, stock_actuel: null } : lg))}
            onSelect={art => {
              const prix = typeDoc === 'achat' ? art.prix_achat_ht : art.prix_vente_ht
              onChange(lignes.map((lg, idx) => idx === i ? {
                ...lg,
                description: art.designation,
                article_id: art.id,
                prix_unitaire: nombreArticleSaisie(prix),
                tva: nombreArticleSaisie(art.tva),
                qualification_tva: qualificationArticle(art.tva),
                stock_actuel: art.stock_actuel ?? null,
                is_stockable: art.is_stockable === true,
                unite: art.unite || 'unité',
              } : lg))
            }}
          />
          <label className={styles.champLigneMobile}><span>Quantité</span>
            <input className={`${styles.inputSm} ${styles.num}`} type="number" min="0.0001" step="0.01"
              value={l.quantite} onChange={e => majLigne(i, 'quantite', e.target.value)} />
          </label>
          <label className={styles.champLigneMobile}><span>Prix unitaire HT</span>
            <input className={`${styles.inputSm} ${styles.num}`} type="number" min="0" step="0.01"
              value={l.prix_unitaire} onChange={e => majLigne(i, 'prix_unitaire', e.target.value)} />
          </label>
          {avecTVA && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <select className={styles.inputSm} value={l.tva}
                onChange={e => {
                  const taux = Number(e.target.value)
                  onChange(lignes.map((ligne, index) => index === i ? {
                    ...ligne, tva: e.target.value,
                    qualification_tva: e.target.value === '' ? '' : qualificationParDefautPourTaux(taux, l.qualification_tva),
                  } : ligne))
                }}>
                <option value="">À vérifier</option>
                {tauxTVAAvecHistorique(dateDoc, l.tva).map(t => <option key={t} value={t}>{t}%</option>)}
              </select>
              {nombreSaisieConnu(l.tva) && Number(l.tva) === 0 && <select className={styles.inputSm} value={l.qualification_tva || 'exonere_sans_deduction'} onChange={e => majLigne(i, 'qualification_tva', e.target.value)} title="Qualification du 0 %">
                {QUALIFICATIONS_TVA.filter(q => q.value !== 'taxable').map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
              </select>}
            </div>
          )}
          <span className={`${styles.inputSm} ${styles.num}`}
            style={{ border: 'none', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontWeight: 500 }}>
            {nombreSaisieConnu(l.prix_unitaire) ? formatMAD((parseFloat(l.quantite) || 0) * Number(l.prix_unitaire)) : 'À vérifier'}
          </span>
          <button className={styles.btnSuppr} onClick={() => supprimerLigne(i)} disabled={lignes.length <= 1}>
            <i className="ti ti-trash" />
          </button>
        </div>
      ))}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// FORMULAIRES
// ═══════════════════════════════════════════════════════════════════════════════

function DiagnosticStockDevis({ lignes }) {
  const { annee } = useExercice()
  const [revision, setRevision] = useState(0)
  const [lecture, setLecture] = useState(null)
  const payload = JSON.stringify(lignes.map(l => ({ article_id: l.article_id || null, quantite: Number(l.quantite) })))
  const cle = `${annee}:${revision}:${payload}`
  const rattache = lignes.some(l => l.article_id)
  const valide = lignes.every(l => Number.isFinite(Number(l.quantite)) && Number(l.quantite) >= 0)
  useEffect(() => {
    if (!rattache || !valide) return
    let actif = true
    const controller = new AbortController()
    const timer = setTimeout(() => {
      setLecture({ cle, loading: true })
      apiFetch('/api/devis/diagnostic-stock', { method: 'POST', body: JSON.stringify({ lignes: JSON.parse(payload) }), signal: controller.signal })
        .then(resultat => { if (actif) setLecture({ cle, resultat }) })
        .catch(e => { if (actif && e.name !== 'AbortError') setLecture({ cle, erreur: e.message }) })
    }, 250)
    return () => { actif = false; clearTimeout(timer); controller.abort() }
  }, [cle, payload, rattache, valide])
  if (!rattache) return null
  const courant = lecture?.cle === cle ? lecture : null
  const resultat = courant?.resultat
  const quantite = value => typeof value === 'string' ? value : value === null || value === undefined ? 'Non renseigné' : value.toLocaleString('fr-MA', { maximumSignificantDigits: 17 })
  return (
    <section className={styles.stockDiagnostic} aria-label="Stock indicatif" aria-live="polite">
      <div className={styles.stockDiagnosticHeader}>
        <strong><i className="ti ti-package" /> Stock indicatif</strong>
        <button type="button" className={styles.btnSec} onClick={() => setRevision(v => v + 1)} disabled={!valide || courant?.loading}>Actualiser le stock</button>
      </div>
      <p>Le devis reste autorisé, même en rupture. Cette lecture du stock physique ne réserve aucune quantité.</p>
      {!valide ? <p>Quantités à vérifier : le stock ne peut pas être évalué pour cette saisie.</p>
        : courant?.erreur ? <p role="alert">Lecture du stock indisponible : {courant.erreur}. Vous pouvez enregistrer le devis.</p>
        : !resultat ? <p>Vérification du stock en cours…</p>
        : <>
          <ul>
            {resultat.articles.map(a => (
              <li key={a.article_id} className={a.statut === 'a_approvisionner' || a.statut === 'inconnu' ? styles.stockDiagnosticWarning : ''}>
                <strong>{a.designation || `Article ${a.article_id}`}</strong>
                {a.statut === 'non_stockable' ? <span>Non stockable — aucun contrôle de rupture.</span>
                  : a.statut === 'inconnu' ? <span>Stock inconnu — à vérifier.</span>
                  : <span>{a.statut === 'a_approvisionner' ? 'À approvisionner' : 'Disponible'} · Demandé : {quantite(a.quantite_demandee)} · Stock physique : {quantite(a.stock_disponible)} · Manquant : {quantite(a.quantite_manquante)} {a.unite || ''}</span>}
                {a.diagnostics.map((d, i) => <small key={i}>{d}</small>)}
              </li>
            ))}
          </ul>
          {resultat.lignes_non_rattachees.length > 0 && <p>Les lignes sans article rattaché ne font pas l'objet d'un contrôle de stock.</p>}
          <small>Constaté le {new Date(resultat.constate_le).toLocaleString('fr-MA')} · Stock actuel de la société, sans réservation.</small>
        </>}
    </section>
  )
}

function FormulaireDevis({ onFermer, onSuccess }) {
  const { annee } = useExercice()
  const [form, setForm] = useState({
    numero: '', date: dateLocaleISO(),
    tiers: '', tiers_id: null, reference: '', validite_jours: 30, notes: '',
  })
  // Numérotation automatique séquentielle
  useEffect(() => {
    apiFetch(`/api/societe/prochain-numero?type_doc=devis&exercice=${annee}`)
      .then(d => setForm(p => p.numero ? p : { ...p, numero: d.numero }))
      .catch(() => setForm(p => p.numero ? p : { ...p, numero: `DV-${annee}-001` }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const [lignes, setLignes] = useState([{ description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, remise2: 0, rabais: 0, article_id: null, stock_actuel: null, unite: 'unité' }])
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  const totaux = useMemo(() => {
    let ht = 0, tva = 0
    lignes.forEach(l => {
      const h = (parseFloat(l.quantite) || 0) * (parseFloat(l.prix_unitaire) || 0)
      ht += h; tva += h * (tvaEffective(l) / 100)
    })
    return { ht, tva, ttc: ht + tva }
  }, [lignes])

  async function handleSave() {
    if (!form.tiers.trim())  { setErreur('Le client est obligatoire'); return }
    const lignesActives = lignes.filter(l => l.description.trim())
    if (!lignesActives.length) { setErreur('Ajoutez au moins une ligne avec un article'); return }
    if (lignesActives.some(l => !nombreSaisieConnu(l.prix_unitaire) || !nombreSaisieConnu(l.tva) || Number(l.tva) > 100)) { setErreur('Renseignez un prix unitaire et un taux de TVA connus, finis et non négatifs sur chaque ligne.'); return }
    if (lignesActives.some(l => nombreOuDefaut(l.quantite, 0) <= 0)) { setErreur('La quantité doit être strictement positive sur chaque ligne.'); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch('/api/devis', {
        method: 'POST',
        body: JSON.stringify({ ...form, numero: null, validite_jours: entierOuDefaut(form.validite_jours, 30), lignes: lignesActives }),
      })
      onSuccess(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouveau devis" icone="ti-file-description" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>
        <FormSection icon="ti-file-description" title="Informations du devis" description="Renseignez le client et la durée de validité ; le numéro définitif est géré automatiquement.">
        <div className={styles.formGrid3}>
          <div className={styles.formGroup}>
            <label className={styles.label}>N° Devis</label>
            <input className={styles.input} value={form.numero || 'Attribué à l’enregistrement'} readOnly />
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Aperçu uniquement · réservation définitive côté serveur</span>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date</label>
            <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Validité (jours)</label>
            <input className={styles.input} type="number" min="1" value={form.validite_jours}
              onChange={e => setForm(p => ({ ...p, validite_jours: e.target.value }))} />
          </div>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label}>Client *</label>
          <ChampTiers value={form.tiers}
            onChange={v => setForm(p => ({ ...p, tiers: v }))}
            onSelect={t => setForm(p => ({ ...p, tiers_id: t?.id || null }))}
            placeholder="Nom du client..." type="client" />
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label}>Référence</label>
          <input className={styles.input} value={form.reference} onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} />
        </div>
        </FormSection>
        <FormSection icon="ti-list-details" title="Articles & prix" description="Ajoutez les lignes proposées au client.">
        <TableLignes lignes={lignes} onChange={setLignes} avecTVA typeDoc="vente" dateDoc={form.date} />
        <div className={styles.totaux}>
          <div className={styles.totauxLigne}><span>Total HT</span><span>{montantLignesSaisies(totaux.ht, lignes, formatMAD)} MAD</span></div>
          <div className={styles.totauxLigne}><span>TVA</span><span>{montantLignesSaisies(totaux.tva, lignes, formatMAD)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC</span><span>{montantLignesSaisies(totaux.ttc, lignes, formatMAD)} MAD</span></div>
        </div>
        </FormSection>
        <AdvancedSection title="Notes internes / commerciales" icon="ti-notes">
        {['effet', 'cheque'].includes(form.mode) && (
          <div className={styles.formGroup}>
            <label className={styles.label}>Échéance {form.mode === 'effet' ? '*' : '(chèque postdaté)'}</label>
            <input className={styles.input} type="date" min={form.date || undefined} value={form.date_echeance || ''}
              onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
          </div>
        )}
        <div className={styles.formGroup}>
          <label className={styles.label}>Notes</label>
          <textarea className={styles.textarea} rows={2} value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
        </div>
        </AdvancedSection>
        <DiagnosticStockDevis lignes={lignes} />
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <ActionBar hint="Le devis reste modifiable tant qu’il n’est pas transformé en commande.">
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={handleSave} disabled={!form.tiers.trim() || loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : 'Créer le devis'}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )
}

function FormulaireBonCommande({ onFermer, onSuccess, devisSource = null, typeInitial = 'vente' }) {
  const { annee } = useExercice()
  const [form, setForm] = useState({
    numero: '', type: typeInitial,
    date: dateLocaleISO(),
    tiers: devisSource?.tiers || '', tiers_id: devisSource?.tiers_id || null, reference: devisSource?.reference || '',
    date_livraison: '', notes: '',
    devis_id: devisSource?.id || null,
  })
  // Numérotation automatique séquentielle
  useEffect(() => {
    apiFetch(`/api/societe/prochain-numero?type_doc=bc&exercice=${annee}`)
      .then(d => setForm(p => p.numero ? p : { ...p, numero: d.numero }))
      .catch(() => setForm(p => p.numero ? p : { ...p, numero: `BC-${annee}-001` }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const [lignes, setLignes] = useState(
    devisSource?.lignes?.map(l => ({
      description: l.description, quantite: l.quantite, prix_unitaire: l.prix_unitaire,
      tva: l.tva ?? 20, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20), remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
      article_id: l.article_id || null, source_ligne_devis_id: l.id || null, stock_actuel: null, unite: 'unité',
    }))
    || [{ description: '', quantite: 1, prix_unitaire: 0, tva: 20, qualification_tva: 'taxable', remise: 0, remise2: 0, rabais: 0, article_id: null, stock_actuel: null, unite: 'unité' }]
  )
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  const totauxBC = useMemo(() => {
    let ht = 0, tva = 0
    lignes.forEach(l => {
      const h = (parseFloat(l.quantite) || 0) * (parseFloat(l.prix_unitaire) || 0)
      ht += h; tva += h * (tvaEffective(l) / 100)
    })
    return { ht, tva, ttc: ht + tva }
  }, [lignes])

  async function handleSave() {
    if (!form.tiers.trim())  { setErreur('Le tiers est obligatoire'); return }
    const lignesActives = lignes.filter(l => l.description.trim())
    if (!lignesActives.length) { setErreur('Ajoutez au moins une ligne avec un article'); return }
    if (lignesActives.some(l => !nombreSaisieConnu(l.prix_unitaire) || !nombreSaisieConnu(l.tva) || Number(l.tva) > 100)) { setErreur('Renseignez un prix unitaire et un taux de TVA connus, finis et non négatifs sur chaque ligne.'); return }
    if (lignesActives.some(l => nombreOuDefaut(l.quantite, 0) <= 0)) { setErreur('La quantité doit être strictement positive sur chaque ligne.'); return }
    if (form.date_livraison && form.date_livraison < form.date) { setErreur('La date de livraison souhaitée ne peut pas précéder la date de commande.'); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch('/api/bons-commande', {
        method: 'POST',
        body: JSON.stringify({ ...form, numero: null, date_livraison: form.date_livraison || null, lignes: lignesActives }),
      })
      onSuccess(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouveau bon de commande" icone="ti-clipboard-list" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>
        <FormSection icon="ti-clipboard-list" title="Commande" description="Définissez le type, le tiers et la date de livraison souhaitée.">
        {devisSource && (
          <div className={styles.sourceInfo}>
            <i className="ti ti-link" /> Issu du devis <strong>{devisSource.numero}</strong>
          </div>
        )}
        <div className={styles.formGrid4}>
          <div className={styles.formGroup}>
            <label className={styles.label}>N° BC</label>
            <input className={styles.input} value={form.numero || 'Attribué à l’enregistrement'} readOnly />
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Aperçu uniquement · réservation définitive côté serveur</span>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Type</label>
            <div className={styles.typeToggle}>
              {['vente', 'achat'].map(t => (
                <button key={t} className={`${styles.typeBtn} ${form.type === t ? styles.typeBtnActif : ''}`}
                  onClick={() => setForm(p => ({ ...p, type: t }))}>
                  {t === 'vente' ? 'Vente' : 'Achat'}
                </button>
              ))}
            </div>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date</label>
            <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date livraison souhaitée</label>
            <input className={styles.input} type="date" value={form.date_livraison} onChange={e => setForm(p => ({ ...p, date_livraison: e.target.value }))} />
          </div>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label}>{form.type === 'vente' ? 'Client *' : 'Fournisseur *'}</label>
          <ChampTiers value={form.tiers}
            onChange={v => setForm(p => ({ ...p, tiers: v }))}
            onSelect={t => setForm(p => ({ ...p, tiers_id: t?.id || null }))}
            placeholder={form.type === 'vente' ? 'Nom du client...' : 'Nom du fournisseur...'}
            type={form.type === 'vente' ? 'client' : 'fournisseur'} />
        </div>
        </FormSection>
        <FormSection icon="ti-list-details" title="Lignes de commande" description="Les quantités seront ensuite suivies jusqu’à la livraison/réception et la facturation.">
        <TableLignes lignes={lignes} onChange={setLignes} avecTVA typeDoc={form.type || 'vente'} dateDoc={form.date} />
        <div className={styles.totaux}>
          <div className={styles.totauxLigne}><span>Total HT</span><span>{montantLignesSaisies(totauxBC.ht, lignes, formatMAD)} MAD</span></div>
          <div className={styles.totauxLigne}><span>TVA</span><span>{montantLignesSaisies(totauxBC.tva, lignes, formatMAD)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC</span><span>{montantLignesSaisies(totauxBC.ttc, lignes, formatMAD)} MAD</span></div>
        </div>
        </FormSection>
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <AdvancedSection title="Notes de commande" icon="ti-notes">
          <div className={styles.formGroup}>
            <label className={styles.label}>Notes</label>
            <textarea className={styles.textarea} rows={2} value={form.notes}
              onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
          </div>
        </AdvancedSection>
        <ActionBar hint="La commande servira de référence aux livraisons/réceptions et aux factures partielles.">
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={handleSave} disabled={!form.tiers.trim() || loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : 'Créer la commande'}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )
}

function FormulaireReglement({ facture, onFermer, onSuccess }) {
  const [banques, setBanques] = useState([])
  const [situation, setSituation] = useState(null)
  const [loadingSituation, setLoadingSituation] = useState(!!facture?.id)
  useEffect(() => { apiFetch('/api/banques').then(setBanques).catch(() => {}) }, [])
  const [form, setForm] = useState({
    facture_id: facture?.id || null,
    tiers: facture?.tiers || '',
    date: dateLocaleISO(),
    montant: facture?.total_ttc || '',
    mode: facture?.mode_reglement_prevu || 'virement', reference: facture?.reference_reglement_prevue || '', banque: '', date_echeance: '', notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    if (!facture?.id) return
    let annule = false
    setSituation(null); setErreur('')
    setLoadingSituation(true)
    apiFetch(`/api/factures/${facture.id}/reglements`)
      .then(data => {
        if (annule) return
        setSituation(data)
        setForm(p => ({ ...p, montant: typeof data.solde_restant === 'number' && Number.isFinite(data.solde_restant) ? String(Math.max(data.solde_restant, 0)) : '' }))
      })
      .catch(e => { if (!annule) setErreur(e.message) })
      .finally(() => { if (!annule) setLoadingSituation(false) })
    return () => { annule = true }
  }, [facture?.id])

  async function handleSave() {
    if (facture?.id && (!situation || typeof situation.solde_restant !== 'number' || !Number.isFinite(situation.solde_restant))) {
      setErreur('Situation de paiement indisponible. Vérifiez les données avant tout règlement.'); return
    }
    const montant = nombreOuDefaut(form.montant, 0)
    if (montant <= 0) { setErreur('Le montant du règlement doit être strictement positif.'); return }
    if (situation && montant > nombreOuDefaut(situation.solde_restant, 0) + 0.01) {
      setErreur(`Le règlement dépasse le reste à payer (${formatMAD(situation.solde_restant)} MAD).`)
      return
    }
    if (!form.date) { setErreur('La date du règlement est obligatoire.'); return }
    if (form.mode === 'effet' && !form.date_echeance) { setErreur("La date d'échéance est obligatoire pour un effet de commerce."); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch('/api/reglements', { method: 'POST', body: JSON.stringify({ ...form, montant, date_echeance: form.date_echeance || null }) })
      onSuccess(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre="Enregistrer un règlement" icone="ti-coin" onFermer={onFermer} largeur="md">
      <div className={styles.formContenu}>
        <FormSection icon="ti-cash" title="Règlement" description="Le reste à payer est calculé automatiquement pour éviter tout sur-règlement.">
        {facture && (
          <div className={styles.sourceInfo}>
            <i className="ti ti-file-invoice" /> Facture <strong>{facture.numero}</strong> — {facture.tiers}
            <span style={{ marginLeft: 'auto', fontWeight: 600 }}>{formatMAD(facture.total_ttc)} MAD TTC</span>
          </div>
        )}
        {situation && (
          <div className={styles.sourceInfo} style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            <span>TTC <strong>{formatMAD(situation.total_ttc)} MAD</strong></span>
            <span>Déjà imputé <strong>{situation.solde_restant === null ? 'À vérifier' : `${formatMAD((situation.total_regle || 0) + (situation.total_avoirs || 0) + (situation.total_acomptes || 0) + (situation.montant_ras_impute || 0))} MAD`}</strong></span>
            <span>Reste à payer <strong>{situation.solde_restant === null ? 'À vérifier' : `${formatMAD(situation.solde_restant)} MAD`}</strong></span>
          </div>
        )}
        <ResumeRASSituation situation={situation} />
        <div className={styles.formGrid3}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date *</label>
            <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Montant *</label>
            <input className={styles.input} type="number" min="0.01" step="0.01"
              max={situation ? situation.solde_restant : undefined}
              value={form.montant} onChange={e => setForm(p => ({ ...p, montant: e.target.value }))} />
            {loadingSituation && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Calcul du solde…</span>}
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mode</label>
            <select className={styles.input} value={form.mode} onChange={e => setForm(p => ({ ...p, mode: e.target.value }))}>
              {MODES_REGLEMENT.map(m => <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>)}
            </select>
          </div>
        </div>
        {!facture && (
          <div className={styles.formGroup}>
            <label className={styles.label}>Tiers *</label>
            <ChampTiers value={form.tiers} onChange={v => setForm(p => ({ ...p, tiers: v }))} />
          </div>
        )}
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Référence (N° chèque, virement...)</label>
            <input className={styles.input} value={form.reference} onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Banque</label>
            {banques.length > 0 && ['virement', 'cheque', 'effet', 'carte', 'prelevement'].includes(form.mode) ? (
              <select className={styles.input} value={form.banque}
                onChange={e => setForm(p => ({ ...p, banque: e.target.value }))}>
                <option value="">— Choisir une banque —</option>
                {banques.map(b => (
                  <option key={b.id} value={b.banque}>{b.banque}{b.agence ? ` — ${b.agence}` : ''}</option>
                ))}
              </select>
            ) : (
              <input className={styles.input} placeholder="Nom de la banque..."
                value={form.banque} onChange={e => setForm(p => ({ ...p, banque: e.target.value }))} />
            )}
          </div>
        </div>
        {['effet', 'cheque'].includes(form.mode) && (
          <div className={styles.formGroup}>
            <label className={styles.label}>Échéance {form.mode === 'effet' ? '*' : '(chèque postdaté)'}</label>
            <input className={styles.input} type="date" min={form.date || undefined} value={form.date_echeance || ''}
              onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
          </div>
        )}
        <div className={styles.formGroup}>
          <label className={styles.label}>Notes</label>
          <textarea className={styles.textarea} rows={2} value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
        </div>
        </FormSection>
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <ActionBar hint={situation ? `Reste à payer : ${formatMAD(situation.solde_restant)} MAD` : 'Le règlement sera rattaché à la pièce sélectionnée.'}>
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={handleSave}
            disabled={nombreOuDefaut(form.montant, 0) <= 0 || loading || loadingSituation || (facture?.id && (!situation || situation.solde_restant === null)) || (situation && nombreOuDefaut(form.montant, 0) > nombreOuDefaut(situation.solde_restant, 0) + 0.01)}>
            <i className="ti ti-check" /> {loading ? 'Enregistrement...' : 'Enregistrer le règlement'}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )
}


// ─── Formulaire édition devis ─────────────────────────────────────────────────
function FormulaireEditionDevis({ devis, onFermer, onSuccess }) {
  const [form, setForm] = useState({
    numero: devis.numero || '',
    date: (devis.date || '').slice(0, 10),
    tiers: devis.tiers || '',
    tiers_id: devis.tiers_id || null,
    reference: devis.reference || '',
    validite_jours: devis.validite_jours || 30,
    statut: devis.statut || 'brouillon',
    notes: devis.notes || '',
  })
  const [lignes, setLignes] = useState(
    (devis.lignes || []).map(l => ({ description: l.description, quantite: l.quantite, prix_unitaire: l.prix_unitaire, tva: l.tva ?? 20, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20), remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0, article_id: l.article_id || null, stock_actuel: null, unite: 'unité' }))
  )
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  const totaux = useMemo(() => {
    let ht = 0, tva = 0
    lignes.forEach(l => {
      const h = (parseFloat(l.quantite) || 0) * (parseFloat(l.prix_unitaire) || 0)
      ht += h; tva += h * (tvaEffective(l) / 100)
    })
    return { ht, tva, ttc: ht + tva }
  }, [lignes])

  async function handleSave() {
    if (!form.tiers.trim() || !form.numero.trim()) return
    const lignesActives = lignes.filter(l => (l.description || "").trim())
    if (lignesActives.some(l => !nombreSaisieConnu(l.prix_unitaire) || !nombreSaisieConnu(l.tva) || Number(l.tva) > 100)) { setErreur('Renseignez un prix unitaire et un taux de TVA connus, finis et non négatifs sur chaque ligne.'); return }
    setLoading(true); setErreur('')
    try {
      // PATCH champs scalaires uniquement
      await apiFetch(`/api/devis/${devis.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          numero:         form.numero,
          date:           form.date,
          tiers:          form.tiers,
          tiers_id:       form.tiers_id,
          reference:      form.reference || null,
          validite_jours: parseInt(form.validite_jours) || 30,
          statut:         form.statut,
          notes:          form.notes || null,
          lignes:         lignes.map(l => ({
            article_id: l.article_id || null, description: l.description,
            quantite: parseFloat(l.quantite) || 0, prix_unitaire: parseFloat(l.prix_unitaire) || 0,
            tva: parseFloat(l.tva) || 0, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva),
            remise: parseFloat(l.remise) || 0, remise2: parseFloat(l.remise2) || 0, rabais: parseFloat(l.rabais) || 0,
          })),
        }),
      })

      onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={`Modifier devis ${devis.numero}`} icone="ti-pencil" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>
        <div className={styles.formGrid3}>
          <div className={styles.formGroup}>
            <label className={styles.label}>N° Devis *</label>
            <input className={styles.input} value={form.numero} readOnly />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date</label>
            <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Validité (jours)</label>
            <input className={styles.input} type="number" value={form.validite_jours} onChange={e => setForm(p => ({ ...p, validite_jours: e.target.value }))} />
          </div>
        </div>
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Client *</label>
            <ChampTiers value={form.tiers}
              onChange={v => setForm(p => ({ ...p, tiers: v }))}
              onSelect={t => setForm(p => ({ ...p, tiers_id: t?.id || null }))}
              type="client" />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Statut</label>
            <select className={styles.input} value={form.statut} disabled title="Le statut évolue via les actions du cycle du devis">
              {Object.entries(STATUT_DEVIS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
        </div>
        <TableLignes lignes={lignes} onChange={setLignes} avecTVA typeDoc="vente" dateDoc={form.date} />
        <div className={styles.totaux}>
          <div className={styles.totauxLigne}><span>Total HT</span><span>{montantLignesSaisies(totaux.ht, lignes, formatMAD)} MAD</span></div>
          <div className={styles.totauxLigne}><span>TVA</span><span>{montantLignesSaisies(totaux.tva, lignes, formatMAD)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC</span><span>{montantLignesSaisies(totaux.ttc, lignes, formatMAD)} MAD</span></div>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label}>Notes</label>
          <textarea className={styles.textarea} rows={2} value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
        </div>
        {['effet', 'cheque'].includes(form.mode) && (
          <div className={styles.formGroup}>
            <label className={styles.label}>Échéance {form.mode === 'effet' ? '*' : '(chèque postdaté)'}</label>
            <input className={styles.input} type="date" min={form.date || undefined} value={form.date_echeance || ''}
              onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
          </div>
        )}

        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <DiagnosticStockDevis lignes={lignes} />
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Formulaire édition BC ────────────────────────────────────────────────────
function FormulaireEditionBC({ bc, onFermer, onSuccess }) {
  const [form, setForm] = useState({
    numero: bc.numero || '',
    date: bc.date || '',
    tiers: bc.tiers || '',
    tiers_id: bc.tiers_id || null,
    type: bc.type || 'vente',
    statut: bc.statut || 'en_attente',
    date_livraison: bc.date_livraison || '',
    notes: bc.notes || '',
  })
  const [lignes, setLignes] = useState(
    (bc.lignes || []).map(l => ({ description: l.description, quantite: l.quantite, prix_unitaire: l.prix_unitaire, tva: l.tva ?? 20, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20), remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0, article_id: l.article_id || null, source_ligne_devis_id: l.source_ligne_devis_id || null, stock_actuel: null, unite: 'unité' }))
  )
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  const totauxEditionBC = useMemo(() => {
    let ht = 0, tva = 0
    lignes.forEach(l => {
      const h = (parseFloat(l.quantite) || 0) * (parseFloat(l.prix_unitaire) || 0)
      ht += h; tva += h * (tvaEffective(l) / 100)
    })
    return { ht, tva, ttc: ht + tva }
  }, [lignes])

  async function handleSave() {
    if (!form.tiers.trim() || !form.numero.trim()) return
    const lignesActives = lignes.filter(l => (l.description || "").trim())
    if (lignesActives.some(l => !nombreSaisieConnu(l.prix_unitaire) || !nombreSaisieConnu(l.tva) || Number(l.tva) > 100)) { setErreur('Renseignez un prix unitaire et un taux de TVA connus, finis et non négatifs sur chaque ligne.'); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch(`/api/bons-commande/${bc.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...form, date_livraison: form.date_livraison || null, lignes }),
      })
      onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={`Modifier BC ${bc.numero}`} icone="ti-pencil" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>
        <div className={styles.formGrid4}>
          <div className={styles.formGroup}>
            <label className={styles.label}>N° BC *</label>
            <input className={styles.input} value={form.numero} readOnly />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Type</label>
            <div className={styles.typeToggle}>
              {["vente","achat"].map(t => (
                <button key={t} className={`${styles.typeBtn} ${form.type === t ? styles.typeBtnActif : ''}`}
                  onClick={() => setForm(p => ({ ...p, type: t }))}>
                  {t === "vente" ? "Vente" : "Achat"}
                </button>
              ))}
            </div>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date</label>
            <input className={styles.input} type="date" value={form.date} onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Statut</label>
            <select className={styles.input} value={form.statut} disabled title="Le statut est piloté par les livraisons/réceptions et la facturation">
              {Object.entries(STATUT_BC).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
        </div>
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>{form.type === "vente" ? "Client *" : "Fournisseur *"}</label>
            <ChampTiers value={form.tiers}
              onChange={v => setForm(p => ({ ...p, tiers: v }))}
              onSelect={t => setForm(p => ({ ...p, tiers_id: t?.id || null }))}
              type={form.type === "vente" ? "client" : "fournisseur"} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>
              <i className="ti ti-truck" style={{ marginRight: 4, fontSize: 12 }} />
              Date de livraison promise
            </label>
            <input className={styles.input} type="date" value={form.date_livraison}
              onChange={e => setForm(p => ({ ...p, date_livraison: e.target.value }))} />
          </div>
        </div>
        <TableLignes lignes={lignes} onChange={setLignes} avecTVA typeDoc={form.type} dateDoc={form.date} />
        <div className={styles.totaux}>
          <div className={styles.totauxLigne}><span>Total HT</span><span>{formatMAD(totauxEditionBC.ht)} MAD</span></div>
          <div className={styles.totauxLigne}><span>TVA</span><span>{formatMAD(totauxEditionBC.tva)} MAD</span></div>
          <div className={`${styles.totauxLigne} ${styles.totauxTTC}`}><span>Total TTC</span><span>{formatMAD(totauxEditionBC.ttc)} MAD</span></div>
        </div>
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={loading}>
            <i className="ti ti-device-floppy" /> {loading ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </div>
    </Modal>
  )
}


// ─── Formulaire Bon de Réception ─────────────────────────────────────────────
function FormulaireBonReception({ bc, annee, onFermer, onSuccess }) {
  const [numero,    setNumero]    = useState('')
  useEffect(() => {
    apiFetch(`/api/societe/prochain-numero?type_doc=br&exercice=${annee}`)
      .then(d => setNumero(prev => prev || d.numero))
      .catch(() => setNumero(prev => prev || `BR-${annee}-001`))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const [date,      setDate]      = useState(dateLocaleISO())
  const [lignes,    setLignes]    = useState(
    (bc.lignes || []).map(l => ({
      description: l.description, article_id: l.article_id || null, source_ligne_bc_id: l.id,
      quantite_prevue: l.reste_a_livrer ?? l.quantite, quantite_livree: l.reste_a_livrer ?? l.quantite,
      prix_unitaire: l.prix_unitaire || 0, tva: l.tva ?? 20, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20),
      remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
    }))
  )
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')

  function majLigne(i, champ, val) {
    setLignes(prev => prev.map((l, idx) => idx === i ? { ...l, [champ]: val } : l))
  }

  async function handleSave() {
    if (!date) { setErreur('La date de réception est obligatoire.'); return }
    if (!lignes.some(l => nombreOuDefaut(l.quantite_livree, 0) > 0)) { setErreur('Saisissez au moins une quantité reçue positive.'); return }
    if (lignes.some(l => nombreOuDefaut(l.quantite_livree, 0) < 0)) { setErreur('Une quantité reçue ne peut pas être négative.'); return }
    if (lignes.some(l => nombreOuDefaut(l.quantite_livree, 0) > nombreOuDefaut(l.quantite_prevue, 0) + 0.0001)) {
      setErreur('La quantité reçue ne peut pas dépasser le reliquat de la commande.'); return
    }
    const lignesRecues = lignes
      .map(l => ({
        ligne_bc_id: l.source_ligne_bc_id || null,
        description: l.description,
        quantite: nombreOuDefaut(l.quantite_livree, 0),
      }))
      .filter(l => l.quantite > 0)
    setLoading(true); setErreur('')
    try {
      await apiFetch(`/api/bons-commande/${bc.id}/convertir-bl`, {
        method: 'POST',
        body: JSON.stringify({ date, lignes: lignesRecues }),
      })
      onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouveau bon de réception" icone="ti-package-import" onFermer={onFermer} largeur="lg">
      <div className={styles.formContenu}>

        {/* Info BC source */}
        <div className={styles.sourceInfo}>
          <i className="ti ti-link" /> Issu du BC <strong>{bc.numero}</strong>
          <span style={{ margin: '0 8px', color: 'var(--border-medium)' }}>·</span>
          Fournisseur : <strong>{bc.tiers}</strong>
        </div>

        {/* En-tête */}
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>N° BR</label>
            <input className={styles.input} value={numero || 'Attribué à l’enregistrement'} readOnly />
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Aperçu uniquement · réservation définitive côté serveur</span>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date de réception *</label>
            <input className={styles.input} type="date" value={date} onChange={e => setDate(e.target.value)} />
          </div>
        </div>

        {/* Lignes avec quantités reçues modifiables */}
        <div className={`${styles.lignesTable} hp-line-editor`}>
          <table className={styles.tableLignes}>
            <thead>
              <tr>
                <th style={{ width: '45%' }}>Article</th>
                <th style={{ width: '20%', textAlign: 'center' }}>Reliquat à recevoir</th>
                <th style={{ width: '20%', textAlign: 'center' }}>Qté reçue *</th>
                <th style={{ width: '15%', textAlign: 'center' }}>Écart</th>
              </tr>
            </thead>
            <tbody>
              {lignes.map((l, i) => {
                const ecart = (parseFloat(l.quantite_livree) || 0) - (parseFloat(l.quantite_prevue) || 0)
                return (
                  <tr key={i}>
                    <td data-label="Article" style={{ padding: '6px 8px', fontSize: 13 }}>{l.description}</td>
                    <td data-label="Reliquat à recevoir" style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-secondary)', padding: '6px 8px' }}>
                      {l.quantite_prevue}
                    </td>
                    <td data-label="Quantité reçue">
                      <input className={styles.inputLigne} type="number" min="0" step="0.01"
                        value={l.quantite_livree}
                        onChange={e => majLigne(i, 'quantite_livree', e.target.value)}
                        style={{ textAlign: 'center', fontWeight: 600 }} />
                    </td>
                    <td data-label="Écart" style={{ textAlign: 'center', fontSize: 11, fontWeight: 600,
                      color: ecart === 0 ? 'var(--text-tertiary)' : ecart > 0 ? '#3B6D11' : '#A32D2D' }}>
                      {ecart === 0 ? '—' : ecart > 0 ? `+${ecart}` : ecart}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={loading}>
            <i className="ti ti-package-import" /> {loading ? 'Enregistrement...' : 'Créer le bon de réception'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ONGLETS
// ═══════════════════════════════════════════════════════════════════════════════

function OngletDevis({ annee, onConvertirBC }) {
  const navigate = useNavigate()
  const { lignes: devis, loading, erreurLecture, charger } = useListeCommerciale(`/api/devis?exercice=${annee}`, null)
  const [showForm, setShowForm] = useState(false)
  const [recherche, setRecherche] = useState('')
  const [devisDetail, setDevisDetail] = useState(null)
  const [devisEdit, setDevisEdit] = useState(null)

  async function convertirEnFacture(d) {
    if (d.facture_id) {
      notifier(`Une facture existe déjà pour ce devis${d.facture_numero ? ` (${d.facture_numero})` : ''}.`)
      return
    }
    if (d.bon_commande_id) {
      notifier(`Le bon de commande ${d.bon_commande_numero || ''} existe déjà. Poursuivez la facturation depuis le BC ou le bon de livraison.`)
      return
    }
    // Le devis ne devient "converti" qu'après création effective de la facture.
    // Ouvrir puis annuler le formulaire Facture ne modifie donc plus son statut.
    navigate('/factures', {
      state: {
        nouvelleFacture: {
          type:      'vente',
          tiers:     d.tiers,
          reference: d.numero,
          devis_id:  d.id,
          lignes: (d.lignes || []).map(l => ({
            description:   l.description,
            quantite:      l.quantite,
            prix_unitaire: l.prix_unitaire,
            tva:           l.tva ?? 20,
            qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20),
            remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
            article_id: l.article_id || null, source_ligne_devis_id: l.id || null,
          })),
        }
      }
    })
  }



  async function changerStatut(id, statut) {
    try { await apiFetch(`/api/devis/${id}`, { method: 'PATCH', body: JSON.stringify({ statut }) }); charger() }
    catch {}
  }

  const [devisAConvertir, setDevisAConvertir] = useState(null)

  async function ouvrirConversionBC(d) {
    if (d.facture_id) {
      notifier(`Une facture existe déjà pour ce devis${d.facture_numero ? ` (${d.facture_numero})` : ''}.`)
      return
    }
    if (d.bon_commande_id) {
      notifier(`Un bon de commande (${d.bon_commande_numero || d.bon_commande_id}) existe déjà pour ce devis.`)
      return
    }
    // Double contrôle pour les données historiques ou un écran resté ouvert.
    try {
      const bcs = await apiFetch(`/api/bons-commande?exercice=${annee}`)
      const bcExistant = bcs.find(bc => bc.devis_id === d.id)
      if (bcExistant) {
        await charger()
        notifier(`Un bon de commande (${bcExistant.numero}) existe déjà pour ce devis.`)
        return
      }
    } catch {}
    setDevisAConvertir(d)
  }

  async function confirmerConversionBC(d) {
    try {
      await apiFetch(`/api/devis/${d.id}/convertir-bc`, { method: 'POST' })
      setDevisAConvertir(null)
      charger()
      onConvertirBC?.()
    } catch (e) { notifier.erreur(e.message) }
  }

  async function supprimer(id) {
    if (!confirm('Supprimer ce devis ?')) return
    try { await apiFetch(`/api/devis/${id}`, { method: 'DELETE' }); charger() } catch {}
  }

  const filtres = useMemo(() =>
    devis.filter(d => !recherche || d.tiers.toLowerCase().includes(recherche.toLowerCase()) || d.numero.toLowerCase().includes(recherche.toLowerCase())),
    [devis, recherche]
  )

  return (
    <div className={styles.ongletContent}>
      {showForm && <FormulaireDevis onFermer={() => setShowForm(false)} onSuccess={charger} />}
      {devisEdit && (
        <FormulaireEditionDevis
          devis={devisEdit}
          onFermer={() => setDevisEdit(null)}
          onSuccess={() => { setDevisEdit(null); charger() }}
        />
      )}

      {devisAConvertir && (
        <FormulaireBonCommande
          onFermer={() => setDevisAConvertir(null)}
          onSuccess={() => { setDevisAConvertir(null); charger(); onConvertirBC?.() }}
          devisSource={devisAConvertir}
          modeConversion
          onConversionConfirmee={() => confirmerConversionBC(devisAConvertir)}
        />
      )}
      <div className={styles.ongletTopbar}>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={loading}>Actualiser la liste</button>
        <div className={styles.recherche}>
          <i className="ti ti-search" />
          <input type="text" placeholder="Rechercher..." value={recherche} onChange={e => setRecherche(e.target.value)} className={styles.inputRecherche} />
        </div>
        <button className={styles.btnPrim} onClick={() => setShowForm(true)}>
          <i className="ti ti-plus" /> Nouveau devis
        </button>
      </div>
      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /> Chargement...</div>
        ) : erreurLecture ? (
          <ErreurListeCommerciale message={erreurLecture} charger={charger} />
        ) : filtres.length === 0 ? (
          <div className={styles.vide}><i className="ti ti-file-description" /><span>Aucun devis</span></div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr>
                <th>N° Devis</th><th>Date</th><th>Client</th>
                <th style={{ textAlign: 'right' }}>HT</th>
                <th style={{ textAlign: 'right' }}>TTC</th>
                <th>Validité</th><th>Statut</th><th />
              </tr></thead>
              <tbody>
                {filtres.map(d => (
                  <React.Fragment key={d.id}>
                  <tr style={{ background: devisDetail?.id === d.id ? 'var(--blue-light)' : '' }}>
                    <td><span className={styles.numDoc}>{d.numero}</span></td>
                    <td className={styles.tdDate}>{formatDate(d.date)}</td>
                    <td><strong>{d.tiers}</strong></td>
                    <td style={{ textAlign: 'right' }}>{formatMAD(d.total_ht)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatMAD(d.total_ttc)}</td>
                    <td style={{ fontSize: 11, color: estDevisDepasse(d) ? 'var(--red)' : 'var(--text-tertiary)', fontWeight: estDevisDepasse(d) ? 600 : 400 }}>
                      {d.validite_jours}j
                      {estDevisDepasse(d) && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 3, marginTop: 2 }}>
                          <i className="ti ti-alert-triangle" style={{ fontSize: 10 }} />
                          <span>dépassée</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <Badge statut={d.statut} map={STATUT_DEVIS} />
                        {estDevisDepasse(d) && (
                          <span style={{ fontSize: 10, color: 'var(--red)', display: 'flex', alignItems: 'center', gap: 3 }}>
                            <i className="ti ti-clock-x" style={{ fontSize: 10 }} />
                            Expiré (non acté)
                          </span>
                        )}
                        {d.facture_id && (
                          <span style={{ fontSize: 10, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 3 }}>
                            <i className="ti ti-file-invoice" style={{ fontSize: 10 }} />
                            {d.facture_numero || `Brouillon facture #${d.facture_id}`}
                          </span>
                        )}
                        {!d.facture_id && d.bon_commande_id && (
                          <span style={{ fontSize: 10, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 3 }}>
                            <i className="ti ti-clipboard-list" style={{ fontSize: 10 }} />
                            {d.bon_commande_numero || 'BC généré'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <button className={styles.btnAction} onClick={() => setDevisDetail(devisDetail?.id === d.id ? null : d)} title="Voir détail / note">
                          <i className={`ti ${devisDetail?.id === d.id ? 'ti-eye-off' : 'ti-eye'}`} />
                        </button>
                        <button className={styles.btnAction}
                          onClick={() => telechargerPDF(`/api/devis/${d.id}/pdf`, `devis_${d.numero}.pdf`).catch(e => notifier.erreur(e.message))}
                          title="Télécharger PDF"><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                        <button className={styles.btnAction}
                          onClick={() => preparerEmailDocument({ endpoint: `/api/devis/${d.id}/pdf`, nomFichier: `devis_${d.numero}.pdf`, typeDocument: 'Devis', numero: d.numero, tiers: d.tiers, tiersId: d.tiers_id }).catch(e => notifier.erreur(e.message))}
                          title="Télécharger le PDF et préparer un e-mail"><i className="ti ti-mail-forward" /><span className="libelle-action" aria-hidden="true">Télécharger le PDF et préparer un e-mail</span></button>
                        {d.statut !== 'converti' && (
                          <button className={styles.btnAction} onClick={() => setDevisEdit(d)} title="Modifier"><i className="ti ti-pencil" /><span className="libelle-action" aria-hidden="true">Modifier</span></button>
                        )}
                        {d.statut === 'brouillon' && (
                          <button className={styles.btnAction} onClick={() => changerStatut(d.id, 'envoye')} title="Marquer envoyé"><i className="ti ti-send" /><span className="libelle-action" aria-hidden="true">Marquer envoyé</span></button>
                        )}
                        {(d.statut === 'envoye' || d.statut === 'brouillon') && (
                          <button className={`${styles.btnAction} ${styles.btnStatusSuccess}`} onClick={() => changerStatut(d.id, 'accepte')} title="Marquer accepté"><i className="ti ti-check" /><span className="libelle-action" aria-hidden="true">Marquer accepté</span></button>
                        )}
                        {estDevisDepasse(d) && (
                          <button className={`${styles.btnAction} ${styles.btnStatusDanger}`} onClick={() => changerStatut(d.id, 'expire')} title="Acter le statut Expiré"><i className="ti ti-clock-x" /><span className="libelle-action" aria-hidden="true">Acter le statut Expiré</span></button>
                        )}
                        {d.statut === 'accepte' && !d.bon_commande_id && !d.facture_id && (
                          <div className={styles.transformGroup} aria-label="Transformer le devis">
                            <button className={styles.btnTransformSecondary} onClick={() => ouvrirConversionBC(d)} title="Créer un bon de commande à partir du devis">
                              <i className="ti ti-clipboard-list" /> Créer BC
                            </button>
                            <button className={styles.btnTransformPrimary}
                              onClick={() => convertirEnFacture(d)}
                              title="Créer directement une facture sans passer par un bon de commande">
                              <i className="ti ti-file-invoice" /> Créer facture
                            </button>
                          </div>
                        )}
                        {(d.bon_commande_id || d.facture_id) && (
                          <div className={styles.transformGroup} aria-label="Document déjà transformé">
                            <span className={styles.transformDone} title={d.facture_id
                              ? 'Ce devis a déjà généré une facture. Aucune nouvelle transformation n’est disponible.'
                              : 'Ce devis a déjà généré un bon de commande. Continuez le cycle depuis le BC.'}>
                              <i className="ti ti-circle-check" />
                              {d.facture_id ? 'Facture créée' : 'BC créé'}
                            </span>
                          </div>
                        )}
                        <button className={styles.btnTrash} onClick={() => supprimer(d.id)} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>
                      </div>
                    </td>
                  </tr>
                  {devisDetail?.id === d.id && (
                    <tr>
                      <td colSpan={8} style={{ background: "#EFF6FF", padding: 0 }}>
                        <div style={{ padding: "12px 16px", display: "flex", gap: 24, flexWrap: "wrap" }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Lignes du devis</div>
                            {(d.lignes || []).map((l, idx) => (
                              <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "3px 0", borderBottom: "0.5px solid var(--border-light)" }}>
                                <span>{l.description}</span>
                                <span style={{ color: "var(--text-secondary)" }}>{l.quantite} × {formatMAD(l.prix_unitaire)} MAD HT</span>
                              </div>
                            ))}
                          </div>
                          {d.notes && (
                            <div style={{ minWidth: 200, maxWidth: 320 }}>
                              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Note</div>
                              <div style={{ fontSize: 12, color: "var(--text-secondary)", background: "var(--bg-primary)", padding: "8px 10px", borderRadius: 6, whiteSpace: "pre-wrap" }}>
                                {d.notes}
                              </div>
                            </div>
                          )}
                          {(d.facture_id || d.facture_numero) && (
                            <div style={{ minWidth: 160 }}>
                              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                                <i className="ti ti-file-invoice" style={{ marginRight: 4 }} />Documents liés
                              </div>
                              <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6,
                                background: '#E6F1FB', color: '#185FA5', padding: '4px 10px', borderRadius: 4, width: 'fit-content' }}>
                                <i className="ti ti-file-invoice" style={{ fontSize: 11 }} />
                                {d.facture_numero || `FA #${d.facture_id}`}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function OngletBonsCommande({ annee, onConvertirFacture, onConvertirBL, typeForce = null }) {
  const navigate = useNavigate()
  const { lignes: bcs, loading, erreurLecture, charger } = useListeCommerciale(`/api/bons-commande?exercice=${annee}`, typeForce)
  const [showForm, setShowForm] = useState(false)
  const [bcAFacturer, setBcAFacturer] = useState(null)
  const [bcALivrer, setBcALivrer] = useState(null)
  const [reliquat, setReliquat] = useState(null)      // détail du reste à livrer
  const [qtesLivrees, setQtesLivrees] = useState({})  // ligne BC → quantité saisie
  const [dateLivraisonBL, setDateLivraisonBL] = useState(dateLocaleISO())
  const [bcAReceptionner, setBcAReceptionner] = useState(null)
  const [bcEdit, setBcEdit] = useState(null)
  const [expandedPJ, setExpandedPJ] = useState(null)
  const [bcDetail, setBcDetail] = useState(null)




  function confirmerFacture(bc) {
    setBcAFacturer(null)
    navigate('/factures', {
      state: {
        nouvelleFacture: {
          type: bc.type || 'vente',
          tiers: bc.tiers,
          // Sur un achat, la référence doit venir de la facture émise par le
          // fournisseur, jamais du numéro de notre bon de commande.
          reference: bc.type === 'achat' ? '' : bc.numero,
          source_document_numero: bc.numero,
          bc_id: bc.id,
          tiers_id: bc.tiers_id || null,
          lignes: (bc.lignes || []).map(l => ({
            description: l.description, quantite: l.quantite, prix_unitaire: l.prix_unitaire,
            tva: l.tva ?? 20, qualification_tva: l.qualification_tva || qualificationParDefautPourTaux(l.tva ?? 20), remise: l.remise ?? 0, remise2: l.remise2 ?? 0, rabais: l.rabais ?? 0,
            article_id: l.article_id || null, source_ligne_devis_id: l.source_ligne_devis_id || null,
            source_ligne_bc_id: l.id,
          })),
        }
      }
    })
  }

  // À l'ouverture de la modale, on récupère le reste à livrer : une commande
  // peut avoir déjà fait l'objet de livraisons partielles.
  async function ouvrirLivraison(bc) {
    setBcALivrer(bc); setReliquat(null); setQtesLivrees({})
    try {
      const r = await apiFetch(`/api/bons-commande/${bc.id}/reliquat`)
      setReliquat(r)
      const init = {}
      r.lignes.forEach(l => { if (l.reliquat > 0) init[String(l.ligne_bc_id || l.description)] = String(l.reliquat) })
      setQtesLivrees(init)
    } catch (e) { notifier.erreur(e.message) }
  }

  async function confirmerBL(bc, dateLivraison) {
    try {
      // Quantités partielles : on n'envoie que les lignes réellement livrées
      const lignes = (reliquat?.lignes || [])
        .map(l => ({
          ligne_bc_id: l.ligne_bc_id || null, description: l.description,
          quantite: parseFloat(qtesLivrees[String(l.ligne_bc_id || l.description)]) || 0,
        }))
        .filter(l => l.quantite > 0)
      await apiFetch(`/api/bons-commande/${bc.id}/convertir-bl`, {
        method: 'POST',
        body: JSON.stringify({ date: dateLivraison || null, lignes: lignes.length ? lignes : null }),
      })
      setBcALivrer(null)
      charger(); onConvertirBL?.()
    } catch (e) { notifier.erreur(e.message) }
  }

  async function ouvrirModaleFacture(bc) {
    if ((bc.facturation_reservee_pct || bc.facturation_pct || 0) > 0) {
      notifier('Ce bon de commande est déjà facturé ou réservé dans un brouillon au moins partiellement. Facturez les BL/BR restants pour éviter un doublon.')
      return
    }
    // Une facture issue directement du BC ne référence pas les lignes du BR.
    // Dès qu'une réception existe, utiliser son propre parcours de facturation.
    if (bc.type === 'achat') {
      try {
        const receptions = await apiFetch(`/api/bons-reception?exercice=${annee}`)
        if (receptions.some(br => Number(br.bon_commande_id) === Number(bc.id) && br.statut !== 'retourne')) {
          notifier(`Le bon de commande ${bc.numero} possède déjà un bon de réception. Ouvrez « Bons de réception » et cliquez sur « Facturer » pour conserver le lien BC → BR → facture.`)
          return
        }
      } catch (e) {
        notifier.erreur(`Impossible de vérifier les bons de réception : ${e.message}`)
        return
      }
    }
    setBcAFacturer(bc)
  }

  async function ouvrirModaleBL(bc) {
    // Recharger le BC depuis l'API pour avoir le facture_id à jour
    let bcFrais = bc
    try {
      const bcs = await apiFetch(`/api/bons-commande?exercice=${annee}`)
      bcFrais = bcs.find(b => b.id === bc.id) || bc
    } catch {}

    // Le BL peut précéder la facture. La facturation directe du BC reste disponible
    // pour les cycles courts ; le cycle standard peut suivre BC → BL → Facture.
    // Plusieurs bons de livraison sont possibles pour une même commande
    // (livraisons partielles) : c'est le reliquat qui décide, pas l'existence d'un BL.
    setDateLivraisonBL(dateLocaleISO())
    await ouvrirLivraison(bcFrais)
  }

  async function ouvrirModaleBR(bc) {
    // Recharger le BC depuis l'API pour avoir facture_id à jour
    let bcFrais = bc
    try {
      const bcs = await apiFetch(`/api/bons-commande?exercice=${annee}`)
      bcFrais = bcs.find(b => b.id === bc.id) || bc
    } catch {}

    // Le bon de réception peut précéder la facture fournisseur et plusieurs BR
    // peuvent couvrir une même commande en cas de réceptions partielles.
    setBcAReceptionner(bcFrais)
  }



  async function supprimer(id) {
    if (!confirm('Supprimer ce bon de commande ?')) return
    try { await apiFetch(`/api/bons-commande/${id}`, { method: 'DELETE' }); charger() } catch (e) { notifier.erreur(e.message) }
  }

  return (
    <div className={styles.ongletContent}>
      {showForm && <FormulaireBonCommande typeInitial={typeForce || 'vente'} onFermer={() => setShowForm(false)} onSuccess={charger} />}
      <div className={styles.ongletTopbar}>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={loading}>Actualiser la liste</button>
        <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{loading || erreurLecture ? 'Nombre de commandes indisponible' : `${bcs.length} bon${bcs.length !== 1 ? 's' : ''} de commande`}</span>
        <button className={styles.btnPrim} onClick={() => setShowForm(true)}>
          <i className="ti ti-plus" /> Nouveau BC
        </button>
      </div>
      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
        ) : erreurLecture ? (
          <ErreurListeCommerciale message={erreurLecture} charger={charger} />
        ) : bcs.length === 0 ? (
          <div className={styles.vide}><i className="ti ti-clipboard-list" /><span>Aucun bon de commande</span></div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr>
                <th>N° BC</th><th>Type</th><th>Date</th><th>Tiers</th>
                <th style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Total HT</th>
                <th style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Total TTC</th>
                <th>Livraison</th><th>Facturation</th><th>Statut</th><th />
              </tr></thead>
              <tbody>
                {bcs.map(bc => (
                  <tr key={bc.id}>
                    <td><span className={styles.numDoc}>{bc.numero}</span></td>
                    <td>
                      <span style={{
                        fontSize: 10, padding: '2px 7px', borderRadius: 100,
                        background: bc.type === 'vente' ? '#E6F1FB' : '#EEEDFE',
                        color: bc.type === 'vente' ? '#185FA5' : '#534AB7',
                      }}>
                        {bc.type === 'vente' ? 'Vente' : 'Achat'}
                      </span>
                    </td>
                    <td className={styles.tdDate}>{formatDate(bc.date)}</td>
                    <td><strong>{bc.tiers}</strong></td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{formatMAD(bc.total_ht)}</td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap', fontWeight: 600 }}>{formatMAD(bc.total_ttc)}</td>
                    <td style={{ fontSize: 11, minWidth: 145 }}>
                      <div className={styles.progressMeta}>
                        <span>{bc.type === 'achat' ? 'Réceptionné' : 'Livré'} : <strong>{Math.round(bc.livraison_pct || 0)}%</strong></span>
                        <span>{formatMAD(bc.reste_a_livrer_ht || 0)} MAD HT restant</span>
                      </div>
                      <div className={styles.progressTrack}><span style={{ width: `${Math.min(100, bc.livraison_pct || 0)}%` }} /></div>
                      {bc.date_livraison && (
                        <div style={{ marginTop: 5 }}>
                          {(() => {
                            const actif = (bc.livraison_pct || 0) < 100 && bc.statut !== 'annule'
                            if (!actif) return <span style={{ color: 'var(--text-tertiary)' }}>Prévu {formatDate(bc.date_livraison)}</span>
                            const info = infosRetardLivraison(bc)
                            if (!info) return <span style={{ color: 'var(--text-tertiary)' }}>{formatDate(bc.date_livraison)}</span>
                            if (info.joursEcart > 0) return <span style={{ color: '#A32D2D', fontWeight: 600 }}>En retard de {info.joursEcart}j</span>
                            return <span style={{ color: 'var(--text-tertiary)' }}>Prévu {formatDate(bc.date_livraison)}</span>
                          })()}
                        </div>
                      )}
                    </td>
                    <td style={{ fontSize: 11, minWidth: 145 }}>
                      <div className={styles.progressMeta}>
                        <span>Facturé : <strong>{Math.round(bc.facturation_pct || 0)}%</strong></span>
                        <span>{formatMAD(bc.reste_a_facturer_ht || 0)} MAD HT restant</span>
                      </div>
                      <div className={styles.progressTrack}><span style={{ width: `${Math.min(100, bc.facturation_pct || 0)}%` }} /></div>
                      {(bc.nb_factures || 0) > 0 && <div className={styles.progressNote}>{bc.nb_factures} facture{bc.nb_factures > 1 ? 's' : ''}</div>}
                      {(bc.nb_brouillons || 0) > 0 && (
                        <div className={styles.progressNote}>
                          {bc.nb_brouillons} brouillon{bc.nb_brouillons > 1 ? 's' : ''} · {formatMAD(bc.montant_brouillon_ht || 0)} MAD HT réservé
                        </div>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <Badge statut={bc.statut_cycle === 'termine' ? 'facture' : (bc.statut_cycle === 'a_traiter' ? 'en_attente' : bc.statut_cycle)} map={STATUT_BC} />
                        {bc.statut_cycle === 'termine' && (
                          <span style={{ fontSize: 10, color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 3 }}>
                            <i className="ti ti-circle-check" style={{ fontSize: 10 }} /> Cycle documenté
                          </span>
                        )}
                        {bc.devis_id && (
                          <span style={{ fontSize: 10, color: '#534AB7', display: 'flex', alignItems: 'center', gap: 3 }}>
                            <i className="ti ti-file-description" style={{ fontSize: 10 }} />
                            Issu d'un devis
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        {bc.statut !== 'annule' && (bc.facturation_reservee_pct || bc.facturation_pct || 0) === 0 && (
                          <button className={styles.btnTransformPrimary} onClick={() => ouvrirModaleFacture(bc)} title="Facturer directement la commande">
                            <i className="ti ti-file-invoice" /> Facturer
                          </button>
                        )}
                        {bc.statut !== 'annule' && bc.type === 'vente' && (bc.livraison_pct || 0) < 100 && (
                          <button className={styles.btnTransformSecondary} onClick={() => ouvrirModaleBL(bc)} title="Créer un bon de livraison sur le reliquat">
                            <i className="ti ti-truck" /> Livrer
                          </button>
                        )}
                        {bc.statut !== 'annule' && bc.type === 'achat' && (bc.livraison_pct || 0) < 100 && (
                          <button className={styles.btnTransformSecondary} onClick={() => ouvrirModaleBR(bc)} title="Créer un bon de réception sur le reliquat">
                            <i className="ti ti-package-import" /> Réceptionner
                          </button>
                        )}
                        <button className={styles.btnAction} onClick={() => setBcDetail(bc)} title="Voir le détail commandé / livré / facturé"><i className="ti ti-list-details" /><span className="libelle-action" aria-hidden="true">Voir le détail commandé / livré / facturé</span></button>
                        <button className={styles.btnAction} onClick={() => setBcEdit(bc)} title="Modifier"><i className="ti ti-pencil" /><span className="libelle-action" aria-hidden="true">Modifier</span></button>
                        <button className={styles.btnAction}
                          onClick={() => setExpandedPJ(expandedPJ === bc.id ? null : bc.id)}
                          title="Pièces jointes" style={{ color: expandedPJ === bc.id ? 'var(--blue)' : '' }}><i className="ti ti-paperclip" /><span className="libelle-action" aria-hidden="true">Pièces jointes</span></button>
                        <button className={styles.btnAction}
                          onClick={() => telechargerPDF(`/api/bons-commande/${bc.id}/pdf`, `bc_${bc.numero}.pdf`).catch(e => notifier.erreur(e.message))}
                          title="Télécharger PDF"><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                        <button className={styles.btnAction}
                          onClick={() => preparerEmailDocument({ endpoint: `/api/bons-commande/${bc.id}/pdf`, nomFichier: `bc_${bc.numero}.pdf`, typeDocument: 'Bon de commande', numero: bc.numero, tiers: bc.tiers, tiersId: bc.tiers_id }).catch(e => notifier.erreur(e.message))}
                          title="Télécharger le PDF et préparer un e-mail"><i className="ti ti-mail-forward" /><span className="libelle-action" aria-hidden="true">Télécharger le PDF et préparer un e-mail</span></button>
                        <button className={styles.btnTrash} onClick={() => supprimer(bc.id)}>
                          <i className="ti ti-trash" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {expandedPJ && (
              <div style={{ padding: '12px 20px', borderTop: '0.5px solid var(--border-light)', background: '#FAFAFA' }}>
                <PiecesJointes docType="bc" docId={expandedPJ} />
              </div>
            )}
          </div>
        )}
      </div>

      {bcDetail && (
        <Modal titre={`Suivi de ${bcDetail.numero}`} icone="ti-list-details" onFermer={() => setBcDetail(null)} largeur="lg">
          <div className={styles.formContenu}>
            <div className={styles.sourceInfo}>
              <i className="ti ti-building-store" /> {bcDetail.tiers} — suivi ligne par ligne
            </div>
            <div className={styles.cycleLineTable}>
              <div className={styles.cycleLineHead}>
                <span>Article</span><span>Commandé</span><span>{bcDetail.type === 'achat' ? 'Réceptionné' : 'Livré'}</span><span>Facturé</span><span>Reste à livrer</span><span>Reste à facturer</span>
              </div>
              {(bcDetail.lignes || []).map(l => (
                <div className={styles.cycleLineRow} key={l.id}>
                  <span><strong>{l.description}</strong><small>{l.tva ?? 0}% TVA</small></span>
                  <span data-label="Commandé">{l.quantite_commandee ?? l.quantite}</span>
                  <span data-label={bcDetail.type === 'achat' ? 'Réceptionné' : 'Livré'}>{l.quantite_livree ?? 0}</span>
                  <span data-label="Facturé">
                    {l.quantite_facturee ?? 0}
                    {(l.quantite_brouillon || 0) > 0 && <small>+ {l.quantite_brouillon} brouillon</small>}
                  </span>
                  <span data-label="Reste à livrer" className={(l.reste_a_livrer || 0) > 0 ? styles.resteActif : ''}>{l.reste_a_livrer ?? l.quantite}</span>
                  <span data-label="Reste à facturer" className={(l.reste_a_facturer || 0) > 0 ? styles.resteActif : ''}>{l.reste_a_facturer ?? l.quantite}</span>
                </div>
              ))}
            </div>
            <div className={styles.cycleSummary}>
              <span>{bcDetail.type === 'achat' ? 'Réception' : 'Livraison'} <strong>{Math.round(bcDetail.livraison_pct || 0)}%</strong></span>
              <span>Facturation <strong>{Math.round(bcDetail.facturation_pct || 0)}%</strong></span>
              {(bcDetail.montant_brouillon_ht || 0) > 0 && <span>Brouillons <strong>{formatMAD(bcDetail.montant_brouillon_ht)} MAD HT</strong></span>}
              <span>À facturer <strong>{formatMAD(bcDetail.reste_a_facturer_ht || 0)} MAD HT</strong></span>
            </div>
            <div className={styles.formActions}>
              <button className={styles.btnSec} onClick={() => setBcDetail(null)}>Fermer</button>
            </div>
          </div>
        </Modal>
      )}

      {bcEdit && (
        <FormulaireEditionBC
          bc={bcEdit}
          onFermer={() => setBcEdit(null)}
          onSuccess={() => { setBcEdit(null); charger() }}
        />
      )}

      {bcAFacturer && (
        <Modal titre={`Facture depuis ${bcAFacturer.numero}`} icone="ti-file-invoice" onFermer={() => setBcAFacturer(null)} largeur="lg">
          <div className={styles.formContenu}>
            <div className={styles.sourceInfo}>
              <i className="ti ti-link" /> Issu du BC <strong>{bcAFacturer.numero}</strong> — {bcAFacturer.tiers}
            </div>
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 8 }}>Lignes</div>
              {(bcAFacturer.lignes || []).map((l, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', borderBottom: '0.5px solid var(--border-light)' }}>
                  <span>{l.description}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{l.quantite} × {formatMAD(l.prix_unitaire)} MAD HT</span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600, marginTop: 8, paddingTop: 8, borderTop: '0.5px solid var(--border-medium)' }}>
                <span>Total HT</span><span>{formatMAD(bcAFacturer.total_ht)} MAD</span>
              </div>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
              Les taux de TVA, remises et rabais sont repris du bon de commande. La facture conservera les liens vers les lignes d'origine.
            </p>
            <div className={styles.formActions}>
              <button className={styles.btnSec} onClick={() => setBcAFacturer(null)}>Annuler</button>
              <button className={styles.btnPrim} onClick={() => confirmerFacture(bcAFacturer)}>
                <i className="ti ti-file-invoice" /> Créer la facture
              </button>
            </div>
          </div>
        </Modal>
      )}

      {bcALivrer && (
        <Modal titre={`Bon de livraison depuis ${bcALivrer.numero}`} icone="ti-truck" onFermer={() => setBcALivrer(null)} largeur="md">
          <div className={styles.formContenu}>
            <div className={styles.sourceInfo}>
              <i className="ti ti-link" /> Issu du BC <strong>{bcALivrer.numero}</strong> — {bcALivrer.tiers}
            </div>
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Quantités à livrer
                {reliquat && reliquat.total_livre > 0 && (
                  <span style={{ marginLeft: 8, fontWeight: 400, color: 'var(--text-tertiary)' }}>
                    — déjà livré : {reliquat.total_livre} sur {reliquat.total_commande}
                  </span>
                )}
              </div>
              {!reliquat ? (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Chargement du reste à livrer…</div>
              ) : (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 70px 70px 90px', gap: 8,
                    fontSize: 10, textTransform: 'uppercase', color: 'var(--text-tertiary)',
                    paddingBottom: 4, borderBottom: '0.5px solid var(--border-medium)', fontWeight: 600 }}>
                    <span>Article</span>
                    <span style={{ textAlign: 'right' }}>Commandé</span>
                    <span style={{ textAlign: 'right' }}>Reste</span>
                    <span style={{ textAlign: 'right' }}>À livrer</span>
                  </div>
                  {reliquat.lignes.map((l, i) => (
                    <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 70px 70px 90px', gap: 8,
                      alignItems: 'center', fontSize: 12, padding: '5px 0',
                      borderBottom: '0.5px solid var(--border-light)',
                      opacity: l.reliquat > 0 ? 1 : 0.45 }}>
                      <span>{l.description}</span>
                      <span style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>{l.quantite_commandee}</span>
                      <span style={{ textAlign: 'right', fontWeight: 600,
                        color: l.reliquat > 0 ? '#C9A227' : 'var(--text-tertiary)' }}>
                        {l.reliquat > 0 ? l.reliquat : 'soldé'}
                      </span>
                      {l.reliquat > 0 ? (
                        <input type="number" min="0" max={l.reliquat} step="0.01"
                          value={qtesLivrees[String(l.ligne_bc_id || l.description)] ?? ''}
                          onChange={e => setQtesLivrees(p => ({ ...p, [String(l.ligne_bc_id || l.description)]: e.target.value }))}
                          style={{ width: '100%', padding: '4px 7px', borderRadius: 4,
                            border: '0.5px solid var(--border-medium)', textAlign: 'right', fontSize: 12,
                            background: 'var(--bg-primary)', boxSizing: 'border-box' }} />
                      ) : <span style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>—</span>}
                    </div>
                  ))}
                  <div style={{ fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 8, lineHeight: 1.4 }}>
                    Livrez moins que le reste dû pour une livraison partielle : le reliquat
                    restera ouvert sur la commande et pourra être livré plus tard.
                  </div>
                </>
              )}
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                Date de livraison
              </label>
              <input type="date" value={dateLivraisonBL} onChange={e => setDateLivraisonBL(e.target.value)}
                style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }} />
            </div>
            <div className={styles.formActions}>
              <button className={styles.btnSec} onClick={() => setBcALivrer(null)}>Annuler</button>
              <button className={styles.btnPrim} onClick={() => confirmerBL(bcALivrer, dateLivraisonBL)}>
                <i className="ti ti-truck" /> Créer le bon de livraison
              </button>
            </div>
          </div>
        </Modal>
      )}

      {bcAReceptionner && (
        <FormulaireBonReception
          bc={bcAReceptionner}
          annee={annee}
          onFermer={() => setBcAReceptionner(null)}
          onSuccess={() => { setBcAReceptionner(null); charger(); onConvertirBL?.() }}
        />
      )}
    </div>
  )
}

// Lecture seule : statut logistique et quantités réservées au BC sont distincts.
function DetailBonLivraison({ bl, onFermer }) {
  const reception = bl.type === 'achat'
  return (
    <Modal titre={`${reception ? 'Bon de réception' : 'Bon de livraison'} ${bl.numero}`}
      icone="ti-truck" onFermer={onFermer} largeur="lg">
      <div className={styles.blDetail}>
        <div className={styles.blDetailIntro}>
          <Badge statut={bl.statut} map={reception ? STATUT_BR : STATUT_BL} />
          <span>{reception ? 'Réception fournisseur' : 'Livraison client'} · {formatDate(bl.date)}</span>
        </div>
        <section className={styles.blDetailSection}>
          <h3>Informations du document</h3>
          <dl className={styles.blDetailFields}>
            <div><dt>{reception ? 'Fournisseur' : 'Client'}</dt><dd>{bl.tiers}</dd></div>
            <div><dt>Date du bon</dt><dd>{formatDate(bl.date)}</dd></div>
            {bl.bon_commande_numero && <div><dt>Bon de commande d’origine</dt><dd>{bl.bon_commande_numero}</dd></div>}
            {bl.transporteur && <div><dt>Transporteur</dt><dd>{bl.transporteur}</dd></div>}
          </dl>
        </section>
        <section className={styles.blDetailSection}>
          <h3>Lignes du document</h3>
          <div className={styles.blDetailLines} role="list" aria-label="Lignes du bon de livraison">
            {(bl.lignes || []).map((ligne, index) => (
              <div className={styles.blDetailLine} role="listitem" key={ligne.id ?? index}>
                <div className={styles.blDetailDescription}>
                  <span className={styles.blDetailLabel}>Désignation</span>
                  <strong>{ligne.description}</strong>
                </div>
                <div><span className={styles.blDetailLabel}>Qté inscrite</span><span>{ligne.quantite_livree ?? 0}</span></div>
                <div><span className={styles.blDetailLabel}>Prix unitaire HT</span><span>{formatMAD(ligne.prix_unitaire || 0)} MAD</span></div>
                <div><span className={styles.blDetailLabel}>TVA</span><span>{ligne.qualification_tva === 'taxable' ? `${ligne.tva ?? 0} %` : 'Non taxable'}</span></div>
                <div><span className={styles.blDetailLabel}>Qté facturée</span><span>{ligne.quantite_facturee ?? 0}</span></div>
                <div><span className={styles.blDetailLabel}>Reste à facturer</span><span>{ligne.reste_a_facturer ?? 0}</span></div>
              </div>
            ))}
          </div>
        </section>
        <section className={styles.blDetailSection}>
          <h3>Suivi de facturation</h3>
          <dl className={styles.blDetailFields}>
            <div><dt>Montant des lignes HT</dt><dd>{formatMAD(bl.montant_a_facturer_ht || 0)} MAD</dd></div>
            <div><dt>Déjà facturé HT</dt><dd>{formatMAD(bl.montant_facture_ht || 0)} MAD</dd></div>
            {(bl.montant_brouillon_ht || 0) > 0 &&
              <div><dt>Réservé dans des brouillons HT</dt><dd>{formatMAD(bl.montant_brouillon_ht)} MAD</dd></div>}
            <div><dt>Reste à facturer HT</dt><dd>{formatMAD(bl.reste_a_facturer_ht || 0)} MAD</dd></div>
            {(bl.facture_numeros || []).length > 0 &&
              <div><dt>Factures validées</dt><dd>{bl.facture_numeros.join(', ')}</dd></div>}
          </dl>
        </section>
        {bl.notes && <section className={styles.blDetailSection}><h3>Notes</h3><p className={styles.blDetailNotes}>{bl.notes}</p></section>}
        {bl.bon_commande_id && bl.statut === 'en_preparation' &&
          <p className={styles.blDetailNotice}>
            Le suivi « Livré à 100 % » de la commande compte les quantités inscrites sur ce bon.
            Son statut « En préparation » signifie que son expédition ou sa remise effective n’a pas encore été confirmée. Pour une prestation de services, confirmez sa réalisation.
          </p>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Fermer</button>
        </div>
      </div>
    </Modal>
  )
}

function OngletBonsLivraison({ annee }) {
  const { recharger: rechargerFactures } = useFactures()
  const [expandedPJ, setExpandedPJ] = useState(null)
  const [blDetailId, setBlDetailId] = useState(null)
  const { lignes: bls, loading, erreurLecture, charger } = useListeCommerciale(`/api/bons-livraison?exercice=${annee}`, 'vente')
  const blDetail = bls.find(bl => bl.id === blDetailId)



  const [facturation, setFacturation] = useState(null)
  const [blAFacturer, setBlAFacturer] = useState(null)
  const [reliquatFacturation, setReliquatFacturation] = useState(null)
  const [dateFactureBL, setDateFactureBL] = useState(dateLocaleISO())
  const [qtesFacturees, setQtesFacturees] = useState({})

  async function ouvrirFacturationBL(bl) {
    setDateFactureBL(dateLocaleISO())
    setBlAFacturer(bl); setReliquatFacturation(null); setQtesFacturees({})
    try {
      const r = await apiFetch(`/api/bons-livraison/${bl.id}/reliquat-facturation`)
      setReliquatFacturation(r)
      const init = {}
      ;(r.lignes || []).forEach(l => {
        if ((l.reste_a_facturer || 0) > 0) init[String(l.ligne_bl_id)] = String(l.reste_a_facturer)
      })
      setQtesFacturees(init)
    } catch (e) { notifier.erreur(e.message); setBlAFacturer(null) }
  }

  async function facturerBL() {
    if (!blAFacturer || !reliquatFacturation) return
    const lignes = (reliquatFacturation.lignes || [])
      .map(l => ({ ligne_bl_id: l.ligne_bl_id, quantite: parseFloat(qtesFacturees[String(l.ligne_bl_id)] || 0) }))
      .filter(l => l.quantite > 0)
    if (!lignes.length) { notifier('Saisissez au moins une quantité à facturer.'); return }
    setFacturation(blAFacturer.id)
    try {
      const f = await apiFetch(`/api/bons-livraison/${blAFacturer.id}/convertir-facture`, {
        method: 'POST', body: JSON.stringify({ date: dateFactureBL, lignes })
      })
      notifier(f.numero
        ? `Facture ${f.numero} créée à partir de ${blAFacturer.numero}.`
        : `Brouillon de facture #${f.id} créé à partir de ${blAFacturer.numero}. Validez-le depuis Factures pour obtenir son numéro définitif.`)
      setBlAFacturer(null); setReliquatFacturation(null); setQtesFacturees({})
      // Conversion directe par le BL : actualiser aussi le contexte partagé
      // avec /factures, sans imposer de rafraîchissement du navigateur.
      await rechargerFactures()
      await charger()
    } catch (e) { notifier.erreur(e.message) }
    finally { setFacturation(null) }
  }

  async function changerStatut(bl, statut) {
    // Un BL/BR peut être validé physiquement avant facturation.
    // Le stock suit le document physique si ce mode est activé dans les paramètres.
    try {
      await apiFetch(`/api/bons-livraison/${bl.id}`, { method: 'PATCH', body: JSON.stringify({ statut }) })
      charger()
    } catch (e) { notifier.erreur(e.message) }
  }

  async function supprimer(id) {
    if (!confirm('Supprimer ce bon de livraison ?')) return
    try { await apiFetch(`/api/bons-livraison/${id}`, { method: 'DELETE' }); charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  return (
    <div className={styles.ongletContent}>
      <div className={styles.ongletTopbar}>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={loading}>Actualiser la liste</button>
        <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{loading || erreurLecture ? 'Nombre de livraisons indisponible' : `${bls.length} bon${bls.length !== 1 ? 's' : ''} de livraison`}</span>
      </div>
      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
        ) : erreurLecture ? (
          <ErreurListeCommerciale message={erreurLecture} charger={charger} />
        ) : bls.length === 0 ? (
          <div className={styles.vide}><i className="ti ti-truck" /><span>Aucun bon de livraison</span></div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr>
                <th>N° BL</th><th>Type</th><th>Date</th><th>Tiers</th>
                <th>Transporteur</th><th>Facturation</th><th>Statut</th><th />
              </tr></thead>
              <tbody>
                {bls.map(bl => (
                  <tr key={bl.id}>
                    <td><button type="button" className={styles.blDetailTrigger}
                      onClick={() => setBlDetailId(bl.id)} aria-label={`Consulter le bon ${bl.numero}`}>
                      {bl.numero}
                    </button></td>
                    <td>
                      <span style={{
                        fontSize: 10, padding: '2px 7px', borderRadius: 100,
                        background: bl.type === 'vente' ? '#E6F1FB' : '#EEEDFE',
                        color: bl.type === 'vente' ? '#185FA5' : '#534AB7',
                      }}>
                        {bl.type === 'vente' ? 'Livraison' : 'Réception'}
                      </span>
                    </td>
                    <td className={styles.tdDate}>{formatDate(bl.date)}</td>
                    <td><strong>{bl.tiers}</strong></td>
                    <td style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{bl.transporteur || '—'}</td>
                    <td style={{ fontSize: 11, minWidth: 145 }}>
                      <div className={styles.progressMeta}>
                        <span><strong>{Math.round(bl.facturation_pct || 0)}%</strong> facturé</span>
                        <span>{formatMAD(bl.reste_a_facturer_ht || 0)} MAD HT restant</span>
                      </div>
                      <div className={styles.progressTrack}><span style={{ width: `${Math.min(100, bl.facturation_pct || 0)}%` }} /></div>
                      {(bl.nb_factures || 0) > 0 && <div className={styles.progressNote}>{bl.nb_factures} facture{bl.nb_factures > 1 ? 's' : ''}</div>}
                      {(bl.nb_brouillons || 0) > 0 && (
                        <div className={styles.progressNote}>
                          {bl.nb_brouillons} brouillon{bl.nb_brouillons > 1 ? 's' : ''} · {formatMAD(bl.montant_brouillon_ht || 0)} MAD HT réservé
                        </div>
                      )}
                    </td>
                    <td><Badge statut={bl.statut} map={STATUT_BL} /></td>
                    <td>
                      <div className={styles.rowActions}>
                        <button className={styles.btnAction}
                          onClick={() => telechargerPDF(`/api/bons-livraison/${bl.id}/pdf?exemplaires=2`, `bl_${bl.numero}.pdf`).catch(e => notifier.erreur(e.message))}
                          title="Télécharger PDF (double exemplaire)"><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                        <button className={styles.btnAction}
                          onClick={() => preparerEmailDocument({ endpoint: `/api/bons-livraison/${bl.id}/pdf?exemplaires=2`, nomFichier: `bl_${bl.numero}.pdf`, typeDocument: 'Bon de livraison', numero: bl.numero, tiers: bl.tiers, tiersId: bl.tiers_id }).catch(e => notifier.erreur(e.message))}
                          title="Télécharger le PDF et préparer un e-mail"><i className="ti ti-mail-forward" /><span className="libelle-action" aria-hidden="true">Télécharger le PDF et préparer un e-mail</span></button>
                        {bl.statut === 'en_preparation' && (
                          <button className={styles.btnAction} onClick={() => changerStatut(bl, 'expedie')} title="Confirmer l'expédition ou la prestation réalisée"><i className="ti ti-truck" /><span className="libelle-action" aria-hidden="true">Confirmer l'expédition ou la prestation réalisée</span></button>
                        )}
                        {bl.statut === 'expedie' && (
                          <button className={`${styles.btnAction} ${styles.btnStatusSuccess}`} onClick={() => changerStatut(bl, 'livre')} title="Confirmer la remise au client"><i className="ti ti-check" /><span className="libelle-action" aria-hidden="true">Confirmer la remise au client</span></button>
                        )}
                        {(bl.facturation_reservee_pct || bl.facturation_pct || 0) < 100 && (
                          <button className={styles.btnTransformPrimary}
                            onClick={() => ouvrirFacturationBL(bl)} disabled={facturation === bl.id}
                            title="Facturer tout ou partie du reliquat de ce bon">
                            <i className="ti ti-file-invoice" /> Facturer
                          </button>
                        )}
                        <button className={styles.btnTrash} onClick={() => supprimer(bl.id)} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {blDetail && <DetailBonLivraison bl={blDetail} onFermer={() => setBlDetailId(null)} />}

      {blAFacturer && (
        <Modal titre={`Facturer ${blAFacturer.numero}`} icone="ti-file-invoice" onFermer={() => setBlAFacturer(null)} largeur="lg">
          <div className={styles.formContenu}>
            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor="date-facture-bl">Date de la facture</label>
              <input id="date-facture-bl" className={styles.input} type="date" value={dateFactureBL}
                onChange={e => setDateFactureBL(e.target.value)} />
            </div>
            <div className={styles.sourceInfo}>
              <i className="ti ti-link" /> {blAFacturer.type === 'achat' ? 'Bon de réception' : 'Bon de livraison'} <strong>{blAFacturer.numero}</strong> — {blAFacturer.tiers}
            </div>
            {!reliquatFacturation ? (
              <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
            ) : (
              <>
                <div className={styles.cycleLineTable}>
                  <div className={`${styles.cycleLineHead} ${styles.facturationHead}`}>
                    <span>Article</span><span>Livré</span><span>Déjà facturé</span><span>Reste</span><span>À facturer</span>
                  </div>
                  {(reliquatFacturation.lignes || []).map(l => (
                    <div className={`${styles.cycleLineRow} ${styles.facturationRow}`} key={l.ligne_bl_id}>
                      <span><strong>{l.description}</strong><small>{l.tva ?? 0}% TVA</small></span>
                      <span data-label="Livré / réceptionné">{l.quantite_livree}</span>
                      <span data-label="Déjà facturé">
                        {l.quantite_facturee}
                        {(l.quantite_brouillon || 0) > 0 && <small>+ {l.quantite_brouillon} brouillon</small>}
                      </span>
                      <span data-label="Reste à facturer" className={(l.reste_a_facturer || 0) > 0 ? styles.resteActif : ''}>{l.reste_a_facturer}</span>
                      <span data-label="À facturer">
                        {(l.reste_a_facturer || 0) > 0 ? (
                          <input type="number" min="0" max={l.reste_a_facturer} step="0.01"
                            value={qtesFacturees[String(l.ligne_bl_id)] ?? ''}
                            onChange={e => setQtesFacturees(p => ({ ...p, [String(l.ligne_bl_id)]: e.target.value }))}
                            className={styles.quantiteInput} />
                        ) : 'soldé'}
                      </span>
                    </div>
                  ))}
                </div>
                <div className={styles.cycleSummary}>
                  <span>Facturé <strong>{Math.round(reliquatFacturation.facturation_pct || 0)}%</strong></span>
                  <span>Déjà facturé <strong>{formatMAD(reliquatFacturation.montant_facture_ht || 0)} MAD HT</strong></span>
                  {(reliquatFacturation.montant_brouillon_ht || 0) > 0 && <span>En brouillon <strong>{formatMAD(reliquatFacturation.montant_brouillon_ht)} MAD HT</strong></span>}
                  <span>Reste <strong>{formatMAD(reliquatFacturation.reste_a_facturer_ht || 0)} MAD HT</strong></span>
                </div>
                <p className={styles.helperText}>
                  Vous pouvez facturer seulement une partie des quantités livrées/réceptionnées. Le reliquat restera disponible pour une facture ultérieure.
                </p>
              </>
            )}
            <div className={styles.formActions}>
              <button className={styles.btnSec} onClick={() => setBlAFacturer(null)}>Annuler</button>
              <button className={styles.btnPrim} onClick={facturerBL} disabled={!dateFactureBL || !reliquatFacturation || facturation === blAFacturer.id}>
                <i className="ti ti-file-invoice" /> Créer la facture
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

// ─── Recherche de facture pour lier un règlement ─────────────────────────────
// ─── Formulaire règlement complet ────────────────────────────────────────────
function FormulaireReglementComplet({ annee, onFermer, onSuccess, typeForce = null }) {
  const [toutesFactures, setToutesFactures] = useState([])
  const [banques,        setBanques]        = useState([])
  const [tiers,          setTiers]          = useState('')
  const [factureId,      setFactureId]      = useState('')
  const [factureSelectee, setFactureSelectee] = useState(null)
  const [situation, setSituation] = useState(null)
  const [loadingSituation, setLoadingSituation] = useState(false)
  const [form, setForm] = useState({
    date: dateLocaleISO(),
    montant: '', mode: 'virement', reference: '', banque: '', date_echeance: '', notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')

  // Charger toutes les factures ouvertes + banques
  useEffect(() => {
    facturesAPI.listerTout(annee)
      .then(data => setToutesFactures(
        data
          .filter(f => f.statut === 'en_attente' || f.statut === 'partiellement_payee')
          .filter(f => !typeForce || f.type === typeForce)
      )).catch(() => {})
    apiFetch('/api/banques').then(setBanques).catch(() => {})
  }, [annee])

  // Factures filtrées par tiers sélectionné
  const facturesDuTiers = useMemo(() =>
    tiers ? toutesFactures.filter(f => f.tiers === tiers) : toutesFactures
  , [toutesFactures, tiers])

  // La situation serveur inclut les avoirs, acomptes et RAS réellement imputée.
  useEffect(() => {
    let annule = false
    setSituation(null); setErreur('')
    if (!factureSelectee) { setLoadingSituation(false); return }
    setLoadingSituation(true)
    apiFetch(`/api/factures/${factureSelectee.id}/reglements`)
      .then(data => { if (!annule) setSituation(data) })
      .catch(e => { if (!annule) setErreur(e.message) })
      .finally(() => { if (!annule) setLoadingSituation(false) })
    return () => { annule = true }
  }, [factureSelectee])

  // Montant déjà réglé
  const dejaRegle = situation?.total_regle ?? 0
  const resteFacture = typeof situation?.solde_restant === 'number' && Number.isFinite(situation.solde_restant) ? situation.solde_restant : null

  // Quand tiers change → reset facture
  function handleTiers(val) {
    setTiers(val)
    setFactureId('')
    setFactureSelectee(null)
  }

  // Quand facture sélectionnée → pré-remplir montant restant
  function handleSelectFacture(id) {
    setFactureId(id)
    if (!id) { setFactureSelectee(null); return }
    const f = facturesDuTiers.find(f => String(f.id) === String(id))
    if (f) {
      setFactureSelectee(f)
      setForm(p => ({ ...p, montant: '', mode: f.mode_reglement_prevu || p.mode, reference: f.reference_reglement_prevue || p.reference }))
    }
  }

  // Recalculer montant quand règlements chargés
  useEffect(() => {
    if (resteFacture !== null) {
      setForm(p => ({ ...p, montant: resteFacture.toFixed(2) }))
    }
  }, [resteFacture])

  const montantNum = parseFloat(form.montant) || 0
  const modeAvecBanque = ['virement', 'cheque', 'effet', 'carte', 'prelevement'].includes(form.mode)

  async function handleSave() {
    if (resteFacture === null || loadingSituation) { setErreur('Situation de paiement indisponible. Vérifiez les données avant tout règlement.'); return }
    if (montantNum > resteFacture + 0.01) { setErreur(`Le règlement dépasse le reste à payer (${formatMAD(resteFacture)} MAD).`); return }
    if (!tiers.trim())          { setErreur('Le tiers est obligatoire'); return }
    if (!factureId || !factureSelectee) { setErreur('Sélectionnez la facture à régler'); return }
    if (!montantNum || montantNum <= 0) { setErreur('Le montant doit être positif'); return }
    if (form.mode === 'effet' && !form.date_echeance) { setErreur("La date d'échéance est obligatoire pour un effet de commerce."); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch('/api/reglements', {
        method: 'POST',
        body: JSON.stringify({
          facture_id: parseInt(factureId),
          tiers,
          date:       form.date,
          montant:    montantNum,
          mode:       form.mode,
          reference:  form.reference || null,
          banque:     form.banque    || null,
          date_echeance: form.date_echeance || null,
          notes:      form.notes     || null,
        }),
      })
      onSuccess(); onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  const MODES = [
    { val: 'virement', label: 'Virement' },
    { val: 'cheque',   label: 'Chèque' },
    { val: 'especes',  label: 'Espèces' },
    { val: 'effet',    label: 'Effet' },
    { val: 'carte',    label: 'Carte' },
    { val: 'prelevement', label: 'Prélèvement' },
    { val: 'autre',    label: 'Autre' },
  ]

  return (
    <Modal titre="Nouveau règlement" icone="ti-coin" onFermer={onFermer} largeur="md">
      <div className={styles.formContenu}>

        {/* ÉTAPE 1 — Tiers */}
        <div className={styles.formGroup}>
          <label className={styles.label}>
            <i className="ti ti-user" style={{ marginRight: 4, fontSize: 11 }} />
            {typeForce === 'vente' ? 'Client *' : typeForce === 'achat' ? 'Fournisseur *' : 'Client / Fournisseur *'}
          </label>
          <TiersPicker
            value={tiers}
            type={typeForce || 'tous'}
            onChange={handleTiers}
            onSelect={t => { if (t) handleTiers(t.nom) }}
            placeholder={typeForce === 'vente' ? 'Rechercher le client à encaisser…' : typeForce === 'achat' ? 'Rechercher le fournisseur à payer…' : 'Rechercher un client ou fournisseur…'}
          />
          {toutesFactures.length === 0 && (
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
              Aucune facture ouverte pour {annee}
            </div>
          )}
        </div>

        {/* ÉTAPE 2 — Facture du tiers */}
        {tiers && (
          <div className={styles.formGroup}>
            <label className={styles.label}>
              <i className="ti ti-file-invoice" style={{ marginRight: 4, fontSize: 11 }} />
              Facture à régler
              {facturesDuTiers.length === 0 && (
                <span style={{ marginLeft: 8, fontSize: 10, color: 'var(--text-tertiary)' }}>
                  (aucune facture ouverte pour ce tiers)
                </span>
              )}
            </label>
            <select className={styles.input} value={factureId} onChange={e => handleSelectFacture(e.target.value)}
              disabled={facturesDuTiers.length === 0}>
              <option value="">— Choisir une facture —</option>
              {facturesDuTiers.map(f => {
                const deja = 0 // sera recalculé après chargement
                return (
                  <option key={f.id} value={f.id} disabled={f.montants_valides === false}>
                    {f.numero} · {formatMAD(f.total_ttc)} MAD
                    {f.statut === 'partiellement_payee' ? ' (partiellement payée)' : ''}
                  </option>
                )
              })}
            </select>
          </div>
        )}

        {/* ÉTAPE 3 — Panneau de la facture sélectionnée */}
        {factureSelectee && (
          <div style={{
            borderRadius: 8, padding: '12px 14px', fontSize: 12,
            background: resteFacture !== null && montantNum >= resteFacture ? '#EAF3DE' : '#EFF6FF',
            border: `1px solid ${resteFacture !== null && montantNum >= resteFacture ? '#A7D87A' : '#B5D4F4'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'monospace', background: 'var(--blue-light)', color: 'var(--blue)', padding: '1px 6px', borderRadius: 3, fontSize: 11 }}>
                  {factureSelectee.numero}
                </span>
                <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{factureSelectee.date}</span>
              </div>
              <strong>{formatMAD(factureSelectee.total_ttc)} MAD TTC</strong>
            </div>
            <div style={{ display: 'flex', gap: 20, fontSize: 11 }}>
              {dejaRegle > 0 && (
                <span style={{ color: '#3B6D11' }}>
                  Déjà réglé : <strong>{formatMAD(dejaRegle)} MAD</strong>
                </span>
              )}
              {resteFacture !== null && resteFacture > 0 && (
                <span style={{ color: '#854F0B', fontWeight: 600 }}>
                  Reste à payer : <strong>{formatMAD(resteFacture)} MAD</strong>
                </span>
              )}
              {resteFacture !== null && resteFacture <= 0 && (
                <span style={{ color: '#3B6D11', fontWeight: 600 }}>
                  <i className="ti ti-circle-check" style={{ marginRight: 3 }} />Déjà soldée
                </span>
              )}
              {resteFacture === null && <span>{loadingSituation ? 'Calcul du solde…' : 'Reste à payer : à vérifier'}</span>}
            </div>
            <ResumeRASSituation situation={situation} />
          </div>
        )}

        {/* Montant + date + mode */}
        <div className={styles.formGrid3}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Montant (MAD) *</label>
            <input className={styles.input} type="number" min="0" step="0.01" placeholder="0.00"
              value={form.montant} onChange={e => setForm(p => ({ ...p, montant: e.target.value }))} />
            {factureSelectee && resteFacture !== null && montantNum > 0 && (
              <div style={{ fontSize: 10, marginTop: 3, color: montantNum >= resteFacture ? '#3B6D11' : '#185FA5' }}>
                {montantNum >= resteFacture
                  ? '✓ Solde total'
                  : `Reste après : ${formatMAD(Math.max(0, resteFacture - montantNum))} MAD`}
              </div>
            )}
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date *</label>
            <input className={styles.input} type="date" value={form.date}
              onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
            <div className={styles.fieldHint}>La date doit appartenir à un exercice comptable ouvert.</div>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mode de paiement</label>
            <select className={styles.input} value={form.mode}
              onChange={e => setForm(p => ({ ...p, mode: e.target.value }))}>
              {MODES.map(m => <option key={m.val} value={m.val}>{m.label}</option>)}
            </select>
          </div>
        </div>

        {/* Référence + Banque */}
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Référence</label>
            <input className={styles.input} placeholder="N° chèque, virement..."
              value={form.reference} onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>
              <i className="ti ti-building-bank" style={{ marginRight: 4, fontSize: 11 }} />
              Banque
            </label>
            {banques.length > 0 && modeAvecBanque ? (
              <select className={styles.input} value={form.banque}
                onChange={e => setForm(p => ({ ...p, banque: e.target.value }))}>
                <option value="">— Choisir une banque —</option>
                {banques.map(b => (
                  <option key={b.id} value={b.banque}>
                    {b.banque}{b.agence ? ` — ${b.agence}` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <input className={styles.input} placeholder="Nom de la banque..."
                value={form.banque} onChange={e => setForm(p => ({ ...p, banque: e.target.value }))} />
            )}
          </div>
        </div>

        {['effet', 'cheque'].includes(form.mode) && (
          <div className={styles.formGroup}>
            <label className={styles.label}>Échéance {form.mode === 'effet' ? '*' : '(chèque postdaté)'}</label>
            <input className={styles.input} type="date" min={form.date || undefined} value={form.date_echeance || ''}
              onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
          </div>
        )}

        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave}
            disabled={!form.montant || !tiers.trim() || loading || loadingSituation || resteFacture === null}>
            {loading ? 'Enregistrement...' : <><i className="ti ti-check" /> Enregistrer le règlement</>}
          </button>
        </div>
      </div>
    </Modal>
  )
}


// ─── Formulaire édition règlement ────────────────────────────────────────────
function FormulaireEditionReglement({ reglement, onFermer, onSuccess }) {
  const [banques, setBanques] = useState([])
  useEffect(() => { apiFetch('/api/banques').then(setBanques).catch(() => {}) }, [])
  const [form, setForm] = useState({
    date:      reglement.date      || dateLocaleISO(),
    montant:   reglement.montant   || '',
    mode:      reglement.mode      || 'virement',
    reference: reglement.reference || '',
    banque:    reglement.banque    || '',
    date_echeance: reglement.date_echeance ? String(reglement.date_echeance).slice(0, 10) : '',
    notes:     reglement.notes     || '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')
  const MODES = ['virement', 'cheque', 'especes', 'effet', 'carte', 'prelevement', 'autre']

  async function handleSave() {
    if (!form.montant) return
    // L'échéance conditionne l'encaissement d'un effet : elle ne peut pas être vide.
    if (form.mode === 'effet' && !form.date_echeance) {
      setErreur("La date d'échéance est obligatoire pour un effet de commerce.")
      return
    }
    setLoading(true); setErreur('')
    try {
      await apiFetch(`/api/reglements/${reglement.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...form, montant: parseFloat(form.montant) }),
      })
      onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={`Modifier règlement`} icone="ti-pencil" onFermer={onFermer} largeur="md">
      <div className={styles.formContenu}>
        <div className={styles.sourceInfo}>
          <i className="ti ti-coin" /> Règlement — {reglement.tiers}
          <span style={{ marginLeft: 'auto', fontWeight: 600 }}>{formatMAD(reglement.montant)} MAD</span>
        </div>
        <div className={styles.formGrid3}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Montant *</label>
            <input className={styles.input} type="number" min="0" step="0.01"
              value={form.montant} onChange={e => setForm(p => ({ ...p, montant: e.target.value }))} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Date *</label>
            <input className={styles.input} type="date" value={form.date}
              onChange={e => setForm(p => ({ ...p, date: e.target.value }))} />
            <div className={styles.fieldHint}>La date doit appartenir à un exercice comptable ouvert.</div>
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mode</label>
            <select className={styles.input} value={form.mode}
              onChange={e => setForm(p => ({ ...p, mode: e.target.value }))}>
              {MODES.map(m => <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>)}
            </select>
          </div>
        </div>
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Référence</label>
            <input className={styles.input} value={form.reference}
              onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} />
          </div>
          {['effet', 'cheque'].includes(form.mode) && (
            <div className={styles.formGroup}>
              <label className={styles.label}>
                Date d&apos;échéance {form.mode === 'effet' && '*'}
              </label>
              <input className={styles.input} type="date" value={form.date_echeance}
                onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} />
              <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 3 }}>
                {form.mode === 'effet'
                  ? "L'encaissement ne sera possible qu'à partir de cette date."
                  : 'Pour un chèque post-daté (optionnel).'}
              </span>
            </div>
          )}
          <div className={styles.formGroup}>
            <label className={styles.label}>Banque</label>
            {banques.length > 0 && ['virement', 'cheque', 'effet', 'carte', 'prelevement'].includes(form.mode) ? (
              <select className={styles.input} value={form.banque}
                onChange={e => setForm(p => ({ ...p, banque: e.target.value }))}>
                <option value="">— Choisir une banque —</option>
                {banques.map(b => (
                  <option key={b.id} value={b.banque}>{b.banque}{b.agence ? ` — ${b.agence}` : ''}</option>
                ))}
              </select>
            ) : (
              <input className={styles.input} placeholder="Nom de la banque..."
                value={form.banque} onChange={e => setForm(p => ({ ...p, banque: e.target.value }))} />
            )}
          </div>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="reglement-edition-notes">Commentaire</label>
          <textarea id="reglement-edition-notes" className={styles.input} rows={3}
            value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
        </div>
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" /> {erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave} disabled={!form.montant || loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

function FormulaireRASReglement({ reglement, onFermer, onSuccess }) {
  const [modeRas, setModeRas] = useState('libre')
  const [captureTvaEnCours, setCaptureTvaEnCours] = useState(false)
  const [capacites, setCapacites] = useState(null)
  const [comptes, setComptes] = useState([])
  const [erreur, setErreur] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [form, setForm] = useState({ montant: '', date_operation: reglement.date, reference: '', compte_destination: '' })
  const actif = useRef(true)
  const jeton = useRef(TOKEN())
  useEffect(() => {
    actif.current = true
    let annule = false
    Promise.all([apiFetch(`/api/reglements/${reglement.id}/ras`), apiFetch('/api/plan-comptable?inclure_inactifs=false')])
      .then(([data, plan]) => { if (!annule && TOKEN() === jeton.current) { setCapacites(data); setComptes(plan.filter(c => c.actif)) } })
      .catch(e => { if (!annule && TOKEN() === jeton.current) setErreur(e.message) })
    return () => { annule = true; actif.current = false }
  }, [reglement.id])
  const existante = capacites?.captures?.length > 0
  const admissible = capacites?.disponible && capacites.peut_capturer && !existante && peutEcrire() &&
    reglement.est_comptabilisee && reglement.statut === 'complet' && capacites.modes_admis?.includes(reglement.mode)
  const changer = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  async function enregistrer(e) {
    e.preventDefault()
    const montant = Number(form.montant)
    if (!form.montant.trim() || !Number.isFinite(montant) || montant <= 0 || Math.abs(montant * 100 - Math.round(montant * 100)) > 1e-7) {
      setErreur('Saisissez un montant fini, positif et au centime.'); return
    }
    if (!admissible || TOKEN() !== jeton.current) return
    setEnvoi(true); setErreur('')
    try {
      await apiFetch(`/api/reglements/${reglement.id}/ras`, { method: 'POST', body: JSON.stringify({ ...form, montant: form.montant }) })
      if (actif.current && TOKEN() === jeton.current) { onSuccess(); onFermer() }
    } catch (e) { if (actif.current && TOKEN() === jeton.current) setErreur(e.message) }
    finally { if (actif.current && TOKEN() === jeton.current) setEnvoi(false) }
  }
  return <Modal titre="RAS déclarée sur règlement" onFermer={() => { if (!captureTvaEnCours) onFermer() }} largeur="lg">
    <div style={{ display: 'grid', gap: 16, minWidth: 0 }}>
    {admissible && <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }} aria-label="Mode de saisie RAS">
      <button type="button" disabled={captureTvaEnCours} className={modeRas === 'libre' ? styles.btnPrim : styles.btnSec} onClick={() => setModeRas('libre')}>Saisie déclarative libre</button>
      <button type="button" disabled={captureTvaEnCours} className={modeRas === 'tva' ? styles.btnPrim : styles.btnSec} onClick={() => setModeRas('tva')}>RAS TVA guidée</button>
    </div>}
    {modeRas === 'tva' && admissible ? <RasTvaReglement reglement={reglement} comptes={comptes} onOccupation={setCaptureTvaEnCours} onSuccess={() => { onSuccess(); onFermer() }} /> :
    <form onSubmit={enregistrer} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <InlineNotice tone="info">{existante ? 'Capture déclarative conservée avec sa piste d’audit.' : 'Saisie déclarative libre sans calcul de taux ni prorata.'} Le compte doit être justifié par votre opération. L’OD est à contrôler et à valider dans le journal ; aucune attestation fiscale n’est validée ici.</InlineNotice>
      {erreur && <div role="alert" style={{ color: 'var(--red)' }}>{erreur}</div>}
      {!capacites && !erreur && <p>Chargement de la disponibilité…</p>}
      {capacites && !capacites.disponible && <div role="alert">Capture indisponible : migration {capacites.migration_requise} à appliquer manuellement par votre administrateur. Aucune migration n'est exécutée par cet écran.</div>}
      {capacites?.captures?.map(c => <div key={c.id} style={{ padding: 12, border: '1px solid var(--border-light)', borderRadius: 8 }}>
        <strong>{formatMAD(Number(c.montant))} MAD · {c.reference}</strong>
        <div>{formatDate(c.date_operation)} · Compte {c.compte_destination}</div>
        <div>OD #{c.ecriture_id} · {c.ecriture_est_validee === true ? 'Validée' : c.ecriture_est_validee === false ? 'À contrôler et à valider' : 'Statut à consulter dans le journal'}</div>
        {c.annulation_id && <div>Annulée par contrepassation #{c.ecriture_annulation_id} ; historique conservé.</div>}
      </div>)}
      {capacites?.disponible && !existante && !admissible && <p>La saisie exige un règlement immédiat comptabilisé et complet, par virement ou espèces, et une permission d'écriture.</p>}
      {capacites?.disponible && !existante && capacites.blocages?.length > 0 && <div role="alert">{capacites.blocages.join(' · ')}</div>}
      {admissible && <FormSection title="Montant effectivement déclaré">
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}><label className={styles.label} htmlFor="ras-montant">Montant RAS *</label><input className={styles.input} id="ras-montant" name="montant" type="number" step="0.01" min="0.01" required value={form.montant} onChange={changer} /></div>
          <div className={styles.formGroup}><label className={styles.label} htmlFor="ras-date">Date de l'opération RAS *</label><input className={styles.input} id="ras-date" name="date_operation" type="date" required value={form.date_operation} onChange={changer} /></div>
          <div className={styles.formGroup}><label className={styles.label} htmlFor="ras-reference">Référence RAS *</label><input className={styles.input} id="ras-reference" name="reference" maxLength={100} required value={form.reference} onChange={changer} /></div>
          <div className={styles.formGroup}><label className={styles.label} htmlFor="ras-compte">Compte destination RAS *</label><select className={styles.input} id="ras-compte" name="compte_destination" required value={form.compte_destination} onChange={changer}><option value="">Choisir explicitement un compte</option>{comptes.map(c => <option key={c.numero} value={c.numero}>{c.numero} — {c.libelle}</option>)}</select></div>
        </div>
      </FormSection>}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className={styles.btnSec} type="button" onClick={onFermer}>Fermer</button>
        {admissible && <button className={styles.btnPrim} type="submit" disabled={envoi}>{envoi ? 'Préparation…' : 'Préparer la RAS déclarée'}</button>}
      </div>
    </form>}
    {existante && <RasTvaReglement reglement={reglement} consultation />}
    </div>
  </Modal>
}

function OngletReglements({ annee, typeForce = null }) {
  const [erreurChargement, setErreurChargement] = useState('')
  const [annulation, setAnnulation] = useState(null)
  const [annulationEnCours, setAnnulationEnCours] = useState(false)
  const [erreurAnnulation, setErreurAnnulation] = useState('')
  const generationAnnulation = useRef(0)
  const verrouAnnulation = useRef(false)
  const [reglements, setReglements] = useState([])
  const [annulationLotEnCours, setAnnulationLotEnCours] = useState(false)
  const generationChargementReglements = useRef(0)
  const generationAnnulationLot = useRef(0)
  const contexteAnnulationLot = useRef(null)
  const tokenAnnulationLot = TOKEN()
  contexteAnnulationLot.current = { annee, typeForce, token: tokenAnnulationLot }
  useEffect(() => {
    setAnnulationLotEnCours(false)
    setAnnulation(null)
    setAnnulationEnCours(false)
    setErreurAnnulation('')
    verrouAnnulation.current = false
    return () => { generationAnnulationLot.current += 1; generationAnnulation.current += 1 }
  }, [annee, typeForce, tokenAnnulationLot])
  const [facturesMap, setFacturesMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [ventiler, setVentiler] = useState(false)
  const [recherche, setRecherche] = useState('')
  const [filtreMode, setFiltreMode] = useState('TOUS')
  const [reglEdit, setReglEdit] = useState(null)
  const [rasReglement, setRasReglement] = useState(null)
  const { recharger: rechargerFactures } = useFactures()
  useEffect(() => { setRasReglement(null) }, [annee, typeForce])

  async function charger() {
    const token = TOKEN()
    if (annee !== contexteAnnulationLot.current?.annee
      || typeForce !== contexteAnnulationLot.current?.typeForce
      || token !== contexteAnnulationLot.current?.token) return
    const generation = ++generationChargementReglements.current
    const courant = () => generation === generationChargementReglements.current
      && annee === contexteAnnulationLot.current?.annee
      && typeForce === contexteAnnulationLot.current?.typeForce
      && token === TOKEN()
    if (!courant()) return
    setLoading(true)
    setErreurChargement('')
    try {
      const [d, f] = await Promise.all([
        apiFetch(`/api/reglements?exercice=${annee}`),
        facturesAPI.listerTout(annee),
      ])
      if (!courant()) return
      // Cumul règlements par facture
      const cumuls = {}
      d.forEach(r => {
        if (r.facture_id && !['rejete', 'annule'].includes(r.statut)) {
          const connu = r.montant_valide !== false && r.montant != null && Number.isFinite(r.montant)
          cumuls[r.facture_id] = !connu || cumuls[r.facture_id] === null
            ? null : (cumuls[r.facture_id] ?? 0) + r.montant
        }
      })
      const facMap = Object.fromEntries(f.map(fac => [fac.id, { ...fac, cumul: Object.hasOwn(cumuls, fac.id) ? cumuls[fac.id] : 0 }]))
      // Un règlement de N peut solder une facture de N-1. L'API expose son
      // lien natif et sa qualification actuelle, indépendamment du filtre N.
      d.forEach(r => {
        if (r.facture_id && !facMap[r.facture_id] && r.facture_type) {
          facMap[r.facture_id] = {
            numero: r.facture_numero, type: r.facture_type, exercice: r.facture_exercice,
            statut: r.facture_statut, montants_valides: r.facture_montants_valides === true,
            cumul: Object.hasOwn(cumuls, r.facture_id) ? cumuls[r.facture_id] : 0,
          }
        }
      })
      setFacturesMap(facMap)

      // Filtrer par type si typeForce défini
      // FACT-H : tout règlement est obligatoirement rattaché à une facture ;
      // son sens vente/achat est donc déterminé sans ambiguïté par celle-ci.
      const reglsFiltres = typeForce
        ? [...d].filter(r => {
            const fac = facMap[r.facture_id]
            return fac?.type === typeForce
          })
        : [...d]
      setReglements(reglsFiltres)
    }
    catch {
      if (courant()) {
        setReglements([])
        setErreurChargement('Chargement des règlements impossible. La liste et le total ne sont pas disponibles.')
      }
    }
    finally { if (courant()) setLoading(false) }
  }

  useEffect(() => {
    charger()
    return () => { generationChargementReglements.current += 1 }
  }, [annee, typeForce, tokenAnnulationLot])

  async function supprimer(id) {
    const r = reglements.find(x => x.id === id)
    const detail = r ? `

${r.tiers || 'Tiers'} — ${formatMAD(r.montant)} MAD — ${r.mode || ''} du ${String(r.date || '').split('-').reverse().join('/')}` : ''
    if (!confirm(`Supprimer ce règlement non comptabilisé ?${detail}

Aucune écriture n'est touchée ; la facture redevient due de ce montant.`)) return
    try { await apiFetch(`/api/reglements/${id}`, { method: 'DELETE' }); charger() }
    catch (e) { notifier.erreur(e.message || 'Suppression impossible.') }
  }

  function annulerReglement(r) {
    setErreurAnnulation('')
    setAnnulation({ reglement: r, date: dateLocaleISO(), motif: '', contexte: { ...contexteAnnulationLot.current } })
  }

  async function confirmerAnnulation(e) {
    e.preventDefault()
    if (!annulation || verrouAnnulation.current) return
    const { reglement: r, contexte, date, motif } = annulation
    const generation = ++generationAnnulation.current
    const courant = () => generation === generationAnnulation.current
      && contexte.annee === contexteAnnulationLot.current?.annee
      && contexte.typeForce === contexteAnnulationLot.current?.typeForce
      && contexte.token === contexteAnnulationLot.current?.token && contexte.token === TOKEN()
    if (!courant()) return
    verrouAnnulation.current = true
    setAnnulationEnCours(true)
    setErreurAnnulation('')
    try {
      await apiFetch(annulation.lot ? `/api/reglements/par-tiers/${annulation.lot}/annuler` : `/api/reglements/${r.id}/annuler`, {
        method: 'POST',
        body: JSON.stringify({ date_annulation: date, motif: motif.trim() || null }),
      })
      if (!courant()) return
      setAnnulation(null)
      await charger()
      if (courant()) await rechargerFactures()
    } catch (e) { if (courant()) setErreurAnnulation(e.message || 'Annulation impossible.') }
    finally {
      if (courant()) { verrouAnnulation.current = false; setAnnulationEnCours(false) }
    }
  }

  const lots = useMemo(() => {
    const groupes = {}
    reglements.forEach(r => {
      const match = /^VT-([a-f0-9]{32})-\d{2}$/.exec(r.numero || '')
      if (match) (groupes[match[1]] ||= []).push(r)
    })
    const premiers = {}
    Object.entries(groupes).forEach(([id, rows]) => {
      if (rows.some(r => r.statut === 'complet')) {
        const premier = [...rows].sort((a, b) => a.numero.localeCompare(b.numero))[0]
        premiers[premier.id] = id
      }
    })
    return premiers
  }, [reglements])

  async function annulerLot(id) {
    if (annulationLotEnCours) return
    const generation = ++generationAnnulationLot.current
    const contexte = { ...contexteAnnulationLot.current }
    const courant = () => generation === generationAnnulationLot.current
      && contexte.annee === contexteAnnulationLot.current.annee
      && contexte.typeForce === contexteAnnulationLot.current.typeForce
      && contexte.token === TOKEN()
    setAnnulationLotEnCours(true)
    try {
      // Relire le lot entier, même si les filtres masquent certaines lignes.
      const rows = await apiFetch(`/api/reglements/par-tiers/${id}`)
      if (!courant()) return
      if (rows.some(r => r.montant_valide === false || !Number.isFinite(r.montant) || r.statut !== 'complet')) {
        throw new Error('Lot incomplet, partiellement annulé ou montant à vérifier : consulter chaque règlement.')
      }
      const centimes = rows.reduce((s, r) => s + Math.round(r.montant * 100), 0)
      if (!Number.isSafeInteger(centimes)) throw new Error('Total du lot hors limites : vérifier chaque règlement.')
      if (!courant()) return
      setErreurAnnulation('')
      setAnnulation({
        lot: id, lignes: rows, reglement: { montant: centimes / 100, tiers: rows[0]?.tiers },
        date: dateLocaleISO(), motif: '', contexte,
      })
    } catch (e) { if (courant()) notifier.erreur(e.message || 'Annulation de la ventilation impossible.') }
    finally { if (generation === generationAnnulationLot.current) setAnnulationLotEnCours(false) }
  }

  const filtres = useMemo(() => reglements.filter(r => {
    const okRecherche = !recherche ||
      r.tiers.toLowerCase().includes(recherche.toLowerCase()) ||
      (r.reference || '').toLowerCase().includes(recherche.toLowerCase())
    const okMode = filtreMode === 'TOUS' || r.mode === filtreMode
    return okRecherche && okMode
  }), [reglements, recherche, filtreMode])

  const totalRegle = useMemo(() => {
    if (loading || erreurChargement) return null
    const actifs = filtres.filter(r => !['rejete', 'annule'].includes(r.statut))
    if (actifs.some(r => r.montant_valide === false || r.montant == null || !Number.isFinite(r.montant))) return null
    const total = actifs.reduce((s, r) => s + r.montant, 0)
    return Number.isFinite(total) ? total : null
  }, [filtres, loading, erreurChargement])

  const ICONES_MODE = {
    virement: 'ti-building-bank', cheque: 'ti-writing', especes: 'ti-cash',
    effet: 'ti-clock', carte: 'ti-credit-card', prelevement: 'ti-repeat', autre: 'ti-dots'
  }
  const MODES_FILTRES = ['TOUS', 'virement', 'cheque', 'especes', 'effet', 'carte', 'prelevement', 'autre']

  return (
    <div className={styles.ongletContent}>
      {annulation && <Modal titre={annulation.lot ? 'Annuler toute la ventilation' : 'Annuler le règlement'} icone="ti-arrow-back-up" onFermer={() => { if (!verrouAnnulation.current) setAnnulation(null) }}>
        <form onSubmit={confirmerAnnulation}>
          <InlineNotice tone="info">Contrepasser {formatMAD(annulation.reglement.montant)} MAD pour {annulation.reglement.tiers}. La RAS liée sera également contrepassée. Les écritures d’origine sont conservées ; les contrepassations seront à valider dans le journal.</InlineNotice>
          {annulation.lot && <div>
            <p>Toute la ventilation sera annulée : {annulation.lignes.length} règlement(s), y compris les lignes masquées par les filtres.</p>
            <ul>{annulation.lignes.map(r => <li key={r.id}>{r.numero} · {formatMAD(r.montant)} MAD</li>)}</ul>
          </div>}
          {erreurAnnulation && <div role="alert"><InlineNotice tone="danger">{erreurAnnulation}</InlineNotice></div>}
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="annulation-reglement-date">Date d’annulation *</label>
            <input id="annulation-reglement-date" className={styles.input} type="date" required disabled={annulationEnCours} value={annulation.date} onChange={e => setAnnulation({ ...annulation, date: e.target.value })} />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="annulation-reglement-motif">Motif (facultatif)</label>
            <textarea id="annulation-reglement-motif" className={styles.input} rows={3} maxLength={500} disabled={annulationEnCours} value={annulation.motif} onChange={e => setAnnulation({ ...annulation, motif: e.target.value })} />
          </div>
          <div className={styles.formActions}>
            <button type="button" className={styles.btnSec} disabled={annulationEnCours} onClick={() => setAnnulation(null)}>Fermer</button>
            <button type="submit" className={styles.btnPrim} disabled={annulationEnCours}>{annulationEnCours ? 'Annulation en cours…' : 'Confirmer l’annulation'}</button>
          </div>
        </form>
      </Modal>}
      {ventiler && <ReglementParTiers annee={annee} typeForce={typeForce} onFermer={() => setVentiler(false)} onSuccess={() => { charger(); rechargerFactures() }} />}
      {rasReglement && <FormulaireRASReglement reglement={rasReglement} onFermer={() => setRasReglement(null)} onSuccess={() => { charger(); rechargerFactures() }} />}
      {reglEdit && (
        <FormulaireEditionReglement
          reglement={reglEdit}
          onFermer={() => setReglEdit(null)}
          onSuccess={() => { setReglEdit(null); charger() }}
        />
      )}
      <div className={styles.ongletTopbar} style={{ flexWrap: 'wrap' }}>
        <div className={styles.recherche}>
          <i className="ti ti-search" />
          <input type="text" placeholder="Chercher par tiers ou référence..."
            value={recherche} onChange={e => setRecherche(e.target.value)}
            className={styles.inputRecherche} />
        </div>
        {peutEcrire() && typeForce && <button className={styles.btnPrim} onClick={() => setVentiler(true)}>Ventiler par tiers</button>}
        <span style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 5, flex: '1 1 240px', minWidth: 0 }}>
          <i className="ti ti-info-circle" />
          Pour encaisser, ouvrez la facture concernée et cliquez sur « Encaisser »
        </span>
      </div>

      {/* Filtres mode + stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button type="button" className={styles.btnSec} aria-label="Actualiser les règlements" onClick={charger} disabled={loading}>
          <i className="ti ti-refresh" aria-hidden="true" /> Actualiser
        </button>
        {MODES_FILTRES.map(m => (
          <button key={m}
            onClick={() => setFiltreMode(m)}
            style={{
              fontSize: 11, padding: '4px 10px', borderRadius: 100, cursor: 'pointer', border: '0.5px solid',
              background: filtreMode === m ? 'var(--blue)' : 'var(--bg-primary)',
              color: filtreMode === m ? '#fff' : 'var(--text-secondary)',
              borderColor: filtreMode === m ? 'var(--blue)' : 'var(--border-medium)',
            }}>
            {m === 'TOUS' ? 'Tous modes' : m.charAt(0).toUpperCase() + m.slice(1)}
          </button>
        ))}
        {!loading && !erreurChargement && totalRegle === null && <span role="alert" style={{ color: 'var(--red)' }}>
          Total à vérifier : un règlement historique contient un montant invalide.
        </span>}
        {totalRegle > 0 && (
          <span style={{ marginLeft: 'auto', fontSize: 13, fontWeight: 600, color: 'var(--green)' }}>
            {formatMAD(totalRegle)} MAD
          </span>
        )}
      </div>

      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
        ) : erreurChargement ? (
          <div className={styles.vide} role="alert">
            <InlineNotice tone="danger">{erreurChargement}</InlineNotice>
            <button type="button" className={styles.btnSec} onClick={charger}>Réessayer</button>
          </div>
        ) : filtres.length === 0 ? (
          <div className={styles.vide}><i className="ti ti-coin" /><span>Aucun règlement trouvé</span></div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr>
                <th>Date</th>
                <th>Tiers</th>
                <th>Facture liée</th>
                <th>Mode</th>
                <th>Référence</th>
                <th style={{ textAlign: 'right' }}>Montant</th>
                <th />
              </tr></thead>
              <tbody>
                {filtres.map(r => (
                  <tr key={r.id}>
                    <td className={styles.tdDate}>{formatDate(r.date)}</td>
                    <td><strong>{r.tiers}</strong></td>
                    <td>
                      {r.facture_id ? (() => {
                        const fac = facturesMap[r.facture_id]
                        const inconnu = r.montant_valide === false || !fac || fac.montants_valides === false || fac.cumul === null
                        const isPartiel = fac && fac.statut !== 'payee' 
                        return (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <span style={{ fontFamily: 'monospace', fontSize: 10, background: 'var(--blue-light)', color: 'var(--blue)', padding: '2px 6px', borderRadius: 3 }}>
                              {fac ? fac.numero : `FA #${r.facture_id}`}
                            </span>
                            <span style={{ fontSize: 9, fontWeight: 600, color: isPartiel ? '#854F0B' : '#3B6D11' }}>
                              {inconnu ? 'Situation à vérifier' : isPartiel ? '~ Partiel' : '✓ Soldée'}
                            </span>
                          </div>
                        )
                      })() : <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>—</span>}
                    </td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
                        <i className={`ti ${ICONES_MODE[r.mode] || 'ti-coin'}`} style={{ fontSize: 13, color: 'var(--blue)' }} />
                        {r.mode.charAt(0).toUpperCase() + r.mode.slice(1)}
                      </span>
                      {r.statut && r.statut !== 'complet' && (
                        <span style={{ fontSize: 9, color: r.statut === 'annule' || r.statut === 'rejete' ? 'var(--red)' : 'var(--text-tertiary)' }}>
                          {r.statut.replaceAll('_', ' ')}
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{r.reference || '—'}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--green)' }}>
                      {formatMAD(r.montant)} MAD
                      {r.montant_valide === false && <div style={{ color: 'var(--red)', fontSize: 11, fontWeight: 400, maxWidth: 220 }}>
                        {r.montant_anomalie || 'Montant historique à vérifier.'}
                      </div>}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        {peutEcrire() && lots[r.id] && <button className={styles.btnTrash} onClick={() => annulerLot(lots[r.id])} disabled={annulationLotEnCours} title="Annuler toute la ventilation"><i className="ti ti-arrows-exchange" /><span className="libelle-action" aria-hidden="true">Annuler toute la ventilation</span></button>}
                        <button className={styles.btnAction} onClick={() => setRasReglement(r)} disabled={r.montant_valide === false} title="Consulter ou déclarer la RAS"><i className="ti ti-receipt-tax" /><span className="libelle-action" aria-hidden="true">Consulter ou déclarer la RAS</span></button>
                        {peutEcrire() && !r.est_comptabilisee && !['rejete', 'annule'].includes(r.statut) && (<>
                          <button className={styles.btnAction} onClick={() => setReglEdit(r)} disabled={r.montant_valide === false} title="Modifier"><i className="ti ti-pencil" /><span className="libelle-action" aria-hidden="true">Modifier</span></button>
                          <button className={styles.btnTrash} onClick={() => supprimer(r.id)} disabled={r.montant_valide === false} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>
                        </>)}
                        {peutEcrire() && r.est_comptabilisee && ['complet', 'portefeuille', 'a_payer'].includes(r.statut) && (
                          <button className={styles.btnTrash} onClick={() => annulerReglement(r)} disabled={r.montant_valide === false} title="Annuler par contrepassation"><i className="ti ti-arrow-back-up" /><span className="libelle-action" aria-hidden="true">Annuler par contrepassation</span></button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function OngletBonsReception({ annee, onOuvrirCommandes }) {
  const [erreurLecture, setErreurLecture] = useState('')
  const generationLectureBR = useRef(0)
  const contexteLectureBR = useRef(null)
  const jetonLectureBR = TOKEN()
  contexteLectureBR.current = { annee, jeton: jetonLectureBR }
  const { recharger: rechargerFactures } = useFactures()
  const [retourFacturation, setRetourFacturation] = useState(null)
  const [brAFacturer, setBrAFacturer] = useState(null)
  const [reliquatBR, setReliquatBR] = useState(null)
  const [qtesBR, setQtesBR] = useState({})
  const [dateFactureBR, setDateFactureBR] = useState(dateLocaleISO())
  const [facturationBR, setFacturationBR] = useState(false)
  const [expandedPJ, setExpandedPJ] = useState(null)
  const [brs, setBRs] = useState([])
  const [loading, setLoading] = useState(true)
  const [brSelectionne, setBrSelectionne] = useState(null)

  async function charger() {
    const jeton = TOKEN()
    if (annee !== contexteLectureBR.current?.annee || jeton !== contexteLectureBR.current?.jeton) return
    const generation = ++generationLectureBR.current
    const courant = () => generation === generationLectureBR.current
      && annee === contexteLectureBR.current?.annee && jeton === TOKEN()
    setLoading(true)
    setErreurLecture('')
    try {
      const data = await apiFetch(`/api/bons-reception?exercice=${annee}`)
      if (courant()) setBRs(data)
    } catch {
      if (courant()) {
        setBRs([])
        setErreurLecture('Chargement des réceptions impossible. La liste n’est pas disponible.')
      }
    } finally { if (courant()) setLoading(false) }
  }

  useEffect(() => {
    charger()
    return () => { generationLectureBR.current += 1 }
  }, [annee, jetonLectureBR])

  async function changerStatut(id, statut) {
    try {
      await apiFetch(`/api/bons-reception/${id}`, { method: 'PATCH', body: JSON.stringify({ statut }) })
      charger()
    } catch {}
  }

  async function supprimer(id) {
    if (!confirm('Supprimer ce bon de réception ?')) return
    try { await apiFetch(`/api/bons-reception/${id}`, { method: 'DELETE' }); charger() } catch {}
  }

  async function ouvrirFacturationBR(br) {
    setRetourFacturation(null)
    setBrAFacturer(br); setReliquatBR(null); setQtesBR({})
    setDateFactureBR(dateLocaleISO())
    try {
      const reliquat = await apiFetch(`/api/bons-livraison/${br.id}/reliquat-facturation`)
      if (reliquat.type !== 'achat') throw new Error('Ce document n’est pas une réception fournisseur.')
      setReliquatBR(reliquat)
      const quantites = {}
      for (const ligne of reliquat.lignes || []) {
        if (Number(ligne.reste_a_facturer || 0) > 0) quantites[String(ligne.ligne_bl_id)] = String(ligne.reste_a_facturer)
      }
      setQtesBR(quantites)
    } catch (e) { notifier.erreur(e.message); setBrAFacturer(null) }
  }

  async function facturerBR() {
    if (!brAFacturer || !reliquatBR || !dateFactureBR || facturationBR) return
    const lignes = (reliquatBR.lignes || [])
      .map(l => ({ ligne_bl_id: l.ligne_bl_id, quantite: Number(qtesBR[String(l.ligne_bl_id)] || 0) }))
      .filter(l => l.quantite > 0)
    if (!lignes.length) { notifier('Indiquez au moins une quantité à facturer.'); return }
    setFacturationBR(true)
    try {
      const facture = await apiFetch(`/api/bons-livraison/${brAFacturer.id}/convertir-facture`, {
        method: 'POST', body: JSON.stringify({ date: dateFactureBR, lignes }),
      })
      const message = `Brouillon de facture fournisseur #${facture.id} créé depuis ${brAFacturer.numero}. Renseignez son numéro fournisseur dans Factures avant validation.`
      setRetourFacturation({ tone: 'success', message })
      // La création a réussi : fermer avant les rechargements, qui peuvent
      // échouer indépendamment sans faire croire à un échec de facturation.
      setBrAFacturer(null); setReliquatBR(null); setQtesBR({})
      try { await Promise.all([rechargerFactures(), charger()]) }
      catch { setRetourFacturation({ tone: 'warning', message: `${message} Facture créée ; actualisez les listes si elles ne sont pas à jour.` }) }
    } catch (e) { notifier.erreur(e.message) }
    finally { setFacturationBR(false) }
  }

  return (
    <div className={styles.ongletContent}>
      {retourFacturation && <div role="status"><InlineNotice tone={retourFacturation.tone}>{retourFacturation.message}</InlineNotice></div>}

      <div className={styles.ongletTopbar} style={{ flexWrap: 'wrap' }}>
        <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          {loading ? 'Chargement…' : erreurLecture ? 'Réceptions indisponibles' : `${brs.length} bon${brs.length !== 1 ? 's' : ''} de réception`}
        </span>
        <button type="button" className={styles.btnSec} aria-label="Actualiser les réceptions" disabled={loading} onClick={charger}>
          <i className="ti ti-refresh" aria-hidden="true" /> Actualiser
        </button>
        {peutEcrire() && <button type="button" className={styles.btnPrim} onClick={onOuvrirCommandes}>
          <i className="ti ti-clipboard-list" aria-hidden="true" /> Préparer depuis une commande
        </button>}
      </div>

      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
        ) : erreurLecture ? (
          <div className={styles.vide} role="alert">
            <InlineNotice tone="danger">{erreurLecture}</InlineNotice>
            <button type="button" className={styles.btnSec} onClick={charger}>Réessayer</button>
          </div>
        ) : brs.length === 0 ? (
          <div className={styles.vide}>
            <i className="ti ti-package-import" />
            <span>Aucun bon de réception</span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              Les BR sont créés depuis les bons de commande achat
            </span>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr>
                <th>N° BR</th>
                <th>Date</th>
                <th>Fournisseur</th>
                <th>Articles</th>
                <th>Statut</th>
                <th />
              </tr></thead>
              <tbody>
                {brs.map(br => {
                  const aEcart = br.lignes?.some(l => l.quantite_livree !== l.quantite_prevue)
                  return (
                    <tr key={br.id} style={{ cursor: 'pointer' }}
                      onClick={() => setBrSelectionne(brSelectionne?.id === br.id ? null : br)}>
                      <td><span className={styles.numDoc}>{br.numero}</span></td>
                      <td className={styles.tdDate}>{formatDate(br.date)}</td>
                      <td><strong>{br.tiers}</strong></td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {(br.lignes || []).slice(0, 2).map((l, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                              <span style={{ color: 'var(--text-secondary)' }}>{l.description}</span>
                              <span style={{
                                fontSize: 10, padding: '1px 5px', borderRadius: 3,
                                background: l.quantite_livree < l.quantite_prevue ? '#FAEEDA'
                                  : l.quantite_livree > l.quantite_prevue ? '#E6F1FB' : '#EAF3DE',
                                color: l.quantite_livree < l.quantite_prevue ? '#854F0B'
                                  : l.quantite_livree > l.quantite_prevue ? '#185FA5' : '#3B6D11',
                              }}>
                                {l.quantite_livree}/{l.quantite_prevue}
                              </span>
                            </div>
                          ))}
                          {(br.lignes || []).length > 2 && (
                            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                              +{br.lignes.length - 2} article{br.lignes.length - 2 > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Badge statut={br.statut} map={STATUT_BR} />
                          {aEcart && (
                            <span style={{ fontSize: 10, background: '#FAEEDA', color: '#854F0B', padding: '1px 6px', borderRadius: 3 }}>
                              ⚠ Écart
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          {br.statut === 'en_preparation' && (
                            <button className={styles.btnAction} title="Marquer en cours"
                              onClick={e => { e.stopPropagation(); changerStatut(br.id, 'expedie') }}><i className="ti ti-clock" /><span className="libelle-action" aria-hidden="true">Marquer en cours</span></button>
                          )}
                          {br.statut === 'expedie' && (
                            <button className={styles.btnAction} style={{ color: 'var(--green)' }}
                              title="Marquer réceptionné"
                              onClick={e => { e.stopPropagation(); changerStatut(br.id, 'livre') }}><i className="ti ti-check" /><span className="libelle-action" aria-hidden="true">Marquer réceptionné</span></button>
                          )}
                          {br.statut === 'livre' && (
                            <button className={styles.btnAction} style={{ color: 'var(--red)' }}
                              title="Retour fournisseur"
                              onClick={e => { e.stopPropagation(); changerStatut(br.id, 'retourne') }}><i className="ti ti-arrow-back" /><span className="libelle-action" aria-hidden="true">Retour fournisseur</span></button>
                          )}
                          {br.statut === 'livre' && (
                            <button className={styles.btnTransformPrimary}
                              onClick={e => { e.stopPropagation(); ouvrirFacturationBR(br) }}
                              title="Créer la facture fournisseur depuis ce bon de réception">
                              <i className="ti ti-file-invoice" /> Facturer
                            </button>
                          )}
                          <button className={styles.btnAction}
                            onClick={e => { e.stopPropagation(); setExpandedPJ(expandedPJ === br.id ? null : br.id) }}
                            title="Pièces jointes" style={{ color: expandedPJ === br.id ? 'var(--blue)' : '' }}><i className="ti ti-paperclip" /><span className="libelle-action" aria-hidden="true">Pièces jointes</span></button>
                          <button className={styles.btnAction}
                            onClick={e => { e.stopPropagation(); telechargerPDF(`/api/bons-reception/${br.id}/pdf?exemplaires=2`, `br_${br.numero}.pdf`).catch(err => notifier.erreur(err.message)) }}
                            title="Télécharger PDF"><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                          <button className={styles.btnAction}
                            onClick={e => { e.stopPropagation(); preparerEmailDocument({ endpoint: `/api/bons-reception/${br.id}/pdf?exemplaires=2`, nomFichier: `br_${br.numero}.pdf`, typeDocument: 'Bon de réception', numero: br.numero, tiers: br.tiers, tiersId: br.tiers_id }).catch(err => notifier.erreur(err.message)) }}
                            title="Télécharger le PDF et préparer un e-mail"><i className="ti ti-mail-forward" /><span className="libelle-action" aria-hidden="true">Télécharger le PDF et préparer un e-mail</span></button>
                          <button className={styles.btnTrash}
                            onClick={e => { e.stopPropagation(); supprimer(br.id) }}>
                            <i className="ti ti-trash" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {expandedPJ && (
              <div style={{ padding: '12px 20px', borderTop: '0.5px solid var(--border-light)', background: '#FAFAFA' }}>
                <PiecesJointes docType="br" docId={expandedPJ} />
              </div>
            )}
          </div>
        )}
      </div>

      {brAFacturer && (
        <Modal titre={`Facturer le bon de réception ${brAFacturer.numero}`} icone="ti-file-invoice"
          onFermer={() => { if (!facturationBR) setBrAFacturer(null) }} largeur="lg">
          <div className={styles.formContenu}>
            <div className={styles.sourceInfo}>
              <i className="ti ti-link" /> Bon de réception <strong>{brAFacturer.numero}</strong> — {brAFacturer.tiers}
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor="date-facture-br">Date de la facture fournisseur</label>
              <input id="date-facture-br" className={styles.input} type="date" value={dateFactureBR}
                onChange={e => setDateFactureBR(e.target.value)} />
            </div>
            {!reliquatBR ? <div className={styles.vide}>Chargement du reste à facturer…</div> : (
              <>
                <div className={styles.cycleLineTable}>
                  <div className={`${styles.cycleLineHead} ${styles.facturationHead}`}>
                    <span>Prestation / article</span><span>Reçu</span><span>Déjà facturé</span><span>Reste</span><span>À facturer</span>
                  </div>
                  {(reliquatBR.lignes || []).map(l => (
                    <div className={`${styles.cycleLineRow} ${styles.facturationRow}`} key={l.ligne_bl_id}>
                      <span><strong>{l.description}</strong><small>{l.tva ?? 0}% TVA</small></span>
                      <span data-label="Reçu">{l.quantite_livree}</span>
                      <span data-label="Déjà facturé">{l.quantite_facturee}</span>
                      <span data-label="Reste à facturer">{l.reste_a_facturer}</span>
                      <span data-label="À facturer">
                        <input className={styles.quantiteInput} type="number" min="0" max={l.reste_a_facturer} step="0.01"
                          value={qtesBR[String(l.ligne_bl_id)] ?? ''}
                          onChange={e => setQtesBR(prev => ({ ...prev, [String(l.ligne_bl_id)]: e.target.value }))} />
                      </span>
                    </div>
                  ))}
                </div>
                <p className={styles.helperText}>Une facture fournisseur sera créée en brouillon avec le lien au BC et au BR. Son numéro fournisseur devra être renseigné avant validation.</p>
              </>
            )}
            <div className={styles.formActions}>
              <button className={styles.btnSec} onClick={() => setBrAFacturer(null)} disabled={facturationBR}>Annuler</button>
              <button className={styles.btnPrim} onClick={facturerBR} disabled={!dateFactureBR || !reliquatBR || facturationBR || !(reliquatBR.lignes || []).some(l => Number(qtesBR[String(l.ligne_bl_id)] || 0) > 0)}>
                <i className="ti ti-file-invoice" /> {facturationBR ? 'Création…' : 'Créer la facture en brouillon'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Détail BR sélectionné — écarts prévu/reçu */}
      {brSelectionne && (
        <div className={styles.card} style={{ padding: 16, gap: 12, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 500 }}>
              <i className="ti ti-package-import" style={{ marginRight: 6 }} />
              Détail BR {brSelectionne.numero} — {brSelectionne.tiers}
            </span>
            <button onClick={() => setBrSelectionne(null)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)' }}>✕</button>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)' }}>
                <th style={{ padding: '7px 12px', textAlign: 'left', fontWeight: 500, fontSize: 11, color: 'var(--text-secondary)' }}>Article</th>
                <th style={{ padding: '7px 12px', textAlign: 'center', fontWeight: 500, fontSize: 11, color: 'var(--text-secondary)' }}>Qté prévue</th>
                <th style={{ padding: '7px 12px', textAlign: 'center', fontWeight: 500, fontSize: 11, color: 'var(--text-secondary)' }}>Qté reçue</th>
                <th style={{ padding: '7px 12px', textAlign: 'center', fontWeight: 500, fontSize: 11, color: 'var(--text-secondary)' }}>Écart</th>
              </tr>
            </thead>
            <tbody>
              {(brSelectionne.lignes || []).map((l, i) => {
                const ecart = l.quantite_livree - l.quantite_prevue
                return (
                  <tr key={i} style={{ borderBottom: '0.5px solid var(--border-light)' }}>
                    <td style={{ padding: '8px 12px' }}>{l.description}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>{l.quantite_prevue}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>{l.quantite_livree}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      {ecart === 0 ? (
                        <span style={{ color: 'var(--green)', fontSize: 11 }}>✓ OK</span>
                      ) : (
                        <span style={{
                          fontSize: 11, fontWeight: 600,
                          color: ecart < 0 ? '#854F0B' : '#185FA5',
                        }}>
                          {ecart > 0 ? '+' : ''}{ecart}
                          <span style={{ fontWeight: 400, marginLeft: 4 }}>
                            {ecart < 0 ? '(manquant)' : '(surplus)'}
                          </span>
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {brSelectionne.notes && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              {brSelectionne.notes}
            </div>
          )}
        </div>
      )}
    </div>
  )
}


// ─── Onglet Factures dans Commercial ─────────────────────────────────────────

function OngletFactures({ annee, typeForce = null }) {
  const navigate = useNavigate()
  const { lignes: factures, loading, erreurLecture, charger } = useListeCommerciale(`/api/factures?exercice=${annee}`, typeForce)

  const STATUT = {
    reglement_en_cours: { label: 'Règlement en cours', bg: '#E6F1FB', color: '#185FA5' },
    payee:      { label: 'Payée',      bg: '#EAF3DE', color: '#3B6D11' },
    partiellement_payee: { label: 'Part. payée', bg: '#E6F1FB', color: '#185FA5' },
    en_attente: { label: 'En attente', bg: '#FAEEDA', color: '#854F0B' },
    annulee:    { label: 'Annulée',    bg: '#F0EFED', color: '#5A5955' },
  }

  const aujourd = new Date()

  return (
    <div className={styles.ongletContent}>
      <div className={styles.ongletTopbar}>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={loading}>Actualiser la liste</button>
        <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{loading || erreurLecture ? 'Nombre de factures indisponible' : `${factures.length} facture${factures.length !== 1 ? 's' : ''}`}</span>
        <button className={styles.btnPrim} onClick={() => navigate('/factures')}>
          <i className="ti ti-external-link" /> Ouvrir page Factures
        </button>
      </div>
      {loading ? (
        <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /><span>Chargement...</span></div>
      ) : erreurLecture ? (
        <ErreurListeCommerciale message={erreurLecture} charger={charger} />
      ) : factures.length === 0 ? (
        <div className={styles.vide}><i className="ti ti-file-off" /><span>Aucune facture pour {annee}</span></div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>N° Facture</th>
                <th>Type</th>
                <th>Date</th>
                <th>Tiers</th>
                <th style={{ textAlign: 'right' }}>TTC</th>
                <th>Statut</th>
                <th>Échéance</th>
              </tr>
            </thead>
            <tbody>
              {factures.map(f => {
                const ech = f.date_echeance
                  ? new Date(`${f.date_echeance}T12:00:00`)
                  : (f.date ? new Date(`${f.date}T12:00:00`) : null)
                if (ech && !f.date_echeance) ech.setDate(ech.getDate() + (f.delai_paiement ?? 60))
                const enRetard = ech && ech < aujourd && f.statut !== 'payee' && f.statut !== 'annulee'
                const statut = STATUT[statutPaiementAffiche(f)] || STATUT.en_attente
                return (
                  <tr key={f.id} onClick={() => navigate('/factures')} style={{ cursor: 'pointer' }}>
                    <td><span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--blue)', fontWeight: 600 }}>{f.numero}</span></td>
                    <td><span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 100, background: f.type === 'vente' ? '#E6F1FB' : '#EEEDFE', color: f.type === 'vente' ? '#185FA5' : '#534AB7' }}>{f.type === 'vente' ? 'Vente' : 'Achat'}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{formatDate(f.date)}</td>
                    <td style={{ fontWeight: 500 }}>{f.tiers}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatMAD(f.total_ttc)} MAD</td>
                    <td>
                      <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 100, background: statut.bg, color: statut.color, fontWeight: 500 }}>{statut.label}</span>
                      {f.statut === 'payee' && Number(f.total_reglement_en_cours || 0) > 0 && (
                        <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginTop: 3 }}>Encaissement en cours</div>
                      )}
                    </td>
                    <td>
                      {ech && f.statut !== 'payee' && f.statut !== 'annulee' && (
                        <span style={{ fontSize: 11, color: enRetard ? '#A32D2D' : 'var(--text-tertiary)', fontWeight: enRetard ? 600 : 400 }}>
                          {enRetard && <i className="ti ti-clock-exclamation" style={{ marginRight: 3 }} />}
                          {ech.toLocaleDateString('fr-MA', { day: '2-digit', month: '2-digit', year: '2-digit' })}
                          {enRetard && ' (retard)'}
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}


// ─── Onglet Réception client (vente) ────────────────────────────────────────
// Permet de confirmer que le client a bien reçu la marchandise

function OngletReceptionClient({ annee }) {
  const { lignes: receptions, associees: factures, loading, erreurLecture, charger } = useListeCommerciale(`/api/bons-livraison?exercice=${annee}`, 'vente', `/api/factures?exercice=${annee}`)
  const [documentsClient, setDocumentsClient] = useState(null)
  const facturesMap = useMemo(() => Object.fromEntries(factures.map(f => [f.id, f])), [factures])
  const [showForm, setShowForm] = useState(false)
  const [recherche, setRecherche] = useState('')
  const [avoirRetour, setAvoirRetour] = useState(null) // { facture, avoirsExistants, quantitesRetour, motifDefaut }
  const [form, setForm] = useState({
    tiers: '', date: dateLocaleISO(),
    reference_bl: '', notes: '', statut: 'recu',
  })
  const [saving, setSaving] = useState(false)



  useEffect(() => { setDocumentsClient(null) }, [annee])

  const filtres = useMemo(() =>
    receptions.filter(r =>
      !recherche || r.tiers?.toLowerCase().includes(recherche.toLowerCase()) ||
      r.numero?.toLowerCase().includes(recherche.toLowerCase())
    ), [receptions, recherche]
  )

  const STATUT_BL_LABEL = {
    en_preparation: { label: 'En préparation', bg: '#FAEEDA', color: '#854F0B' },
    expedie:        { label: 'Expédié',         bg: '#E6F1FB', color: '#185FA5' },
    livre:          { label: 'Livré / Reçu',    bg: '#EAF3DE', color: '#3B6D11' },
    retourne:       { label: 'Retourné',        bg: '#FCEBEB', color: '#A32D2D' },
  }

  async function marquerRecu(id) {
    try {
      await apiFetch(`/api/bons-livraison/${id}`, {
        method: 'PATCH', body: JSON.stringify({ statut: 'livre' })
      })
      charger()
    } catch (e) { notifier.erreur(e.message) }
  }

  async function marquerRetour(bl) {
    if (!confirm("Marquer ce bon de livraison comme retourné ?\nLe stock sera automatiquement réintégré.")) return
    try {
      await apiFetch(`/api/bons-livraison/${bl.id}`, {
        method: 'PATCH', body: JSON.stringify({ statut: 'retourne' })
      })
      charger()

      if (!bl.facture_id) {
        notifier("Stock réintégré. Cette livraison n'est liée à aucune facture — aucun avoir à générer.")
        return
      }

      // Pré-remplir un avoir avec les quantités effectivement retournées sur ce BL
      const [factures, avoirs] = await Promise.all([
        apiFetch(`/api/factures?exercice=${annee}`).catch(() => []),
        apiFetch(`/api/avoirs?exercice=${annee}&facture_id=${bl.facture_id}`).catch(() => []),
      ])
      const facture = factures.find(f => f.id === bl.facture_id)
      if (!facture) {
        notifier.erreur("Stock réintégré. Impossible de charger la facture liée pour proposer un avoir — à créer manuellement si besoin.")
        return
      }
      const quantitesRetour = {}
      ;(bl.lignes || []).forEach(l => {
        quantitesRetour[l.description] = (quantitesRetour[l.description] || 0) + (l.quantite_livree || 0)
      })
      setAvoirRetour({
        facture,
        avoirsExistants: avoirs,
        quantitesRetour,
        motifDefaut: `Retour client — BL ${bl.numero}`,
      })
    } catch (e) { notifier.erreur(e.message) }
  }

  return (
    <div className={styles.ongletContent}>
      <div className={styles.ongletTopbar}>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={loading}>Actualiser la liste</button>
        <div className={styles.recherche}>
          <i className="ti ti-search" />
          <input type="text" placeholder="Chercher tiers ou numéro..."
            value={recherche} onChange={e => setRecherche(e.target.value)}
            className={styles.inputRecherche} />
        </div>
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          Confirmations de réception par les clients
        </span>
      </div>

      <div className={styles.card}>
        {loading ? (
          <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /></div>
        ) : erreurLecture ? (
          <ErreurListeCommerciale message={erreurLecture} charger={charger} />
        ) : filtres.length === 0 ? (
          <div className={styles.vide}>
            <i className="ti ti-clipboard-check" />
            <span>Aucun bon de livraison trouvé</span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              Les BL apparaissent ici une fois créés depuis les bons de commande
            </span>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>N° BL</th>
                  <th>Date</th>
                  <th>Client</th>
                  <th>Articles</th>
                  <th>Statut</th>
                  <th>Facture liée</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtres.map((bl, i) => {
                  const statut = STATUT_BL_LABEL[bl.statut] || STATUT_BL_LABEL.en_preparation
                  return (
                    <tr key={bl.id} className={i % 2 === 0 ? styles.rowPair : ''}>
                      <td><span className={styles.numDoc}>{bl.numero}</span></td>
                      <td className={styles.tdDate}>{formatDate(bl.date)}</td>
                      <td><strong>{bl.tiers}</strong></td>
                      <td style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        {(bl.lignes || []).slice(0, 2).map((l, j) => (
                          <span key={j} style={{ display: 'block' }}>{l.quantite}× {l.description}</span>
                        ))}
                        {(bl.lignes || []).length > 2 && (
                          <span style={{ color: 'var(--text-tertiary)' }}>+{bl.lignes.length - 2} autres</span>
                        )}
                      </td>
                      <td>
                        <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 100, background: statut.bg, color: statut.color, fontWeight: 500 }}>
                          {statut.label}
                        </span>
                      </td>
                      <td>
                        {bl.facture_id ? (
                          <span style={{ fontSize: 10, fontFamily: 'monospace', background: 'var(--blue-light)', color: 'var(--blue)', padding: '2px 6px', borderRadius: 3 }}>
                            {facturesMap[bl.facture_id]?.numero || `FA #${bl.facture_id}`}
                          </span>
                        ) : <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>—</span>}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button className={styles.btnAction} style={{ color: '#DC2626' }}
                            onClick={() => telechargerPDF(`/api/bons-livraison/${bl.id}/pdf?exemplaires=2`, `bl_${bl.numero}.pdf`).catch(e => notifier.erreur(e.message))}
                            title="Télécharger PDF (double exemplaire)"><i className="ti ti-file-type-pdf" /><span className="libelle-action" aria-hidden="true">Télécharger PDF</span></button>
                          <button className={styles.btnAction}
                            onClick={() => preparerEmailDocument({ endpoint: `/api/bons-livraison/${bl.id}/pdf?exemplaires=2`, nomFichier: `bl_${bl.numero}.pdf`, typeDocument: 'Bon de livraison', numero: bl.numero, tiers: bl.tiers, tiersId: bl.tiers_id }).catch(e => notifier.erreur(e.message))}
                            title="Télécharger le PDF et préparer un e-mail"><i className="ti ti-mail-forward" /><span className="libelle-action" aria-hidden="true">Télécharger le PDF et préparer un e-mail</span></button>
                          <button className={styles.btnAction}
                            onClick={() => setDocumentsClient({ bl, annee })}
                            title="Documents reçus du client" aria-label="Documents reçus du client"><i className="ti ti-paperclip" /><span className="libelle-action" aria-hidden="true">Documents reçus du client</span></button>
                          {bl.statut === 'expedie' && (
                            <button className={styles.btnActionPrim} onClick={() => marquerRecu(bl.id)} title="Confirmer réception client">
                              <i className="ti ti-clipboard-check" /> Reçu
                            </button>
                          )}
                          {bl.statut === 'livre' && (
                            <button className={styles.btnAction} style={{ color: 'var(--red)' }} onClick={() => marquerRetour(bl)} title="Retour client"><i className="ti ti-arrow-back" /><span className="libelle-action" aria-hidden="true">Retour client</span></button>
                          )}
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

      {documentsClient?.annee === annee && (
        <Modal titre={`Documents reçus du client — ${documentsClient.bl.numero}`}
          icone="ti-paperclip" largeur="lg" onFermer={() => setDocumentsClient(null)}>
          <div className={styles.clientDocuments}>
            <strong>{documentsClient.bl.tiers} · {documentsClient.bl.numero}</strong>
            <p>Conservez ici le bon de réception ou le document transmis par le client, signé lorsqu'il vous a été fourni ainsi. Le dépôt ne confirme pas automatiquement la réception ni l'authenticité d'une signature.</p>
            <p>Aucun mouvement de stock, changement de statut ou écriture comptable n'est créé par ce dépôt.</p>
            <PiecesJointes key={`${annee}:${documentsClient.bl.id}`} docType="bl"
              docId={documentsClient.bl.id} readOnly={!peutEcrire()} preserveExisting />
          </div>
        </Modal>
      )}
      {avoirRetour && (
        <FormulaireAvoir
          facture={avoirRetour.facture}
          avoirsExistants={avoirRetour.avoirsExistants}
          quantitesRetour={avoirRetour.quantitesRetour}
          motifDefaut={avoirRetour.motifDefaut}
          onFermer={() => setAvoirRetour(null)}
          onSuccess={() => { setAvoirRetour(null); charger() }}
        />
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE PRINCIPALE
// ═══════════════════════════════════════════════════════════════════════════════

const ONGLETS_VENTE = [
  { id: 'devis',    label: 'Devis',              icon: 'ti-file-description' },
  { id: 'bc',       label: 'Bons de commande',   icon: 'ti-clipboard-list' },
  { id: 'bl',       label: 'Bons de livraison',  icon: 'ti-truck' },
  { id: 'brc',      label: 'Réception client',   icon: 'ti-clipboard-check' },
  { id: 'factures', label: 'Factures',           icon: 'ti-file-invoice' },
  { id: 'regl',     label: 'Règlements',         icon: 'ti-coin' },
]

const ONGLETS_ACHAT = [
  { id: 'bc',       label: 'Bons de commande',   icon: 'ti-clipboard-list' },
  { id: 'br',       label: 'Bons de réception',  icon: 'ti-package-import' },
  { id: 'factures', label: 'Factures',           icon: 'ti-file-invoice' },
  { id: 'regl',     label: 'Règlements',         icon: 'ti-coin' },
]

export default function Commercial() {
  const { annee } = useExercice()
  const [mode, setMode] = useState('vente')   // vente | achat
  const [ongletVente, setOngletVente] = useState('devis')
  const [ongletAchat, setOngletAchat] = useState('bc')
  const [refreshBC, setRefreshBC] = useState(0)
  const [refreshBL, setRefreshBL] = useState(0)

  const onglets = mode === 'vente' ? ONGLETS_VENTE : ONGLETS_ACHAT
  const onglet  = mode === 'vente' ? ongletVente   : ongletAchat
  const setOnglet = mode === 'vente' ? setOngletVente : setOngletAchat

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar} style={{ flexWrap: 'wrap' }}>
        <div>
          <h1 className={styles.pageTitle}>Cycle commercial</h1>
          <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            {mode === 'vente'
              ? 'Devis → Bon de commande → Bon de livraison → Facture → Règlement'
              : 'Bon de commande → Bon de réception → Facture fournisseur → Règlement'}
          </p>
        </div>

        {/* Toggle Vente / Achat */}
        <div style={{ display: 'flex', gap: 0, borderRadius: 8, overflow: 'hidden', border: '0.5px solid var(--border-medium)', flexShrink: 0 }}>
          {[
            { val: 'vente', label: 'Vente', icon: 'ti-arrow-up-right', couleur: '#185FA5' },
            { val: 'achat', label: 'Achat', icon: 'ti-arrow-down-left', couleur: '#534AB7' },
          ].map(m => (
            <button key={m.val} onClick={() => setMode(m.val)} style={{
              padding: '7px 18px', border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 500,
              background: mode === m.val ? (m.val === 'vente' ? '#E6F1FB' : '#EEEDFE') : 'var(--bg-primary)',
              color: mode === m.val ? m.couleur : 'var(--text-secondary)',
              transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <i className={`ti ${m.icon}`} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline indicateur */}
      <div style={{ padding: '8px 24px', background: 'var(--bg-secondary)', borderBottom: '0.5px solid var(--border-light)', display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        {onglets.map((o, i) => (
          <div key={o.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button style={{
              fontSize: 11, padding: '3px 10px', borderRadius: 100, cursor: 'pointer', border: 'none',
              background: onglet === o.id ? 'var(--blue)' : 'var(--bg-primary)',
              color: onglet === o.id ? '#fff' : 'var(--text-secondary)',
              fontWeight: onglet === o.id ? 500 : 400, transition: 'all 0.15s',
            }} onClick={() => setOnglet(o.id)}>
              <i className={`ti ${o.icon}`} style={{ marginRight: 4 }} />
              {o.label}
            </button>
            {i < onglets.length - 1 && (
              <i className="ti ti-chevron-right" style={{ fontSize: 10, color: 'var(--border-medium)' }} />
            )}
          </div>
        ))}
      </div>

      <div className={styles.content}>
        {/* ── VENTE ── */}
        {mode === 'vente' && onglet === 'devis' && (
          <OngletDevis annee={annee} onConvertirBC={() => setRefreshBC(p => p + 1)} />
        )}
        {mode === 'vente' && onglet === 'bc' && (
          <OngletBonsCommande key={`v-${refreshBC}`} annee={annee} typeForce="vente"
            onConvertirFacture={() => {}} onConvertirBL={() => setRefreshBL(p => p + 1)} />
        )}
        {mode === 'vente' && onglet === 'factures' && (
          <OngletFactures annee={annee} typeForce="vente" />
        )}
        {mode === 'vente' && onglet === 'bl' && (
          <OngletBonsLivraison key={`v-${refreshBL}`} annee={annee} />
        )}
        {mode === 'vente' && onglet === 'brc' && (
          <OngletReceptionClient annee={annee} />
        )}
        {mode === 'vente' && onglet === 'regl' && (
          <OngletReglements annee={annee} typeForce="vente" />
        )}

        {/* ── ACHAT ── */}
        {mode === 'achat' && onglet === 'bc' && (
          <OngletBonsCommande key={`a-${refreshBC}`} annee={annee} typeForce="achat"
            onConvertirFacture={() => {}} onConvertirBL={() => setRefreshBL(p => p + 1)} />
        )}
        {mode === 'achat' && onglet === 'factures' && (
          <OngletFactures annee={annee} typeForce="achat" />
        )}
        {mode === 'achat' && onglet === 'br' && (
          <OngletBonsReception key={`a-${refreshBL}`} annee={annee} onOuvrirCommandes={() => setOngletAchat('bc')} />
        )}
        {mode === 'achat' && onglet === 'regl' && (
          <OngletReglements annee={annee} typeForce="achat" />
        )}
      </div>
    </div>
  )
}
