import { useEffect, useMemo, useState, useRef } from 'react'
import { exporterCSV } from '../services/exportCSV.js'
import { comptabiliteAPI, getToken } from '../services/api.js'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { trouverCompteLecture } from '../data/planComptableCache.js'
import { formatMAD, formatDate } from '../data/donnees.js'
import styles from './GrandLivre.module.css'

function montantSigne(valeur) {
  const n = Number(valeur || 0)
  return `${n < 0 ? '-' : ''}${formatMAD(Math.abs(n))}`
}

export default function GrandLivre() {
  const { annee, exercice } = useExercice()
  const { societe } = useModules()
  const [recherche, setRecherche] = useState('')
  const [compteOuvert, setCompteOuvert] = useState(null)
  const [dateDebut, setDateDebut] = useState(() => exercice?.date_debut || `${annee}-01-01`)
  const [dateFin, setDateFin] = useState(() => exercice?.date_fin || `${annee}-12-31`)
  const [rapport, setRapport] = useState({ comptes: [], nb_ecritures: 0 })
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const periodeContexte = useRef({ annee, societeId: societe?.id ?? null, saisie: false })

  useEffect(() => {
    const precedent = periodeContexte.current
    const societeId = societe?.id ?? null
    const changement = precedent.annee !== annee
      || (precedent.societeId !== null && societeId !== null && precedent.societeId !== societeId)
    const saisie = changement ? false : precedent.saisie
    periodeContexte.current = { annee, societeId: societeId ?? precedent.societeId, saisie }
    // Une hydratation tardive du même exercice ne remplace pas le filtre saisi.
    if (!saisie) {
      setDateDebut(exercice?.date_debut || `${annee}-01-01`)
      setDateFin(exercice?.date_fin || `${annee}-12-31`)
    }
  }, [annee, societe?.id, exercice?.date_debut, exercice?.date_fin])

  useEffect(() => {
    let annule = false
    if (dateDebut && dateFin && dateDebut > dateFin) {
      setChargement(false)
      setErreur('La date de début doit être antérieure ou égale à la date de fin.')
      setRapport({ comptes: [], nb_ecritures: 0 })
      return () => { annule = true }
    }

    setChargement(true); setErreur('')
    comptabiliteAPI.grandLivre(annee, { dateFrom: dateDebut, dateTo: dateFin })
      .then(data => { if (!annule) setRapport(data || { comptes: [], nb_ecritures: 0 }) })
      .catch(e => { if (!annule) { setErreur(e.message); setRapport({ comptes: [], nb_ecritures: 0 }) } })
      .finally(() => { if (!annule) setChargement(false) })
    return () => { annule = true }
  }, [annee, societe?.id, dateDebut, dateFin])

  const comptes = useMemo(() => (rapport.comptes || []).map(c => ({
    compte: c.compte,
    totalDebit: Number(c.total_debit || 0),
    totalCredit: Number(c.total_credit || 0),
    soldeInitial: Number(c.solde_initial || 0),
    solde: Number(c.solde_final ?? c.solde ?? 0),
    info: trouverCompteLecture(c.compte, getToken()),
    mouvements: (c.mouvements || []).map(m => ({
      ...m,
      ligneLibelle: m.ligne_libelle,
      soldeCumule: Number(m.solde_cumule || 0),
    })),
  })), [rapport])

  const soldesComptes = useMemo(() => comptes.filter(c => {
    if (!recherche.trim()) return true
    const q = recherche.trim().toLowerCase()
    if (c.compte.toLowerCase().includes(q) || (c.info?.libelle || '').toLowerCase().includes(q)) return true
    return c.mouvements.some(m => [m.tiers, m.libelle, m.ligneLibelle, m.reference, m.numero_ecriture, m.journal]
      .some(v => String(v || '').toLowerCase().includes(q)))
  }), [comptes, recherche])

  const compteDetail = compteOuvert ? comptes.find(c => c.compte === compteOuvert) : null

  const exporter = () => {
    const plat = soldesComptes.flatMap(c => c.mouvements.map(m => ({
      compte: c.compte,
      libelleCompte: c.info?.libelle || '',
      soldeInitial: c.soldeInitial,
      ...m,
    })))
    exporterCSV('grand_livre', [
      { label: 'Compte', get: l => l.compte },
      { label: 'Libellé compte', get: l => l.libelleCompte },
      { label: 'Solde initial', get: l => l.soldeInitial, type: 'nombre' },
      { label: 'Date', get: l => l.date },
      { label: 'Journal', get: l => l.journal },
      { label: 'N° écriture', get: l => l.numero_ecriture },
      { label: 'Référence', get: l => l.reference || '' },
      { label: 'Tiers', get: l => l.tiers || '' },
      { label: 'Libellé', get: l => l.ligneLibelle || l.libelle },
      { label: 'Débit', get: l => l.debit, type: 'nombre' },
      { label: 'Crédit', get: l => l.credit, type: 'nombre' },
      { label: 'Solde cumulé', get: l => l.soldeCumule, type: 'nombre' },
      { label: 'Lettrage', get: l => l.code_lettrage || '' },
    ], plat)
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Grand livre</h1>
          <div className={styles.subtitle}>Écritures définitives · soldes d'ouverture et cumulés</div>
        </div>
        <div className={styles.topbarRight}>
          <div className={styles.dateFilters}>
            <label>Du</label>
            <input type="date" value={dateDebut} onChange={e => { periodeContexte.current.saisie = true; setDateDebut(e.target.value) }} />
            <label>Au</label>
            <input type="date" value={dateFin} onChange={e => { periodeContexte.current.saisie = true; setDateFin(e.target.value) }} />
          </div>
          <button className={styles.btnSec} onClick={exporter} disabled={chargement || Boolean(erreur) || soldesComptes.length === 0}>
            <i className="ti ti-download" aria-hidden="true" /> Exporter CSV
          </button>
        </div>
      </div>

      <div className={styles.content}>
        {erreur && <div className={styles.errorBox} role="alert">{erreur}</div>}
        <div className={styles.recherche}>
          <i className="ti ti-search" aria-hidden="true" />
          <input type="text" placeholder="Compte, libellé, tiers, référence, n° écriture…"
            value={recherche} onChange={e => setRecherche(e.target.value)}
            className={styles.inputRecherche} />
          {recherche && <button className={styles.clearBtn} onClick={() => setRecherche('')}><i className="ti ti-x" aria-hidden="true" /></button>}
        </div>

        {chargement ? (
          <div className={styles.loading}><i className="ti ti-loader-2" /> Chargement du grand livre définitif…</div>
        ) : erreur ? null : (
          <div className={compteDetail ? styles.twoCols : styles.fullWidth}>
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>{soldesComptes.length} compte{soldesComptes.length !== 1 ? 's' : ''} mouvementé{soldesComptes.length !== 1 ? 's' : ''} · {rapport.nb_ecritures || 0} écriture(s) définitive(s)</span>
              </div>
              <div className={styles.tableWrapper}>
                <table className={`${styles.table} ${styles.tableComptes}`}>
                  <thead>
                    <tr>
                      <th>Compte</th><th>Libellé</th>
                      <th style={{ textAlign: 'right' }}>Solde initial</th>
                      <th style={{ textAlign: 'right' }}>Mvt débit</th>
                      <th style={{ textAlign: 'right' }}>Mvt crédit</th>
                      <th style={{ textAlign: 'right' }}>Solde final</th>
                      <th style={{ textAlign: 'right' }}>Mvt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {soldesComptes.map(c => (
                      <tr key={c.compte}
                        className={compteOuvert === c.compte ? styles.rowSelected : ''}
                        onClick={() => setCompteOuvert(compteOuvert === c.compte ? null : c.compte)}>
                        <td><span className={styles.cptBadge}>{c.compte}</span></td>
                        <td>{c.info?.libelle || <span style={{ color: 'var(--text-tertiary)' }}>Compte non référencé</span>}</td>
                        <td className={styles.numberCell}>{montantSigne(c.soldeInitial)}</td>
                        <td className={styles.numberCell} style={{ color: 'var(--green)' }}>{formatMAD(c.totalDebit)}</td>
                        <td className={styles.numberCell} style={{ color: 'var(--red)' }}>{formatMAD(c.totalCredit)}</td>
                        <td className={styles.numberCell} style={{ fontWeight: 600, color: c.solde >= 0 ? 'var(--green)' : 'var(--red)' }}>{montantSigne(c.solde)}</td>
                        <td className={styles.numberCell} style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>{c.mouvements.length}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {soldesComptes.length === 0 && (
                  <div className={styles.vide}><i className="ti ti-book-off" aria-hidden="true" /><span>Aucun mouvement définitif pour cette période</span></div>
                )}
              </div>
            </div>

            {compteDetail && (
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <div><span className={styles.cardTitle}><span className={styles.cptBadge}>{compteDetail.compte}</span>{compteDetail.info?.libelle || 'Compte non référencé'}</span></div>
                  <button className={styles.btnIcone} onClick={() => setCompteOuvert(null)} aria-label="Fermer le détail"><i className="ti ti-x" aria-hidden="true" /></button>
                </div>

                <div className={styles.soldeRecap}>
                  <div className={styles.soldeItem}><span className={styles.soldeLabel}>Solde initial</span><span className={styles.soldeFinal}>{montantSigne(compteDetail.soldeInitial)} MAD</span></div>
                  <div className={styles.soldeSep} />
                  <div className={styles.soldeItem}><span className={styles.soldeLabel}>Mvt débit</span><span className={styles.soldeDebit}>{formatMAD(compteDetail.totalDebit)} MAD</span></div>
                  <div className={styles.soldeSep} />
                  <div className={styles.soldeItem}><span className={styles.soldeLabel}>Mvt crédit</span><span className={styles.soldeCredit}>{formatMAD(compteDetail.totalCredit)} MAD</span></div>
                  <div className={styles.soldeSep} />
                  <div className={styles.soldeItem}><span className={styles.soldeLabel}>Solde final</span><span className={styles.soldeFinal} style={{ color: compteDetail.solde >= 0 ? 'var(--green)' : 'var(--red)' }}>{montantSigne(compteDetail.solde)} MAD</span></div>
                </div>

                <div className={styles.tableWrapper}>
                  <table className={`${styles.table} ${styles.tableDetail}`}>
                    <thead><tr>
                      <th>Date</th><th>Journal</th><th>N° écriture</th><th>Référence</th><th>Tiers</th><th>Libellé</th>
                      <th style={{ textAlign: 'right' }}>Débit</th><th style={{ textAlign: 'right' }}>Crédit</th><th style={{ textAlign: 'right' }}>Solde cumulé</th><th>Lettrage</th>
                    </tr></thead>
                    <tbody>
                      {compteDetail.mouvements.map(m => (
                        <tr key={m.ligne_id}>
                          <td className={styles.tdDate}>{formatDate(m.date)}</td>
                          <td><span className={styles.journalBadge}>{m.journal || '—'}</span></td>
                          <td className={styles.mono}>{m.numero_ecriture || '—'}</td>
                          <td>{m.reference || '—'}</td>
                          <td>
                            {m.tiers || '—'}
                            {m.tiers && m.tiers_identifie === false && <span className={styles.badgeWarning}>Non identifié</span>}
                          </td>
                          <td><div>{m.libelle}</div>{m.ligneLibelle && m.ligneLibelle !== m.libelle && <div className={styles.secondaryText}>{m.ligneLibelle}</div>}</td>
                          <td className={styles.numberCell} style={{ color: 'var(--green)', fontWeight: m.debit > 0 ? 500 : 400 }}>{m.debit > 0 ? formatMAD(m.debit) : '—'}</td>
                          <td className={styles.numberCell} style={{ color: 'var(--red)', fontWeight: m.credit > 0 ? 500 : 400 }}>{m.credit > 0 ? formatMAD(m.credit) : '—'}</td>
                          <td className={styles.numberCell} style={{ fontWeight: 600, color: m.soldeCumule >= 0 ? 'var(--green)' : 'var(--red)' }}>{montantSigne(m.soldeCumule)}</td>
                          <td className={styles.mono}>{m.code_lettrage || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
