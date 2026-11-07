import { useState, useEffect, useMemo } from 'react'
import { tiersAPI, facturesAPI, API_BASE, getToken } from '../services/api.js'
import { collecterPages } from '../utils/collecterPages.js'
import { chargerSoldes, joursDepuis, resumerActivite, correspondDelaiPaiement } from '../utils/tiersActivite.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import Modal from '../components/Modal.jsx'
import { FormSection, AdvancedSection, InlineNotice, ActionBar } from '../components/FormUX.jsx'
import styles from './Tiers.module.css'
import { emailValide, entierOuDefaut, iceValide, ifValide, nombreOuDefaut, normaliserIceSaisie, normaliserIfSaisie } from '../utils/formUtils.js'

// Filtres d'activité commerciale, calculés sur les factures de l'exercice
const ACTIVITES = [
  { val: 'TOUS',     label: 'Toute activité' },
  { val: 'recent',   label: 'Actifs (< 30 j)' },
  { val: 'dormant',  label: 'Sans mouvement (> 90 j)' },
  { val: 'frequent', label: 'Réguliers (3 factures et +)' },
  { val: 'impaye',   label: 'Avec impayés' },
]

const DELAIS = [
  ['TOUS', 'Tous les délais'], ['comptant', 'Comptant (0 jour)'],
  ['1_30', '1–30 jours'], ['31_60', '31–60 jours'],
  ['plus_60', 'Plus de 60 jours'], ['a_verifier', 'À vérifier'],
]

const TYPES = [
  { val: 'TOUS',        label: 'Tous'                },
  { val: 'client',      label: 'Clients'             },
  { val: 'fournisseur', label: 'Fournisseurs'        },
  { val: 'les_deux',    label: 'Clients & Fournis.'  },
]

function BadgeType({ type }) {
  const config = {
    client:      { label: 'Client',      bg: '#E6F1FB', color: '#185FA5' },
    fournisseur: { label: 'Fournisseur', bg: '#EEEDFE', color: '#534AB7' },
    les_deux:    { label: 'Les deux',    bg: '#EAF3DE', color: '#3B6D11' },
  }
  const c = config[type] || config.client
  return <span className={styles.badge} style={{ background: c.bg, color: c.color }}>{c.label}</span>
}

