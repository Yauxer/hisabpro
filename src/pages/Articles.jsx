import { useState, useEffect, useMemo, useRef } from 'react'
import { formatMAD } from '../data/donnees.js'
import { rechercherCompte, PLAN_COMPTES } from '../data/planComptes.js'
import Modal from '../components/Modal.jsx'
import { FormSection, AdvancedSection, InlineNotice, ActionBar } from '../components/FormUX.jsx'
import styles from './Articles.module.css'
import { API_BASE } from '../services/api.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { tauxTVAAvecHistorique } from '../utils/tvaUtils.js'
import { nombreArticleConnu, nombreArticleSaisie, nombreSaisieConnu, montantArticle, margeArticle } from '../utils/articlesNombres.js'

const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE

const UNITES     = ['unité', 'kg', 'g', 'tonne', 'm', 'm²', 'm³', 'litre', 'heure', 'jour', 'forfait']
const stockConnu = article => Number.isFinite(article?.stock_actuel) && article.stock_actuel >= 0

// Autocomplete sur le plan comptable CGNC, filtré par classe (ex: '7' pour les ventes).
// Le dropdown est rendu en position fixed pour ne pas être coupé par l'overflow des modales.
function ChampCompte({ value, onChange, classe, placeholder }) {
  const [suggestions, setSuggestions] = useState([])
  const [ouvert, setOuvert] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0, versLeHaut: false })
  const inputRef = useRef(null)

  function filtrer(val) {
    if (val && val.trim()) {
      return rechercherCompte(val).filter(c => !classe || [].concat(classe).some(k => c.compte.startsWith(k)))
    }
    // Champ vide : proposer les comptes de la classe (les plus génériques d'abord)
    return PLAN_COMPTES
      .filter(c => !classe || [].concat(classe).some(k => c.compte.startsWith(k)))
      .sort((a, b) => a.compte.length - b.compte.length || a.compte.localeCompare(b.compte))
      .slice(0, 15)
  }

  function ouvrir(val) {
    const res = filtrer(val)
    setSuggestions(res)
    if (res.length === 0) { setOuvert(false); return }
    const rect = inputRef.current?.getBoundingClientRect()
    if (rect) {
      const hauteurListe = Math.min(res.length * 32 + 8, 220)
      const versLeHaut = rect.bottom + hauteurListe > window.innerHeight - 12
      setPos({
        top: versLeHaut ? rect.top - hauteurListe - 4 : rect.bottom + 4,
        left: rect.left,
        width: rect.width,
        versLeHaut,
      })
    }
    setOuvert(true)
  }

  function handleChange(val) {
    onChange(val)
    ouvrir(val)
  }

  return (
    <div style={{ position: 'relative' }}>
      <input ref={inputRef} className={styles.input} type="text" placeholder={placeholder}
        value={value}
        onChange={e => handleChange(e.target.value)}
        onFocus={() => ouvrir(value)}
        onBlur={() => setTimeout(() => setOuvert(false), 180)} />
      {ouvert && (
        <div style={{
          position: 'fixed', top: pos.top, left: pos.left, width: pos.width, zIndex: 9999,
          background: 'var(--bg-primary)', border: '0.5px solid var(--border-medium)',
          borderRadius: 6, boxShadow: '0 6px 20px rgba(0,0,0,0.15)', maxHeight: 220, overflowY: 'auto',
        }}>
          {suggestions.map(c => (
            <div key={c.compte}
              onMouseDown={() => { onChange(c.compte); setOuvert(false) }}
              style={{ padding: '6px 10px', fontSize: 12, cursor: 'pointer', display: 'flex', gap: 8, alignItems: 'center' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-secondary)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}>
              <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--blue)', flexShrink: 0 }}>{c.compte}</span>
              <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.libelle}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Erreur' }))
    throw new Error(err.detail)
  }
  if (res.status === 204) return null
  return res.json()
}

// ─── Formulaire article ───────────────────────────────────────────────────────
function FormulaireArticle({ article, familles, annee, onFermer, onSuccess }) {
  const [form, setForm] = useState({
    code:            article?.code            || '',
    designation:     article?.designation     || '',
    description:     article?.description     || '',
    famille_id:      article?.famille_id      || '',
    prix_vente_ht:   article ? nombreArticleSaisie(article.prix_vente_ht) : 0,
    prix_achat_ht:   article ? nombreArticleSaisie(article.prix_achat_ht) : 0,
    frais_emballage: article ? nombreArticleSaisie(article.frais_emballage) : 0,
    frais_transport: article ? nombreArticleSaisie(article.frais_transport) : 0,
    tva:             article ? nombreArticleSaisie(article.tva) : 20,
    unite:           article?.unite           || 'unité',
    code_barre:      article?.code_barre      || '',
    stock_actuel:    article?.id ? (stockConnu(article) ? article.stock_actuel : '') : 0,
    stock_min:       article ? nombreArticleSaisie(article.stock_min) : 0,
    emplacement:     article?.emplacement     || '',
    is_stockable:    article?.is_stockable    ?? true,
    compte_vente:    article?.compte_vente    || '',
    compte_achat:    article?.compte_achat    || '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')
  const champsNumeriques = useRef({})
  const nombresModifies = useRef(new Set())
  function saisirNombre(cle, valeur) {
    nombresModifies.current.add(cle)
    setForm(p => ({ ...p, [cle]: valeur }))
  }
  const famille = familles.find(f => f.id === parseInt(form.famille_id))
  const prixTTCIndicatif = nombreSaisieConnu(form.prix_vente_ht) && nombreSaisieConnu(form.tva) ? Number(form.prix_vente_ht) * (1 + Number(form.tva) / 100) : null
  const margeIndicative = nombreSaisieConnu(form.prix_vente_ht) && nombreSaisieConnu(form.prix_achat_ht) ? Number(form.prix_vente_ht) - Number(form.prix_achat_ht) : null

  // Quand on choisit une famille → reprend son taux TVA par défaut
  function handleFamille(id) {
    const f = familles.find(f => f.id === parseInt(id))
    if (f) nombresModifies.current.add('tva')
    setErreur('')
    setForm(p => ({ ...p, famille_id: id, tva: f ? nombreArticleSaisie(f.tva_defaut) : p.tva }))
  }

  async function handleSave() {
    if (!form.code.trim())        { setErreur('Le code article est obligatoire'); return }
    if (!form.designation.trim()) { setErreur('La désignation est obligatoire'); return }
    const valeurs = {}
    const aVerifier = [
      ['prix_vente_ht', 'Le prix de vente', 0], ['prix_achat_ht', 'Le prix d’achat', 0],
      ['frais_emballage', 'Le montant des frais d’emballage', 0], ['frais_transport', 'Le montant des frais de transport', 0],
      ['tva', 'Le taux de TVA', 20],
      ...(form.is_stockable ? [['stock_min', 'Le stock minimum', 0]] : []),
      ...(form.is_stockable && !article?.id ? [['stock_actuel', 'Le stock initial', 0]] : []),
    ]
    for (const [cle, libelle, defaut] of aVerifier) {
      if (cle === 'tva' && form.tva === '' && (!article?.id || nombresModifies.current.has('tva'))) {
        setErreur('Le taux de TVA est inconnu : renseignez une valeur explicite avant d’enregistrer.'); return
      }
      // Un champ historique inconnu et laissé vide reste absent du PATCH.
      if (article?.id && form[cle] === '' && !nombreArticleConnu(article[cle]) && !champsNumeriques.current[cle]?.validity.badInput) {
        if (!nombresModifies.current.has(cle)) continue
        setErreur(`${libelle} est inconnu : renseignez une valeur explicite ou annulez cette modification.`); return
      }
      const valeur = form[cle] === '' ? defaut : Number(form[cle])
      if (champsNumeriques.current[cle]?.validity.badInput || !Number.isFinite(valeur)) {
        setErreur(`${libelle} doit être un nombre fini valide.`); return
      }
      if (valeur < 0) { setErreur(`${libelle} ne peut pas être négatif.`); return }
      valeurs[cle] = valeur
    }
    const prixVente = valeurs.prix_vente_ht
    const prixAchat = valeurs.prix_achat_ht
    const tva = valeurs.tva
    const stockInitial = form.is_stockable && !article?.id ? valeurs.stock_actuel : 0
    const stockMin = form.is_stockable ? valeurs.stock_min : 0
    if (tva < 0 || tva > 100) { setErreur('Le taux de TVA doit être compris entre 0 et 100 %.'); return }
    if (article?.id && article.is_stockable !== false && !form.is_stockable && (!stockConnu(article) || article.stock_actuel !== 0)) {
      setErreur(stockConnu(article) ? 'Ramenez d’abord le stock à 0 via un ajustement de stock avant de convertir cet article en service.' : 'Stock historique inconnu : vérifiez la source avant de convertir cet article en service.')
      return
    }
    setLoading(true); setErreur('')
    try {
      const payload = {
        famille_id:    form.famille_id ? parseInt(form.famille_id) : null,
        designation:   form.designation.trim(),
        description:   form.description?.trim() || null,
        prix_vente_ht: prixVente,
        prix_achat_ht: prixAchat,
        frais_emballage: valeurs.frais_emballage,
        frais_transport: valeurs.frais_transport,
        tva,
        unite:         form.unite,
        stock_min:     stockMin,
        code_barre:    form.code_barre?.trim() || null,
        emplacement:   form.is_stockable ? (form.emplacement?.trim() || null) : null,
        is_stockable:  form.is_stockable,
        compte_vente:  form.compte_vente?.trim() || null,
        compte_achat:  form.compte_achat?.trim() || null,
      }
      if (article?.id) {
        for (const cle of Object.keys(payload)) {
          const ancienne = article[cle] === '' ? null : (article[cle] ?? null)
          if (payload[cle] === undefined || payload[cle] === ancienne || (Object.hasOwn(article.nombres_diagnostics || {}, cle) && !nombresModifies.current.has(cle))) delete payload[cle]
        }
        await apiFetch(`/api/articles/${article.id}`, { method: 'PATCH', body: JSON.stringify(payload) })
      } else {
        await apiFetch('/api/articles', {
          method: 'POST',
          body: JSON.stringify({ ...payload, code: form.code.trim(), stock_actuel: stockInitial }),
        })
      }
      onSuccess()
      onFermer()
    } catch (e) {
      setErreur(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal titre={article ? 'Modifier l\'article' : 'Nouvel article'} icone="ti-package" onFermer={onFermer} largeur="md">
      <div className="hp-form-stack">
        {article && Object.keys(article.nombres_diagnostics || {}).length > 0 && <InlineNotice tone="warning" title="Valeurs historiques à vérifier">Les champs numériques inconnus restent vides et sont conservés tant que vous ne renseignez pas une valeur explicite. {Object.values(article.nombres_diagnostics).join(' ')}</InlineNotice>}
        <FormSection icon="ti-tag" title="Informations générales"
          description="Identifiez l'article ou le service tel qu'il apparaîtra dans les documents.">
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field">
              <label>Code <span className="hp-required">*</span></label>
              <input className={styles.input} type="text" placeholder="ART-001"
                value={form.code} readOnly={Boolean(article?.id)}
                title={article?.id ? 'Le code article est figé après création' : undefined}
                onChange={e => setForm(p => ({ ...p, code: e.target.value.toUpperCase() }))} />
              {article?.id && <span className="hp-field__hint">Code figé après création.</span>}
            </div>
            <div className="hp-field">
              <label>Famille</label>
              <select className={styles.input} value={form.famille_id} onChange={e => handleFamille(e.target.value)}>
                <option value="">— Sans famille —</option>
                {familles.map(f => <option key={f.id} value={f.id}>{f.libelle}</option>)}
              </select>
            </div>
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Désignation <span className="hp-required">*</span></label>
              <input className={styles.input} type="text" placeholder="Nom de l'article ou service"
                value={form.designation} onChange={e => setForm(p => ({ ...p, designation: e.target.value }))} />
            </div>
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Description</label>
              <textarea className={styles.textarea} rows={2} placeholder="Description détaillée (optionnel)"
                value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
            </div>
          </div>
        </FormSection>

        <FormSection icon="ti-currency-dirham" title="Prix & fiscalité"
          description="Ces valeurs seront proposées automatiquement sur les factures, devis et commandes.">
          <div className="hp-form-grid hp-form-grid--4">
            <div className="hp-field"><label>Prix vente HT</label><input ref={el => { champsNumeriques.current.prix_vente_ht = el }} className={styles.input} type="number" min="0" step="0.01" value={form.prix_vente_ht} onChange={e => saisirNombre('prix_vente_ht', e.target.value)} /></div>
            <div className="hp-field"><label>Prix achat HT</label><input ref={el => { champsNumeriques.current.prix_achat_ht = el }} className={styles.input} type="number" min="0" step="0.01" value={form.prix_achat_ht} onChange={e => saisirNombre('prix_achat_ht', e.target.value)} /></div>
            <div className="hp-field"><label>TVA proposée</label><select className={styles.input} value={form.tva} onChange={e => saisirNombre('tva', e.target.value)}><option value="">À vérifier</option>{tauxTVAAvecHistorique(`${annee}-01-01`, form.tva).map(t => <option key={t} value={t}>{t}%</option>)}</select>{famille && !nombreArticleConnu(famille.tva_defaut) && <span className="hp-field__hint">La TVA de cette famille est inconnue. Choisissez une valeur explicite pour cet article ; la famille historique reste inchangée.</span>}{nombreSaisieConnu(form.tva) && Number(form.tva) === 0 && <span className="hp-field__hint">Le motif du 0 % (exonération, hors champ, suspension…) sera précisé sur la pièce.</span>}</div>
            <div className="hp-field"><label>Unité</label><select className={styles.input} value={form.unite} onChange={e => setForm(p => ({ ...p, unite: e.target.value }))}>{UNITES.map(u => <option key={u} value={u}>{u}</option>)}</select></div>
          </div>
          {Number(form.prix_vente_ht) > 0 && Number.isFinite(prixTTCIndicatif) && (
            <div className="hp-summary" style={{ marginTop: 12 }}>
              <div className="hp-summary__row"><span>Prix de vente TTC</span><strong>{formatMAD(prixTTCIndicatif)} MAD</strong></div>
              {Number(form.prix_achat_ht) > 0 && Number.isFinite(margeIndicative) && <div className="hp-summary__row"><span>Marge brute indicative</span><strong>{formatMAD(margeIndicative)} MAD</strong></div>}
            </div>
          )}
        </FormSection>

        <FormSection icon="ti-truck" title="Emballage & transport"
          description="Montants HT par unité, à reporter dans les frais du document selon la quantité.">
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field"><label>Emballage HT par unité</label><input ref={el => { champsNumeriques.current.frais_emballage = el }} className={styles.input} type="number" min="0" step="0.01" value={form.frais_emballage} onChange={e => saisirNombre('frais_emballage', e.target.value)} /><span className="hp-field__hint">Facultatif.</span></div>
            <div className="hp-field"><label>Transport HT par unité</label><input ref={el => { champsNumeriques.current.frais_transport = el }} className={styles.input} type="number" min="0" step="0.01" value={form.frais_transport} onChange={e => saisirNombre('frais_transport', e.target.value)} /><span className="hp-field__hint">Facultatif.</span></div>
          </div>
        </FormSection>

        <FormSection icon={form.is_stockable ? 'ti-box' : 'ti-briefcase'} title="Nature & stock"
          description={form.is_stockable ? 'Le stock sera suivi automatiquement à partir des mouvements.' : 'Les services et frais ne génèrent aucun mouvement de stock.'}>
          <div className="hp-choice-cards" style={{ gridTemplateColumns: 'repeat(2,minmax(0,1fr))', marginBottom: 12 }}>
            <button type="button" className={`hp-choice-card ${form.is_stockable ? 'is-active' : ''}`} onClick={() => setForm(p => ({ ...p, is_stockable: true }))}><i className="ti ti-box" /> Article stockable</button>
            <button type="button" className={`hp-choice-card ${!form.is_stockable ? 'is-active' : ''}`} onClick={() => setForm(p => ({ ...p, is_stockable: false }))}><i className="ti ti-briefcase" /> Service / frais</button>
          </div>
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field"><label>Code-barres</label><input className={styles.input} type="text" placeholder="EAN13 ou référence..." value={form.code_barre} onChange={e => setForm(p => ({ ...p, code_barre: e.target.value }))} /></div>
            {form.is_stockable && <div className="hp-field"><label>Emplacement</label><input className={styles.input} type="text" placeholder="Magasin central, Entrepôt..." value={form.emplacement} onChange={e => setForm(p => ({ ...p, emplacement: e.target.value }))} /></div>}
            {form.is_stockable && <div className="hp-field"><label>{article?.id ? 'Stock actuel' : 'Stock initial'}</label><input ref={el => { champsNumeriques.current.stock_actuel = el }} className={styles.input} type="number" min="0" step="0.01" value={form.stock_actuel} placeholder={article?.id && !stockConnu(article) ? 'À vérifier' : undefined} onChange={e => !article?.id && setForm(p => ({ ...p, stock_actuel: e.target.value }))} readOnly={Boolean(article?.id)} /><span className="hp-field__hint">{article?.id && !stockConnu(article) ? (article.stock_diagnostic || 'Stock historique inconnu : à vérifier.') : article?.id ? 'Lecture seule : corrigez le stock via un mouvement traçable.' : 'Créera un mouvement d’ouverture.'}</span></div>}
            {form.is_stockable && <div className="hp-field"><label>Stock minimum</label><input ref={el => { champsNumeriques.current.stock_min = el }} className={styles.input} type="number" min="0" step="0.01" placeholder="0 = pas d'alerte" value={form.stock_min} onChange={e => saisirNombre('stock_min', e.target.value)} /><span className="hp-field__hint">Seuil d’alerte de réapprovisionnement.</span></div>}
          </div>
        </FormSection>

        <AdvancedSection title="Comptes comptables" icon="ti-book-2">
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field"><label>Compte de vente</label><ChampCompte classe="7" value={form.compte_vente} placeholder={famille?.compte_vente || '7111 (défaut famille)'} onChange={v => setForm(p => ({ ...p, compte_vente: v }))} /><span className="hp-field__hint">Vide = compte de la famille.</span></div>
            <div className="hp-field"><label>Compte d'achat (charge 6xxx ou immobilisation 2xxx)</label><ChampCompte classe={['6', '2']} value={form.compte_achat} placeholder={famille?.compte_achat || '6111 (défaut famille)'} onChange={v => setForm(p => ({ ...p, compte_achat: v }))} /><span className="hp-field__hint">Vide = compte de la famille.</span></div>
          </div>
        </AdvancedSection>

        {erreur && <InlineNotice tone="danger">{erreur}</InlineNotice>}
        <ActionBar hint={article ? 'Le code est conservé pour préserver la traçabilité.' : 'Les champs obligatoires suffisent pour créer rapidement une fiche.'}>
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={handleSave} disabled={!form.code.trim() || !form.designation.trim() || loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : (article ? 'Enregistrer les modifications' : 'Créer l’article')}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )

}

// ─── Formulaire famille ───────────────────────────────────────────────────────
function FormulaireFamille({ onFermer, onSuccess }) {
  // Une famille n'est qu'un regroupement : seul son nom est saisi.
  // Le code est dérivé du nom, les valeurs comptables prennent les défauts
  // (elles restent modifiables article par article).
  const [nom, setNom] = useState('')
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')

  async function handleSave() {
    if (!nom.trim()) return
    setLoading(true); setErreur('')
    try {
      // Code technique dérivé du nom : "Mobilier de bureau" → "MOBILIERDEB"
      const code = nom.trim().toUpperCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^A-Z0-9]/g, '').slice(0, 11) || 'FAM'
      await apiFetch('/api/familles', {
        method: 'POST',
        body: JSON.stringify({
          code, libelle: nom.trim(),
          tva_defaut: 20, compte_vente: '7111', compte_achat: '6111',
        }),
      })
      onSuccess(); onFermer()
    } catch (e) {
      setErreur(e.message)
    } finally { setLoading(false) }
  }

  return (
    <Modal titre="Nouvelle famille" icone="ti-folder" onFermer={onFermer} largeur="sm">
      <div className={styles.formContenu}>
        <div className={styles.formGroup}>
          <label className={styles.label}>Nom de la famille *</label>
          <input className={styles.input} type="text" placeholder="Mobilier de bureau"
            autoFocus value={nom}
            onChange={e => setNom(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && nom.trim()) handleSave() }} />
          <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 4 }}>
            Sert à regrouper les articles. Les comptes et la TVA se règlent sur chaque article.
          </span>
        </div>
        {erreur && <div className={styles.erreur}>{erreur}</div>}
        <div className={styles.formActions}>
          <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
          <button className={styles.btnPrim} onClick={handleSave}
            disabled={!nom.trim() || loading}>
            {loading ? '...' : 'Créer'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Page principale Articles ─────────────────────────────────────────────────
export default function Articles() {
  const [articles,   setArticles]   = useState([])
  const [familles,   setFamilles]   = useState([])
  const [recherche,  setRecherche]  = useState('')
  const [filtreF,    setFiltreF]    = useState('')
  const [ventes, setVentes] = useState({})   // { designation → { qte, ca } }
  const [ventesPartielles, setVentesPartielles] = useState(false)
  const [tri, setTri] = useState('ventes')   // ventes | nom | stock | marge
  const { annee } = useExercice()
  const [showForm,   setShowForm]   = useState(false)
  const [showFamF,   setShowFamF]   = useState(false)
  const [selected,   setSelected]   = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [erreurSuppression, setErreurSuppression] = useState('')

  async function charger() {
    setLoading(true)
    try {
      const [arts, fams] = await Promise.all([
        apiFetch('/api/articles'),
        apiFetch('/api/familles'),
      ])
      setArticles(arts)
      setFamilles(fams)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [])

  // Quantités vendues sur l'exercice, pour mettre les articles qui tournent en tête
  useEffect(() => {
    let annule = false
    fetch(`${API_BASE}/api/factures?exercice=${annee}&limit=2000`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('hisabpro_token')}` },
    })
      .then(r => r.ok ? r.json() : [])
      .then(fs => {
        if (annule) return
        const m = {}
        ;(fs || []).forEach(f => {
          if (f.type !== 'vente' || f.est_proforma) return
          ;(f.lignes || []).forEach(l => {
            const cle = (l.description || '').trim().toLowerCase()
            if (!cle) return
            if (!m[cle]) m[cle] = { qte: 0, ca: 0 }
            m[cle].qte += l.quantite || 0
            m[cle].ca  += (l.quantite || 0) * (l.prix_unitaire || 0)
          })
        })
        setVentes(m)
        // Statistiques de vente calculées sur un maximum de 2 000 factures :
        // au-delà, le classement peut être incomplet.
        setVentesPartielles((fs || []).length >= 2000)
      })
      .catch(() => { if (!annule) setVentes({}) })
    return () => { annule = true }
  }, [annee])

  async function supprimer(id) {
    if (!confirm('Supprimer cet article ?')) return
    setErreurSuppression('')
    try {
      await apiFetch(`/api/articles/${id}`, { method: 'DELETE' })
      setArticles(prev => prev.filter(a => a.id !== id))
    } catch (e) { setErreurSuppression(e.message || 'La suppression a échoué.') }
  }

  const vd = a => ventes[(a.designation || '').trim().toLowerCase()] || { qte: 0, ca: 0 }

  const articlesFiltres = useMemo(() => {
    const liste = articles.filter(a => {
      const ok = !recherche || a.designation.toLowerCase().includes(recherche.toLowerCase()) ||
                 a.code.toLowerCase().includes(recherche.toLowerCase())
      const okF = !filtreF || a.famille_id === parseInt(filtreF)
      return ok && okF
    })
    const parNom = (a, b) => (a.designation || '').localeCompare(b.designation || '', 'fr')
    if (tri === 'nom')   return [...liste].sort(parNom)
    if (tri === 'stock') return [...liste].sort((a, b) => {
      const connuA = a.is_stockable !== false && stockConnu(a)
      const connuB = b.is_stockable !== false && stockConnu(b)
      if (connuA !== connuB) return connuA ? -1 : 1
      return connuA ? a.stock_actuel - b.stock_actuel || parNom(a, b) : parNom(a, b)
    })
    if (tri === 'marge') return [...liste].sort((a, b) => {
      const ma = margeArticle(a), mb = margeArticle(b)
      return ma === null ? (mb === null ? 0 : 1) : mb === null ? -1 : mb - ma
    })
    // Défaut : les plus vendus d'abord (à volume égal, ordre alphabétique)
    return [...liste].sort((a, b) => vd(b).qte - vd(a).qte || parNom(a, b))
  }, [articles, recherche, filtreF, tri, ventes])

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Articles & Services</h1>
        <div className={styles.topbarRight}>
          <button className={styles.btnSec} onClick={() => setShowFamF(true)}>
            <i className="ti ti-folder-plus" /> Nouvelle famille
          </button>
          <button className={styles.btnPrim} onClick={() => { setSelected(null); setShowForm(true) }}>
            <i className="ti ti-plus" /> Nouvel article
          </button>
        </div>
      </div>

      {showForm && (
        <FormulaireArticle
          article={selected}
          familles={familles}
          annee={annee}
          onFermer={() => { setShowForm(false); setSelected(null) }}
          onSuccess={charger}
        />
      )}
      {showFamF && (
        <FormulaireFamille
          onFermer={() => setShowFamF(false)}
          onSuccess={charger}
        />
      )}

      <div className={styles.content}>
        {erreurSuppression && <div role="alert" className={styles.erreur}>{erreurSuppression}</div>}
        {/* Familles en badges */}
        {familles.length > 0 && (
          <div className={styles.familles}>
            <button className={`${styles.familleBtn} ${!filtreF ? styles.familleBtnActif : ''}`}
              onClick={() => setFiltreF('')}>
              Tous ({articles.length})
            </button>
            {familles.map(f => (
              <button key={f.id}
                className={`${styles.familleBtn} ${filtreF == f.id ? styles.familleBtnActif : ''}`}
                onClick={() => setFiltreF(filtreF == f.id ? '' : f.id)}>
                {f.libelle}
              </button>
            ))}
          </div>
        )}

        {/* Recherche + tri */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <div className={styles.recherche} style={{ flex: 1, minWidth: 200 }}>
            <i className="ti ti-search" />
            <input type="text" placeholder="Rechercher un article..."
              value={recherche} onChange={e => setRecherche(e.target.value)} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Trier par</span>
            {ventesPartielles && tri === 'ventes' && (
              <span title="Plus de 2 000 factures sur l'exercice : le classement porte sur les 2 000 premières"
                style={{ fontSize: 10.5, color: '#8A5A0B', background: '#FDF3E3',
                  padding: '2px 7px', borderRadius: 20 }}>
                <i className="ti ti-alert-triangle" style={{ marginRight: 3 }} />partiel
              </span>
            )}
            {[
              { val: 'ventes', label: 'Les plus vendus' },
              { val: 'nom',    label: 'Nom' },
              { val: 'stock',  label: 'Stock faible' },
              { val: 'marge',  label: 'Marge' },
            ].map(t => (
              <button key={t.val}
                className={`${styles.familleBtn} ${tri === t.val ? styles.familleBtnActif : ''}`}
                onClick={() => setTri(t.val)}
                title={t.val === 'ventes' ? `Volumes vendus sur l'exercice ${annee}` : undefined}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className={styles.card}>
          {loading ? (
            <div className={styles.vide}><i className="ti ti-loader-2 ti-spin" /> Chargement...</div>
          ) : articlesFiltres.length === 0 ? (
            <div className={styles.vide}>
              <i className="ti ti-package-off" />
              <span>{articles.length === 0 ? 'Aucun article — créez votre premier catalogue !' : 'Aucun résultat'}</span>
            </div>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Désignation</th>
                  <th>Famille</th>
                  <th style={{ textAlign: 'right' }}>P.V. HT</th>
                  <th style={{ textAlign: 'right' }}>P.A. HT</th>
                  <th style={{ textAlign: 'right' }}>TVA</th>
                  <th style={{ textAlign: 'right' }}>Stock</th>
                  <th style={{ textAlign: 'right' }}>Vendus</th>
                  <th style={{ textAlign: 'right' }}>Valeur stock</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {articlesFiltres.map(a => (
                  <tr key={a.id} onClick={() => { setSelected(a); setShowForm(true) }}
                    style={{ cursor: 'pointer' }}>
                    <td><span className={styles.code}>{a.code}</span></td>
                    <td><strong>{a.designation}</strong>
                      {a.description && <div className={styles.desc}>{a.description}</div>}
                    </td>
                    <td>
                      {a.famille ? (
                        <span className={styles.familleTag}>{a.famille.libelle}</span>
                      ) : <span className={styles.sansFamille}>—</span>}
                    </td>
                    <td style={{ textAlign: 'right' }} title={a.nombres_diagnostics?.prix_vente_ht}>{montantArticle(a.prix_vente_ht, formatMAD)}</td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }} title={a.nombres_diagnostics?.prix_achat_ht}>{montantArticle(a.prix_achat_ht, formatMAD)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <span className={styles.tvaBadge} title={a.nombres_diagnostics?.tva}>{nombreArticleConnu(a.tva) ? `${a.tva}%` : 'À vérifier'}</span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {a.is_stockable === false ? (
                        <span style={{ fontSize: 10, color: '#534AB7', background: '#EEEDFE', padding: '2px 6px', borderRadius: 4 }}>
                          Non stockable
                        </span>
                      ) : !stockConnu(a) ? (
                        <span title={a.stock_diagnostic || 'Vérifier la source historique.'} style={{ fontSize: 11, color: 'var(--amber)' }}>Stock inconnu</span>
                      ) : (
                        <>
                          <span style={{
                            fontWeight: 600,
                            color: a.stock_actuel <= 0 ? 'var(--red)' : a.stock_actuel < 5 ? 'var(--amber)' : 'var(--green)',
                            fontSize: 13,
                          }}>
                            {a.stock_actuel}
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 3 }}>{a.unite}</span>
                          {a.stock_actuel <= 0 ? (
                            <div style={{ fontSize: 10, color: 'var(--red)', fontWeight: 600 }}>Rupture</div>
                          ) : (a.stock_min > 0 && a.stock_actuel <= a.stock_min) && (
                            <div style={{ fontSize: 10, color: '#C9A227', fontWeight: 500 }}
                              title={`Seuil de réapprovisionnement : ${a.stock_min}`}>
                              À réapprovisionner
                            </div>
                          )}
                        </>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {vd(a).qte > 0 ? (
                        <>
                          <span style={{ fontWeight: 600, fontSize: 12.5 }}>{vd(a).qte}</span>
                          <div style={{ fontSize: 10.5, color: 'var(--text-tertiary)' }}>
                            {formatMAD(vd(a).ca)} MAD
                          </div>
                        </>
                      ) : <span style={{ opacity: 0.35 }}>—</span>}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {a.is_stockable !== false && (!stockConnu(a) || !nombreArticleConnu(a.cmup) || !Number.isFinite(a.stock_actuel * a.cmup)) ? (
                        <span title="Valeur de stock indéterminable : quantité ou coût historique à vérifier" style={{ fontSize: 11, color: 'var(--amber)' }}>À vérifier</span>
                      ) : (a.cmup || 0) > 0 && (a.stock_actuel || 0) !== 0 ? (
                        <>
                          <span style={{ fontWeight: 600, fontSize: 12.5 }}>
                            {formatMAD((a.stock_actuel || 0) * (a.cmup || 0))}
                          </span>
                          <div style={{ fontSize: 10.5, color: 'var(--text-tertiary)' }}>
                            coût moyen {formatMAD(a.cmup)}
                          </div>
                        </>
                      ) : <span style={{ opacity: 0.35 }}>—</span>}
                    </td>
                    <td>
                      <button className={styles.btnSuppr}
                        onClick={e => { e.stopPropagation(); supprimer(a.id) }}>
                        <i className="ti ti-trash" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
