import { useEffect, useMemo, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { API_BASE, estAdmin, peutEcrire, exercicesAPI, formatErreurAPI } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import { nombreInventaire } from '../utils/inventaireComptage.js'

const montantStock = valeur => nombreInventaire(valeur) === null ? 'À vérifier' : formatMAD(valeur)
import { PLAN_COMPTES, trouverCompte } from '../data/planComptes.js'
import styles from './GrandLivre.module.css'
import GestionExercices from '../components/GestionExercices.jsx'
import CalculProrataInventaire from '../components/CalculProrataInventaire.jsx'
import ContrepassationsOuverture from '../components/ContrepassationsOuverture.jsx'
import ReprisesProvisions from '../components/ReprisesProvisions.jsx'
import { notifier } from '../services/notifications.js'

const TYPE_UI = {
  cca: { label: "Charge constatée d'avance (CCA)", activite: '6125', fixe: '3491', aide: 'Charge déjà comptabilisée mais qui concerne l’exercice suivant.' },
  pca: { label: "Produit constaté d'avance (PCA)", activite: '7124', fixe: '4491', aide: 'Produit déjà comptabilisé mais qui concerne l’exercice suivant.' },
  fnp: { label: 'Facture non parvenue (FNP)', activite: '6125', fixe: '4417', aide: 'Charge de l’exercice dont la facture fournisseur n’est pas encore reçue.' },
  fae: { label: 'Facture à établir (FAE)', activite: '7124', fixe: '3427', aide: 'Produit acquis sur l’exercice mais pas encore facturé au client.' },
  provision_risque: { label: 'Provision pour risques et charges', activite: '6195', fixe: '1518', aide: 'Risque ou charge probable à constater à la clôture.' },
  depreciation_client: { label: 'Dépréciation créance client', activite: '61964', fixe: '3942', aide: 'Perte probable sur une créance client.' },
  depreciation_stock: { label: 'Dépréciation de stock', activite: '61961', fixe: '3911', aide: 'Perte de valeur probable sur les stocks.' },
}

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('hisabpro_token')}`, 'Content-Type': 'application/json' }
}

async function jsonOrError(res) {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message = formatErreurAPI(data.detail?.message || data.detail || data.message || `Erreur HTTP ${res.status}`)
    throw new Error(message)
  }
  return data
}

export default function Cloture() {
  const { annee, exercice, rechargerExercices } = useExercice()
  const { recharger } = useEcritures()
  const navigate = useNavigate()
  const [etat, setEtat] = useState(null)
  const [ajustements, setAjustements] = useState([])
  const [typesAjustements, setTypesAjustements] = useState({})
  const [periodes, setPeriodes] = useState([])
  const [chargement, setChargement] = useState(true)
  const [action, setAction] = useState(false)
  const [formVisible, setFormVisible] = useState(false)
  const [form, setForm] = useState({ type: 'cca', libelle: '', montant: '', compte_activite: '6125', compte_contrepartie: '3491' })
  const [apercu, setApercu] = useState(null)
  const [verification, setVerification] = useState(false)
  const [erreurApercu, setErreurApercu] = useState('')
  const generationApercu = useRef(0)
  const cleApercu = JSON.stringify([annee, form, localStorage.getItem('hisabpro_token')])
  const cleApercuCourante = useRef(cleApercu)
  cleApercuCourante.current = cleApercu
  const apercuActuel = apercu?.cle === cleApercu ? apercu : null
  useEffect(() => {
    generationApercu.current += 1
    setVerification(false); setErreurApercu('')
    return () => { generationApercu.current += 1 }
  }, [cleApercu])
  const [affectForm, setAffectForm] = useState({
    date_decision: '', date_affectation: '', reference_decision: '', organe_decision: '',
    reserve_legale: '', autres_reserves: '', report_a_nouveau: '', dividendes: ''
  })
  const [periodeForm, setPeriodeForm] = useState({ date_debut: '', date_fin: '' })
  const generationChargement = useRef(0)
  const anneeCourante = useRef(annee)
  anneeCourante.current = annee

  useEffect(() => {
    setPeriodeForm({
      date_debut: exercice?.date_debut || '',
      date_fin: exercice?.date_fin || '',
    })
  }, [exercice?.id, exercice?.date_debut, exercice?.date_fin])

  const cfg = TYPE_UI[form.type]
  const periodeFinExercice = useMemo(() => {
    const d = exercice?.date_fin
    if (!d) return null
    return periodes.find(p => d >= p.date_debut && d <= p.date_fin) || null
  }, [exercice?.date_fin, periodes])
  const periodeInventaireFermee = !!periodeFinExercice && periodeFinExercice.statut !== 'ouverte'
  const comptesActivite = useMemo(() => {
    const prefix = ['pca', 'fae'].includes(form.type) ? '7' : '6'
    return PLAN_COMPTES.filter(c => c.compte.startsWith(prefix))
  }, [form.type])
  const comptesProvision = useMemo(() => {
    const prefixes = typesAjustements[form.type]?.prefixes_contrepartie || []
    return PLAN_COMPTES.filter(c => prefixes.some(p => c.compte.startsWith(p)))
  }, [form.type, typesAjustements])

  async function chargerEtat() {
    if (annee !== anneeCourante.current) return
    const generation = ++generationChargement.current
    const token = localStorage.getItem('hisabpro_token')
    const courant = () => generation === generationChargement.current
      && annee === anneeCourante.current && token === localStorage.getItem('hisabpro_token')
    setChargement(true)
    setEtat(null); setAjustements([]); setPeriodes([]); setTypesAjustements({})
    try {
      const [rEtat, rAjust, rPeriodes, rTypes] = await Promise.all([
        fetch(`${API_BASE}/api/cloture/etat?exercice=${annee}`, { headers: authHeaders() }),
        fetch(`${API_BASE}/api/cloture/ajustements?exercice=${annee}`, { headers: authHeaders() }),
        fetch(`${API_BASE}/api/exercices/${annee}/periodes`, { headers: authHeaders() }),
        fetch(`${API_BASE}/api/cloture/types-ajustements`, { headers: authHeaders() }),
      ])
      const [etatRecu, ajustementsRecus, periodesRecues, typesRecus] = await Promise.all([
        jsonOrError(rEtat), jsonOrError(rAjust), jsonOrError(rPeriodes),
        jsonOrError(rTypes),
      ])
      if (!courant()) return
      setEtat(etatRecu)
      setAjustements(ajustementsRecus)
      setPeriodes(periodesRecues)
      setTypesAjustements(Object.fromEntries(typesRecus.map(t => [t.type, t])))
    } catch (e) {
      if (!courant()) return
      console.error(e)
      setEtat(null)
      setAjustements([])
      setPeriodes([])
      setTypesAjustements({})
    } finally { if (courant()) setChargement(false) }
  }

  useEffect(() => {
    chargerEtat()
    setFormVisible(false); setApercu(null); setErreurApercu(''); setVerification(false)
    generationApercu.current += 1
    return () => { generationChargement.current += 1 }
    /* eslint-disable-next-line */
  }, [annee])

  const affectation = etat?.affectation_resultat
  useEffect(() => {
    if (!affectation || affectation.affecte || !affectation.exercice_affectation_disponible) return
    setAffectForm(prev => ({
      ...prev,
      date_decision: prev.date_decision || affectation.date_debut || '',
      date_affectation: prev.date_affectation || affectation.date_debut || '',
      reserve_legale: affectation.type_resultat === 'benefice' && !prev.reserve_legale
        ? String(affectation.reserve_legale_minimale ?? 0)
        : prev.reserve_legale,
      report_a_nouveau: affectation.type_resultat === 'perte'
        ? String(affectation.montant_restant ?? '')
        : prev.report_a_nouveau,
    }))
  }, [
    affectation?.exercice_origine, affectation?.date_debut, affectation?.montant_restant,
    affectation?.montant_a_ventiler, affectation?.reserve_legale_minimale, affectation?.type_resultat,
    affectation?.affecte, affectation?.exercice_affectation_disponible
  ])

  function changerType(type) {
    const c = TYPE_UI[type]
    setForm({ type, libelle: '', montant: '', compte_activite: c.activite, compte_contrepartie: c.fixe })
  }

  async function verifierAjustement() {
    if (!peutEcrire()) return
    const cle = cleApercu
    const generation = ++generationApercu.current
    setVerification(true); setErreurApercu(''); setApercu(null)
    try {
      const data = await jsonOrError(await fetch(`${API_BASE}/api/cloture/ajustements/apercu?exercice=${annee}`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(form),
      }))
      if (generation !== generationApercu.current || cle !== cleApercuCourante.current) return
      setApercu({ ...data, cle })
    } catch (e) {
      if (generation === generationApercu.current && cle === cleApercuCourante.current) setErreurApercu(e.message)
    } finally { if (generation === generationApercu.current) setVerification(false) }
  }

  async function creerAjustement(e) {
    e.preventDefault()
    if (!peutEcrire() || !apercuActuel) return
    if (periodeInventaireFermee) {
      return notifier(`${periodeFinExercice.libelle} n’est pas ouverte. Ouvrez-la avant de comptabiliser les écritures d’inventaire de fin d’exercice.`)
    }
    if (!form.libelle.trim()) return notifier('Saisissez un libellé.')
    if (!Number.isFinite(Number(form.montant)) || !(Number(form.montant) > 0)) return notifier('Saisissez un montant strictement positif et fini.')
    setAction(true)
    try {
      const res = await fetch(`${API_BASE}/api/cloture/ajustements?exercice=${annee}`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({
          type: form.type,
          libelle: form.libelle.trim(),
          montant: form.montant,
          compte_activite: form.compte_activite,
          compte_contrepartie: form.compte_contrepartie,
        }),
      })
      await jsonOrError(res)
      setFormVisible(false)
      changerType('cca')
      await recharger?.()
      await chargerEtat()
    } catch (err) { notifier.erreur(err.message) }
    finally { setAction(false) }
  }

  async function supprimerAjustement(a) {
    if (!peutEcrire()) return
    if (!confirm(`Supprimer l'ajustement « ${a.libelle} » et ses écritures associées ?`)) return
    setAction(true)
    try {
      const res = await fetch(`${API_BASE}/api/cloture/ajustements/${a.id}`, { method: 'DELETE', headers: authHeaders() })
      await jsonOrError(res)
      await recharger?.()
      await chargerEtat()
    } catch (err) { notifier.erreur(err.message) }
    finally { setAction(false) }
  }

  async function genererDotations() {
    if (!peutEcrire()) return
    if (!confirm(
      `Générer les ${etat.nb_dotations_manquantes} dotation(s) aux amortissements de ${annee} ?\n\n` +
      `Une écriture sera créée au ${formatDateCourte(etat.date_fin)} pour chaque immobilisation concernée, soit ${formatMAD(etat.total_dotations_manquantes)} MAD de charges.`
    )) return
    setAction(true)
    try {
      const data = await jsonOrError(await fetch(`${API_BASE}/api/cloture/generer-dotations?exercice=${annee}`, {
        method: 'POST', headers: authHeaders(),
      }))
      notifier(`${data.nb_generees} dotation(s) générée(s) — ${formatMAD(data.total_dotation)} MAD.`)
      await recharger?.()
      await chargerEtat()
    } catch (e) { notifier.erreur(e.message) }
    finally { setAction(false) }
  }

  async function changerStatutPeriode(p) {
    if (!estAdmin()) return notifier('Action réservée à un administrateur.')
    if (etat?.est_clos) return notifier('Exercice définitivement clôturé : ses périodes ne peuvent plus être rouvertes.')
    const nouveau = p.statut === 'ouverte' ? 'fermee' : 'ouverte'
    const verbe = nouveau === 'fermee' ? 'Fermer' : 'Ouvrir'
    const detail = nouveau === 'fermee'
      ? '\n\nCette période pourra être rouverte ultérieurement par un administrateur tant que l’exercice n’est pas clôturé.'
      : '\n\nLes écritures définitives existantes restent non modifiables.'
    if (!confirm(`${verbe} la période ${p.libelle} ?${detail}`)) return
    setAction(true)
    try {
      await jsonOrError(await fetch(`${API_BASE}/api/exercices/${annee}/periodes/${p.numero}`, {
        method: 'PATCH', headers: authHeaders(), body: JSON.stringify({ statut: nouveau }),
      }))
      await chargerEtat()
    } catch (e) { notifier.erreur(e.message) }
    finally { setAction(false) }
  }

  async function ouvrirToutesPeriodes() {
    if (!estAdmin()) return notifier('Action réservée à un administrateur.')
    if (etat?.est_clos) return notifier('Exercice définitivement clôturé : ses périodes restent verrouillées.')
    if (!confirm(`Ouvrir toutes les périodes de l’exercice ${annee} ?\n\nLes écritures déjà validées resteront définitives.`)) return
    setAction(true)
    try {
      const res = await jsonOrError(await fetch(`${API_BASE}/api/exercices/${annee}/periodes/ouvrir-toutes`, {
        method: 'POST', headers: authHeaders(),
      }))
      await chargerEtat()
      notifier(`${res.nb_ouvertes} périodes ouvertes (${res.nb_modifiees} modifiées).`)
    } catch (e) { notifier.erreur(e.message) }
    finally { setAction(false) }
  }

  async function cloturer() {
    if (!peutEcrire()) return
    if (etat?.stock_cloture?.valorisation_complete === false) {
      notifier('À vérifier : la valorisation du stock est incomplète. Corrigez les sources avant de clôturer.')
      return
    }
    const resultatFinal = etat?.fiscalite_is?.resultat_net_apres_is ?? etat.resultat_net
    const impotAuto = Number(etat?.fiscalite_is?.a_comptabiliser || 0)
    if (!confirm(
      `Clôturer l'exercice ${annee} ?\n\n` +
      (impotAuto > 0 ? `• L'impôt sur les résultats (${formatMAD(impotAuto)} MAD) sera comptabilisé automatiquement avant le soldage.\n` : '') +
      `• Le résultat net (${formatMAD(resultatFinal)} MAD) sera constaté.\n` +
      `• Les soldes seront reportés en à-nouveaux sur ${annee + 1}.\n` +
      `• L'exercice ${annee} sera verrouillé définitivement.\n\n` +
      `Après clôture, toute correction devra être enregistrée sur une période ouverte ultérieure.`
    )) return
    setAction(true)
    try {
      const data = await jsonOrError(await fetch(`${API_BASE}/api/cloture/cloturer?exercice=${annee}`, {
        method: 'POST', headers: authHeaders(),
      }))
      notifier(`${data.message}\nRésultat : ${formatMAD(data.resultat_net)} MAD (${data.type_resultat})\nÀ-nouveaux générés sur ${data.a_nouveaux_sur}.`)
      await recharger?.()
      await rechargerExercices?.()
      await chargerEtat()
    } catch (e) { notifier.erreur(e.message) }
    finally { setAction(false) }
  }

  async function affecterResultat(e) {
    e.preventDefault()
    if (!affectation || affectation.affecte) return
    if (!peutEcrire()) return notifier('Cette action nécessite un rôle Administrateur ou Comptable.')

    const restant = Number(affectation.montant_restant || 0)
    const aVentiler = Number(affectation.montant_a_ventiler ?? restant)
    const valeurs = {
      reserve_legale: Number(affectForm.reserve_legale || 0),
      autres_reserves: Number(affectForm.autres_reserves || 0),
      report_a_nouveau: Number(affectForm.report_a_nouveau || 0),
      dividendes: Number(affectForm.dividendes || 0),
    }
    if (!affectForm.date_decision) return notifier('Saisissez la date de la décision d’affectation.')
    if (!affectForm.date_affectation) return notifier("Saisissez la date de comptabilisation de l'affectation.")
    if (!affectForm.reference_decision.trim()) return notifier('Saisissez la référence de la décision (PV / décision associée).')
    if (!affectForm.organe_decision.trim()) return notifier('Saisissez l’organe ayant décidé l’affectation.')
    if (affectForm.date_affectation < affectForm.date_decision) return notifier('La date de comptabilisation ne peut pas être antérieure à la décision.')
    if (Object.values(valeurs).some(v => !Number.isFinite(v) || v < 0)) return notifier("Les montants d'affectation doivent être positifs ou nuls.")

    if (affectation.type_resultat === 'benefice') {
      if (!affectation.forme_juridique_supportee) {
        return notifier('Affectation bloquée : la forme juridique n’est pas encore couverte par le moteur de réserve légale. Vérifiez les paramètres société.')
      }
      const reserveMini = Number(affectation.reserve_legale_minimale || 0)
      if (valeurs.reserve_legale + 0.01 < reserveMini) {
        return notifier(`La réserve légale doit être au minimum de ${formatMAD(reserveMini)} MAD.`)
      }
      const total = Object.values(valeurs).reduce((a, b) => a + b, 0)
      if (Math.abs(total - aVentiler) > 0.01) {
        return notifier(`Après apurement automatique des pertes antérieures, la décision doit ventiler exactement ${formatMAD(aVentiler)} MAD. Total saisi : ${formatMAD(total)} MAD.`)
      }
      const dividendesMax = Number(affectation.dividendes_max_sur_resultat ?? aVentiler)
      if (valeurs.dividendes - dividendesMax > 0.01) {
        return notifier(`Les dividendes saisis dépassent le maximum contrôlé de ${formatMAD(dividendesMax)} MAD.`)
      }
    } else if (affectation.type_resultat === 'perte') {
      if (Math.abs(valeurs.report_a_nouveau - restant) > 0.01) {
        return notifier(`La perte de ${formatMAD(restant)} MAD doit être reportée intégralement.`)
      }
      valeurs.reserve_legale = 0
      valeurs.autres_reserves = 0
      valeurs.dividendes = 0
    }

    if (!confirm(
      `Affecter définitivement le résultat ${annee} dans l'exercice ${affectation.exercice_affectation} ?\n\n` +
      `Décision : ${affectForm.reference_decision.trim()} — ${affectForm.organe_decision.trim()}\n` +
      `Date de décision : ${formatDateCourte(affectForm.date_decision)}\n` +
      `Date de comptabilisation : ${formatDateCourte(affectForm.date_affectation)}\n` +
      `Résultat d'origine : ${formatMAD(restant)} MAD`
    )) return

    setAction(true)
    try {
      const data = await jsonOrError(await fetch(`${API_BASE}/api/cloture/affecter-resultat?exercice_origine=${annee}`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({
          date_decision: affectForm.date_decision,
          date_affectation: affectForm.date_affectation,
          reference_decision: affectForm.reference_decision.trim(),
          organe_decision: affectForm.organe_decision.trim(),
          ...valeurs,
        }),
      }))
      notifier(`${data.message} Décision ${data.reference_decision}. Écriture ${data.numero_ecriture || `#${data.ecriture_id}`}.`)
      await recharger?.()
      await rechargerExercices?.()
      await chargerEtat()
    } catch (err) { notifier.erreur(err.message) }
    finally { setAction(false) }
  }

  async function enregistrerPeriodeExercice(e) {
    e.preventDefault()
    if (!estAdmin()) return notifier('Action réservée à un administrateur.')
    if (!periodeForm.date_debut || !periodeForm.date_fin) return notifier('Renseignez les deux dates de l’exercice.')
    if (new Date(periodeForm.date_fin).getFullYear() !== Number(annee)) {
      return notifier(`L’exercice ${annee} doit se clôturer en ${annee}.`)
    }
    if (!confirm(`Modifier les dates de l’exercice ${annee} ?
${periodeForm.date_debut} → ${periodeForm.date_fin}`)) return
    setAction(true)
    try {
      await exercicesAPI.modifier(annee, periodeForm)
      await rechargerExercices?.()
      await chargerEtat()
    } catch (err) { notifier.erreur(err.message) }
    finally { setAction(false) }
  }

  const stockIncomplet = etat?.stock_cloture?.valorisation_complete === false
  const stockBloquant = stockIncomplet || !!(etat?.stock_cloture?.inventaire_requis && !etat?.stock_cloture?.stock_rapproche)
  const immoBloquant = !!(etat?.immobilisations_rapprochement && !etat.immobilisations_rapprochement.rapproche)
  const fecBloquant = !!(etat?.fec_controle && !etat.fec_controle.conforme)
  const fiscaliteIS = etat?.fiscalite_is
  const isIncoherent = !!(fiscaliteIS?.applicable && !fiscaliteIS.coherente && !fiscaliteIS.absente)
  const deficitsFiscauxBloquants = !!fiscaliteIS?.deficits_a_confirmer
  const dateClotureBloquante = !!(etat && !etat.est_clos && etat.date_fin_atteinte === false)
  const blocage = !etat || etat.nb_ecritures === 0 || !etat.equilibre || etat.nb_dotations_manquantes > 0 || etat.nb_ecritures_brouillon > 0 || stockBloquant || immoBloquant || fecBloquant || isIncoherent || deficitsFiscauxBloquants || dateClotureBloquante

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Clôture de l'exercice {annee}</h1>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 24 }}>
        <GestionExercices />
        {chargement ? (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-tertiary)' }}>Chargement…</div>
        ) : !etat ? (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--red)' }}>Impossible de charger l'état de l'exercice.</div>
        ) : (
          <div style={{ maxWidth: 780, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>

            <Card>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ fontSize: 28 }}>{etat.est_clos ? '🔒' : '📖'}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>{etat.est_clos ? `Exercice ${annee} clôturé` : `Exercice ${annee} ouvert`}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {etat.est_clos
                      ? `Clôturé le ${new Date(etat.date_cloture).toLocaleDateString('fr-MA')} — clôture définitive`
                      : `${etat.nb_ecritures} écriture${etat.nb_ecritures > 1 ? 's' : ''} — ${etat.nb_ajustements_inventaire || 0} ajustement(s) d'inventaire`}
                  </div>
                </div>
              </div>
            </Card>

            <Card titre="Dates de l’exercice">
              <form onSubmit={enregistrerPeriodeExercice} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, alignItems: 'end' }}>
                <Field label="Date de début">
                  <input type="date" value={periodeForm.date_debut} disabled={etat.est_clos || !estAdmin()}
                    onChange={e => setPeriodeForm(f => ({ ...f, date_debut: e.target.value }))} style={inputStyle} />
                </Field>
                <Field label="Date de clôture">
                  <input type="date" value={periodeForm.date_fin} disabled={etat.est_clos || !estAdmin()}
                    onChange={e => setPeriodeForm(f => ({ ...f, date_fin: e.target.value }))} style={inputStyle} />
                </Field>
                {estAdmin() && !etat.est_clos && <button type="submit" disabled={action} style={btnSecondary}>Enregistrer</button>}
              </form>
              <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                L’exercice peut couvrir deux années civiles sans dépasser douze mois. Sa référence reste l’année de clôture : par exemple 01/07/2026 → 30/06/2027 = exercice 2027.
                {!estAdmin() && ' Modification réservée à un administrateur.'}
              </div>
            </Card>

            <Card titre="Périodes comptables">
              <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', marginBottom: 10 }}>
                {exercice ? `${formatDateCourte(exercice.date_debut)} — ${formatDateCourte(exercice.date_fin)}` : `Exercice ${annee}`}
                {' · '}Les périodes peuvent être rouvertes par un administrateur tant que l’exercice n’est pas définitivement clôturé.
              </div>
              {estAdmin() && !etat.est_clos && (
                <button type="button" onClick={ouvrirToutesPeriodes} disabled={action || periodes.every(p => p.statut === 'ouverte')}
                  style={{ ...btnSecondary, marginBottom: 12 }}>
                  <i className="ti ti-lock-open" style={{ marginRight: 6 }} />Ouvrir toutes les périodes
                </button>
              )}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(145px, 1fr))', gap: 7 }}>
                {periodes.map(p => {
                  const verrouillee = etat.est_clos
                  const ouverte = p.statut === 'ouverte' && !verrouillee
                  const disabled = action || verrouillee || !estAdmin()
                  const statutLabel = verrouillee
                    ? '🔒 Fermée par clôture'
                    : p.statut === 'ouverte'
                      ? '● Ouverte'
                      : p.statut === 'fermee'
                        ? '🔒 Fermée (réouvrable)'
                        : '○ À ouvrir'
                  return (
                    <button key={p.id} type="button" disabled={disabled}
                      onClick={() => changerStatutPeriode(p)}
                      title={verrouillee
                        ? 'Verrouillée par la clôture de l’exercice'
                        : (estAdmin() ? `${p.statut === 'ouverte' ? 'Fermer' : 'Ouvrir'} ${p.libelle}` : 'Action réservée à un administrateur')}
                      style={{
                        border: `0.5px solid ${ouverte ? '#B8D69B' : 'var(--border-medium)'}`,
                        background: ouverte ? '#F2F8EC' : 'var(--bg-secondary)',
                        borderRadius: 8, padding: '8px 10px', textAlign: 'left', cursor: disabled ? 'default' : 'pointer',
                        color: 'var(--text-primary)', opacity: p.statut === 'a_venir' ? .82 : 1
                      }}>
                      <div style={{ fontSize: 11.5, fontWeight: 600 }}>{p.libelle}</div>
                      <div style={{ fontSize: 10.5, marginTop: 2, color: ouverte ? '#3B6D11' : 'var(--text-tertiary)' }}>
                        {statutLabel}
                      </div>
                    </button>
                  )
                })}
              </div>
            </Card>

            <ContrepassationsOuverture exercice={annee} />
            <ReprisesProvisions exercice={annee} />

            <Card titre="Résultat de l'exercice">
              <LigneRecap label="Total des produits (classe 7)" valeur={etat.total_produits} />
              <LigneRecap label="Total des charges actuellement comptabilisées (classe 6)" valeur={etat.total_charges} />
              {fiscaliteIS?.applicable && <>
                <div style={{ borderTop: '0.5px solid var(--border-light)', margin: '4px 0' }} />
                <LigneRecap label="Résultat comptable avant IS" valeur={fiscaliteIS.resultat_comptable_avant_is} />
                <LigneRecap
                  label={`${fiscaliteIS.nature_impot === 'CM' ? 'Cotisation minimale' : 'IS'} de l'exercice (${fiscaliteIS.compte_charge_attendu || '6701/6705'})`}
                  valeur={fiscaliteIS.attendu}
                />
                {fiscaliteIS.resultat_net_apres_is != null && <LigneRecap
                  label="Résultat net après impôt"
                  valeur={fiscaliteIS.resultat_net_apres_is}
                  gras
                  couleur={fiscaliteIS.resultat_net_apres_is >= 0 ? 'var(--green)' : 'var(--red)'}
                />}
              </>}
              {!fiscaliteIS?.applicable && <>
                <div style={{ borderTop: '0.5px solid var(--border-light)', margin: '4px 0' }} />
                <LigneRecap label={`Résultat net (${etat.type_resultat})`} valeur={etat.resultat_net} gras couleur={etat.resultat_net >= 0 ? 'var(--green)' : 'var(--red)'} />
              </>}
            </Card>

            {!etat.est_clos && fiscaliteIS?.applicable && fiscaliteIS.absente && Number(fiscaliteIS.attendu || 0) > 0 && (
              <div style={{ padding: '10px 16px', borderRadius: 8, fontSize: 12.5, background: '#EAF3DE', color: '#3B6D11' }}>
                ✓ À la clôture, HisabPro comptabilisera automatiquement {formatMAD(fiscaliteIS.attendu)} MAD sur {fiscaliteIS.compte_charge_attendu} par le crédit du 4453 avant de déterminer le résultat net.
              </div>
            )}

            {!etat.est_clos && isIncoherent && (
              <WarningBox title="Impôt sur les résultats non rapproché">
                <div style={{ fontSize: 12, lineHeight: 1.55 }}>
                  Calcul fiscal attendu : <strong>{formatMAD(fiscaliteIS.attendu)} MAD</strong> sur <strong>{fiscaliteIS.compte_charge_attendu}</strong> ;
                  comptabilisé : <strong>{formatMAD(fiscaliteIS.comptabilise)} MAD</strong>. La clôture est bloquée pour éviter un double compte ou un résultat faux.
                </div>
              </WarningBox>
            )}

            {!etat.est_clos && deficitsFiscauxBloquants && (
              <WarningBox title="Imputation des déficits fiscaux à confirmer">
                <div style={{ fontSize: 12, lineHeight: 1.55, marginBottom: 10 }}>
                  Le calcul IS utilise une imputation de déficits proposée qui n'est pas encore confirmée. Confirmez-la dans Résultat fiscal / IS avant la clôture.
                </div>
                <button onClick={() => navigate('/fiscalite-is')} style={btnSecondary}>Ouvrir Résultat fiscal / IS</button>
              </WarningBox>
            )}

            {!etat.est_clos && etat.resultat_anterieur_a_reclasser && (
              <WarningBox title={`Résultat ${etat.resultat_anterieur_a_reclasser.exercice_origine} toujours en instance d’affectation`}>
                <div style={{ fontSize: 12, lineHeight: 1.55 }}>
                  À la clôture de {annee}, HisabPro reclassera automatiquement {formatMAD(etat.resultat_anterieur_a_reclasser.montant)} MAD
                  du compte <strong>{etat.resultat_anterieur_a_reclasser.compte_source}</strong> vers le compte
                  <strong> {etat.resultat_anterieur_a_reclasser.compte_cible}</strong>, afin de distinguer le résultat de l’exercice des résultats antérieurs encore en instance d’affectation.
                </div>
              </WarningBox>
            )}

            {etat.est_clos && affectation && (
              <Card titre={`Affectation du résultat ${annee}`}>
                {!affectation.exercice_affectation_disponible && !affectation.affecte ? (
                  <WarningBox title={`Exercice ${affectation.exercice_affectation} indisponible`}>
                    <div style={{ fontSize: 12, lineHeight: 1.5 }}>
                      Créez ou ouvrez un exercice comptable disponible à partir de {affectation.exercice_affectation} pour comptabiliser la décision d’affectation du résultat {annee}.
                    </div>
                  </WarningBox>
                ) : affectation.affecte ? (
                  <div style={{ display: 'grid', gap: 9 }}>
                    <div style={{ padding: '10px 12px', borderRadius: 8, fontSize: 12.5, background: '#EAF3DE', color: '#3B6D11' }}>
                      ✓ Résultat {annee} entièrement affecté dans {affectation.exercice_affectation}
                      {affectation.date_affectation ? ` le ${formatDateCourte(affectation.date_affectation)}` : ''}
                      {affectation.ecriture_affectation_id ? ` · écriture #${affectation.ecriture_affectation_id}` : ''}.
                    </div>
                    {affectation.decision_tracee ? (
                      <div style={{ padding: '10px 12px', border: '0.5px solid var(--border-light)', borderRadius: 8, fontSize: 12, lineHeight: 1.55 }}>
                        <strong>Décision :</strong> {affectation.reference_decision} · {affectation.organe_decision}
                        {affectation.date_decision ? ` · ${formatDateCourte(affectation.date_decision)}` : ''}
                      </div>
                    ) : affectation.legacy ? (
                      <WarningBox title="Affectation antérieure au patch de traçabilité 052">
                        <div style={{ fontSize: 12, lineHeight: 1.5 }}>
                          Cette affectation existe comptablement, mais aucune fiche de décision structurée n’était enregistrée par l’ancienne version.
                        </div>
                      </WarningBox>
                    ) : null}
                  </div>
                ) : affectation.type_resultat === 'nul' ? (
                  <div style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>Résultat nul : aucune écriture d'affectation n'est nécessaire.</div>
                ) : (
                  <form onSubmit={affecterResultat} style={{ display: 'grid', gap: 12 }}>
                    <div style={{ fontSize: 12, lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                      Le résultat clôturé est disponible sur le compte <strong>{affectation.compte_source}</strong>
                      {affectation.reclasse_en_instance ? ' (résultat antérieur reclassé en instance d’affectation)' : ''}.
                      Montant d’origine : <strong>{formatMAD(affectation.montant_restant)} MAD</strong>.
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 10 }}>
                      <Field label="Référence de la décision / PV">
                        <input type="text" value={affectForm.reference_decision}
                          onChange={e => setAffectForm(f => ({ ...f, reference_decision: e.target.value }))}
                          placeholder="Ex. PV-AGO-2027-01" style={inputStyle} required />
                      </Field>
                      <Field label="Organe de décision">
                        <input type="text" value={affectForm.organe_decision}
                          onChange={e => setAffectForm(f => ({ ...f, organe_decision: e.target.value }))}
                          placeholder="Ex. Assemblée générale ordinaire" style={inputStyle} required />
                      </Field>
                      <Field label="Date de la décision">
                        <input type="date" min={affectation.date_debut} max={affectation.date_fin}
                          value={affectForm.date_decision}
                          onChange={e => setAffectForm(f => ({ ...f, date_decision: e.target.value }))}
                          style={inputStyle} required />
                      </Field>
                      <Field label={`Date de comptabilisation dans ${affectation.exercice_affectation}`}>
                        <input type="date" min={affectation.date_debut} max={affectation.date_fin}
                          value={affectForm.date_affectation}
                          onChange={e => setAffectForm(f => ({ ...f, date_affectation: e.target.value }))}
                          style={inputStyle} required />
                      </Field>
                    </div>

                    {affectation.type_resultat === 'benefice' ? (
                      <>
                        {!affectation.forme_juridique_supportee ? (
                          <WarningBox title="Forme juridique non couverte par le moteur de réserve légale">
                            <div style={{ fontSize: 12, lineHeight: 1.55 }}>
                              Forme renseignée : <strong>{affectation.forme_juridique || 'non renseignée'}</strong>.
                              L’affectation bénéficiaire est bloquée tant que la règle légale correspondante n’est pas explicitement prise en charge.
                            </div>
                          </WarningBox>
                        ) : (
                          <div style={{ padding: '10px 12px', borderRadius: 8, background: 'var(--bg-secondary)', fontSize: 11.8, lineHeight: 1.6 }}>
                            <div><strong>Forme juridique :</strong> {affectation.forme_juridique} · capital : {formatMAD(affectation.capital_social)} MAD</div>
                            <div><strong>Réserve légale avant décision :</strong> {formatMAD(affectation.reserve_legale_avant)} MAD · minimum à affecter : <strong>{formatMAD(affectation.reserve_legale_minimale)} MAD</strong>{affectation.plafond_reserve_legale != null ? ` · plafond contrôlé : ${formatMAD(affectation.plafond_reserve_legale)} MAD` : ''}</div>
                            <div><strong>Référentiel appliqué :</strong> {affectation.referentiel_reserve_legale || '—'}</div>
                            {Number(affectation.pertes_a_apurer || 0) > 0 && (
                              <div><strong>Pertes antérieures apurées automatiquement :</strong> {formatMAD(affectation.pertes_a_apurer)} MAD.</div>
                            )}
                            <div><strong>Montant restant à ventiler par la décision :</strong> {formatMAD(affectation.montant_a_ventiler)} MAD · dividendes maximum contrôlés sur ce résultat : {formatMAD(affectation.dividendes_max_sur_resultat)} MAD.</div>
                          </div>
                        )}

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                          <Field label="Réserve légale (1140)">
                            <input type="number" min={affectation.reserve_legale_minimale || 0} step="0.01" value={affectForm.reserve_legale}
                              onChange={e => setAffectForm(f => ({ ...f, reserve_legale: e.target.value }))} style={inputStyle} />
                          </Field>
                          <Field label="Autres réserves (1152)">
                            <input type="number" min="0" step="0.01" value={affectForm.autres_reserves}
                              onChange={e => setAffectForm(f => ({ ...f, autres_reserves: e.target.value }))} style={inputStyle} />
                          </Field>
                          <Field label="Report à nouveau (1161)">
                            <input type="number" min="0" step="0.01" value={affectForm.report_a_nouveau}
                              onChange={e => setAffectForm(f => ({ ...f, report_a_nouveau: e.target.value }))} style={inputStyle} />
                          </Field>
                          <Field label="Dividendes à payer (4465)">
                            <input type="number" min="0" max={affectation.dividendes_max_sur_resultat ?? undefined} step="0.01" value={affectForm.dividendes}
                              onChange={e => setAffectForm(f => ({ ...f, dividendes: e.target.value }))} style={inputStyle} />
                          </Field>
                        </div>
                        <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                          HisabPro contrôle la réserve légale et les pertes antérieures à partir des données comptables disponibles. Les réserves statutaires ou contractuelles propres à la société doivent rester conformes aux statuts et à la décision de l’organe compétent.
                        </div>
                      </>
                    ) : (
                      <Field label="Perte reportée à nouveau (1169)">
                        <input type="number" min="0" step="0.01" value={affectForm.report_a_nouveau} readOnly
                          style={{ ...inputStyle, background: 'var(--bg-secondary)' }} />
                      </Field>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button type="submit" disabled={action || !peutEcrire() || (affectation.type_resultat === 'benefice' && !affectation.forme_juridique_supportee)}
                        title={!peutEcrire() ? 'Action réservée aux rôles Administrateur et Comptable' : (!affectation.forme_juridique_supportee && affectation.type_resultat === 'benefice' ? 'Forme juridique non prise en charge par le contrôle normatif' : undefined)}
                        style={{ ...btnPrimary, opacity: action || !peutEcrire() || (affectation.type_resultat === 'benefice' && !affectation.forme_juridique_supportee) ? .5 : 1 }}>
                        {action ? 'Affectation…' : `Comptabiliser l'affectation dans ${affectation.exercice_affectation}`}
                      </button>
                    </div>
                  </form>
                )}
              </Card>
            )}

            {!etat.est_clos && (
              <Card titre="Écritures d'inventaire">
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
                  Préparez ici les écritures d'inventaire au {formatDateCourte(etat.date_fin)}. Pour les CCA, PCA, FNP et FAE, une contrepassation en brouillon est préparée au lendemain de la clôture. Les provisions restent à réexaminer et à reprendre explicitement lorsqu'elles deviennent sans objet. Les écritures se valident ensuite dans le Journal.
                </div>

                {ajustements.length === 0 ? (
                  <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 8, fontSize: 12.5, color: 'var(--text-tertiary)' }}>
                    Aucun ajustement d'inventaire enregistré pour {annee}.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginBottom: 12 }}>
                    {ajustements.map(a => (
                      <div key={a.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 12, alignItems: 'center', padding: '9px 10px', border: '0.5px solid var(--border-light)', borderRadius: 8 }}>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: 12.5, fontWeight: 600 }}>{TYPE_UI[a.type]?.label || a.type} — {a.libelle}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                            {a.compte_activite} / {a.compte_contrepartie}{a.date ? ` · ${formatDateCourte(a.date)}` : ''}{a.contrepassation_date ? ` · contrepassation ${formatDateCourte(a.contrepassation_date)}` : ''} · {a.est_validee ? 'validée' : 'brouillon'}
                          </div>
                        </div>
                        <strong style={{ fontSize: 12.5 }}>{formatMAD(a.montant)} MAD</strong>
                        {peutEcrire() && <button aria-label="Supprimer l'ajustement" onClick={() => supprimerAjustement(a)} disabled={action || a.est_validee || a.contrepassation_validee}
                          title={a.est_validee || a.contrepassation_validee ? 'Écriture validée : suppression impossible, utilisez une contrepassation si nécessaire' : 'Supprimer'}
                          style={{ border: 0, background: 'transparent', cursor: 'pointer', color: 'var(--red)', opacity: a.est_validee || a.contrepassation_validee ? .35 : 1 }}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>}
                      </div>
                    ))}
                  </div>
                )}

                <CalculProrataInventaire exercice={annee} dateFin={etat.date_fin}
                  peutReprendre={peutEcrire() && !periodeInventaireFermee && !action}
                  onReprendre={(type, montant, libelle) => {
                    setForm({ type, montant, libelle, compte_activite: TYPE_UI[type].activite, compte_contrepartie: TYPE_UI[type].fixe })
                    setFormVisible(true)
                  }} />
                {periodeInventaireFermee && (
                  <div style={{ fontSize: 12, color: '#8A5A0B', background: '#FDF3E3', border: '0.5px solid #E0C088', padding: '9px 11px', borderRadius: 8, marginBottom: 10 }}>
                    <strong>{periodeFinExercice.libelle} n’est pas ouverte.</strong> Les écritures d’inventaire doivent être comptabilisées avant sa fermeture définitive.
                  </div>
                )}

                {!formVisible ? (
                  <button
                    onClick={() => setFormVisible(true)}
                    disabled={periodeInventaireFermee || !peutEcrire()}
                    title={!peutEcrire() ? 'Consultation seule' : periodeInventaireFermee ? `Ouvrez ${periodeFinExercice.libelle} avant d’ajouter un ajustement` : undefined}
                    style={{ ...btnSecondary, opacity: periodeInventaireFermee || !peutEcrire() ? .45 : 1, cursor: periodeInventaireFermee || !peutEcrire() ? 'not-allowed' : 'pointer' }}
                  >
                    <i className="ti ti-plus" style={{ marginRight: 6 }} />Ajouter un ajustement
                  </button>
                ) : (
                  <form onSubmit={creerAjustement} style={{ background: 'var(--bg-secondary)', borderRadius: 10, padding: 14, display: 'grid', gap: 10 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 10 }}>
                      <Field label="Type">
                        <select aria-label="Type d’ajustement" value={form.type} onChange={e => changerType(e.target.value)} style={inputStyle}>
                          {Object.entries(TYPE_UI).map(([k, v]) => <option value={k} key={k}>{v.label}</option>)}
                        </select>
                      </Field>
                      <Field label="Montant HT / comptable (MAD)">
                        <input type="number" min="0.01" step="0.01" value={form.montant} onChange={e => setForm(f => ({ ...f, montant: e.target.value }))} style={inputStyle} required />
                      </Field>
                    </div>
                    <Field label="Libellé / justification">
                        <input maxLength={300} value={form.libelle} onChange={e => setForm(f => ({ ...f, libelle: e.target.value }))} placeholder="Ex. Assurance payée concernant l’exercice suivant" style={inputStyle} required />
                    </Field>
                    <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)' }}>{cfg.aide}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 10 }}>
                      <Field label={['pca', 'fae'].includes(form.type) ? 'Compte de produit' : 'Compte de charge / dotation'}>
                        <input aria-label={['pca', 'fae'].includes(form.type) ? 'Compte de produit' : 'Compte de charge / dotation'} list="comptes-activite-cloture" value={form.compte_activite} onChange={e => setForm(f => ({ ...f, compte_activite: e.target.value }))} style={inputStyle} required />
                        <datalist id="comptes-activite-cloture">
                          {comptesActivite.map(c => <option key={c.compte} value={c.compte}>{c.libelle}</option>)}
                        </datalist>
                        <CompteHint numero={form.compte_activite} />
                      </Field>
                      <Field label="Compte de contrepartie">
                        {['provision_risque', 'depreciation_client', 'depreciation_stock'].includes(form.type) ? (
                          <>
                            <input aria-label="Compte de contrepartie" list="comptes-provision-cloture" value={form.compte_contrepartie} onChange={e => setForm(f => ({ ...f, compte_contrepartie: e.target.value }))} style={inputStyle} required />
                            <datalist id="comptes-provision-cloture">
                              {comptesProvision.map(c => <option key={c.compte} value={c.compte}>{c.libelle}</option>)}
                            </datalist>
                          </>
                        ) : (
                          <input aria-label="Compte de contrepartie" value={cfg.fixe} readOnly style={{ ...inputStyle, background: 'var(--bg-primary)', color: 'var(--text-secondary)' }} />
                        )}
                        <CompteHint numero={form.compte_contrepartie} />
                      </Field>
                    </div>
                    <div style={{ fontSize: 11, color: '#8A5A0B', background: '#FDF3E3', padding: '8px 10px', borderRadius: 7 }}>
                      Cet assistant génère le cut-off comptable. Il ne force aucune TVA sur FNP/FAE : la TVA reste pilotée par les pièces et les règles d'exigibilité/déduction du moteur TVA.
                    </div>
                    {erreurApercu && <div role="alert" style={{ color: 'var(--red)', fontSize: 12 }}>{erreurApercu}</div>}
                    {apercuActuel && (
                      <section aria-label="Aperçu de l'ajustement" style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 8 }}>
                        <strong style={{ fontSize: 12.5 }}>Journal OD · {formatDateCourte(apercuActuel.date)} · Brouillon</strong>
                        <div style={{ overflowX: 'auto', marginTop: 8 }}>
                          <table style={{ width: '100%', tableLayout: 'fixed', fontSize: 12, borderCollapse: 'collapse' }}>
                            <colgroup><col style={{ width: '48%' }} /><col style={{ width: '26%' }} /><col style={{ width: '26%' }} /></colgroup>
                            <thead><tr><th style={{ textAlign: 'left' }}>Compte</th><th style={{ textAlign: 'right', padding: '0 0 0 10px' }}>Débit</th><th style={{ textAlign: 'right', padding: '0 0 0 10px' }}>Crédit</th></tr></thead>
                            <tbody>{apercuActuel.lignes.map(l => <tr key={l.compte}>
                              <td style={{ padding: '7px 0', whiteSpace: 'normal', overflowWrap: 'anywhere' }}>{l.compte}<div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{l.libelle_compte || ''}</div></td>
                              <td style={{ textAlign: 'right', whiteSpace: 'nowrap', padding: '7px 0 7px 10px' }}>{formatMAD(l.debit)}</td><td style={{ textAlign: 'right', whiteSpace: 'nowrap', padding: '7px 0 7px 10px' }}>{formatMAD(l.credit)}</td>
                            </tr>)}</tbody>
                          </table>
                        </div>
                        <div style={{ fontSize: 11.5, marginTop: 8 }}>{apercuActuel.contrepassation_date
                          ? `Contrepassation inverse préparée au ${formatDateCourte(apercuActuel.contrepassation_date)}.`
                          : 'Aucune contrepassation automatique.'} Les périodes et droits sont contrôlés à nouveau lors de la création.</div>
                      </section>
                    )}
                    <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: 8 }}>
                      <button type="button" onClick={() => setFormVisible(false)} style={btnSecondary}>Annuler</button>
                      <button type="button" onClick={verifierAjustement} disabled={action || verification} style={btnSecondary}>{verification ? 'Vérification…' : 'Vérifier l’écriture'}</button>
                      <button type="submit" disabled={action || verification || !apercuActuel || !peutEcrire()} style={btnPrimary}>{action ? 'Création…' : 'Créer l’écriture'}</button>
                    </div>
                  </form>
                )}
              </Card>
            )}

            {dateClotureBloquante && (
              <WarningBox title={`Clôture disponible à partir du ${formatDateCourte(etat.date_fin)}`}>
                <div style={{ fontSize: 12, lineHeight: 1.5 }}>
                  L’exercice est encore en cours. HisabPro interdit la clôture définitive avant sa date de fin paramétrée.
                </div>
              </WarningBox>
            )}

            {!etat.est_clos && etat.nb_dotations_manquantes > 0 && (
              <WarningBox title={`${etat.nb_dotations_manquantes} dotation(s) aux amortissements non comptabilisée(s)`}>
                <div style={{ fontSize: 12, marginBottom: 10 }}>
                  Clôturer sans ces dotations surévaluerait le résultat de <strong>{formatMAD(etat.total_dotations_manquantes)} MAD</strong>.
                </div>
                <button onClick={genererDotations} disabled={action || !peutEcrire()} style={{ ...btnPrimary, background: '#8A5A0B' }}>
                  Générer les dotations {annee}
                </button>
              </WarningBox>
            )}

            {stockIncomplet && <div role="alert" style={{ padding: 14, marginBottom: 16, color: '#8A5A0B', background: 'var(--bg-secondary)', borderRadius: 8 }}><strong>À vérifier — valorisation du stock incomplète</strong>{(etat.stock_cloture.diagnostics || []).map((d, i) => <div key={`${d.article_id}-${d.champ}-${i}`}>{d.code ? `${d.code} : ` : ''}{d.message}</div>)}<div>La clôture reste bloquée tant que les sources de stock ou de coût ne sont pas qualifiées.</div><button onClick={() => navigate('/inventaire')} style={{ ...btnPrimary, marginTop: 8 }}>Vérifier l'inventaire</button></div>}
            {!etat.est_clos && etat.stock_cloture?.inventaire_requis && !etat.stock_cloture?.inventaire_valide && (
              <WarningBox title="Inventaire physique de clôture non validé">
                <div style={{ fontSize: 12, lineHeight: 1.5, marginBottom: 10 }}>
                  Le module Stocks valorise actuellement le stock à <strong>{montantStock(etat.stock_cloture.valeur_physique_brute)} MAD</strong>,
                  mais aucun comptage physique n'a été figé au {formatDateCourte(etat.stock_cloture.date_fin)}.
                </div>
                <button onClick={() => navigate('/inventaire')} style={btnSecondary}>Ouvrir l’inventaire</button>
              </WarningBox>
            )}

            {!etat.est_clos && etat.stock_cloture?.inventaire_requis && etat.stock_cloture?.inventaire_valide && !etat.stock_cloture?.stock_rapproche && (
              <WarningBox title="Stock physique non rapproché de la comptabilité">
                <div style={{ fontSize: 12, lineHeight: 1.6, marginBottom: 10 }}>
                  Stock physique brut : <strong>{montantStock(etat.stock_cloture.valeur_physique_brute)} MAD</strong><br />
                  Stock comptable brut (31xx) : <strong>{montantStock(etat.stock_cloture.valeur_comptable_brute)} MAD</strong><br />
                  Dépréciations (391x) : <strong>{montantStock(etat.stock_cloture.depreciations)} MAD</strong><br />
                  Écart brut à comptabiliser : <strong>{montantStock(etat.stock_cloture.ecart_brut)} MAD</strong>.
                </div>
                <button onClick={() => navigate('/inventaire')} style={{ ...btnPrimary, background: '#8A5A0B' }}>Rapprocher le stock</button>
              </WarningBox>
            )}

            {!etat.est_clos && etat.stock_cloture?.inventaire_requis && etat.stock_cloture?.stock_rapproche && (
              <div style={{ padding: '10px 16px', borderRadius: 8, fontSize: 12.5, background: '#EAF3DE', color: '#3B6D11' }}>
                ✓ Stock rapproché — physique brut {montantStock(etat.stock_cloture.valeur_physique_brute)} MAD, comptable brut {montantStock(etat.stock_cloture.valeur_comptable_brute)} MAD.
              </div>
            )}

            {etat.immobilisations_rapprochement && !etat.immobilisations_rapprochement.rapproche && (
              <WarningBox title="Immobilisations non rapprochées de la comptabilité">
                <div style={{ fontSize: 12, lineHeight: 1.6, marginBottom: 10 }}>
                  Valeur brute du registre : <strong>{formatMAD(etat.immobilisations_rapprochement.brut_module)} MAD</strong><br />
                  Valeur brute comptable : <strong>{formatMAD(etat.immobilisations_rapprochement.brut_comptable)} MAD</strong><br />
                  Amortissements du registre : <strong>{formatMAD(etat.immobilisations_rapprochement.amortissements_module)} MAD</strong><br />
                  Amortissements comptables : <strong>{formatMAD(etat.immobilisations_rapprochement.amortissements_comptables)} MAD</strong>.
                  {etat.est_clos && <><br />L’exercice est clôturé : toute correction doit être comptabilisée sur une période ouverte ultérieure.</>}
                </div>
                <button onClick={() => navigate('/immobilisations')} style={btnSecondary}>Ouvrir les immobilisations</button>
              </WarningBox>
            )}

            {!etat.est_clos && etat.immobilisations_rapprochement?.rapproche && (
              <div style={{ padding: '10px 16px', borderRadius: 8, fontSize: 12.5, background: '#EAF3DE', color: '#3B6D11' }}>
                ✓ Immobilisations rapprochées — brut registre et amortissements cumulés cohérents avec la comptabilité.
              </div>
            )}

            {!etat.est_clos && etat.fec_controle && !etat.fec_controle.conforme && (
              <WarningBox title={`FEC non conforme — ${etat.fec_controle.nb_bloquants} anomalie(s) bloquante(s)`}>
                <div style={{ fontSize: 12, lineHeight: 1.5, marginBottom: 8 }}>
                  La clôture est désormais impossible tant que les contrôles FEC ne sont pas conformes.
                </div>
                {etat.fec_controle.bloquants?.slice(0, 5).map((a, i) => (
                  <div key={`${a.code}-${i}`} style={{ fontSize: 11.5, padding: '3px 0' }}>
                    <strong>{a.code}</strong> · {a.message}
                  </div>
                ))}
                <button onClick={() => navigate('/journal')} style={{ ...btnSecondary, marginTop: 10 }}>Ouvrir le Journal / contrôle FEC</button>
              </WarningBox>
            )}

            {!etat.est_clos && etat.fec_controle?.conforme && (
              <div style={{ padding: '10px 16px', borderRadius: 8, fontSize: 12.5, background: '#EAF3DE', color: '#3B6D11' }}>
                ✓ FEC conforme — aucun contrôle bloquant détecté avant clôture.
              </div>
            )}

            {!etat.est_clos && etat.nb_ecritures_brouillon > 0 && (
              <WarningBox title={`${etat.nb_ecritures_brouillon} écriture(s) encore en brouillon`}>
                <div style={{ fontSize: 12, lineHeight: 1.5, marginBottom: 10 }}>
                  HisabPro ne clôture plus un exercice contenant des écritures non validées. Validez-les dans le Journal après contrôle.
                </div>
                {etat.ecritures_brouillon?.slice(0, 5).map(e => (
                  <div key={e.id} style={{ fontSize: 11.5, padding: '3px 0' }}>#{e.id} · {e.journal} · {e.libelle}</div>
                ))}
                <button onClick={() => navigate('/journal')} style={{ ...btnSecondary, marginTop: 10 }}>Ouvrir le Journal</button>
              </WarningBox>
            )}

            <div style={{ padding: '10px 16px', borderRadius: 8, fontSize: 12.5, display: 'flex', alignItems: 'center', gap: 8,
              background: etat.equilibre ? '#EAF3DE' : '#FBEAEA', color: etat.equilibre ? '#3B6D11' : '#A32D2D' }}>
              <span>{etat.equilibre ? '✓' : '⚠️'}</span>
              <span>{etat.equilibre ? 'Balance équilibrée.' : `Comptabilité déséquilibrée (écart ${formatMAD(etat.ecart)} MAD).`}</span>
            </div>

            {!etat.est_clos && etat.apercu_a_nouveaux?.length > 0 && (
              <details style={{ background: 'var(--bg-primary)', border: '0.5px solid var(--border-light)', borderRadius: 12, overflow: 'hidden' }}>
                <summary style={{ padding: '12px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                  Aperçu des à-nouveaux sur {annee + 1} ({etat.apercu_a_nouveaux.length} lignes)
                </summary>
                <div className={styles.apercuAnContenu}>
                  <div className={styles.apercuAnTable} role="table" aria-label={`À-nouveaux ${annee + 1}`}>
                    <div role="rowgroup">
                      <div className={`${styles.apercuAnRow} ${styles.apercuAnHeader}`} role="row">
                        <span role="columnheader">Compte</span>
                        <span role="columnheader">Libellé</span>
                        <span role="columnheader">Débit</span>
                        <span role="columnheader">Crédit</span>
                      </div>
                    </div>
                    <div role="rowgroup">
                      {etat.apercu_a_nouveaux.map((l, i) => <div className={styles.apercuAnRow} role="row" key={i}>
                        <span className={styles.apercuAnCompte} role="cell" style={{ fontWeight: l.resultat ? 700 : 400 }}>{l.compte}</span>
                        <span className={styles.apercuAnLibelle} role="cell">
                          {l.resultat ? "Résultat de l'exercice" : (trouverCompte(l.compte)?.libelle || '—')}
                          {l.compte_auxiliaire_snapshot && <small style={{ display: 'block', marginTop: 3, overflowWrap: 'anywhere' }}>
                            {l.compte_auxiliaire_snapshot} · {l.libelle_auxiliaire_snapshot}
                          </small>}
                        </span>
                        <span className={styles.apercuAnDebit} role="cell"><span className={styles.apercuAnMontantLabel}>Débit</span>{l.debit ? formatMAD(l.debit) : '—'}</span>
                        <span className={styles.apercuAnCredit} role="cell"><span className={styles.apercuAnMontantLabel}>Crédit</span>{l.credit ? formatMAD(l.credit) : '—'}</span>
                      </div>)}
                      <div className={`${styles.apercuAnRow} ${styles.apercuAnTotal}`} role="row">
                        <span className={styles.apercuAnCompte} role="cell">Total</span>
                        <span className={styles.apercuAnLibelle} role="cell" aria-label="Total des mouvements" />
                        <span className={styles.apercuAnDebit} role="cell"><span className={styles.apercuAnMontantLabel}>Débit</span>{formatMAD(etat.total_an_debit)}</span>
                        <span className={styles.apercuAnCredit} role="cell"><span className={styles.apercuAnMontantLabel}>Crédit</span>{formatMAD(etat.total_an_credit)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </details>
            )}

            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 8, paddingBottom: 20 }}>
              {etat.est_clos ? (
                <div style={{ ...btnSecondary, cursor: 'default', opacity: .78 }}>
                  <i className="ti ti-lock" style={{ marginRight: 6 }} />Exercice {annee} clôturé définitivement
                </div>
              ) : (
                <button onClick={cloturer} disabled={action || blocage || !peutEcrire()}
                  title={dateClotureBloquante ? `Clôture disponible à partir du ${formatDateCourte(etat.date_fin)}` : (blocage ? 'Corrigez les contrôles bloquants avant la clôture' : undefined)}
                  style={{ ...btnPrimary, opacity: blocage ? .45 : 1, cursor: blocage ? 'not-allowed' : 'pointer' }}>
                  <i className="ti ti-lock" style={{ marginRight: 6 }} />{action ? 'Clôture…' : `Clôturer l'exercice ${annee}`}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function formatDateCourte(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

function Card({ titre, children }) {
  return <div style={{ background: 'var(--bg-primary)', border: '0.5px solid var(--border-light)', borderRadius: 12, overflow: 'hidden' }}>
    {titre && <div style={{ padding: '12px 20px', borderBottom: '0.5px solid var(--border-light)', fontSize: 13, fontWeight: 600 }}>{titre}</div>}
    <div style={{ padding: titre ? '12px 20px' : '16px 20px' }}>{children}</div>
  </div>
}

function WarningBox({ title, children }) {
  return <div style={{ padding: '14px 18px', borderRadius: 10, background: '#FDF3E3', border: '0.5px solid #E0C088', color: '#6F4707' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13.5, fontWeight: 600, marginBottom: 7 }}><i className="ti ti-alert-triangle" />{title}</div>
    {children}
  </div>
}

function Field({ label, children }) {
  return <label style={{ display: 'grid', gap: 5, fontSize: 11.5, color: 'var(--text-secondary)' }}><span>{label}</span>{children}</label>
}

function CompteHint({ numero }) {
  const c = trouverCompte(numero)
  return <span style={{ fontSize: 10.5, minHeight: 14, color: 'var(--text-tertiary)' }}>{c?.libelle || ''}</span>
}

function LigneRecap({ label, valeur, gras, couleur }) {
  return <div style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', fontSize: gras ? 14 : 13 }}>
    <span style={{ fontWeight: gras ? 600 : 400, color: couleur || 'var(--text-secondary)' }}>{label}</span>
    <span style={{ fontWeight: gras ? 700 : 500, color: couleur || 'var(--text-primary)' }}>{formatMAD(valeur)} MAD</span>
  </div>
}

const inputStyle = { width: '100%', height: 36, borderRadius: 7, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)', padding: '0 10px', fontSize: 12.5, boxSizing: 'border-box' }
const btnPrimary = { padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--blue)', color: '#fff', cursor: 'pointer', fontSize: 12.5, fontWeight: 500 }
const btnSecondary = { padding: '8px 14px', borderRadius: 8, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12.5, fontWeight: 500 }
