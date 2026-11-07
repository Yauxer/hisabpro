import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { API_BASE, getToken, formatErreurAPI, rapprochementAPI } from '../services/api.js'
import Modal from '../components/Modal.jsx'
import { formatMAD as formatMADConnu, formatDate } from '../data/donnees.js'
import styles from './RapprochementBancaire.module.css'
import { decoderCsv, lignesDepuisTableauReleve, tableauDepuisCsv } from '../utils/releveImport.js'
import { dateLocaleISO } from '../utils/formUtils.js'

const COMPTES_BANQUE = [
  { compte: '5141', label: 'Banque principale (5141)' },
  { compte: '5142', label: 'Banque 2 (5142)' },
  { compte: '5143', label: 'Banque 3 (5143)' },
]

const formatMAD = valeur => valeur == null || !Number.isFinite(Number(valeur)) ? 'À vérifier' : formatMADConnu(valeur)
const montantReleveExploitable = ligne => ligne.montant != null && ligne.montant_valide !== false
  && Number.isFinite(Number(ligne.montant)) && Number(ligne.montant) > 0
function sommeReleve(lignes, avecSens = false) {
  if (lignes.some(l => !montantReleveExploitable(l))) return null
  return lignes.reduce((s, l) => s + Number(l.montant) * (avecSens && l.sens !== 'credit' ? -1 : 1), 0)
}

