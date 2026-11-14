import React, { useEffect, useMemo, useState, useRef } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { formatMAD } from '../data/donnees.js'
import styles from './Immobilisations.module.css'
import { API_BASE, formatErreurAPI, peutEcrire, estAdmin } from '../services/api.js'
import { dateLocaleISO } from '../utils/formUtils.js'
import { QUALIFICATIONS_TVA, tauxTVAPourDate, tauxTVAAvecHistorique, qualificationSansTVA } from '../utils/tvaUtils.js'
import { notifier } from '../services/notifications.js'

const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE
async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: 'Erreur' }))
    throw new Error(formatErreurAPI(e.detail))
  }
  if (res.status === 204) return null
  return res.json()
}

const CATEGORIES = ['Matériel de bureau', 'Matériel informatique', 'Véhicule', 'Mobilier', 'Logiciel', 'Bâtiment', 'Terrain', 'Outillage', 'Autre']
const COMPTES_IMMO = [
  { compte: '2220', label: '2220 — Brevets, marques, droits et valeurs similaires' },
  { compte: '2285', label: '2285 — Autres immobilisations incorporelles' },
  { compte: '2311', label: '2311 — Terrains nus' },
  { compte: '2312', label: '2312 — Terrains aménagés' },
  { compte: '2313', label: '2313 — Terrains bâtis' },
  { compte: '2321', label: '2321 — Bâtiments' },
  { compte: '2332', label: '2332 — Matériel et outillage' },
  { compte: '2340', label: '2340 — Matériel de transport' },
  { compte: '2351', label: '2351 — Mobilier de bureau' },
  { compte: '2352', label: '2352 — Matériel de bureau' },
  { compte: '2355', label: '2355 — Matériel informatique' },
  { compte: '2380', label: '2380 — Autres immobilisations corporelles' },
]
const COMPTES_AMORT = [
  { compte: '2822', label: '2822 — Amort. brevets, marques, droits et valeurs similaires' },
  { compte: '2828', label: '2828 — Amort. autres immobilisations incorporelles' },
  { compte: '2831', label: '2831 — Amort. terrains amortissables / aménagements' },
  { compte: '2832', label: '2832 — Amort. constructions' },
  { compte: '28332', label: '28332 — Amort. matériel et outillage' },
  { compte: '2834', label: '2834 — Amort. matériel de transport' },
  { compte: '28351', label: '28351 — Amort. mobilier de bureau' },
  { compte: '28352', label: '28352 — Amort. matériel de bureau' },
  { compte: '28355', label: '28355 — Amort. matériel informatique' },
  { compte: '2838', label: '2838 — Amort. autres immobilisations corporelles' },
]
const COMPTES_DOT = [
  { compte: '61922', label: '61922 — DEA brevets, marques, droits et valeurs similaires' },
  { compte: '61928', label: '61928 — DEA autres immobilisations incorporelles' },
  { compte: '61931', label: '61931 — DEA terrains amortissables / aménagements' },
  { compte: '61932', label: '61932 — DEA constructions' },
  { compte: '61933', label: '61933 — DEA installations techniques, matériel et outillage' },
  { compte: '61934', label: '61934 — DEA matériel de transport' },
  { compte: '61935', label: '61935 — DEA mobilier, matériel de bureau et aménagements divers' },
  { compte: '61938', label: '61938 — DEA autres immobilisations corporelles' },
]

const today = () => dateLocaleISO()
const n = (v) => {
  if (v === null || v === undefined || v === '') return 0
  const x = Number(String(v).replace(',', '.'))
  return Number.isFinite(x) ? x : 0
}

const CATEGORY_DEFAULTS = {
  'Matériel de bureau':     { compte_immo: '2352', compte_amort: '28352', compte_dotation: '61935', duree_amort: 10, amortissable: true },
  'Matériel informatique':  { compte_immo: '2355', compte_amort: '28355', compte_dotation: '61935', duree_amort: 5,  amortissable: true },
  'Véhicule':               { compte_immo: '2340', compte_amort: '2834',  compte_dotation: '61934', duree_amort: 5,  amortissable: true },
  'Mobilier':               { compte_immo: '2351', compte_amort: '28351', compte_dotation: '61935', duree_amort: 10, amortissable: true },
  'Logiciel':               { compte_immo: '2220', compte_amort: '2822',  compte_dotation: '61922', duree_amort: 5,  amortissable: true },
  'Bâtiment':               { compte_immo: '2321', compte_amort: '2832',  compte_dotation: '61932', duree_amort: 20, amortissable: true },
  'Terrain':                { compte_immo: '2311', compte_amort: '2831',  compte_dotation: '61931', duree_amort: null, amortissable: false },
  'Outillage':              { compte_immo: '2332', compte_amort: '28332', compte_dotation: '61933', duree_amort: 10, amortissable: true },
  'Autre':                  { compte_immo: '2380', compte_amort: '2838',  compte_dotation: '61938', duree_amort: 5,  amortissable: true },
}

const FORM_INIT = {
  designation: '', reference: '', categorie: 'Matériel informatique', fournisseur: '', fournisseur_tiers_id: null,
  date_acquisition: today(), date_mise_en_service: today(),
  prix_acquisition_ht: '', taux_tva: 20, qualification_tva: 'taxable', tva_recuperable_pct: 100,
  acquisition_payee: false, date_paiement: '', compte_reglement: '5141',
  amortissable: true, duree_amort: 5, methode: 'lineaire', taux_degressif: '',
  vehicule_tourisme: false,
  compte_immo: '2355', compte_amort: '28355', compte_dotation: '61935',
  compte_tva: '34551', compte_fournisseur: '4481', valeur_residuelle: 0, notes: '',
}

function appliquerCategorie(form, categorie) {
  const defaut = CATEGORY_DEFAULTS[categorie] || CATEGORY_DEFAULTS.Autre
  return {
    ...form,
    categorie,
    compte_immo: defaut.compte_immo,
    compte_amort: defaut.compte_amort,
    compte_dotation: defaut.compte_dotation,
    compte_tva: '34551',
    compte_fournisseur: '4481',
    amortissable: defaut.amortissable,
    duree_amort: defaut.duree_amort,
    methode: categorie === 'Terrain' || categorie === 'Bâtiment' || categorie === 'Logiciel' ? 'lineaire' : form.methode,
    vehicule_tourisme: categorie === 'Véhicule' ? form.vehicule_tourisme : false,
  }
}

function normaliserTexte(v) {
  return String(v || '').trim().replace(/\s+/g, ' ').toLocaleLowerCase('fr')
}

