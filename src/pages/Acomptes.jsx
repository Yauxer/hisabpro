import React, { useState, useEffect, useMemo } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { formatMAD, formatDate } from '../data/donnees.js'
import Modal from '../components/Modal.jsx'
import TiersPicker from '../components/TiersPicker.jsx'
import { FormSection, AdvancedSection, InlineNotice, ActionBar } from '../components/FormUX.jsx'
import styles from './Acomptes.module.css'
import { API_BASE, peutEcrire } from '../services/api.js'
import { dateLocaleISO, nombreOuDefaut } from '../utils/formUtils.js'
import { QUALIFICATIONS_TVA, tauxTVAPourDate } from '../utils/tvaUtils.js'

const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Erreur' })); throw new Error(typeof e.detail === 'string' ? e.detail : 'Erreur') }
  if (res.status === 204) return null
  return res.json()
}

const STATUT_BADGE = {
  disponible: { bg: '#EAF3DE', color: '#3B6D11', label: 'Disponible' },
  partiellement_impute: { bg: '#FFF4D6', color: '#8A5A00', label: 'Partiellement imputé' },
  impute:     { bg: '#E6F1FB', color: '#185FA5', label: 'Imputé' },
  annule:     { bg: '#F3F4F6', color: '#6B7280', label: 'Annulé' },
}

const MODES = { virement: 'Virement', cheque: 'Chèque', especes: 'Espèces', effet: 'Effet', carte: 'Carte', prelevement: 'Prélèvement', autre: 'Autre' }

function BadgeStatut({ statut }) {
  const b = STATUT_BADGE[statut] || STATUT_BADGE.disponible
  return <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: b.bg, color: b.color, fontWeight: 500 }}>{b.label}</span>
}

function BadgeType({ type }) {
  return (
    <span style={{
      fontSize: 10, padding: '2px 8px', borderRadius: 4,
      background: type === 'client' ? '#E6F1FB' : '#EAF3DE',
      color: type === 'client' ? '#185FA5' : '#3B6D11',
    }}>
      {type === 'client' ? 'Client' : 'Fournisseur'}
    </span>
  )
}

