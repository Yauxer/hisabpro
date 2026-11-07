import { useEffect, useMemo, useRef, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { fiscaliteAPI, peutEcrire } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from './FiscaliteIS.module.css'

const TYPE_LABEL = { reintegration: 'Réintégration', deduction: 'Déduction' }
const CATEGORIES_RETRAITEMENT = {
  amendes_penalites: 'Amendes, pénalités et majorations',
  liberalites: 'Libéralités',
  cadeaux_publicitaires: 'Cadeaux publicitaires',
  dons: 'Dons',
  charges_non_justifiees: 'Charges non justifiées',
  paiements_especes: 'Paiements en espèces au-delà des limites',
  amortissement_vehicule: 'Amortissement / location de véhicule de tourisme',
  amortissements_non_deductibles: 'Amortissements non déductibles',
  provisions_non_deductibles: 'Provisions à contrôler',
  interets_comptes_courants_associes: "Intérêts de comptes courants d'associés",
  produits_participation_abattement: 'Produits de participation — abattement de 100%',
  reprises_provisions_taxees: 'Reprises de provisions antérieurement taxées',
  produits_exoneres: 'Produits exonérés / non imposables',
  charges_liees_produits_exoneres: 'Charges liées à des produits exonérés',
  autre: 'Autre retraitement',
}

const n = v => Number(v || 0)
const mad = v => `${formatMAD(n(v))} MAD`
const pct = v => `${n(v).toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 3 })} %`

export default function FiscaliteIS() {
  const { annee } = useExercice()
  const [data, setData] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [sauvegarde, setSauvegarde] = useState(false)
  const [params, setParams] = useState(null)
  const [nouveau, setNouveau] = useState({
    type: 'reintegration', categorie: 'autre', libelle: '', montant: '', compte_source: '', reference: '', commentaire: '',
  })
  const [nouveauDeficit, setNouveauDeficit] = useState({
    exercice_origine: '', montant_ordinaire: '', montant_amortissements: '', commentaire: '',
  })
  const [acompteDrafts, setAcompteDrafts] = useState({})
  const saisiesAcomptes = useRef({})
  const [creditDraft, setCreditDraft] = useState({ type: 'pprf', montant: '', montant_deja_impute_acomptes: '', date_retenue: '', reference: '', commentaire: '' })
  const [cssDraft, setCssDraft] = useState({ montant_verse: '', date_versement: '', reference_paiement: '', commentaire: '' })

  const editable = peutEcrire()

  async function charger() {
    setChargement(true); setErreur('')
    try {
      const d = await fiscaliteAPI.situationIS(annee)
      setData(d)
      setParams({
        ...d.parametres,
        deficit_reportable_disponible: n(d.parametres.deficit_reportable_disponible),
        taux_is_force: d.parametres.taux_is_force == null ? '' : n(d.parametres.taux_is_force),
        cm_base_exclue: n(d.parametres.cm_base_exclue),
        cm_base_taux_reduit_015: n(d.parametres.cm_base_taux_reduit_015),
        acomptes_reference_forcee: d.parametres.acomptes_reference_forcee == null ? '' : n(d.parametres.acomptes_reference_forcee),
        css_benefice_reference_forcee: d.parametres.css_benefice_reference_forcee == null ? '' : n(d.parametres.css_benefice_reference_forcee),
      })
    } catch (e) {
      setErreur(e.message || 'Impossible de charger le calcul fiscal.')
    } finally { setChargement(false) }
  }

  useEffect(() => {
    saisiesAcomptes.current = {}
    setAcompteDrafts({})
    charger()
  }, [annee]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    const drafts = {}
    for (const a of (data?.acomptes?.acomptes || [])) {
      drafts[a.numero] = {
        montant_verse: n(a.montant_verse) || '',
        date_versement: a.date_versement || '',
        reference_paiement: a.reference_paiement || '',
        dispense: !!a.dispense,
        reference_dispense: a.reference_dispense || '',
        commentaire: a.commentaire || '',
      }
    }
    if (data?.liquidation?.confirmee) saisiesAcomptes.current = {}
    setAcompteDrafts(precedents => {
      const suivants = { ...drafts }
      for (const numero of Object.keys(drafts)) {
        if (saisiesAcomptes.current[`${annee}:${numero}`]?.modifie && precedents[numero]) {
          suivants[numero] = precedents[numero]
        }
      }
      return suivants
    })
    const p = data?.contribution_solidarite?.paiement
    setCssDraft({
      montant_verse: p ? n(p.montant_verse) : '',
      date_versement: p?.date_versement || '',
      reference_paiement: p?.reference_paiement || '',
      commentaire: p?.commentaire || '',
    })
  }, [data])

  const manuels = useMemo(() => (data?.retraitements || []).filter(r => !r.automatique), [data])
  const automatiques = useMemo(() => (data?.retraitements || []).filter(r => r.automatique), [data])
  const aConfirmer = useMemo(() => data?.retraitements_a_confirmer || [], [data])
  const categoriesRetraitement = data?.categories_retraitement || CATEGORIES_RETRAITEMENT

  function preparerDepuisCandidat(r) {
    if (!editable) return
    setNouveau({
      type: r.type_suggere || r.type || 'reintegration',
      categorie: r.categorie || 'autre',
      libelle: r.libelle || '',
      montant: r.montant_detecte == null ? '' : n(r.montant_detecte),
      compte_source: r.compte_source || '',
      reference: r.reference || '',
      commentaire: r.commentaire || '',
    })
  }

  async function sauverParametres() {
    if (!params || !editable) return
    setSauvegarde(true); setErreur('')
    try {
      const payload = {
        ...params,
        deficit_reportable_disponible: Number(params.deficit_reportable_disponible || 0),
        taux_is_force: params.taux_is_force === '' ? null : Number(params.taux_is_force),
        justification_taux_force: params.taux_is_force === '' ? null : params.justification_taux_force,
        cm_base_exclue: Number(params.cm_base_exclue || 0),
        cm_base_taux_reduit_015: Number(params.cm_base_taux_reduit_015 || 0),
        acomptes_reference_forcee: params.acomptes_reference_forcee === '' ? null : Number(params.acomptes_reference_forcee),
        acomptes_justification_reference_forcee: params.acomptes_reference_forcee === '' ? null : params.acomptes_justification_reference_forcee,
        css_benefice_reference_forcee: params.css_benefice_reference_forcee === '' ? null : Number(params.css_benefice_reference_forcee),
        css_justification_reference_forcee: params.css_benefice_reference_forcee === '' ? null : params.css_justification_reference_forcee,
      }
      await fiscaliteAPI.enregistrerParametresIS(annee, payload)
      await charger()
    } catch (e) { setErreur(e.message) }
    finally { setSauvegarde(false) }
  }

  async function ajouter(e) {
    e.preventDefault()
    if (!editable) return
    if (!nouveau.libelle.trim() || Number(nouveau.montant) <= 0) {
      setErreur('Renseigne un libellé et un montant supérieur à zéro.')
      return
    }
    try {
      await fiscaliteAPI.ajouterRetraitement(annee, {
        ...nouveau,
        montant: Number(nouveau.montant),
        compte_source: nouveau.compte_source || null,
        reference: nouveau.reference || null,
        commentaire: nouveau.commentaire || null,
      })
      setNouveau({ type: 'reintegration', categorie: 'autre', libelle: '', montant: '', compte_source: '', reference: '', commentaire: '' })
      await charger()
    } catch (e2) { setErreur(e2.message) }
  }

  async function supprimer(id) {
    if (!editable || !id) return
    try { await fiscaliteAPI.supprimerRetraitement(id); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function ajouterDeficit(e) {
    e.preventDefault()
    if (!editable) return
    const origine = Number(nouveauDeficit.exercice_origine)
    const ord = Number(nouveauDeficit.montant_ordinaire || 0)
    const amort = Number(nouveauDeficit.montant_amortissements || 0)
    if (!origine || origine >= annee) { setErreur(`Le millésime doit être antérieur à l'exercice ${annee}.`); return }
    if (ord + amort <= 0) { setErreur('Renseigne un montant de déficit positif.'); return }
    try {
      await fiscaliteAPI.ajouterDeficit({
        exercice_origine: origine, montant_ordinaire: ord, montant_amortissements: amort,
        commentaire: nouveauDeficit.commentaire || null,
      })
      setNouveauDeficit({ exercice_origine: '', montant_ordinaire: '', montant_amortissements: '', commentaire: '' })
      await charger()
    } catch (e2) { setErreur(e2.message) }
  }

  async function supprimerDeficit(id) {
    if (!editable || !id) return
    if (!window.confirm('Supprimer ce millésime de déficit fiscal ?')) return
    try { await fiscaliteAPI.supprimerDeficit(id); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function enregistrerDeficitGenere() {
    if (!editable) return
    try { await fiscaliteAPI.enregistrerDeficitGenere(annee); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function confirmerImputation() {
    if (!editable) return
    try { await fiscaliteAPI.confirmerImputationDeficits(annee); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function annulerImputation() {
    if (!editable) return
    if (!window.confirm(`Annuler l'imputation de déficits enregistrée pour ${annee} ?`)) return
    try { await fiscaliteAPI.annulerImputationDeficits(annee); await charger() }
    catch (e) { setErreur(e.message) }
  }

  function majAcompte(numero, champ, valeur) {
    const cle = `${annee}:${numero}`
    saisiesAcomptes.current[cle] = { version: (saisiesAcomptes.current[cle]?.version || 0) + 1, modifie: true }
    setAcompteDrafts(d => ({ ...d, [numero]: { ...(d[numero] || {}), [champ]: valeur } }))
  }

  function confirmerSaisieAcompte(cle, version) {
    if (saisiesAcomptes.current[cle]?.version === version) {
      saisiesAcomptes.current[cle] = { version, modifie: false }
    }
  }

  async function sauverAcompte(numero) {
    if (!editable) return
    const d = acompteDrafts[numero] || {}
    const cle = `${annee}:${numero}`
    const version = saisiesAcomptes.current[cle]?.version || 0
    try {
      await fiscaliteAPI.enregistrerAcompteIS(annee, numero, {
        montant_verse: d.dispense ? 0 : Number(d.montant_verse || 0),
        date_versement: d.dispense ? null : (d.date_versement || null),
        reference_paiement: d.dispense ? null : (d.reference_paiement || null),
        dispense: !!d.dispense,
        reference_dispense: d.dispense ? (d.reference_dispense || null) : null,
        commentaire: d.commentaire || null,
      })
      confirmerSaisieAcompte(cle, version)
      await charger()
    } catch (e) { setErreur(e.message) }
  }

  async function supprimerAcompte(numero) {
    if (!editable) return
    const cle = `${annee}:${numero}`
    const version = saisiesAcomptes.current[cle]?.version || 0
    try {
      await fiscaliteAPI.supprimerAcompteIS(annee, numero)
      confirmerSaisieAcompte(cle, version)
      await charger()
    }
    catch (e) { setErreur(e.message) }
  }

  async function confirmerLiquidation() {
    if (!editable || data?.liquidation?.confirmee) return
    const reference = data?.acomptes?.reference || {}
    if (!reference.disponible && !reference.non_applicable) {
      setErreur(`Référence des acomptes ${annee} indisponible : confirme la liquidation fiscale ${annee - 1} ou renseigne une référence annuelle justifiée avant de confirmer la liquidation IS.`)
      return
    }
    if (!window.confirm(`Confirmer définitivement la liquidation IS ${annee} ? Cette photographie fiscale deviendra immuable.`)) return
    try { await fiscaliteAPI.confirmerLiquidationIS(annee); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function ajouterCreditIS(e) {
    e.preventDefault()
    if (!editable || data?.liquidation?.confirmee) return
    if (Number(creditDraft.montant || 0) <= 0 || !creditDraft.reference.trim()) {
      setErreur('Renseigne un montant positif et une référence justificative pour le crédit IS.')
      return
    }
    try {
      await fiscaliteAPI.ajouterCreditIS(annee, {
        type: creditDraft.type,
        montant: Number(creditDraft.montant || 0),
        montant_deja_impute_acomptes: Number(creditDraft.montant_deja_impute_acomptes || 0),
        date_retenue: creditDraft.date_retenue || null,
        reference: creditDraft.reference,
        commentaire: creditDraft.commentaire || null,
      })
      setCreditDraft({ type: 'pprf', montant: '', montant_deja_impute_acomptes: '', date_retenue: '', reference: '', commentaire: '' })
      await charger()
    } catch (e2) { setErreur(e2.message) }
  }

  async function supprimerCreditIS(id) {
    if (!editable || data?.liquidation?.confirmee) return
    try { await fiscaliteAPI.supprimerCreditIS(annee, id); await charger() }
    catch (e) { setErreur(e.message) }
  }

  async function sauverCSS() {
    if (!editable) return
    if (Number(cssDraft.montant_verse || 0) <= 0 || !cssDraft.date_versement || !cssDraft.reference_paiement.trim()) {
      setErreur('Renseigne le montant, la date et la référence du paiement CSS.')
      return
    }
    try {
      await fiscaliteAPI.enregistrerPaiementCSS(annee, {
        montant_verse: Number(cssDraft.montant_verse),
        date_versement: cssDraft.date_versement,
        reference_paiement: cssDraft.reference_paiement,
        commentaire: cssDraft.commentaire || null,
      })
      await charger()
    } catch (e) { setErreur(e.message) }
  }

  async function supprimerCSS() {
    if (!editable) return
    try { await fiscaliteAPI.supprimerPaiementCSS(annee); await charger() }
    catch (e) { setErreur(e.message) }
  }

  if (chargement && !data) return <div className={styles.center}>Chargement du calcul fiscal…</div>

  const c = data?.calcul || {}
  const cm = data?.cotisation_minimale || {}
  const liquidationLive = data?.liquidation || {}
  const snapshotDetail = liquidationLive.snapshot?.detail || {}
  const liquidation = liquidationLive.confirmee && snapshotDetail.liquidation
    ? { ...liquidationLive, ...snapshotDetail.liquidation }
    : liquidationLive
  const acompteSituationLive = data?.acomptes || {}
  const acompteSituation = liquidationLive.confirmee && Array.isArray(snapshotDetail.acomptes)
    ? { ...acompteSituationLive, ...(snapshotDetail.totaux_acomptes || {}), reference: snapshotDetail.reference_acomptes || acompteSituationLive.reference, acomptes: snapshotDetail.acomptes }
    : acompteSituationLive
  const lignesAcomptes = acompteSituation.acomptes || []
  const referenceAcomptesBloquante = !!acompteSituation.reference && !acompteSituation.reference.disponible && !acompteSituation.reference.non_applicable
  const creditsISLive = data?.credits_is || {}
  const creditsIS = liquidationLive.confirmee && snapshotDetail.credits_is
    ? { ...creditsISLive, ...snapshotDetail.credits_is }
    : creditsISLive
  const lignesCreditsIS = creditsIS.lignes || []
  const css = data?.contribution_solidarite || {}
  const src = data?.source_comptable || {}
  const deficits = data?.deficits || {}
  const inventaireDeficits = deficits.inventaire || []
  const deficitCourantEnregistre = inventaireDeficits.find(d => Number(d.exercice_origine) === Number(annee))

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Résultat fiscal & IS</h1>
          <span className={styles.pageSubtitle}>Passage du résultat comptable au bénéfice fiscal imposable — Maroc</span>
        </div>
        <div className={styles.exercice}><i className="ti ti-calendar" /> Exercice {annee}</div>
      </div>

      <div className={styles.content}>
        {erreur && <div className={styles.erreur}><i className="ti ti-alert-triangle" /> {erreur}</div>}
        {(data?.alertes || []).map((a, i) => <div className={styles.alerte} key={i}><i className="ti ti-info-circle" /> {a}</div>)}

        <div className={styles.kpis}>
          <Kpi label="Résultat comptable avant IS" value={mad(c.resultat_comptable_avant_is)} />
          <Kpi label="Résultat fiscal avant déficit" value={mad(c.resultat_fiscal_avant_deficit)} />
          <Kpi label="Bénéfice fiscal imposable" value={mad(c.benefice_fiscal_imposable)} />
          <Kpi label="IS théorique" value={mad(c.is_theorique)} />
          <Kpi label={`Impôt dû avant acomptes · ${liquidation.nature_impot_du || '—'}`} value={mad(liquidation.impot_du_avant_acomptes)} accent />
          <Kpi label={`CSS ${annee}`} value={css.disponible ? mad(css.montant_du) : 'Référence manquante'} />
        </div>

        <div className={styles.grid2}>
          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div><strong>Paramètres IS, CM & CSS</strong><span>Historisés pour l'exercice {annee}</span></div>
              <button className={styles.btnPrimary} onClick={sauverParametres} disabled={!editable || sauvegarde}>
                {sauvegarde ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
            {params && <div className={styles.formGrid}>
              <label className={styles.fieldWide}>Catégorie fiscale
                <select value={params.categorie_is} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, categorie_is: e.target.value }))}>
                  {Object.entries(data?.categories_is || {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </label>
              {params.categorie_is !== 'droit_commun' && <label className={styles.fieldWide}>Justification du régime particulier
                <input value={params.justification_regime || ''} disabled={!editable}
                  placeholder="Statut CFC/ZAI, convention, référence légale, période d’exonération…"
                  onChange={e => setParams(p => ({ ...p, justification_regime: e.target.value }))} />
              </label>}
              {annee >= 2023 && annee <= 2026 && <label className={styles.checkboxField}>
                <input type="checkbox" checked={!!params.maintien_taux_35_transition} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, maintien_taux_35_transition: e.target.checked }))} />
                <span>Seuil de 100 M MAD déjà atteint pendant la transition 2023–2026</span>
              </label>}
              <label>Taux dérogatoire (optionnel)
                <input type="number" min="0" max="100" step="0.001" placeholder="Automatique"
                  value={params.taux_is_force ?? ''} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, taux_is_force: e.target.value }))} />
              </label>
              {params.taux_is_force !== '' && <label>Justification du taux dérogatoire
                <input value={params.justification_taux_force || ''} disabled={!editable}
                  placeholder="Référence légale / régime particulier"
                  onChange={e => setParams(p => ({ ...p, justification_taux_force: e.target.value }))} />
              </label>}

              <div className={styles.formSubTitle}>Cotisation minimale — CGI art. 144</div>
              <label>Base CM exclue (optionnel)
                <input type="number" min="0" step="0.01" value={params.cm_base_exclue ?? 0} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, cm_base_exclue: e.target.value }))} />
              </label>
              <label>Base éligible au taux réduit 0,15 %
                <input type="number" min="0" step="0.01" value={params.cm_base_taux_reduit_015 ?? 0} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, cm_base_taux_reduit_015: e.target.value }))} />
              </label>
              {n(params.cm_base_exclue) > 0 && <label className={styles.fieldWide}>Justification de la base CM exclue
                <input value={params.cm_justification_base_exclue || ''} disabled={!editable}
                  placeholder="Référence légale / régime / détail des opérations exclues"
                  onChange={e => setParams(p => ({ ...p, cm_justification_base_exclue: e.target.value }))} />
              </label>}
              {n(params.cm_base_taux_reduit_015) > 0 && <label className={styles.fieldWide}>Justification du taux réduit 0,15 %
                <input value={params.cm_justification_taux_reduit || ''} disabled={!editable}
                  placeholder="Nature des ventes éligibles et justificatif de la ventilation"
                  onChange={e => setParams(p => ({ ...p, cm_justification_taux_reduit: e.target.value }))} />
              </label>}
              <label className={styles.checkboxField}>
                <input type="checkbox" checked={!!params.cm_exoneration_totale} disabled={!editable}
                  onChange={e => setParams(p => ({ ...p, cm_exoneration_totale: e.target.checked }))} />
                <span>Exonération totale de cotisation minimale pour cet exercice</span>
              </label>
              {params.cm_exoneration_totale && <label className={styles.fieldWide}>Justification de l'exonération CM
                <input value={params.cm_justification_exoneration || ''} disabled={!editable}
                  placeholder="Ex. début d'exploitation : 36 mois sous conditions / autre référence légale"
                  onChange={e => setParams(p => ({ ...p, cm_justification_exoneration: e.target.value }))} />
              </label>}
              <label className={styles.checkboxField}>
                <input type="checkbox" checked={!!params.cm_minimum_3000_exonere} disabled={!editable || !!params.cm_exoneration_totale}
                  onChange={e => setParams(p => ({ ...p, cm_minimum_3000_exonere: e.target.checked }))} />
                <span>Minimum de perception de 3 000 MAD non applicable</span>
              </label>
              {params.cm_minimum_3000_exonere && !params.cm_exoneration_totale && <label className={styles.fieldWide}>Justification de la neutralisation du minimum
                <input value={params.cm_justification_minimum_exonere || ''} disabled={!editable}
                  placeholder="Référence légale / situation particulière"
                  onChange={e => setParams(p => ({ ...p, cm_justification_minimum_exonere: e.target.value }))} />
              </label>}

              <div className={styles.formSubTitle}>Acomptes provisionnels — reprise / exception</div>
              <label>Référence annuelle forcée (optionnel)
                <input type="number" min="0" step="0.01" placeholder="Automatique depuis N-1 confirmée"
                  value={params.acomptes_reference_forcee ?? ''} disabled={!editable || !!liquidation.confirmee}
                  onChange={e => setParams(p => ({ ...p, acomptes_reference_forcee: e.target.value }))} />
              </label>
              {params.acomptes_reference_forcee !== '' && <label className={styles.fieldWide}>Justification de la référence forcée
                <input value={params.acomptes_justification_reference_forcee || ''} disabled={!editable || !!liquidation.confirmee}
                  placeholder="Reprise de dossier, avis d'imposition N-1, déclaration fiscale de référence…"
                  onChange={e => setParams(p => ({ ...p, acomptes_justification_reference_forcee: e.target.value }))} />
              </label>}

              {annee >= 2023 && annee <= 2028 && <>
                <div className={styles.formSubTitle}>Contribution sociale de solidarité — CGI art. 267 à 273</div>
                <label>Bénéfice net fiscal de référence forcé (optionnel)
                  <input type="number" min="0" step="0.01" placeholder={`Automatique depuis ${annee - 1}`}
                    value={params.css_benefice_reference_forcee ?? ''} disabled={!editable}
                    onChange={e => setParams(p => ({ ...p, css_benefice_reference_forcee: e.target.value }))} />
                </label>
                {params.css_benefice_reference_forcee !== '' && <label className={styles.fieldWide}>Justification de la référence CSS forcée
                  <input value={params.css_justification_reference_forcee || ''} disabled={!editable}
                    placeholder="Reprise de dossier / déclaration fiscale du dernier exercice clos…"
                    onChange={e => setParams(p => ({ ...p, css_justification_reference_forcee: e.target.value }))} />
                </label>}
                <label className={styles.checkboxField}>
                  <input type="checkbox" checked={!!params.css_exoneration_permanente} disabled={!editable}
                    onChange={e => setParams(p => ({ ...p, css_exoneration_permanente: e.target.checked }))} />
                  <span>Société exonérée de manière permanente de l'IS — exclusion de la CSS</span>
                </label>
                {params.css_exoneration_permanente && <label className={styles.fieldWide}>Justification de l'exonération permanente CSS
                  <input value={params.css_justification_exoneration || ''} disabled={!editable}
                    placeholder="Référence légale / nature de l'exonération permanente"
                    onChange={e => setParams(p => ({ ...p, css_justification_exoneration: e.target.value }))} />
                </label>}
              </>}
            </div>}
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}><div><strong>Calcul de l'IS</strong><span>{c.libelle_taux || '—'}</span></div></div>
            <div className={styles.calcul}>
              <Ligne label="Résultat comptable avant IS" value={c.resultat_comptable_avant_is} />
              <Ligne sign="+" label="Réintégrations fiscales" value={c.reintegrations} />
              <Ligne sign="−" label="Déductions fiscales" value={c.deductions} />
              <Ligne total label="Résultat fiscal avant déficit" value={c.resultat_fiscal_avant_deficit} />
              <Ligne sign="−" label="Déficit antérieur imputé" value={c.deficit_impute} />
              <Ligne total label="Bénéfice fiscal imposable" value={c.benefice_fiscal_imposable} />
              <div className={styles.tauxRow}><span>Taux IS appliqué</span><strong>{pct(c.taux_is)}</strong></div>
              <div className={styles.isFinal}><span>IS théorique</span><strong>{mad(c.is_theorique)}</strong></div>
            </div>
            <div className={styles.legal}>{c.source_taux}{c.taux_provisoire ? ' — estimation à confirmer pour cet exercice.' : ''}</div>
          </section>
        </div>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Cotisation minimale</strong>
              <span>CGI art. 144 — comparaison avec l'IS théorique</span>
            </div>
          </div>
          <div className={styles.cmGrid}>
            <div className={styles.cmBreakdown}>
              <Ligne label="Base CM comptable brute" value={cm.base_comptable_brute} />
              <Ligne sign="−" label="Base exclue justifiée" value={cm.base_exclue} />
              <Ligne total label="Base CM après exclusions" value={cm.base_apres_exclusion} />
              <Ligne label="Base au taux réduit de 0,15 %" value={cm.base_taux_reduit_015} />
              <Ligne label="Base au taux standard de 0,25 %" value={cm.base_taux_standard_025} />
            </div>
            <div className={styles.cmBreakdown}>
              <div className={styles.tauxRow}><span>CM sur base à 0,15 %</span><strong>{mad(cm.cm_part_reduite)}</strong></div>
              <div className={styles.tauxRow}><span>CM sur base à 0,25 %</span><strong>{mad(cm.cm_part_standard)}</strong></div>
              <Ligne total label="CM calculée" value={cm.cm_calculee} />
              <Ligne label="Minimum de perception" value={cm.minimum_3000} />
              <div className={styles.cmFinal}><span>CM exigible</span><strong>{mad(cm.cm_exigible)}</strong></div>
            </div>
          </div>
          <div className={styles.cmCompare}>
            <div><span>IS théorique</span><strong>{mad(liquidation.is_theorique)}</strong></div>
            <div><span>CM exigible</span><strong>{mad(liquidation.cm_exigible)}</strong></div>
            <div className={styles.cmDue}><span>Impôt dû avant acomptes · {liquidation.nature_impot_du || '—'}</span><strong>{mad(liquidation.impot_du_avant_acomptes)}</strong></div>
          </div>
          <div className={styles.cmLegal}>
            <strong>Base comptable détectée :</strong> CA et autres produits d'exploitation, produits financiers, subventions et dons.
            Les variations de stocks, immobilisations produites, reprises/transferts et cessions d'immobilisations ne sont pas incluses automatiquement.
            {(cm.produits_taux_reduit_015 || []).length > 0 && <span> Taux 0,15 % : {cm.produits_taux_reduit_015.join(', ')}.</span>}
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Contribution sociale de solidarité — {annee}</strong>
              <span>CGI art. 267 à 273 — bénéfice net fiscal du dernier exercice clos</span>
            </div>
            <span className={`${styles.acompteStatus} ${styles[`css_${css.statut}`] || ''}`}>
              {({solde:'Soldée',partiel:'Partielle',a_payer:'À payer',en_retard:'En retard',non_due:'Non due',reference_manquante:'Réf. manquante',hors_periode:'Hors période'})[css.statut] || css.statut || '—'}
            </span>
          </div>
          <div className={styles.cssGrid}>
            <div><span>Exercice de référence</span><strong>{css.exercice_reference || annee - 1}</strong></div>
            <div><span>Bénéfice net fiscal retenu</span><strong>{css.disponible ? mad(css.base) : 'Indisponible'}</strong></div>
            <div><span>Taux CSS</span><strong>{pct(css.taux)}</strong></div>
            <div><span>Contribution due</span><strong>{mad(css.montant_du)}</strong></div>
            <div><span>Échéance</span><strong>{css.date_echeance || '—'}</strong></div>
            <div><span>Reste à payer</span><strong>{mad(css.reste_a_payer)}</strong></div>
          </div>
          <div className={styles.cssSource}>
            <strong>Source :</strong> {css.libelle_source || '—'}
            {css.exoneree_permanente && <span> · Exonération permanente appliquée.</span>}
          </div>
          {css.applicable && css.disponible && n(css.montant_du) > 0 && <div className={styles.cssPayment}>
            <input type="number" min="0" step="0.01" placeholder="Montant versé" value={cssDraft.montant_verse} disabled={!editable}
              onChange={e => setCssDraft(v => ({ ...v, montant_verse: e.target.value }))} />
            <input type="date" value={cssDraft.date_versement} disabled={!editable}
              onChange={e => setCssDraft(v => ({ ...v, date_versement: e.target.value }))} />
            <input placeholder="Référence paiement / déclaration" value={cssDraft.reference_paiement} disabled={!editable}
              onChange={e => setCssDraft(v => ({ ...v, reference_paiement: e.target.value }))} />
            <input placeholder="Commentaire (optionnel)" value={cssDraft.commentaire} disabled={!editable}
              onChange={e => setCssDraft(v => ({ ...v, commentaire: e.target.value }))} />
            {editable && <button type="button" className={styles.btnPrimary} onClick={sauverCSS}>Enregistrer</button>}
            {editable && css.paiement && <button type="button" className={styles.btnSecondary} onClick={supprimerCSS}>Effacer</button>}
          </div>}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Retenues & crédits imputables sur l'IS</strong>
              <span>Ordre de liquidation : PPRF → rémunérations à des tiers → autres crédits → acomptes</span>
            </div>
          </div>
          <div className={styles.creditStats}>
            <div><span>Total enregistré</span><strong>{mad(creditsIS.total_montant)}</strong></div>
            <div><span>Déjà imputé sur acomptes</span><strong>{mad(creditsIS.total_deja_impute_acomptes)}</strong></div>
            <div><span>Disponible à la liquidation</span><strong>{mad(creditsIS.total_disponible_liquidation)}</strong></div>
          </div>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead><tr><th>Nature</th><th>Date</th><th>Référence</th><th>Montant</th><th>Déjà imputé acomptes</th><th>Solde liquidation</th><th /></tr></thead>
              <tbody>
                {lignesCreditsIS.length === 0 && <tr><td colSpan="7" className={styles.empty}>Aucune retenue / crédit IS enregistré.</td></tr>}
                {lignesCreditsIS.map(cr => <tr key={cr.id}>
                  <td><strong>{cr.libelle_type || creditsIS.types?.[cr.type] || cr.type}</strong></td>
                  <td>{cr.date_retenue || '—'}</td>
                  <td>{cr.reference}</td>
                  <td className={styles.amount}>{mad(cr.montant)}</td>
                  <td className={styles.amount}>{mad(cr.montant_deja_impute_acomptes)}</td>
                  <td className={styles.amount}><strong>{mad(cr.solde_liquidation)}</strong></td>
                  <td>{editable && !liquidation.confirmee && <button type="button" className={styles.iconBtn} onClick={() => supprimerCreditIS(cr.id)} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>}</td>
                </tr>)}
              </tbody>
            </table>
          </div>
          {editable && !liquidation.confirmee && <form className={styles.creditForm} onSubmit={ajouterCreditIS}>
            <select value={creditDraft.type} onChange={e => setCreditDraft(v => ({ ...v, type: e.target.value }))}>
              {Object.entries(creditsIS.types || {pprf:'PPRF',retenue_tiers:'Retenue tiers',autre:'Autre crédit'}).map(([k,v]) => <option value={k} key={k}>{v}</option>)}
            </select>
            <input type="number" min="0" step="0.01" placeholder="Montant retenu" value={creditDraft.montant} onChange={e => setCreditDraft(v => ({ ...v, montant: e.target.value }))} />
            <input type="number" min="0" step="0.01" placeholder="Déjà imputé acomptes" value={creditDraft.montant_deja_impute_acomptes} onChange={e => setCreditDraft(v => ({ ...v, montant_deja_impute_acomptes: e.target.value }))} />
            <input type="date" value={creditDraft.date_retenue} onChange={e => setCreditDraft(v => ({ ...v, date_retenue: e.target.value }))} />
            <input placeholder="Référence justificative" value={creditDraft.reference} onChange={e => setCreditDraft(v => ({ ...v, reference: e.target.value }))} />
            <button className={styles.btnPrimary}>Ajouter</button>
          </form>}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Acomptes provisionnels & liquidation</strong>
              <span>CGI art. 170 — quatre échéances de 25 % et liquidation annuelle</span>
            </div>
            {liquidation.confirmee ?
              <span className={styles.confirmedBadge}><i className="ti ti-lock" /> Liquidation confirmée</span> :
              editable && <button type="button" className={styles.btnPrimary} onClick={confirmerLiquidation} disabled={referenceAcomptesBloquante} title={referenceAcomptesBloquante ? `Confirme la liquidation fiscale ${annee - 1} ou renseigne une référence annuelle justifiée.` : ''}>Confirmer la liquidation</button>}
          </div>

          {referenceAcomptesBloquante && !liquidation.confirmee && <div className={styles.liquidationGuard}>
            <i className="ti ti-lock" />
            <span><strong>Liquidation bloquée.</strong> La référence des acomptes est indisponible : confirme la liquidation fiscale {annee - 1} ou renseigne une référence annuelle justifiée.</span>
          </div>}

          <div className={styles.acompteReference}>
            <div><span>Exercice de référence</span><strong>{acompteSituation.reference?.non_applicable ? 'Aucun' : (acompteSituation.reference?.exercice_reference || annee - 1)}</strong></div>
            <div><span>Base annuelle des acomptes</span><strong>{acompteSituation.reference?.non_applicable ? '—' : mad(acompteSituation.reference?.montant_annuel)}</strong></div>
            <div><span>Source</span><strong>{acompteSituation.reference?.libelle_source || 'Référence indisponible'}</strong></div>
            <div><span>Excédent N-1 à imputer</span><strong>{mad(acompteSituation.credit_n_1_initial)}</strong></div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead><tr><th>#</th><th>Échéance</th><th>Dû</th><th>Crédit N-1</th><th>Retenues imputées</th><th>Net à verser</th><th>Versement / dispense</th><th>Statut</th><th /></tr></thead>
              <tbody>
                {lignesAcomptes.map(a => {
                  const d = acompteDrafts[a.numero] || {}
                  const acompteNonApplicable = a.statut === 'non_applicable'
                  return <tr key={a.numero}>
                    <td><strong>{a.numero}</strong></td>
                    <td>{a.date_echeance || '—'}</td>
                    <td className={styles.amount}>{mad(a.montant_du)}</td>
                    <td className={styles.amount}>{mad(a.credit_n_1_impute)}</td>
                    <td className={styles.amount}>{mad(a.credit_ras_impute)}</td>
                    <td className={styles.amount}><strong>{mad(a.montant_net_a_verser)}</strong></td>
                    <td>
                      {acompteNonApplicable ? <span className={styles.acompteNAHint}>Aucun acompte à saisir</span> :
                        <div className={styles.acompteEdit}>
                          <label className={styles.acompteDispense}><input type="checkbox" checked={!!d.dispense} disabled={!editable || liquidation.confirmee} onChange={e => majAcompte(a.numero, 'dispense', e.target.checked)} /> Dispense</label>
                          {!d.dispense ? <>
                            <input type="number" min="0" step="0.01" placeholder="Montant" value={d.montant_verse ?? ''} disabled={!editable || liquidation.confirmee} onChange={e => majAcompte(a.numero, 'montant_verse', e.target.value)} />
                            <input type="date" value={d.date_versement || ''} disabled={!editable || liquidation.confirmee} onChange={e => majAcompte(a.numero, 'date_versement', e.target.value)} />
                            <input placeholder="Réf. paiement" value={d.reference_paiement || ''} disabled={!editable || liquidation.confirmee} onChange={e => majAcompte(a.numero, 'reference_paiement', e.target.value)} />
                          </> : <input placeholder="Réf. déclaration de dispense" value={d.reference_dispense || ''} disabled={!editable || liquidation.confirmee} onChange={e => majAcompte(a.numero, 'reference_dispense', e.target.value)} />}
                        </div>}
                    </td>
                    <td>
                      <div className={styles.acompteStatusCell}>
                        <span className={`${styles.acompteStatus} ${styles[`acompte_${a.statut}`] || ''}`}>{({solde:'Soldé',partiel:'Partiel',partiel_en_retard:'Partiel — en retard',a_venir:'À venir',en_retard:'En retard',dispense:'Dispensé',reference_manquante:'Réf. manquante',non_applicable:'Non applicable'})[a.statut] || a.statut}</span>
                        {['partiel', 'partiel_en_retard'].includes(a.statut) && n(a.reste_a_couvrir) > 0 && <span className={styles.acompteReste}>Reste : {mad(a.reste_a_couvrir)}</span>}
                      </div>
                    </td>
                    <td>{editable && !liquidation.confirmee && !acompteNonApplicable && <div className={styles.rowActions}><button type="button" className={styles.iconBtn} title="Enregistrer" onClick={() => sauverAcompte(a.numero)}><i className="ti ti-device-floppy" /><span className="libelle-action" aria-hidden="true">Enregistrer</span></button>{(n(a.montant_verse) > 0 || a.dispense) && <button type="button" className={styles.iconBtn} title="Effacer" onClick={() => supprimerAcompte(a.numero)}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Effacer</span></button>}</div>}</td>
                  </tr>
                })}
              </tbody>
            </table>
          </div>

          <div className={styles.liquidationGrid}>
            <div><span>Impôt dû avant imputations</span><strong>{mad(liquidation.impot_du_avant_acomptes)}</strong></div>
            <div><span>Retenues / crédits IS disponibles</span><strong>{mad(liquidation.credits_is_disponibles_liquidation)}</strong></div>
            <div><span>Acomptes versés</span><strong>{mad(liquidation.acomptes_verses)}</strong></div>
            <div><span>Crédit N-1 imputé sur acomptes</span><strong>{mad(liquidation.credit_n_1_impute_sur_acomptes)}</strong></div>
            <div><span>Retenues déjà imputées sur acomptes</span><strong>{mad(creditsIS.total_deja_impute_acomptes)}</strong></div>
            <div className={styles.liquidationDue}><span>{n(liquidation.solde_a_payer) > 0 ? 'Solde IS à payer' : 'Excédent total'}</span><strong>{mad(n(liquidation.solde_a_payer) > 0 ? liquidation.solde_a_payer : liquidation.excedent_total)}</strong></div>
          </div>
          {n(liquidation.excedent_total) > 0 && <div className={styles.liquidationExcess}>
            Excédent retenues/crédits : <strong>{mad(liquidation.excedent_credits_is)}</strong> · Excédent acomptes/crédit N-1 : <strong>{mad(liquidation.excedent_acomptes)}</strong>.
          </div>}
          {liquidation.snapshot && <div className={styles.liquidationSnapshot}>
            <i className="ti ti-lock" /> Photographie confirmée le {String(liquidation.snapshot.date_confirmation || '').replace('T', ' ').slice(0, 16)} — impôt dû {mad(liquidation.snapshot.impot_du)}, crédits IS {mad(liquidation.snapshot.credits_is_imputables)}, acomptes / crédits déjà imputés {mad(liquidation.snapshot.acomptes_imputables)}, solde {mad(liquidation.snapshot.solde_a_payer)}.{liquidation.snapshot.detail && <> Les {liquidation.snapshot.detail.acomptes?.length || 0} échéances, leurs références de paiement et les retenues/crédits affichés ci-dessus proviennent du snapshot figé.</>}
          </div>}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Déficits fiscaux reportables</strong>
              <span>Suivi par millésime — CGI art. 12</span>
            </div>
          </div>

          {n(deficits.legacy_non_millesime) > 0 && <div className={styles.legacyWarn}>
            Ancien solde non millésimé : <strong>{mad(deficits.legacy_non_millesime)}</strong>.
            Ventile-le par année d'origine ci-dessous ; il n'est plus utilisé dans le calcul tant que son délai de report n'est pas vérifiable.
          </div>}

          <div className={styles.deficitStats}>
            <div><span>Ordinaire disponible</span><strong>{mad(deficits.disponible_ordinaire)}</strong><small>Report limité à N+4</small></div>
            <div><span>Amortissements disponibles</span><strong>{mad(deficits.disponible_amortissements)}</strong><small>Sans limite de 4 exercices</small></div>
            <div><span>Imputation proposée {annee}</span><strong>{mad(deficits.total_propose)}</strong><small>{deficits.confirmation_a_jour ? 'Confirmée' : 'À confirmer'}</small></div>
            <div><span>Ordinaire expiré</span><strong>{mad(deficits.ordinaire_expire)}</strong><small>Non imputable en {annee}</small></div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead><tr><th>Millésime</th><th>Ordinaire initial</th><th>Amort. initial</th><th>Solde ordinaire</th><th>Solde amort.</th><th>Échéance ordinaire</th><th>Source</th><th /></tr></thead>
              <tbody>
                {inventaireDeficits.length === 0 && <tr><td colSpan="8" className={styles.empty}>Aucun déficit fiscal antérieur enregistré.</td></tr>}
                {inventaireDeficits.map(d => <tr key={d.id}>
                  <td><strong>{d.exercice_origine}</strong></td>
                  <td className={styles.amount}>{mad(d.montant_ordinaire_initial ?? d.montant_ordinaire)}</td>
                  <td className={styles.amount}>{mad(d.montant_amortissements_initial ?? d.montant_amortissements)}</td>
                  <td className={styles.amount}>
                    {mad(d.ordinaire_restant_avant_exercice)}
                    {n(d.ordinaire_expire) > 0 && <small className={styles.expired}>Expiré</small>}
                  </td>
                  <td className={styles.amount}>{mad(d.amortissements_restants_avant_exercice)}</td>
                  <td>{Number(d.exercice_origine) + 4}</td>
                  <td><span className={styles.sourceBadge}>{d.source === 'calcul' ? 'HisabPro' : 'Manuel'}</span></td>
                  <td>{editable && n(d.montant_confirme_exercice) === 0 && <button type="button" className={styles.iconBtn} onClick={() => supprimerDeficit(d.id)} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>}</td>
                </tr>)}
              </tbody>
            </table>
          </div>

          {n(deficits.total_propose) > 0 && <div className={styles.imputationBox}>
            <div className={styles.imputationHead}>
              <div><strong>Proposition d'imputation {annee}</strong><span>Priorité aux déficits ordinaires les plus proches de l'expiration.</span></div>
              <div className={styles.imputationActions}>
                {deficits.confirmation_a_jour ? <span className={styles.confirmedBadge}><i className="ti ti-check" /> Confirmée</span> :
                  editable && <button type="button" className={styles.btnPrimary} onClick={confirmerImputation}>{n(deficits.total_confirme) > 0 ? 'Reconfirmer' : 'Confirmer l’imputation'}</button>}
                {editable && n(deficits.total_confirme) > 0 && <button type="button" className={styles.btnSecondary} onClick={annulerImputation}>Annuler</button>}
              </div>
            </div>
            <div className={styles.imputationList}>
              {(deficits.proposition || []).map((p, i) => <div key={`${p.deficit_id}-${p.nature}-${i}`}>
                <span>{p.exercice_origine} · {p.nature === 'ordinaire' ? `Ordinaire (échéance ${p.expiration})` : 'Fraction amortissements'}</span>
                <strong>{mad(p.montant)}</strong>
              </div>)}
            </div>
          </div>}

          {n(deficits.deficit_genere_propose?.montant_total) > 0 && <div className={styles.generatedDeficit}>
            <div>
              <strong>Déficit fiscal généré par {annee} : {mad(deficits.deficit_genere_propose.montant_total)}</strong>
              <span>Ordinaire : {mad(deficits.deficit_genere_propose.part_ordinaire)} · Fraction amortissements : {mad(deficits.deficit_genere_propose.part_amortissements)}</span>
              <small>Amortissements fiscalement retenus pour la ventilation : {mad(deficits.amortissements_deductibles)}</small>
            </div>
            {editable && <button type="button" className={styles.btnPrimary} onClick={enregistrerDeficitGenere}>
              {deficitCourantEnregistre?.source === 'calcul' ? 'Mettre à jour le millésime' : `Enregistrer le déficit ${annee}`}
            </button>}
          </div>}

          {editable && <form className={styles.deficitForm} onSubmit={ajouterDeficit}>
            <div><label>Exercice d'origine<input type="number" min="1900" max={annee - 1} placeholder={String(annee - 1)} value={nouveauDeficit.exercice_origine} onChange={e => setNouveauDeficit(v => ({ ...v, exercice_origine: e.target.value }))} /></label></div>
            <div><label>Part ordinaire<input type="number" min="0" step="0.01" placeholder="0,00" value={nouveauDeficit.montant_ordinaire} onChange={e => setNouveauDeficit(v => ({ ...v, montant_ordinaire: e.target.value }))} /></label></div>
            <div><label>Part amortissements<input type="number" min="0" step="0.01" placeholder="0,00" value={nouveauDeficit.montant_amortissements} onChange={e => setNouveauDeficit(v => ({ ...v, montant_amortissements: e.target.value }))} /></label></div>
            <div className={styles.deficitComment}><label>Commentaire<input placeholder="Origine / justificatif du solde" value={nouveauDeficit.commentaire} onChange={e => setNouveauDeficit(v => ({ ...v, commentaire: e.target.value }))} /></label></div>
            <button className={styles.btnSecondary}>Ajouter un millésime antérieur</button>
          </form>}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <strong>Retraitements fiscaux</strong>
              <span>{automatiques.length} automatique(s) · {aConfirmer.length} à confirmer · {manuels.length} manuel(s)</span>
            </div>
          </div>
          {automatiques.length > 0 && <div className={styles.autoBlock}>
            <div className={styles.autoTitle}><i className="ti ti-sparkles" /> Retraitements automatiques — inclus dans le calcul</div>
            {automatiques.map((r, i) => <RetraitementAuto key={`a${i}`} r={r} />)}
          </div>}
          {aConfirmer.length > 0 && <div className={styles.confirmBlock}>
            <div className={styles.confirmTitle}><i className="ti ti-alert-circle" /> Éléments à confirmer — aucun impact fiscal tant qu'ils ne sont pas validés</div>
            <div className={styles.confirmList}>
              {aConfirmer.map((r, i) => <RetraitementCandidat key={`c${i}`} r={r} editable={editable} onPrepare={() => preparerDepuisCandidat(r)} />)}
            </div>
          </div>}
          <div className={styles.manualTitle}>Retraitements manuels confirmés</div>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead><tr><th>Type</th><th>Catégorie / libellé</th><th>Compte</th><th>Référence</th><th>Montant</th><th /></tr></thead>
              <tbody>
                {manuels.length === 0 && <tr><td colSpan="6" className={styles.empty}>Aucun retraitement manuel.</td></tr>}
                {manuels.map(r => <RetraitementRow key={r.id} r={r} onDelete={() => supprimer(r.id)} editable={editable} />)}
              </tbody>
            </table>
          </div>

          <form className={styles.addForm} onSubmit={ajouter}>
            <select value={nouveau.type} disabled={!editable} onChange={e => setNouveau(v => ({ ...v, type: e.target.value }))}>
              <option value="reintegration">Réintégration</option><option value="deduction">Déduction</option>
            </select>
            <select value={nouveau.categorie} disabled={!editable} onChange={e => setNouveau(v => ({ ...v, categorie: e.target.value }))}>
              {Object.entries(categoriesRetraitement).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <input placeholder="Libellé du retraitement" value={nouveau.libelle} disabled={!editable}
              onChange={e => setNouveau(v => ({ ...v, libelle: e.target.value }))} />
            <input placeholder="Compte (optionnel)" value={nouveau.compte_source} disabled={!editable}
              onChange={e => setNouveau(v => ({ ...v, compte_source: e.target.value }))} />
            <input type="number" min="0" step="0.01" placeholder="Montant MAD" value={nouveau.montant} disabled={!editable}
              onChange={e => setNouveau(v => ({ ...v, montant: e.target.value }))} />
            <button className={styles.btnPrimary} disabled={!editable}>Ajouter</button>
          </form>
          {(data?.checklist_fiscale || []).length > 0 && <div className={styles.checklist}>
            <div className={styles.checklistTitle}>Contrôles à documenter avant liquidation définitive de l'IS</div>
            <div className={styles.checklistGrid}>
              {(data?.checklist_fiscale || []).map(item => <div className={styles.checkItem} key={item.code}>
                <i className="ti ti-clipboard-check" />
                <div><strong>{item.libelle}</strong><span>{item.regle}</span><small>{item.reference}</small></div>
              </div>)}
            </div>
          </div>}
        </section>

        <section className={styles.sourceCard}>
          <div><strong>Source comptable</strong><span>{src.nb_ecritures_validees || 0} écriture(s) validée(s) · {src.nb_brouillons_exclus || 0} brouillon(s) exclu(s)</span></div>
          <div><span>Produits</span><strong>{mad(src.produits_comptables)}</strong></div>
          <div><span>Charges hors IS</span><strong>{mad(src.charges_hors_is)}</strong></div>
          <div><span>IS déjà comptabilisé (classe 67)</span><strong>{mad(src.is_deja_comptabilise)}</strong></div>
        </section>
      </div>
    </div>
  )
}