function FormulaireImmo({ onFermer, onSuccess, initial = null }) {
  const [form, setForm] = useState(() => initial ? {
    ...FORM_INIT, ...initial,
    prix_acquisition_ht: initial.prix_acquisition_ht ?? '',
    fournisseur_tiers_id: initial.fournisseur_tiers_id ?? null,
    acquisition_payee: !!initial.date_paiement,
    date_paiement: initial.date_paiement || '',
  } : FORM_INIT)
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')
  const [fournisseurs, setFournisseurs] = useState([])
  const [comptesBancaires, setComptesBancaires] = useState([])
  const [focusFournisseur, setFocusFournisseur] = useState(false)
  const [showComptes, setShowComptes] = useState(false)
  const [comptesPersonnalises, setComptesPersonnalises] = useState(false)
  const acquisitionVerrouillee = !!initial?.ecriture_acquisition_id

  useEffect(() => {
    let actif = true
    Promise.all([
      apiFetch('/api/tiers?type=fournisseur&limit=300').catch(() => []),
      apiFetch('/api/banques').catch(() => []),
    ]).then(([listeFournisseurs, banques]) => {
      if (!actif) return
      setFournisseurs(Array.isArray(listeFournisseurs) ? listeFournisseurs : [])
      setComptesBancaires(Array.isArray(banques) ? banques : [])
      if (!initial && Array.isArray(banques) && banques.length > 0) {
        const compte = banques.find(b => b.compte_comptable)?.compte_comptable
        if (compte) setForm(p => p.compte_reglement === '5141' ? { ...p, compte_reglement: compte } : p)
      }
    })
    return () => { actif = false }
  }, [])

  const calcul = useMemo(() => {
    const ht = n(form.prix_acquisition_ht)
    const taux = qualificationSansTVA(form.qualification_tva) ? 0 : n(form.taux_tva)
    const ded = qualificationSansTVA(form.qualification_tva) ? 0 : Math.max(0, Math.min(100, n(form.tva_recuperable_pct)))
    const tva = ht * taux / 100
    const tvaRecup = tva * ded / 100
    const tvaNonRecup = tva - tvaRecup
    return { ht, tva, tvaRecup, tvaNonRecup, coutEntree: ht + tvaNonRecup, ttc: ht + tva }
  }, [form.prix_acquisition_ht, form.taux_tva, form.qualification_tva, form.tva_recuperable_pct])

  const fournisseurExact = useMemo(() => {
    const cible = normaliserTexte(form.fournisseur)
    return cible ? fournisseurs.find(f => normaliserTexte(f.nom) === cible) || null : null
  }, [fournisseurs, form.fournisseur])

  const fournisseurSelectionne = useMemo(
    () => fournisseurs.find(f => f.id === form.fournisseur_tiers_id) || fournisseurExact,
    [fournisseurs, form.fournisseur_tiers_id, fournisseurExact]
  )

  const suggestionsFournisseur = useMemo(() => {
    const q = normaliserTexte(form.fournisseur)
    const base = q ? fournisseurs.filter(f => normaliserTexte(f.nom).includes(q)) : fournisseurs
    return base.slice(0, 7)
  }, [fournisseurs, form.fournisseur])

  const optionsTresorerie = useMemo(() => {
    const map = new Map([
      ['5141', '5141 — Banque'],
      ['5161', '5161 — Caisse'],
    ])
    comptesBancaires.forEach(b => {
      if (!b.compte_comptable) return
      const detail = [b.banque, b.agence].filter(Boolean).join(' · ')
      map.set(String(b.compte_comptable), `${b.compte_comptable} — ${detail || 'Compte bancaire'}`)
    })
    if (form.compte_reglement && !map.has(String(form.compte_reglement))) {
      map.set(String(form.compte_reglement), `${form.compte_reglement} — Compte actuel`)
    }
    return [...map.entries()].map(([value, label]) => ({ value, label }))
  }, [comptesBancaires, form.compte_reglement])

  function maj(k, v) { setForm(p => ({ ...p, [k]: v })) }
  function majCompte(k, v) { setComptesPersonnalises(true); maj(k, v) }

  function majCategorie(v) {
    if (comptesPersonnalises && !acquisitionVerrouillee) {
      const reinitialiser = window.confirm(`Réappliquer les comptes CGNC recommandés pour « ${v} » ?\n\nOK : appliquer les recommandations\nAnnuler : conserver vos comptes personnalisés`)
      if (!reinitialiser) {
        setForm(p => ({ ...p, categorie: v, vehicule_tourisme: v === 'Véhicule' ? p.vehicule_tourisme : false }))
        return
      }
    }
    setForm(p => appliquerCategorie(p, v))
    setComptesPersonnalises(false)
  }

  function reappliquerComptes() {
    setForm(p => appliquerCategorie(p, p.categorie))
    setComptesPersonnalises(false)
  }

  function majFournisseur(v) {
    const exact = fournisseurs.find(f => normaliserTexte(f.nom) === normaliserTexte(v))
    setForm(p => ({ ...p, fournisseur: v, fournisseur_tiers_id: exact?.id || null }))
  }

  function choisirFournisseur(f) {
    setForm(p => ({ ...p, fournisseur: f.nom, fournisseur_tiers_id: f.id }))
    setFocusFournisseur(false)
  }

  async function handleSave() {
    if (!form.designation || n(form.prix_acquisition_ht) <= 0 || !form.date_acquisition) return
    setLoading(true); setErreur('')
    try {
      const payload = {
        designation: form.designation,
        reference: form.reference || null,
        categorie: form.categorie,
        date_acquisition: form.date_acquisition,
        date_mise_en_service: form.date_mise_en_service || form.date_acquisition,
        prix_acquisition_ht: n(form.prix_acquisition_ht),
        taux_tva: qualificationSansTVA(form.qualification_tva) ? 0 : n(form.taux_tva),
        qualification_tva: form.qualification_tva || 'taxable',
        tva_recuperable_pct: qualificationSansTVA(form.qualification_tva) ? 0 : n(form.tva_recuperable_pct),
        fournisseur: form.fournisseur?.trim() || null,
        fournisseur_tiers_id: form.fournisseur_tiers_id || fournisseurExact?.id || null,
        amortissable: !!form.amortissable,
        duree_amort: form.amortissable ? n(form.duree_amort) : null,
        methode: form.amortissable ? form.methode : 'lineaire',
        taux_degressif: null,
        vehicule_tourisme: !!form.vehicule_tourisme,
        compte_immo: form.compte_immo,
        compte_amort: form.compte_amort,
        compte_dotation: form.compte_dotation,
        compte_tva: form.compte_tva || '34551',
        compte_fournisseur: form.compte_fournisseur || '4481',
        compte_reglement: form.compte_reglement || '5141',
        valeur_residuelle: n(form.valeur_residuelle),
        notes: form.notes || null,
      }
      if (!initial) payload.date_paiement = form.acquisition_payee ? (form.date_paiement || form.date_acquisition) : null

      if (initial) {
        if (acquisitionVerrouillee) {
          delete payload.prix_acquisition_ht
          delete payload.taux_tva
          delete payload.qualification_tva
          delete payload.tva_recuperable_pct
          delete payload.compte_immo
          delete payload.compte_tva
          delete payload.compte_fournisseur
          delete payload.categorie
        }
        // Un libellé modifié ne doit pas renvoyer les paramètres inchangés
        // du plan verrouillé ; les changements réels restent contrôlés par l’API.
        for (const [champ, valeur] of Object.entries(payload)) {
          // Les Decimal de l’API sont sérialisés en chaînes (ex. "0.00").
          const avant = typeof valeur === 'number' && initial[champ] != null && initial[champ] !== ''
            ? Number(initial[champ]) : initial[champ]
          if (valeur === avant && (typeof valeur !== 'number' || Number.isFinite(valeur))) delete payload[champ]
        }
        await apiFetch(`/api/immobilisations/${initial.id}`, { method: 'PATCH', body: JSON.stringify(payload) })
      } else {
        await apiFetch('/api/immobilisations', { method: 'POST', body: JSON.stringify(payload) })
      }
      onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal} style={{ width: 860 }}>
        <div className={styles.modalHeader}>
          <span><i className="ti ti-building-factory" style={{ marginRight: 6 }} />{initial ? 'Modifier l’immobilisation' : 'Nouvelle immobilisation'}</span>
          <button onClick={onFermer} className={styles.btnClose}><i className="ti ti-x" /></button>
        </div>
        <div className={styles.modalBody}>
          {acquisitionVerrouillee && (
            <div className={styles.infoWarning}>
              L’écriture d’acquisition existe : le prix, la TVA et les comptes d’acquisition sont verrouillés pour préserver la cohérence comptable.
            </div>
          )}

          <section className={styles.formSection}>
            <div className={styles.sectionTitle}><i className="ti ti-id" /> Identification</div>
            <div className={styles.formGrid2}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Désignation *</label>
                <input className={styles.input} value={form.designation} onChange={e => maj('designation', e.target.value)} placeholder="Ex: Serveur Dell PowerEdge" />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Référence / n° série</label>
                <input className={styles.input} value={form.reference || ''} onChange={e => maj('reference', e.target.value)} placeholder="Optionnel" />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Catégorie</label>
                <select className={styles.input} disabled={acquisitionVerrouillee} value={form.categorie || ''} onChange={e => majCategorie(e.target.value)}>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <div className={styles.fieldHint}>Les comptes CGNC et la durée recommandée sont proposés automatiquement.</div>
              </div>
              <div className={`${styles.formGroup} ${styles.autocomplete}`}>
                <label className={styles.label}>Fournisseur</label>
                <div className={styles.inputWithIcon}>
                  <i className="ti ti-truck" />
                  <input
                    className={styles.input}
                    value={form.fournisseur || ''}
                    onFocus={() => setFocusFournisseur(true)}
                    onBlur={() => setTimeout(() => setFocusFournisseur(false), 120)}
                    onChange={e => majFournisseur(e.target.value)}
                    placeholder="Rechercher ou saisir un nouveau fournisseur"
                    autoComplete="off"
                  />
                </div>
                {focusFournisseur && (suggestionsFournisseur.length > 0 || (form.fournisseur && !fournisseurExact)) && (
                  <div className={styles.suggestions}>
                    {suggestionsFournisseur.map(f => (
                      <button type="button" key={f.id} className={styles.suggestionItem} onMouseDown={e => { e.preventDefault(); choisirFournisseur(f) }}>
                        <span><i className="ti ti-building-store" /> {f.nom}</span>
                        <small>{f.ville || f.ice || 'Fournisseur existant'}</small>
                      </button>
                    ))}
                    {form.fournisseur?.trim() && !fournisseurExact && (
                      <div className={styles.createSuggestion}><i className="ti ti-plus" /> « {form.fournisseur.trim()} » sera créé comme fournisseur à l’enregistrement</div>
                    )}
                  </div>
                )}
                {fournisseurSelectionne ? (
                  <div className={styles.fieldOk}><i className="ti ti-circle-check" /> Fournisseur existant sélectionné</div>
                ) : form.fournisseur?.trim() ? (
                  <div className={styles.fieldHint}><i className="ti ti-plus" /> Nouveau fournisseur : création automatique à l’enregistrement</div>
                ) : null}
                {fournisseurSelectionne?.assujetti_tva === false && form.qualification_tva === 'taxable' && n(form.taux_tva) > 0 && (
                  <div className={styles.fieldAlert}>Ce fournisseur est marqué non assujetti à la TVA. Vérifie le taux de la facture.</div>
                )}
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Date d’acquisition *</label>
                <input className={styles.input} type="date" value={form.date_acquisition} disabled={!!initial} onChange={e => {
                  const date_acquisition = e.target.value
                  setForm(p => {
                    const autorises = tauxTVAPourDate(date_acquisition).filter(t => t > 0)
                    const courant = Number(p.taux_tva)
                    return {
                      ...p,
                      date_acquisition,
                      date_mise_en_service: initial ? p.date_mise_en_service : date_acquisition,
                      taux_tva: p.qualification_tva === 'taxable' && !autorises.includes(courant)
                        ? (autorises.includes(20) ? 20 : (autorises[0] || 0)) : courant,
                    }
                  })
                }} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Date de mise en service *</label>
                <input className={styles.input} type="date" value={form.date_mise_en_service || form.date_acquisition} onChange={e => maj('date_mise_en_service', e.target.value)} />
              </div>
            </div>
          </section>

          <section className={styles.formSection}>
            <div className={styles.sectionTitle}><i className="ti ti-receipt-tax" /> Acquisition & TVA</div>
            <div className={styles.formGrid3}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Prix d’acquisition HT *</label>
                <input className={styles.input} disabled={acquisitionVerrouillee} type="number" step="0.01" min="0" value={form.prix_acquisition_ht} onChange={e => maj('prix_acquisition_ht', e.target.value)} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Traitement TVA</label>
                <select className={styles.input} disabled={acquisitionVerrouillee} value={form.qualification_tva || 'taxable'} onChange={e => {
                  const qualification_tva = e.target.value
                  setForm(p => {
                    const autorises = tauxTVAPourDate(p.date_acquisition).filter(t => t > 0)
                    return {
                      ...p, qualification_tva,
                      taux_tva: qualification_tva === 'taxable'
                        ? (autorises.includes(Number(p.taux_tva)) ? Number(p.taux_tva) : (autorises.includes(20) ? 20 : (autorises[0] || 0))) : 0,
                      tva_recuperable_pct: qualification_tva === 'taxable' ? p.tva_recuperable_pct : 0,
                    }
                  })
                }}>
                  {QUALIFICATIONS_TVA.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Taux TVA (%)</label>
                <select className={styles.input} disabled={acquisitionVerrouillee || qualificationSansTVA(form.qualification_tva)} value={qualificationSansTVA(form.qualification_tva) ? '0' : String(n(form.taux_tva))} onChange={e => maj('taux_tva', e.target.value)}>
                  {qualificationSansTVA(form.qualification_tva)
                    ? <option value="0">0 % — selon qualification</option>
                    : tauxTVAAvecHistorique(form.date_acquisition, form.taux_tva).filter(t => t > 0).map(t => <option key={t} value={t}>{t} %</option>)}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>TVA récupérable (%)</label>
                <input className={styles.input} disabled={acquisitionVerrouillee || qualificationSansTVA(form.qualification_tva)} type="number" step="0.01" min="0" max="100" value={qualificationSansTVA(form.qualification_tva) ? 0 : form.tva_recuperable_pct} onChange={e => maj('tva_recuperable_pct', e.target.value)} />
              </div>
            </div>
            <div className={styles.calcGrid}>
              {[
                ['TVA totale', calcul.tva], ['TVA récupérable', calcul.tvaRecup],
                ['Coût d’entrée', calcul.coutEntree], ['TTC fournisseur', calcul.ttc],
              ].map(([label, value]) => (
                <div key={label} className={styles.calcCard}>
                  <div>{label}</div><strong>{formatMAD(value)} MAD</strong>
                </div>
              ))}
            </div>
            {calcul.tvaNonRecup > 0 && <div className={styles.fieldAlert}>TVA non récupérable capitalisée dans le coût du bien : {formatMAD(calcul.tvaNonRecup)} MAD.</div>}
          </section>

          {!initial && (
            <section className={styles.formSection}>
              <div className={styles.sectionTitle}><i className="ti ti-credit-card" /> Paiement</div>
              <label className={styles.checkLine}>
                <input type="checkbox" checked={form.acquisition_payee} onChange={e => maj('acquisition_payee', e.target.checked)} /> Acquisition déjà payée
              </label>
              {form.acquisition_payee && <div className={styles.formGrid2} style={{ marginTop: 10 }}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Date de paiement</label>
                  <input className={styles.input} type="date" value={form.date_paiement || form.date_acquisition} onChange={e => maj('date_paiement', e.target.value)} />
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Compte de trésorerie</label>
                  <select className={styles.input} value={form.compte_reglement} onChange={e => maj('compte_reglement', e.target.value)}>
                    {optionsTresorerie.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <div className={styles.fieldHint}>{comptesBancaires.length ? 'Comptes bancaires actifs de la société.' : 'Aucun compte bancaire paramétré : compte CGNC par défaut proposé.'}</div>
                </div>
              </div>}
            </section>
          )}

          <section className={styles.formSection}>
            <div className={styles.sectionTitle}><i className="ti ti-chart-line" /> Amortissement</div>
            <label className={styles.checkLine}>
              <input type="checkbox" checked={!!form.amortissable} disabled={form.categorie === 'Terrain'} onChange={e => maj('amortissable', e.target.checked)} /> Immobilisation amortissable
              {form.categorie === 'Terrain' && <span className={styles.autoBadge}>Non amortissable automatiquement</span>}
            </label>
            {form.amortissable && <div className={styles.formGrid3} style={{ marginTop: 10 }}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Durée (années)</label>
                <input className={styles.input} type="number" min="1" max="100" value={form.duree_amort || ''} onChange={e => maj('duree_amort', e.target.value)} />
                <div className={styles.fieldHint}>Préremplie selon la catégorie, modifiable.</div>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Méthode</label>
                <select className={styles.input} value={form.methode} onChange={e => maj('methode', e.target.value)}>
                  <option value="lineaire">Linéaire</option>
                  <option value="degressif">Dégressif</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Valeur résiduelle</label>
                <input className={styles.input} type="number" min="0" step="0.01" value={form.valeur_residuelle || 0} onChange={e => maj('valeur_residuelle', e.target.value)} />
              </div>
              {form.methode === 'degressif' && <div className={styles.formGroup}>
                <label className={styles.label}>Coefficient fiscal</label>
                <input className={styles.input} readOnly value={n(form.duree_amort) <= 4 ? '1.5' : n(form.duree_amort) <= 6 ? '2' : '3'} />
              </div>}
              {form.categorie === 'Véhicule' && <label className={styles.checkLine} style={{ marginTop: 22 }}>
                <input type="checkbox" checked={!!form.vehicule_tourisme} onChange={e => maj('vehicule_tourisme', e.target.checked)} /> Véhicule de transport de personnes
              </label>}
            </div>}
          </section>

          <section className={styles.formSection}>
            <div className={styles.sectionHeaderRow}>
              <div>
                <div className={styles.sectionTitle} style={{ marginBottom: 2 }}><i className="ti ti-calculator" /> Paramétrage comptable</div>
                <div className={styles.fieldHint}>Comptes proposés automatiquement à partir de la catégorie.</div>
              </div>
              <div className={styles.sectionActions}>
                {comptesPersonnalises && <span className={styles.customBadge}>Personnalisé</span>}
                {!acquisitionVerrouillee && <button type="button" className={styles.btnMini} onClick={reappliquerComptes}><i className="ti ti-refresh" /> Recommandés</button>}
                <button type="button" className={styles.btnMini} onClick={() => setShowComptes(v => !v)}>{showComptes ? 'Masquer' : 'Modifier les comptes'}</button>
              </div>
            </div>
            <div className={styles.accountSummary}>
              <div><span>Immobilisation</span><strong>{form.compte_immo}</strong></div>
              <div><span>Amortissement</span><strong>{form.compte_amort}</strong></div>
              <div><span>Dotation</span><strong>{form.compte_dotation}</strong></div>
              <div><span>TVA immo</span><strong>{form.compte_tva}</strong></div>
              <div><span>Dette acquisition</span><strong>{form.compte_fournisseur}</strong></div>
            </div>
            {showComptes && <div className={styles.advancedAccounts}>
              <div className={styles.formGrid3}>
                <div className={styles.formGroup}><label className={styles.label}>Immobilisation</label><select disabled={acquisitionVerrouillee} className={styles.input} value={form.compte_immo} onChange={e => majCompte('compte_immo', e.target.value)}>{COMPTES_IMMO.map(c => <option key={c.compte} value={c.compte}>{c.label}</option>)}</select></div>
                <div className={styles.formGroup}><label className={styles.label}>Amortissement</label><select className={styles.input} value={form.compte_amort} onChange={e => majCompte('compte_amort', e.target.value)}>{COMPTES_AMORT.map(c => <option key={c.compte} value={c.compte}>{c.label}</option>)}</select></div>
                <div className={styles.formGroup}><label className={styles.label}>Dotation</label><select className={styles.input} value={form.compte_dotation} onChange={e => majCompte('compte_dotation', e.target.value)}>{COMPTES_DOT.map(c => <option key={c.compte} value={c.compte}>{c.label}</option>)}</select></div>
                <div className={styles.formGroup}><label className={styles.label}>TVA immobilisation</label><select disabled={acquisitionVerrouillee} className={styles.input} value={form.compte_tva} onChange={e => majCompte('compte_tva', e.target.value)}><option value="34551">34551 — TVA récupérable sur immobilisations</option></select></div>
                <div className={styles.formGroup}><label className={styles.label}>Dette acquisition</label><select disabled={acquisitionVerrouillee} className={styles.input} value={form.compte_fournisseur} onChange={e => majCompte('compte_fournisseur', e.target.value)}><option value="4481">4481 — Dettes sur acquisition d’immobilisations</option><option value="4411">4411 — Fournisseurs</option></select></div>
              </div>
            </div>}
          </section>

          <div className={styles.formGroup}><label className={styles.label}>Notes</label><textarea className={styles.input} rows={2} value={form.notes || ''} onChange={e => maj('notes', e.target.value)} placeholder="Informations complémentaires…" /></div>
          {erreur && <div className={styles.erreur}>{erreur}</div>}
        </div>
        <div className={styles.modalFooter}>
          <div className={styles.footerHint}><i className="ti ti-sparkles" /> Les paramètres recommandés restent modifiables avant comptabilisation.</div>
          <div className={styles.footerActions}>
            <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
            <button className={styles.btnPrim} onClick={handleSave} disabled={loading || !form.designation || n(form.prix_acquisition_ht) <= 0}><i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : initial ? 'Modifier' : 'Créer'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function FormulaireSortie({ immo, onFermer, onSuccess }) {
  const [form, setForm] = useState({ type_sortie: 'cession', date_sortie: today(), prix_cession_ht: '', taux_tva_cession: 20, qualification_tva_cession: 'taxable', encaissement_immediat: true, date_encaissement: today(), compte_tresorerie: '5141' })
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')
  const [apercu, setApercu] = useState(null)
  const [calculEnCours, setCalculEnCours] = useState(false)
  const cleFormulaire = JSON.stringify(form)
  const revisionFormulaire = useRef(0)
  useEffect(() => { revisionFormulaire.current += 1; setApercu(null) }, [cleFormulaire])
  const apercuCourant = apercu?.cle === cleFormulaire ? apercu : null
  const tva = n(form.prix_cession_ht) * (qualificationSansTVA(form.qualification_tva_cession) ? 0 : n(form.taux_tva_cession)) / 100

  function construirePayload() {
    return { ...form, prix_cession_ht: n(form.prix_cession_ht), taux_tva_cession: qualificationSansTVA(form.qualification_tva_cession) ? 0 : n(form.taux_tva_cession), date_encaissement: form.encaissement_immediat ? (form.date_encaissement || form.date_sortie) : null }
  }

  async function calculerApercu() {
    const cle = cleFormulaire
    const revision = revisionFormulaire.current
    setCalculEnCours(true)
    try {
      const resultat = await apiFetch(`/api/immobilisations/${immo.id}/sortie/apercu`, { method: 'POST', body: JSON.stringify(construirePayload()) })
      if (revision === revisionFormulaire.current) setApercu({ cle, resultat })
    } catch (e) { if (revision === revisionFormulaire.current) setApercu({ cle, erreur: e.message }) }
    finally { setCalculEnCours(false) }
  }

  async function envoyer() {
    setLoading(true); setErreur('')
    try {
      const payload = { ...construirePayload(), ...(apercuCourant?.resultat ? { empreinte_apercu: apercuCourant.resultat.empreinte_apercu } : {}) }
      const res = await apiFetch(`/api/immobilisations/${immo.id}/sortie`, { method: 'POST', body: JSON.stringify(payload) })
      notifier(`${res.type_sortie === 'cession' ? 'Cession' : 'Mise au rebut'} comptabilisée\nVNC : ${formatMAD(res.vnc)} MAD\nRésultat de sortie : ${formatMAD(res.resultat_cession)} MAD`)
      onSuccess()
    } catch (e) { setErreur(e.message); setApercu(null) }
    finally { setLoading(false) }
  }

  return <div className={styles.modalOverlay}>
    <div className={styles.modal} style={{ width: 600 }}>
      <div className={styles.modalHeader}><span>Sortie — {immo.designation}</span><button className={styles.btnClose} disabled={loading} onClick={onFermer}><i className="ti ti-x" /></button></div>
      <div className={styles.modalBody}>
        <fieldset disabled={loading} style={{border:0,padding:0,margin:0,minWidth:0}}>
        <div className={styles.formGrid2}>
          <div className={styles.formGroup}><label className={styles.label}>Type de sortie</label><select className={styles.input} value={form.type_sortie} onChange={e => setForm(p => ({ ...p, type_sortie: e.target.value }))}><option value="cession">Cession</option><option value="rebut">Mise au rebut</option></select></div>
          <div className={styles.formGroup}><label className={styles.label}>Date de sortie</label><input className={styles.input} type="date" value={form.date_sortie} onChange={e => {
            const date_sortie = e.target.value
            setForm(p => {
              const autorises = tauxTVAPourDate(date_sortie).filter(t => t > 0)
              const courant = Number(p.taux_tva_cession)
              return { ...p, date_sortie, taux_tva_cession: p.qualification_tva_cession === 'taxable' && !autorises.includes(courant)
                ? (autorises.includes(20) ? 20 : (autorises[0] || 0)) : courant }
            })
          }} /></div>
        </div>
        {form.type_sortie === 'cession' && <>
          <div className={styles.formGrid2}>
            <div className={styles.formGroup}><label className={styles.label}>Prix de cession HT</label><input className={styles.input} type="number" step="0.01" value={form.prix_cession_ht} onChange={e => setForm(p => ({ ...p, prix_cession_ht: e.target.value }))} /></div>
            <div className={styles.formGroup}><label className={styles.label}>Traitement TVA</label><select className={styles.input} value={form.qualification_tva_cession} onChange={e => {
              const qualification_tva_cession = e.target.value
              setForm(p => {
                const autorises = tauxTVAPourDate(p.date_sortie).filter(t => t > 0)
                return { ...p, qualification_tva_cession, taux_tva_cession: qualification_tva_cession === 'taxable'
                  ? (autorises.includes(Number(p.taux_tva_cession)) ? Number(p.taux_tva_cession) : (autorises.includes(20) ? 20 : (autorises[0] || 0))) : 0 }
              })
            }}>{QUALIFICATIONS_TVA.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}</select></div>
          </div>
          <div className={styles.formGrid2}>
            <div className={styles.formGroup}><label className={styles.label}>TVA cession (%)</label><select className={styles.input} disabled={qualificationSansTVA(form.qualification_tva_cession)} value={qualificationSansTVA(form.qualification_tva_cession) ? '0' : String(n(form.taux_tva_cession))} onChange={e => setForm(p => ({ ...p, taux_tva_cession: Number(e.target.value) }))}>{qualificationSansTVA(form.qualification_tva_cession) ? <option value="0">0 % — selon qualification</option> : tauxTVAPourDate(form.date_sortie).filter(t => t > 0).map(t => <option key={t} value={t}>{t} %</option>)}</select></div>
          </div>
          <div style={{ fontSize: 11, background: 'var(--bg-secondary)', padding: 8, borderRadius: 6 }}>TTC cession : <b>{formatMAD(n(form.prix_cession_ht) + tva)} MAD</b> — TVA : {formatMAD(tva)} MAD</div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}><input type="checkbox" checked={form.encaissement_immediat} onChange={e => setForm(p => ({ ...p, encaissement_immediat: e.target.checked }))} /> Cession encaissée immédiatement</label>
          {form.encaissement_immediat && <div className={styles.formGrid2}>
            <div className={styles.formGroup}><label className={styles.label}>Date d’encaissement</label><input className={styles.input} type="date" value={form.date_encaissement} onChange={e => setForm(p => ({ ...p, date_encaissement: e.target.value }))} /></div>
            <div className={styles.formGroup}><label className={styles.label}>Compte trésorerie</label><input className={styles.input} value={form.compte_tresorerie} onChange={e => setForm(p => ({ ...p, compte_tresorerie: e.target.value }))} /></div>
          </div>}
        </>}
        <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>La sortie calcule la dotation jusqu’à la date de sortie, retire la valeur brute et les amortissements cumulés du bilan et constate la VNA. Les exercices clôturés ne sont jamais réécrits.</div>
        <section aria-label="Aperçu de la sortie" style={{marginTop:12,padding:12,border:'1px solid var(--border-light)',borderRadius:8,overflowWrap:'anywhere'}}>
          <button className={styles.btnSec} type="button" disabled={loading || calculEnCours || !form.date_sortie || (form.type_sortie === 'cession' && n(form.prix_cession_ht) <= 0)} onClick={calculerApercu}>{calculEnCours ? 'Calcul de l’aperçu…' : 'Calculer avant comptabilisation'}</button>
          {apercuCourant?.erreur && <p role="alert">{apercuCourant.erreur}</p>}
          {apercuCourant?.resultat && <>
            <h3>Montants avant enregistrement</h3><p>{apercuCourant.resultat.convention}</p>
            <dl style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(0,1fr)',gap:8}}>{[['Valeur brute','valeur_brute'],['Amortissements selon le plan','cumul_amortissement'],['VNC théorique à la sortie','vnc'],['Résultat comptable de sortie','resultat_cession'],['TVA de cession','tva_cession'],['Prix de cession TTC','ttc_cession']].map(([label,champ])=><React.Fragment key={champ}><dt>{label}</dt><dd style={{margin:0,textAlign:'right'}} data-testid={`sortie-apercu-${champ}`}>{formatMAD(apercuCourant.resultat[champ])} MAD</dd></React.Fragment>)}</dl>
            <h4>Dotations jusqu’à la sortie</h4>{apercuCourant.resultat.dotations.length ? <ul>{apercuCourant.resultat.dotations.map(d=><li key={d.annee}>{d.annee} · {d.debut_periode} au {d.fin_periode} : {formatMAD(d.dotation)} MAD — {d.etat}</li>)}</ul> : <p>Aucune dotation sur les exercices examinés.</p>}
            <p>{apercuCourant.resultat.avertissement}</p>
          </>}
          {!apercuCourant && <p>Consultez la VNC, le prorata et le résultat avant de créer les écritures. Un changement de saisie retire l’ancien aperçu.</p>}
        </section>
        </fieldset>
        {erreur && <div className={styles.erreur}>{erreur}</div>}
      </div>
      <div className={styles.modalFooter}><button className={styles.btnSec} disabled={loading} onClick={onFermer}>Annuler</button><button className={styles.btnPrim} disabled={loading || calculEnCours || (form.type_sortie === 'cession' && n(form.prix_cession_ht) <= 0)} onClick={envoyer}>{loading ? 'Comptabilisation...' : 'Comptabiliser la sortie'}</button></div>
    </div>
  </div>
}

function TableauAmortissement({ immo, annee, onGenerer }) {
  const ecriture = peutEcrire()
  const [tableau, setTableau] = useState([])
  const [loading, setLoading] = useState(true)
  const [erreurLecture, setErreurLecture] = useState('')
  const requeteLecture = useRef(0)
  const [generant, setGenerant] = useState(null)
  async function chargerPlan() {
    const requete = ++requeteLecture.current
    setLoading(true); setErreurLecture('')
    try {
      const d = await apiFetch(`/api/immobilisations/${immo.id}/tableau`)
      if (requete === requeteLecture.current) setTableau(d.tableau)
    } catch (e) {
      if (requete === requeteLecture.current) setErreurLecture(e.message || 'Lecture indisponible.')
    } finally { if (requete === requeteLecture.current) setLoading(false) }
  }
  useEffect(() => { chargerPlan(); return () => { requeteLecture.current += 1 } }, [immo.id])

  async function generer(a) {
    setGenerant(a)
    try { const res = await apiFetch(`/api/immobilisations/${immo.id}/generer-ecriture?annee=${a}`, { method: 'POST' }); notifier(`Écriture générée — ${a} : ${formatMAD(res.dotation)} MAD`); onGenerer() }
    catch (e) { notifier.erreur(e.message) } finally { setGenerant(null) }
  }
  if (loading) return <div style={{ padding: 20, textAlign: 'center' }}><i className="ti ti-loader-2 ti-spin" /></div>
  if (erreurLecture) return <div role="alert" style={{padding:14}}><p>Impossible de charger le plan d’amortissement.</p><p>{erreurLecture}</p><button className={styles.btnSec} onClick={chargerPlan}>Réessayer le plan</button></div>
  if (!immo.amortissable) return <div style={{ padding: 14, fontSize: 12, color: 'var(--text-secondary)' }}>Immobilisation non amortissable.</div>
  return <table className={styles.table}>
    <thead><tr><th>Année</th><th>Période</th><th style={{ textAlign: 'right' }}>Prorata</th><th style={{ textAlign: 'right' }}>Dotation</th><th style={{ textAlign: 'right' }}>Cumul</th><th style={{ textAlign: 'right' }}>VNC</th><th /></tr></thead>
    <tbody>{tableau.map((l, i) => <tr key={l.annee} style={{ background: l.annee === annee ? '#EBF5FB' : i % 2 === 0 ? 'var(--bg-secondary)' : '' }}>
      <td style={{ fontWeight: l.annee === annee ? 700 : 400 }}>{l.annee}</td><td style={{ fontSize: 10 }}>{l.debut_periode} → {l.fin_periode}</td><td style={{ textAlign: 'right' }}>{(n(l.prorata) * 100).toFixed(2)}%</td>
      <td style={{ textAlign: 'right', fontWeight: 500 }}>{formatMAD(l.dotation)} MAD</td><td style={{ textAlign: 'right' }}>{formatMAD(l.cumul)} MAD</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{formatMAD(l.valeur_nette)} MAD</td>
      <td>{ecriture && <button className={styles.btnAction} style={{ width: 'auto', padding: '0 7px', fontSize: 10 }} disabled={generant === l.annee || !immo.actif} onClick={() => generer(l.annee)}>{generant === l.annee ? '...' : 'Générer'}</button>}</td>
    </tr>)}</tbody>
  </table>
}


function ReconciliationHistorique({ annee, onFermer, onSuccess }) {
  const administrateur = estAdmin()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const [categories, setCategories] = useState({})
  const [selection, setSelection] = useState({})
  const [reconstitution, setReconstitution] = useState({})

  async function chargerDiagnostic() {
    setLoading(true); setErreur('')
    try {
      const d = await apiFetch(`/api/immobilisations/reconciliation-historique?exercice=${annee}`)
      setData(d)
      const cats = {}; const sel = {}; const rec = {}
      ;(d.items || []).forEach(x => {
        cats[x.id] = x.categorie_suggeree || x.categorie_actuelle || 'Autre'
        sel[x.id] = !!(x.comptes_a_reclasser || x.suggestion_categorie_forte)
        if (x.acquisition?.statut === 'manquante_exercice') {
          rec[x.id] = { selected: true, mode: 'dette_acquisition', compte: x.acquisition.compte_fournisseur || '4481' }
        } else if (x.acquisition?.statut === 'manquante_anterieure') {
          rec[x.id] = { selected: false, mode: 'reprise_anterieure', compte: '' }
        }
      })
      setCategories(cats); setSelection(sel); setReconstitution(rec)
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { chargerDiagnostic() }, [annee])

  function badgeAcquisition(x) {
    const st = x.acquisition?.statut
    if (st === 'comptabilisee') return ['Comptabilisée', '#EAF3DE', '#3B6D11']
    if (st === 'manquante_exercice') return [`Acquisition ${annee} manquante`, '#FCEBEB', '#A32D2D']
    if (st === 'manquante_anterieure') return ['Antériorité manquante', '#FFF4E5', '#854F0B']
    return [st || 'À vérifier', '#F1F1F1', '#666']
  }

  async function appliquer() {
    const items = (data?.items || [])
      .filter(x => selection[x.id] && (x.comptes_a_reclasser || x.suggestion_categorie_forte))
      .map(x => ({ immo_id: x.id, categorie_cible: categories[x.id] || x.categorie_suggeree || 'Autre' }))
    if (!items.length) return
    if (!confirm(`Générer les reclassements sûrs de ${items.length} immobilisation(s) ?\n\nAucun montant, acquisition, dette ou TVA manquante ne sera créé.`)) return
    setEnvoi(true); setErreur('')
    try {
      const r = await apiFetch('/api/immobilisations/reconciliation-historique/reclasser', {
        method: 'POST', body: JSON.stringify({ exercice: annee, items }),
      })
      notifier(`${r.nb_ecritures} écriture(s) de reclassement créée(s) en brouillon.\n${r.sans_ecriture?.length || 0} immobilisation(s) : registre corrigé sans écriture artificielle.\n\nContrôlez puis validez les OD dans le Journal.`)
      onSuccess()
      onFermer()
    } catch (e) { setErreur(e.message) }
    finally { setEnvoi(false) }
  }

  function changerModeReconstitution(id, mode, x) {
    setReconstitution(p => {
      const current = p[id] || {}
      let compte = current.compte || ''
      if (mode === 'dette_acquisition') compte = x.acquisition?.compte_fournisseur || '4481'
      if (mode === 'tresorerie') compte = x.acquisition?.compte_reglement || '5141'
      if (mode === 'reprise_anterieure') compte = ''
      return { ...p, [id]: { ...current, mode, compte } }
    })
  }

  async function reconstituerAcquisitions() {
    const items = (data?.items || []).filter(x => x.acquisition?.statut?.startsWith('manquante') && reconstitution[x.id]?.selected)
      .map(x => ({ immo_id: x.id, mode: reconstitution[x.id]?.mode, compte_contrepartie: (reconstitution[x.id]?.compte || '').trim() }))
    if (!items.length) return
    const invalide = items.find(x => !/^[1-5][0-9]{2,9}$/.test(x.compte_contrepartie))
    if (invalide) { setErreur('Chaque reconstitution sélectionnée doit avoir un compte de contrepartie de bilan valide (classe 1 à 5).'); return }
    if (!confirm(`Créer ${items.length} écriture(s) de reconstitution en brouillon ?\n\nHisabPro utilisera uniquement les comptes de contrepartie que vous avez confirmés.`)) return
    setEnvoi(true); setErreur('')
    try {
      const r = await apiFetch('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions', {
        method: 'POST', body: JSON.stringify({ exercice: annee, items }),
      })
      notifier(`${r.nb_ecritures} écriture(s) de reconstitution créée(s) en brouillon.\n\nContrôlez-les dans le Journal avant validation.`)
      await chargerDiagnostic(); await onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setEnvoi(false) }
  }

  async function corrigerAmortissements() {
    if (!confirm(`Générer les corrections de dotation ${annee} pour ramener chaque immobilisation au plan d'amortissement actuel ?\n\nLes exercices antérieurs ne seront pas réécrits.`)) return
    setEnvoi(true); setErreur('')
    try {
      const r = await apiFetch('/api/immobilisations/reconciliation-historique/corriger-amortissements', {
        method: 'POST', body: JSON.stringify({ exercice: annee, immo_ids: null }),
      })
      notifier(`${r.nb_ecritures} correction(s) d'amortissement créée(s) en brouillon.\n${r.ignorees?.length || 0} immobilisation(s) ignorée(s).\n\nContrôlez les écritures AM dans le Journal.`)
      await chargerDiagnostic(); await onSuccess()
    } catch (e) { setErreur(e.message) }
    finally { setEnvoi(false) }
  }

  return <div className={styles.modalOverlay}>
    <div className={styles.modal} style={{ width: 'min(1180px, 96vw)', maxHeight: '90vh' }}>
      <div className={styles.modalHeader}>
        <span><i className="ti ti-adjustments-check" style={{ marginRight: 6 }} />Réconciliation historique — {annee}</span>
        <button className={styles.btnClose} onClick={onFermer}><i className="ti ti-x" /></button>
      </div>
      <div className={styles.modalBody} style={{ overflow: 'auto' }}>
        {loading ? <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /> Diagnostic...</div> : <>
          {!administrateur && <p role="status">Diagnostic en consultation : les corrections sont réservées à un administrateur.</p>}
          <fieldset disabled={!administrateur || !data?.peut_reclasser || envoi} style={{border:0,padding:0,margin:0,minWidth:0}}>
          {data && <div className={styles.reconciliationKpis} style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 10 }}>
            {[
              ['Catégories suspectes', data.nb_categories_suspectes],
              ['Acquisitions manquantes', data.nb_acquisitions_manquantes],
              ['Écarts amortissement', data.nb_ecarts_amortissement],
              ['TVA incohérentes', data.nb_tva_incoherentes],
            ].map(([l,v]) => <div key={l} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 9 }}><div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{l}</div><b>{v}</b></div>)}
          </div>}

          {!data?.peut_reclasser && <div className={styles.infoWarning} style={{ marginBottom: 10 }}>
            Exercice {annee} clôturé : diagnostic uniquement. Rouvrez l'exercice avant de générer les reclassements.
          </div>}
          <div style={{ fontSize: 11, padding: 9, borderRadius: 7, background: '#F0F7FF', marginBottom: 10 }}>
            <b>Garde-fou :</b> cette action ne fabrique jamais une acquisition, une dette fournisseur, une TVA ou un solde d'ouverture manquant. Elle ne fait que transférer des montants déjà comptabilisés vers les comptes de la catégorie confirmée, sans changer le résultat.
          </div>

          <div style={{ overflowX: 'auto' }}><table className={`${styles.table} ${styles.reconciliationTable}`} style={{ minWidth: 1080 }}>
            <thead><tr><th></th><th>Immobilisation</th><th>Catégorie actuelle</th><th>Catégorie cible</th><th>Comptes</th><th>Acquisition</th><th>Amort. cumulé</th><th>Alertes</th></tr></thead>
            <tbody>{(data?.items || []).map(x => {
              const [lab,bg,col] = badgeAcquisition(x)
              const cible = categories[x.id] || x.categorie_suggeree
              const comptesCible = CATEGORY_DEFAULTS[cible] || CATEGORY_DEFAULTS.Autre
              const alerts = []
              if (x.suggestion_categorie_forte) alerts.push('Catégorie suspecte')
              if (x.tva?.incoherente) alerts.push('TVA historique incohérente')
              if (Math.abs(n(x.amortissement?.ecart_cumule)) > .01) alerts.push(`Écart amort. ${formatMAD(x.amortissement.ecart_cumule)}`)
              return <tr key={x.id}>
                <td data-label="Sélectionner"><input type="checkbox" checked={!!selection[x.id]} onChange={e => setSelection(p => ({...p,[x.id]:e.target.checked}))} /></td>
                <td data-label="Immobilisation"><b>{x.designation}</b><div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{x.date_acquisition}</div></td>
                <td data-label="Catégorie actuelle">{x.categorie_actuelle || '—'}{x.suggestion_categorie_forte && <div style={{ fontSize: 9, color: '#A32D2D' }}>Suggestion forte : {x.categorie_suggeree}</div>}</td>
                <td data-label="Catégorie cible"><select className={styles.input} style={{ minWidth: 150 }} value={cible} onChange={e => setCategories(p => ({...p,[x.id]:e.target.value}))}>{(data?.categories || CATEGORIES).map(c => <option key={c}>{c}</option>)}</select></td>
                <td data-label="Comptes" style={{ fontSize: 10 }}>
                  <div>{x.comptes_actuels.compte_immo} → <b>{comptesCible.compte_immo}</b></div>
                  <div>{x.comptes_actuels.compte_amort} → <b>{comptesCible.compte_amort}</b></div>
                  <div>{x.comptes_actuels.compte_dotation} → <b>{comptesCible.compte_dotation}</b></div>
                </td>
                <td data-label="Acquisition"><span style={{ fontSize: 9, borderRadius: 20, padding: '2px 6px', background: bg, color: col }}>{lab}</span><div style={{ fontSize: 9, marginTop: 3 }}>Registre {formatMAD(x.acquisition.brut_registre)} · compta {formatMAD(x.acquisition.brut_comptabilise)}</div></td>
                <td data-label="Amortissement cumulé" style={{ fontSize: 10 }}>Attendu <b>{formatMAD(x.amortissement.attendu_cumule)}</b><br/>Compta <b>{formatMAD(x.amortissement.comptabilise_cumule)}</b></td>
                <td data-label="Alertes" style={{ fontSize: 9, color: alerts.length ? '#854F0B' : '#3B6D11' }}>{alerts.length ? alerts.join(' · ') : 'Aucune alerte'}</td>
              </tr>
            })}</tbody>
          </table></div>

          {(data?.items || []).some(x => x.acquisition?.statut?.startsWith('manquante')) && <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>Reconstitution contrôlée des acquisitions manquantes</div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginBottom: 8 }}>
              Une acquisition de {annee} reprend les montants HT/TVA/TTC déjà stockés dans le registre. Une antériorité est reprise au 01/01/{annee}, sans recréer de TVA historique. Le compte de contrepartie reste toujours sous votre contrôle.
            </div>
            <div style={{ overflowX: 'auto' }}><table className={`${styles.table} ${styles.reconciliationTable}`} style={{ minWidth: 1000 }}>
              <thead><tr><th></th><th>Immobilisation</th><th>Traitement</th><th>Montants repris</th><th>Compte de contrepartie</th></tr></thead>
              <tbody>{(data?.items || []).filter(x => x.acquisition?.statut?.startsWith('manquante')).map(x => {
                const cfg = reconstitution[x.id] || {}
                const ancien = x.acquisition.statut === 'manquante_anterieure'
                return <tr key={`reconst-${x.id}`}>
                  <td data-label="Sélectionner"><input type="checkbox" checked={!!cfg.selected} disabled={!data?.peut_reclasser} onChange={e => setReconstitution(p => ({...p,[x.id]:{...(p[x.id]||{}),selected:e.target.checked}}))} /></td>
                  <td data-label="Immobilisation"><b>{x.designation}</b><div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{x.date_acquisition}</div></td>
                  <td data-label="Traitement">{ancien ? <div><b>Reprise d'ouverture</b><div style={{ fontSize: 9 }}>Écriture AN au 01/01/{annee}</div></div> : <select className={styles.input} value={cfg.mode || 'dette_acquisition'} onChange={e => changerModeReconstitution(x.id, e.target.value, x)}>
                    <option value="dette_acquisition">Dette d'acquisition</option><option value="tresorerie">Paiement direct trésorerie</option><option value="autre">Autre contrepartie de bilan</option>
                  </select>}</td>
                  <td data-label="Montants repris" style={{ fontSize: 10 }}>{ancien ? <>
                    Brut <b>{formatMAD(x.acquisition.brut_registre)}</b><br/>Amort. antérieurs <b>{formatMAD(x.acquisition.amortissement_ouverture_suggere)}</b><br/>VNC ouverture <b>{formatMAD(x.acquisition.vnc_ouverture_suggeree)}</b>
                  </> : <>
                    HT <b>{formatMAD(x.acquisition.prix_ht)}</b><br/>TVA récup. <b>{formatMAD(x.acquisition.tva_recuperable_registre)}</b><br/>TTC <b>{formatMAD(x.acquisition.ttc_registre)}</b>
                  </>}</td>
                  <td data-label="Compte de contrepartie"><input className={styles.input} value={cfg.compte || ''} placeholder={ancien ? 'Compte d’ouverture à confirmer' : '4481 / 5141 / autre'} onChange={e => setReconstitution(p => ({...p,[x.id]:{...(p[x.id]||{}),compte:e.target.value}}))} />
                    {ancien && <div style={{ fontSize: 9, color: '#854F0B', marginTop: 3 }}>Aucun compte n’est proposé automatiquement pour une antériorité.</div>}
                  </td>
                </tr>
              })}</tbody>
            </table></div>
          </div>}
          </fieldset>
        </>}
        {erreur && <div className={styles.erreur} style={{ marginTop: 10 }}>{erreur}</div>}
      </div>
      <div className={styles.modalFooter} style={{ gap: 7, flexWrap: 'wrap' }}>
        <button className={styles.btnSec} onClick={onFermer}>Fermer</button>
        {administrateur && <>
          <button className={styles.btnSec} disabled={loading || envoi || !data?.peut_reclasser || !(data?.items || []).some(x => selection[x.id] && (x.comptes_a_reclasser || x.suggestion_categorie_forte))} onClick={appliquer}>Reclassements sûrs</button>
          <button className={styles.btnPrim} disabled={loading || envoi || !data?.peut_reclasser || !(data?.items || []).some(x => x.acquisition?.statut?.startsWith('manquante') && reconstitution[x.id]?.selected)} onClick={reconstituerAcquisitions}>{envoi ? 'Génération...' : 'Reconstituer acquisitions'}</button>
          <button className={styles.btnSec} title={data?.nb_acquisitions_manquantes ? 'Résolvez d’abord les acquisitions manquantes' : ''} disabled={loading || envoi || !data?.peut_reclasser || !!data?.nb_acquisitions_manquantes || !data?.nb_ecarts_amortissement} onClick={corrigerAmortissements}>Corriger amortissements {annee}</button>
        </>}
      </div>
    </div>
  </div>
}