// ── Formulaire de création ────────────────────────────────────────────────────
function FormulaireAcompte({ onFermer, onSuccess }) {
  const [form, setForm] = useState({
    type: 'client', tiers: '', tiers_id: null, date: dateLocaleISO(),
    montant: '', mode: 'virement', banque: '', compte_bancaire_id: null, reference: '', date_echeance: '', notes: '', comptabiliser: true,
    tva_applicable: true, taux_tva: 20, qualification_tva: 'taxable',
  })
  const [tiersSelectionne, setTiersSelectionne] = useState(null)
  const [banques, setBanques] = useState([])
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    apiFetch('/api/banques').then(setBanques).catch(() => setBanques([]))
  }, [])

  async function enregistrer() {
    if (!form.tiers_id || !form.tiers.trim()) { setErreur('Sélectionnez un tiers dans la liste.'); return }
    if (!(nombreOuDefaut(form.montant, 0) > 0)) { setErreur('Le montant doit être strictement positif.'); return }
    if (!form.date) { setErreur('La date est obligatoire.'); return }
    if (form.mode === 'effet' && !form.date_echeance) { setErreur("L'échéance est obligatoire pour un effet."); return }
    setLoading(true); setErreur('')
    try {
      await apiFetch('/api/acomptes', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          montant: nombreOuDefaut(form.montant, 0),
          date_echeance: form.date_echeance || null,
          tva_applicable: form.qualification_tva === 'taxable',
          taux_tva: form.qualification_tva === 'taxable' ? nombreOuDefaut(form.taux_tva, 0) : 0,
          qualification_tva: form.qualification_tva,
        }),
      })
      onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouvel acompte" icone="ti-coins" onFermer={onFermer} largeur="md">
      <div className="hp-form-stack">
        <FormSection icon="ti-arrows-exchange" title="Nature de l'acompte"
          description="Choisissez si l’acompte est reçu d’un client ou versé à un fournisseur.">
          <div className="hp-choice-cards" style={{ gridTemplateColumns: 'repeat(2,minmax(0,1fr))', marginBottom: 12 }}>
            <button type="button" className={`hp-choice-card ${form.type === 'client' ? 'is-active' : ''}`} onClick={() => { setForm(p => ({ ...p, type: 'client', tiers: '', tiers_id: null })); setTiersSelectionne(null) }}><i className="ti ti-arrow-down-left" /> Acompte client reçu</button>
            <button type="button" className={`hp-choice-card ${form.type === 'fournisseur' ? 'is-active' : ''}`} onClick={() => { setForm(p => ({ ...p, type: 'fournisseur', tiers: '', tiers_id: null })); setTiersSelectionne(null) }}><i className="ti ti-arrow-up-right" /> Acompte fournisseur versé</button>
          </div>
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field">
              <label>Date <span className="hp-required">*</span></label>
              <input type="date" value={form.date} onChange={e => {
                const date = e.target.value
                setForm(p => {
                  const autorises = tauxTVAPourDate(date).filter(t => t > 0)
                  const courant = Number(p.taux_tva)
                  const taux = p.qualification_tva === 'taxable' && !autorises.includes(courant)
                    ? (autorises.includes(20) ? 20 : (autorises[0] || 0)) : courant
                  return { ...p, date, taux_tva: taux }
                })
              }} />
            </div>
            <div className="hp-field">
              <label>{form.type === 'client' ? 'Client' : 'Fournisseur'} <span className="hp-required">*</span></label>
              <TiersPicker
                value={form.tiers}
                type={form.type}
                onChange={nom => { setForm(p => ({ ...p, tiers: nom, tiers_id: null })); setTiersSelectionne(null); setErreur('') }}
                onSelect={t => {
                  setTiersSelectionne(t || null)
                  setForm(p => ({ ...p, tiers: t?.nom || p.tiers, tiers_id: t?.id || null }))
                  setErreur('')
                }}
              />
              {tiersSelectionne && <span className="hp-field__hint">
                <i className="ti ti-circle-check" /> Compte {form.type === 'client' ? (tiersSelectionne.compte_client || '3421') : (tiersSelectionne.compte_fournisseur || '4411')}
                {tiersSelectionne.ice ? ` · ICE ${tiersSelectionne.ice}` : ''}
                {tiersSelectionne.delai_paiement === 0 ? ' · comptant' : (tiersSelectionne.delai_paiement != null ? ` · ${tiersSelectionne.delai_paiement} j` : '')}
              </span>}
            </div>
          </div>
        </FormSection>

        <FormSection icon="ti-cash" title="Paiement"
          description="Saisissez le montant réellement encaissé ou versé et son moyen de paiement.">
          <div className="hp-form-grid hp-form-grid--3">
            <div className="hp-field"><label>Montant (MAD) <span className="hp-required">*</span></label><input type="number" min="0" step="0.01" value={form.montant} onChange={e => setForm(p => ({ ...p, montant: e.target.value }))} /></div>
            <div className="hp-field"><label>Mode</label><select value={form.mode} onChange={e => setForm(p => ({ ...p, mode: e.target.value }))}>{Object.entries(MODES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
            <div className="hp-field"><label>Référence</label><input value={form.reference} onChange={e => setForm(p => ({ ...p, reference: e.target.value }))} placeholder="N° chèque, virement..." /></div>
          </div>
          {form.mode !== 'especes' && banques.length > 0 && <div className="hp-field" style={{ marginTop: 12 }}><label>Compte bancaire</label><select value={form.compte_bancaire_id || ''} onChange={e => { const id = e.target.value ? Number(e.target.value) : null; const b = banques.find(x => x.id === id); setForm(p => ({ ...p, compte_bancaire_id: id, banque: b?.banque || '' })) }}><option value="">— Compte bancaire par défaut —</option>{banques.map(b => <option key={b.id} value={b.id}>{b.banque}{b.agence ? ` — ${b.agence}` : ''} · {b.compte_comptable || '5141'}{b.rib ? ` · ${b.rib}` : ''}</option>)}</select></div>}
          {(form.mode === 'cheque' || form.mode === 'effet') && <div className="hp-field" style={{ marginTop: 12 }}><label>Échéance {form.mode === 'effet' ? <span className="hp-required">*</span> : null}</label><input type="date" min={form.date} value={form.date_echeance} onChange={e => setForm(p => ({ ...p, date_echeance: e.target.value }))} /><span className="hp-field__hint">Le chèque/effet restera « en attente » jusqu'à confirmation de son encaissement/paiement.</span></div>}
        </FormSection>

        <AdvancedSection title="TVA, comptabilisation & notes" icon="ti-adjustments-horizontal">
          <div className="hp-form-grid hp-form-grid--2" style={{ marginBottom: 12 }}>
            <div className="hp-field">
              <label>Traitement TVA de l’opération</label>
              <select value={form.qualification_tva} onChange={e => {
                const qualification_tva = e.target.value
                setForm(p => {
                  const autorises = tauxTVAPourDate(p.date).filter(t => t > 0)
                  const taux = qualification_tva === 'taxable'
                    ? (autorises.includes(Number(p.taux_tva)) ? Number(p.taux_tva) : (autorises.includes(20) ? 20 : (autorises[0] || 0)))
                    : 0
                  return { ...p, qualification_tva, tva_applicable: qualification_tva === 'taxable', taux_tva: taux }
                })
              }}>
                {QUALIFICATIONS_TVA.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
              </select>
            </div>
            <div className="hp-field">
              <label>Taux TVA</label>
              <select disabled={form.qualification_tva !== 'taxable'} value={form.qualification_tva === 'taxable' ? form.taux_tva : 0} onChange={e => setForm(p => ({ ...p, taux_tva: Number(e.target.value) }))}>
                {form.qualification_tva === 'taxable'
                  ? tauxTVAPourDate(form.date).filter(t => t > 0).map(t => <option key={t} value={t}>TVA {t} %</option>)
                  : <option value="0">0 % — selon qualification</option>}
              </select>
            </div>
          </div>
          {form.type === 'client'
            ? <InlineNotice>Un acompte client encaissé constitue un fait générateur de TVA lorsqu’il se rattache à une opération taxable. Le montant saisi est TTC.</InlineNotice>
            : <InlineNotice>L’acompte fournisseur peut mémoriser le régime attendu, mais aucune TVA n’est déduite avant rattachement à une facture justificative.</InlineNotice>}
          <div className="hp-field" style={{ marginTop: 12 }}><label>Notes</label><textarea rows={2} value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} /></div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: 12, cursor: 'pointer' }}><input type="checkbox" checked={form.comptabiliser} onChange={e => setForm(p => ({ ...p, comptabiliser: e.target.checked }))} /> Comptabiliser automatiquement ({form.type === 'client' ? 'trésorerie → 4421' : '3411 → trésorerie'})</label>
        </AdvancedSection>

        {erreur && <InlineNotice tone="danger">{erreur}</InlineNotice>}
        <ActionBar hint="L’acompte restera disponible jusqu’à son imputation sur une facture.">
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={enregistrer} disabled={loading || !form.tiers_id || !(nombreOuDefaut(form.montant, 0) > 0)}><i className="ti ti-coins" /> {loading ? 'Enregistrement...' : 'Enregistrer l’acompte'}</button>
        </ActionBar>
      </div>
    </Modal>
  )

}

