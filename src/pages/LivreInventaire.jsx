import { useEffect, useMemo, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { API_BASE, estAdmin, formatErreurAPI, getToken } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import { nombreInventaire } from '../utils/inventaireComptage.js'

const montantStock = valeur => nombreInventaire(valeur) === null ? 'À vérifier' : formatMAD(valeur)
import styles from './LivreInventaire.module.css'

async function apiFetch(url, opts = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({ detail: `Erreur HTTP ${res.status}` }))
    throw new Error(formatErreurAPI(e.detail))
  }
  return res.json()
}

const Badge = ({ ok, labelOk = 'OK', labelKo = 'À vérifier' }) => (
  <span className={`${styles.badge} ${ok ? styles.badgeOk : styles.badgeWarn}`}>
    {ok ? labelOk : labelKo}
  </span>
)

function formatDateFR(value) {
  if (!value) return '—'
  const part = String(value).slice(0, 10).split('-')
  if (part.length !== 3) return value
  return `${part[2]}/${part[1]}/${part[0]}`
}

function formatDateHeureFR(value) {
  if (!value) return '—'
  const raw = String(value)
  const [d, t = ''] = raw.split('T')
  return `${formatDateFR(d)}${t ? ` ${t.slice(0, 5)}` : ''}`
}

function libelleStatut(value) {
  const map = { cloture: 'Clôturé', ouvert: 'Ouvert', a_venir: 'À venir', prepare: 'Préparé' }
  return map[value] || value || '—'
}

