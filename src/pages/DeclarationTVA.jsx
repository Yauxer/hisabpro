import { useEffect, useMemo, useState } from 'react'
import { formatMAD } from '../data/donnees.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import LogoDocument from '../components/LogoDocument.jsx'
import RasTvaAssistant from '../components/RasTvaAssistant.jsx'
import RasTvaRegistre from '../components/RasTvaRegistre.jsx'
import { tvaAPI, peutEcrire } from '../services/api.js'
import styles from './DeclarationTVA.module.css'

// Depuis 2026, la réforme TVA converge vers les taux normaux 10 % et 20 %.
// Les taux réellement présents sur les factures restent affichés dynamiquement
// afin de gérer l'historique et les cas particuliers sans lire les libellés.
const TAUX_STANDARD_2026 = [10, 20]
const TAUX_HISTORIQUES = [7, 10, 14, 20]

function normaliserBloc(bloc, tauxDisponibles) {
  const parTaux = {}
  tauxDisponibles.forEach(t => {
    const src = bloc?.par_taux?.[String(t)] || bloc?.par_taux?.[`${t}.0`] || {}
    parTaux[t] = { base: Number(src.base || 0), tva: Number(src.tva || 0) }
  })
  return { total: Number(bloc?.total || 0), parTaux }
}

function dateLimiteElectronique(anneeTVA, periode, mois, trimestre) {
  if (periode === 'annuelle') return null
  let anneeCible = anneeTVA
  let moisCible
  if (periode === 'mensuelle') {
    moisCible = mois + 1
  } else {
    moisCible = trimestre * 3 + 1
  }
  if (moisCible > 12) {
    moisCible -= 12
    anneeCible += 1
  }
  const dernierJour = new Date(anneeCible, moisCible, 0).getDate()
  return `${String(dernierJour).padStart(2, '0')}/${String(moisCible).padStart(2, '0')}/${anneeCible}`
}

const LIBELLES_ECARTS = {
  collectee: 'TVA collectée', recuperable: 'TVA récupérable', credit_anterieur: 'Crédit antérieur',
  tva_due: 'TVA due', credit_tva: 'Crédit à reporter',
}