// ── Modale d'imputation sur facture ───────────────────────────────────────────
function ModalImputation({ acompte, onFermer, onSuccess }) {
  const [factures, setFactures] = useState([])
  const [factureId, setFactureId] = useState('')
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')
  const [situation, setSituation] = useState(null)
  const [loadingSituation, setLoadingSituation] = useState(false)
  const [montantImputation, setMontantImputation] = useState('')
  const [dateImputation, setDateImputation] = useState(dateLocaleISO())
  const disponibleAcompte = Number(acompte.montant_disponible ?? acompte.montant ?? 0)

  useEffect(() => {
    apiFetch(`/api/acomptes/${acompte.id}/factures-imputables`)
      .then(setFactures)
      .catch(() => setFactures([]))
  }, [acompte.id])

  async function choisirFacture(id) {
    setFactureId(id)
    setSituation(null)
    setErreur('')
    if (!id) return
    setLoadingSituation(true)
    try {
      const data = await apiFetch(`/api/factures/${id}/reglements`)
      setSituation(data)
      setMontantImputation(String(Math.min(disponibleAcompte, Number(data.solde_restant || 0)).toFixed(2)))
    } catch (e) {
      setErreur(e.message)
    } finally {
      setLoadingSituation(false)
    }
  }

  async function imputer() {
    if (!factureId) { setErreur('Choisis une facture'); return }
    const montant = nombreOuDefaut(montantImputation, 0)
    if (!(montant > 0)) { setErreur('Le montant à imputer doit être strictement positif.'); return }
    if (montant > disponibleAcompte + 0.01) { setErreur(`Il ne reste que ${formatMAD(disponibleAcompte)} MAD disponibles sur cet acompte.`); return }
    if (situation && montant > Number(situation.solde_restant || 0) + 0.01) {
      setErreur(`Le montant à imputer dépasse le solde de la facture (${formatMAD(situation.solde_restant)} MAD).`)
      return
    }
    setLoading(true); setErreur('')
    try {
      await apiFetch(`/api/acomptes/${acompte.id}/imputer`, {
        method: 'POST',
        body: JSON.stringify({ facture_id: parseInt(factureId), montant, date_imputation: dateImputation, comptabiliser: true }),
      })
      onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <Modal titre={`Imputer ${acompte.numero} — ${formatMAD(disponibleAcompte)} MAD disponibles`} icone="ti-arrow-merge" onFermer={onFermer} largeur="sm">
      <div className="hp-form-stack">
        <FormSection icon="ti-arrow-merge" title="Choisir la facture" description={`Choisissez la facture et le montant à imputer. Un acompte peut désormais être réparti sur plusieurs factures.`}>
        {erreur && <InlineNotice tone="danger">{erreur}</InlineNotice>}
        <InlineNotice>Une écriture d’imputation ({acompte.type === 'client' ? '4421 → compte client paramétré' : 'compte fournisseur paramétré → 3411'}) sera générée.</InlineNotice>
        <div>
          <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
            Facture de {acompte.tiers} ({acompte.type === 'client' ? 'vente' : 'achat'})
          </label>
          {factures.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: '10px 0' }}>
              Aucune facture ouverte pour ce tiers, tous exercices confondus.
            </div>
          ) : (
            <select value={factureId} onChange={e => choisirFacture(e.target.value)}
              style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }}>
              <option value="">— Choisir une facture —</option>
              {factures.map(f => (
                <option key={f.id} value={f.id}>
                  {f.numero} — reste {formatMAD(f.solde_restant)} MAD — {f.exercice} ({formatDate(f.date)})
                </option>
              ))}
            </select>
          )}
        </div>
        {factureId && (
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field">
              <label>Montant à imputer (MAD)</label>
              <input type="number" min="0.01" step="0.01" max={Math.min(disponibleAcompte, Number(situation?.solde_restant || disponibleAcompte))}
                value={montantImputation} onChange={e => setMontantImputation(e.target.value)} />
              <span className="hp-field__hint">Disponible sur l’acompte : {formatMAD(disponibleAcompte)} MAD</span>
            </div>
            <div className="hp-field">
              <label>Date d’imputation</label>
              <input type="date" value={dateImputation} min={acompte.date} onChange={e => setDateImputation(e.target.value)} />
            </div>
          </div>
        )}
        {loadingSituation && <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Calcul du solde...</div>}
        {situation && (
          <div className="hp-summary">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}><span>Total TTC</span><strong>{formatMAD(situation.total_ttc)} MAD</strong></div>
            {situation.total_regle > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}><span>Règlements</span><span>- {formatMAD(situation.total_regle)} MAD</span></div>}
            {situation.total_avoirs > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}><span>Avoirs</span><span>- {formatMAD(situation.total_avoirs)} MAD</span></div>}
            {situation.total_acomptes > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}><span>Acomptes déjà imputés</span><span>- {formatMAD(situation.total_acomptes)} MAD</span></div>}
            {situation.montant_ras > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}><span>RAS</span><span>- {formatMAD(situation.montant_ras)} MAD</span></div>}
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '0.5px solid var(--border-light)', paddingTop: 6, marginTop: 6 }}>
              <strong>Reste à payer</strong><strong>{formatMAD(situation.solde_restant)} MAD</strong>
            </div>
            <div style={{ marginTop: 7, color: 'var(--text-tertiary)', fontSize: 10.5 }}><i className="ti ti-info-circle" /> L’imputation est affectée automatiquement à l’échéance ouverte la plus ancienne de la facture.</div>
          </div>
        )}
        </FormSection>
        <ActionBar hint={situation ? `Reste à payer : ${formatMAD(situation.solde_restant)} MAD` : 'Sélectionnez une facture ouverte.'}>
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={imputer} disabled={loading || !factureId || loadingSituation || !(nombreOuDefaut(montantImputation, 0) > 0) || nombreOuDefaut(montantImputation, 0) > disponibleAcompte + 0.01 || (situation && nombreOuDefaut(montantImputation, 0) > Number(situation.solde_restant || 0) + 0.01)}>
            <i className="ti ti-arrow-merge" /> {loading ? 'Imputation...' : 'Imputer l’acompte'}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )
}

