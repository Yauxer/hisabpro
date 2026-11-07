import { useState, useMemo, useEffect } from 'react'
import { formatMAD, formatDate } from '../data/donnees.js'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { useFactures } from '../data/FacturesContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import FormulaireEcriture from '../components/FormulaireEcriture.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { API_BASE, ecrituresAPI } from '../services/api.js'
import { useNavigate } from 'react-router-dom'
import styles from './Dashboard.module.css'
import DashboardCommercial from '../components/DashboardCommercial.jsx'
import { factureEnRetard, joursAvantEcheance } from '../utils/echeancesFactures.js'
import { notifier } from '../services/notifications.js'
import AFaire from '../components/AFaire.jsx'

// ─── Carte KPI ───────────────────────────────────────────────────────────────
function CarteKPI({ icone, label, valeur, sous, couleur }) {
  return (
    <div className={styles.kpiCard}>
      <div className={styles.kpiLabel}>
        <i className={`ti ${icone}`} style={{ color: couleur }} aria-hidden="true" />
        {label}
      </div>
      <div className={styles.kpiValeur}>{formatMAD(valeur)}<span className={styles.kpiDevise}> MAD</span></div>
      {sous && <div className={styles.kpiSous} style={{ color: couleur }}>{sous}</div>}
    </div>
  )
}

// ─── Badge journal ────────────────────────────────────────────────────────────
function BadgeJournal({ code }) {
  const couleurs = {
    AC: { bg: '#EAF3DE', color: '#3B6D11' },
    VT: { bg: '#E6F1FB', color: '#185FA5' },
    BQ: { bg: '#FAEEDA', color: '#854F0B' },
    CA: { bg: '#FBEAF0', color: '#993556' },
    OD: { bg: '#EEEDFE', color: '#534AB7' },
  }
  const c = couleurs[code] || { bg: '#f0efed', color: '#5a5955' }
  return (
    <span className={styles.badge} style={{ background: c.bg, color: c.color }}>
      {code}
    </span>
  )
}

