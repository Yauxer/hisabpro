import { useState, useRef, useEffect, useMemo } from 'react'
import { JOURNAUX, formatMAD } from '../data/donnees.js'
import { rechercherCompte, trouverCompte } from '../data/planComptes.js'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { API_BASE, tiersAPI, modelesAPI } from '../services/api.js'
import Modal from './Modal.jsx'
import styles from './FormulaireEcriture.module.css'
import { tauxTVAAvecHistorique } from '../utils/tvaUtils.js'
import { calculerMontantsModele, montantLigneModele, recalculerTauxModele } from '../utils/montantsModeles.js'
import { initialiserLibelleLigne, synchroniserLibelleCompte, libelleEffectifLigne } from '../utils/libellesEcriture.js'

// ─── Libellés types par journal ──────────────────────────────────────────────
const LIBELLES_PAR_JOURNAL = {
  AC: [
    { label: 'Achat de marchandises',         texte: 'Achat de marchandises — ' },
    { label: 'Achat de matières premières',    texte: 'Achat de matières premières — ' },
    { label: 'Achat de fournitures',           texte: 'Achat de fournitures — ' },
    { label: 'Achat de services',              texte: 'Achat de services — ' },
    { label: 'Facture fournisseur',            texte: 'Facture fournisseur — ' },
  ],
  VT: [
    { label: 'Vente de marchandises',          texte: 'Vente de marchandises — ' },
    { label: 'Vente de produits finis',        texte: 'Vente de produits finis — ' },
    { label: 'Prestation de services',         texte: 'Prestation de services — ' },
    { label: 'Facture client',                 texte: 'Facture client — ' },
  ],
  BQ: [
    { label: 'Virement reçu',                  texte: 'Virement reçu — ' },
    { label: 'Virement émis',                  texte: 'Virement émis — ' },
    { label: 'Encaissement client',            texte: 'Encaissement client — ' },
    { label: 'Paiement fournisseur',           texte: 'Paiement fournisseur — ' },
    { label: 'Frais bancaires',                texte: 'Frais bancaires — ' },
    { label: 'Agios / intérêts',               texte: 'Agios bancaires — ' },
    { label: 'Remise de chèques',              texte: 'Remise de chèques — ' },
    { label: 'Versement caisse en banque',      texte: 'Versement de la caisse en banque — ' },
    { label: 'Virement interne bancaire',       texte: 'Virement entre comptes bancaires — ' },
    { label: 'Paiement de TVA par banque',      texte: 'Paiement TVA par banque — ' },
    { label: 'Libération de capital par virement', texte: 'Libération du capital — virement bancaire — ' },
  ],
  CA: [
    { label: 'Encaissement espèces',           texte: 'Encaissement espèces — ' },
    { label: 'Paiement espèces',               texte: 'Paiement espèces — ' },
    { label: 'Libération de capital en espèces', texte: 'Libération du capital — espèces — ' },
  ],
  OD: [
    { label: 'Régularisation',                 texte: 'Régularisation — ' },
    { label: 'Charges à payer',                texte: 'Charges à payer — ' },
    { label: 'Produits à recevoir',            texte: 'Produits à recevoir — ' },
    { label: 'Reclassement comptable',         texte: 'Reclassement comptable — ' },
    { label: 'Souscription de capital',        texte: 'Souscription du capital — ' },
    { label: 'Apport en nature',               texte: 'Libération du capital — apport en nature — ' },
  ],
  AM: [
    { label: 'Dotation aux amortissements',    texte: 'Dotation aux amortissements — ' },
    { label: 'Amortissement immobilisations',  texte: 'Amortissement immobilisations — ' },
    { label: 'Amortissement matériel',         texte: 'Amortissement matériel bureau — ' },
    { label: 'Amortissement véhicule',         texte: 'Amortissement véhicule — ' },
    { label: 'Amortissement logiciel',         texte: 'Amortissement logiciel — ' },
  ],
  PR: [
    { label: 'Provision pour créances douteuses', texte: 'Provision créances douteuses — ' },
    { label: 'Provision pour risques',         texte: 'Provision pour risques — ' },
    { label: 'Reprise de provision',           texte: 'Reprise de provision — ' },
  ],
  TV: [
    { label: 'Déclaration TVA',                texte: 'Déclaration TVA — ' },
    { label: 'Régularisation TVA',             texte: 'Régularisation TVA — ' },
  ],
  SA: [
    { label: 'Rémunérations du personnel',    texte: 'Rémunérations du personnel — ' },
    { label: 'Primes et gratifications',      texte: 'Primes et gratifications — ' },
  ],
  AN: [
    { label: 'Report à nouveau',               texte: 'Report à nouveau — ' },
    { label: 'Solde à nouveau',                texte: 'Solde à nouveau exercice — ' },
  ],
  AV: [
    { label: "Avoir client",                   texte: "Avoir client — " },
    { label: "Avoir sur vente",                texte: "Avoir sur vente — " },
    { label: "Avoir fournisseur",              texte: "Avoir fournisseur — " },
    { label: "Avoir sur achat",                texte: "Avoir sur achat — " },
    { label: "Note de crédit",                 texte: "Note de crédit — " },
  ],
  AE: [
    { label: "Effet à encaisser",              texte: "Effet à encaisser — " },
    { label: "Billet à ordre reçu",            texte: "Billet à ordre reçu — " },
  ],
  EN: [
    { label: "Facture en cours",               texte: "Facture en cours — " },
    { label: "Travaux en cours",               texte: "Travaux en cours — " },
  ],
}

// ─── Icônes par catégorie ─────────────────────────────────────────────────────
const ICONES_MODELES = {
  achat_marchandises:   { icon: 'ti-shopping-cart',    couleur: '#534AB7' },
  achat_matieres:       { icon: 'ti-package',           couleur: '#534AB7' },
  achat_fournitures:    { icon: 'ti-pencil',            couleur: '#534AB7' },
  achat_services:       { icon: 'ti-briefcase',         couleur: '#534AB7' },
  achat_honoraires:     { icon: 'ti-user-check',        couleur: '#534AB7' },
  achat_loyer:          { icon: 'ti-building',          couleur: '#534AB7' },
  achat_telephone:      { icon: 'ti-phone',             couleur: '#534AB7' },
  achat_electricite:    { icon: 'ti-bolt',              couleur: '#534AB7' },
  achat_assurance:      { icon: 'ti-shield',            couleur: '#534AB7' },
  achat_entretien:      { icon: 'ti-tool',              couleur: '#534AB7' },
  achat_transport:      { icon: 'ti-truck',             couleur: '#534AB7' },
  achat_immo:           { icon: 'ti-building-factory',  couleur: '#534AB7' },
  vente_marchandises:   { icon: 'ti-arrow-up-right',    couleur: '#185FA5' },
  vente_produits:       { icon: 'ti-arrow-up-right',    couleur: '#185FA5' },
  vente_services:       { icon: 'ti-arrows-right-left', couleur: '#185FA5' },
  vente_travaux:        { icon: 'ti-hard-hat',          couleur: '#185FA5' },
  vente_locations:      { icon: 'ti-home',              couleur: '#185FA5' },
  encaissement_client:  { icon: 'ti-cash',              couleur: '#3B6D11' },
  paiement_fournisseur: { icon: 'ti-credit-card',       couleur: '#854F0B' },
  frais_bancaires:      { icon: 'ti-building-bank',     couleur: '#854F0B' },
  virement_salaires:    { icon: 'ti-users',             couleur: '#854F0B' },
  paiement_tva:         { icon: 'ti-percentage',        couleur: '#A32D2D' },
  paiement_cnss:        { icon: 'ti-heart-handshake',   couleur: '#A32D2D' },
  paiement_ir:          { icon: 'ti-receipt-tax',       couleur: '#A32D2D' },
  paiement_is:          { icon: 'ti-receipt',           couleur: '#A32D2D' },
  paie_salaires:        { icon: 'ti-wallet',            couleur: '#3B6D11' },
}