// ── Détail d'un acompte et historique d'imputations ───────────────────────────
function ModalDetailAcompte({ acompte, onFermer, onSuccess }) {
  const peutModifier = peutEcrire()
  const [busy, setBusy] = useState(false)
  const [erreur, setErreur] = useState('')
  const [dateOperation, setDateOperation] = useState(dateLocaleISO())
  const imputations = acompte.imputations || []

  async function changerStatutPaiement(statut) {
    const libelle = statut === 'encaisse' ? (acompte.type === 'client' ? 'encaissement' : 'paiement') : 'rejet'
    const dateEffective = dateOperation || dateLocaleISO()
    if (!confirm(`Confirmer ${libelle} de ${acompte.numero} au ${formatDate(dateEffective)} ?`)) return
    setBusy(true); setErreur('')
    try {
      await apiFetch(`/api/acomptes/${acompte.id}/statut-paiement`, {
        method: 'POST', body: JSON.stringify({ statut, date_operation: dateEffective }),
      })
      onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setBusy(false) }
  }

  async function annulerImputation(row) {
    if (!confirm(`Annuler l'imputation de ${formatMAD(row.montant)} MAD sur ${row.facture_numero || 'la facture'} ?\nUne contrepassation sera créée si elle a été comptabilisée.`)) return
    setBusy(true); setErreur('')
    try {
      await apiFetch(`/api/acomptes/${acompte.id}/imputations/${row.id}/annuler`, { method: 'POST' })
      onSuccess?.()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setBusy(false) }
  }

  const paiementLabel = acompte.statut_paiement === 'en_attente' ? 'En attente'
    : acompte.statut_paiement === 'rejete' ? 'Rejeté' : 'Encaissé / payé'

  return (
    <Modal titre={`Acompte ${acompte.numero}`} icone="ti-coins" onFermer={onFermer} largeur="md">
      <div className="hp-form-stack">
        {erreur && <InlineNotice tone="danger">{erreur}</InlineNotice>}
        <FormSection icon="ti-info-circle" title="Situation de l'acompte">
          <div className="hp-summary" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Tiers</span><div style={{ fontWeight: 600 }}>{acompte.tiers}</div></div>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Date</span><div>{formatDate(acompte.date)}</div></div>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Montant</span><div style={{ fontWeight: 600 }}>{formatMAD(acompte.montant)} MAD</div></div>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Disponible</span><div style={{ fontWeight: 600 }}>{formatMAD(acompte.montant_disponible)} MAD</div></div>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Paiement</span><div>{paiementLabel}</div></div>
            <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Mode / référence</span><div>{MODES[acompte.mode] || acompte.mode}{acompte.reference ? ` · ${acompte.reference}` : ''}</div></div>
            {acompte.date_echeance && <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Échéance</span><div>{formatDate(acompte.date_echeance)}</div></div>}
            {acompte.date_encaissement && <div><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Date effective</span><div>{formatDate(acompte.date_encaissement)}</div></div>}
            {acompte.banque && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>Banque</span><div>{acompte.banque}</div></div>}
          </div>
          {peutModifier && ['cheque','effet'].includes(acompte.mode) && acompte.statut_paiement === 'en_attente' && acompte.statut !== 'annule' && (
            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
              <label style={{ display: 'grid', gap: 4, flexBasis: '100%' }}>
                Date de l’opération
                <input type="date" value={dateOperation} disabled={busy} style={{ maxWidth: 220 }}
                  onChange={e => setDateOperation(e.target.value)} />
              </label>
              <button type="button" className="hp-btn-primary" disabled={busy} onClick={() => changerStatutPaiement('encaisse')}>
                <i className="ti ti-circle-check" /> Confirmer {acompte.type === 'client' ? "l'encaissement" : 'le paiement'}
              </button>
              <button type="button" className="hp-btn-secondary" disabled={busy} onClick={() => changerStatutPaiement('rejete')}>
                <i className="ti ti-x" /> Marquer rejeté
              </button>
            </div>
          )}
        </FormSection>

        <FormSection icon="ti-history" title="Historique des imputations" description="Une imputation erronée est annulée et contrepassée ; elle n'est jamais supprimée de l'historique.">
          {imputations.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Aucune imputation pour cet acompte.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}>
                <thead><tr style={{ background: 'var(--bg-secondary)' }}>
                  <th style={{ padding: 7, textAlign: 'left' }}>Date</th><th style={{ padding: 7, textAlign: 'left' }}>Facture</th>
                  <th style={{ padding: 7, textAlign: 'right' }}>Montant</th><th style={{ padding: 7, textAlign: 'center' }}>Statut</th><th style={{ width: 42 }} />
                </tr></thead>
                <tbody>{imputations.map(row => <tr key={row.id} style={{ borderBottom: '0.5px solid var(--border-light)', opacity: row.statut === 'annulee' ? 0.55 : 1 }}>
                  <td style={{ padding: 7 }}>{formatDate(row.date_imputation)}</td>
                  <td style={{ padding: 7 }}>{row.facture_numero || `#${row.facture_id}`}</td>
                  <td style={{ padding: 7, textAlign: 'right', fontWeight: 600 }}>{formatMAD(row.montant)} MAD</td>
                  <td style={{ padding: 7, textAlign: 'center' }}>{row.statut === 'annulee' ? 'Annulée' : 'Active'}</td>
                  <td style={{ padding: 7, textAlign: 'center' }}>{peutModifier && row.statut !== 'annulee' && <button type="button" title="Annuler cette imputation" disabled={busy} onClick={() => annulerImputation(row)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#A32D2D' }}><i className="ti ti-arrow-back-up" /><span className="libelle-action" aria-hidden="true">Annuler cette imputation</span></button>}</td>
                </tr>)}</tbody>
              </table>
            </div>
          )}
        </FormSection>
        <ActionBar><button className="hp-btn-secondary" type="button" onClick={onFermer}>Fermer</button></ActionBar>
      </div>
    </Modal>
  )
}