// ─── Formulaire tiers ─────────────────────────────────────────────────────────
function FormulaireTiers({ tiers, onFermer, onSave }) {
  const [form, setForm] = useState(tiers || {
    type: 'client', nom: '', ice: '', identifiant_fiscal: '',
    rc: '', adresse: '', ville: '', telephone: '', email: '', categorie_fiscale: 'professionnel',
    compte_client: '3421', compte_fournisseur: '4411',
    assujetti_tva: true, taux_ras: '', delai_paiement: 60, plafond_credit: 0,
  })
  const [loading, setLoading] = useState(false)
  const [erreur,  setErreur]  = useState('')
  const [fieldErrors, setFieldErrors] = useState({})

  function maj(champ, val) {
    setForm(p => ({ ...p, [champ]: val }))
    setFieldErrors(p => ({ ...p, [champ]: '' }))
  }

  function validerForm() {
    const e = {}
    if (!form.nom?.trim()) e.nom = 'Le nom / raison sociale est obligatoire.'
    if (!iceValide(form.ice)) e.ice = 'L’ICE doit contenir exactement 15 chiffres.'
    if (!ifValide(form.identifiant_fiscal)) e.identifiant_fiscal = 'L’IF doit être numérique.'
    if (!emailValide(form.email)) e.email = 'Adresse email invalide.'
    const delai = entierOuDefaut(form.delai_paiement, 60)
    if (delai < 0) e.delai_paiement = 'Le délai ne peut pas être négatif.'
    const plafond = nombreOuDefaut(form.plafond_credit, 0)
    if (plafond < 0) e.plafond_credit = 'Le plafond ne peut pas être négatif.'
    if (form.taux_ras !== '' && form.taux_ras !== null && form.taux_ras !== undefined) {
      const taux = nombreOuDefaut(form.taux_ras, -1)
      if (taux < 0 || taux > 100) e.taux_ras = 'Le taux doit être compris entre 0 et 100 %.'
    }
    setFieldErrors(e)
    return Object.keys(e).length === 0
  }

  async function handleSave() {
    if (!validerForm()) { setErreur('Vérifiez les champs signalés.'); return }
    setLoading(true)
    setErreur('')
    try {
      const data = {
        ...form,
        nom:            form.nom.trim(),
        ice:            normaliserIceSaisie(form.ice) || null,
        identifiant_fiscal: normaliserIfSaisie(form.identifiant_fiscal) || null,
        email:          form.email?.trim() || null,
        taux_ras:       form.taux_ras === '' || form.taux_ras === null ? null : nombreOuDefaut(form.taux_ras, 0),
        delai_paiement: entierOuDefaut(form.delai_paiement, 60),
        plafond_credit: nombreOuDefaut(form.plafond_credit, 0),
      }
      if (tiers?.id) {
        await tiersAPI.modifier(tiers.id, data)
      } else {
        await tiersAPI.creer(data)
      }
      onSave()
    } catch (e) {
      setErreur(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal titre={tiers ? 'Modifier le tiers' : 'Nouveau tiers'}
      icone={tiers ? 'ti-edit' : 'ti-user-plus'} onFermer={onFermer} largeur="md">
      <div className="hp-form-stack">
        <FormSection icon="ti-building-store" title="Identité du tiers"
          description="Définissez son rôle et les informations utilisées dans vos documents commerciaux.">
          <div className="hp-field" style={{ marginBottom: 12 }}>
            <label>Type <span className="hp-required">*</span></label>
            <div className="hp-choice-cards">
              {[
                ['client', 'ti-user-dollar', 'Client'],
                ['fournisseur', 'ti-truck-delivery', 'Fournisseur'],
                ['les_deux', 'ti-arrows-exchange', 'Les deux'],
              ].map(([val, icon, label]) => (
                <button key={val} type="button"
                  className={`hp-choice-card ${form.type === val ? 'is-active' : ''}`}
                  onClick={() => maj('type', val)}>
                  <i className={`ti ${icon}`} /> {label}
                </button>
              ))}
            </div>
          </div>

          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Profil de facturation</label>
              <select className={styles.input} value={form.categorie_fiscale || 'indetermine'}
                onChange={e => maj('categorie_fiscale', e.target.value)}>
                <option value="professionnel">Professionnel / entreprise</option>
                <option value="autoentrepreneur">Auto-entrepreneur</option>
                <option value="particulier">Particulier</option>
                <option value="indetermine">À préciser</option>
              </select>
              <span className="hp-field__hint">Le profil renseigne le statut du tiers ; il ne détermine pas à lui seul son régime de TVA.</span>
            </div>
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Nom / raison sociale <span className="hp-required">*</span></label>
              <input className={`${styles.input} ${fieldErrors.nom ? styles.inputError : ''}`} type="text"
                placeholder="Ex. Atlas Distribution SARL" autoFocus
                value={form.nom} onChange={e => maj('nom', e.target.value)} />
              {fieldErrors.nom && <span className="hp-field__error">{fieldErrors.nom}</span>}
            </div>
            <div className="hp-field">
              <label>ICE</label>
              <input className={`${styles.input} ${fieldErrors.ice ? styles.inputError : ''}`} type="text" inputMode="numeric" maxLength={15}
                placeholder="15 chiffres" value={form.ice || ''}
                onChange={e => maj('ice', normaliserIceSaisie(e.target.value))} />
              {fieldErrors.ice ? <span className="hp-field__error">{fieldErrors.ice}</span> : <span className="hp-field__hint">Identifiant commun de l'entreprise.</span>}
            </div>
            <div className="hp-field">
              <label>Identifiant fiscal (IF)</label>
              <input className={`${styles.input} ${fieldErrors.identifiant_fiscal ? styles.inputError : ''}`} type="text" inputMode="numeric" placeholder="Identifiant fiscal"
                value={form.identifiant_fiscal || ''} onChange={e => maj('identifiant_fiscal', normaliserIfSaisie(e.target.value))} />
              {fieldErrors.identifiant_fiscal && <span className="hp-field__error">{fieldErrors.identifiant_fiscal}</span>}
            </div>
            <div className="hp-field">
              <label>Registre de commerce (RC)</label>
              <input className={styles.input} type="text" placeholder="N° RC"
                value={form.rc || ''} onChange={e => maj('rc', e.target.value)} />
            </div>
          </div>
        </FormSection>

        <FormSection icon="ti-address-book" title="Coordonnées"
          description="Ces informations peuvent être reprises sur les factures et autres pièces commerciales.">
          <div className="hp-form-grid hp-form-grid--2">
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Adresse</label>
              <input className={styles.input} type="text" placeholder="Adresse complète"
                value={form.adresse || ''} onChange={e => maj('adresse', e.target.value)} />
            </div>
            <div className="hp-field">
              <label>Ville</label>
              <input className={styles.input} type="text" placeholder="Casablanca"
                value={form.ville || ''} onChange={e => maj('ville', e.target.value)} />
            </div>
            <div className="hp-field">
              <label>Téléphone</label>
              <input className={styles.input} type="tel" placeholder="+212 ..."
                value={form.telephone || ''} onChange={e => maj('telephone', e.target.value)} />
            </div>
            <div className="hp-field" style={{ gridColumn: '1 / -1' }}>
              <label>Email</label>
              <input className={`${styles.input} ${fieldErrors.email ? styles.inputError : ''}`} type="email"
                placeholder="contact@entreprise.ma" value={form.email || ''} onChange={e => maj('email', e.target.value)} />
              {fieldErrors.email && <span className="hp-field__error">{fieldErrors.email}</span>}
            </div>
          </div>
        </FormSection>

        <FormSection icon="ti-calendar-dollar" title="Conditions de règlement"
          description="Paramètres proposés automatiquement lors de la facturation.">
          <div className="hp-form-grid hp-form-grid--3">
            <div className="hp-field">
              <label>Délai de paiement</label>
              <input className={`${styles.input} ${fieldErrors.delai_paiement ? styles.inputError : ''}`} type="number" min="0" step="1"
                value={form.delai_paiement ?? 60} onChange={e => maj('delai_paiement', e.target.value)} />
              <span className="hp-field__hint">{Number(form.delai_paiement) === 0 ? 'Paiement comptant' : `${form.delai_paiement || 0} jour(s) après facture`}</span>
              {fieldErrors.delai_paiement && <span className="hp-field__error">{fieldErrors.delai_paiement}</span>}
            </div>
            <div className="hp-field">
              <label>Plafond de crédit (MAD)</label>
              <input className={`${styles.input} ${fieldErrors.plafond_credit ? styles.inputError : ''}`} type="number" min="0" step="100"
                placeholder="0 = illimité" value={form.plafond_credit ?? 0} onChange={e => maj('plafond_credit', e.target.value)} />
              <span className="hp-field__hint">0 = aucun plafond.</span>
              {fieldErrors.plafond_credit && <span className="hp-field__error">{fieldErrors.plafond_credit}</span>}
            </div>
            <div className="hp-field">
              <label>Retenue à la source (%)</label>
              <input className={`${styles.input} ${fieldErrors.taux_ras ? styles.inputError : ''}`} type="number" min="0" max="100" step="0.01"
                placeholder="0" value={form.taux_ras ?? ''} onChange={e => maj('taux_ras', e.target.value)} />
              {fieldErrors.taux_ras && <span className="hp-field__error">{fieldErrors.taux_ras}</span>}
            </div>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: 12, cursor: 'pointer' }}>
            <input type="checkbox" checked={form.assujetti_tva} onChange={e => maj('assujetti_tva', e.target.checked)} />
            Assujetti à la TVA
          </label>
        </FormSection>

        <AdvancedSection title="Paramétrage comptable" icon="ti-book-2">
          <div className="hp-form-grid hp-form-grid--2">
            {(form.type === 'client' || form.type === 'les_deux') && (
              <div className="hp-field">
                <label>Compte client</label>
                <input className={styles.input} type="text" placeholder="3421"
                  value={form.compte_client || '3421'} onChange={e => maj('compte_client', e.target.value)} />
                <span className="hp-field__hint">Compte utilisé pour les factures et règlements clients.</span>
              </div>
            )}
            {(form.type === 'fournisseur' || form.type === 'les_deux') && (
              <div className="hp-field">
                <label>Compte fournisseur</label>
                <input className={styles.input} type="text" placeholder="4411"
                  value={form.compte_fournisseur || '4411'} onChange={e => maj('compte_fournisseur', e.target.value)} />
                <span className="hp-field__hint">Compte utilisé pour les factures et règlements fournisseurs.</span>
              </div>
            )}
          </div>
        </AdvancedSection>

        {erreur && <InlineNotice tone="danger">{erreur}</InlineNotice>}

        <ActionBar hint="Les informations seront proposées automatiquement dans les prochains documents.">
          <button className="hp-btn-secondary" type="button" onClick={onFermer}>Annuler</button>
          <button className="hp-btn-primary" type="button" onClick={handleSave} disabled={!form.nom.trim() || loading}>
            <i className="ti ti-device-floppy" /> {loading ? 'Enregistrement...' : (tiers ? 'Enregistrer les modifications' : 'Créer le tiers')}
          </button>
        </ActionBar>
      </div>
    </Modal>
  )

}

// ─── Détail tiers ─────────────────────────────────────────────────────────────
function DetailTiers({ tiers, onFermer, onEdit }) {
  const estClient = tiers.type === 'client' || tiers.type === 'les_deux'
  const estFournisseur = tiers.type === 'fournisseur' || tiers.type === 'les_deux'
  const profils = {
    professionnel: 'Professionnel / entreprise',
    autoentrepreneur: 'Auto-entrepreneur',
    particulier: 'Particulier',
    indetermine: 'À préciser',
  }
  const sections = [
    {
      titre: 'Identité',
      icone: 'ti-building-store',
      champs: [
        ['Profil de facturation', profils[tiers.categorie_fiscale] || 'À préciser'],
        ['ICE', tiers.ice],
        ['Identifiant fiscal (IF)', tiers.identifiant_fiscal],
        ['Registre de commerce (RC)', tiers.rc],
      ],
    },
    {
      titre: 'Coordonnées',
      icone: 'ti-address-book',
      champs: [
        ['Adresse', tiers.adresse],
        ['Ville', tiers.ville],
        ['Téléphone', tiers.telephone],
        ['Email', tiers.email],
      ],
    },
    {
      titre: 'Comptabilité et règlement',
      icone: 'ti-receipt',
      champs: [
        ...(estClient ? [
          ['Compte client', tiers.compte_client],
          ['Auxiliaire client', tiers.code_aux_client],
        ] : []),
        ...(estFournisseur ? [
          ['Compte fournisseur', tiers.compte_fournisseur],
          ['Auxiliaire fournisseur', tiers.code_aux_fournisseur],
        ] : []),
        ['Délai de paiement', tiers.delai_paiement === 0 ? 'Comptant' : (tiers.delai_paiement != null ? `${tiers.delai_paiement} jours` : null)],
        ['Taux RAS', tiers.taux_ras != null && tiers.taux_ras !== '' ? `${tiers.taux_ras} %` : null],
        ['TVA', tiers.assujetti_tva == null ? null : (tiers.assujetti_tva ? 'Assujetti' : 'Non assujetti')],
      ],
    },
  ]

  return (
    <Modal titre={tiers.nom} icone="ti-user" onFermer={onFermer} largeur="md">
      <div className={styles.detailSheet}>
        <div className={styles.detailIntro}>
          <BadgeType type={tiers.type} />
          <span>Fiche du tiers</span>
        </div>
        {sections.map(({ titre, icone, champs }) => {
          const renseignes = champs.filter(([, valeur]) => valeur !== null && valeur !== undefined && valeur !== '')
          return (
            <section className={styles.detailSection} key={titre} aria-label={titre}>
              <h3 className={styles.detailSectionTitle}><i className={`ti ${icone}`} aria-hidden="true" />{titre}</h3>
              {renseignes.length ? (
                <dl className={styles.detailFields}>
                  {renseignes.map(([label, valeur]) => (
                    <div key={label} className={styles.detailField}>
                      <dt>{label}</dt>
                      <dd>{valeur}</dd>
                    </div>
                  ))}
                </dl>
              ) : <p className={styles.detailEmpty}>Aucune information renseignée.</p>}
            </section>
          )
        })}
        <div className={styles.detailActions}>
          <button className={styles.btnSec} type="button" onClick={onFermer}>Fermer</button>
          <button className={styles.btnPrim} type="button" onClick={onEdit}>
            <i className="ti ti-edit" aria-hidden="true" /> Modifier le tiers
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ─── Page Tiers ───────────────────────────────────────────────────────────────
// Résume l'activité d'un tiers : ancienneté du dernier mouvement, volume, impayés
function CelluleActivite({ info, incertain }) {
  if (incertain) return <span style={{ fontSize: 11, color: '#8A5A0B' }}>Activité indisponible</span>
  if (!info || !info.derniere) {
    return <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Aucun mouvement</span>
  }
  const jours = joursDepuis(info.derniere)
  const couleur = jours <= 30 ? '#3B6D11' : jours <= 90 ? '#C9A227' : 'var(--text-tertiary)'
  const depuis = jours < 0 ? 'date à venir' : jours === 0 ? "aujourd'hui"
    : jours === 1 ? 'hier'
    : jours < 30 ? `il y a ${jours} j`
    : jours < 365 ? `il y a ${Math.round(jours / 30)} mois`
    : `il y a ${Math.floor(jours / 365)} an${jours >= 730 ? 's' : ''}`
  return (
    <div style={{ fontSize: 11, lineHeight: 1.35 }}>
      <span style={{ color: couleur }}>{depuis}</span>
      <span style={{ color: 'var(--text-tertiary)' }}> · {info.nb} fact.</span>
      {info.creances > 0.01 && (
        <div style={{ color: '#A32D2D' }}>
          {info.creances.toLocaleString('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MAD à recevoir
        </div>
      )}
      {info.dettes > 0.01 && <div style={{ color: '#A32D2D' }}>{info.dettes.toLocaleString('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MAD à payer</div>}
      {info.indetermines > 0 && <div style={{ color: '#8A5A0B' }}>Solde à vérifier · {info.indetermines} fact.</div>}
    </div>
  )
}

export default function Tiers() {
  const [tiers,      setTiers]      = useState([])
  const [chargement, setChargement] = useState(false)
  const [filtreType, setFiltreType] = useState('TOUS')
  const [filtreActivite, setFiltreActivite] = useState('TOUS')
  const [filtreDelai, setFiltreDelai] = useState('TOUS')
  const [recherche,  setRecherche]  = useState('')
  const [factures,   setFactures]   = useState([])
  const [soldes, setSoldes] = useState({})
  const [activiteErreur, setActiviteErreur] = useState('')
  const [activiteChargement, setActiviteChargement] = useState(true)
  const [tiersErreur, setTiersErreur] = useState('')
  const { annee } = useExercice()
  const [panneau,    setPanneau]    = useState(null) // null | { mode: 'new'|'edit'|'detail', tiers? }

  async function charger() {
    setChargement(true)
    try {
      const token = getToken()
      const data = await collecterPages(async pagination => {
        if (getToken() !== token) throw new Error('La société active a changé. Rechargez les tiers.')
        const page = await tiersAPI.lister(pagination)
        if (getToken() !== token) throw new Error('La société active a changé. Rechargez les tiers.')
        return page
      })
      setTiers([...data].sort((a, b) => b.id - a.id))
      setTiersErreur('')
    } catch (e) { setTiersErreur(e.message); setTiers([]) }
    finally { setChargement(false) }
  }

  useEffect(() => { charger() }, [])

  // Factures de l'exercice : servent à calculer l'activité de chaque tiers
  useEffect(() => {
    let annule = false
    const token = getToken()
    setActiviteChargement(true); setActiviteErreur(''); setFactures([]); setSoldes({})
    facturesAPI.listerTout(annee)
      .then(async d => {
        const details = await chargerSoldes(d.filter(f => f.tiers_id != null), async id => {
          if (annule || getToken() !== token) throw new Error('Chargement interrompu')
          const r = await fetch(`${API_BASE}/api/factures/${id}/reglements`, { headers: { Authorization: `Bearer ${token}` } })
          if (!r.ok) throw new Error('Solde indisponible')
          const resultat = await r.json()
          if (getToken() !== token) throw new Error('La société active a changé')
          return resultat
        })
        if (annule) return
        if (getToken() !== token) throw new Error('La société active a changé. Rechargez les tiers.')
        setFactures(d); setSoldes(details)
      })
      .catch(e => { if (!annule) setActiviteErreur(e.message) })
      .finally(() => { if (!annule) setActiviteChargement(false) })
    return () => { annule = true }
  }, [annee])

  // Indicateurs par tiers : dernière facture, nombre, montant impayé
  const { parTiers: activiteParTiers, nonRattachees } = useMemo(() => resumerActivite(tiers, factures, soldes), [tiers, factures, soldes])

  const tiersFiltres = useMemo(() => {
    return tiers.filter(t => {
      if (!correspondDelaiPaiement(t.delai_paiement, filtreDelai)) return false
      if (filtreType !== 'TOUS') {
        if (filtreType === 'client'      && t.type !== 'client'      && t.type !== 'les_deux') return false
        if (filtreType === 'fournisseur' && t.type !== 'fournisseur' && t.type !== 'les_deux') return false
        if (filtreType === 'les_deux'    && t.type !== 'les_deux') return false
      }
      if (filtreActivite !== 'TOUS') {
        const a = activiteParTiers[t.id]
        const jours = a?.derniere
          ? joursDepuis(a.derniere)
          : null
        if (filtreActivite === 'recent'   && !(jours !== null && jours >= 0 && jours <= 30)) return false
        if (filtreActivite === 'dormant'  && (nonRattachees > 0 || !(jours === null || jours > 90))) return false
        if (filtreActivite === 'frequent' && !(a && a.nb >= 3)) return false
        if (filtreActivite === 'impaye'   && !(a && a.impaye > 0.01)) return false
      }
      if (recherche) {
        const q = recherche.toLowerCase()
        return t.nom.toLowerCase().includes(q) ||
               (t.ice || '').includes(q) ||
               (t.ville || '').toLowerCase().includes(q)
      }
      return true
    })
  }, [tiers, filtreType, filtreActivite, filtreDelai, recherche, activiteParTiers, nonRattachees])

  const stats = useMemo(() => ({
    clients:       tiers.filter(t => t.type === 'client'      || t.type === 'les_deux').length,
    fournisseurs:  tiers.filter(t => t.type === 'fournisseur' || t.type === 'les_deux').length,
  }), [tiers])

  async function supprimerTiers(id) {
    if (!confirm('Supprimer ce tiers ?')) return
    await tiersAPI.supprimer(id)
    charger()
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Clients / Fournisseurs</h1>
        <button className={styles.btnPrim}
          onClick={() => setPanneau({ mode: 'new' })}>
          <i className="ti ti-plus" aria-hidden="true" /> Nouveau tiers
        </button>
      </div>

      <div className={styles.content}>
        {/* KPIs */}
        <div className={styles.kpiGrid}>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-users" style={{ color: 'var(--blue)' }} aria-hidden="true" />Clients</div>
            <div className={styles.kpiValeur}>{stats.clients}<span className={styles.kpiSub}> tiers</span></div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-truck" style={{ color: '#534AB7' }} aria-hidden="true" />Fournisseurs</div>
            <div className={styles.kpiValeur}>{stats.fournisseurs}<span className={styles.kpiSub}> tiers</span></div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}><i className="ti ti-users-group" style={{ color: 'var(--green)' }} aria-hidden="true" />Total</div>
            <div className={styles.kpiValeur}>{tiers.length}<span className={styles.kpiSub}> tiers</span></div>
          </div>
        </div>

        {/* Filtres */}
        <div className={styles.filtres}>
          <div className={styles.recherche}>
            <i className="ti ti-search" aria-hidden="true" />
            <input type="text" placeholder="Rechercher nom, ICE, ville..."
              value={recherche} onChange={e => setRecherche(e.target.value)}
              className={styles.inputRecherche} />
            {recherche && <button className={styles.clearBtn} onClick={() => setRecherche('')}><i className="ti ti-x" aria-hidden="true" /></button>}
          </div>
          <div className={styles.filtresBarre}>
            <select className={styles.filtreBtn} aria-label="Délai de paiement"
              title="Délai paramétré dans la fiche du tiers, indépendamment des échéances des factures"
              value={filtreDelai} onChange={e => setFiltreDelai(e.target.value)}>
              {DELAIS.map(([valeur, label]) => <option key={valeur} value={valeur}>{label}</option>)}
            </select>
            {TYPES.map(({ val, label }) => (
              <button key={val}
                className={`${styles.filtreBtn} ${filtreType === val ? styles.filtreBtnActif : ''}`}
                onClick={() => setFiltreType(val)}>{label}</button>
            ))}
          </div>
          <div className={styles.filtresBarre}>
            {(activiteChargement || activiteErreur || tiersErreur || nonRattachees > 0) && (
              <span title={activiteErreur || tiersErreur || 'Les factures sans identifiant de tiers ne sont pas attribuées par leur nom.'}
                style={{ fontSize: 10.5, color: '#8A5A0B', background: '#FDF3E3',
                  padding: '3px 8px', borderRadius: 20, marginRight: 4 }}>
                <i className="ti ti-alert-triangle" style={{ marginRight: 3 }} />{activiteChargement ? 'Chargement de l’activité…' : activiteErreur || tiersErreur ? 'Activité indisponible' : `${nonRattachees} facture(s) non rattachée(s)`}
              </span>
            )}
            {ACTIVITES.map(({ val, label }) => (
              <button key={val}
                className={`${styles.filtreBtn} ${filtreActivite === val ? styles.filtreBtnActif : ''}`}
                onClick={() => setFiltreActivite(val)}
                disabled={val !== 'TOUS' && (activiteChargement || !!activiteErreur || !!tiersErreur)}
                title={`Basé sur les factures de l'exercice ${annee}`}>{label}</button>
            ))}
          </div>
        </div>

        <div className={styles.fullWidth}>
          {/* Table */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>{tiersFiltres.length} tiers</span>
            </div>
            {chargement ? (
              <div className={styles.vide}><i className="ti ti-loader-2" aria-hidden="true" /><span>Chargement...</span></div>
            ) : tiersFiltres.length === 0 ? (
              <div className={styles.vide}>
                <i className="ti ti-users-off" aria-hidden="true" />
                <span>Aucun tiers — créez votre premier client ou fournisseur</span>
              </div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Nom</th>
                      <th>Type</th>
                      <th>ICE</th>
                      <th>Ville</th>
                      <th>Délai</th>
                      <th>Activité</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {tiersFiltres.map(t => (
                      <tr key={t.id}
                        className={panneau?.tiers?.id === t.id ? styles.rowSelected : ''}
                        onClick={() => setPanneau({ mode: 'detail', tiers: t })}>
                        <td><strong>{t.nom}</strong></td>
                        <td><BadgeType type={t.type} /></td>
                        <td className={styles.tdMono}>{t.ice || '—'}</td>
                        <td>{t.ville || '—'}</td>
                        <td>{t.delai_paiement === 0 ? 'Comptant' : (t.delai_paiement != null ? `${t.delai_paiement}j` : '—')}</td>
                        <td><CelluleActivite info={activiteParTiers[t.id]} incertain={activiteChargement || !!activiteErreur || nonRattachees > 0 && !activiteParTiers[t.id]} /></td>
                        <td>
                          <button className={styles.btnTrash}
                            onClick={e => { e.stopPropagation(); supprimerTiers(t.id) }}
                            aria-label="Supprimer">
                            <i className="ti ti-trash" aria-hidden="true" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Panneau droit */}
          {panneau?.mode === 'new' && (
            <FormulaireTiers
              onFermer={() => setPanneau(null)}
              onSave={() => { charger(); setPanneau(null) }}
            />
          )}
          {panneau?.mode === 'edit' && (
            <FormulaireTiers
              tiers={panneau.tiers}
              onFermer={() => setPanneau(null)}
              onSave={() => { charger(); setPanneau(null) }}
            />
          )}
          {panneau?.mode === 'detail' && (
            <DetailTiers
              tiers={panneau.tiers}
              onFermer={() => setPanneau(null)}
              onEdit={() => setPanneau({ mode: 'edit', tiers: panneau.tiers })}
            />
          )}
        </div>
      </div>
    </div>
  )
}