export default function Immobilisations() {
  const ecriture = peutEcrire()
  const { annee } = useExercice()
  const { recharger: rechargerEcritures } = useEcritures()
  const [immobilisations, setImmobilisations] = useState([])
  const [loading, setLoading] = useState(true)
  const [erreurChargement, setErreurChargement] = useState('')
  const requeteChargement = useRef(0)
  const [showForm, setShowForm] = useState(false)
  const [editImmo, setEditImmo] = useState(null)
  const [sortieImmo, setSortieImmo] = useState(null)
  const [immoDetail, setImmoDetail] = useState(null)
  const [genDotations, setGenDotations] = useState(false)
  const [showReconciliation, setShowReconciliation] = useState(false)
  const [aCreer, setACreer] = useState([])  // lot 979 : achats d'immobilisations par facture sans fiche
  const chargerACreer = () => apiFetch('/api/immobilisations/a-creer-depuis-factures').then(setACreer).catch(() => setACreer([]))
  useEffect(() => { chargerACreer() }, [])
  async function creerDepuisFacture(x) {
    const saisie = x.duree_defaut ? window.prompt(`Créer la fiche de « ${x.designation} » (${formatMAD(x.montant_ht)} MAD HT, compte ${x.compte}).
Durée d'amortissement en années :`, String(x.duree_defaut)) : ''
    if (saisie === null) return
    try {
      await apiFetch(`/api/immobilisations/depuis-facture/${x.facture_id}`, { method: 'POST', body: JSON.stringify({ ligne_id: x.ligne_id, duree_amort: saisie ? Number(saisie) : null }) })
      notifier.succes(`Fiche créée pour « ${x.designation} ».`)
      await Promise.all([charger(), chargerACreer()])
    } catch (e) { notifier.erreur(e.message) }
  }

  async function charger() {
    const requete = ++requeteChargement.current
    setLoading(true); setErreurChargement('')
    try {
      const lignes = await apiFetch('/api/immobilisations?inclure_sorties=true')
      if (requete === requeteChargement.current) setImmobilisations(lignes)
    } catch (e) {
      if (requete === requeteChargement.current) setErreurChargement(e.message || 'Lecture indisponible.')
    } finally { if (requete === requeteChargement.current) setLoading(false) }
  }
  async function rafraichirCompta() {
    await Promise.all([charger(), rechargerEcritures()])
  }
  useEffect(() => { charger(); return () => { requeteChargement.current += 1 } }, [])

  async function genererDotationsAnnee() {
    if (!confirm(`Générer les dotations ${annee} pour toutes les immobilisations concernées ?`)) return
    setGenDotations(true)
    try { const res = await apiFetch(`/api/immobilisations/generer-dotations-annee?annee=${annee}`, { method: 'POST' }); notifier(`${res.nb_generees} dotation(s) générée(s) — Total ${formatMAD(res.total_dotation)} MAD\n${res.nb_ignorees} déjà comptabilisée(s)`); await rafraichirCompta() }
    catch (e) { notifier.erreur(e.message) } finally { setGenDotations(false) }
  }

  async function payer(immo) {
    const d = prompt(`Date de paiement de ${immo.designation} (AAAA-MM-JJ)`, today())
    if (!d) return
    const compte = prompt('Compte de trésorerie', immo.compte_reglement || '5141')
    if (!compte) return
    try { await apiFetch(`/api/immobilisations/${immo.id}/payer`, { method: 'POST', body: JSON.stringify({ date_paiement: d, compte_reglement: compte }) }); await rafraichirCompta() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function encaisserCession(immo) {
    const d = prompt(`Date d’encaissement de la cession de ${immo.designation}`, today())
    if (!d) return
    const compte = prompt('Compte de trésorerie', '5141')
    if (!compte) return
    try { await apiFetch(`/api/immobilisations/${immo.id}/encaisser-cession`, { method: 'POST', body: JSON.stringify({ date_encaissement: d, compte_tresorerie: compte }) }); await rafraichirCompta() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function supprimer(immo) {
    if (!confirm(`Archiver ${immo.designation} ?`)) return
    try { await apiFetch(`/api/immobilisations/${immo.id}`, { method: 'DELETE' }); charger() } catch (e) { notifier.erreur(e.message) }
  }

  const actifs = immobilisations.filter(i => i.actif)
  const totalBrut = actifs.reduce((s, i) => s + n(i.valeur_brute), 0)
  const totalVnc = actifs.reduce((s, i) => s + n(i.vnc_actuelle), 0)
  const totalAmort = actifs.reduce((s, i) => s + n(i.cumul_amortissement), 0)

  return <div className={styles.page} data-form-page>
    <div className={styles.topbar}>
      <div><h2 className={styles.pageTitle}>Immobilisations</h2><div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Acquisitions, TVA, amortissements, cessions et mises au rebut</div></div>
      <div style={{ display: 'flex', gap: 8 }}><button className={styles.btnSec} onClick={() => setShowReconciliation(true)}><i className="ti ti-adjustments-check" /> Réconciliation historique</button><button className={styles.btnSec} onClick={genererDotationsAnnee} disabled={!ecriture || loading || Boolean(erreurChargement) || genDotations}><i className="ti ti-calculator" /> {genDotations ? 'Génération...' : `Dotations ${annee}`}</button><button className={styles.btnPrim} disabled={!ecriture || loading || Boolean(erreurChargement)} onClick={() => { setEditImmo(null); setShowForm(true) }}><i className="ti ti-plus" /> Nouvelle immobilisation</button></div>
    </div>
    <div className={styles.content}>
      {!ecriture && <p role="status">Consultation seule : le registre, les plans et le diagnostic restent accessibles sans modification.</p>}
      <div className={styles.kpiGrid}>
        {[
          ['Valeur brute active', totalBrut, 'ti-building-factory', 'var(--blue)'], ['Amortissements cumulés', totalAmort, 'ti-chart-down', '#854F0B'], ['VNC active', totalVnc, 'ti-chart-line', '#3B6D11'], ['Biens actifs', actifs.length, 'ti-list', '#534AB7'],
        ].map(([label, val, icon, color], idx) => <div key={label} className={styles.kpiCard}><div className={styles.kpiLabel}><i className={`ti ${icon}`} style={{ color }} /> {label}</div><div className={styles.kpiValeur} style={{ color }}>{loading || erreurChargement ? '—' : idx === 3 ? `${val} biens` : `${formatMAD(val)} MAD`}</div></div>)}
      </div>

      {aCreer.length > 0 && <div className={styles.card} aria-label="Achats d'immobilisations sans fiche">
        <div className={styles.cardHeader}><span className={styles.cardTitle}>Achats d'immobilisations sans fiche</span><span style={{ fontSize: 11 }}>Créez la fiche pour démarrer les amortissements</span></div>
        <div className={styles.tableWrapper}><table className={styles.table}><thead><tr><th>Facture</th><th>Date</th><th>Fournisseur</th><th>Désignation</th><th>Compte</th><th style={{ textAlign: 'right' }}>Montant HT</th><th /></tr></thead><tbody>
          {aCreer.map(x => <tr key={`${x.facture_id}-${x.ligne_id}`}><td>{x.facture}</td><td>{x.date}</td><td>{x.fournisseur}</td><td>{x.designation}</td><td>{x.compte}</td><td style={{ textAlign: 'right' }}>{formatMAD(x.montant_ht)}</td>
            <td>{ecriture && <button className={styles.btnSec} onClick={() => creerDepuisFacture(x)}>Créer la fiche</button>}</td></tr>)}
        </tbody></table></div></div>}

      <div className={styles.card}>
        <div className={styles.cardHeader}><span className={styles.cardTitle}><i className="ti ti-building-factory" style={{ marginRight: 6 }} />Registre des immobilisations</span><span style={{ fontSize: 11 }}>{loading ? 'Lecture en cours…' : erreurChargement ? 'Lecture indisponible' : `Valeurs théoriques au ${today().split('-').reverse().join('/')} · ${immobilisations.length} bien(s)`}</span></div>
        {loading ? <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" />Chargement...</div> : erreurChargement ? <div className={styles.vide} role="alert"><p>Impossible de charger le registre des immobilisations.</p><p>{erreurChargement}</p><button className={styles.btnSec} onClick={charger}>Réessayer le registre</button></div> : immobilisations.length === 0 ? <div className={styles.vide}><i className="ti ti-building-factory" />Aucune immobilisation</div> : <div className={styles.tableWrapper}>
          <table className={styles.table}><thead><tr><th>Désignation</th><th>Statut</th><th>Acquisition</th><th>Mise en service</th><th style={{ textAlign: 'right' }}>Valeur brute</th><th style={{ textAlign: 'right' }}>VNC</th><th>Amortissement</th><th>Paiement</th><th /></tr></thead>
          <tbody>{immobilisations.map((immo, i) => <React.Fragment key={immo.id}>
            <tr className={i % 2 === 0 ? styles.rowPair : ''} style={{ cursor: 'pointer', opacity: immo.actif ? 1 : 0.72 }} onClick={() => setImmoDetail(immoDetail?.id === immo.id ? null : immo)}>
              <td><div style={{ fontWeight: 600 }}>{immo.designation}</div><div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{immo.categorie}{immo.reference ? ` · ${immo.reference}` : ''}</div></td>
              <td><span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 20, background: immo.actif ? '#EAF3DE' : '#F1F1F1', color: immo.actif ? '#3B6D11' : '#666' }}>{immo.actif ? 'Actif' : immo.type_sortie === 'cession' ? 'Cédé' : immo.type_sortie === 'rebut' ? 'Rebut' : 'Archivé'}</span></td>
              <td style={{ fontSize: 11 }}>{immo.date_acquisition}<div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{formatMAD(immo.prix_acquisition_ht)} HT</div></td>
              <td style={{ fontSize: 11 }}>{immo.date_mise_en_service}</td>
              <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatMAD(immo.valeur_brute)} MAD</td>
              <td style={{ textAlign: 'right', fontWeight: 600, color: '#3B6D11' }}>{formatMAD(immo.vnc_actuelle)} MAD<div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{formatMAD(immo.cumul_amortissement)} amorti</div></td>
              <td style={{ fontSize: 11 }}>{!immo.amortissable ? 'Non amortissable' : `${immo.duree_amort} ans · ${immo.methode === 'degressif' ? 'Dégressif' : 'Linéaire'}`}</td>
              <td style={{ fontSize: 11 }}>{immo.date_paiement ? <span style={{ color: '#3B6D11' }}>Payé · {immo.date_paiement}</span> : <span style={{ color: '#854F0B' }}>À payer</span>}</td>
              <td><div style={{ display: 'flex', gap: 4 }}>
                {ecriture && immo.actif && !immo.date_paiement && immo.ecriture_acquisition_id && !String(immo.reference || '').startsWith('FA-') && <button className={styles.btnAction} title="Marquer l’acquisition payée" onClick={e => { e.stopPropagation(); payer(immo) }}><i className="ti ti-cash" /><span className="libelle-action" aria-hidden="true">Marquer l’acquisition payée</span></button>}
                {ecriture && immo.actif && <button className={styles.btnAction} title="Modifier" onClick={e => { e.stopPropagation(); setEditImmo(immo); setShowForm(true) }}><i className="ti ti-pencil" /><span className="libelle-action" aria-hidden="true">Modifier</span></button>}
                {ecriture && immo.actif && <button className={styles.btnAction} title="Cession / mise au rebut" onClick={e => { e.stopPropagation(); setSortieImmo(immo) }}><i className="ti ti-logout" /><span className="libelle-action" aria-hidden="true">Cession / mise au rebut</span></button>}
                {ecriture && !immo.actif && immo.type_sortie === 'cession' && !immo.date_encaissement_cession && <button className={styles.btnAction} title="Encaisser la cession" onClick={e => { e.stopPropagation(); encaisserCession(immo) }}><i className="ti ti-cash-banknote" /><span className="libelle-action" aria-hidden="true">Encaisser la cession</span></button>}
                {ecriture && immo.actif && !immo.ecriture_acquisition_id && <button className={styles.btnTrash} title="Archiver" onClick={e => { e.stopPropagation(); supprimer(immo) }}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Archiver</span></button>}
              </div></td>
            </tr>
            {immoDetail?.id === immo.id && <tr><td colSpan={9} style={{ background: '#F0F7FF', padding: 0 }}><div style={{ padding: '12px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><b style={{ fontSize: 12, color: 'var(--blue)' }}>Tableau d’amortissement — {immo.designation}</b><span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>TVA acquisition {formatMAD(immo.tva_acquisition)} · récupérable {formatMAD(immo.tva_recuperable)} MAD</span></div>
              <TableauAmortissement immo={immo} annee={annee} onGenerer={rafraichirCompta} />
            </div></td></tr>}
          </React.Fragment>)}</tbody></table>
        </div>}
      </div>
    </div>
    {ecriture && showForm && <FormulaireImmo initial={editImmo} onFermer={() => { setShowForm(false); setEditImmo(null) }} onSuccess={() => { setShowForm(false); setEditImmo(null); rafraichirCompta() }} />}
    {ecriture && sortieImmo && <FormulaireSortie immo={sortieImmo} onFermer={() => setSortieImmo(null)} onSuccess={() => { setSortieImmo(null); rafraichirCompta() }} />}
    {showReconciliation && <ReconciliationHistorique annee={annee} onFermer={() => setShowReconciliation(false)} onSuccess={rafraichirCompta} />}
  </div>
}