// ── Page principale ───────────────────────────────────────────────────────────
export default function Acomptes() {
  const peutModifier = peutEcrire()
  const { annee } = useExercice()
  const { recharger: rechargerEcritures } = useEcritures() || {}

  const [acomptes, setAcomptes] = useState([])
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const [filtreType, setFiltreType] = useState('tous')
  const [filtreStatut, setFiltreStatut] = useState('tous')
  const [recherche, setRecherche] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [aImputer, setAImputer] = useState(null)
  const [aDetail, setADetail] = useState(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  function charger() {
    setLoading(true); setErreur('')
    apiFetch(`/api/acomptes?exercice=${annee}`)
      .then(setAcomptes)
      .catch(e => setErreur(e.message))
      .finally(() => setLoading(false))
  }
  useEffect(() => { charger() }, [annee])

  const filtres = useMemo(() => acomptes.filter(a => {
    if (filtreType !== 'tous' && a.type !== filtreType) return false
    if (filtreStatut !== 'tous' && a.statut !== filtreStatut) return false
    if (recherche) {
      const r = recherche.toLowerCase()
      if (!a.numero?.toLowerCase().includes(r) && !a.tiers?.toLowerCase().includes(r) &&
          !a.reference?.toLowerCase().includes(r) && !a.facture_numero?.toLowerCase().includes(r)) return false
    }
    return true
  }), [acomptes, filtreType, filtreStatut, recherche])

  const stats = useMemo(() => {
    const actifs = acomptes.filter(a => a.statut !== 'annule' && Number(a.montant_disponible || 0) > 0.01)
    return {
      total: acomptes.length,
      disponibles: actifs.length,
      montantDispo: actifs.reduce((s, a) => s + Number(a.montant_disponible || 0), 0),
    }
  }, [acomptes])

  async function action(fn, okMsg) {
    setBusy(true); setMsg('')
    try {
      await fn()
      setMsg(`✓ ${okMsg}`)
      charger()
      if (rechargerEcritures) rechargerEcritures()
    } catch (e) { setMsg(`✗ ${e.message}`) }
    finally { setBusy(false); setTimeout(() => setMsg(''), 4000) }
  }

  function comptabiliser(a) {
    if (!confirm(`Comptabiliser l'acompte ${a.numero} (${formatMAD(a.montant)} MAD) ?`)) return
    action(() => apiFetch(`/api/acomptes/${a.id}/comptabiliser`, { method: 'POST' }), `Acompte ${a.numero} comptabilisé`)
  }
  function annuler(a) {
    if (!confirm(`Annuler l'acompte ${a.numero} ?${a.est_comptabilisee ? '\nUne contrepassation comptable sera créée automatiquement.' : ''}`)) return
    action(() => apiFetch(`/api/acomptes/${a.id}/annuler`, { method: 'POST' }), `Acompte ${a.numero} annulé`)
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Acomptes</h1>
          <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Avances reçues des clients et versées aux fournisseurs, imputables sur factures
          </p>
        </div>
        <button onClick={() => setShowForm(true)} disabled={!peutModifier}
          title={!peutModifier ? 'Compte en consultation seule' : undefined}
          style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: peutModifier ? 'var(--blue)' : 'var(--border-medium)', color: '#fff', cursor: peutModifier ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
          <i className="ti ti-plus" /> Nouvel acompte
        </button>
      </div>

      <div className={styles.content}>
        {/* Stats */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
              {stats.total} acompte(s)
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: '#EAF3DE', color: '#3B6D11' }}>
              {stats.disponibles} disponible(s)
            </span>
            <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, background: 'var(--bg-secondary)', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
              Montant disponible : <strong>{formatMAD(stats.montantDispo)} MAD</strong>
            </span>
          </div>
        </div>

        {/* Filtres */}
        <div className={styles.card} style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Type</label>
              <select value={filtreType} onChange={e => setFiltreType(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }}>
                <option value="tous">Tous</option>
                <option value="client">Client</option>
                <option value="fournisseur">Fournisseur</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Statut</label>
              <select value={filtreStatut} onChange={e => setFiltreStatut(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', fontSize: 13 }}>
                <option value="tous">Tous</option>
                <option value="disponible">Disponible</option>
                <option value="partiellement_impute">Partiellement imputé</option>
                <option value="impute">Imputé</option>
                <option value="annule">Annulé</option>
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Recherche</label>
              <input value={recherche} onChange={e => setRecherche(e.target.value)}
                placeholder="N°, tiers, référence, facture..."
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
              <i className="ti ti-coins" />
              <span>Aucun acompte {filtreType !== 'tous' || filtreStatut !== 'tous' || recherche ? 'ne correspond aux filtres' : 'pour cet exercice'}</span>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '0.5px solid var(--border-medium)' }}>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>N°</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Date</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Type</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Tiers</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500 }}>Montant</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Mode</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Statut</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 500 }}>Facture</th>
                  <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 500 }}>Compta</th>
                  <th style={{ width: 110 }} />
                </tr>
              </thead>
              <tbody>
                {filtres.map((a, i) => (
                  <tr key={a.id} style={{
                    borderBottom: '0.5px solid var(--border-light)',
                    background: i % 2 === 0 ? '' : 'var(--bg-secondary)',
                    opacity: a.statut === 'annule' ? 0.55 : 1,
                  }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600 }}>{a.numero}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{formatDate(a.date)}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}><BadgeType type={a.type} /></td>
                    <td style={{ padding: '8px 12px' }}>{a.tiers}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}><strong>{formatMAD(a.montant)} MAD</strong>{Number(a.montant_disponible ?? a.montant) < Number(a.montant) - 0.01 && <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)' }}>{formatMAD(a.montant_disponible)} dispo.</div>}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center', fontSize: 11, color: 'var(--text-secondary)' }}>
                      {MODES[a.mode] || a.mode}
                      {a.statut_paiement === 'en_attente' && <div style={{ fontSize: 9.5, color: '#8A5A00' }}>En attente</div>}
                      {a.statut_paiement === 'rejete' && <div style={{ fontSize: 9.5, color: '#A32D2D' }}>Rejeté</div>}
                    </td>
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}><BadgeStatut statut={a.statut} /></td>
                    <td style={{ padding: '8px 12px' }}>
                      {Number(a.nb_factures_imputees || 0) > 1
                        ? <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{a.nb_factures_imputees} factures</span>
                        : a.facture_numero
                          ? <span style={{ fontSize: 10, fontFamily: 'monospace', background: 'var(--blue-light, #E6F1FB)', color: 'var(--blue)', padding: '2px 6px', borderRadius: 3 }}>{a.facture_numero}</span>
                          : <span style={{ color: 'var(--text-tertiary)' }}>—</span>}
                    </td>
                    <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                      {a.est_comptabilisee
                        ? <i className="ti ti-circle-check" style={{ color: '#3B6D11', fontSize: 14 }} title="Comptabilisé" />
                        : <i className="ti ti-circle-dashed" style={{ color: 'var(--text-tertiary)', fontSize: 14 }} title="Non comptabilisé" />}
                    </td>
                    <td style={{ padding: '8px 6px' }}>
                      <div style={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                        <button className={styles.actionButton} aria-label="Voir le détail et l'historique" onClick={() => setADetail(a)} disabled={busy} title="Voir le détail et l'historique"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 14 }}><i className="ti ti-eye" /><span className="libelle-action" aria-hidden="true">Voir le détail et l'historique</span></button>
                        {peutModifier && ['disponible','partiellement_impute'].includes(a.statut) && a.statut_paiement === 'encaisse' && Number(a.montant_disponible ?? 0) > 0.01 && (
                          <button className={styles.actionButton} aria-label="Imputer sur une facture" onClick={() => setAImputer(a)} disabled={busy} title="Imputer sur une facture"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--blue)', fontSize: 14 }}><i className="ti ti-arrow-merge" /><span className="libelle-action" aria-hidden="true">Imputer sur une facture</span></button>
                        )}
                        {peutModifier && !a.est_comptabilisee && a.statut !== 'annule' && a.statut_paiement === 'encaisse' && (
                          <button className={styles.actionButton} aria-label="Comptabiliser" onClick={() => comptabiliser(a)} disabled={busy} title="Comptabiliser"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--blue)', fontSize: 14 }}><i className="ti ti-calculator" /><span className="libelle-action" aria-hidden="true">Comptabiliser</span></button>
                        )}
                        {peutModifier && a.statut === 'disponible' && (
                          <button className={styles.actionButton} aria-label="Annuler l'acompte" onClick={() => annuler(a)} disabled={busy} title="Annuler l'acompte"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 14 }}><i className="ti ti-ban" /><span className="libelle-action" aria-hidden="true">Annuler l'acompte</span></button>
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

      {peutModifier && showForm && (
        <FormulaireAcompte
          onFermer={() => setShowForm(false)}
          onSuccess={() => { charger(); if (rechargerEcritures) rechargerEcritures() }}
        />
      )}
      {peutModifier && aImputer && (
        <ModalImputation
          acompte={aImputer}
          onFermer={() => setAImputer(null)}
          onSuccess={() => { charger(); if (rechargerEcritures) rechargerEcritures() }}
        />
      )}
      {aDetail && (
        <ModalDetailAcompte
          acompte={aDetail}
          onFermer={() => setADetail(null)}
          onSuccess={() => { charger(); if (rechargerEcritures) rechargerEcritures() }}
        />
      )}
    </div>
  )
}