const CATEGORIES = [
  { id: 'ventes',      label: 'Ventes',            prefixes: ['vente_', 'avoir_client'] },
  { id: 'achats',      label: 'Achats',            prefixes: ['achat_', 'avoir_fournisseur'] },
  { id: 'treso',       label: 'Trésorerie',        prefixes: ['treso_', 'encaissement_client', 'paiement_fournisseur', 'frais_bancaires', 'virement_salaires'] },
  { id: 'effets',      label: 'Effets de commerce', prefixes: ['effet_'] },
  { id: 'paie',        label: 'Paie',              prefixes: ['paie_'] },
  { id: 'fiscalite',   label: 'TVA / Fiscalité',   prefixes: ['tva_', 'fiscal_', 'paiement_tva', 'paiement_cnss', 'paiement_ir', 'paiement_is'] },
  { id: 'financement', label: 'Financement',       prefixes: ['financement_', 'associe_', 'capital_'] },
  { id: 'cloture',     label: 'Fin d\'exercice',   prefixes: ['cloture_'] },
]

function modeleAutoCalculable(modele) {
  const lignes = modele?.lignes || []
  const principales = lignes.filter(l => l.est_principal)
  const autres = lignes.filter(l => !l.est_principal && !l.est_tva)
  // Automatisation sûre uniquement pour les schémas simples :
  // 1 ligne principale + éventuellement TVA + 1 contrepartie.
  // Les écritures complexes (paie, ventilations...) restent préremplies
  // mais leurs montants sont laissés à la saisie afin de ne pas inventer
  // des contreparties.
  return principales.length === 1 && autres.length === 1 && lignes.length <= 3
}

