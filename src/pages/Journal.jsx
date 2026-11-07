import React, { useState, useMemo, useRef, useEffect } from 'react'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { JOURNAUX, formatMAD, formatDate } from '../data/donnees.js'
import { trouverCompteLecture } from '../data/planComptableCache.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import LogoDocument from '../components/LogoDocument.jsx'
import { API_BASE, APP_VERSION, ecrituresAPI, tiersAPI, getToken, peutEcrire } from '../services/api.js'
import { exporterCSV } from '../services/exportCSV.js'
import FormulaireEcriture from '../components/FormulaireEcriture.jsx'
import PiecesJointes from '../components/PiecesJointes.jsx'
import styles from './Journal.module.css'
import { notifier } from '../services/notifications.js'

const BADGE_COULEURS = {
  AC: { bg: '#EAF3DE', color: '#3B6D11' },
  VT: { bg: '#E6F1FB', color: '#185FA5' },
  BQ: { bg: '#FAEEDA', color: '#854F0B' },
  CA: { bg: '#FBEAF0', color: '#993556' },
  OD: { bg: '#EEEDFE', color: '#534AB7' },
  CL: { bg: '#F0EAFB', color: '#5B3A8A' },
}

function BadgeJournal({ code }) {
  const c = BADGE_COULEURS[code] || { bg: '#f0efed', color: '#5a5955' }
  return (
    <span className={styles.badge} style={{ background: c.bg, color: c.color }}>
      {code}
    </span>
  )
}