// Dépôt figé (959) : les montants déposés ne changent plus ; un recalcul différent est signalé.
function DepotDeclaration({ donnees, anneeTVA, mois, trimestre, onDepose }) {
  const deposee = donnees?.declaration_deposee
  const ecarts = donnees?.ecarts_depot
  const [ouvert, setOuvert] = useState(false)
  const [dateDepot, setDateDepot] = useState('')
  const [reference, setReference] = useState('')
  const [motif, setMotif] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const rectificative = Boolean(deposee)

  async function enregistrer() {
    setEnvoi(true); setErreur('')
    try {
      await tvaAPI.deposer({
        exercice: anneeTVA, ...(mois ? { mois } : { trimestre }),
        date_depot: dateDepot, reference_depot: reference,
        ...(rectificative ? { remplace_id: deposee.id, motif_rectification: motif } : {}),
      })
      setOuvert(false); setDateDepot(''); setReference(''); setMotif('')
      onDepose()
    } catch (e) {
      setErreur(e.message || 'Enregistrement du dépôt impossible')
    } finally {
      setEnvoi(false)
    }
  }

  const champ = { padding: '7px 9px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', width: '100%' }
  return (
    <div data-depot-tva style={{ padding: '10px 12px', marginBottom: 12, borderRadius: 8, fontSize: 13,
      border: `1px solid ${ecarts ? 'var(--amber)' : deposee ? 'var(--green)' : 'var(--border-medium)'}` }}>
      {deposee ? (
        <div>
          <strong>Déclaration déposée le {deposee.date_depot.split('-').reverse().join('/')}</strong>
          {' '}— réf. {deposee.reference_depot}. Montants figés : TVA due {formatMAD(deposee.tva_due)} MAD,
          crédit reporté {formatMAD(deposee.credit_tva)} MAD.
          {ecarts && (
            <div role="alert" style={{ marginTop: 6 }}>
              <strong>Écart avec le recalcul actuel :</strong>{' '}
              {Object.entries(ecarts).map(([k, v]) => `${LIBELLES_ECARTS[k] || k} ${v > 0 ? '+' : ''}${formatMAD(v)} MAD`).join(' — ')}.
              {' '}Aucun montant déposé n’est modifié : régularisation ou rectificative à qualifier.
            </div>
          )}
        </div>
      ) : (
        <span>Période non déposée : les montants restent recalculés à chaque consultation.</span>
      )}
      {peutEcrire() && !ouvert && (
        <button className={styles.btnSec} style={{ marginLeft: 8 }} onClick={() => setOuvert(true)}>
          <i className="ti ti-lock" aria-hidden="true" /> {rectificative ? 'Déposer une rectificative' : 'Enregistrer le dépôt'}
        </button>
      )}
      {ouvert && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 8, marginTop: 8, alignItems: 'end' }}>
          <label style={{ fontSize: 11 }}>Date de dépôt
            <input type="date" aria-label="Date de dépôt" style={champ} value={dateDepot} onChange={e => setDateDepot(e.target.value)} />
          </label>
          <label style={{ fontSize: 11 }}>Référence du dépôt
            <input aria-label="Référence du dépôt" maxLength={100} style={champ} value={reference} onChange={e => setReference(e.target.value)} />
          </label>
          {rectificative && (
            <label style={{ fontSize: 11 }}>Motif de la rectificative
              <input aria-label="Motif de la rectificative" style={champ} value={motif} onChange={e => setMotif(e.target.value)} />
            </label>
          )}
          <div style={{ display: 'flex', gap: 6 }}>
            <button className={styles.btnPrim} onClick={enregistrer}
              disabled={envoi || !dateDepot || !reference.trim() || (rectificative && !motif.trim())}>
              {envoi ? 'Enregistrement…' : 'Figer la déclaration'}
            </button>
            <button className={styles.btnSec} onClick={() => { setOuvert(false); setErreur('') }}>Annuler</button>
          </div>
          {erreur && <div role="alert" style={{ color: 'var(--red)', gridColumn: '1 / -1' }}>{erreur}</div>}
        </div>
      )}
    </div>
  )
}