// ─── Sélecteur de modèle ──────────────────────────────────────────────────────
function SelecteurModele({ onChoisir, onFermer }) {
  const [modeles,    setModeles]    = useState([])
  const [categorie,  setCategorie]  = useState('ventes')
  const [recherche,  setRecherche]  = useState('')
  const [chargement, setChargement] = useState(true)

  useEffect(() => {
    modelesAPI.lister()
      .then(data => { setModeles(data); setChargement(false) })
      .catch(() => setChargement(false))
  }, [])

  const modelesFiltres = modeles.filter(m => {
    if (recherche) {
      return m.libelle.toLowerCase().includes(recherche.toLowerCase()) ||
             m.compte_declencheur?.includes(recherche)
    }
    const cat = CATEGORIES.find(c => c.id === categorie)
    if (!cat) return true
    return cat.prefixes.some(p => m.code.startsWith(p) || m.code === p)
  })

  return (
    <div className={styles.selecteurOverlay} onClick={e => { if (e.target === e.currentTarget) onFermer() }}>
      <div className={styles.selecteurModal}>
        <div className={styles.selecteurHeader}>
          <span className={styles.selecteurTitre}>
            <i className="ti ti-list-check" aria-hidden="true" /> Choisir un modèle d'écriture
          </span>
          <button className={styles.btnIcone} onClick={onFermer}><i className="ti ti-x" aria-hidden="true" /></button>
        </div>

        {/* Recherche */}
        <div className={styles.selecteurRecherche}>
          <i className="ti ti-search" aria-hidden="true" />
          <input type="text" placeholder="Rechercher une opération..."
            value={recherche} onChange={e => setRecherche(e.target.value)}
            autoFocus />
        </div>

        {/* Catégories */}
        {!recherche && (
          <div className={styles.selecteurCats}>
            {CATEGORIES.map(c => (
              <button key={c.id}
                className={`${styles.selecteurCatBtn} ${categorie === c.id ? styles.selecteurCatActif : ''}`}
                onClick={() => setCategorie(c.id)}>
                {c.label}
              </button>
            ))}
          </div>
        )}

        {/* Liste des modèles */}
        <div className={styles.selecteurListe}>
          {chargement ? (
            <div className={styles.selecteurVide}>Chargement...</div>
          ) : modelesFiltres.length === 0 ? (
            <div className={styles.selecteurVide}>Aucun modèle trouvé</div>
          ) : modelesFiltres.map(m => {
            const config = ICONES_MODELES[m.code] || { icon: 'ti-edit', couleur: '#666' }
            return (
              <button key={m.id} className={styles.selecteurItem} onClick={() => onChoisir(m)}>
                <div className={styles.selecteurItemIcone} style={{ background: config.couleur + '18', color: config.couleur }}>
                  <i className={`ti ${config.icon}`} aria-hidden="true" />
                </div>
                <div className={styles.selecteurItemInfo}>
                  <span className={styles.selecteurItemLibelle}>{m.libelle}</span>
                  <div className={styles.selecteurItemComptes}>
                    {m.lignes.map((l, i) => (
                      <span key={i} className={styles.selecteurCompteBadge}
                        style={{ color: l.sens === 'debit' ? 'var(--green)' : 'var(--red)' }}>
                        {l.compte} {l.sens === 'debit' ? 'D' : 'C'}
                      </span>
                    ))}
                  </div>
                </div>
                <i className="ti ti-chevron-right" style={{ color: 'var(--text-tertiary)', fontSize: 14 }} aria-hidden="true" />
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Autocomplete compte ──────────────────────────────────────────────────────
function ChampCompte({ value, onChange }) {
  const [suggestions, setSuggestions] = useState([])
  const [ouvert, setOuvert] = useState(false)
  const ref = useRef(null)

  function handleChange(val) {
    onChange(val)
    if (val.length >= 1) {
      const res = rechercherCompte(val)
      setSuggestions(res)
      setOuvert(res.length > 0)
    } else {
      setSuggestions([])
      setOuvert(false)
    }
  }

  useEffect(() => {
    function clickDehors(e) {
      if (ref.current && !ref.current.contains(e.target)) setOuvert(false)
    }
    document.addEventListener('mousedown', clickDehors)
    return () => document.removeEventListener('mousedown', clickDehors)
  }, [])

  const compteInfo = trouverCompte(value)

  return (
    <div className={styles.autocompleteWrap} ref={ref}>
      <input
        className={styles.inputSm}
        type="text"
        placeholder="Ex: 6111"
        value={value}
        onChange={e => handleChange(e.target.value)}
        onBlur={() => setOuvert(false)}
        onFocus={() => {
          if (value && value.length >= 1) {
            const res = rechercherCompte(value)
            setSuggestions(res)
            setOuvert(res.length > 0)
          }
        }}
        maxLength={8}
      />
      {compteInfo && !ouvert && (
        <span className={styles.compteTip}>{compteInfo.libelle}</span>
      )}
      {ouvert && suggestions.length > 0 && (
        <ul className={styles.suggestions}>
          {suggestions.map(c => (
            <li key={c.compte} onMouseDown={() => { onChange(c.compte); setOuvert(false) }}
              className={styles.suggestion}>
              <span className={styles.suggNum}>{c.compte}</span>
              <span className={styles.suggLib}>{c.libelle}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ─── Mini formulaire création tiers rapide ───────────────────────────────────
function MiniFormTiers({ nom, type, onCreer, onAnnuler }) {
  const [form, setForm] = useState({
    nom: nom || '',
    type: type || 'fournisseur',
    ville: '',
    telephone: '',
    ice: '',
  })
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')

  async function handleCreer() {
    if (!form.nom.trim()) return
    setLoading(true)
    setErreur('')
    try {
      const nouveau = await tiersAPI.creer({
        ...form,
        compte_client: '3421',
        compte_fournisseur: '4411',
        assujetti_tva: true,
        delai_paiement: 60,
      })
      onCreer(nouveau)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.miniForm}>
      <div className={styles.miniFormTitre}>
        <i className="ti ti-user-plus" aria-hidden="true" />
        Créer un nouveau tiers
      </div>
      <div className={styles.miniFormRow}>
        <div className={styles.miniFormGroup}>
          <label>Nom *</label>
          <input type="text" value={form.nom}
            onChange={e => setForm(p => ({ ...p, nom: e.target.value }))} />
        </div>
        <div className={styles.miniFormGroup}>
          <label>Type</label>
          <select value={form.type}
            onChange={e => setForm(p => ({ ...p, type: e.target.value }))}>
            <option value="client">Client</option>
            <option value="fournisseur">Fournisseur</option>
            <option value="les_deux">Les deux</option>
          </select>
        </div>
      </div>
      <div className={styles.miniFormRow}>
        <div className={styles.miniFormGroup}>
          <label>ICE</label>
          <input type="text" placeholder="000000000000000"
            value={form.ice}
            onChange={e => setForm(p => ({ ...p, ice: e.target.value }))} />
        </div>
        <div className={styles.miniFormGroup}>
          <label>Ville</label>
          <input type="text" placeholder="Casablanca"
            value={form.ville}
            onChange={e => setForm(p => ({ ...p, ville: e.target.value }))} />
        </div>
      </div>
      {erreur && <div className={styles.miniFormErreur}>{erreur}</div>}
      <div className={styles.miniFormActions}>
        <button className={styles.miniFormAnnuler} onClick={onAnnuler}>Annuler</button>
        <button className={styles.miniFormCreer} onClick={handleCreer} disabled={!form.nom.trim() || loading}>
          {loading ? 'Création...' : <><i className="ti ti-check" aria-hidden="true" /> Créer</>}
        </button>
      </div>
    </div>
  )
}

// ─── Autocomplete tiers ───────────────────────────────────────────────────────
function natureAuxiliaireCompte(compte) {
  const c = String(compte || '').trim()
  if (['3421', '3425', '4421'].some(p => c.startsWith(p))) return 'client'
  if (['4411', '4415', '3411', '4481'].some(p => c.startsWith(p))) return 'fournisseur'
  return null
}

function ChampTiers({ value, onChange, onSelect, compte, tiersId }) {
  const [suggestions, setSuggestions] = useState([])
  const [ouvert, setOuvert] = useState(false)
  const [listeTiers, setListeTiers] = useState([])
  const [estNouveau, setEstNouveau] = useState(false)
  const [showMiniForm, setShowMiniForm] = useState(false)
  const ref = useRef(null)

  const typeDefaut = natureAuxiliaireCompte(compte)
  const estCompteTiers = Boolean(typeDefaut)

  useEffect(() => {
    tiersAPI.lister().then(setListeTiers).catch(() => {})
  }, [])

  function handleChange(val) {
    onChange(val)
    onSelect?.(null) // toute saisie libre rompt la sélection explicite
    if (val.length >= 2) {
      const q = val.toLowerCase()
      const res = listeTiers.filter(t => {
        const roleOk = !typeDefaut || t.type === typeDefaut || t.type === 'les_deux'
        return roleOk && (t.nom.toLowerCase().includes(q) || (t.ice || '').includes(q))
      }).slice(0, 8)
      setSuggestions(res)
      setOuvert(true)
      setEstNouveau(val.length > 2 && !listeTiers.find(t =>
        t.nom.toLowerCase() === val.toLowerCase()))
    } else {
      setSuggestions([]); setOuvert(false); setEstNouveau(false)
    }
  }

  function handleCreerTiers(nouveau) {
    setListeTiers(prev => [...prev, nouveau])
    onChange(nouveau.nom)
    onSelect?.(nouveau)
    setOuvert(false)
    setEstNouveau(false)
    setShowMiniForm(false)
  }

  useEffect(() => {
    function clickDehors(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOuvert(false)
        setShowMiniForm(false)
      }
    }
    document.addEventListener('mousedown', clickDehors)
    return () => document.removeEventListener('mousedown', clickDehors)
  }, [])

  return (
    <div className={styles.autocompleteWrap} ref={ref} style={{ flex: 1 }}>
      <div style={{ position: 'relative' }}>
        <input
          className={styles.inputSm}
          type="text"
          placeholder={estCompteTiers ? 'Nom client / fournisseur...' : 'Libellé ligne'}
          value={value}
          onChange={e => handleChange(e.target.value)}
          style={{ paddingRight: estNouveau ? 72 : 8 }}
        />
        {estNouveau && <span className={styles.nouveauBadge}>Nouveau</span>}
      </div>
      {estCompteTiers && tiersId && (
        <small style={{ display: 'block', marginTop: 3, color: 'var(--text-secondary)' }}>
          Auxiliaire sélectionné
        </small>
      )}

      {ouvert && !showMiniForm && (
        <ul className={styles.suggestions}>
          {suggestions.map(t => (
            <li key={t.id}
              onMouseDown={() => { onChange(t.nom); onSelect?.(t); setOuvert(false); setEstNouveau(false) }}
              className={styles.suggestion}>
              <span className={styles.suggNum}>
                {t.type === 'client' ? '👤' : t.type === 'fournisseur' ? '🏢' : '↔️'}
              </span>
              <span className={styles.suggLib}>{t.nom}</span>
              {estCompteTiers && (
                <span className={styles.suggVille}>
                  {typeDefaut === 'client' ? t.code_aux_client : t.code_aux_fournisseur}
                </span>
              )}
              {t.ville && <span className={styles.suggVille}>{t.ville}</span>}
            </li>
          ))}
          {/* Bouton créer si tiers non trouvé */}
          {estNouveau && estCompteTiers && (
            <li className={styles.suggestionCreer}
              onMouseDown={e => {
                e.preventDefault()
                e.stopPropagation()
                setOuvert(false)
                setShowMiniForm(true)
              }}>
              <i className="ti ti-plus" aria-hidden="true" />
              Créer "<strong>{value}</strong>" comme {typeDefaut}
            </li>
          )}
        </ul>
      )}

      {/* Mini formulaire création — affiché en dehors du wrapper */}
      {showMiniForm && (
        <div className={styles.miniFormOverlay}>
          <MiniFormTiers
            nom={value}
            type={typeDefaut}
            onCreer={handleCreerTiers}
            onAnnuler={() => setShowMiniForm(false)}
          />
        </div>
      )}
    </div>
  )
}

// Accepte aussi bien 1234.56 que 1 234,56 (saisie francophone).
function parseMontant(value) {
  if (value === null || value === undefined || value === '') return 0
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0
  const normalise = String(value).trim().replace(/\s/g, '').replace(',', '.')
  const montant = Number(normalise)
  return Number.isFinite(montant) ? montant : 0
}

function dateLocaleISO() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const j = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${j}`
}

function bornesExercice(exercice, annee) {
  const debut = String(exercice?.date_debut || `${annee}-01-01`).slice(0, 10)
  const fin   = String(exercice?.date_fin   || `${annee}-12-31`).slice(0, 10)
  return { debut, fin }
}

function dateDansExercice(exercice, annee) {
  const { debut, fin } = bornesExercice(exercice, annee)
  const aujourdHui = dateLocaleISO()
  if (aujourdHui < debut) return debut
  if (aujourdHui > fin) return fin
  return aujourdHui
}

const META_JOURNAL = {
  AC: { libelle: 'Achat fournisseur', ref: 'N° facture / justificatif fournisseur' },
  VT: { libelle: 'Vente client', ref: 'N° facture / justificatif client' },
  BQ: { libelle: 'Opération bancaire', ref: 'Réf. relevé / virement / chèque' },
  CA: { libelle: 'Opération de caisse', ref: 'Réf. justificatif de caisse' },
  OD: { libelle: 'Opération diverse', ref: 'Réf. justificatif (optionnel)' },
  AV: { libelle: 'Avoir', ref: 'N° avoir / note de crédit' },
  AN: { libelle: 'À-nouveau', ref: 'Réf. reprise / clôture' },
  EN: { libelle: 'En-cours', ref: 'Réf. dossier / justificatif' },
  AE: { libelle: 'Effet à encaisser', ref: 'N° effet / chèque' },
  AM: { libelle: 'Dotation aux amortissements', ref: 'Réf. immobilisation / calcul' },
  SA: { libelle: 'Rémunérations du personnel', ref: 'Réf. bulletin / période' },
  TV: { libelle: 'TVA', ref: 'Réf. déclaration / paiement' },
  PR: { libelle: 'Provision / reprise', ref: 'Réf. dossier / justificatif' },
}

function tiersDepuisLignes(lignes) {
  const ligne = (lignes || []).find(l => {
    const c = String(l.compte || '')
    return c.startsWith('3421') || c.startsWith('3424') ||
           c.startsWith('4411') || c.startsWith('4415')
  })
  if (!ligne?.libelle) return ''
  const lib = String(ligne.libelle).trim()
  const compte = trouverCompte(ligne.compte)?.libelle || ''
  return lib && lib !== compte ? lib : ''
}

function natureDepuisLignes(journal, lignes) {
  const debit = prefix => (lignes || []).some(l => String(l.compte || '').startsWith(prefix) && parseMontant(l.debit) > 0)
  const credit = prefix => (lignes || []).some(l => String(l.compte || '').startsWith(prefix) && parseMontant(l.credit) > 0)

  if (journal === 'BQ') {
    if (debit('514') && (credit('1111') || credit('3461') || credit('3462'))) return 'Libération du capital par banque'
    if (debit('514') && credit('3421')) return 'Encaissement client'
    if (credit('514') && debit('4411')) return 'Paiement fournisseur'
    if (credit('514') && debit('6')) return 'Paiement / frais bancaire'
  }
  if (journal === 'CA') {
    if (debit('5161') && (credit('1111') || credit('3461'))) return 'Libération du capital en espèces'
    if (debit('5161') && credit('3421')) return 'Encaissement client en espèces'
    if (credit('5161') && debit('4411')) return 'Paiement fournisseur en espèces'
  }
  if (journal === 'OD') {
    if ((debit('3461') || debit('3462')) && (credit('1111') || credit('1119'))) return 'Souscription ou appel du capital'
    if ((debit('23') || debit('22')) && (credit('1111') || credit('3461'))) return 'Libération du capital par apport en nature'
  }
  return META_JOURNAL[journal]?.libelle || 'Écriture comptable'
}

function genererLibelleIntelligent(journal, reference, lignes) {
  const nature = natureDepuisLignes(journal, lignes)
  const tiers = tiersDepuisLignes(lignes)
  const parts = [nature]
  if (tiers) parts.push(tiers)
  if (String(reference || '').trim()) parts.push(`réf. ${String(reference).trim()}`)
  return parts.join(' — ')
}

// ─── Formulaire principal ─────────────────────────────────────────────────────
export default function FormulaireEcriture({ onFermer, onSuccess, ecriture = null }) {
  const { ajouterEcriture, modifierEcriture } = useEcritures()
  const { annee, exercice } = useExercice()
  const edition = !!ecriture   // null → création, objet → modification
  const bornes = bornesExercice(exercice, annee)
  const dateInitiale = ecriture?.date
    ? String(ecriture.date).slice(0, 10)
    : dateDansExercice(exercice, annee)
  const datePieceInitiale = ecriture?.date_piece
    ? String(ecriture.date_piece).slice(0, 10)
    : dateInitiale

  // En modification, les champs sont pré-remplis avec l'écriture existante.
  const [journal,       setJournal]       = useState(ecriture?.journal || 'AC')
  const [date,          setDate]          = useState(dateInitiale)
  const [datePiece,     setDatePiece]     = useState(datePieceInitiale)
  // Par défaut, le justificatif porte la même date que l'écriture. En édition,
  // on conserve automatiquement ce mode lorsque les deux dates enregistrées sont égales.
  const [datePieceAuto, setDatePieceAuto] = useState(datePieceInitiale === dateInitiale)
  const [libelle,       setLibelle]       = useState(ecriture?.libelle || '')
  const [libelleAuto,   setLibelleAuto]   = useState(!ecriture)
  const [reference,     setReference]     = useState(ecriture?.reference || '')
  const [numeroPreview, setNumeroPreview] = useState(ecriture?.numero_ecriture || '')
  const numeroVerrouille = Boolean((ecriture?.numero_ecriture || '').trim())
  // Valider à l'enregistrement : l'écriture devient définitive immédiatement
  const [validerDirect, setValiderDirect] = useState(false)
  const [lignes,        setLignes]        = useState(
    ecriture?.lignes?.length
      ? ecriture.lignes.map(l => initialiserLibelleLigne({
          compte:  l.compte || '',
          libelle: l.libelle || '',
          tiers_id: l.tiers_id || null,
          debit:   l.debit  ? String(l.debit)  : '',
          credit:  l.credit ? String(l.credit) : '',
        }, trouverCompte, natureAuxiliaireCompte))
      : [
          { compte: '', libelle: '', tiers_id: null, debit: '', credit: '', libelle_personnalise: false },
          { compte: '', libelle: '', tiers_id: null, debit: '', credit: '', libelle_personnalise: false },
          { compte: '', libelle: '', tiers_id: null, debit: '', credit: '', libelle_personnalise: false },
        ])
  const [modelePropose, setModelePropose] = useState(null)
  const rechercheModeleVersion = useRef(0)
  const [modeleActif,   setModeleActif]   = useState(null)
  const [modeAssist,    setModeAssist]    = useState(!ecriture)
  const [showSelecteur, setShowSelecteur] = useState(false)
  const [enregistre,    setEnregistre]    = useState(false)
  const [erreur,        setErreur]        = useState('')
  const [loading,       setLoading]       = useState(false)
  const [alerteDoublon, setAlerteDoublon] = useState(null)
  const [chargementRef, setChargementRef] = useState(false)

  const totalDebit  = lignes.reduce((s, l) => s + parseMontant(l.debit), 0)
  const totalCredit = lignes.reduce((s, l) => s + parseMontant(l.credit), 0)
  const ecart       = Math.abs(totalDebit - totalCredit)
  const lignesUtilisees = lignes.filter(l => l.compte || l.debit || l.credit)
  const lignesCompletes = lignesUtilisees.length >= 2 && lignesUtilisees.every(l => {
    const debit = parseMontant(l.debit)
    const credit = parseMontant(l.credit)
    return Boolean(l.compte) && ((debit > 0 && credit === 0) || (credit > 0 && debit === 0))
  })
  // 0 = 0 n'est pas une écriture comptable : chaque sens doit porter un montant.
  const equilibre   = totalDebit > 0 && totalCredit > 0 && ecart < 0.005
  const auxiliairesComplets = lignesUtilisees.every(l => {
    const c = String(l.compte || '')
    return !(c.startsWith('3421') || c.startsWith('4411')) || Boolean(l.tiers_id)
  })
  const valide      = equilibre && Boolean(libelle.trim()) && lignesCompletes && (!validerDirect || auxiliairesComplets)

  // ── Alertes intelligentes ──────────────────────────────────────────────────
  const alertes = useMemo(() => {
    const liste = []

    // 1. Caisse créditrice — compte 5161 ne peut pas être créditeur
    lignes.forEach((l, i) => {
      if (l.compte.startsWith('5161')) {
        const solde = parseMontant(l.debit) - parseMontant(l.credit)
        if (solde < 0) {
          liste.push({
            type: 'danger',
            icon: 'ti-alert-triangle',
            message: `La caisse (compte 5161) ne peut pas être créditrice — solde négatif impossible`,
          })
        }
      }
    })

    // 2. Cash > 5 000 MAD — limite légale paiements espèces fournisseur
    lignes.forEach(l => {
      if (l.compte.startsWith('5161')) {
        const montant = parseMontant(l.credit)
        if (montant > 5000) {
          liste.push({
            type: 'warning',
            icon: 'ti-cash',
            message: `Paiement en espèces de ${formatMAD(montant)} MAD dépasse la limite légale de 5 000 MAD par fournisseur`,
          })
        }
      }
    })

    // 3. Compte banque créditeur (5141) sans écriture de transfert
    const ligne5141 = lignes.find(l => l.compte.startsWith('5141'))
    if (ligne5141) {
      const credit = parseMontant(ligne5141.credit)
      const debit  = parseMontant(ligne5141.debit)
      if (credit > debit && journal === 'CA') {
        liste.push({
          type: 'warning',
          icon: 'ti-building-bank',
          message: 'Vérifiez que le compte banque 5141 ne devient pas créditeur — utilisez 5541 si nécessaire',
        })
      }
    }

    // 4. Même compte en débit et crédit sur la même écriture
    const comptes = lignes.filter(l => l.compte).map(l => l.compte)
    const doublons = comptes.filter((c, i) => comptes.indexOf(c) !== i)
    if (doublons.length > 0) {
      liste.push({
        type: 'info',
        icon: 'ti-info-circle',
        message: `Le compte ${[...new Set(doublons)].join(', ')} apparaît plusieurs fois — vérifiez si c'est intentionnel`,
      })
    }

    return liste
  }, [lignes, journal])

  // ── Numéro interne et métadonnées automatiques ─────────────────────────────
  useEffect(() => {
    // Un brouillon sans numéro peut encore changer de journal : on affiche
    // seulement une prévision, jamais un numéro réservé.
    if (!numeroVerrouille) chargerProchainNumero(journal)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [journal, annee, numeroVerrouille])

  useEffect(() => {
    if (libelleAuto) {
      setLibelle(genererLibelleIntelligent(journal, reference, lignes))
    }
  }, [journal, reference, lignes, libelleAuto])

  async function chargerProchainNumero(j) {
    setChargementRef(true)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const res = await fetch(
        `${API_BASE}/api/references/prochain-numero?journal=${encodeURIComponent(j)}&exercice=${annee}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (res.ok) {
        const data = await res.json()
        setNumeroPreview(data.numero || '')
      }
    } catch {
      setNumeroPreview('')
    } finally {
      setChargementRef(false)
    }
  }

  async function verifierDoublon(ref, j) {
    const propre = String(ref || '').trim()
    if (propre.length < 3) { setAlerteDoublon(null); return }
    try {
      const token = localStorage.getItem('hisabpro_token')
      const params = new URLSearchParams({
        reference: propre,
        journal: j,
        exercice: String(annee),
      })
      if (edition && ecriture?.id) params.append('exclude_id', String(ecriture.id))
      const res = await fetch(
        `${API_BASE}/api/references/verifier-doublon?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (res.ok) {
        const data = await res.json()
        setAlerteDoublon(data.doublon ? data.ecriture : null)
      }
    } catch {}
  }

  function majReference(val) {
    setReference(val)
    setAlerteDoublon(null)
    clearTimeout(window._doublon)
    window._doublon = setTimeout(() => verifierDoublon(val, journal), 600)
  }

  function majJournal(val) {
    // 07C.2 : le journal reste modifiable tant que le brouillon n'a pas reçu
    // de numéro définitif. Après validation, le périmètre est verrouillé.
    if (numeroVerrouille) return
    setJournal(val)
    setAlerteDoublon(null)
  }

  // ── Modification d'une ligne ───────────────────────────────────────────────
  function majLigne(i, champ, val) {
    setLignes(prev => {
      const nouvLignes = prev.map((l, idx) => {
        if (idx !== i) return l
        if (champ === 'compte') {
          return synchroniserLibelleCompte(l, val, trouverCompte, natureAuxiliaireCompte)
        }
        if (champ === 'libelle_personnalise' && !val) {
          return { ...l, libelle_personnalise: false, libelle: trouverCompte(l.compte)?.libelle || '' }
        }
        return { ...l, [champ]: val }
      })

      if ((champ === 'debit' || champ === 'credit') && modeleActif && modeAssist && modeleAutoCalculable(modeleActif)) {
        const montant = parseMontant(val)
        if (montant === 0) return nouvLignes

        const lignesModele = modeleActif.lignes
        const lmActuel     = lignesModele[i]
        if (!lmActuel) return nouvLignes

        const montants = calculerMontantsModele(modeleActif, lmActuel, montant)
        if (!montants) return nouvLignes

        const lignesRecalc = lignesModele.map((lm, idx) => {
          if (idx === i) return nouvLignes[idx] // garde la valeur saisie
          const v = montantLigneModele(modeleActif, lm, montants).toFixed(2)
          return { ...nouvLignes[idx], debit: lm.sens === 'debit' ? v : '', credit: lm.sens === 'credit' ? v : '' }
        })
        return [...lignesRecalc, ...nouvLignes.slice(lignesModele.length)]
      }
      return nouvLignes
    })

    if (champ === 'compte' && val.length >= 3) {
      const version = ++rechercheModeleVersion.current
      setModelePropose(null)
      // Propose un modèle
      modelesAPI.parCompte(val)
        .then(mods => {
          if (version !== rechercheModeleVersion.current) return
          const exact = mods.filter(m => m.compte_declencheur === val)
          if (exact.length) setModelePropose({ modele: exact.length === 1 ? exact[0] : null, modeles: exact, indexLigne: i })
          else setModelePropose(null)
        })
        .catch(() => { if (version === rechercheModeleVersion.current) setModelePropose(null) })
    } else if (champ === 'compte') {
      rechercheModeleVersion.current++
      setModelePropose(null)
    }
  }

  // ── Applique un modèle ─────────────────────────────────────────────────────
  function changerTauxModele(nouveauTaux) {
    if (!modeleActif || !modeleAutoCalculable(modeleActif)) return
    const idxPrincipal = modeleActif.lignes.findIndex(lm => lm.est_principal)
    if (idxPrincipal === -1) return
    const lp = lignes[idxPrincipal]
    const montantPrincipal = parseMontant(lp?.debit || lp?.credit || 0)
    const recalcul = recalculerTauxModele(modeleActif, montantPrincipal, nouveauTaux)
    if (!recalcul) return
    setModeleActif(recalcul.modele)
    if (!montantPrincipal) return
    setLignes(prev => prev.map((l, idx) => {
      const lm = recalcul.modele.lignes[idx]
      if (!lm) return l
      const v = montantLigneModele(recalcul.modele, lm, recalcul.montants).toFixed(2)
      return { ...l, debit: lm.sens === 'debit' ? v : '', credit: lm.sens === 'credit' ? v : '' }
    }))
  }

  function appliquerModele(modele, montantBase = 0, compteSource = null) {
    const autoCalculable = modeleAutoCalculable(modele)
    const ligneSource = compteSource
      ? modele.lignes.find(lm => lm.compte === compteSource)
      : modele.lignes.find(lm => lm.est_principal)
    const montants = autoCalculable && montantBase && ligneSource
      ? calculerMontantsModele(modele, ligneSource, montantBase) : null
    const nouvLignes = modele.lignes.map(lm => {
      let debit = '', credit = ''
      if (montants) {
        const valeur = montantLigneModele(modele, lm, montants).toFixed(2)
        if (lm.sens === 'debit') debit = valeur
        if (lm.sens === 'credit') credit = valeur
      } else if (!autoCalculable && lm.est_principal) {
        if (lm.sens === 'debit')  debit  = montantBase ? montantBase.toString() : ''
        if (lm.sens === 'credit') credit = montantBase ? montantBase.toString() : ''
      }
      return initialiserLibelleLigne({ compte: lm.compte, libelle: lm.libelle || '', tiers_id: null, debit, credit }, trouverCompte, natureAuxiliaireCompte)
    })

    if (modele.journal) majJournal(modele.journal)
    setModeleActif(modele)
    setLignes([...nouvLignes, { compte: '', libelle: '', tiers_id: null, debit: '', credit: '', libelle_personnalise: false }])
    setModelePropose(null)
  }

  function handleChoisirModele(modele) {
    setShowSelecteur(false)
    appliquerModele(modele)
  }

  function handleAppliquerPropose() {
    if (!modelePropose?.modele) return
    const { modele, indexLigne } = modelePropose
    const montantBase = parseMontant(lignes[indexLigne]?.debit || lignes[indexLigne]?.credit || 0)
    appliquerModele(modele, montantBase, lignes[indexLigne]?.compte)
  }

  function ajouterLigne() {
    setLignes(prev => [...prev, { compte: '', libelle: '', tiers_id: null, debit: '', credit: '', libelle_personnalise: false }])
  }

  function supprimerLigne(i) {
    if (lignes.length <= 2) return
    setLignes(prev => prev.filter((_, idx) => idx !== i))
  }

  async function handleSubmit() {
    if (!valide) return
    setLoading(true); setErreur('')
    try {
      const lignesFiltrees = lignes.filter(l => l.compte || l.debit || l.credit)
      const donnees = {
        journal,
        date,
        date_piece: datePiece || date,
        libelle: libelle.trim(),
        reference: reference.trim(),
        est_validee: validerDirect,
        lignes: lignesFiltrees.map(l => ({
          compte:  l.compte,
          libelle: libelleEffectifLigne(l, trouverCompte, natureAuxiliaireCompte),
          tiers_id: l.tiers_id || null,
          debit:   parseMontant(l.debit),
          credit:  parseMontant(l.credit),
        })),
      }
      if (edition) await modifierEcriture(ecriture.id, donnees)
      else         await ajouterEcriture(donnees)
      setEnregistre(true)
      setTimeout(() => { onSuccess?.(); onFermer?.() }, 600)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {showSelecteur && (
        <SelecteurModele
          onChoisir={handleChoisirModele}
          onFermer={() => setShowSelecteur(false)}
        />
      )}

      <Modal titre={edition ? `Modifier l'écriture n° ${ecriture.id}` : "Nouvelle écriture comptable"} icone="ti-edit" onFermer={onFermer} largeur="xl">
        {enregistre ? (
          <div className={styles.successMsg}>
            <i className="ti ti-circle-check" aria-hidden="true" />
            Écriture enregistrée !
          </div>
        ) : (
          <div className={styles.contenu}>
            {/* Boutons d'action rapide */}
            <div className={styles.actionsRapides}>
              <button className={styles.btnModele} onClick={() => setShowSelecteur(true)}>
                <i className="ti ti-list-check" aria-hidden="true" />
                Choisir un modèle d'écriture
              </button>
            </div>

            {/* En-tête */}
            <div className={styles.entete}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Date comptable *</label>
                <input className={`${styles.input} ${numeroVerrouille ? styles.inputDisabled : ''}`} type="date" value={date}
                  min={bornes.debut} max={bornes.fin} disabled={numeroVerrouille}
                  onChange={e => {
                    const v = e.target.value
                    setDate(v)
                    if (datePieceAuto) setDatePiece(v)
                  }} />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Journal *</label>
                <select className={`${styles.input} ${numeroVerrouille ? styles.inputDisabled : ''}`} value={journal}
                  disabled={numeroVerrouille}
                  onChange={e => majJournal(e.target.value)}>
                  <optgroup label="── Journaux standards ──">
                    {JOURNAUX.filter(j => j.groupe === 'standard').map(j => (
                      <option key={j.code} value={j.code}>{j.code} — {j.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="── Journaux spéciaux ──">
                    {JOURNAUX.filter(j => j.groupe === 'special').map(j => (
                      <option key={j.code} value={j.code}>{j.code} — {j.label}</option>
                    ))}
                  </optgroup>
                </select>

              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>
                  N° écriture
                  {chargementRef && <span className={styles.loadingTiny}>...</span>}
                </label>
                <input className={`${styles.input} ${styles.inputReadOnly}`} type="text"
                  value={numeroVerrouille ? ecriture.numero_ecriture : (numeroPreview ? `${numeroPreview} (prévision)` : 'Brouillon non numéroté — Attribué à la validation')} readOnly />
              </div>

              <div className={`${styles.formGroup} ${styles.libelleGroup}`}>
                <label className={styles.labelRow}>
                  <span>Libellé de l'écriture *</span>
                  <button type="button" className={`${styles.btnAuto} ${libelleAuto ? styles.btnAutoActif : ''}`}
                    onClick={() => {
                      setLibelleAuto(true)
                      setLibelle(genererLibelleIntelligent(journal, reference, lignes))
                    }}>
                    <i className="ti ti-wand" aria-hidden="true" /> Auto
                  </button>
                </label>
                <input className={styles.input} type="text"
                  placeholder={META_JOURNAL[journal]?.libelle || 'Libellé de l’écriture'}
                  value={libelle}
                  onChange={e => { setLibelle(e.target.value); setLibelleAuto(false) }} />
                {LIBELLES_PAR_JOURNAL[journal]?.length > 0 && (
                  <select className={styles.input} aria-label="Choisir un libellé type pour ce journal"
                    value="" onChange={e => {
                      setLibelle(e.target.value)
                      setLibelleAuto(false)
                    }}>
                    <option value="" disabled>Choisir un libellé type…</option>
                    {LIBELLES_PAR_JOURNAL[journal].map(({ label, texte }) => (
                      <option key={label} value={texte}>{label}</option>
                    ))}
                  </select>
                )}
              </div>

              <div className={`${styles.formGroup} ${styles.dateJustificatifGroup}`}>
                <label className={styles.label}>Date du justificatif</label>
                <label className={styles.sameDateOption}>
                  <input type="checkbox"
                    checked={datePieceAuto}
                    onChange={e => {
                      const memeDate = e.target.checked
                      setDatePieceAuto(memeDate)
                      if (memeDate) setDatePiece(date)
                    }} />
                  <span>Même date pour le justificatif</span>
                </label>
                <input className={`${styles.input} ${datePieceAuto ? styles.inputDisabled : ''}`}
                  type="date" value={datePiece}
                  disabled={datePieceAuto}
                  onChange={e => setDatePiece(e.target.value)} />
              </div>

              <div className={`${styles.formGroup} ${styles.referenceGroup}`}>
                <label className={styles.label}>Référence du justificatif</label>
                <input className={styles.input} type="text"
                  placeholder={META_JOURNAL[journal]?.ref || 'Référence du justificatif'}
                  value={reference}
                  onChange={e => majReference(e.target.value)} />
              </div>
            </div>

            {/* Alerte doublon */}
            {alerteDoublon && (
              <div className={styles.alerteDoublon}>
                <i className="ti ti-alert-triangle" aria-hidden="true" />
                <div>
                  <strong>Référence du justificatif déjà utilisée</strong> — {alerteDoublon.reference}
                  <span style={{ color: 'var(--text-tertiary)', marginLeft: 8 }}>
                    {alerteDoublon.numero_ecriture ? `${alerteDoublon.numero_ecriture} · ` : ''}{alerteDoublon.date} · {alerteDoublon.libelle}
                  </span>
                </div>
              </div>
            )}

            {/* Modèle détecté */}
            {modelePropose && (
              <div className={styles.modelePropose}>
                <div className={styles.modeleProposeLeft}>
                  <i className="ti ti-wand" aria-hidden="true" />
                  <div>
                    <strong>{modelePropose.modeles.length > 1 ? 'Plusieurs modèles possibles' : 'Modèle détecté'}</strong>
                    {modelePropose.modeles.length > 1 && <select aria-label="Opération comptable proposée"
                      value={modelePropose.modele?.id || ''} onChange={e => setModelePropose(prev => prev && ({ ...prev,
                        modele: prev.modeles.find(m => String(m.id) === e.target.value) || null }))}>
                      <option value="">Choisir l'opération...</option>
                      {modelePropose.modeles.map(m => <option key={m.id} value={m.id}>{m.libelle}</option>)}
                    </select>}
                    {modelePropose.modele && <> — {modelePropose.modele.libelle}</>}
                    <div className={styles.modeleLignes}>
                      {modelePropose.modele?.lignes.map((l, i) => (
                        <span key={i} className={styles.modeleLigneBadge}>
                          {l.compte} <span style={{ opacity: 0.6 }}>{l.sens === 'debit' ? 'D' : 'C'}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className={styles.btnAppliquer} disabled={!modelePropose.modele} onClick={handleAppliquerPropose}>
                    <i className="ti ti-check" aria-hidden="true" /> Appliquer
                  </button>
                  <button className={styles.btnIgnorer} onClick={() => setModelePropose(null)}>
                    Ignorer
                  </button>
                </div>
              </div>
            )}

            {/* Table des lignes */}
            <div className={styles.lignesSection}>
              <div className={styles.lignesHeader}>
                <span className={styles.lignesTitle}>Lignes d'écriture</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {modeleActif && modeleActif.lignes.some(lm => lm.est_tva) && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-secondary)' }}>
                      <i className="ti ti-percentage" style={{ fontSize: 13 }} aria-hidden="true" />
                      TVA
                      <select
                        aria-label="Taux TVA du modèle"
                        value={modeleActif.lignes.find(lm => lm.est_tva)?.taux_tva ?? 20}
                        onChange={e => changerTauxModele(parseFloat(e.target.value))}
                        style={{ padding: '3px 6px', borderRadius: 4, border: '0.5px solid var(--border-medium)', fontSize: 12, background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
                        {tauxTVAAvecHistorique(datePiece || date, modeleActif.lignes.find(lm => lm.est_tva)?.taux_tva ?? 20).map(t => <option key={t} value={t}>{t}%</option>)}
                      </select>
                    </div>
                  )}
                  {modeleActif && (
                    <label style={{ display: 'flex', alignItems: 'center', gap: 7, cursor: 'pointer', fontSize: 13, color: modeAssist ? 'var(--primary)' : 'var(--text-tertiary)', userSelect: 'none' }}>
                      <div
                        onClick={() => setModeAssist(p => !p)}
                        style={{
                          width: 36, height: 20, borderRadius: 10, position: 'relative', cursor: 'pointer',
                          background: modeAssist ? '#4f46e5' : '#cbd5e1',
                          transition: 'background 0.2s',
                          flexShrink: 0,
                        }}>
                        <div style={{
                          position: 'absolute', top: 3, left: modeAssist ? 18 : 3,
                          width: 14, height: 14, borderRadius: '50%', background: '#fff',
                          transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                        }} />
                      </div>
                      <i className="ti ti-sparkles" style={{ fontSize: 13 }} aria-hidden="true" />
                      Mode assist
                    </label>
                  )}
                  <button className={styles.btnAjout} onClick={ajouterLigne}>
                    <i className="ti ti-plus" aria-hidden="true" /> Ajouter une ligne
                  </button>
                </div>
              </div>

              <table className={styles.lignesTable}>
                <thead>
                  <tr>
                    <th style={{ width: 180 }}>Compte</th>
                    <th>Libellé du compte / Tiers</th>
                    <th style={{ width: 140, textAlign: 'right' }}>Débit (MAD)</th>
                    <th style={{ width: 140, textAlign: 'right' }}>Crédit (MAD)</th>
                    <th style={{ width: 36 }} />
                  </tr>
                </thead>
                <tbody>
                  {lignes.map((ligne, i) => {
                    const lmModele   = modeleActif?.lignes[i]
                    const sensModele = lmModele?.sens // 'debit' | 'credit' | undefined
                    const debitLock  = modeAssist && sensModele === 'credit'
                    const creditLock = modeAssist && sensModele === 'debit'
                    const estCompteTiers = Boolean(natureAuxiliaireCompte(ligne.compte))
                    const libelleCompte = trouverCompte(ligne.compte)?.libelle || '' 
                    return (
                    <tr key={i}>
                      <td>
                        <ChampCompte value={ligne.compte}
                          onChange={val => majLigne(i, 'compte', val)} />
                      </td>
                      <td>
                        {estCompteTiers ? (
                          <ChampTiers value={ligne.libelle}
                            onChange={val => majLigne(i, 'libelle', val)}
                            onSelect={tiers => majLigne(i, 'tiers_id', tiers?.id || null)}
                            tiersId={ligne.tiers_id}
                            compte={ligne.compte} />
                        ) : (
                          <div className={styles.libelleCompteRow}>
                            <input
                              className={styles.inputSm}
                              aria-label={ligne.libelle_personnalise ? 'Libellé personnalisé de la ligne' : 'Libellé du compte'}
                              title={!ligne.libelle_personnalise ? libelleCompte : undefined}
                              placeholder={ligne.compte ? 'Compte non trouvé dans le plan actif' : 'Choisissez un compte'}
                              value={ligne.libelle_personnalise ? ligne.libelle : (libelleCompte || ligne.libelle)}
                              readOnly={!ligne.libelle_personnalise}
                              onChange={e => majLigne(i, 'libelle', e.target.value)}
                            />
                            {libelleCompte && (
                              <button type="button" className={styles.btnLibellePerso}
                                aria-label={ligne.libelle_personnalise ? 'Reprendre le libellé du compte' : 'Personnaliser le libellé de la ligne'}
                                title={ligne.libelle_personnalise ? 'Reprendre le libellé du compte' : 'Personnaliser le libellé de la ligne'}
                                onClick={() => majLigne(i, 'libelle_personnalise', !ligne.libelle_personnalise)}>
                                <i className={ligne.libelle_personnalise ? 'ti ti-rotate-2' : 'ti ti-pencil'} aria-hidden="true" />
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                      <td data-label="Débit (MAD)">
                        <input className={`${styles.inputSm} ${styles.num}`}
                          type="text" inputMode="decimal" placeholder="0,00"
                          value={ligne.debit}
                          onChange={e => majLigne(i, 'debit', e.target.value)}
                          disabled={debitLock}
                          style={debitLock ? { opacity: 0.35, cursor: 'not-allowed', background: 'var(--bg-secondary)' } : {}} />
                      </td>
                      <td data-label="Crédit (MAD)">
                        <input className={`${styles.inputSm} ${styles.num}`}
                          type="text" inputMode="decimal" placeholder="0,00"
                          value={ligne.credit}
                          onChange={e => majLigne(i, 'credit', e.target.value)}
                          disabled={creditLock}
                          style={creditLock ? { opacity: 0.35, cursor: 'not-allowed', background: 'var(--bg-secondary)' } : {}} />
                      </td>
                      <td>
                        <button className={styles.btnSuppr}
                          onClick={() => supprimerLigne(i)}
                          disabled={lignes.length <= 2}>
                          <i className="ti ti-trash" aria-hidden="true" />
                        </button>
                      </td>
                    </tr>
                    )
                  })}
                </tbody>
                <tfoot>
                  <tr className={styles.totauxRow}>
                    <td colSpan={2}><strong>Total</strong></td>
                    <td style={{ textAlign: 'right' }}><strong>{formatMAD(totalDebit)}</strong></td>
                    <td style={{ textAlign: 'right' }}><strong>{formatMAD(totalCredit)}</strong></td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Alertes intelligentes */}
            {alertes.length > 0 && (
              <div className={styles.alertesZone}>
                {alertes.map((a, i) => (
                  <div key={i} className={`${styles.alerte} ${styles[`alerte_${a.type}`]}`}>
                    <i className={`ti ${a.icon}`} aria-hidden="true" />
                    <span>{a.message}</span>
                  </div>
                ))}
              </div>
            )}

            <div className={`${styles.equilibre} ${equilibre ? styles.equilibreOk : styles.equilibreKo}`}>
              <i className={`ti ${equilibre ? 'ti-check' : 'ti-alert-triangle'}`} aria-hidden="true" />
              {equilibre ? 'Écriture équilibrée — débit = crédit' : `Écart : ${formatMAD(ecart)} MAD`}
            </div>

            {erreur && (
              <div className={styles.erreur}>
                <i className="ti ti-alert-circle" aria-hidden="true" /> {erreur}
              </div>
            )}

            <div className={styles.actions}>
              {!edition && (
                <label style={{ display: 'flex', alignItems: 'center', gap: 7, marginRight: 'auto',
                  fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  <input type="checkbox" checked={validerDirect}
                    onChange={e => setValiderDirect(e.target.checked)} />
                  <span>
                    Valider immédiatement
                    <span style={{ display: 'block', fontSize: 10.5, color: 'var(--text-tertiary)' }}>
                      L&apos;écriture devient définitive et ne pourra plus être modifiée
                    </span>
                  </span>
                </label>
              )}
              <button className={styles.btnSec} onClick={onFermer}>Annuler</button>
              <button className={styles.btnPrim} onClick={handleSubmit}
                disabled={!valide || loading}>
                {loading ? 'Enregistrement...'
                  : <><i className="ti ti-device-floppy" aria-hidden="true" /> {edition ? 'Enregistrer les modifications' : "Enregistrer l'écriture"}</>}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