export default function Journal() {
  const { ecritures, supprimerEcriture, chargement, erreur, validerEcriture, contrepasserEcriture, validerLot, recharger } = useEcritures()
  const { annee, exercice } = useExercice()
  const { societe } = useModules()
  const peutModifier = peutEcrire()
  const [exportFec, setExportFec] = useState(false)
  const [fecControle, setFecControle] = useState(null)
  const [fecTiers, setFecTiers] = useState([])
  const [fecFixValues, setFecFixValues] = useState({})
  const [fecFixSaving, setFecFixSaving] = useState('')
  const [auditEcriture, setAuditEcriture] = useState(null)
  const [auditEvents, setAuditEvents] = useState([])
  const [auditLoading, setAuditLoading] = useState(false)
  const [justifEcriture, setJustifEcriture] = useState(null)
  const [justifInfo, setJustifInfo] = useState(null)
  const [justifReference, setJustifReference] = useState('')
  const [justifDate, setJustifDate] = useState('')
  const [justifMotif, setJustifMotif] = useState('')
  const [justifSaving, setJustifSaving] = useState(false)
  const [validationEnCours, setValidationEnCours] = useState(false)
  const [retourValidation, setRetourValidation] = useState(null)
  const contexteValidation = `${societe?.id}:${annee}`
  const contexteValidationRef = useRef(contexteValidation)
  contexteValidationRef.current = contexteValidation
  useEffect(() => { setRetourValidation(null); setValidationEnCours(false) }, [contexteValidation])
  const exerciceOuvert = !exercice || exercice.statut === 'ouvert'

  function ouvrirNouvelleEcriture() {
    if (!exerciceOuvert) {
      notifier(
        `Exercice ${annee} clôturé\n\n` +
        `Il n’est plus possible d’ajouter une écriture comptable sur cet exercice. ` +
        `Sélectionnez un exercice ouvert pour créer une nouvelle écriture.`
      )
      return
    }
    setShowForm(true)
  }

  function numeroAffiche(e) {
    return e?.numero_ecriture || `Brouillon #${e?.id ?? '—'}`
  }

  function exporterJournalCSV() {
    const lignes = []
    ecrituresFiltrees.forEach(e => {
      e.lignes.forEach((l, i) => {
        lignes.push({
          numero: i === 0 ? numeroAffiche(e) : '',
          date: i === 0 ? e.date : '',
          datePiece: i === 0 ? (e.date_piece_fec || e.date_piece || e.date || '') : '',
          journal: i === 0 ? e.journal : '',
          libelleEcriture: i === 0 ? e.libelle : '',
          reference: i === 0 ? (e.reference_fec || e.reference || '') : '',
          compte: l.compte,
          compteLibelle: trouverCompteLecture(l.compte, getToken())?.libelle || '',
          auxiliaire: l.compte_auxiliaire_snapshot || '',
          auxiliaireLibelle: l.libelle_auxiliaire_snapshot || '',
          libelleLigne: l.libelle || '',
          debit: l.debit || 0,
          credit: l.credit || 0,
        })
      })
    })
    exporterCSV(`journal_${annee}`, [
      { label: 'N° écriture', get: r => r.numero },
      { label: 'Date', get: r => r.date },
      { label: 'Date pièce', get: r => r.datePiece },
      { label: 'Journal', get: r => r.journal },
      { label: 'Libellé écriture', get: r => r.libelleEcriture },
      { label: 'Référence pièce', get: r => r.reference },
      { label: 'Compte', get: r => r.compte },
      { label: 'Intitulé du compte', get: r => r.compteLibelle },
      { label: 'Compte auxiliaire', get: r => r.auxiliaire },
      { label: 'Libellé auxiliaire', get: r => r.auxiliaireLibelle },
      { label: 'Libellé ligne', get: r => r.libelleLigne },
      { label: 'Débit', get: r => r.debit, type: 'nombre' },
      { label: 'Crédit', get: r => r.credit, type: 'nombre' },
    ], lignes)
  }

  async function exporterFEC() {
    setExportFec(true)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const controleRes = await fetch(`${API_BASE}/api/fec/apercu?exercice=${annee}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!controleRes.ok) throw new Error('Impossible de lancer les contrôles FEC')
      let apercu = await controleRes.json()

      // Patch 099 : avant de demander une ressaisie manuelle, HisabPro tente
      // de récupérer automatiquement les métadonnées FEC depuis une facture
      // source exacte (journal + date + TTC, puis indices exacts si nécessaire).
      // La réparation est append-only ; un rapprochement ambigu reste intact.
      if (peutModifier && !apercu.conforme_export && (apercu.bloquants || []).some(a =>
        ['AUXILIAIRE_MANQUANT', 'REFERENCE_PIECE_MANQUANTE'].includes(a.code)
      )) {
        try {
          const autoRes = await fetch(`${API_BASE}/api/fec/reparer-sources-factures?exercice=${annee}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
          })
          if (autoRes.ok) {
            const auto = await autoRes.json()
            if ((auto.nb_auxiliaires_ajoutes || 0) + (auto.nb_references_ajoutees || 0) > 0) {
              const controleApres = await fetch(`${API_BASE}/api/fec/apercu?exercice=${annee}`, {
                headers: { Authorization: `Bearer ${token}` },
              })
              if (controleApres.ok) apercu = await controleApres.json()
            }
          }
        } catch {
          // Le contrôle FEC reste utilisable même si l'utilisateur n'a pas le
          // droit d'écriture requis pour cette réparation append-only.
        }
      }

      if (!apercu.conforme_export) {
        // Patch 095 : ne jamais tronquer les anomalies FEC dans une alerte native.
        // Patch 098 : les anciennes lacunes documentaires/auxiliaires peuvent
        // être complétées ici sans réécrire l'écriture définitive.
        if ((apercu.bloquants || []).some(a => a.code === 'AUXILIAIRE_MANQUANT')) {
          try { setFecTiers(await tiersAPI.lister({ limit: 500 })) } catch { setFecTiers([]) }
        }
        setFecControle(apercu)
        return
      }

      if (apercu.nb_avertissements > 0) {
        const avertissements = (apercu.avertissements || []).slice(0, 5)
          .map(a => `• ${a.message}`)
          .join('\n')
        if (!confirm(`FEC conforme aux contrôles bloquants, avec ${apercu.nb_avertissements} avertissement(s) :\n\n${avertissements}\n\nContinuer l'export ?`)) return
      }

      const res = await fetch(`${API_BASE}/api/fec/export?exercice=${annee}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        let message = 'Erreur lors de la génération du FEC'
        try {
          const body = await res.json()
          message = body?.detail?.message || body?.detail || message
        } catch {}
        throw new Error(message)
      }
      const blob = await res.blob()
      const cd = res.headers.get('content-disposition') || ''
      const m = cd.match(/filename="(.+?)"/)
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = m ? m[1] : `FEC_${annee}.txt`
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e) { notifier.erreur(e.message) }
    finally { setExportFec(false) }
  }
  function cleCorrectionFec(a, i) {
    return `${a.code || 'ANOMALIE'}-${a.ecriture_id || 'global'}-${a.details?.ligne_ecriture_id || 'na'}-${i}`
  }

  async function recontrolerFec() {
    const token = localStorage.getItem('hisabpro_token')
    const res = await fetch(`${API_BASE}/api/fec/apercu?exercice=${annee}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error('Impossible de relancer le contrôle FEC')
    const apercu = await res.json()
    setFecControle(apercu.conforme_export ? null : apercu)
    return apercu
  }

  async function corrigerReferenceFec(a, i, ecriture) {
    const key = cleCorrectionFec(a, i)
    const reference = String(fecFixValues[key]?.reference || '').trim()
    if (!reference) return
    setFecFixSaving(key)
    try {
      await ecrituresAPI.ajouterJustificatif(a.ecriture_id, {
        reference,
        date_piece: ecriture?.date_piece || ecriture?.date || null,
        motif: 'Complément documentaire FEC historique.',
      })
      setFecFixValues(v => ({ ...v, [key]: {} }))
      await recharger()
      await recontrolerFec()
    } catch (err) {
      notifier.erreur(err.message)
    } finally {
      setFecFixSaving('')
    }
  }

  async function corrigerAuxiliaireFec(a, i) {
    const key = cleCorrectionFec(a, i)
    const tiersId = Number(fecFixValues[key]?.tiers_id || 0)
    const ligneId = Number(a.details?.ligne_ecriture_id || 0)
    if (!tiersId || !ligneId) return
    setFecFixSaving(key)
    try {
      await ecrituresAPI.ajouterAuxiliaireComplement(a.ecriture_id, ligneId, {
        tiers_id: tiersId,
        motif: 'Complément auxiliaire FEC historique.',
      })
      setFecFixValues(v => ({ ...v, [key]: {} }))
      await recontrolerFec()
    } catch (err) {
      notifier.erreur(err.message)
    } finally {
      setFecFixSaving('')
    }
  }

  const [showForm,       setShowForm]       = useState(false)
  const [ecritureEdit,   setEcritureEdit]   = useState(null)
  const [filtreJ,      setFiltreJ]      = useState('TOUS')
  const [filtreDate,   setFiltreDate]   = useState('')
  const [filtreEtat,   setFiltreEtat]   = useState('toutes')
  const [recherche,    setRecherche]    = useState('')
  const [groupement,   setGroupement]   = useState('aucun')  // aucun | jour | mois | trimestre

  const ecrituresFiltrees = useMemo(() => {
    return ecritures.filter(e => {
      if (filtreJ !== 'TOUS' && e.journal !== filtreJ) return false
      if (filtreDate && e.date !== filtreDate) return false
      if (filtreEtat === 'brouillons' && e.est_validee) return false
      if (filtreEtat === 'validees' && !e.est_validee) return false
      if (recherche) {
        const q = recherche.toLowerCase()
        const dansLibelle = e.libelle.toLowerCase().includes(q)
        const dansPiece = (e.reference_fec || e.reference || '').toLowerCase().includes(q)
        const dansNumero = (e.numero_ecriture || '').toLowerCase().includes(q)
        const dansLignes  = e.lignes.some(
          l => (l.libelle || '').toLowerCase().includes(q) || l.compte.includes(q)
        )
        if (!dansLibelle && !dansPiece && !dansNumero && !dansLignes) return false
      }
      return true
    })
  }, [ecritures, filtreJ, filtreDate, filtreEtat, recherche])

  // Groupement des écritures
  const ecrituresGroupees = useMemo(() => {
    if (groupement === 'aucun') return [{ cle: null, label: null, ecritures: ecrituresFiltrees }]

    const groupes = {}
    ecrituresFiltrees.forEach(e => {
      const d = new Date(e.date)
      let cle, label
      if (groupement === 'jour') {
        cle = e.date
        label = new Date(e.date).toLocaleDateString('fr-MA', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
      } else if (groupement === 'mois') {
        cle = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`
        label = d.toLocaleDateString('fr-MA', { month: 'long', year: 'numeric' })
      } else if (groupement === 'trimestre') {
        const t = Math.ceil((d.getMonth() + 1) / 3)
        cle = `${d.getFullYear()}-T${t}`
        label = `T${t} ${d.getFullYear()}`
      }
      if (!groupes[cle]) groupes[cle] = { cle, label, ecritures: [] }
      groupes[cle].ecritures.push(e)
    })
    return Object.values(groupes).sort((a, b) => a.cle > b.cle ? -1 : 1)
  }, [ecrituresFiltrees, groupement])

  // Numérotation continue des mouvements, dans l'ordre d'affichage.
  // (La capture de référence numérote chaque ligne du journal.)
  const numerosLigne = useMemo(() => {
    const m = new Map()
    let n = 0
    ecrituresGroupees.forEach(g => g.ecritures.forEach(e =>
      e.lignes.forEach((_, i) => { n += 1; m.set(`${e.id}-${i}`, n) })
    ))
    return m
  }, [ecrituresGroupees])

  async function valider(e) {
    if (!confirm(
      `Valider l'écriture ${numeroAffiche(e)} — ${e.libelle} ?\n\n` +
      `Une écriture validée devient définitive : elle ne pourra plus être modifiée ni supprimée.\n` +
      `En cas d'erreur, HisabPro créera une contrepassation traçable.`
    )) return
    try { await validerEcriture(e.id) } catch (err) { notifier.erreur(err.message) }
  }

  async function contrepasser(e) {
    if (!confirm(
      `Contrepasser l'écriture ${numeroAffiche(e)} — ${e.libelle} ?\n\n` +
      `HisabPro créera automatiquement une nouvelle écriture inverse, validée et numérotée. ` +
      `L'écriture originale restera intacte dans la piste d'audit.`
    )) return
    try {
      const r = await contrepasserEcriture(e.id)
      notifier(r.message || 'Contrepassation créée.')
    } catch (err) { notifier.erreur(err.message) }
  }

  async function ouvrirAudit(e) {
    setAuditEcriture(e)
    setAuditEvents([])
    setAuditLoading(true)
    try {
      setAuditEvents(await ecrituresAPI.audit(e.id))
    } catch (err) {
      notifier.erreur(err.message)
      setAuditEcriture(null)
    } finally {
      setAuditLoading(false)
    }
  }

  async function ouvrirJustificatifs(e) {
    setJustifEcriture(e)
    setJustifInfo(null)
    setJustifReference('')
    setJustifDate(e.date_piece_fec || e.date_piece || e.date || '')
    setJustifMotif('')
    try {
      setJustifInfo(await ecrituresAPI.justificatifs(e.id))
    } catch (err) {
      notifier.erreur(err.message)
      setJustifEcriture(null)
    }
  }

  async function ajouterReferenceJustificative() {
    const reference = justifReference.trim()
    if (!reference || !justifEcriture) return
    setJustifSaving(true)
    try {
      await ecrituresAPI.ajouterJustificatif(justifEcriture.id, {
        reference,
        date_piece: justifDate || justifEcriture.date,
        motif: justifMotif.trim() || null,
      })
      const info = await ecrituresAPI.justificatifs(justifEcriture.id)
      setJustifInfo(info)
      setJustifReference('')
      setJustifMotif('')
      await recharger()
    } catch (err) {
      notifier.erreur(err.message)
    } finally {
      setJustifSaving(false)
    }
  }

  async function rafraichirJustificatifs() {
    if (!justifEcriture) return
    try {
      setJustifInfo(await ecrituresAPI.justificatifs(justifEcriture.id))
      await recharger()
    } catch {}
  }

  function libelleAction(action) {
    const labels = {
      creation_manuelle: 'Création manuelle',
      creation_systeme: 'Création système',
      modification: 'Modification',
      modification_systeme: 'Modification système',
      validation: 'Validation',
      validation_lot: 'Validation en lot',
      contrepassation: 'Contrepassation',
      suppression_brouillon: 'Suppression brouillon',
      suppression: 'Suppression',
      ligne_ajoutee: 'Ligne ajoutée',
      ligne_modifiee: 'Ligne modifiée',
      ligne_supprimee: 'Ligne supprimée',
      baseline_initiale: 'État initial au déploiement 07A',
      baseline_ligne: 'Ligne initiale au déploiement 07A',
    }
    return labels[action] || action || 'Événement'
  }

  function resumeAudit(ev) {
    if (ev.action === 'baseline_initiale') return 'Photographie initiale de l’écriture lors de l’installation de la piste d’audit'
    if (ev.table_cible === 'lignes_ecriture') {
      const x = ev.nouveau || ev.ancien || {}
      const montant = Number(x.debit || 0) > 0
        ? `Débit ${formatMAD(Number(x.debit || 0))}`
        : `Crédit ${formatMAD(Number(x.credit || 0))}`
      return `Ligne ${x.compte || '—'} · ${montant}`
    }
    const avant = ev.ancien || {}
    const apres = ev.nouveau || {}
    if (ev.action?.includes('devalidation')) return 'Écriture repassée en brouillon'
    if (ev.action?.includes('validation')) return 'Écriture rendue définitive'
    if (ev.action?.includes('suppression')) return `Suppression de « ${avant.libelle || 'écriture'} »`
    if (ev.action?.includes('creation')) return `Création de « ${apres.libelle || 'écriture'} »`
    const changements = []
    ;['numero_ecriture', 'date', 'date_piece', 'journal', 'libelle', 'reference'].forEach(k => {
      if (avant[k] !== apres[k]) changements.push(`${k}: ${avant[k] ?? '—'} → ${apres[k] ?? '—'}`)
    })
    return changements.length ? changements.join(' · ') : 'Données comptables modifiées'
  }

  async function toutValider() {
    if (validationEnCours) return
    const contexte = contexteValidation
    const aValider = ecrituresFiltrees.filter(e => !e.est_validee)
    if (!aValider.length) return setRetourValidation({ erreur: false, message: 'Aucune écriture en brouillon dans la sélection.' })
    if (!confirm(
      `Valider ${aValider.length} écriture(s) en brouillon ?\n\n` +
      `Elles deviendront définitives et ne pourront plus être modifiées.`
    )) return
    setRetourValidation(null)
    setValidationEnCours(true)
    try {
      const r = await validerLot(aValider.map(e => e.id))
      let msg = `${r.nb_validees} écriture(s) validée(s).`
      if (r.nb_refusees) {
        msg += `\n\n${r.nb_refusees} refusée(s) :\n` +
          r.refusees.map(x => `  n° ${x.id} : ${x.motif}`).join('\n')
      }
      if (contexteValidationRef.current === contexte) setRetourValidation({ erreur: Boolean(r.nb_refusees), message: msg })
    } catch (err) {
      if (contexteValidationRef.current === contexte) setRetourValidation({ erreur: true, message: err.message })
    } finally {
      if (contexteValidationRef.current === contexte) setValidationEnCours(false)
    }
  }


  const totaux = useMemo(() => {
    let debit = 0, credit = 0
    ecrituresFiltrees.forEach(e =>
      e.lignes.forEach(l => { debit += l.debit; credit += l.credit })
    )
    return { debit, credit }
  }, [ecrituresFiltrees])

  if (erreur) return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}><h1 className={styles.pageTitle}>Journal comptable</h1></div>
      <div className={styles.content}>
        <div role="alert" style={{ padding: 20, border: '1px solid var(--red)', borderRadius: 8 }}>
          <p>{erreur}</p>
          <button className={styles.btnSec} onClick={recharger}>Réessayer</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Journal comptable</h1>
        <div className={styles.topbarRight}>
          <button className={styles.btnSec} onClick={toutValider} disabled={!peutModifier || validationEnCours || chargement}
            title="Valider toutes les écritures en brouillon de la sélection">
            <i className="ti ti-checks" aria-hidden="true" /> {validationEnCours ? 'Validation en cours…' : 'Valider les brouillons'}
          </button>
          <button className={styles.btnSec} onClick={() => window.print()} disabled={!societe?.id} title="Imprimer le Journal complet">
            <i className="ti ti-printer" aria-hidden="true" /> Imprimer
          </button>
          <button className={styles.btnSec} onClick={exporterJournalCSV}
            disabled={chargement || Boolean(erreur) || ecrituresFiltrees.length === 0}>
            <i className="ti ti-download" aria-hidden="true" /> Exporter CSV
          </button>
          <button className={styles.btnSec} onClick={exporterFEC} disabled={exportFec}
            title="Export FEC HisabPro — 18 colonnes, écritures définitives uniquement">
            <i className="ti ti-file-export" aria-hidden="true" /> {exportFec ? 'Export...' : 'Export FEC'}
          </button>
          <button
            className={`${styles.btnPrim} ${!exerciceOuvert || !peutModifier ? styles.btnPrimBloque : ''}`}
            onClick={ouvrirNouvelleEcriture}
            disabled={!peutModifier}
            aria-disabled={!exerciceOuvert || !peutModifier}
            title={!peutModifier ? 'Consultation seule' : exerciceOuvert ? 'Créer une nouvelle écriture' : `Exercice ${annee} clôturé : cliquez pour afficher la raison`}>
            <i className="ti ti-plus" aria-hidden="true" /> Nouvelle écriture
          </button>
        </div>
      </div>

      {retourValidation && <div role={retourValidation.erreur ? 'alert' : 'status'} aria-label="Résultat de validation des écritures" style={{ padding: 12, marginBottom: 12, border: '1px solid var(--border-light)', borderRadius: 8, whiteSpace: 'pre-line', overflowWrap: 'anywhere' }}>
        <p>{retourValidation.message}</p><button className={styles.btnSec} onClick={() => setRetourValidation(null)}>Fermer le résultat de validation</button>
      </div>}

      <div className={styles.printMeta}>
        <LogoDocument societe={societe} />
        <strong>{societe?.raison_sociale || 'Société'}</strong>
        <span>Journal comptable — état unique</span>
        <span>Période : {exercice?.date_debut || `${annee}-01-01`} au {exercice?.date_fin || `${annee}-12-31`}</span>
        <span>Édité le {new Date().toLocaleString('fr-MA')} — HisabPro v{APP_VERSION}</span>
      </div>

      <div className={styles.content}>
        {/* Filtres */}
        <div className={styles.filtres}>
          <div className={styles.recherche}>
            <i className="ti ti-search" aria-hidden="true" />
            <input
              type="text"
              placeholder="Rechercher libellé, compte..."
              value={recherche}
              onChange={e => setRecherche(e.target.value)}
              className={styles.inputRecherche}
            />
            {recherche && (
              <button className={styles.clearBtn} onClick={() => setRecherche('')}>
                <i className="ti ti-x" aria-hidden="true" />
              </button>
            )}
          </div>

          <div className={styles.filtresBarre}>
            <select className={styles.inputDate} aria-label="État des écritures"
              value={filtreEtat} onChange={e => setFiltreEtat(e.target.value)}>
              <option value="toutes">Toutes les écritures</option>
              <option value="brouillons">Brouillons</option>
              <option value="validees">Validées</option>
            </select>
            {['TOUS', ...JOURNAUX.map(j => j.code)].map(code => (
              <button
                key={code}
                className={`${styles.filtreBtn} ${filtreJ === code ? styles.filtreBtnActif : ''}`}
                onClick={() => setFiltreJ(code)}
              >
                {code === 'TOUS'
                  ? 'Tous'
                  : `${code} — ${JOURNAUX.find(j => j.code === code)?.label}`}
              </button>
            ))}
            <input
              type="date"
              className={styles.inputDate}
              value={filtreDate}
              onChange={e => setFiltreDate(e.target.value)}
            />
            {filtreDate && (
              <button className={styles.clearBtn} onClick={() => setFiltreDate('')}>
                <i className="ti ti-x" aria-hidden="true" />
              </button>
            )}
          </div>

          {/* Groupement */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginRight: 4 }}>
              <i className="ti ti-layout-rows" style={{ marginRight: 4 }} />Grouper par :
            </span>
            {[
              { val: 'aucun',     label: 'Aucun' },
              { val: 'jour',      label: 'Jour' },
              { val: 'mois',      label: 'Mois' },
              { val: 'trimestre', label: 'Trimestre' },
            ].map(g => (
              <button key={g.val}
                className={`${styles.filtreBtn} ${groupement === g.val ? styles.filtreBtnActif : ''}`}
                onClick={() => setGroupement(g.val)}>
                {g.label}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.fullWidth}>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                {ecrituresFiltrees.length} écriture{ecrituresFiltrees.length !== 1 ? 's' : ''}
              </span>
              <div className={styles.totauxHeader}>
                <span>Débit : <strong>{formatMAD(totaux.debit)}</strong></span>
                <span>Crédit : <strong>{formatMAD(totaux.credit)}</strong></span>
              </div>
            </div>

            {chargement ? (
              <div className={styles.vide}>
                <i className="ti ti-loader-2" aria-hidden="true" />
                <span>Chargement des écritures...</span>
              </div>
            ) : ecrituresFiltrees.length === 0 ? (
              <div className={styles.vide}>
                <i className="ti ti-inbox" aria-hidden="true" />
                <span>Aucune écriture trouvée</span>
              </div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.tableJournal}>
                  <thead>
                    <tr>
                      <th className={styles.thNum}>N°</th>
                      <th style={{ width: 88 }}>Date</th>
                      <th style={{ width: 62 }}>Journal</th>
                      <th style={{ width: 78 }}>Compte</th>
                      <th>Libellé</th>
                      <th className={styles.thMontant}>Débit</th>
                      <th className={styles.thMontant}>Crédit</th>
                      <th style={{ width: 74 }} title="Code de lettrage : rapproche une facture de son règlement">
                        Lettrage
                      </th>
                      <th style={{ width: 118 }} title="Numéro interne séquentiel de l’écriture">
                        N° écriture
                      </th>
                      <th style={{ width: 118 }} title="Référence du document justificatif (facture, bon, relevé…)">
                        Pièce
                      </th>
                      <th style={{ width: 56 }} />
                    </tr>
                  </thead>
                  <tbody>
                    {ecrituresGroupees.map(groupe => {
                      const totGrp = groupe.ecritures.reduce((acc, e) => {
                        e.lignes.forEach(l => { acc.d += l.debit; acc.c += l.credit })
                        return acc
                      }, { d: 0, c: 0 })

                      return (
                        <React.Fragment key={`grp-${groupe.cle ?? 'all'}`}>
                          {/* Bandeau de groupe (jour / mois / trimestre) */}
                          {groupe.label && (
                            <tr className={styles.rowGroupe}>
                              <td colSpan={5}>
                                <i className="ti ti-calendar" style={{ marginRight: 6, fontSize: 11 }} />
                                {groupe.label}
                                <span className={styles.grpCount}>
                                  {groupe.ecritures.length} écriture{groupe.ecritures.length > 1 ? 's' : ''}
                                </span>
                              </td>
                              <td className={styles.tdMontant}>{formatMAD(totGrp.d)}</td>
                              <td className={styles.tdMontant}>{formatMAD(totGrp.c)}</td>
                              <td colSpan={4} />
                            </tr>
                          )}

                          {/* Format à plat : une ligne du tableau = un mouvement comptable */}
                          {groupe.ecritures.map(e => {
                            const desequilibre = Math.abs(
                              e.lignes.reduce((s, l) => s + (l.debit || 0) - (l.credit || 0), 0)
                            ) > 0.01
                            return e.lignes.map((l, i) => {
                              const intitule = trouverCompteLecture(l.compte, getToken())?.libelle || ''
                              // Libellé du mouvement : celui de la ligne s'il apporte
                              // une information, sinon celui de l'écriture.
                              const lib = (l.libelle && l.libelle !== intitule) ? l.libelle : e.libelle
                              const premiere = i === 0
                              const derniere = i === e.lignes.length - 1
                              return (
                                <tr key={`${e.id}-${i}`}
                                  className={[
                                    styles.rowMvt,
                                    premiere ? styles.rowMvtDebut : '',
                                    derniere ? styles.rowMvtFin : '',
                                  ].join(' ')}>
                                  <td className={styles.tdNumLigne}>{numerosLigne.get(`${e.id}-${i}`)}</td>
                                  {/* Colonnes communes à toute l'écriture : fusionnées
                                      verticalement et centrées sur ses lignes. */}
                                  {premiere && (
                                    <td className={styles.tdFusion} rowSpan={e.lignes.length}>
                                      {formatDate(e.date)}
                                    </td>
                                  )}
                                  {premiere && (
                                    <td className={styles.tdFusion} rowSpan={e.lignes.length}>
                                      <BadgeJournal code={e.journal} />
                                    </td>
                                  )}
                                  <td><span className={styles.compteBadge}>{l.compte}</span></td>
                                  <td className={styles.tdLibelle}>
                                    <span className={styles.libTexte}>
                                      {lib}
                                      {premiere && !e.est_validee && (
                                        <span title="Écriture en brouillon : modifiable, non définitive"
                                          style={{ marginLeft: 8, fontSize: 9.5, padding: '1px 7px',
                                            borderRadius: 20, background: '#FDF3E3', color: '#8A5A0B',
                                            fontWeight: 500, verticalAlign: 'middle' }}>
                                          brouillon
                                        </span>
                                      )}
                                    </span>
                                    {intitule && (
                                      <span className={styles.libCompte}>{intitule}</span>
                                    )}
                                  </td>
                                  <td className={`${styles.tdMontant} ${styles.tdDebit}`}>
                                    {l.debit > 0 ? formatMAD(l.debit) : ''}
                                  </td>
                                  <td className={`${styles.tdMontant} ${styles.tdCredit}`}>
                                    {l.credit > 0 ? formatMAD(l.credit) : ''}
                                  </td>
                                  <td className={styles.tdLettrage}>{l.code_lettrage || ''}</td>
                                  {premiere && (
                                    <td className={`${styles.tdFusion} ${styles.tdMvt}`} rowSpan={e.lignes.length}
                                      title={`ID technique : ${e.id}`}>
                                      {numeroAffiche(e)}
                                    </td>
                                  )}
                                  {premiere && (
                                    <td className={`${styles.tdFusion} ${styles.tdPiece}`}
                                      rowSpan={e.lignes.length} title={e.reference_fec || e.reference || ''}>
                                      {e.reference_fec || e.reference || '—'}
                                    </td>
                                  )}
                                  {premiere && (
                                    <td className={`${styles.tdFusion} ${styles.tdActions}`} rowSpan={e.lignes.length}>
                                      <div className={styles.actionsGroupe}>
                                        {desequilibre && (
                                          <i className="ti ti-alert-triangle" title="Écriture déséquilibrée"
                                            style={{ color: '#A32D2D', fontSize: 13 }} />
                                        )}
                                        <button className={styles.btnAction} onClick={() => ouvrirJustificatifs(e)}
                                          aria-label="Justificatifs"
                                          title={`Justificatifs${e.nb_justificatifs ? ` (${e.nb_justificatifs})` : ''}`}><i className="ti ti-paperclip" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">{`Justificatifs${e.nb_justificatifs ? ` (${e.nb_justificatifs})` : ''}`}</span></button>
                                        <button className={styles.btnAction} onClick={() => ouvrirAudit(e)}
                                          aria-label="Piste d'audit" title="Voir l'historique et la piste d'audit"><i className="ti ti-history" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Voir l'historique et la piste d'audit</span></button>
                                        {peutModifier && (e.est_validee ? (
                                          <button className={styles.btnAction} onClick={() => contrepasser(e)}
                                            aria-label="Contrepasser"
                                            title="Écriture définitive — créer une contrepassation traçable"
                                            style={{ color: '#8A5A0B' }}><i className="ti ti-arrow-back-up" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Écriture définitive</span></button>
                                        ) : (
                                          <>
                                            <button className={styles.btnAction} onClick={() => valider(e)}
                                              aria-label="Valider" title="Valider : rend l'écriture définitive"
                                              style={{ color: 'var(--blue)' }}><i className="ti ti-check" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Valider</span></button>
                                            <button className={styles.btnAction} onClick={() => setEcritureEdit(e)}
                                              aria-label="Modifier" title="Modifier l'écriture"><i className="ti ti-pencil" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Modifier l'écriture</span></button>
                                            {!e.numero_ecriture && (
                                              <button className={styles.btnTrash} onClick={() => supprimerEcriture(e.id)}
                                                aria-label="Supprimer" title="Supprimer le brouillon non numéroté"><i className="ti ti-trash" aria-hidden="true" /><span className="libelle-action" aria-hidden="true">Supprimer le brouillon non numéroté</span></button>
                                            )}
                                          </>
                                        ))}
                                      </div>
                                    </td>
                                  )}
                                </tr>
                              )
                            })
                          })}
                        </React.Fragment>
                      )
                    })}
                    {/* Totaux généraux */}
                    <tr className={styles.rowTotalGeneral}>
                      <td colSpan={5}>Total {groupement === 'aucun' ? 'général' : 'de la sélection'}</td>
                      <td className={styles.tdMontant}>{formatMAD(totaux.debit)}</td>
                      <td className={styles.tdMontant}>{formatMAD(totaux.credit)}</td>
                      <td colSpan={4} />
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Modal formulaire nouvelle écriture */}
        {showForm && (
          <FormulaireEcriture
            onFermer={() => setShowForm(false)}
            onSuccess={() => setShowForm(false)}
          />
        )}

        {/* Modal édition écriture */}
        {ecritureEdit && (
          <FormulaireEcriture
            ecriture={ecritureEdit}
            onFermer={() => setEcritureEdit(null)}
            onSuccess={() => setEcritureEdit(null)}
          />
        )}

        {justifEcriture && (
          <div className={styles.auditOverlay} onMouseDown={ev => { if (ev.target === ev.currentTarget) setJustifEcriture(null) }}>
            <div className={styles.auditModal}>
              <div className={styles.auditHeader}>
                <div>
                  <strong>Justificatifs — {numeroAffiche(justifEcriture)}</strong>
                  <div className={styles.auditSubtitle}>
                    Référence FEC : {justifInfo?.reference_fec || justifEcriture.reference_fec || justifEcriture.reference || 'à compléter'}
                    {' · '}Date pièce : {justifInfo?.date_piece_fec || justifEcriture.date_piece_fec || justifEcriture.date_piece || justifEcriture.date}
                  </div>
                </div>
                <button className={styles.auditClose} onClick={() => setJustifEcriture(null)} aria-label="Fermer">
                  <i className="ti ti-x" />
                </button>
              </div>
              <div className={styles.auditNotice}>
                La validation comptable reste légère : ces informations peuvent être complétées après coup sans modifier l’écriture définitive.
              </div>
              <div className={styles.auditBody}>
                {peutModifier && <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 160px', gap: 10, alignItems: 'end' }}>
                  <label style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                    Référence du justificatif
                    <input value={justifReference} onChange={e => setJustifReference(e.target.value)}
                      placeholder="N° facture, relevé, contrat…"
                      style={{ width: '100%', marginTop: 5, padding: '8px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
                  </label>
                  <label style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                    Date
                    <input type="date" value={justifDate} onChange={e => setJustifDate(e.target.value)}
                      style={{ width: '100%', marginTop: 5, padding: '8px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
                  </label>
                </div>
                <label style={{ display: 'block', marginTop: 10, fontSize: 11, color: 'var(--text-secondary)' }}>
                  Motif / note (facultatif)
                  <input value={justifMotif} onChange={e => setJustifMotif(e.target.value)}
                    placeholder="Ex. référence complétée après réception du document"
                    style={{ width: '100%', marginTop: 5, padding: '8px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }} />
                </label>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                  <button className={styles.btnPrim} onClick={ajouterReferenceJustificative}
                    disabled={justifSaving || !justifReference.trim()}>
                    <i className="ti ti-link" /> {justifSaving ? 'Ajout…' : 'Ajouter la référence'}
                  </button>
                </div>
                </>}

                {justifInfo?.complements?.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>Historique documentaire</div>
                    {justifInfo.complements.slice().reverse().map(j => (
                      <div key={j.id} style={{ padding: '7px 9px', borderBottom: '0.5px solid var(--border-light)', fontSize: 11 }}>
                        <strong>{j.reference}</strong> · {j.date_piece}
                        <span style={{ color: 'var(--text-tertiary)', marginLeft: 7 }}>{j.source_type === 'fichier' ? 'pièce jointe' : 'référence ajoutée'}</span>
                        {j.prioritaire && <span style={{ marginLeft: 7, color: 'var(--blue)' }}>utilisée pour le FEC</span>}
                      </div>
                    ))}
                  </div>
                )}

                <PiecesJointes docType="ecriture" docId={justifEcriture.id} readOnly={!peutModifier} preserveExisting={Boolean(justifEcriture.est_validee)} onChange={rafraichirJustificatifs} />
              </div>
            </div>
          </div>
        )}


        {fecControle && !fecControle.conforme_export && (
          <div className={styles.auditOverlay} onMouseDown={ev => { if (ev.target === ev.currentTarget) setFecControle(null) }}>
            <div className={styles.auditModal} style={{ width: 'min(920px, 96vw)' }}>
              <div className={styles.auditHeader}>
                <div>
                  <strong>Contrôle FEC — {fecControle.nb_bloquants || 0} anomalie(s) bloquante(s)</strong>
                  <div className={styles.auditSubtitle}>
                    Exercice {annee} · {fecControle.nb_ecritures_validees || 0} écriture(s) validée(s) · {fecControle.nb_lignes || 0} ligne(s)
                  </div>
                </div>
                <button className={styles.auditClose} onClick={() => setFecControle(null)} aria-label="Fermer">
                  <i className="ti ti-x" />
                </button>
              </div>
              <div className={styles.auditNotice} style={{ background: '#fff7ed', color: '#8a4b08' }}>
                Export bloqué. La liste ci-dessous est exhaustive : aucune anomalie n’est masquée.
                {peutModifier ? <>HisabPro a d’abord récupéré automatiquement ce qui pouvait l’être sans ambiguïté depuis
                les factures sources ; seules les anomalies restantes sont affichées et les écritures définitives ne sont pas modifiées.</>
                : <>Consultation seule : les anomalies sont affichées sans tentative de réparation. Les compléments sont réservés aux profils autorisés.</>}
              </div>
              <div className={styles.auditBody}>
                {(fecControle.bloquants || []).map((a, i) => {
                  const ecriture = a.ecriture_id ? ecritures.find(e => Number(e.id) === Number(a.ecriture_id)) : null
                  const numero = a.numero_ecriture || (ecriture ? numeroAffiche(ecriture) : null)
                  const contexte = [
                    numero ? `Écriture ${numero}` : null,
                    a.journal || ecriture?.journal || null,
                    ecriture?.date || null,
                    ecriture?.libelle || null,
                    a.details?.compte ? `Compte ${a.details.compte}` : null,
                  ].filter(Boolean).join(' · ')
                  return (
                    <div key={`${a.code || 'ANOMALIE'}-${a.ecriture_id || 'global'}-${i}`}
                      style={{ padding: '10px 0', borderBottom: '0.5px solid var(--border-light)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 999, background: '#FCEBEB', color: '#A32D2D' }}>
                          {a.code || 'ANOMALIE'}
                        </span>
                        {contexte && <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{contexte}</span>}
                      </div>
                      <div style={{ marginTop: 5, fontSize: 12, lineHeight: 1.45, color: 'var(--text-primary)' }}>
                        {a.message}
                      </div>

                      {peutModifier && a.code === 'REFERENCE_PIECE_MANQUANTE' && a.ecriture_id && (
                        <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                          <input
                            value={fecFixValues[cleCorrectionFec(a, i)]?.reference || ''}
                            onChange={ev => {
                              const key = cleCorrectionFec(a, i)
                              setFecFixValues(v => ({ ...v, [key]: { ...(v[key] || {}), reference: ev.target.value } }))
                            }}
                            placeholder="Référence du justificatif existant"
                            style={{ minWidth: 270, flex: '1 1 300px' }}
                          />
                          <button
                            className={styles.btnSec}
                            disabled={fecFixSaving === cleCorrectionFec(a, i) || !String(fecFixValues[cleCorrectionFec(a, i)]?.reference || '').trim()}
                            onClick={() => corrigerReferenceFec(a, i, ecriture)}
                          >
                            {fecFixSaving === cleCorrectionFec(a, i) ? 'Ajout...' : 'Ajouter la référence'}
                          </button>
                        </div>
                      )}

                      {peutModifier && a.code === 'AUXILIAIRE_MANQUANT' && a.ecriture_id && a.details?.ligne_ecriture_id && (
                        <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                          <select
                            value={fecFixValues[cleCorrectionFec(a, i)]?.tiers_id || ''}
                            onChange={ev => {
                              const key = cleCorrectionFec(a, i)
                              setFecFixValues(v => ({ ...v, [key]: { ...(v[key] || {}), tiers_id: ev.target.value } }))
                            }}
                            style={{ minWidth: 270, flex: '1 1 300px' }}
                          >
                            <option value="">Sélectionner le tiers historique exact…</option>
                            {fecTiers
                              .filter(t => {
                                const client = String(a.details?.compte || '').startsWith('3421')
                                return client ? ['client', 'les_deux'].includes(t.type) : ['fournisseur', 'les_deux'].includes(t.type)
                              })
                              .map(t => (
                                <option key={t.id} value={t.id}>
                                  {t.nom}{t.ice ? ` · ICE ${t.ice}` : ''}
                                </option>
                              ))}
                          </select>
                          <button
                            className={styles.btnSec}
                            disabled={fecFixSaving === cleCorrectionFec(a, i) || !fecFixValues[cleCorrectionFec(a, i)]?.tiers_id}
                            onClick={() => corrigerAuxiliaireFec(a, i)}
                          >
                            {fecFixSaving === cleCorrectionFec(a, i) ? 'Association...' : 'Associer ce tiers'}
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {auditEcriture && (
          <div className={styles.auditOverlay} onMouseDown={ev => { if (ev.target === ev.currentTarget) setAuditEcriture(null) }}>
            <div className={styles.auditModal}>
              <div className={styles.auditHeader}>
                <div>
                  <strong>Piste d'audit — {numeroAffiche(auditEcriture)}</strong>
                  <div className={styles.auditSubtitle}>
                    {auditEcriture.date} · {auditEcriture.journal} · {auditEcriture.libelle}
                    {(auditEcriture.reference_fec || auditEcriture.reference) ? ` · pièce ${auditEcriture.reference_fec || auditEcriture.reference}` : ''}
                  </div>
                </div>
                <button className={styles.auditClose} onClick={() => setAuditEcriture(null)} aria-label="Fermer">
                  <i className="ti ti-x" />
                </button>
              </div>
              <div className={styles.auditNotice}>
                Piste d’audit append-only : les opérations historiques sont conservées ; une écriture définitive se corrige par contrepassation.
              </div>
              <div className={styles.auditBody}>
                {auditLoading ? (
                  <div className={styles.auditEmpty}>Chargement…</div>
                ) : auditEvents.length === 0 ? (
                  <div className={styles.auditEmpty}>Aucun événement enregistré pour cette écriture.</div>
                ) : auditEvents.map(ev => (
                  <div className={styles.auditEvent} key={ev.id}>
                    <div className={styles.auditDot} />
                    <div className={styles.auditEventMain}>
                      <div className={styles.auditEventTop}>
                        <strong>{libelleAction(ev.action)}</strong>
                        <span>{new Date(ev.created_at).toLocaleString('fr-MA')}</span>
                      </div>
                      <div className={styles.auditSummary}>{resumeAudit(ev)}</div>
                      <div className={styles.auditMeta}>
                        {ev.acteur_nom || ev.acteur_email
                          ? `${ev.acteur_nom || ev.acteur_email}${ev.acteur_role ? ` · ${ev.acteur_role}` : ''}`
                          : 'Action système / origine non attribuée'}
                        {ev.table_cible === 'lignes_ecriture' && ev.ligne_id ? ` · ligne #${ev.ligne_id}` : ''}
                      </div>
                      {ev.motif && <div className={styles.auditMotif}><strong>Motif :</strong> {ev.motif}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
