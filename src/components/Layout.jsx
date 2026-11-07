import { useEffect, useState, useRef, useCallback } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import SelecteurSociete from './SelecteurSociete.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { API_BASE, getToken, planComptableAPI, estAdmin, formatErreurAPI } from '../services/api.js'
import { cleCachePlan, restaurerPlanSociete, enregistrerPlanSociete, EVENEMENT_PLAN_MODIFIE } from '../data/planComptableCache.js'
import styles from './Layout.module.css'

const LABEL_STATUT = {
  ouvert: 'Ouvert',
  a_venir: 'À venir',
  cloture: 'Clôturé',
}

function formatDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

export default function Layout() {
  const location = useLocation()
  const [menuOuvert, setMenuOuvert] = useState(false)
  const boutonMenu = useRef(null)
  const fermerMenu = useCallback(() => {
    setMenuOuvert(false)
    boutonMenu.current?.focus()
  }, [])
  useEffect(() => { setMenuOuvert(false) }, [location.pathname])
  const { societe, chargement: chargementSociete } = useModules()
  // Cache disponible synchroniquement, avant le moindre aller-retour réseau.
  const [planClePrete, setPlanClePrete] = useState(() => restaurerPlanSociete(getToken()))
  const [planRevision, setPlanRevision] = useState(0)
  const [erreurPlan, setErreurPlan] = useState('')
  const [relancePlan, setRelancePlan] = useState(0)
  const [preparationPlan, setPreparationPlan] = useState(false)
  const {
    annee, setAnnee, exercice, exercices,
    chargementExercices, erreurExercices, rechargerExercices, exercicePrecedent, exerciceSuivant,
  } = useExercice()

  const cleSociete = societe?.id ? cleCachePlan(getToken(), societe.id) : null
  const planPret = chargementSociete
    ? Boolean(planClePrete)
    : (!societe?.id || (Boolean(cleSociete) && planClePrete === cleSociete))

  useEffect(() => {
    if (chargementSociete || !societe?.id || !cleSociete) return
    let actif = true
    const cle = cleSociete
    // Sur un changement de société, restaurer uniquement son propre plan.
    const enCache = restaurerPlanSociete(getToken(), societe.id)
    if (enCache) setPlanClePrete(cle)
    else setPlanClePrete(null)
    setErreurPlan('')
    planComptableAPI.lister(true)
      .then(rows => {
        if (!actif || cleCachePlan(getToken(), societe.id) !== cle) return
        const { modifie } = enregistrerPlanSociete(rows, getToken(), societe.id)
        setPlanClePrete(cle)
        setErreurPlan('')
        if (modifie) setPlanRevision(v => v + 1)
      })
      .catch(err => {
        if (!actif) return
        console.error('Erreur actualisation du plan comptable société', err)
        setErreurPlan(err?.message || 'Plan comptable inaccessible.')
        // En présence du cache, conserver l'affichage sans masquer l'erreur.
        // À froid, ne jamais substituer le plan d'une autre entreprise.
        if (!enCache) setPlanClePrete(null)
      })
    return () => { actif = false }
  }, [societe?.id, chargementSociete, cleSociete, relancePlan])

  useEffect(() => {
    function actualisationLocale(event) {
      if (event.detail?.cle === cleCachePlan(getToken())) {
        setPlanRevision(v => v + 1)
      }
    }
    window.addEventListener(EVENEMENT_PLAN_MODIFIE, actualisationLocale)
    return () => window.removeEventListener(EVENEMENT_PLAN_MODIFIE, actualisationLocale)
  }, [])

  async function initialiserPlan() {
    setPreparationPlan(true)
    try {
      const response = await fetch(`${API_BASE}/api/plan-comptable/initialiser`, {
        method: 'POST', headers: { Authorization: `Bearer ${getToken()}` },
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(formatErreurAPI(data.detail))
      setRelancePlan(n => n + 1)
    } catch (error) { setErreurPlan(error.message) }
    finally { setPreparationPlan(false) }
  }

  return (
    <div className={styles.layout}>
      <Sidebar mobileOuvert={menuOuvert} onFermer={fermerMenu} />
      {menuOuvert && <button type="button" className={styles.voileNavigation}
        aria-label="Fermer la navigation" onClick={fermerMenu} />}

      <div className={styles.main}>
        <div className={styles.topbar}>
          <button type="button" ref={boutonMenu} className={styles.menuMobile}
            aria-label="Ouvrir la navigation" aria-controls="navigation-principale"
            aria-expanded={menuOuvert} onClick={() => setMenuOuvert(v => !v)}>
            <i className="ti ti-menu-2" aria-hidden="true" />
          </button>
          <div className={styles.exerciceBar}>
            <i className="ti ti-calendar" aria-hidden="true" />
            <span className={styles.exerciceLabel}>Exercice</span>

            <button
              type="button"
              className={styles.navExerciceBtn}
              disabled={!exercicePrecedent}
              title={exercicePrecedent ? `Exercice ${exercicePrecedent.annee}` : 'Aucun exercice précédent'}
              onClick={() => exercicePrecedent && setAnnee(exercicePrecedent.annee)}>
              <i className="ti ti-chevron-left" />
            </button>

            <div className={styles.exerciceSelectWrap}>
              <select
                aria-label="Exercice comptable"
                className={styles.exerciceSelect}
                value={annee}
                disabled={chargementExercices || !exercices.length}
                onChange={e => setAnnee(Number(e.target.value))}>
                {!exercices.length && <option value={annee}>{annee}</option>}
                {[...exercices].reverse().map(ex => (
                  <option key={ex.id || ex.annee} value={ex.annee}>
                    {ex.libelle || ex.annee} — {LABEL_STATUT[ex.statut] || ex.statut}
                  </option>
                ))}
              </select>
              <i className="ti ti-chevron-down" aria-hidden="true" />
            </div>

            <button
              type="button"
              className={styles.navExerciceBtn}
              disabled={!exerciceSuivant}
              title={exerciceSuivant ? `Exercice ${exerciceSuivant.annee}` : 'Aucun exercice suivant'}
              onClick={() => exerciceSuivant && setAnnee(exerciceSuivant.annee)}>
              <i className="ti ti-chevron-right" />
            </button>

            {exercice && (
              <span className={`${styles.exerciceStatut} ${styles[`statut_${exercice.statut}`] || ''}`}>
                {LABEL_STATUT[exercice.statut] || exercice.statut}
              </span>
            )}
          </div>

          <div className={styles.topbarRight}>
            <SelecteurSociete
              societeActuelle={societe?.raison_sociale}
              onSwitch={() => {}}
            />
            <span className={styles.periodeLabel}>
              {erreurExercices ? 'Calendrier indisponible' : exercice
                ? `${formatDate(exercice.date_debut)} — ${formatDate(exercice.date_fin)}`
                : `01/01/${annee} — 31/12/${annee}`}
            </span>
          </div>
        </div>

        <main className={styles.content}>
          {erreurExercices && (
            <div role="alert" aria-label="Calendrier indisponible" style={{ padding: '9px 20px', fontSize: 12, color: 'var(--red)' }}>
              Calendrier indisponible : {erreurExercices}{' '}
              <button type="button" disabled={chargementExercices}
                onClick={() => rechargerExercices().catch(() => {})}>Réessayer le calendrier</button>
            </div>
          )}
          {erreurPlan && (
            <div role="alert" style={{ padding: '9px 20px', fontSize: 12, color: 'var(--red)' }}>
              Plan comptable non actualisé : {erreurPlan}{' '}
              <button type="button" disabled={preparationPlan} onClick={() => setRelancePlan(n => n + 1)}>Réessayer</button>
              {estAdmin() && !planPret && <button type="button" disabled={preparationPlan} onClick={initialiserPlan}
                style={{ marginLeft: 8 }}>Initialiser le plan de cette société</button>}
            </div>
          )}
          {planPret ? (
            <Outlet key={`${cleSociete || planClePrete || 'initial'}:${planRevision}`} />
          ) : !erreurPlan ? (
            <div style={{ padding: 24, fontSize: 13 }} role="status">
              Chargement du plan comptable de cette société…
            </div>
          ) : null}
        </main>
      </div>
    </div>
  )
}
