import { useState, useEffect, useMemo } from 'react'
import { formatMAD } from '../data/donnees.js'
import { API_BASE, formatErreurAPI } from '../services/api.js'
import { exporterCSV } from '../services/exportCSV.js'
import { preparerLignesComptage, nombreInventaire, sourceInventaireConnue, ecartInventaire } from '../utils/inventaireComptage.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import styles from './Inventaire.module.css'
import { notifier } from '../services/notifications.js'

const montantInventaire = valeur => nombreInventaire(valeur) === null ? 'À vérifier' : formatMAD(valeur)
const quantiteInventaire = valeur => nombreInventaire(valeur) === null ? 'À vérifier' : valeur
const diagnosticInventaire = ligne => Object.values(ligne.nombres_diagnostics || {}).join(' · ')

function DiagnosticsInventaire({ etat }) {
  if (!etat?.diagnostics?.length) return null
  return <div role="alert" style={{ marginBottom: 12, color: '#8A5A0B', fontSize: 12, lineHeight: 1.5 }}>
    <strong>À vérifier — valorisation incomplète</strong>
    {etat.diagnostics.map((d, i) => <div key={`${d.article_id}-${d.champ}-${i}`}>{d.code ? `${d.code} : ` : ''}{d.message}</div>)}
  </div>
}

const TOKEN = () => localStorage.getItem('hisabpro_token')

