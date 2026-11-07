import React, { useEffect, useMemo, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { formatMAD } from '../data/donnees.js'
import { API_BASE, peutEcrire, formatErreurAPI } from '../services/api.js'
import { exporterCSV } from '../services/exportCSV.js'
import Modal from '../components/Modal.jsx'
import { dateLocaleISO, nombreOuDefaut } from '../utils/formUtils.js'
import styles from './SituationFinanciere.module.css'

const TRANCHES = [
  { cle: 'non_echu', label: 'Non échu' },
  { cle: '1_30', label: '1 – 30 j' },
  { cle: '31_60', label: '31 – 60 j' },
  { cle: '61_90', label: '61 – 90 j' },
  { cle: 'plus_90', label: '+ 90 j' },
]

const LABEL_STATUT = {
  a_echoir: 'À échoir',
  echue: 'Échue aujourd’hui',
  en_retard: 'En retard',
  partiellement_reglee: 'Partiellement réglée',
  non_reglee: 'Non réglée',
  reglee: 'Réglée',
  sans_echeance: 'Sans échéance',
  indetermine: 'À vérifier',
}

function montantConnu(v) { return typeof v === 'number' && Number.isFinite(v) }
function montantAffiche(v) { return montantConnu(v) ? formatMAD(v) : 'À vérifier' }
function montantCSV(v) { return montantConnu(v) ? v.toFixed(2).replace('.', ',') : 'À vérifier' }

function authHeaders(json = false) {
  const h = { Authorization: `Bearer ${localStorage.getItem('hisabpro_token')}` }
  if (json) h['Content-Type'] = 'application/json'
  return h
}

function fmtDate(v) {
  if (!v) return '—'
  const [y, m, d] = String(v).slice(0, 10).split('-')
  return y && m && d ? `${d}/${m}/${y}` : v
}

function BadgeStatut({ facture }) {
  const statut = facture.statut
  return (
    <span className={`${styles.badge} ${styles[`badge_${statut}`] || ''}`}>
      {LABEL_STATUT[statut] || statut}
      {facture.statut === 'en_retard' && facture.statut_paiement === 'partiellement_reglee' && (
        <span className={styles.badgeDetail}> · partiel</span>
      )}
    </span>
  )
}

function CarteKPI({ label, valeur, detail, icone, alerte = false, format = 'mad' }) {
  return (
    <div className={`${styles.kpi} ${alerte ? styles.kpiAlerte : ''}`}>
      <div className={styles.kpiLabel}><i className={`ti ${icone}`} />{label}</div>
      <div className={styles.kpiValeur}>{!montantConnu(valeur) ? 'À vérifier' : format === 'pct' ? valeur.toFixed(1) : formatMAD(valeur)} {montantConnu(valeur) && <span>{format === 'pct' ? '%' : 'MAD'}</span>}</div>
      {detail && <div className={styles.kpiDetail}>{detail}</div>}
    </div>
  )
}

export default function SituationFinanciere() {
  const { annee } = useExercice()
  const [data, setData] = useState(null)
  const [relances, setRelances] = useState([])
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const [message, setMessage] = useState('')
  const [onglet, setOnglet] = useState('vue')
  const [type, setType] = useState('vente')
  const [recherche, setRecherche] = useState('')
  const [filtreStatut, setFiltreStatut] = useState('ouvertes')
  const [montantMin, setMontantMin] = useState('')
  const [retardMin, setRetardMin] = useState('')
  const [echeanceMax, setEcheanceMax] = useState('')
  const [relanceFacture, setRelanceFacture] = useState(null)
  const [savingRelance, setSavingRelance] = useState(false)
  const [relanceEdition, setRelanceEdition] = useState(null)
  const [annulationRelance, setAnnulationRelance] = useState(null)
  const [relanceForm, setRelanceForm] = useState({
    niveau: 1,
    date_relance: dateLocaleISO(),
    canal: 'email',
    commentaire: '',
    date_promesse_reglement: '',
    montant_promis: '',
    prochaine_relance: '',
  })

  async function charger() {
    setLoading(true); setErreur('')
    try {
      const [s, r] = await Promise.all([
        fetch(`${API_BASE}/api/recouvrement/situation?exercice=${annee}`, { headers: authHeaders() }),
        fetch(`${API_BASE}/api/recouvrement/relances?exercice=${annee}`, { headers: authHeaders() }),
      ])
      if (!s.ok) throw new Error(formatErreurAPI((await s.json().catch(() => ({}))).detail))
      if (!r.ok) throw new Error(formatErreurAPI((await r.json().catch(() => ({}))).detail))
      setData(await s.json())
      setRelances(await r.json())
    } catch (e) {
      setErreur(e.message || 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { charger() }, [annee])

  const factures = useMemo(() => {
    if (!data) return []
    const q = recherche.trim().toLowerCase()
    return data.factures.filter(f => {
      if (f.type !== type) return false
      if (q && !`${f.numero || ''} ${f.tiers || ''}`.toLowerCase().includes(q)) return false
      if (filtreStatut === 'ouvertes' && montantConnu(f.reste_du) && f.reste_du <= 0.01) return false
      if (filtreStatut === 'retard' && f.statut_echeance !== 'en_retard') return false
      if (filtreStatut === 'a_echoir' && f.statut_echeance !== 'a_echoir') return false
      if (filtreStatut === 'partiel' && (f.statut_paiement !== 'partiellement_reglee' || f.reste_du <= 0.01)) return false
      if (montantMin !== '' && f.reste_du < Number(montantMin || 0)) return false
      if (retardMin !== '' && f.jours_retard < Number(retardMin || 0)) return false
      if (echeanceMax && (!f.date_echeance || f.date_echeance > echeanceMax)) return false
      return true
    })
  }, [data, type, recherche, filtreStatut, montantMin, retardMin, echeanceMax])

  const relancesFiltrees = useMemo(() => {
    const factMap = new Map((data?.factures || []).map(f => [f.id, f]))
    return relances
      .map(r => ({ ...r, facture: factMap.get(r.facture_id) }))
  }, [relances, data])

  function ouvrirRelance(f) {
    if (!peutEcrire()) return
    setRelanceEdition(null)
    setErreur('')
    setRelanceFacture(f)
    const prochaine = new Date()
    prochaine.setDate(prochaine.getDate() + 7)
    const niveauPrecedent = f.derniere_relance?.niveau || 0
    setRelanceForm({
      niveau: Math.min(3, niveauPrecedent + 1 || 1),
      date_relance: dateLocaleISO(),
      canal: 'email',
      commentaire: '',
      date_promesse_reglement: '',
      montant_promis: '',
      prochaine_relance: `${prochaine.getFullYear()}-${String(prochaine.getMonth() + 1).padStart(2, '0')}-${String(prochaine.getDate()).padStart(2, '0')}`,
    })
  }

  function modifierRelance(r) {
    if (!peutEcrire() || r.statut === 'annulee') return
    setErreur('')
    setRelanceEdition(r)
    setRelanceFacture(r.facture || { id: r.facture_id, numero: r.facture_numero, tiers: r.tiers })
    setRelanceForm({ niveau: r.niveau, date_relance: r.date_relance, canal: r.canal,
      commentaire: r.commentaire || '', date_promesse_reglement: r.date_promesse_reglement || '',
      montant_promis: r.montant_promis ?? '', prochaine_relance: r.prochaine_relance || '' })
  }

  async function annulerRelance(r) {
    if (!peutEcrire() || annulationRelance !== null) return
    if (!window.confirm('Annuler cette relance ? Elle restera visible dans l’historique.')) return
    setAnnulationRelance(r.id); setErreur(''); setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/recouvrement/relances/${r.id}`, {
        method: 'PATCH', headers: authHeaders(true), body: JSON.stringify({ statut: 'annulee' }),
      })
      if (!res.ok) throw new Error(formatErreurAPI((await res.json().catch(() => ({}))).detail))
      setMessage('Relance annulée ; historique conservé.')
      await charger()
    } catch (e) { setErreur(e.message) }
    finally { setAnnulationRelance(null) }
  }

  async function enregistrerRelance(e) {
    e.preventDefault()
    if (!relanceFacture || !peutEcrire() || savingRelance) return
    setSavingRelance(true); setErreur(''); setMessage('')
    try {
      const payload = {
        facture_id: relanceFacture.id,
        niveau: Number(relanceForm.niveau),
        date_relance: relanceForm.date_relance,
        canal: relanceForm.canal,
        commentaire: relanceForm.commentaire.trim() || null,
        date_promesse_reglement: relanceForm.date_promesse_reglement || null,
        montant_promis: relanceForm.montant_promis === '' ? null : nombreOuDefaut(relanceForm.montant_promis, null),
        prochaine_relance: relanceForm.prochaine_relance || null,
      }
      const modifications = relanceEdition ? Object.fromEntries(Object.entries(payload)
        .filter(([key, value]) => !['facture_id', 'date_relance'].includes(key) && value !== (relanceEdition[key] ?? null))) : payload
      const res = await fetch(`${API_BASE}/api/recouvrement/relances${relanceEdition ? `/${relanceEdition.id}` : ''}`, {
        method: relanceEdition ? 'PATCH' : 'POST', headers: authHeaders(true), body: JSON.stringify(modifications),
      })
      if (!res.ok) throw new Error(formatErreurAPI((await res.json().catch(() => ({}))).detail))
      setRelanceFacture(null)
      setMessage(relanceEdition ? 'Relance mise à jour.' : 'Relance enregistrée dans l’historique.')
      setRelanceEdition(null)
      await charger()
    } catch (e2) {
      setErreur(e2.message)
    } finally {
      setSavingRelance(false)
    }
  }

  function exporter() {
    exporterCSV(`echeances_${type}_${annee}`, [
      { label: 'Facture', get: x => x.numero || `#${x.id}` },
      { label: type === 'vente' ? 'Client' : 'Fournisseur', get: x => x.tiers },
      { label: 'Date facture', get: x => x.date },
      { label: 'Échéance', get: x => x.date_echeance },
      { label: 'TTC', get: x => x.total_ttc, type: 'nombre' },
      { label: 'Imputé', get: x => montantCSV(x.total_impute) },
      { label: 'Reste dû', get: x => montantCSV(x.reste_du) },
      { label: 'Retard (j)', get: x => x.jours_retard, type: 'nombre' },
      { label: 'Statut', get: x => LABEL_STATUT[x.statut] || x.statut },
      { label: 'Diagnostic', get: x => x.ras_anomalie || '' },
    ], factures)
  }

  const vente = data?.resume?.vente
  const achat = data?.resume?.achat

  return (
    <div className={styles.page}>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Situation financière & recouvrement</h1>
          <p className={styles.pageSub}>Échéances, impayés, balance âgée et relances — exercice {annee}</p>
        </div>
        <button className={styles.btnSec} onClick={exporter} disabled={!data || onglet !== 'echeances'}>
          <i className="ti ti-download" /> Exporter
        </button>
      </div>

      <div className={styles.tabs}>
        <button className={onglet === 'vue' ? styles.tabActive : ''} onClick={() => setOnglet('vue')}>Vue d’ensemble</button>
        <button className={onglet === 'echeances' ? styles.tabActive : ''} onClick={() => setOnglet('echeances')}>Échéances & impayés</button>
        <button className={onglet === 'balance' ? styles.tabActive : ''} onClick={() => setOnglet('balance')}>Balance âgée</button>
        <button className={onglet === 'relances' ? styles.tabActive : ''} onClick={() => setOnglet('relances')}>Relances</button>
      </div>

      <div className={styles.content}>
        {message && <div className={styles.success}><i className="ti ti-circle-check" />{message}</div>}
        {loading ? <div className={styles.etatVide}>Chargement…</div> : erreur && !data ? (
          <div className={styles.etatErreur}>{erreur}</div>
        ) : !data ? null : (
          <>
            {erreur && <div className={styles.etatErreurInline}>{erreur}</div>}
            {(vente.calcul_incomplet || achat.calcul_incomplet) && <div role="status" className={styles.etatErreurInline}>Calcul incomplet : des soldes historiques sont à vérifier. Les totaux et la balance âgée concernés ne peuvent pas être déterminés ; consultez les diagnostics dans Échéances & impayés.</div>}

            {onglet === 'vue' && <VueEnsemble data={data} />}

            {onglet === 'echeances' && (
              <>
                <BarreFiltres type={type} setType={setType} recherche={recherche} setRecherche={setRecherche}
                  filtreStatut={filtreStatut} setFiltreStatut={setFiltreStatut}
                  montantMin={montantMin} setMontantMin={setMontantMin} retardMin={retardMin} setRetardMin={setRetardMin}
                  echeanceMax={echeanceMax} setEcheanceMax={setEcheanceMax} />
                <div className={styles.card}>
                  <div className={styles.cardHeader}>
                    <div>
                      <div className={styles.cardTitle}>{type === 'vente' ? 'Créances clients' : 'Dettes fournisseurs'}</div>
                      <div className={styles.cardSub}>{factures.length} facture{factures.length > 1 ? 's' : ''} affichée{factures.length > 1 ? 's' : ''}</div>
                    </div>
                  </div>
                  <div className={styles.tableWrap}>
                    <table className={styles.facturesTable}>
                      <thead><tr>
                        <th>Facture</th><th>{type === 'vente' ? 'Client' : 'Fournisseur'}</th><th>Échéance</th>
                        <th className={styles.right}>TTC</th><th className={styles.right}>Imputé</th><th className={styles.right}>Reste dû</th>
                        <th>Situation</th><th>Dernière relance</th><th />
                      </tr></thead>
                      <tbody>
                        {factures.length === 0 ? (
                          <tr><td colSpan="9" className={styles.emptyRow}>Aucune facture ne correspond aux filtres.</td></tr>
                        ) : factures.map(f => (
                          <tr key={f.id}>
                            <td><strong>{f.numero || `Brouillon #${f.id}`}</strong><div className={styles.muted}>{fmtDate(f.date)}</div></td>
                            <td><div className={styles.tiersNom}>{f.tiers}</div></td>
                            <td>{fmtDate(f.date_echeance)}{(f.echeances?.length || 0) > 1 && <div className={styles.muted}>{f.echeances.filter(e => Number(e.reste_du || 0) > 0.01).length}/{f.echeances.length} échéances ouvertes</div>}{f.jours_retard > 0 && <div className={styles.retard}>{f.jours_retard} j de retard · {formatMAD(f.montant_en_retard || 0)} MAD</div>}</td>
                            <td className={styles.right}>{montantAffiche(f.total_ttc)}</td>
                            <td className={styles.right}><span className={styles.mutedAmount}>{montantAffiche(f.total_impute)}</span></td>
                            <td className={`${styles.right} ${styles.reste}`}>{montantAffiche(f.reste_du)}</td>
                            <td><BadgeStatut facture={f} />{f.ras_anomalie && <div className={styles.muted}>{f.ras_anomalie}</div>}</td>
                            <td>{f.derniere_relance ? <><strong>Niv. {f.derniere_relance.niveau}</strong><div className={styles.muted}>{fmtDate(f.derniere_relance.date_relance)}</div></> : <span className={styles.muted}>Jamais</span>}</td>
                            <td className={styles.actionsCell}>
                              {peutEcrire() && f.type === 'vente' && f.reste_du > 0.01 && (
                                <button className={styles.btnRelance} onClick={() => ouvrirRelance(f)}><i className="ti ti-mail-forward" /> Relancer</button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}

            {onglet === 'balance' && (
              <div className={styles.balanceGrid}>
                <BalanceBloc titre="Balance âgée clients" bloc={vente} />
                <BalanceBloc titre="Balance âgée fournisseurs" bloc={achat} />
              </div>
            )}

            {onglet === 'relances' && (
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div><div className={styles.cardTitle}>Historique des relances clients</div><div className={styles.cardSub}>{relancesFiltrees.length} relance{relancesFiltrees.length > 1 ? 's' : ''}</div></div>
                </div>
                <div className={styles.tableWrap}>
                  <table className={styles.facturesTable}>
                    <thead><tr><th>Date</th><th>Facture</th><th>Client</th><th>Niveau</th><th>Canal</th><th>Promesse</th><th>Prochaine relance</th><th>Commentaire</th><th>Statut</th><th>Actions</th></tr></thead>
                    <tbody>
                      {relancesFiltrees.length === 0 ? <tr><td colSpan="10" className={styles.emptyRow}>Aucune relance enregistrée.</td></tr> : relancesFiltrees.map(r => (
                        <tr key={r.id}>
                          <td>{fmtDate(r.date_relance)}</td>
                          <td><strong>{r.facture?.numero || r.facture_numero || `#${r.facture_id}`}</strong></td>
                          <td>{r.facture?.tiers || r.tiers || '—'}</td>
                          <td><span className={styles.niveau}>Niveau {r.niveau}</span></td>
                          <td>{canalLabel(r.canal)}</td>
                          <td>{r.date_promesse_reglement ? <>{fmtDate(r.date_promesse_reglement)}{r.montant_promis != null && <div className={styles.muted}>{formatMAD(r.montant_promis)} MAD</div>}</> : '—'}</td>
                          <td>{fmtDate(r.prochaine_relance)}</td>
                          <td className={styles.commentaire}>{r.commentaire || '—'}</td>
                          <td>{r.statut === 'annulee' ? 'Annulée' : 'Effectuée'}</td>
                          <td className={styles.actionsCell}>{peutEcrire() && r.statut !== 'annulee' && <>
                            <button className={styles.btnSec} disabled={annulationRelance !== null} onClick={() => modifierRelance(r)}>Modifier</button>{' '}
                            <button className={styles.btnSec} disabled={annulationRelance !== null} onClick={() => annulerRelance(r)}>Annuler la relance</button>
                          </>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {relanceFacture && (
        <Modal titre={relanceEdition ? 'Modifier la relance' : `Relancer ${relanceFacture.tiers}`} icone="ti-mail-forward" onFermer={() => !savingRelance && setRelanceFacture(null)} largeur="md">
          <form onSubmit={enregistrerRelance} className={styles.relanceForm}>
            <p>Enregistrez ici le compte-rendu d’un contact effectué avec le client.</p>
            {erreur && <div role="alert" className={styles.etatErreurInline}>{erreur}</div>}
            <div className={styles.factureResume}>
              <div><span>Facture</span><strong>{relanceFacture.numero}</strong></div>
              <div><span>Échéance</span><strong>{fmtDate(relanceFacture.date_echeance)}</strong></div>
              <div><span>Reste à payer</span><strong>{relanceFacture.reste_du == null ? 'À compléter' : `${formatMAD(relanceFacture.reste_du)} MAD`}</strong></div>
              <div><span>Retard</span><strong>{relanceFacture.jours_retard ? `${relanceFacture.jours_retard} jours` : '—'}</strong></div>
            </div>
            <div className={styles.formGrid}>
              <label>Niveau de relance<select value={relanceForm.niveau} onChange={e => setRelanceForm(v => ({ ...v, niveau: e.target.value }))}><option value="1">Niveau 1 — rappel</option><option value="2">Niveau 2 — ferme</option><option value="3">Niveau 3 — dernier rappel</option></select></label>
              <label>Canal<select value={relanceForm.canal} onChange={e => setRelanceForm(v => ({ ...v, canal: e.target.value }))}><option value="email">E-mail</option><option value="telephone">Téléphone</option><option value="whatsapp">WhatsApp</option><option value="courrier">Courrier</option><option value="autre">Autre</option></select></label>
              <label>Date de relance<input type="date" required disabled={!!relanceEdition} value={relanceForm.date_relance} onChange={e => setRelanceForm(v => ({ ...v, date_relance: e.target.value }))} /></label>
              <label>Prochaine relance<input type="date" value={relanceForm.prochaine_relance} onChange={e => setRelanceForm(v => ({ ...v, prochaine_relance: e.target.value }))} /></label>
              <label>Date promise<input type="date" value={relanceForm.date_promesse_reglement} onChange={e => setRelanceForm(v => ({ ...v, date_promesse_reglement: e.target.value }))} /></label>
              <label>Montant promis (MAD)<input type="number" min="0.01" step="0.01" max={relanceEdition?.montant_promis != null ? Math.max(relanceFacture.reste_du ?? relanceEdition.montant_promis, relanceEdition.montant_promis) : relanceFacture.reste_du} value={relanceForm.montant_promis} onChange={e => setRelanceForm(v => ({ ...v, montant_promis: e.target.value }))} placeholder={relanceFacture.reste_du == null ? '' : formatMAD(relanceFacture.reste_du)} /></label>
            </div>
            <label className={styles.fullLabel}>Commentaire<textarea rows="3" value={relanceForm.commentaire} onChange={e => setRelanceForm(v => ({ ...v, commentaire: e.target.value }))} placeholder="Compte-rendu de l’échange, engagement du client…" /></label>
            <div className={styles.modalActions}>
              <button type="button" className={styles.btnSec} disabled={savingRelance} onClick={() => setRelanceFacture(null)}>Annuler</button>
              <button type="submit" className={styles.btnPrimary} disabled={savingRelance}>{savingRelance ? 'Enregistrement…' : relanceEdition ? 'Enregistrer' : 'Enregistrer la relance'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}

function VueEnsemble({ data }) {
  const vente = data.resume.vente
  const achat = data.resume.achat
  const pos = data.resume.position_nette
  return <>
    <div className={styles.grilleKPI}>
      <CarteKPI label="Créances clients" valeur={vente.reste} detail={vente.calcul_incomplet ? 'Nombre de factures à vérifier' : `${vente.nb_ouvertes} facture${vente.nb_ouvertes > 1 ? 's' : ''} ouverte${vente.nb_ouvertes > 1 ? 's' : ''}`} icone="ti-clock-dollar" />
      <CarteKPI label="Clients en retard" valeur={vente.en_retard} detail={vente.calcul_incomplet ? 'Nombre de factures à vérifier' : `${vente.nb_retard} facture${vente.nb_retard > 1 ? 's' : ''} échue${vente.nb_retard > 1 ? 's' : ''}`} icone="ti-alert-triangle" alerte={vente.en_retard > 0} />
      <CarteKPI label="Dettes fournisseurs" valeur={achat.reste} detail={achat.calcul_incomplet ? 'Nombre de factures à vérifier' : `${achat.nb_ouvertes} facture${achat.nb_ouvertes > 1 ? 's' : ''} à régler`} icone="ti-receipt" />
      <CarteKPI label="Taux de règlement commercial" valeur={vente.taux_reglement} detail="Pourcentage du TTC clients déjà imputé" icone="ti-percentage" format="pct" />
    </div>

    <div className={styles.position}>
      <div><div className={styles.positionLabel}>Position nette créances − dettes</div><div className={styles.cardSub}>Situation recalculée depuis les règlements, avoirs, acomptes et RAS.</div></div>
      <strong className={!montantConnu(pos) ? undefined : pos >= 0 ? styles.positif : styles.negatif}>{montantAffiche(pos)}{montantConnu(pos) && ' MAD'}</strong>
    </div>

    <div className={styles.balanceGrid}>
      <Anciennete titre="Créances clients" bloc={vente} />
      <Anciennete titre="Dettes fournisseurs" bloc={achat} />
    </div>

    <div className={styles.card}>
      <div className={styles.cardHeader}><div className={styles.cardTitle}>Effets et chèques en circulation</div>{data.effets.echus > 0 && <span className={styles.badgeRetard}>{data.effets.echus} arrivé{data.effets.echus > 1 ? 's' : ''} à échéance</span>}</div>
      <div className={styles.miniGrid}>
        <MiniStat label="En portefeuille" valeur={data.effets.portefeuille} />
        <MiniStat label="À l’encaissement" valeur={data.effets.encaissement} />
        <MiniStat label="À payer" valeur={data.effets.a_payer} />
      </div>
    </div>
  </>
}

function BarreFiltres({ type, setType, recherche, setRecherche, filtreStatut, setFiltreStatut, montantMin, setMontantMin, retardMin, setRetardMin, echeanceMax, setEcheanceMax }) {
  return <div className={styles.filtersWrap}>
    <div className={styles.filters}>
      <div className={styles.segmented}><button className={type === 'vente' ? styles.segmentActive : ''} onClick={() => setType('vente')}>Clients</button><button className={type === 'achat' ? styles.segmentActive : ''} onClick={() => setType('achat')}>Fournisseurs</button></div>
      <div className={styles.search}><i className="ti ti-search" /><input value={recherche} onChange={e => setRecherche(e.target.value)} placeholder="Facture ou tiers…" /></div>
      <select value={filtreStatut} onChange={e => setFiltreStatut(e.target.value)} className={styles.statusSelect}>
        <option value="ouvertes">Toutes les ouvertes</option><option value="retard">En retard</option><option value="a_echoir">À échoir</option><option value="partiel">Partiellement réglées</option><option value="toutes">Toutes</option>
      </select>
    </div>
    <div className={styles.advancedFilters}>
      <label>Reste dû ≥<input type="number" min="0" step="0.01" value={montantMin} onChange={e => setMontantMin(e.target.value)} placeholder="Montant" /></label>
      <label>Retard ≥<input type="number" min="0" step="1" value={retardMin} onChange={e => setRetardMin(e.target.value)} placeholder="Jours" /></label>
      <label>Échéance jusqu’au<input type="date" value={echeanceMax} onChange={e => setEcheanceMax(e.target.value)} /></label>
      {(montantMin || retardMin || echeanceMax) && <button className={styles.clearFilters} onClick={() => { setMontantMin(''); setRetardMin(''); setEcheanceMax('') }}>Effacer les filtres</button>}
    </div>
  </div>
}

function Anciennete({ titre, bloc }) {
  const total = bloc.reste
  return <div className={styles.card}>
    <div className={styles.cardHeader}><div><div className={styles.cardTitle}>{titre}</div><div className={styles.cardSub}>{bloc.calcul_incomplet ? 'Nombre de pièces à vérifier' : `${bloc.nb_ouvertes} pièce${bloc.nb_ouvertes > 1 ? 's' : ''} ouverte${bloc.nb_ouvertes > 1 ? 's' : ''}`}</div></div><strong>{montantAffiche(total)}{montantConnu(total) && ' MAD'}</strong></div>
    <div className={styles.cardBody}>{TRANCHES.map(t => { const v = bloc.tranches[t.cle]; const connu = montantConnu(total) && montantConnu(v); const pct = connu && total > 0 ? v / total * 100 : 0; return <div className={styles.ageRow} key={t.cle}><span>{t.label}</span><div className={styles.ageBar}>{connu && <i style={{ width: `${pct}%` }} />}</div><strong>{!montantConnu(v) ? 'À vérifier' : v > 0 ? formatMAD(v) : '—'}</strong></div> })}</div>
  </div>
}

function BalanceBloc({ titre, bloc }) {
  return <div className={styles.card}>
    <div className={styles.cardHeader}><div><div className={styles.cardTitle}>{titre}</div><div className={styles.cardSub}>{bloc.calcul_incomplet ? 'Ventilation par tiers à vérifier' : `${bloc.tiers.length} tiers avec solde ouvert`}</div></div><strong>{montantAffiche(bloc.reste)}{montantConnu(bloc.reste) && ' MAD'}</strong></div>
    <div className={styles.tableWrap}><table className={styles.balanceTable}><thead><tr><th>Tiers</th>{TRANCHES.map(t => <th key={t.cle} className={styles.right}>{t.label}</th>)}<th className={styles.right}>Total</th></tr></thead><tbody>
      {bloc.tiers.length === 0 ? <tr><td colSpan="7" className={styles.emptyRow}>{bloc.calcul_incomplet ? 'À vérifier : ventilation indisponible, consultez les diagnostics des factures.' : 'Aucun solde ouvert.'}</td></tr> : bloc.tiers.map(t => <tr key={`${t.tiers_id || ''}-${t.tiers}`}><td><strong>{t.tiers}</strong><div className={styles.muted}>{t.nb_factures} facture{t.nb_factures > 1 ? 's' : ''}{t.retard_max > 0 ? ` · retard max ${t.retard_max} j` : ''}</div></td>{TRANCHES.map(tr => <td key={tr.cle} className={styles.right}>{t.tranches[tr.cle] > 0 ? formatMAD(t.tranches[tr.cle]) : '—'}</td>)}<td className={`${styles.right} ${styles.reste}`}>{formatMAD(t.montant)}</td></tr>)}
    </tbody></table></div>
  </div>
}

function MiniStat({ label, valeur }) { return <div className={styles.miniStat}><span>{label}</span><strong>{formatMAD(valeur)} <small>MAD</small></strong></div> }
function canalLabel(v) { return ({ email: 'E-mail', telephone: 'Téléphone', whatsapp: 'WhatsApp', courrier: 'Courrier', autre: 'Autre' }[v] || v) }