function TableauSimple({ rows, type = 'montant' }) {
  if (!rows?.length) return <div className={styles.vide}>Aucune donnée.</div>
  return (
    <table className={styles.tableau}>
      <thead><tr><th>Rubrique</th><th className={styles.num}>Montant (MAD)</th></tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={`${r.label}-${i}`}>
            <td>{r.label}</td>
            <td className={styles.num}>{formatMAD(type === 'net' ? r.net : r.montant)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function LivreInventaire() {
  const { annee, exercice } = useExercice()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const [onglet, setOnglet] = useState('synthese')
  const [archivage, setArchivage] = useState(false)

  async function charger() {
    setLoading(true); setErreur('')
    try { setData(await apiFetch(`/api/inventaire/livre?exercice=${annee}`)) }
    catch (e) { setErreur(e.message); setData(null) }
    finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [annee]) // eslint-disable-line react-hooks/exhaustive-deps

  const snap = data?.snapshot
  const archive = data?.archive
  const revisionRequise = Boolean(data?.revision_requise)
  const ctrl = snap?.controles || {}
  const rapImmos = snap?.immobilisations?.rapprochement || {}

  const cpcRows = useMemo(() => snap ? [
    ['Produits d’exploitation', snap.cpc.total_produits_exploitation],
    ['Charges d’exploitation', snap.cpc.total_charges_exploitation],
    ['Résultat d’exploitation', snap.cpc.resultat_exploitation],
    ['Résultat financier', snap.cpc.resultat_financier],
    ['Résultat non courant', snap.cpc.resultat_non_courant],
    ['Impôt sur les résultats', snap.cpc.impot_resultat],
    ['Résultat net', snap.cpc.resultat_net],
  ] : [], [snap])

  async function archiver() {
    if (!confirm(
      revisionRequise
        ? `Créer l'archive version 2 du livre d'inventaire ${annee} ?\n\nL'archive version ${archive?.version || 1} restera conservée avec son empreinte d'origine.`
        : `Archiver définitivement le livre d'inventaire ${annee} ?\n\nUne fois créée, cette version archivée restera conservée dans HisabPro.`
    )) return
    setArchivage(true); setErreur('')
    try {
      const r = await apiFetch(`/api/inventaire/livre/archiver?exercice=${annee}`, { method: 'POST' })
      setData(r)
    } catch (e) { setErreur(e.message) }
    finally { setArchivage(false) }
  }

  async function telechargerPdf() {
    setErreur('')
    try {
      const res = await fetch(`${API_BASE}/api/inventaire/livre/pdf?exercice=${annee}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({ detail: `Erreur HTTP ${res.status}` }))
        throw new Error(formatErreurAPI(e.detail))
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `livre_inventaire_${annee}.pdf`; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) { setErreur(e.message) }
  }

  if (loading) return <div className={styles.page}><div className={styles.vide}>Construction du livre d’inventaire {annee}…</div></div>

  return (
    <div className={styles.page}>
      <div className={styles.topbar}>
        <div>
          <div className={styles.titreLigne}>
            <h1 className={styles.pageTitle}>Livre d’inventaire</h1>
            {archive && !revisionRequise
              ? <span className={styles.archive}>Archivé v{archive.version}</span>
              : archive && revisionRequise
                ? <span className={styles.apercu}>Archive v{archive.version} — révision requise</span>
                : <span className={styles.apercu}>Aperçu dynamique</span>}
          </div>
          <p className={styles.pageSub}>
            Exercice {annee}{exercice ? ` — ${formatDateFR(exercice.date_debut)} au ${formatDateFR(exercice.date_fin)}` : ''}{snap?.exercice?.statut ? ` · ${libelleStatut(snap.exercice.statut)}` : ''}
          </p>
        </div>
        <div className={styles.actions}>
          <button className={styles.btnSec} onClick={telechargerPdf} disabled={!snap}>
            <i className="ti ti-file-type-pdf" /> Exporter PDF
          </button>
          {(!archive || revisionRequise) && estAdmin() && (
            <button
              className={styles.btnPrim}
              onClick={archiver}
              disabled={archivage || !ctrl.archivable}
              title={!ctrl.archivable ? 'Tous les contrôles doivent être au vert avant archivage.' : ''}
            >
              <i className="ti ti-lock-check" /> {archivage ? 'Archivage…' : (revisionRequise ? 'Archiver la version 2' : 'Archiver définitivement')}
            </button>
          )}
        </div>
      </div>

      {erreur && <div className={styles.erreur}>{erreur}</div>}

      {archive && (
        <div className={styles.archiveInfo}>
          <div><b>Archive v{archive.version} figée</b> le {formatDateHeureFR(archive.date_etablissement)}</div>
          <div className={styles.hash}>SHA-256 : {archive.empreinte_sha256}</div>
        </div>
      )}

      {archive && revisionRequise && (
        <div className={styles.warning}>
          Cette archive v{archive.version} reste conservée, mais elle a été créée avant les contrôles 05B.
          L'écran ci-dessous est recalculé avec les règles actuelles. Une archive v2 ne pourra être créée qu'après rapprochement des immobilisations.
        </div>
      )}

      {!archive && snap && (
        <div className={styles.info}>
          Cet écran est encore un aperçu calculé sur les données actuelles. Après clôture et contrôles, l’archivage fige une copie indépendante des modifications futures.
        </div>
      )}

      {(!archive || revisionRequise) && snap && !ctrl.archivable && (
        <div className={styles.warning}>
          Archivage définitif bloqué : tous les contrôles doivent être au vert.
          {!ctrl.inventaire_stock_valide && <> Aucun inventaire physique de clôture n’a été validé.</>}
          {ctrl.inventaire_stock_valide && !ctrl.stock_rapproche && (
            <> Stock physique brut {montantStock(snap.stocks.valeur_physique)} MAD, stock comptable brut {montantStock(snap.stocks.valeur_comptable_brute)} MAD, écart {montantStock(snap.stocks.ecart_physique_comptable)} MAD.</>
          )}
          {!ctrl.immobilisations_rapprochees && rapImmos && (
            <> Immobilisations : brut registre {formatMAD(rapImmos.brut_module)} MAD / comptabilité {formatMAD(rapImmos.brut_comptable)} MAD ; amortissements registre {formatMAD(rapImmos.amortissements_module)} MAD / comptabilité {formatMAD(rapImmos.amortissements_comptables)} MAD.</>
          )}
        </div>
      )}

      {snap && (
        <>
          {snap.stocks.valorisation_complete === false && <div role="alert" className={styles.warning}><strong>À vérifier — valorisation du stock incomplète</strong>{(snap.stocks.diagnostics || []).map((d, i) => <div key={i}>{d.code ? `${d.code} : ` : ''}{d.message}</div>)}</div>}
          <div className={styles.controles}>
            <div><span>Exercice clôturé</span><Badge ok={ctrl.exercice_cloture} /></div>
            <div><span>Aucun brouillon</span><Badge ok={ctrl.aucun_brouillon} /></div>
            <div><span>Balance équilibrée</span><Badge ok={ctrl.balance_equilibree} /></div>
            <div><span>Bilan équilibré</span><Badge ok={ctrl.bilan_equilibre} /></div>
            <div><span>Inventaire stock</span><Badge ok={ctrl.inventaire_stock_valide} labelKo="À valider" /></div>
            <div><span>Stock / comptabilité</span><Badge ok={ctrl.stock_rapproche} labelKo="Écart à analyser" /></div>
            <div><span>Immobilisations / comptabilité</span><Badge ok={ctrl.immobilisations_rapprochees} labelKo="Écart à analyser" /></div>
          </div>

          {ctrl.historique_stock_limite && (
            <div className={styles.warning}>
              Sans inventaire physique de clôture validé, les quantités et CMUP affichés pour les articles stockables proviennent de l’état courant. Cet aperçu ne constitue pas une photographie historique du stock à la clôture.
            </div>
          )}

          <div className={styles.kpis}>
            <div><span>Total actif</span><b>{formatMAD(snap.bilan.total_actif)} MAD</b></div>
            <div><span>Total passif</span><b>{formatMAD(snap.bilan.total_passif)} MAD</b></div>
            <div><span>Résultat net</span><b>{formatMAD(snap.cpc.resultat_net)} MAD</b></div>
            <div><span>Stock physique</span><b>{montantStock(snap.stocks.valeur_physique)} MAD</b></div>
            <div><span>VNC immobilisations</span><b>{formatMAD(snap.immobilisations.vnc)} MAD</b></div>
          </div>

          <div className={styles.onglets}>
            {[
              ['synthese', 'Bilan & CPC'],
              ['stocks', 'Stocks'],
              ['immos', 'Immobilisations'],
              ['ajustements', 'Ajustements'],
              ['balance', 'Balance de clôture'],
            ].map(([id, label]) => (
              <button key={id} onClick={() => setOnglet(id)} className={onglet === id ? styles.ongletActif : ''}>{label}</button>
            ))}
          </div>

          {onglet === 'synthese' && (
            <div className={styles.grid2}>
              <section className={styles.card}>
                <h2>Bilan — Actif</h2>
                <h3>Actif immobilisé</h3><TableauSimple rows={snap.bilan.actif_immobilise} type="net" />
                <h3>Actif circulant</h3><TableauSimple rows={snap.bilan.actif_circulant} type="net" />
                <h3>Trésorerie-actif</h3><TableauSimple rows={snap.bilan.tresorerie_actif} type="net" />
              </section>
              <section className={styles.card}>
                <h2>Bilan — Passif</h2>
                <h3>Capitaux propres</h3><TableauSimple rows={snap.bilan.capitaux_propres} />
                <h3>Financement permanent</h3><TableauSimple rows={snap.bilan.financement_permanent} />
                <h3>Passif circulant</h3><TableauSimple rows={snap.bilan.passif_circulant} />
                <h3>Trésorerie-passif</h3><TableauSimple rows={snap.bilan.tresorerie_passif} />
              </section>
              <section className={`${styles.card} ${styles.large}`}>
                <h2>Compte de produits et charges — synthèse</h2>
                <table className={styles.tableau}>
                  <thead><tr><th>Rubrique</th><th className={styles.num}>Montant (MAD)</th></tr></thead>
                  <tbody>{cpcRows.map(([l, v]) => <tr key={l}><td>{l}</td><td className={styles.num}>{formatMAD(v)}</td></tr>)}</tbody>
                </table>
              </section>
            </div>
          )}

          {onglet === 'stocks' && (
            <section className={styles.card}>
              <div className={styles.sectionHeader}>
                <h2>Inventaire des stocks</h2>
                <span>Physique brut {montantStock(snap.stocks.valeur_physique)} MAD · Comptable brut {montantStock(snap.stocks.valeur_comptable_brute)} MAD · Dépréciations {montantStock(snap.stocks.depreciations)} MAD · Net {montantStock(snap.stocks.valeur_comptable_nette)} MAD · Écart brut {montantStock(snap.stocks.ecart_physique_comptable)} MAD</span>
              </div>
              <table className={styles.tableau}>
                <thead><tr><th>Code</th><th>Désignation</th><th>Emplacement</th><th className={styles.num}>Qté</th><th className={styles.num}>CMUP</th><th className={styles.num}>Valeur</th></tr></thead>
                <tbody>{snap.stocks.lignes.map(x => <tr key={x.article_id}><td className={styles.mono}>{x.code}</td><td>{x.designation}{Object.values(x.nombres_diagnostics || {}).map((d, i) => <div key={i} style={{ color: '#8A5A0B', fontSize: 11 }}>{d}</div>)}</td><td>{x.emplacement || '—'}</td><td className={styles.num}>{nombreInventaire(x.quantite) === null ? 'À vérifier' : x.quantite}</td><td className={styles.num}>{montantStock(x.cmup)}</td><td className={styles.num}>{montantStock(x.valeur)}</td></tr>)}</tbody>
              </table>
              {!snap.stocks.lignes.length && <div className={styles.vide}>Aucun article stockable.</div>}
            </section>
          )}

          {onglet === 'immos' && (
            <section className={styles.card}>
              <div className={styles.sectionHeader}><h2>Inventaire des immobilisations</h2><span>{snap.immobilisations.nb} immobilisation(s) · VNC registre {formatMAD(snap.immobilisations.vnc)} MAD</span></div>

              <div className={ctrl.immobilisations_rapprochees ? styles.info : styles.warning}>
                Registre : brut {formatMAD(rapImmos.brut_module)} MAD · amortissements {formatMAD(rapImmos.amortissements_module)} MAD · VNC {formatMAD(rapImmos.vnc_module)} MAD.
                {' '}Comptabilité sur les comptes configurés : brut {formatMAD(rapImmos.brut_comptable)} MAD · amortissements {formatMAD(rapImmos.amortissements_comptables)} MAD · VNC {formatMAD(rapImmos.vnc_comptable)} MAD.
              </div>

              {!ctrl.immobilisations_rapprochees && rapImmos.details_comptes?.length > 0 && (
                <table className={styles.tableau}>
                  <thead><tr><th>Nature</th><th>Compte</th><th className={styles.num}>Registre</th><th className={styles.num}>Comptabilité</th><th className={styles.num}>Écart</th></tr></thead>
                  <tbody>{rapImmos.details_comptes.filter(x => Math.abs(Number(x.ecart || 0)) > 0.009).map((x, i) => (
                    <tr key={`${x.nature}-${x.compte}-${i}`}><td>{x.nature === 'brut' ? 'Valeur brute' : 'Amortissement'}</td><td className={styles.mono}>{x.compte}</td><td className={styles.num}>{formatMAD(x.module)}</td><td className={styles.num}>{formatMAD(x.comptable)}</td><td className={styles.num}>{formatMAD(x.ecart)}</td></tr>
                  ))}</tbody>
                </table>
              )}

              <table className={styles.tableau}>
                <thead><tr><th>Référence</th><th>Désignation</th><th>Compte</th><th className={styles.num}>Brut</th><th className={styles.num}>Amort. cumulés</th><th className={styles.num}>VNC</th></tr></thead>
                <tbody>{snap.immobilisations.lignes.map(x => <tr key={x.id}><td>{x.reference || '—'}</td><td>{x.designation}</td><td className={styles.mono}>{x.compte_immo}</td><td className={styles.num}>{formatMAD(x.valeur_brute)}</td><td className={styles.num}>{formatMAD(x.amortissements_cumules)}</td><td className={styles.num}>{formatMAD(x.vnc)}</td></tr>)}</tbody>
              </table>
            </section>
          )}

          {onglet === 'ajustements' && (
            <section className={styles.card}>
              <h2>Écritures d’inventaire et cut-off</h2>
              <table className={styles.tableau}>
                <thead><tr><th>Type</th><th>Libellé</th><th>Comptes</th><th className={styles.num}>Montant</th></tr></thead>
                <tbody>{snap.ajustements_inventaire.map(x => <tr key={x.id}><td>{x.type.toUpperCase()}</td><td>{x.libelle}</td><td className={styles.mono}>{x.compte_activite} / {x.compte_contrepartie}</td><td className={styles.num}>{formatMAD(x.montant)}</td></tr>)}</tbody>
              </table>
              {!snap.ajustements_inventaire.length && <div className={styles.vide}>Aucun ajustement d’inventaire.</div>}
            </section>
          )}

          {onglet === 'balance' && (
            <section className={styles.card}>
              <div className={styles.sectionHeader}><h2>Balance des comptes de bilan</h2><span>{snap.comptabilite.nb_ecritures_validees} écriture(s) validée(s)</span></div>
              <table className={styles.tableau}>
                <thead><tr><th>Compte</th><th className={styles.num}>Débit</th><th className={styles.num}>Crédit</th><th>Sens</th></tr></thead>
                <tbody>{snap.comptabilite.balance_comptes_bilan.map(x => <tr key={x.compte}><td className={styles.mono}>{x.compte}</td><td className={styles.num}>{formatMAD(x.debit)}</td><td className={styles.num}>{formatMAD(x.credit)}</td><td>{x.sens}</td></tr>)}</tbody>
              </table>
            </section>
          )}

          <div className={styles.legal}>
            Archive numérique interne HisabPro. Elle ne remplace pas, à elle seule, les formalités externes de conservation, cotation ou paraphe qui peuvent rester applicables à l’entreprise.
          </div>
        </>
      )}
    </div>
  )
}