// ─── Page Dashboard ───────────────────────────────────────────────────────────
export default function Dashboard() {
  const [showForm, setShowForm] = useState(false)

  const { ecritures, erreur: erreurEcritures, chargement: chargementEcritures, recharger: rechargerEcritures } = useEcritures()
  // Écritures en attente de validation, les plus anciennes d'abord :
  // ce sont elles qui bloquent la clôture et méritent l'attention.
  const ecrituresAValider = useMemo(
    () => ecritures
      .filter(e => !e.est_validee)
      .sort((a, b) => new Date(a.date) - new Date(b.date)),
    [ecritures])
  const { factures }  = useFactures()
  const { aFacturation, societe } = useModules()
  const { annee, exercice } = useExercice()
  const exerciceOuvert = !exercice || exercice.statut === 'ouvert'
  const [kpisAPI, setKpisAPI] = useState(null)
  const [alertesStock, setAlertesStock] = useState([])
  const [showDrilldown, setShowDrilldown] = useState(false)
  const [alertesOuvertes, setAlertesOuvertes] = useState(new Set())
  const [alertesVisibles, setAlertesVisibles] = useState(() => {
    const v = localStorage.getItem('hisabpro_alertes_visibles')
    return v === null ? true : v === 'true'
  })
  const [filtrePeriode, setFiltrePeriode] = useState('annee')  // annee | T1 | T2 | T3 | T4 | M1..M12
  const navigate = useNavigate()

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

  function toggleAlertesVisibles() {
    setAlertesVisibles(prev => {
      const next = !prev
      localStorage.setItem('hisabpro_alertes_visibles', String(next))
      return next
    })
  }

  function toggleAlerte(key) {
    setAlertesOuvertes(prev => {
      const n = new Set(prev)
      n.has(key) ? n.delete(key) : n.add(key)
      return n
    })
  }

  useEffect(() => {
    ecrituresAPI.kpi(annee)
      .then(setKpisAPI)
      .catch(() => setKpisAPI(null))
  }, [annee])

  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    fetch(API_BASE + '/api/articles', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(arts => {
        const enAlerte = arts.filter(a => a.actif && a.stock_actuel !== null && a.stock_actuel <= 0)
        const faible   = arts.filter(a => a.actif && a.stock_actuel > 0 && a.stock_actuel < 5)
        setAlertesStock({ rupture: enAlerte, faible })
      })
      .catch(() => {})
  }, [])

  const [bonsCommande, setBonsCommande] = useState([])
  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    fetch(`${API_BASE}/api/bons-commande?exercice=${annee}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setBonsCommande)
      .catch(() => setBonsCommande([]))
  }, [annee])

  const [devis, setDevis] = useState([])
  useEffect(() => {
    const token = localStorage.getItem('hisabpro_token')
    fetch(`${API_BASE}/api/devis?exercice=${annee}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setDevis)
      .catch(() => setDevis([]))
  }, [annee])

  // Alertes : factures en retard de paiement
  const alertes = useMemo(() => {
    if (!aFacturation) return []
    const aujourd = new Date()
    const enRetard = factures.filter(f => factureEnRetard(f, aujourd))
    const urgentes = factures.filter(f => {
      const jours = joursAvantEcheance(f, aujourd)
      return jours !== null && jours >= 0 && jours <= 7
    })
    const liste = []
    if (enRetard.length > 0) {
      liste.push({
        key: 'factures-retard',
        type: 'danger',
        icon: 'ti-clock-exclamation',
        message: `${enRetard.length} facture${enRetard.length > 1 ? 's' : ''} en retard de paiement`,
        cible: 'Voir les factures',
        action: () => navigate('/factures'),
        items: enRetard.map(f => ({
          label: f.numero, sousLabel: f.tiers,
          droite: f.montants_valides === false ? 'Montants à vérifier' : `${formatMAD(f.total_ttc)} MAD`,
        })),
      })
    }
    if (urgentes.length > 0) {
      liste.push({
        key: 'factures-urgentes',
        type: 'warning',
        icon: 'ti-clock',
        message: `${urgentes.length} facture${urgentes.length > 1 ? 's arrivent' : ' arrive'} à échéance dans moins de 7 jours`,
        cible: 'Voir les factures',
        action: () => navigate('/factures'),
        items: urgentes.map(f => ({
          label: f.numero, sousLabel: f.tiers,
          droite: f.montants_valides === false ? 'Montants à vérifier' : `${formatMAD(f.total_ttc)} MAD`,
        })),
      })
    }
    // BC en retard de livraison
    const bcEnRetard = bonsCommande.filter(bc => {
      if (['livre', 'annule'].includes(bc.statut)) return false
      if (!bc.date_livraison) return false
      const [y, m, d] = bc.date_livraison.split('-').map(Number)
      const dl = new Date(y, m - 1, d)
      return dl < aujourd
    })
    if (bcEnRetard.length > 0) {
      liste.push({
        key: 'bc-retard',
        type: 'danger',
        icon: 'ti-truck-off',
        message: `${bcEnRetard.length} bon${bcEnRetard.length > 1 ? 's' : ''} de commande en retard de livraison`,
        cible: 'Voir le commercial',
        action: () => navigate('/commercial'),
        items: bcEnRetard.map(bc => ({
          label: bc.numero, sousLabel: bc.tiers,
          droite: bc.date_livraison ? formatDate(bc.date_livraison) : '',
        })),
      })
    }
    // Devis expirés (date + validité dépassée) mais encore en brouillon/envoyé
    const devisOuverts = devis.filter(d => d.statut === 'brouillon' || d.statut === 'envoye')
    function dateExpiration(d) {
      if (!d.date) return null
      const [y, m, j] = d.date.split('-').map(Number)
      const dt = new Date(y, m - 1, j)
      dt.setDate(dt.getDate() + (d.validite_jours || 30))
      return dt
    }
    const devisExpires = devisOuverts.filter(d => {
      const exp = dateExpiration(d)
      return exp && exp < aujourd
    })
    const devisBientotExpires = devisOuverts.filter(d => {
      const exp = dateExpiration(d)
      if (!exp) return false
      const jours = Math.ceil((exp - aujourd) / (1000 * 60 * 60 * 24))
      return jours >= 0 && jours <= 5
    })
    if (devisExpires.length > 0) {
      liste.push({
        key: 'devis-expires',
        type: 'danger',
        icon: 'ti-file-x',
        message: `${devisExpires.length} devis expiré${devisExpires.length > 1 ? 's' : ''} à traiter`,
        cible: 'Voir les devis',
        action: () => navigate('/commercial'),
        items: devisExpires.map(d => ({
          label: d.numero, sousLabel: d.tiers,
          droite: `${formatMAD(d.total_ttc)} MAD`,
        })),
      })
    }
    if (devisBientotExpires.length > 0) {
      liste.push({
        key: 'devis-bientot',
        type: 'warning',
        icon: 'ti-hourglass-low',
        message: `${devisBientotExpires.length} devis arrive${devisBientotExpires.length > 1 ? 'nt' : ''} à expiration dans moins de 5 jours`,
        cible: 'Voir les devis',
        action: () => navigate('/commercial'),
        items: devisBientotExpires.map(d => ({
          label: d.numero, sousLabel: d.tiers,
          droite: `${formatMAD(d.total_ttc)} MAD`,
        })),
      })
    }
    return liste
  }, [factures, bonsCommande, devis, aFacturation, navigate])

  // Fallback : calcul local si l'API ne répond pas
  const kpisLocal = useMemo(() => {
    let ca = 0, charges = 0, tva = 0
    ecritures.forEach(e => {
      e.lignes.forEach(l => {
        if (l.compte.startsWith('7') && l.credit > 0) ca += l.credit
        if (l.compte.startsWith('6') && l.debit > 0) charges += l.debit
        if (l.compte.startsWith('4455') && l.credit > 0) tva += l.credit
        if (l.compte.startsWith('3455') && l.debit > 0) tva -= l.debit
      })
    })
    return { ca, charges, resultat: ca - charges, tvaDue: Math.max(0, tva) }
  }, [ecritures])

  const kpis = kpisAPI
    ? {
        ca:       kpisAPI.chiffre_affaires,
        charges:  kpisAPI.charges,
        resultat: kpisAPI.resultat_net,
        tvaDue:   kpisAPI.tva_due,
      }
    : kpisLocal

  // ── Drill-down CA par article ─────────────────────────────────────────────
  const drilldownCA = useMemo(() => {
    const TRIMESTRES = { T1: [1,2,3], T2: [4,5,6], T3: [7,8,9], T4: [10,11,12] }
    const map = {}
    factures
      .filter(f => {
        if (f.type !== 'vente' || f.statut === 'annulee') return false
        if (filtrePeriode === 'annee') return true
        const mois = new Date(f.date).getMonth() + 1
        if (filtrePeriode.startsWith('T')) return TRIMESTRES[filtrePeriode]?.includes(mois)
        if (filtrePeriode.startsWith('M')) return mois === parseInt(filtrePeriode.slice(1))
        return true
      })
      .forEach(f => {
        ;(f.lignes || []).forEach(l => {
          const key = l.description || 'Sans désignation'
          if (!map[key]) map[key] = { designation: key, quantite: 0, ca_ht: 0, ca_ttc: 0 }
          const qte = parseFloat(l.quantite) || 1
          const pu  = parseFloat(l.prix_unitaire) || parseFloat(l.montant_ht / qte) || 0
          const ht  = qte * pu
          const ttc = ht * (1 + (parseFloat(l.tva) || 0) / 100)
          map[key].quantite += qte
          map[key].ca_ht    += ht
          map[key].ca_ttc   += ttc
        })
      })
    const liste = Object.values(map).filter(x => x.ca_ht > 0).sort((a, b) => b.ca_ht - a.ca_ht)
    const totalHT = liste.reduce((s, x) => s + x.ca_ht, 0)
    return liste.map(x => ({ ...x, pct: totalHT > 0 ? (x.ca_ht / totalHT * 100) : 0 }))
  }, [factures, filtrePeriode])

  const BADGE_COULEURS = {
    AC: { bg: '#EAF3DE', color: '#3B6D11' },
    VT: { bg: '#E6F1FB', color: '#185FA5' },
    BQ: { bg: '#FAEEDA', color: '#854F0B' },
    CA: { bg: '#FBEAF0', color: '#993556' },
    OD: { bg: '#EEEDFE', color: '#534AB7' },
  }

  return (
    <div className={styles.page}>
      {/* Topbar */}
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Tableau de bord</h1>
        <div className={styles.topbarRight}>
          <div className={styles.periodeBadge}>
            <i className="ti ti-calendar" aria-hidden="true" /> Exercice {annee}
          </div>
          <button
            className={`${styles.btnPrimaire} ${!exerciceOuvert ? styles.btnPrimaireBloque : ''}`}
            onClick={ouvrirNouvelleEcriture}
            aria-disabled={!exerciceOuvert}
            title={exerciceOuvert ? 'Créer une nouvelle écriture' : `Exercice ${annee} clôturé : création désactivée`}
          >
            <i className="ti ti-plus" aria-hidden="true" /> Nouvelle écriture
          </button>
        </div>
      </div>

      <div className={styles.content}>
        <AFaire annee={annee} nbBrouillons={ecrituresAValider.length} factures={factures}
          periodiciteTVA={(societe?.periodicite_tva || 'mensuelle').toLowerCase()} />
        <DashboardCommercial exercice={annee} />

        {/* Alertes */}
        {(alertes.length > 0 || alertesStock?.rupture?.length > 0 || alertesStock?.faible?.length > 0) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {(() => {
            const nbLignes = alertes.length
              + (alertesStock?.rupture?.length > 0 ? 1 : 0)
              + (alertesStock?.faible?.length > 0 ? 1 : 0)
            return (
              <div className={styles.alertesHeader}>
                <span className={styles.alertesHeaderLabel}>
                  <i className="ti ti-bell" aria-hidden="true" />
                  {nbLignes} alerte{nbLignes > 1 ? 's' : ''} en cours
                </span>
                <button className={styles.alertesToggleBtn} onClick={toggleAlertesVisibles}>
                  <i className={`ti ${alertesVisibles ? 'ti-eye-off' : 'ti-eye'}`} aria-hidden="true" />
                  {alertesVisibles ? 'Masquer' : 'Afficher'}
                </button>
              </div>
            )
          })()}
          {alertesVisibles && (
          <div className={styles.alertesZone}>
            {alertes.map((a) => {
              const ouverte = alertesOuvertes.has(a.key)
              const aDetail = a.items && a.items.length > 0
              return (
                <div key={a.key} className={`${styles.alerteWrap} ${styles[`alerte_${a.type}`]}`}>
                  <div
                    className={styles.alerte}
                    onClick={() => aDetail ? toggleAlerte(a.key) : a.action()}
                    style={{ cursor: 'pointer' }}>
                    <i className={`ti ${a.icon}`} aria-hidden="true" />
                    <span>{a.message}</span>
                    {aDetail && (
                      <i className={`ti ${ouverte ? 'ti-chevron-up' : 'ti-chevron-down'}`}
                        style={{ fontSize: 13, marginLeft: 'auto', opacity: 0.7 }} aria-hidden="true" />
                    )}
                    <span
                      onClick={e => { e.stopPropagation(); a.action() }}
                      style={{ marginLeft: aDetail ? 10 : 'auto', fontSize: 11, opacity: 0.7, whiteSpace: 'nowrap' }}>
                      {a.cible || 'Voir le détail'} →
                    </span>
                  </div>
                  {aDetail && ouverte && (
                    <div className={styles.alerteDetail}>
                      {a.items.map((it, idx) => (
                        <div key={idx} className={styles.alerteDetailItem} onClick={a.action}>
                          <span className={styles.alerteDetailLabel}>
                            <strong>{it.label}</strong>{it.sousLabel ? ` — ${it.sousLabel}` : ''}
                          </span>
                          {it.droite && <span className={styles.alerteDetailDroite}>{it.droite}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
            {alertesStock?.rupture?.length > 0 && (
              <div className={`${styles.alerteWrap} ${styles.alerte_danger}`}>
                <div className={styles.alerte}
                  onClick={() => toggleAlerte('stock-rupture')} style={{ cursor: 'pointer' }}>
                  <i className="ti ti-box-off" aria-hidden="true" />
                  <span>
                    <strong>{alertesStock.rupture.length} article{alertesStock.rupture.length > 1 ? 's' : ''} en rupture de stock</strong>
                  </span>
                  <i className={`ti ${alertesOuvertes.has('stock-rupture') ? 'ti-chevron-up' : 'ti-chevron-down'}`}
                    style={{ fontSize: 13, marginLeft: 'auto', opacity: 0.7 }} aria-hidden="true" />
                  <span onClick={e => { e.stopPropagation(); navigate('/articles') }}
                    style={{ marginLeft: 10, fontSize: 11, opacity: 0.7, whiteSpace: 'nowrap' }}>Voir les articles →</span>
                </div>
                {alertesOuvertes.has('stock-rupture') && (
                  <div className={styles.alerteDetail}>
                    {alertesStock.rupture.map((a2, idx) => (
                      <div key={idx} className={styles.alerteDetailItem} onClick={() => navigate('/articles')}>
                        <span className={styles.alerteDetailLabel}><strong>{a2.designation}</strong></span>
                        <span className={styles.alerteDetailDroite}>0 {a2.unite || ''}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            {alertesStock?.faible?.length > 0 && (
              <div className={`${styles.alerteWrap} ${styles.alerte_warning}`}>
                <div className={styles.alerte}
                  onClick={() => toggleAlerte('stock-faible')} style={{ cursor: 'pointer' }}>
                  <i className="ti ti-alert-triangle" aria-hidden="true" />
                  <span>
                    <strong>{alertesStock.faible.length} article{alertesStock.faible.length > 1 ? 's ont' : ' a'} un stock faible</strong>
                  </span>
                  <i className={`ti ${alertesOuvertes.has('stock-faible') ? 'ti-chevron-up' : 'ti-chevron-down'}`}
                    style={{ fontSize: 13, marginLeft: 'auto', opacity: 0.7 }} aria-hidden="true" />
                  <span onClick={e => { e.stopPropagation(); navigate('/articles') }}
                    style={{ marginLeft: 10, fontSize: 11, opacity: 0.7, whiteSpace: 'nowrap' }}>Voir les articles →</span>
                </div>
                {alertesOuvertes.has('stock-faible') && (
                  <div className={styles.alerteDetail}>
                    {alertesStock.faible.map((a2, idx) => (
                      <div key={idx} className={styles.alerteDetailItem} onClick={() => navigate('/articles')}>
                        <span className={styles.alerteDetailLabel}><strong>{a2.designation}</strong></span>
                        <span className={styles.alerteDetailDroite}>{a2.stock_actuel} {a2.unite || ''}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
          )}
          </div>
        )}

        {/* KPIs */}
        <div className={styles.kpiGrid}>
          <div className={styles.kpiCard}
            onClick={() => setShowDrilldown(p => !p)}
            style={{ cursor: 'pointer', border: showDrilldown ? '1px solid var(--green)' : undefined, transition: 'border 0.15s' }}>
            <div className={styles.kpiLabel}>
              <i className="ti ti-arrow-up-right" style={{ color: 'var(--green)' }} aria-hidden="true" />
              Chiffre d'affaires
              <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--green)', opacity: 0.7 }}>
                {showDrilldown ? '▲ réduire' : '▼ détail'}
              </span>
            </div>
            <div className={styles.kpiValeur}>{formatMAD(kpis.ca)}<span className={styles.kpiDevise}> MAD</span></div>
            <div className={styles.kpiSous} style={{ color: 'var(--green)' }}>
              {kpis.ca > 0 ? `Exercice ${annee}` : `Aucune donnée pour ${annee}`}
            </div>
          </div>
          <CarteKPI
            icone="ti-arrow-down-right"
            label="Charges"
            valeur={kpis.charges}
            sous={kpis.charges > 0 ? `Exercice ${annee}` : `Aucune donnée pour ${annee}`}
            couleur="var(--red)"
          />
          <CarteKPI
            icone="ti-trending-up"
            label="Résultat net"
            valeur={kpis.resultat}
            sous={`CA - Charges`}
            couleur="var(--blue)"
          />
          <CarteKPI
            icone="ti-percentage"
            label="TVA à déclarer"
            valeur={kpis.tvaDue}
            sous={`Exercice ${annee}`}
            couleur="var(--amber)"
          />
        </div>

        {/* Drill-down CA par article */}
        {showDrilldown && (
          <div className={styles.card} style={{ padding: 0 }}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-chart-bar" style={{ color: 'var(--green)', marginRight: 6 }} />
                Détail CA/Article — Exercice {annee}
              </span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                {/* Filtres période */}
                {[
                  { val: 'annee', label: 'Année' },
                  { val: 'T1', label: 'T1' },
                  { val: 'T2', label: 'T2' },
                  { val: 'T3', label: 'T3' },
                  { val: 'T4', label: 'T4' },
                ].map(p => (
                  <button key={p.val} onClick={() => setFiltrePeriode(p.val)}
                    style={{
                      fontSize: 11, padding: '2px 9px', borderRadius: 100, cursor: 'pointer', border: '0.5px solid',
                      background: filtrePeriode === p.val ? 'var(--green)' : 'var(--bg-primary)',
                      color: filtrePeriode === p.val ? '#fff' : 'var(--text-secondary)',
                      borderColor: filtrePeriode === p.val ? 'var(--green)' : 'var(--border-medium)',
                    }}>
                    {p.label}
                  </button>
                ))}
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {drilldownCA.length} article{drilldownCA.length > 1 ? 's' : ''}
                </span>
              </div>
            </div>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Article</th>
                    <th style={{ textAlign: 'right' }}>Qté vendue</th>
                    <th style={{ textAlign: 'right' }}>CA HT</th>
                    <th style={{ textAlign: 'right' }}>CA TTC</th>
                    <th style={{ width: 120 }}>Part du CA</th>
                  </tr>
                </thead>
                <tbody>
                  {drilldownCA.map((x, i) => (
                    <tr key={i}>
                      <td><strong>{x.designation}</strong></td>
                      <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{x.quantite}</td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }}>{formatMAD(x.ca_ht)} MAD</td>
                      <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>{formatMAD(x.ca_ttc)} MAD</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ flex: 1, height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ width: `${x.pct}%`, height: '100%', background: 'var(--green)', borderRadius: 3, transition: 'width 0.3s' }} />
                          </div>
                          <span style={{ fontSize: 11, color: 'var(--text-secondary)', minWidth: 32, textAlign: 'right' }}>
                            {x.pct.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        

        {/* Écritures + Formulaire */}
        <div className={showForm ? styles.twoCols : ''}>
          {/* Table écritures */}
          <div className={styles.card} role="region" aria-label="Écritures à valider">
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                Écritures à valider
                {!erreurEcritures && !chargementEcritures && ecrituresAValider.length > 0 && (
                  <span style={{ marginLeft: 8, fontSize: 11, padding: '2px 8px', borderRadius: 20,
                    background: '#FDF3E3', color: '#8A5A0B', fontWeight: 500 }}>
                    {ecrituresAValider.length}
                  </span>
                )}
              </span>
              <button className={styles.lienVoir} onClick={() => navigate('/journal')}>
                Voir le journal →
              </button>
            </div>
            {erreurEcritures ? (
              <div role="alert" style={{ padding: 20 }}>
                <p>{erreurEcritures}</p>
                <button className={styles.lienVoir} onClick={rechargerEcritures}>Réessayer</button>
              </div>
            ) : chargementEcritures ? (
              <p role="status" style={{ padding: 20 }}>Chargement des écritures à valider…</p>
            ) : <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Journal</th>
                    <th>Libellé</th>
                    <th>Compte</th>
                    <th style={{ textAlign: 'right' }}>Débit</th>
                    <th style={{ textAlign: 'right' }}>Crédit</th>
                  </tr>
                </thead>
                <tbody>
                  {ecrituresAValider.slice(0, 4).flatMap(e =>
                    e.lignes.map((l, i) => (
                      <tr key={`${e.id}-${i}`}>
                        <td className={styles.tdDate}>
                          {i === 0 ? formatDate(e.date) : ''}
                        </td>
                        <td>{i === 0 ? <BadgeJournal code={e.journal} /> : ''}</td>
                        <td>{i === 0 ? e.libelle : l.libelle}</td>
                        <td>
                          <span className={styles.compteBadge}>{l.compte}</span>
                        </td>
                        <td className={styles.tdDebit} style={{ textAlign: 'right' }}>
                          {l.debit > 0 ? formatMAD(l.debit) : '—'}
                        </td>
                        <td className={styles.tdCredit} style={{ textAlign: 'right' }}>
                          {l.credit > 0 ? formatMAD(l.credit) : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>}
          </div>
        </div>

        {/* Modal formulaire écriture */}
        {showForm && (
          <FormulaireEcriture
            onFermer={() => setShowForm(false)}
            onSuccess={() => setShowForm(false)}
          />
        )}
      </div>
    </div>
  )
}