async function fetchBanques() {
  const token = localStorage.getItem('hisabpro_token')
  const res = await fetch(`${API_BASE}/api/banques`, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Erreur' })); throw new Error(formatErreurAPI(e.detail)) }
  return res.json()
}

function joursEcart(a, b) {
  if (!a || !b) return 999999
  const da = new Date(`${a}T00:00:00`)
  const db = new Date(`${b}T00:00:00`)
  return Math.abs(Math.round((da - db) / 86400000))
}

function contientRecherche(valeurs, recherche) {
  const q = recherche.trim().toLowerCase()
  if (!q) return true
  return valeurs.filter(Boolean).join(' ').toLowerCase().includes(q)
}

export default function RapprochementBancaire() {
  const { annee, exercice, chargementExercices } = useExercice()
  const { societe, chargement: chargementSociete } = useModules()
  const [compteBancaire, setCompteBancaire] = useState([])
  const [compteSelectionne, setCompteSelectionne] = useState('5141')
  const [dateDebut, setDateDebut] = useState(() => exercice?.date_debut || `${annee}-01-01`)
  const [dateFin, setDateFin] = useState(() => exercice?.date_fin || `${annee}-12-31`)
  const [soldeInitial, setSoldeInitial] = useState('')
  const [soldeFinal, setSoldeFinal] = useState('')
  const [soldeInitialSuggere, setSoldeInitialSuggere] = useState(false)
  const [soldeComptableFinal, setSoldeComptableFinal] = useState(0)
  const [lignesReleve, setLignesReleve] = useState([])
  const [ecrituresCompte, setEcrituresCompte] = useState([])
  const [ventilations, setVentilations] = useState([])
  const [propositions, setPropositions] = useState(null)
  const [selectionPropositions, setSelectionPropositions] = useState([])
  const [chargementPropositions, setChargementPropositions] = useState(false)
  const [envoiPropositions, setEnvoiPropositions] = useState(false)
  const [erreurPropositions, setErreurPropositions] = useState('')
  const versionPropositions = useRef(0)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [message, setMessage] = useState('')
  const [lectureSeuleAPI, setLectureSeuleAPI] = useState(false)
  const [nouvelleOp, setNouvelleOp] = useState({ date: dateLocaleISO(), libelle: '', montant: '', sens: 'debit' })

  const [rechercheCompta, setRechercheCompta] = useState('')
  const [filtreCompta, setFiltreCompta] = useState('toutes')
  const [rechercheReleve, setRechercheReleve] = useState('')
  const [filtreReleve, setFiltreReleve] = useState('toutes')

  const [editionId, setEditionId] = useState(null)
  const [edition, setEdition] = useState({ date: '', libelle: '', montant: '', sens: 'debit' })

  const [onglet, setOnglet] = useState('manuel')
  const [lignesImport, setLignesImport] = useState([])
  const [loadingImport, setLoadingImport] = useState(false)
  const [erreurImport, setErreurImport] = useState('')
  const inputRef = useRef(null)
  const periodeContexte = useRef({ annee, societeId: societe?.id ?? null, saisie: false })
  const versionLecture = useRef(0)
  const scopeLecture = JSON.stringify([societe?.id ?? null, compteSelectionne, dateDebut, dateFin])
  const scopeCourant = useRef(scopeLecture)
  scopeCourant.current = scopeLecture

  const lectureSeule = exercice?.statut === 'cloture' || lectureSeuleAPI
  const tokenPropositions = getToken()
  const contextePropositions = JSON.stringify([annee, societe?.id ?? null, compteSelectionne, dateDebut, dateFin, tokenPropositions, lectureSeule])
  const contextePropositionsCourant = useRef(contextePropositions)
  contextePropositionsCourant.current = contextePropositions
  useEffect(() => {
    versionPropositions.current += 1
    setPropositions(null); setSelectionPropositions([]); setErreurPropositions('')
    setChargementPropositions(false); setEnvoiPropositions(false)
  }, [contextePropositions])
  const dateMin = exercice?.date_debut || `${annee}-01-01`
  const dateMax = exercice?.date_fin || `${annee}-12-31`

  useEffect(() => {
    const precedent = periodeContexte.current
    const societeId = societe?.id ?? null
    const changement = precedent.annee !== annee
      || (precedent.societeId !== null && societeId !== null && precedent.societeId !== societeId)
    const saisie = changement ? false : precedent.saisie
    periodeContexte.current = { annee, societeId: societeId ?? precedent.societeId, saisie }
    if (!saisie) {
      setDateDebut(exercice?.date_debut || `${annee}-01-01`)
      setDateFin(exercice?.date_fin || `${annee}-12-31`)
    }
    const debut = exercice?.date_debut || `${annee}-01-01`
    const fin = exercice?.date_fin || `${annee}-12-31`
    const aujourdHui = dateLocaleISO()
    const dateProposee = aujourdHui < debut ? debut : aujourdHui > fin ? fin : aujourdHui
    setNouvelleOp(p => ({
      ...p,
      date: changement || !p.date || p.date < debut || p.date > fin ? dateProposee : p.date,
    }))
  }, [annee, societe?.id, exercice?.date_debut, exercice?.date_fin])

  useEffect(() => {
    let annule = false
    fetchBanques().then(data => { if (!annule) setCompteBancaire(data) }).catch(() => {})
    return () => { annule = true }
  }, [societe?.id])

  async function chargerSituation() {
    if (!dateDebut || !dateFin || scopeLecture !== scopeCourant.current) return
    const version = ++versionLecture.current
    const courante = () => version === versionLecture.current && scopeLecture === scopeCourant.current
    setChargement(true); setErreur(''); setMessage('')
    try {
      const data = await rapprochementAPI.situation(compteSelectionne, dateDebut, dateFin)
      if (!courante()) return
      setLignesReleve(data.lignes_releve || [])
      setEcrituresCompte(data.ecritures || [])
      setVentilations(data.ventilations || [])
      const reprise = data.solde_initial == null ? data.solde_initial_suggere : null
      setSoldeInitial(data.solde_initial == null ? (reprise == null ? '' : String(reprise)) : String(data.solde_initial))
      setSoldeInitialSuggere(reprise != null)
      setSoldeFinal(data.solde_final == null ? '' : String(data.solde_final))
      setSoldeComptableFinal(Number(data.solde_comptable_final || 0))
      setLectureSeuleAPI(Boolean(data.lecture_seule))
      setEditionId(null)
    } catch (e) {
      if (!courante()) return
      setErreur(e.message); setLignesReleve([]); setEcrituresCompte([])
      setVentilations([])
      setSoldeComptableFinal(0)
      setSoldeInitialSuggere(false)
    } finally { if (courante()) setChargement(false) }
  }

  useEffect(() => {
    chargerSituation()
    return () => { versionLecture.current += 1 }
  }, [societe?.id, compteSelectionne, dateDebut, dateFin]) // eslint-disable-line react-hooks/exhaustive-deps

  // Convention relevé bancaire : crédit = entrée sur le compte, débit = sortie.
  const mouvementReleve = useMemo(() => sommeReleve(lignesReleve, true), [lignesReleve])

  const soldeFinalCalcule = soldeInitial === '' || mouvementReleve == null ? null : Math.round((Number(soldeInitial) + mouvementReleve) * 100) / 100
  const soldeBancaireFinal = soldeFinal !== '' ? Number(soldeFinal || 0) : soldeFinalCalcule
  // Un solde reconstitué ne vaut pas confirmation du solde figurant sur le relevé bancaire.
  const ecartComptaBanque = soldeFinal === '' ? null : soldeComptableFinal - Number(soldeFinal)
  const controleReleve = soldeFinal !== '' && soldeFinalCalcule != null ? Number(soldeFinal) - soldeFinalCalcule : null
  const estEquilibre = mouvementReleve != null && ecartComptaBanque != null && Math.abs(ecartComptaBanque) < 0.01
  const controleReleveOK = controleReleve != null && Math.abs(controleReleve) < 0.01

  const nbRapprochees = ecrituresCompte.filter(e => e.rapprochee).length
  const nbReleveRapprochees = lignesReleve.filter(l => l.rapprochee).length
  const montantRapproche = sommeReleve(lignesReleve.filter(l => l.rapprochee))
  const montantNonRapproche = sommeReleve(lignesReleve.filter(l => !l.rapprochee))

  const ecrituresFiltrees = useMemo(() => ecrituresCompte.filter(e => {
    if (filtreCompta === 'rapprochees' && !e.rapprochee) return false
    if (filtreCompta === 'non_rapprochees' && e.rapprochee) return false
    return contientRecherche([e.date, e.numero_ecriture, e.reference, e.libelle, e.ligne_libelle, e.journal], rechercheCompta)
  }), [ecrituresCompte, filtreCompta, rechercheCompta])

  const lignesReleveFiltrees = useMemo(() => lignesReleve.filter(l => {
    if (filtreReleve === 'rapprochees' && !l.rapprochee) return false
    if (filtreReleve === 'non_rapprochees' && l.rapprochee) return false
    return contientRecherche([l.date, l.libelle, l.montant, l.sens], rechercheReleve)
  }), [lignesReleve, filtreReleve, rechercheReleve])

  function optionsCompatibles(ligneReleve) {
    if (!montantReleveExploitable(ligneReleve)) return []
    return ecrituresCompte
      .filter(e => {
        if (e.rapprochee && e.rapprochement_ligne_id !== ligneReleve.id) return false
        const montantCompta = ligneReleve.sens === 'credit' ? Number(e.debit || 0) : Number(e.credit || 0)
        return Math.abs(montantCompta - Number(ligneReleve.montant || 0)) < 0.01
      })
      .sort((a, b) => joursEcart(a.date, ligneReleve.date) - joursEcart(b.date, ligneReleve.date))
  }

  function ventilationsCompatibles(ligne) {
    if (!montantReleveExploitable(ligne)) return []
    return ventilations.filter(v => v.sens === ligne.sens
      && Math.round(v.montant * 100) === Math.round(ligne.montant * 100)
      && v.ecriture_ligne_ids.every(id => {
        const e = ecrituresCompte.find(x => x.ligne_id === id)
        return e && (!e.rapprochee || e.rapprochement_ligne_id === ligne.id)
      }))
  }

  async function enregistrerSoldes() {
    if (lectureSeule) return
    setErreur(''); setMessage('')
    try {
      await rapprochementAPI.enregistrerEtat(compteSelectionne, {
        date_debut: dateDebut,
        date_fin: dateFin,
        solde_initial: soldeInitial === '' ? null : Number(soldeInitial),
        solde_final: soldeFinal === '' ? null : Number(soldeFinal),
      })
      setMessage('Soldes du relevé enregistrés.')
    } catch (e) { setErreur(e.message) }
  }

  async function ajouterLigneReleve() {
    if (lectureSeule || !nouvelleOp.libelle.trim() || !nouvelleOp.montant || Number(nouvelleOp.montant) <= 0) return
    setErreur(''); setMessage('')
    try {
      await rapprochementAPI.ajouter({ ...nouvelleOp, libelle: nouvelleOp.libelle.trim(), compte: compteSelectionne, montant: Number(nouvelleOp.montant) })
      setNouvelleOp({ date: nouvelleOp.date, libelle: '', montant: '', sens: 'debit' })
      await chargerSituation()
    } catch (e) { setErreur(e.message) }
  }

  async function supprimerLigneReleve(id) {
    if (lectureSeule) return
    const l = lignesReleve.find(x => x.id === id)
    if (!confirm(`Supprimer ${l?.libelle || 'cette ligne'} du relevé bancaire ?`)) return
    setErreur(''); setMessage('')
    try { await rapprochementAPI.supprimer(id); await chargerSituation() }
    catch (e) { setErreur(e.message) }
  }

  function commencerEdition(ligne) {
    if (lectureSeule || ligne.rapprochee) return
    setEditionId(ligne.id)
    setEdition({
      date: ligne.date,
      libelle: ligne.libelle || '',
      montant: String(ligne.montant ?? ''),
      sens: ligne.sens || 'debit',
    })
  }

  async function enregistrerEdition() {
    if (lectureSeule || !editionId || !edition.date || !edition.libelle.trim() || Number(edition.montant) <= 0) return
    setErreur(''); setMessage('')
    try {
      await rapprochementAPI.modifier(editionId, {
        date: edition.date,
        libelle: edition.libelle.trim(),
        montant: Number(edition.montant),
        sens: edition.sens,
      })
      setEditionId(null)
      await chargerSituation()
    } catch (e) { setErreur(e.message) }
  }

  async function changerRapprochement(ligne, valeur) {
    if (lectureSeule) return
    setErreur(''); setMessage('')
    try {
      if (!valeur) await rapprochementAPI.derapprocher(ligne.id)
      else if (valeur.startsWith('VT:')) await rapprochementAPI.rapprocherVentilation(ligne.id, valeur.slice(3))
      else await rapprochementAPI.rapprocher(ligne.id, Number(valeur))
      await chargerSituation()
    } catch (e) { setErreur(e.message) }
  }

  async function proposerRapprochements() {
    if (lectureSeule || chargement || chargementSociete || chargementExercices || !societe?.id
      || contextePropositions !== contextePropositionsCourant.current) return
    const version = ++versionPropositions.current
    const courante = () => version === versionPropositions.current
      && contextePropositions === contextePropositionsCourant.current && getToken() === tokenPropositions
    setChargementPropositions(true); setErreurPropositions('')
    try {
      const data = await rapprochementAPI.propositions(compteSelectionne, dateDebut, dateFin)
      if (!courante()) return
      setPropositions({ ...data, contexte: contextePropositions })
      setSelectionPropositions(data.propositions.slice(0, 500).map(p => p.releve_id))
    } catch (e) { if (courante()) setErreurPropositions(e.message) }
    finally { if (courante()) setChargementPropositions(false) }
  }

  async function confirmerPropositions() {
    if (lectureSeule || envoiPropositions || !selectionPropositions.length
      || propositions?.contexte !== contextePropositions || getToken() !== tokenPropositions
      || contextePropositions !== contextePropositionsCourant.current) return
    const version = versionPropositions.current
    const courante = () => version === versionPropositions.current
      && contextePropositions === contextePropositionsCourant.current && getToken() === tokenPropositions
    setEnvoiPropositions(true); setErreurPropositions('')
    try {
      const r = await rapprochementAPI.confirmerPropositions(compteSelectionne, {
        date_debut: dateDebut, date_fin: dateFin, empreinte: propositions.empreinte,
        releve_ids: selectionPropositions,
      })
      if (!courante()) return
      setPropositions(null); setSelectionPropositions([])
      await chargerSituation()
      if (courante()) setMessage(`${r.nb_rapprochees} opération(s) rapprochée(s).`)
    } catch (e) { if (courante()) setErreurPropositions(e.message) }
    finally { if (courante()) setEnvoiPropositions(false) }
  }

  async function parseExcel(file) {
    if (!file || lectureSeule) return
    setLoadingImport(true); setErreurImport('')
    try {
      const buf = await file.arrayBuffer()
      let rows
      if (/\.csv$/i.test(file.name)) rows = tableauDepuisCsv(decoderCsv(buf))
      else {
        const XLSX = await import('xlsx')
        const wb = XLSX.read(buf, { type: 'array', cellDates: true })
        const ws = wb.Sheets[wb.SheetNames[0]]
        rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
      }
      setLignesImport(lignesDepuisTableauReleve(rows))
    } catch (e) { setLignesImport([]); setErreurImport(e.message) }
    finally { setLoadingImport(false) }
  }

  async function enregistrerImport() {
    if (lectureSeule || !lignesImport.length) return
    setErreurImport(''); setErreur(''); setMessage('')
    try {
      const r = await rapprochementAPI.importer(compteSelectionne, lignesImport)
      // Mémoriser le solde d'ouverture repris de la période précédente : cela
      // permet de calculer la clôture même si le fichier ne donne aucun solde.
      if (soldeInitialSuggere && soldeInitial !== '') {
        await rapprochementAPI.enregistrerEtat(compteSelectionne, {
          date_debut: dateDebut, date_fin: dateFin,
          solde_initial: Number(soldeInitial),
          solde_final: soldeFinal === '' ? null : Number(soldeFinal),
        })
      }
      setLignesImport([]); setOnglet('manuel'); await chargerSituation()
      setMessage(`Import enregistré : ${r.nb_creees} ligne(s), ${r.nb_ignorees} doublon(s) ignoré(s).`)
    } catch (e) { setErreurImport(e.message) }
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Rapprochement bancaire</h1>
          <p className={styles.subtitle}>Rapprochement persistant du relevé avec les écritures définitives</p>
        </div>
      </div>

      <div className={styles.tabs}>
        {[{ id: 'manuel', label: 'Saisie manuelle', icon: 'ti-keyboard' }, { id: 'import', label: 'Import Excel / CSV', icon: 'ti-file-spreadsheet' }].map(o => (
          <button key={o.id} onClick={() => setOnglet(o.id)} className={`${styles.tab} ${onglet === o.id ? styles.tabActive : ''}`}>
            <i className={`ti ${o.icon}`} /> {o.label}
          </button>
        ))}
      </div>

      <div className={styles.content}>
        {lectureSeule && <div className={styles.readOnlyBanner}><i className="ti ti-lock" /> Exercice clôturé : rapprochement bancaire en lecture seule. Les filtres et la consultation restent disponibles.</div>}
        {erreur && <div className={styles.errorBanner}>{erreur}</div>}
        {message && <div className={styles.successBanner}>{message}</div>}
        {mouvementReleve == null && <div className={styles.errorBanner} role="alert">Totaux du relevé à vérifier : au moins une ligne a un montant inexploitable. Consultez le justificatif correspondant.</div>}
        {erreurPropositions && !propositions && <div className={styles.errorBanner} role="alert">{erreurPropositions}</div>}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.cardTitle}>Correspondances exactes</span>
            <button className={styles.primaryButton} onClick={proposerRapprochements} disabled={lectureSeule || chargement || chargementSociete || chargementExercices || !societe?.id || chargementPropositions || envoiPropositions}>
              {chargementPropositions ? 'Recherche…' : 'Proposer les rapprochements'}
            </button>
          </div>
          <p>La date, le sens, le montant et la référence doivent correspondre exactement. Vérifiez la sélection avant de confirmer. Les correspondances ambiguës restent à traiter manuellement.</p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}><span className={styles.cardTitle}>Paramètres</span></div>
          <div className={styles.parameters}>
            <div className={styles.fieldWide}>
              <label className={styles.label}>Compte bancaire</label>
              <select className={styles.input} value={compteSelectionne} onChange={e => setCompteSelectionne(e.target.value)}>
                {COMPTES_BANQUE.map(c => <option key={c.compte} value={c.compte}>{c.label}</option>)}
                {compteBancaire.filter(cb => !COMPTES_BANQUE.some(c => c.compte === cb.compte_comptable)).map(cb => <option key={cb.id} value={cb.compte_comptable}>{cb.banque} — {cb.agence || ''} ({cb.compte_comptable})</option>)}
              </select>
            </div>
            <div><label className={styles.label}>Du</label><input className={styles.input} type="date" min={dateMin} max={dateMax} value={dateDebut} onChange={e => { periodeContexte.current.saisie = true; setDateDebut(e.target.value) }} /></div>
            <div><label className={styles.label}>Au</label><input className={styles.input} type="date" min={dateMin} max={dateMax} value={dateFin} onChange={e => { periodeContexte.current.saisie = true; setDateFin(e.target.value) }} /></div>
            <div><label className={styles.label}>Solde initial du relevé (MAD)</label><input className={styles.input} type="number" step="0.01" placeholder="Début de période" value={soldeInitial} disabled={lectureSeule} onChange={e => { setSoldeInitial(e.target.value); setSoldeInitialSuggere(false) }} onBlur={enregistrerSoldes} /></div>
            <div>
              <label className={styles.label}>Solde final du relevé (MAD)</label>
              <input className={styles.input} type="number" step="0.01" placeholder="Facultatif : solde indiqué par la banque" value={soldeFinal} disabled={lectureSeule} onChange={e => setSoldeFinal(e.target.value)} onBlur={enregistrerSoldes} />
            </div>
          </div>
          <div className={styles.balanceExplanation}>
            {soldeInitialSuggere && <span>Solde initial proposé automatiquement depuis la période précédente. </span>}
            {soldeFinalCalcule == null
              ? mouvementReleve == null ? 'Solde final à vérifier : certains montants du relevé sont inexploitables.' : 'Le solde initial est nécessaire pour calculer le solde final depuis les opérations importées.'
              : <>Solde final calculé automatiquement : <strong>{formatMAD(soldeFinalCalcule)} MAD</strong> (solde initial + mouvements). </>}
            {soldeFinal === ''
              ? 'Le solde final indiqué par la banque est facultatif ; renseignez-le pour un contrôle indépendant.'
              : 'Le solde indiqué par la banque est comparé au calcul pour signaler un éventuel écart.'}
          </div>
        </div>

        {onglet === 'manuel' && <>
          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <div className={styles.kpiLabel}>Solde comptable au {formatDate(dateFin)}</div>
              <div className={styles.kpiValeur}>{formatMAD(soldeComptableFinal)} MAD</div>
              <div className={styles.kpiHint}>{ecrituresCompte.length} ligne(s) définitive(s) sur la période</div>
            </div>
            <div className={styles.kpiCard}>
              <div className={styles.kpiLabel}>{soldeFinal !== '' ? 'Solde bancaire déclaré' : 'Solde final calculé'}</div>
              <div className={styles.kpiValeur}>{soldeBancaireFinal == null ? '—' : `${formatMAD(soldeBancaireFinal)} MAD`}</div>
              <div className={styles.kpiHint}>{soldeFinal !== '' ? 'Solde final déclaré' : soldeFinalCalcule != null ? 'Calculé : initial + mouvements' : 'Solde initial nécessaire au calcul'}</div>
            </div>
            <div className={`${styles.kpiCard} ${ecartComptaBanque == null ? '' : estEquilibre ? styles.kpiOk : styles.kpiWarn}`}>
              <div className={styles.kpiLabel}>Écart compta / banque</div>
              <div className={styles.kpiValeur}>{ecartComptaBanque == null ? '—' : `${formatMAD(Math.abs(ecartComptaBanque))} MAD`}</div>
              <div className={styles.kpiHint}>{ecartComptaBanque == null ? 'Solde bancaire déclaré non renseigné : comparaison indicative uniquement' : estEquilibre ? '✓ Équilibré' : 'À justifier / rapprocher'}</div>
            </div>
            <div className={`${styles.kpiCard} ${controleReleve == null ? '' : controleReleveOK ? styles.kpiOk : styles.kpiWarn}`}>
              <div className={styles.kpiLabel}>Contrôle du relevé</div>
              <div className={styles.kpiValeur}>{controleReleve == null ? '—' : `${formatMAD(Math.abs(controleReleve))} MAD`}</div>
              <div className={styles.kpiHint}>{controleReleve == null ? `Solde déclaré facultatif · Mouvements nets : ${formatMAD(mouvementReleve)} MAD` : controleReleveOK ? '✓ Initial + mouvements = final' : 'Solde final incohérent avec les mouvements'}</div>
            </div>
          </div>

          {chargement ? <div className={styles.cardLoading}>Chargement…</div> : <div className={styles.dualGrid}>
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Écritures comptables</span>
                <span className={styles.cardMeta}>{nbRapprochees}/{ecrituresCompte.length} rapprochées</span>
              </div>
              <div className={styles.tableToolbar}>
                <input className={styles.searchInput} placeholder="Rechercher écriture, libellé, référence…" value={rechercheCompta} onChange={e => setRechercheCompta(e.target.value)} />
                <select className={styles.filterSelect} value={filtreCompta} onChange={e => setFiltreCompta(e.target.value)}>
                  <option value="toutes">Toutes</option><option value="non_rapprochees">Non rapprochées</option><option value="rapprochees">Rapprochées</option>
                </select>
              </div>
              <div className={styles.tableWrapper}>
                <table className={`${styles.table} ${styles.tableCompta}`}>
                  <thead><tr><th>Date</th><th>Libellé</th><th>Référence</th><th className={styles.amount}>Débit</th><th className={styles.amount}>Crédit</th><th>État</th></tr></thead>
                  <tbody>
                    {ecrituresFiltrees.map(e => <tr key={e.ligne_id} className={e.rapprochee ? styles.rowMatched : ''}>
                      <td className={styles.nowrap}>{formatDate(e.date)}</td>
                      <td><div>{e.libelle || e.ligne_libelle || '—'}</div><div className={styles.secondaryText}>{e.numero_ecriture}</div></td>
                      <td>{e.reference || '—'}</td>
                      <td className={styles.amount}>{e.debit > 0 ? formatMAD(e.debit) : '—'}</td>
                      <td className={styles.amount}>{e.credit > 0 ? formatMAD(e.credit) : '—'}</td>
                      <td><span className={`${styles.statusBadge} ${e.rapprochee ? styles.statusOk : styles.statusPending}`}>{e.rapprochee ? 'Rapprochée' : 'À rapprocher'}</span></td>
                    </tr>)}
                    {!ecrituresFiltrees.length && <tr><td colSpan="6" className={styles.emptyCell}>Aucune écriture pour ces filtres.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Relevé bancaire</span>
                <span className={styles.cardMeta}>{nbReleveRapprochees}/{lignesReleve.length} rapprochées</span>
              </div>
              <div className={styles.tableToolbar}>
                <input className={styles.searchInput} placeholder="Rechercher date, libellé, montant…" value={rechercheReleve} onChange={e => setRechercheReleve(e.target.value)} />
                <select className={styles.filterSelect} value={filtreReleve} onChange={e => setFiltreReleve(e.target.value)}>
                  <option value="toutes">Toutes</option><option value="non_rapprochees">Non rapprochées</option><option value="rapprochees">Rapprochées</option>
                </select>
              </div>
              <div className={styles.newLineBar}>
                <div className={styles.newLineGrid}>
                  <input className={styles.inputSm} type="date" min={dateDebut} max={dateFin} value={nouvelleOp.date} disabled={lectureSeule} onChange={e => setNouvelleOp(p => ({ ...p, date: e.target.value }))} />
                  <input className={styles.inputSm} placeholder="Libellé…" value={nouvelleOp.libelle} disabled={lectureSeule} onChange={e => setNouvelleOp(p => ({ ...p, libelle: e.target.value }))} />
                  <input className={styles.inputSm} type="number" min="0.01" step="0.01" placeholder="Montant" value={nouvelleOp.montant} disabled={lectureSeule} onChange={e => setNouvelleOp(p => ({ ...p, montant: e.target.value }))} />
                  <select className={styles.inputSm} value={nouvelleOp.sens} disabled={lectureSeule} onChange={e => setNouvelleOp(p => ({ ...p, sens: e.target.value }))}><option value="debit">Débit</option><option value="credit">Crédit</option></select>
                  <button className={styles.primaryIconButton} onClick={ajouterLigneReleve} disabled={lectureSeule || !nouvelleOp.libelle.trim() || Number(nouvelleOp.montant) <= 0} title="Ajouter l'opération"><i className="ti ti-plus" /><span className="libelle-action" aria-hidden="true">Ajouter l'opération</span></button>
                </div>
              </div>
              <div className={`${styles.tableWrapper} ${styles.releveScroll}`}>
                <table className={`${styles.table} ${styles.tableReleve}`}>
                  <thead><tr><th>Date</th><th>Libellé</th><th>Sens</th><th className={styles.amount}>Montant</th><th>Écriture comptable associée</th><th>Actions</th></tr></thead>
                  <tbody>
                    {lignesReleveFiltrees.map(l => {
                      const enEdition = editionId === l.id
                      const options = optionsCompatibles(l)
                      const groupes = ventilationsCompatibles(l)
                      return <tr key={l.id}>
                        <td className={styles.nowrap}>{enEdition ? <input className={styles.inputSm} type="date" min={dateDebut} max={dateFin} value={edition.date} onChange={e => setEdition(p => ({ ...p, date: e.target.value }))} /> : formatDate(l.date)}</td>
                        <td>{enEdition ? <input className={styles.inputSm} value={edition.libelle} onChange={e => setEdition(p => ({ ...p, libelle: e.target.value }))} /> : (l.libelle || '—')}</td>
                        <td>{enEdition ? <select className={styles.inputSm} value={edition.sens} onChange={e => setEdition(p => ({ ...p, sens: e.target.value }))}><option value="debit">Débit</option><option value="credit">Crédit</option></select> : <span className={`${styles.statusBadge} ${l.sens === 'credit' ? styles.creditBadge : styles.debitBadge}`}>{l.sens === 'credit' ? 'Crédit' : 'Débit'}</span>}</td>
                        <td className={`${styles.amount} ${l.sens === 'credit' ? styles.positive : styles.negative}`}>{enEdition ? <input className={styles.inputSm} type="number" min="0.01" step="0.01" value={edition.montant} onChange={e => setEdition(p => ({ ...p, montant: e.target.value }))} /> : montantReleveExploitable(l) ? `${l.sens === 'credit' ? '+' : '-'}${formatMAD(l.montant)}` : 'À vérifier'}</td>
                        <td>
                          <select className={`${styles.inputSm} ${styles.matchSelect}`} value={l.ventilation_operation_id ? `VT:${l.ventilation_operation_id}` : l.ecriture_ligne_id || ''} disabled={lectureSeule || enEdition || !montantReleveExploitable(l)} onChange={e => changerRapprochement(l, e.target.value)}>
                            <option value="">— Non rapprochée —</option>
                            {groupes.map(v => <option key={v.operation_id} value={`VT:${v.operation_id}`}>Ventilation · {v.reference || v.operation_id.slice(0, 8)} · {v.tiers} · {v.nb_reglements} règlements · {formatMAD(v.montant)} MAD</option>)}
                            {l.ventilation_operation_id && !groupes.some(v => v.operation_id === l.ventilation_operation_id) && <option value={`VT:${l.ventilation_operation_id}`}>Ventilation rapprochée · {l.ecriture_ligne_ids?.length || 0} lignes comptables</option>}
                            {options.map(e => <option key={e.ligne_id} value={e.ligne_id}>{formatDate(e.date)} · {e.numero_ecriture} · {e.libelle || e.ligne_libelle || 'Sans libellé'} · {formatMAD(l.sens === 'credit' ? e.debit : e.credit)} MAD{joursEcart(e.date, l.date) ? ` · J${joursEcart(e.date, l.date)}` : ' · même jour'}</option>)}
                          </select>
                          {!l.rapprochee && options.length === 0 && groupes.length === 0 && <div className={styles.secondaryText}>Aucune écriture de même montant/sens.</div>}
                        </td>
                        <td>
                          <div className={styles.actions}>
                            {enEdition ? <>
                              <button className={styles.actionButton} onClick={enregistrerEdition} title="Enregistrer"><i className="ti ti-check" /><span className="libelle-action" aria-hidden="true">Enregistrer</span></button>
                              <button className={styles.actionButton} onClick={() => setEditionId(null)} title="Annuler"><i className="ti ti-x" /><span className="libelle-action" aria-hidden="true">Annuler</span></button>
                            </> : <>
                              <button className={styles.actionButton} onClick={() => commencerEdition(l)} disabled={lectureSeule || l.rapprochee} title={l.rapprochee ? 'Dérapprochez avant de modifier' : 'Modifier'}><i className="ti ti-pencil" /><span className="libelle-action" aria-hidden="true">Modifier</span></button>
                              <button className={`${styles.actionButton} ${styles.deleteButton}`} onClick={() => supprimerLigneReleve(l.id)} disabled={lectureSeule || l.rapprochee} title={l.rapprochee ? 'Dérapprochez avant de supprimer' : 'Supprimer'}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>
                            </>}
                          </div>
                        </td>
                      </tr>
                    })}
                    {!lignesReleveFiltrees.length && <tr><td colSpan="6" className={styles.emptyCell}>Aucune opération de relevé pour ces filtres.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          </div>}

          <div className={styles.summaryBar}>
            <span><strong>{ecrituresCompte.length - nbRapprochees}</strong> ligne(s) comptable(s) non rapprochée(s)</span>
            <span><strong>{lignesReleve.length - nbReleveRapprochees}</strong> opération(s) de relevé non rapprochée(s)</span>
            <span><strong>{formatMAD(montantRapproche)} MAD</strong> rapprochés</span>
            <span><strong>{formatMAD(montantNonRapproche)} MAD</strong> de relevé restant à rapprocher</span>
          </div>
        </>}

        {onglet === 'import' && <div className={`${styles.card} ${styles.importCard}`}>
          <p style={{ fontSize: 12 }}>Colonnes : Date (JJ/MM/AAAA ou AAAA-MM-JJ), Libellé (facultatif), Débit et Crédit ; ou Montant signé (+ entrée, − sortie), avec Sens facultatif (Débit/Crédit et montant positif). Décimales : 1234,56 ou 1 234,56. La date valeur et les soldes ne sont pas importés comme opérations.</p>
          {!lignesImport.length ? <div
            onDragOver={e => { if (!lectureSeule) e.preventDefault() }}
            onDrop={e => { if (!lectureSeule) { e.preventDefault(); parseExcel(e.dataTransfer.files[0]) } }}
            onClick={() => { if (!lectureSeule) inputRef.current?.click() }}
            className={`${styles.dropzone} ${lectureSeule ? styles.dropzoneDisabled : ''}`}
          >
            <input ref={inputRef} type="file" accept=".xlsx,.xls,.csv" style={{ display: 'none' }} disabled={lectureSeule} onChange={e => parseExcel(e.target.files?.[0])} />
            <i className="ti ti-file-spreadsheet" />
            <div>{lectureSeule ? 'Import désactivé sur un exercice clôturé' : loadingImport ? 'Lecture…' : 'Glisser le relevé ici ou cliquer'}</div>
            {erreurImport && <div className={styles.errorText}>{erreurImport}</div>}
          </div> : <>
            <div className={styles.importHeader}><strong>{lignesImport.length} ligne(s) détectée(s)</strong><button onClick={() => { setLignesImport([]); setErreurImport('') }} className={styles.primaryButton}>Annuler cet import</button><button onClick={enregistrerImport} disabled={lectureSeule} className={styles.primaryButton}>Enregistrer le relevé</button></div>
            <div className={styles.tableWrapper}><table className={`${styles.table} ${styles.tableImport}`}><thead><tr><th>Date</th><th>Libellé</th><th>Sens</th><th className={styles.amount}>Montant</th></tr></thead><tbody>{lignesImport.map((l, i) => <tr key={i}><td>{l.date}</td><td>{l.libelle}</td><td>{l.sens === 'credit' ? 'Crédit' : 'Débit'}</td><td className={styles.amount}>{formatMAD(l.montant)}</td></tr>)}</tbody></table></div>
          </>}
        </div>}
      </div>
      {propositions?.contexte === contextePropositions && <Modal titre="Propositions de rapprochement" icone="ti-arrows-exchange" largeur="lg" onFermer={() => { if (!envoiPropositions) { versionPropositions.current += 1; setPropositions(null) } }}>
        <p>{propositions.propositions.length} correspondance(s) unique(s). {propositions.ambigues.length} opération(s) ambiguë(s) et {propositions.sans_correspondance.length} sans correspondance exacte restent à vérifier.</p>
        <p>Les propositions exigent une même date, un même montant et sens, ainsi qu’une référence comptable identique au libellé du relevé. Si la banque ajoute un descriptif à cette référence, associez la ligne manuellement dans le tableau.</p>
        <p>Seuls les pointages seront enregistrés. Les montants du relevé et les écritures comptables sont conservés.</p>
        {erreurPropositions && <div className={styles.errorBanner} role="alert">{erreurPropositions}</div>}
        {propositions.propositions.map(p => <label key={p.releve_id} style={{ display: 'flex', gap: 10, padding: '10px 0', alignItems: 'flex-start', overflowWrap: 'anywhere' }}>
          <input type="checkbox" checked={selectionPropositions.includes(p.releve_id)} disabled={envoiPropositions || (!selectionPropositions.includes(p.releve_id) && selectionPropositions.length >= 500)} onChange={e => setSelectionPropositions(ids => e.target.checked ? [...ids, p.releve_id] : ids.filter(id => id !== p.releve_id))} />
          <span>{formatDate(p.date)} · {p.reference} · {formatMAD(p.montant)} MAD · {p.sens === 'credit' ? 'Entrée' : 'Sortie'}<br />{p.libelle} · {p.ecriture_ligne_ids.length} ligne(s) comptable(s)</span>
        </label>)}
        {!propositions.propositions.length && <p>Aucun pointage ne peut être proposé avec ces critères. Les opérations restent disponibles dans le tableau.</p>}
        <button className={styles.primaryButton} onClick={confirmerPropositions} disabled={envoiPropositions || lectureSeule || propositions.lecture_seule || !selectionPropositions.length}>{envoiPropositions ? 'Enregistrement…' : 'Rapprocher la sélection'}</button>
      </Modal>}
    </div>
  )
}