export default function DeclarationTVA() {
  const { annee, exercice } = useExercice()
  const { societe } = useModules()
  const anneesTVADisponibles = useMemo(() => {
    const debut = Number((exercice?.date_debut || '').slice(0, 4))
    const fin = Number((exercice?.date_fin || '').slice(0, 4))
    if (Number.isInteger(debut) && debut >= 1 && Number.isInteger(fin) && fin <= 9999 && fin >= debut) {
      return Array.from({ length: fin - debut + 1 }, (_, i) => debut + i)
    }
    return Number.isInteger(annee) && annee >= 1 && annee <= 9999 ? [annee] : []
  }, [annee, exercice?.date_debut, exercice?.date_fin])
  const [anneeTVA, setAnneeTVA] = useState(annee)

  useEffect(() => {
    if (anneesTVADisponibles.length) setAnneeTVA(prev => anneesTVADisponibles.includes(prev) ? prev : anneesTVADisponibles[0])
  }, [anneesTVADisponibles])

  const [periode,    setPeriode]    = useState('mensuelle')
  const [mois,       setMois]       = useState(new Date().getMonth() + 1)
  const [trimestre,  setTrimestre]  = useState(Math.ceil((new Date().getMonth() + 1) / 3))
  const [onglet,     setOnglet]     = useState('synthese')
  const [donneesTVA, setDonneesTVA] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur,     setErreur]     = useState('')
  const [paramTVA,   setParamTVA]   = useState({ credit_ouverture: 0, prorata_deduction_pct: 100 })
  const [sauveParam, setSauveParam] = useState(false)
  const [refreshTVA, setRefreshTVA] = useState(0)
  const calendrierPret = Boolean(societe?.id && exercice?.id && anneesTVADisponibles.includes(anneeTVA))

  useEffect(() => {
    let actif = true
    setChargement(true)
    setErreur('')
    setDonneesTVA(null)
    if (!calendrierPret) return
    const filtres = periode === 'mensuelle'
      ? { mois }
      : periode === 'trimestrielle'
        ? { trimestre }
        : {}

    tvaAPI.declaration(anneeTVA, filtres)
      .then(data => { if (actif) setDonneesTVA(data) })
      .catch(err => { if (actif) setErreur(err.message || 'Impossible de calculer la TVA') })
      .finally(() => { if (actif) setChargement(false) })
    return () => { actif = false }
  }, [anneeTVA, periode, mois, trimestre, refreshTVA, calendrierPret, societe?.id, exercice?.id])

  useEffect(() => {
    let actif = true
    if (!calendrierPret) return
    tvaAPI.parametres(anneeTVA)
      .then(data => {
        if (actif) setParamTVA({
          credit_ouverture: Number(data?.credit_ouverture || 0),
          prorata_deduction_pct: Number(data?.prorata_deduction_pct ?? 100),
        })
      })
      .catch(() => {})
    return () => { actif = false }
  }, [anneeTVA, calendrierPret, societe?.id, exercice?.id])

  async function enregistrerParametresTVA() {
    if (!peutEcrire()) return
    setSauveParam(true)
    setErreur('')
    try {
      const payload = {
        credit_ouverture: Math.max(0, Number(paramTVA.credit_ouverture) || 0),
        prorata_deduction_pct: Math.max(0, Math.min(100, Number(paramTVA.prorata_deduction_pct) || 0)),
      }
      await tvaAPI.enregistrerParametres(anneeTVA, payload)
      setParamTVA(payload)
      setRefreshTVA(v => v + 1)
    } catch (e) {
      setErreur(e.message || 'Impossible d’enregistrer les paramètres TVA')
    } finally {
      setSauveParam(false)
    }
  }

  const tauxDisponibles = useMemo(() => {
    const taux = new Set(anneeTVA >= 2026 ? TAUX_STANDARD_2026 : TAUX_HISTORIQUES)
    Object.keys(donneesTVA?.collectee?.par_taux || {}).forEach(t => taux.add(Number(t)))
    Object.keys(donneesTVA?.recuperable?.par_taux || {}).forEach(t => taux.add(Number(t)))
    return [...taux].filter(Number.isFinite).sort((a, b) => a - b)
  }, [anneeTVA, donneesTVA])

  const tvaData = useMemo(() => ({
    collectee: normaliserBloc(donneesTVA?.collectee, tauxDisponibles),
    recuperable: normaliserBloc(donneesTVA?.recuperable, tauxDisponibles),
    recuperableCharges: normaliserBloc(donneesTVA?.recuperable_charges, tauxDisponibles),
    recuperableImmo: normaliserBloc(donneesTVA?.recuperable_immobilisations, tauxDisponibles),
    creditAnterieur: Number(donneesTVA?.credit_tva_anterieur || 0),
    tvaDueAvantCredit: Number(donneesTVA?.tva_due_avant_credit || 0),
    tvaDue: Number(donneesTVA?.tva_due || 0),
    creditTVA: Number(donneesTVA?.credit_tva || 0),
  }), [donneesTVA, tauxDisponibles])

  const labelPeriode = () => {
    const moisLabels = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
    if (periode === 'mensuelle') return `${moisLabels[mois - 1]} ${anneeTVA}`
    if (periode === 'trimestrielle') return `T${trimestre} ${anneeTVA}`
    return `Annuel ${anneeTVA}`
  }

  return (
    <div className={styles.page} data-tva-print data-form-page>
      {/* Topbar */}
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Déclaration TVA</h1>
          <span className={styles.pageSubtitle}>Calcul TVA depuis les factures et paiements effectifs</span>
        </div>
        <div className={styles.topbarRight}>
          <button className={styles.btnSec} onClick={() => window.print()} disabled={chargement || !donneesTVA || Boolean(erreur) || !societe?.id}>
            <i className="ti ti-printer" aria-hidden="true" /> Imprimer
          </button>
          <span className={styles.pageSubtitle} title="HisabPro prépare la déclaration ; le dépôt se fait sur le portail de la DGI">
            Dépôt sur le portail DGI (hors HisabPro)
          </span>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.printIdentite}>
          <LogoDocument societe={societe} />
          <strong>{societe?.raison_sociale || 'Société à compléter'}</strong>
          <span>IF : {societe?.identifiant_fiscal || 'à compléter'} — ICE : {societe?.ice || 'à compléter'}</span>
          <span>{labelPeriode()} — Brouillon de contrôle, sans dépôt DGI</span>
        </div>
        {/* Paramètres de période */}
        <div className={styles.parametres}>
          <div className={styles.paramCard}>
            <div className={styles.paramLabel}>Vue de calcul</div>
            <div className={styles.toggleGroupe}>
              {['mensuelle', 'trimestrielle', 'annuelle'].map(p => (
                <button
                  key={p}
                  className={`${styles.toggleBtn} ${periode === p ? styles.toggleBtnActif : ''}`}
                  onClick={() => setPeriode(p)}
                >
                  {p === 'annuelle' ? 'Vue annuelle' : p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {periode === 'mensuelle' && (
            <div className={styles.paramCard}>
              <div className={styles.paramLabel}>Mois</div>
              <select
                className={styles.select}
                value={mois}
                onChange={e => setMois(parseInt(e.target.value))}
              >
                {['Janvier','Février','Mars','Avril','Mai','Juin',
                  'Juillet','Août','Septembre','Octobre','Novembre','Décembre'].map((m, i) => (
                  <option key={i + 1} value={i + 1}>{m}</option>
                ))}
              </select>
            </div>
          )}

          {periode === 'trimestrielle' && (
            <div className={styles.paramCard}>
              <div className={styles.paramLabel}>Trimestre</div>
              <div className={styles.toggleGroupe}>
                {[1, 2, 3, 4].map(t => (
                  <button
                    key={t}
                    className={`${styles.toggleBtn} ${trimestre === t ? styles.toggleBtnActif : ''}`}
                    onClick={() => setTrimestre(t)}
                  >
                    T{t}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className={styles.paramCard}>
            <div className={styles.paramLabel}>Année civile TVA</div>
            {anneesTVADisponibles.length > 1 ? (
              <select aria-label="Année civile TVA" className={styles.select} value={anneeTVA} onChange={e => setAnneeTVA(Number(e.target.value))}>
                {anneesTVADisponibles.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            ) : (
              <div className={styles.exerciceDisplay}>{anneeTVA}</div>
            )}
          </div>

          <div className={styles.periodeBadge}>
            <i className="ti ti-calendar-event" aria-hidden="true" />
            {labelPeriode()}
            <span className={styles.periodeCount}>
              {donneesTVA ? `${(donneesTVA.details_ventes?.length || 0) + (donneesTVA.details_achats?.length || 0)} fait(s) générateur(s)` : 'Calcul indisponible'}
            </span>
          </div>
        </div>

        {chargement && <p role="status">Calcul de la déclaration…</p>}
        {erreur && (
          <div role="alert" style={{ padding: '10px 12px', marginBottom: 12, border: '1px solid var(--red)', borderRadius: 8, color: 'var(--red)', fontSize: 13 }}>
            {erreur}
          </div>
        )}
        {(donneesTVA?.alertes || []).length > 0 && (
          <div style={{ padding: '10px 12px', marginBottom: 12, border: '1px solid var(--amber)', borderRadius: 8, fontSize: 12 }}>
            <strong>Points à vérifier avant déclaration :</strong> {donneesTVA.alertes.join(' — ')}
          </div>
        )}

        <nav className="tva-sous-navigation" aria-label="Sections de la déclaration TVA">
          {[['tva-declaration', 'Déclaration'], ['tva-depot', 'Dépôt'], ['tva-ras', 'RAS TVA'], ['tva-parametres', 'Paramètres']].map(([id, libelle]) => (
            <a key={id} href={`#${id}`} onClick={e => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}>{libelle}</a>
          ))}
        </nav>

        {!chargement && donneesTVA && !erreur && periode !== 'annuelle' && (
          <div id="tva-depot">
            <DepotDeclaration
              donnees={donneesTVA} anneeTVA={anneeTVA}
              mois={periode === 'mensuelle' ? mois : null}
              trimestre={periode === 'trimestrielle' ? trimestre : null}
              onDepose={() => setRefreshTVA(v => v + 1)}
            />
          </div>
        )}

        <div id="tva-parametres" style={{
          display: 'grid', gridTemplateColumns: 'minmax(180px, 1fr) minmax(180px, 1fr) auto',
          gap: 10, alignItems: 'end', padding: 12, marginBottom: 12,
          border: '0.5px solid var(--border-medium)', borderRadius: 8, background: 'var(--bg-primary)'
        }}>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
              Crédit TVA d’ouverture — {anneeTVA}
            </label>
            <input
              type="number" min="0" step="0.01"
              disabled={!peutEcrire() || chargement}
              value={paramTVA.credit_ouverture}
              onChange={e => setParamTVA(p => ({ ...p, credit_ouverture: e.target.value }))}
              style={{ width: '100%', padding: '7px 9px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
              Prorata annuel de déduction (%)
            </label>
            <input
              type="number" min="0" max="100" step="0.01"
              disabled={!peutEcrire() || chargement}
              value={paramTVA.prorata_deduction_pct}
              onChange={e => setParamTVA(p => ({ ...p, prorata_deduction_pct: e.target.value }))}
              style={{ width: '100%', padding: '7px 9px', borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)' }}
            />
          </div>
          {peutEcrire() && <button className={styles.btnSec} onClick={enregistrerParametresTVA} disabled={sauveParam || chargement}>
            <i className="ti ti-device-floppy" aria-hidden="true" /> {sauveParam ? 'Enregistrement…' : 'Enregistrer'}
          </button>}
        </div>

        {calendrierPret && <div id="tva-ras">
          <RasTvaRegistre key={`registre:${societe.id}:${anneeTVA}`} annee={anneeTVA} />
          <RasTvaAssistant key={`${societe.id}:${anneeTVA}`} annee={anneeTVA} />
        </div>}
        {!chargement && donneesTVA && !erreur && <>
        {/* KPIs TVA */}
        <div id="tva-declaration" className={styles.kpiGrid}>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>
              <i className="ti ti-arrow-up-right" style={{ color: 'var(--red)' }} aria-hidden="true" />
              TVA collectée
            </div>
            <div className={styles.kpiValeur}>{formatMAD(tvaData.collectee.total)}</div>
            <div className={styles.kpiSous} style={{ color: 'var(--text-tertiary)' }}>MAD</div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>
              <i className="ti ti-arrow-down-right" style={{ color: 'var(--green)' }} aria-hidden="true" />
              TVA récupérable
            </div>
            <div className={styles.kpiValeur}>{formatMAD(tvaData.recuperable.total)}</div>
            <div className={styles.kpiSous} style={{ color: 'var(--text-tertiary)' }}>MAD</div>
          </div>
          <div className={`${styles.kpiCard} ${tvaData.tvaDue > 0 ? styles.kpiCardAlerte : styles.kpiCardOk}`}>
            <div className={styles.kpiLabel}>
              <i className={`ti ${tvaData.tvaDue > 0 ? 'ti-alert-circle' : 'ti-circle-check'}`}
                style={{ color: tvaData.tvaDue > 0 ? 'var(--amber)' : 'var(--green)' }}
                aria-hidden="true"
              />
              {tvaData.tvaDue > 0 ? 'TVA nette à payer' : 'Crédit à reporter'}
            </div>
            <div className={`${styles.kpiValeur} ${tvaData.tvaDue > 0 ? styles.valeurAlerte : styles.valeurOk}`}>
              {formatMAD(tvaData.tvaDue > 0 ? tvaData.tvaDue : tvaData.creditTVA)}
            </div>
            <div className={styles.kpiSous} style={{ color: 'var(--text-tertiary)' }}>MAD</div>
          </div>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>
              <i className="ti ti-calendar-due" style={{ color: 'var(--blue)' }} aria-hidden="true" />
              Échéance déclaration
            </div>
            <div className={styles.kpiValeur} style={{ fontSize: 15 }}>
              {dateLimiteElectronique(anneeTVA, periode, mois, trimestre) || '—'}
            </div>
            <div className={styles.kpiSous} style={{ color: 'var(--blue)' }}>
              {periode === 'annuelle' ? 'Vue de contrôle, pas une périodicité déclarative' : 'Échéance télédéclaration'}
            </div>
          </div>
        </div>

        {/* Onglets */}
        <div className={styles.onglets}>
          {[
            { id: 'synthese',    label: 'Synthèse',          icon: 'ti-chart-bar'   },
            { id: 'detail',      label: 'Détail par taux',   icon: 'ti-table'       },
            { id: 'declaration', label: 'Préparation DGI',   icon: 'ti-file-text'   },
          ].map(o => (
            <button
              key={o.id}
              className={`${styles.ongletBtn} ${onglet === o.id ? styles.ongletBtnActif : ''}`}
              onClick={() => setOnglet(o.id)}
            >
              <i className={`ti ${o.icon}`} aria-hidden="true" />
              {o.label}
            </button>
          ))}
        </div>

        {/* Onglet Synthèse */}
        {onglet === 'synthese' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>Synthèse TVA — {labelPeriode()}</span>
            </div>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Opération</th>
                  <th>Compte CGNC</th>
                  <th style={{ textAlign: 'right' }}>Base HT (MAD)</th>
                  <th style={{ textAlign: 'right' }}>TVA (MAD)</th>
                  <th style={{ textAlign: 'right' }}>TTC (MAD)</th>
                </tr>
              </thead>
              <tbody>
                <tr className={styles.rowSection}>
                  <td colSpan={5}><strong>TVA collectée (sur ventes)</strong></td>
                </tr>
                {tauxDisponibles.map(taux => {
                  const d = tvaData.collectee.parTaux[taux]
                  if (d.tva === 0) return null
                  return (
                    <tr key={`col-${taux}`}>
                      <td style={{ paddingLeft: 24 }}>Ventes soumises à {taux}%</td>
                      <td><span className={styles.cptBadge}>4455</span></td>
                      <td style={{ textAlign: 'right' }}>{formatMAD(d.base)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--red)', fontWeight: 500 }}>{formatMAD(d.tva)}</td>
                      <td style={{ textAlign: 'right' }}>{formatMAD(d.base + d.tva)}</td>
                    </tr>
                  )
                })}
                <tr className={styles.rowTotal}>
                  <td><strong>Total TVA collectée</strong></td>
                  <td />
                  <td style={{ textAlign: 'right' }}>
                    <strong>{formatMAD(tauxDisponibles.reduce((s, t) => s + tvaData.collectee.parTaux[t].base, 0))}</strong>
                  </td>
                  <td style={{ textAlign: 'right', color: 'var(--red)' }}>
                    <strong>{formatMAD(tvaData.collectee.total)}</strong>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <strong>{formatMAD(
                      tauxDisponibles.reduce((s, t) => s + tvaData.collectee.parTaux[t].base + tvaData.collectee.parTaux[t].tva, 0)
                    )}</strong>
                  </td>
                </tr>

                <tr className={styles.rowSpacer}><td colSpan={5} /></tr>

                <tr className={styles.rowSection}>
                  <td colSpan={5}><strong>TVA récupérable (sur achats)</strong></td>
                </tr>
                {tauxDisponibles.map(taux => {
                  const d = tvaData.recuperable.parTaux[taux]
                  if (d.tva === 0) return null
                  return (
                    <tr key={`rec-${taux}`}>
                      <td style={{ paddingLeft: 24 }}>Achats soumis à {taux}%</td>
                      <td><span className={styles.cptBadge}>3455</span></td>
                      <td style={{ textAlign: 'right' }}>{formatMAD(d.base)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--green)', fontWeight: 500 }}>{formatMAD(d.tva)}</td>
                      <td style={{ textAlign: 'right' }}>{formatMAD(d.base + d.tva)}</td>
                    </tr>
                  )
                })}
                <tr className={styles.rowTotal}>
                  <td><strong>Total TVA récupérable</strong></td>
                  <td />
                  <td style={{ textAlign: 'right' }}>
                    <strong>{formatMAD(tauxDisponibles.reduce((s, t) => s + tvaData.recuperable.parTaux[t].base, 0))}</strong>
                  </td>
                  <td style={{ textAlign: 'right', color: 'var(--green)' }}>
                    <strong>{formatMAD(tvaData.recuperable.total)}</strong>
                  </td>
                  <td />
                </tr>

                <tr className={styles.rowSpacer}><td colSpan={5} /></tr>
                <tr>
                  <td colSpan={2}><strong>Crédit TVA antérieur reporté</strong></td>
                  <td />
                  <td style={{ textAlign: 'right', color: 'var(--green)' }}><strong>{formatMAD(tvaData.creditAnterieur)}</strong></td>
                  <td />
                </tr>

                <tr className={tvaData.tvaDue > 0 ? styles.rowResultatDue : styles.rowResultatCredit}>
                  <td colSpan={2}>
                    <strong>{tvaData.tvaDue > 0 ? '▶ TVA nette à payer' : '▶ Crédit TVA à reporter'}</strong>
                  </td>
                  <td />
                  <td style={{ textAlign: 'right' }}>
                    <strong>{formatMAD(tvaData.tvaDue > 0 ? tvaData.tvaDue : tvaData.creditTVA)}</strong>
                  </td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Onglet Détail par taux */}
        {onglet === 'detail' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>Détail par taux de TVA</span>
            </div>
            <div className={styles.tauxGrid}>
              {tauxDisponibles.map(taux => {
                const col = tvaData.collectee.parTaux[taux]
                const rec = tvaData.recuperable.parTaux[taux]
                const net = col.tva - rec.tva
                return (
                  <div key={taux} className={styles.tauxCard}>
                    <div className={styles.tauxHeader}>
                      <span className={styles.tauxBadge}>{taux}%</span>
                      <span className={styles.tauxLabel}>Taux {taux}%</span>
                    </div>
                    <div className={styles.tauxLigne}>
                      <span>Base ventes HT</span>
                      <span>{formatMAD(col.base)} MAD</span>
                    </div>
                    <div className={styles.tauxLigne}>
                      <span>TVA collectée</span>
                      <span style={{ color: 'var(--red)', fontWeight: 500 }}>{formatMAD(col.tva)} MAD</span>
                    </div>
                    <div className={styles.tauxSep} />
                    <div className={styles.tauxLigne}>
                      <span>Base achats HT</span>
                      <span>{formatMAD(rec.base)} MAD</span>
                    </div>
                    <div className={styles.tauxLigne}>
                      <span>TVA récupérable</span>
                      <span style={{ color: 'var(--green)', fontWeight: 500 }}>{formatMAD(rec.tva)} MAD</span>
                    </div>
                    <div className={styles.tauxSep} />
                    <div className={`${styles.tauxNet} ${net > 0 ? styles.tauxNetDue : net < 0 ? styles.tauxNetCredit : ''}`}>
                      <span>{net > 0 ? 'Net à payer' : net < 0 ? 'Crédit' : 'Équilibré'}</span>
                      <span>{formatMAD(Math.abs(net))} MAD</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Onglet Formulaire DGI */}
        {onglet === 'declaration' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-file-text" aria-hidden="true" />
                Préparation de déclaration TVA
              </span>
              <span className={styles.dgiLabel}>Brouillon de contrôle</span>
            </div>
            <div className={styles.dgiForm}>
              <div className={styles.dgiSection}>
                <div className={styles.dgiSectionTitle}>IDENTIFICATION</div>
                <div className={styles.dgiRow}>
                  <label>Raison sociale</label>
                  <input className={styles.dgiInput} type="text" value={societe?.raison_sociale || ''} placeholder="À compléter dans les paramètres société" readOnly aria-label="Raison sociale" />
                </div>
                <div className={styles.dgiRow}>
                  <label>N° IF</label>
                  <input className={styles.dgiInput} type="text" value={societe?.identifiant_fiscal || ''} placeholder="À compléter dans les paramètres société" readOnly aria-label="N° IF" />
                </div>
                <div className={styles.dgiRow}>
                  <label>N° ICE</label>
                  <input className={styles.dgiInput} type="text" value={societe?.ice || ''} placeholder="À compléter dans les paramètres société" readOnly aria-label="N° ICE" />
                </div>
                <div className={styles.dgiRow}>
                  <label>Période</label>
                  <input className={styles.dgiInput} type="text" value={labelPeriode()} readOnly />
                </div>
              </div>

              <div className={styles.dgiSection}>
                <div className={styles.dgiSectionTitle}>OPÉRATIONS TAXABLES — VENTES</div>
                {tauxDisponibles.map(taux => (
                  <div key={taux} className={styles.dgiRow}>
                    <label>Taux {taux}% — Base imposable</label>
                    <input
                      className={styles.dgiInput}
                      type="text"
                      value={formatMAD(tvaData.collectee.parTaux[taux].base)}
                      readOnly
                    />
                    <input
                      className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                      type="text"
                      value={formatMAD(tvaData.collectee.parTaux[taux].tva)}
                      readOnly
                    />
                  </div>
                ))}
                <div className={`${styles.dgiRow} ${styles.dgiRowTotal}`}>
                  <label><strong>Total TVA exigible</strong></label>
                  <input className={styles.dgiInput} type="text" readOnly />
                  <input
                    className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                    type="text"
                    value={formatMAD(tvaData.collectee.total)}
                    readOnly
                    style={{ fontWeight: 600, color: 'var(--red)' }}
                  />
                </div>
              </div>

              <div className={styles.dgiSection}>
                <div className={styles.dgiSectionTitle}>TVA RÉCUPÉRABLE — ACHATS</div>
                {tauxDisponibles.map(taux => (
                  <div key={taux} className={styles.dgiRow}>
                    <label>Taux {taux}% — Base imposable</label>
                    <input
                      className={styles.dgiInput}
                      type="text"
                      value={formatMAD(tvaData.recuperable.parTaux[taux].base)}
                      readOnly
                    />
                    <input
                      className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                      type="text"
                      value={formatMAD(tvaData.recuperable.parTaux[taux].tva)}
                      readOnly
                    />
                  </div>
                ))}
                <div className={`${styles.dgiRow} ${styles.dgiRowTotal}`}>
                  <label><strong>Total TVA récupérable</strong></label>
                  <input className={styles.dgiInput} type="text" readOnly />
                  <input
                    className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                    type="text"
                    value={formatMAD(tvaData.recuperable.total)}
                    readOnly
                    style={{ fontWeight: 600, color: 'var(--green)' }}
                  />
                </div>
              </div>

              <div className={styles.dgiSection}>
                <div className={styles.dgiSectionTitle}>RÉSULTAT DE LA DÉCLARATION</div>
                <div className={styles.dgiRow}>
                  <label>Crédit TVA antérieur</label>
                  <input className={styles.dgiInput} type="text" readOnly />
                  <input className={`${styles.dgiInput} ${styles.dgiInputTVA}`} type="text" value={formatMAD(tvaData.creditAnterieur)} readOnly />
                </div>
                {tvaData.tvaDue > 0 ? (
                  <div className={`${styles.dgiRow} ${styles.dgiRowResultatDue}`}>
                    <label><strong>TVA nette à payer après report</strong></label>
                    <input className={styles.dgiInput} type="text" readOnly />
                    <input
                      className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                      type="text"
                      value={formatMAD(tvaData.tvaDue)}
                      readOnly
                      style={{ fontWeight: 700, color: 'var(--red)' }}
                    />
                  </div>
                ) : (
                  <div className={`${styles.dgiRow} ${styles.dgiRowResultatCredit}`}>
                    <label><strong>Crédit TVA à reporter</strong></label>
                    <input className={styles.dgiInput} type="text" readOnly />
                    <input
                      className={`${styles.dgiInput} ${styles.dgiInputTVA}`}
                      type="text"
                      value={formatMAD(tvaData.creditTVA)}
                      readOnly
                      style={{ fontWeight: 700, color: 'var(--green)' }}
                    />
                  </div>
                )}
              </div>

              <div className={styles.dgiNote}>
                <i className="ti ti-info-circle" aria-hidden="true" />
                Les montants intègrent désormais les encaissements/paiements, avoirs, acomptes clients, crédit antérieur,
                déductibilité explicite des achats et prorata annuel. Les retenues TVA, certaines exclusions légales automatiques,
                les immobilisations saisies hors facture et le gel d’une déclaration déjà déposée restent à traiter : contrôlez l’état avant dépôt.
              </div>
            </div>
          </div>
        )}
        </>}
      </div>
    </div>
  )
}