function Kpi({ label, value, accent }) {
  return <div className={`${styles.kpi} ${accent ? styles.kpiAccent : ''}`}><span>{label}</span><strong>{value}</strong></div>
}
function Ligne({ label, value, sign, total }) {
  return <div className={`${styles.calcRow} ${total ? styles.calcTotal : ''}`}><span>{sign && <b className={styles.sign}>{sign}</b>}{label}</span><strong>{mad(value)}</strong></div>
}
function RetraitementAuto({ r }) {
  return <div className={styles.autoRow}>
    <span className={`${styles.badge} ${styles.reintegration}`}>{TYPE_LABEL[r.type]}</span>
    <span className={styles.autoLabel}>{r.libelle}</span>
    <span className={styles.code}>{r.compte_source}</span>
    <span>{r.reference}</span>
    <strong>{mad(r.montant)}</strong>
  </div>
}
function RetraitementCandidat({ r, editable, onPrepare }) {
  return <div className={styles.confirmRow}>
    <div className={styles.confirmMain}>
      <div className={styles.confirmBadges}>
        <span className={styles.badgeConfirm}>À confirmer</span>
        <span className={`${styles.badge} ${r.type_suggere === 'deduction' ? styles.deduction : styles.reintegration}`}>{TYPE_LABEL[r.type_suggere]}</span>
      </div>
      <strong>{r.libelle}</strong>
      <span>{r.commentaire}</span>
      {(r.questions || []).length > 0 && <ul>{r.questions.map((q, i) => <li key={i}>{q}</li>)}</ul>}
      <small>{r.reference}</small>
    </div>
    <div className={styles.confirmSide}>
      <span className={styles.code}>{r.compte_source || '—'}</span>
      <strong>{r.montant_detecte == null ? 'Montant à déterminer' : mad(r.montant_detecte)}</strong>
      {editable && <button type="button" className={styles.btnSecondary} onClick={onPrepare}>Préremplir</button>}
    </div>
  </div>
}

function RetraitementRow({ r, onDelete, editable }) {
  return <tr>
    <td><span className={`${styles.badge} ${r.type === 'reintegration' ? styles.reintegration : styles.deduction}`}>{TYPE_LABEL[r.type]}</span></td>
    <td><strong>{CATEGORIES_RETRAITEMENT[r.categorie] || r.categorie}</strong><small>{r.libelle}</small></td>
    <td><span className={styles.code}>{r.compte_source || '—'}</span></td>
    <td>{r.reference || '—'}</td>
    <td className={styles.amount}>{mad(r.montant)}</td>
    <td>{editable && <button className={styles.iconBtn} type="button" onClick={onDelete} title="Supprimer"><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>}</td>
  </tr>
}