async function apiFetch(url, opts = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN()}`, ...(opts.headers || {}) },
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: 'Erreur' }))
    throw new Error(formatErreurAPI(e.detail))
  }
  return res.status === 204 ? null : res.json()
}

export default function Inventaire() {
  const [onglet, setOnglet] = useState('comptage')   // comptage | valorisation | mouvements | comptable
  const { annee, exercice } = useExercice()

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Inventaire &amp; valorisation</h1>
          <p className={styles.pageSub}>
            Comptage physique, régularisation des écarts et valeur du stock au coût moyen
          </p>
        </div>
      </div>

      <div className={styles.onglets} style={{ flexWrap: 'wrap' }}>
        {[
          { id: 'comptage',     label: 'Comptage physique', icone: 'ti-clipboard-list' },
          { id: 'valorisation', label: 'Valeur du stock',   icone: 'ti-coins' },
          { id: 'mouvements',   label: 'Mouvements & CMUP',  icone: 'ti-list-details' },
          { id: 'comptable',    label: 'Rapprochement comptable', icone: 'ti-scale' },
        ].map(o => (
          <button key={o.id}
            className={`${styles.ongletBtn} ${onglet === o.id ? styles.ongletBtnActif : ''}`}
            onClick={() => setOnglet(o.id)}>
            <i className={`ti ${o.icone}`} /> {o.label}
          </button>
        ))}
      </div>

      <div className={styles.content}>
        {onglet === 'comptage'     && <OngletComptage annee={annee} exercice={exercice} />}
        {onglet === 'valorisation' && <OngletValorisation />}
        {onglet === 'mouvements'   && <OngletMouvements />}
        {onglet === 'comptable'    && <OngletComptable annee={annee} exercice={exercice} />}
      </div>
    </div>
  )
}

// ─── Onglet 1 : comptage physique ─────────────────────────────────────────────
function OngletComptage({ annee, exercice }) {
  const [feuille, setFeuille]   = useState([])
  const [comptes, setComptes]   = useState({})   // article_id → quantité saisie
  const [chargement, setCharge] = useState(true)
  const [erreur, setErreur]     = useState('')
  const [apercu, setApercu]     = useState(null)
  const [enCours, setEnCours]   = useState(false)
  const [recherche, setRech]    = useState('')
  const [note, setNote]         = useState('')
  const [dateInventaire, setDateInventaire] = useState(exercice?.date_fin || `${annee}-12-31`)
  const [reference, setReference] = useState(`INV-STOCK-${annee}`)

  async function charger() {
    setCharge(true); setErreur('')
    try {
      const d = await apiFetch('/api/inventaire/feuille')
      setFeuille(d)
      // Pré-remplir avec le stock théorique : le comptage ne corrige que les écarts
      const init = {}
      d.forEach(a => { init[a.article_id] = nombreInventaire(a.stock_theorique) === null ? '' : String(a.stock_theorique) })
      setComptes(init)
    } catch (e) { setErreur(e.message) }
    finally { setCharge(false) }
  }
  useEffect(() => { charger() }, [])
  useEffect(() => {
    setDateInventaire(exercice?.date_fin || `${annee}-12-31`)
    setReference(`INV-STOCK-${annee}`)
  }, [annee, exercice?.date_fin])

  const visibles = useMemo(() => {
    if (!recherche) return feuille
    const q = recherche.toLowerCase()
    return feuille.filter(a =>
      a.designation.toLowerCase().includes(q) || (a.code || '').toLowerCase().includes(q))
  }, [feuille, recherche])

  // Écarts calculés en direct pendant la saisie
  const ecarts = useMemo(() => {
    const liste = []
    feuille.forEach(a => {
      const saisi = comptes[a.article_id]
      if (saisi === '' || saisi === undefined) return
      const calcul = ecartInventaire(a, saisi)
      if (calcul.ecart !== null && Math.abs(calcul.ecart) < 0.0001 && calcul.valeur !== null) return
      liste.push({ ...a, ...calcul })
    })
    return liste
  }, [feuille, comptes])

  const sourcesInconnues = feuille.filter(a => !sourceInventaireConnue(a))
  const pertes = ecarts.filter(e => e.valeur < 0).reduce((s, e) => s - e.valeur, 0)
  const excedents = ecarts.filter(e => e.valeur > 0).reduce((s, e) => s + e.valeur, 0)
  const calculIncomplet = sourcesInconnues.length > 0 || ecarts.some(e => e.valeur === null) || !Number.isFinite(pertes) || !Number.isFinite(excedents)
  const totalPerte    = calculIncomplet ? null : pertes
  const totalExcedent = calculIncomplet ? null : excedents

  function lignesPayload() {
    return preparerLignesComptage(feuille, comptes, {
      complet: dateInventaire === (exercice?.date_fin || `${annee}-12-31`),
    })
  }

  async function verifier() {
    setEnCours(true); setErreur('')
    try {
      setApercu(await apiFetch('/api/inventaire/simuler', {
        method: 'POST', body: JSON.stringify({ date: dateInventaire, reference, lignes: lignesPayload(), note }),
      }))
    } catch (e) { setErreur(e.message) }
    finally { setEnCours(false) }
  }

  async function valider() {
    let lignes
    try {
      lignes = lignesPayload()
    } catch (e) {
      setErreur(e.message)
      return
    }
    if (!confirm(
      `Valider l'inventaire physique du ${dateInventaire} ?\n\n` +
      `${lignes.length} article(s) seront figés dans la photographie d'inventaire.\n` +
      `${ecarts.length} écart(s) de quantité seront régularisés.\n` +
      `Impact des écarts : ${montantInventaire(totalExcedent - totalPerte)} MAD.\n\n` +
      `Le stock final devra ensuite être rapproché de la comptabilité.`
    )) return
    setEnCours(true); setErreur('')
    try {
      const r = await apiFetch('/api/inventaire/valider', {
        method: 'POST', body: JSON.stringify({ date: dateInventaire, reference, lignes, note }),
      })
      notifier(
        `Inventaire ${r.reference} validé.\n\n` +
        `${r.nb_regularises} article(s) régularisé(s)\n` +
        `Pertes : ${montantInventaire(r.total_perte)} MAD\n` +
        `Excédents : ${montantInventaire(r.total_excedent)} MAD\n` +
        `Impact net : ${montantInventaire(r.impact_net)} MAD\n` +
        `Valeur du stock figée : ${montantInventaire(r.total_valeur)} MAD`
      )
      setApercu(null); setNote('')
      charger()
    } catch (e) { setErreur(e.message) }
    finally { setEnCours(false) }
  }

  function exporter() {
    exporterCSV(`feuille_comptage_${new Date().toISOString().slice(0, 10)}`, [
      { label: 'Code',            get: l => l.code },
      { label: 'Désignation',     get: l => l.designation },
      { label: 'Unité',           get: l => l.unite },
      { label: 'Stock théorique', get: l => nombreInventaire(l.stock_theorique) === null ? 'À vérifier' : String(l.stock_theorique).replace('.', ',') },
      { label: 'Comptage',        get: l => '' },
      { label: 'CMUP',            get: l => nombreInventaire(l.cmup) === null ? 'À vérifier' : String(l.cmup).replace('.', ',') },
    ], feuille)
  }

  if (chargement) return <div className={styles.vide}>Chargement de la feuille de comptage…</div>

  return (
    <>
      <div className={styles.barre}>
        <div className={styles.recherche}>
          <i className="ti ti-search" />
          <input type="text" placeholder="Rechercher un article…"
            value={recherche} onChange={e => setRech(e.target.value)} />
        </div>
        <input className={styles.inputNote} style={{ minWidth: 150, width: 150 }} type="date" value={dateInventaire}
          min={exercice?.date_debut || ''} max={exercice?.date_fin || ''}
          onChange={e => setDateInventaire(e.target.value)} title="Date du comptage" />
        <input className={styles.inputNote} style={{ minWidth: 170, width: 170 }} type="text" placeholder="Référence inventaire"
          value={reference} onChange={e => setReference(e.target.value)} />
        <input className={styles.inputNote} style={{ minWidth: 220, flex: 1 }} type="text" placeholder="Motif de l'inventaire (optionnel)"
          value={note} onChange={e => setNote(e.target.value)} />
        <button className={styles.btnSec} onClick={exporter}>
          <i className="ti ti-download" /> Feuille vierge
        </button>
      </div>

      {erreur && <div className={styles.erreur}>{erreur}</div>}
      {calculIncomplet && <div className={styles.erreur} role="alert">À vérifier : corrigez les sources de stock ou de coût avant de simuler ou valider. {sourcesInconnues.map(a => <div key={a.article_id}>{a.code} : {diagnosticInventaire(a) || 'Stock théorique ou coût moyen inconnu.'}</div>)}</div>}

      {/* Récapitulatif des écarts, mis à jour pendant la saisie */}
      <div className={styles.recap}>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Articles comptés</span>
          <span className={styles.recapValeur}>{feuille.length}</span>
        </div>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Écarts détectés</span>
          <span className={styles.recapValeur} style={{ color: ecarts.length ? '#C9A227' : 'inherit' }}>
            {ecarts.length}
          </span>
        </div>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Pertes</span>
          <span className={styles.recapValeur} style={{ color: totalPerte ? '#A32D2D' : 'inherit' }}>
            {montantInventaire(totalPerte)} <small>MAD</small>
          </span>
        </div>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Excédents</span>
          <span className={styles.recapValeur} style={{ color: totalExcedent ? '#3B6D11' : 'inherit' }}>
            {montantInventaire(totalExcedent)} <small>MAD</small>
          </span>
        </div>
        <div className={styles.recapActions}>
          <button className={styles.btnSec} onClick={verifier} disabled={enCours || calculIncomplet || !feuille.length}>
            <i className="ti ti-list-check" /> Vérifier
          </button>
          <button className={styles.btnPrim} onClick={valider} disabled={enCours || calculIncomplet || !feuille.length || !dateInventaire || !reference.trim()}>
            <i className="ti ti-check" /> {enCours ? 'Traitement…' : 'Valider l\u2019inventaire'}
          </button>
        </div>
      </div>

      {/* Aperçu renvoyé par le serveur */}
      {apercu && (
        <div className={styles.apercu}>
          <div className={styles.apercuTitre}>
            <i className="ti ti-list-check" /> Contrôle avant validation — {apercu.nb_ecarts} écart(s),
            impact net {montantInventaire(apercu.impact_net)} MAD
            <button className={styles.btnFermerApercu} onClick={() => setApercu(null)}>
              <i className="ti ti-x" />
            </button>
          </div>
          <table className={styles.tableau}>
            <thead>
              <tr>
                <th>Article</th>
                <th className={styles.num}>Théorique</th>
                <th className={styles.num}>Compté</th>
                <th className={styles.num}>Écart</th>
                <th className={styles.num}>Valeur</th>
              </tr>
            </thead>
            <tbody>
              {apercu.ecarts.map(e => (
                <tr key={e.article_id}>
                  <td>{e.designation}</td>
                  <td className={styles.num}>{e.stock_theorique}</td>
                  <td className={styles.num}>{e.stock_reel}</td>
                  <td className={styles.num} style={{ color: e.ecart < 0 ? '#A32D2D' : '#3B6D11' }}>
                    {e.ecart > 0 ? '+' : ''}{e.ecart}
                  </td>
                  <td className={styles.num} style={{ color: e.valeur_ecart < 0 ? '#A32D2D' : '#3B6D11' }}>
                    {e.valeur_ecart > 0 ? '+' : ''}{montantInventaire(e.valeur_ecart)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Feuille de saisie */}
      <div className={styles.card} style={{ overflowX: 'auto' }}>
        <table className={styles.tableau}>
          <thead>
            <tr>
              <th style={{ width: 90 }}>Code</th>
              <th>Désignation</th>
              <th className={styles.num} style={{ width: 100 }}>Théorique</th>
              <th className={styles.num} style={{ width: 110 }}>Comptage</th>
              <th className={styles.num} style={{ width: 90 }}>Écart</th>
              <th className={styles.num} style={{ width: 110 }}>Valeur écart</th>
            </tr>
          </thead>
          <tbody>
            {visibles.map(a => {
              const saisi = comptes[a.article_id]
              const { ecart, valeur } = ecartInventaire(a, saisi)
              const modifie = ecart !== null && Math.abs(ecart) > 0.0001
              return (
                <tr key={a.article_id} className={modifie ? styles.ligneEcart : ''}>
                  <td className={styles.mono}>{a.code}</td>
                  <td>
                    {a.designation}
                    <span className={styles.unite}>{a.unite}</span>
                    {diagnosticInventaire(a) && <div style={{ color: '#8A5A0B', fontSize: 11 }}>À vérifier : {diagnosticInventaire(a)}</div>}
                  </td>
                  <td className={styles.num}>{quantiteInventaire(a.stock_theorique)}</td>
                  <td>
                    <input className={styles.inputQte} type="number" step="0.01"
                      value={saisi ?? ''}
                      onChange={e => setComptes(p => ({ ...p, [a.article_id]: e.target.value }))}
                      onFocus={e => e.target.select()} />
                  </td>
                  <td className={styles.num}
                    style={{ color: ecart === null ? 'var(--text-tertiary)' : ecart < 0 ? '#A32D2D' : ecart > 0 ? '#3B6D11' : 'var(--text-tertiary)' }}>
                    {ecart === null ? 'À vérifier' : ecart === 0 ? '0' : `${ecart > 0 ? '+' : ''}${+ecart.toFixed(2)}`}
                  </td>
                  <td className={styles.num}
                    style={{ color: !valeur ? 'var(--text-tertiary)' : valeur < 0 ? '#A32D2D' : '#3B6D11' }}>
                    {valeur === null ? 'À vérifier' : `${valeur > 0 ? '+' : ''}${montantInventaire(valeur)}`}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {visibles.length === 0 && (
          <div className={styles.vide}>Aucun article stockable ne correspond.</div>
        )}
      </div>
    </>
  )
}

// ─── Onglet 2 : valeur du stock ───────────────────────────────────────────────
function OngletValorisation() {
  const [etat, setEtat] = useState(null)
  const [chargement, setCharge] = useState(true)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    apiFetch('/api/inventaire/valorisation')
      .then(setEtat)
      .catch(e => setErreur(e.message))
      .finally(() => setCharge(false))
  }, [])

  function exporter() {
    if (!etat) return
    exporterCSV(`valorisation_stock_${new Date().toISOString().slice(0, 10)}`, [
      { label: 'Code',        get: l => l.code },
      { label: 'Désignation', get: l => l.designation },
      { label: 'Stock',       get: l => nombreInventaire(l.stock) === null ? 'À vérifier' : String(l.stock).replace('.', ',') },
      { label: 'CMUP',        get: l => nombreInventaire(l.cmup) === null ? 'À vérifier' : String(l.cmup).replace('.', ',') },
      { label: 'Valeur',      get: l => nombreInventaire(l.valeur) === null ? 'À vérifier' : String(l.valeur).replace('.', ',') },
      { label: 'Diagnostic', get: diagnosticInventaire },
    ], etat.lignes)
  }

  if (chargement) return <div className={styles.vide}>Chargement…</div>
  if (erreur)     return <div className={styles.erreur}>{erreur}</div>
  if (!etat)      return null

  const sousSeuil = etat.lignes.filter(l => l.sous_seuil)
  const seuilInconnu = etat.lignes.some(l => l.sous_seuil === null)

  return (
    <>
      <div className={styles.recap}>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Valeur totale du stock</span>
          <span className={styles.recapValeur} style={{ color: 'var(--blue)' }}>
            {montantInventaire(etat.total_valeur)} <small>MAD</small>
          </span>
        </div>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Articles en stock</span>
          <span className={styles.recapValeur}>{etat.nb_articles}</span>
        </div>
        <div className={styles.recapItem}>
          <span className={styles.recapLabel}>Sous le seuil d&apos;alerte</span>
          <span className={styles.recapValeur} style={{ color: sousSeuil.length ? '#A32D2D' : 'inherit' }}>
            {seuilInconnu ? 'À vérifier' : sousSeuil.length}
          </span>
        </div>
        <div className={styles.recapActions}>
          <button className={styles.btnSec} onClick={exporter}>
            <i className="ti ti-download" /> Exporter
          </button>
        </div>
      </div>

      <DiagnosticsInventaire etat={etat} />
      <div className={styles.aide}>
        Le stock est valorisé au <strong>coût moyen unitaire pondéré</strong> : chaque entrée
        recalcule le coût moyen, chaque sortie est valorisée à ce coût sans le modifier.
      </div>

      <div className={styles.card} style={{ overflowX: 'auto' }}>
        <table className={styles.tableau}>
          <thead>
            <tr>
              <th style={{ width: 90 }}>Code</th>
              <th>Désignation</th>
              <th className={styles.num} style={{ width: 100 }}>Stock</th>
              <th className={styles.num} style={{ width: 120 }}>Coût moyen</th>
              <th className={styles.num} style={{ width: 130 }}>Valeur</th>
            </tr>
          </thead>
          <tbody>
            {etat.lignes.map(l => (
              <tr key={l.article_id}>
                <td className={styles.mono}>{l.code}</td>
                <td>
                  {l.designation}
                  {diagnosticInventaire(l) && <div style={{ color: '#8A5A0B', fontSize: 11 }}>À vérifier : {diagnosticInventaire(l)}</div>}
                  {l.sous_seuil && (
                    <span className={styles.badgeSeuil}>
                      <i className="ti ti-alert-triangle" /> sous le seuil
                    </span>
                  )}
                </td>
                <td className={styles.num}>
                  {quantiteInventaire(l.stock)} <span className={styles.unite}>{l.unite}</span>
                </td>
                <td className={styles.num}>{montantInventaire(l.cmup)}</td>
                <td className={`${styles.num} ${styles.gras}`}>{montantInventaire(l.valeur)}</td>
              </tr>
            ))}
            <tr className={styles.ligneTotal}>
              <td colSpan={4}>Valeur totale du stock</td>
              <td className={styles.num}>{montantInventaire(etat.total_valeur)} MAD</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  )
}

// ─── Onglet 3 : audit des mouvements et du CMUP ──────────────────────────────
function OngletMouvements() {
  const [etat, setEtat] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [anomaliesSeulement, setAnomaliesSeulement] = useState(false)

  async function charger() {
    setChargement(true); setErreur('')
    try {
      setEtat(await apiFetch(`/api/inventaire/controle-mouvements?anomalies_uniquement=${anomaliesSeulement ? 'true' : 'false'}`))
    } catch (e) { setErreur(e.message) }
    finally { setChargement(false) }
  }

  useEffect(() => { charger() }, [anomaliesSeulement])

  if (chargement) return <div className={styles.vide}>Audit des mouvements de stock…</div>
  if (erreur) return <div className={styles.erreur}>{erreur}</div>
  if (!etat) return null

  const couleur = statut => statut === 'ok' ? '#3B6D11' : statut === 'warning' ? '#8A5A0B' : '#A32D2D'
  const libelle = statut => statut === 'ok' ? 'OK' : statut === 'warning' ? 'À vérifier' : 'Anomalie'

  return (
    <>
      <div className={styles.recap}>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Articles contrôlés</span><span className={styles.recapValeur}>{etat.articles_controles}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Mouvements contrôlés</span><span className={styles.recapValeur}>{etat.mouvements_controles}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Articles OK</span><span className={styles.recapValeur} style={{ color: '#3B6D11' }}>{etat.articles_ok}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>À vérifier</span><span className={styles.recapValeur} style={{ color: '#8A5A0B' }}>{etat.articles_warning}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>En anomalie</span><span className={styles.recapValeur} style={{ color: etat.articles_erreur ? '#A32D2D' : 'inherit' }}>{etat.articles_erreur}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Moteur 06C</span><span className={styles.recapValeur}>{etat.mouvements_06c ?? 0}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Historique legacy</span><span className={styles.recapValeur}>{etat.mouvements_legacy ?? 0}</span></div>
        <div className={styles.recapActions}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12 }}>
            <input type="checkbox" checked={anomaliesSeulement} onChange={e => setAnomaliesSeulement(e.target.checked)} />
            Afficher uniquement les anomalies
          </label>
          <button className={styles.btnSec} onClick={charger}><i className="ti ti-refresh" /> Recontrôler</button>
        </div>
      </div>

      <div className={styles.aide}>
        Contrôle en lecture seule : continuité stock avant/après, stock négatif, coût des sorties, CMUP avant/après et cohérence avec la fiche article.
        Les mouvements « Moteur 06C » passent par le service centralisé ; les lignes « Historique legacy » restent inchangées et servent uniquement de diagnostic.
      </div>

      {etat.audit_complet === false && <div className={styles.aide} role="alert">
        Audit incomplet — sources historiques à vérifier. Les nombres inconnus ne sont pas remplacés par zéro.
      </div>}

      <div className={styles.card} style={{ overflowX: 'auto' }}>
        <table className={styles.tableau}>
          <thead><tr>
            <th style={{ width: 90 }}>Code</th><th>Article</th>
            <th className={styles.num} style={{ width: 90 }}>Stock</th>
            <th className={styles.num} style={{ width: 110 }}>CMUP</th>
            <th className={styles.num} style={{ width: 90 }}>Mouvements</th>
            <th style={{ width: 95 }}>État</th><th>Diagnostic</th>
          </tr></thead>
          <tbody>
            {etat.lignes.map(l => (
              <tr key={l.article_id}>
                <td className={styles.mono}>{l.code}</td>
                <td>{l.designation}</td>
                <td className={styles.num}>{quantiteInventaire(l.stock_actuel)}</td>
                <td className={styles.num}>{montantInventaire(l.cmup_actuel)}</td>
                <td className={styles.num}>{l.nb_mouvements}</td>
                <td><strong style={{ color: couleur(l.statut) }}>{libelle(l.statut)}</strong></td>
                <td style={{ fontSize: 11.5, lineHeight: 1.45 }}>
                  {l.anomalies.length === 0 ? <span style={{ color: '#3B6D11' }}>Chaîne de mouvements cohérente.</span> :
                    l.anomalies.map((a, i) => <div key={`${a.code}-${i}`} style={{ color: a.niveau === 'warning' ? '#8A5A0B' : '#A32D2D' }}>{a.message}</div>)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {etat.lignes.length === 0 && <div className={styles.vide}>Aucune anomalie de mouvement détectée.</div>}
      </div>
    </>
  )
}

// ─── Onglet 4 : rapprochement stock / comptabilité ───────────────────────────
function OngletComptable({ annee, exercice }) {
  const { recharger } = useEcritures()
  const [etat, setEtat] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [action, setAction] = useState(false)

  async function charger() {
    setChargement(true); setErreur('')
    try { setEtat(await apiFetch(`/api/inventaire/stock/cloture?exercice=${annee}`)) }
    catch (e) { setErreur(e.message) }
    finally { setChargement(false) }
  }
  useEffect(() => { charger() }, [annee])

  async function comptabiliser() {
    if (etat?.valorisation_complete === false || nombreInventaire(etat?.ecart_brut) === null) { setErreur('À vérifier : valorisation du stock incomplète.'); return }
    if (!confirm(
      `Générer l'écriture de stock final ${annee} ?\n\n` +
      `Stock physique brut : ${montantInventaire(etat.valeur_physique_brute)} MAD\n` +
      `Stock comptable brut : ${montantInventaire(etat.valeur_comptable_brute)} MAD\n` +
      `Écart : ${montantInventaire(etat.ecart_brut)} MAD\n\n` +
      `L'écriture sera créée en brouillon au ${etat.date_fin}.`
    )) return
    setAction(true); setErreur('')
    try {
      const r = await apiFetch(`/api/inventaire/comptabiliser-stock?exercice=${annee}`, { method: 'POST' })
      notifier(r.message + (r.ecriture_id ? '\nValidez ensuite cette écriture dans le Journal.' : ''))
      await recharger?.()
      await charger()
    } catch (e) { setErreur(e.message) }
    finally { setAction(false) }
  }

  if (chargement) return <div className={styles.vide}>Contrôle du rapprochement…</div>
  if (erreur) return <div className={styles.erreur}>{erreur}</div>
  if (!etat) return null

  const cloture = exercice?.statut === 'cloture'
  return (
    <>
      <div className={styles.recap}>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Inventaire de clôture</span><span className={styles.recapValeur}>{etat.inventaire_valide ? 'Validé' : 'À valider'}</span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Stock physique brut</span><span className={styles.recapValeur}>{montantInventaire(etat.valeur_physique_brute)} <small>MAD</small></span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Stock comptable brut</span><span className={styles.recapValeur}>{montantInventaire(etat.valeur_comptable_brute)} <small>MAD</small></span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Dépréciations 391x</span><span className={styles.recapValeur}>{montantInventaire(etat.depreciations)} <small>MAD</small></span></div>
        <div className={styles.recapItem}><span className={styles.recapLabel}>Stock comptable net</span><span className={styles.recapValeur}>{montantInventaire(etat.valeur_comptable_nette)} <small>MAD</small></span></div>
      </div>

      <DiagnosticsInventaire etat={etat} />
      <div className={etat.stock_rapproche ? styles.aide : styles.erreur} style={{ marginBottom: 12 }}>
        {etat.valorisation_complete === false
          ? 'À vérifier : la valeur physique du stock est incomplète. Corrigez les sources avant le rapprochement.'
          : etat.stock_rapproche
          ? `Stock rapproché : le brut physique correspond aux comptes 31xx. Valeur nette après dépréciations : ${montantInventaire(etat.valeur_comptable_nette)} MAD.`
          : !etat.inventaire_valide
            ? `Validez d'abord un inventaire physique daté du ${etat.date_fin}. Le comptage peut être validé même s'il n'y a aucun écart de quantité.`
            : `Écart brut à comptabiliser : ${montantInventaire(etat.ecart_brut)} MAD.`}
      </div>

      <div className={styles.card} style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Comptabilisation du stock final — exercice {annee}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Le rapprochement compare la valeur physique brute au compte 31xx. Les dépréciations 391x sont déduites ensuite pour obtenir le stock net au bilan.
            </div>
          </div>
          <button className={styles.btnPrim} onClick={comptabiliser}
            disabled={action || cloture || etat.valorisation_complete === false || !etat.inventaire_valide || etat.stock_rapproche}>
            <i className="ti ti-calculator" /> {action ? 'Génération…' : 'Générer l’écriture de stock'}
          </button>
        </div>
        {cloture && <div style={{ marginTop: 10, fontSize: 11.5, color: '#8A5A0B' }}>L'exercice est clôturé. Rouvrez-le avant de corriger/comptabiliser son stock.</div>}
        {etat.ecriture_stock_id && !etat.ecriture_stock_validee && <div style={{ marginTop: 10, fontSize: 11.5, color: '#8A5A0B' }}>Écriture #{etat.ecriture_stock_id} créée en brouillon : validez-la dans le Journal pour terminer le rapprochement.</div>}
      </div>
    </>
  )
}
