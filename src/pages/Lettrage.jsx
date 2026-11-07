import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { lettrageAPI } from '../services/api.js'
import { formatMAD, formatDate } from '../data/donnees.js'
import styles from './Lettrage.module.css'

const COMPTES_LETTRAGE = [
  { compte: '3421', label: 'Clients (3421)' },
  { compte: '4411', label: 'Fournisseurs (4411)' },
]

function normaliser(value) {
  return String(value || '').trim().toLocaleLowerCase('fr').replace(/\s+/g, ' ')
}

function tiersLigne(ligne) {
  return String(ligne?.tiers || ligne?.ligne_libelle || '').trim()
}

function auxiliaireIdentifiable(ligne) {
  if (!ligne) return false
  if (!['3421', '4411'].includes(ligne.compte)) return true
  return Boolean(normaliser(tiersLigne(ligne)))
}

function memeAuxiliaire(a, b) {
  if (!a || !b || a.compte !== b.compte) return false
  if (!['3421', '4411'].includes(a.compte)) return true
  const ta = normaliser(tiersLigne(a))
  const tb = normaliser(tiersLigne(b))
  return Boolean(ta && tb && ta === tb)
}

function correspondRecherche(ligne, recherche) {
  const q = normaliser(recherche)
  if (!q) return true
  return normaliser([
    ligne.date,
    ligne.journal,
    ligne.numero_ecriture,
    ligne.reference,
    ligne.compte,
    tiersLigne(ligne),
    ligne.libelle,
    ligne.debit,
    ligne.credit,
    ligne.code_lettrage,
  ].filter(Boolean).join(' ')).includes(q)
}

function BadgeCode({ code, partiel = false }) {
  if (!code) return <span className={styles.noCode}>—</span>
  const colors = ['#185FA5', '#3B6D11', '#854F0B', '#993556', '#534AB7']
  let h = 0
  for (const c of code) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  const col = colors[h % colors.length]
  return (
    <span
      className={styles.codeBadge}
      style={{ background: `${col}18`, color: col, borderColor: `${col}40` }}
    >
      {code}{partiel ? ' · partiel' : ''}
    </span>
  )
}

export default function Lettrage() {
  const { annee, exercice } = useExercice()
  const [compte, setCompte] = useState('3421')
  const [tiers, setTiers] = useState('')
  const [statut, setStatut] = useState('toutes')
  const [recherche, setRecherche] = useState('')
  const [selection, setSelection] = useState(new Set())
  const [lignes, setLignes] = useState([])
  const [chargement, setChargement] = useState(true)
  const [actionEnCours, setActionEnCours] = useState(false)
  const [msg, setMsg] = useState('')
  const [erreur, setErreur] = useState('')
  const versionChargement = useRef(0)
  const scopeChargement = useRef(null)
  const scope = `${annee}:${compte}`
  scopeChargement.current = scope

  const lectureSeule = exercice?.statut === 'cloture'

  async function charger() {
    // Une mutation terminée après un changement de filtre peut rappeler
    // cette fonction depuis une ancienne closure.
    if (scopeChargement.current !== scope) return
    const version = ++versionChargement.current
    const estCourant = () => version === versionChargement.current && scopeChargement.current === scope
    setChargement(true)
    setErreur('')
    try {
      const data = await lettrageAPI.lignes(annee, compte)
      if (estCourant()) setLignes(Array.isArray(data) ? data : [])
    } catch (e) {
      if (estCourant()) {
        setErreur(e.message)
        setLignes([])
      }
    } finally {
      if (estCourant()) setChargement(false)
    }
  }

  useEffect(() => {
    scopeChargement.current = scope
    setSelection(new Set())
    setTiers('')
    setStatut('toutes')
    setRecherche('')
    setMsg('')
    charger()
    return () => {
      versionChargement.current += 1
      scopeChargement.current = null
    }
  }, [annee, compte]) // eslint-disable-line react-hooks/exhaustive-deps

  const tiersUniques = useMemo(() => {
    const map = new Map()
    for (const ligne of lignes) {
      const valeur = tiersLigne(ligne)
      if (!valeur) continue
      const cle = normaliser(valeur)
      if (!map.has(cle)) map.set(cle, valeur)
    }
    return [...map.values()].sort((a, b) => a.localeCompare(b, 'fr', { sensitivity: 'base' }))
  }, [lignes])

  const lignesDuTiers = useMemo(() => {
    if (!tiers) return lignes
    const cle = normaliser(tiers)
    return lignes.filter(l => normaliser(tiersLigne(l)) === cle)
  }, [lignes, tiers])

  const lignesFiltrees = useMemo(() => lignesDuTiers.filter(l => {
    if (statut === 'lettrees' && !l.code_lettrage) return false
    if (statut === 'non_lettrees' && l.code_lettrage) return false
    return correspondRecherche(l, recherche)
  }), [lignesDuTiers, statut, recherche])

  const lignesSelectionnees = useMemo(
    () => lignes.filter(l => selection.has(l.ligne_id)),
    [lignes, selection]
  )

  const premiereSelection = lignesSelectionnees[0] || null

  const totauxSel = useMemo(() => {
    let debit = 0
    let credit = 0
    for (const l of lignesSelectionnees) {
      debit += Number(l.debit || 0)
      credit += Number(l.credit || 0)
    }
    return { debit, credit, ecart: Math.abs(debit - credit) }
  }, [lignesSelectionnees])

  const selectionEquilibree = selection.size >= 2 && totauxSel.ecart < 0.005

  const stats = useMemo(() => ({
    lettrees: lignesDuTiers.filter(l => l.code_lettrage).length,
    nonLettres: lignesDuTiers.filter(l => !l.code_lettrage).length,
    solde: lignesDuTiers.reduce((s, l) => s + Number(l.debit || 0) - Number(l.credit || 0), 0),
    debit: lignesDuTiers.reduce((s, l) => s + Number(l.debit || 0), 0),
    credit: lignesDuTiers.reduce((s, l) => s + Number(l.credit || 0), 0),
  }), [lignesDuTiers])

  function ligneCompatible(ligne) {
    if (!auxiliaireIdentifiable(ligne)) return false
    if (!premiereSelection || selection.has(ligne.ligne_id)) return true
    return memeAuxiliaire(premiereSelection, ligne)
  }

  function toggle(ligne) {
    if (lectureSeule || actionEnCours || ligne.code_lettrage) return
    if (!ligneCompatible(ligne)) {
      setErreur('Le lettrage doit concerner un seul compte et un seul client/fournisseur.')
      return
    }
    setErreur('')
    setMsg('')
    setSelection(prev => {
      const next = new Set(prev)
      next.has(ligne.ligne_id) ? next.delete(ligne.ligne_id) : next.add(ligne.ligne_id)
      return next
    })
  }

  // Codes partiels du même auxiliaire que la sélection, pouvant être complétés.
  const partielsCompatibles = useMemo(() => {
    if (!premiereSelection) return []
    const codes = new Set(lignesDuTiers
      .filter(l => l.lettrage_partiel && memeAuxiliaire(premiereSelection, l))
      .map(l => l.code_lettrage))
    return [...codes].sort()
  }, [lignesDuTiers, premiereSelection])

  async function lettrer({ partiel = false, code = null } = {}) {
    if (lectureSeule || actionEnCours) return
    if (!partiel && !code && !selectionEquilibree) return
    setActionEnCours(true)
    setMsg('')
    setErreur('')
    try {
      const r = await lettrageAPI.lettrer([...selection], code, partiel || Boolean(code))
      setMsg(`Code ${r.code} assigné à ${r.nb} ligne(s)${r.partiel ? ' — lettrage partiel, reste à compléter' : ''}.`)
      setSelection(new Set())
      await charger()
    } catch (e) {
      setErreur(e.message)
    } finally {
      setActionEnCours(false)
    }
  }

  async function delettrer(code) {
    if (lectureSeule || actionEnCours) return
    const concernees = lignes.filter(l => l.code_lettrage === code)
    const debit = concernees.reduce((s, l) => s + Number(l.debit || 0), 0)
    const credit = concernees.reduce((s, l) => s + Number(l.credit || 0), 0)
    if (!confirm(`Délettrer toutes les lignes portant le code ${code} ?

${concernees.length} ligne(s) — débit ${formatMAD(debit)} MAD / crédit ${formatMAD(credit)} MAD.
Les écritures restent inchangées ; le code reste réservé dans l'historique et ne sera pas réutilisé.`)) return
    setActionEnCours(true)
    setMsg('')
    setErreur('')
    try {
      const r = await lettrageAPI.delettrer(code)
      setMsg(`Code ${code} délettré sur ${r.nb} ligne(s).`)
      setSelection(new Set())
      await charger()
    } catch (e) {
      setErreur(e.message)
    } finally {
      setActionEnCours(false)
    }
  }

  async function lettrageAuto() {
    if (lectureSeule || actionEnCours) return
    const portee = tiers ? `le tiers « ${tiers} »` : `tous les tiers du compte ${compte}`
    if (!confirm(`Lancer le lettrage automatique par montant exact pour ${portee} ?`)) return
    setActionEnCours(true)
    setMsg('')
    setErreur('')
    try {
      const r = await lettrageAPI.auto(annee, compte, tiers)
      setMsg(r.nb > 0
        ? `${r.nb} correspondance(s) lettrée(s) automatiquement.`
        : 'Aucune correspondance exacte et sûre trouvée.')
      setSelection(new Set())
      await charger()
    } catch (e) {
      setErreur(e.message)
    } finally {
      setActionEnCours(false)
    }
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1 className={styles.pageTitle}>Lettrage</h1>
          <p className={styles.subtitle}>Correspondance des mouvements sur comptes clients et fournisseurs</p>
        </div>
      </div>

      <div className={styles.content}>
        {lectureSeule && (
          <div className={styles.readOnlyBanner}>
            <i className="ti ti-lock" /> Exercice {annee} clôturé : le lettrage est consultable mais ne peut plus être modifié.
          </div>
        )}
        {erreur && <div className={styles.errorBanner}>{erreur}</div>}
        {msg && <div className={styles.successBanner}>{msg}</div>}

        <div className={styles.card}>
          <div className={styles.filtersGrid}>
            <div>
              <label className={styles.label}>Compte</label>
              <select className={styles.input} value={compte} onChange={e => setCompte(e.target.value)}>
                {COMPTES_LETTRAGE.map(c => <option key={c.compte} value={c.compte}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.label}>Tiers</label>
              <select
                className={styles.input}
                value={tiers}
                onChange={e => { setTiers(e.target.value); setSelection(new Set()) }}
              >
                <option value="">— Tous les tiers —</option>
                {tiersUniques.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.label}>État</label>
              <select className={styles.input} value={statut} onChange={e => setStatut(e.target.value)}>
                <option value="toutes">Toutes les lignes</option>
                <option value="non_lettrees">Non lettrées</option>
                <option value="lettrees">Lettrées</option>
              </select>
            </div>
            <div>
              <label className={styles.label}>Recherche</label>
              <div className={styles.searchWrap}>
                <i className="ti ti-search" />
                <input
                  className={styles.searchInput}
                  value={recherche}
                  onChange={e => setRecherche(e.target.value)}
                  placeholder="N°, référence, libellé, montant…"
                />
              </div>
            </div>
          </div>

          <div className={styles.statsBar}>
            <span className={`${styles.statPill} ${styles.statOk}`}>{stats.lettrees} lettrée(s)</span>
            <span className={`${styles.statPill} ${styles.statPending}`}>{stats.nonLettres} non lettrée(s)</span>
            <span className={styles.statNeutral}>Débit : <strong>{formatMAD(stats.debit)} MAD</strong></span>
            <span className={styles.statNeutral}>Crédit : <strong>{formatMAD(stats.credit)} MAD</strong></span>
            <span className={styles.statNeutral}>Solde : <strong>{formatMAD(stats.solde)} MAD</strong></span>
          </div>
        </div>

        <div className={styles.actionsBar}>
          <span className={styles.resultCount}>{lignesFiltrees.length} / {lignesDuTiers.length} ligne(s) affichée(s)</span>
          <div className={styles.actionButtons}>
            <button
              className={styles.secondaryButton}
              onClick={lettrageAuto}
              disabled={lectureSeule || actionEnCours || chargement}
              title="Associe uniquement les montants exactement opposés d'un même auxiliaire, en privilégiant les dates proches"
            >
              <i className="ti ti-wand" /> Lettrage auto exact
            </button>
            <button
              className={styles.primaryButton}
              onClick={() => lettrer()}
              disabled={lectureSeule || actionEnCours || !selectionEquilibree}
            >
              <i className="ti ti-link" />
              {selection.size < 2
                ? 'Sélectionner au moins 2 lignes'
                : selectionEquilibree
                  ? `Lettrer ${selection.size} lignes`
                  : `Écart ${formatMAD(totauxSel.ecart)} MAD`}
            </button>
          </div>
        </div>

        {selection.size > 0 && (
          <div className={styles.selectionBar}>
            <span><strong>{selection.size}</strong> ligne(s) sélectionnée(s)</span>
            <span>Débit : <strong>{formatMAD(totauxSel.debit)} MAD</strong></span>
            <span>Crédit : <strong>{formatMAD(totauxSel.credit)} MAD</strong></span>
            <span className={selectionEquilibree ? styles.selectionOk : styles.selectionWarn}>
              {selectionEquilibree ? 'Sélection équilibrée' : `Écart : ${formatMAD(totauxSel.ecart)} MAD`}
            </span>
            {!selectionEquilibree && !lectureSeule && (
              <>
                {selection.size >= 2 && totauxSel.debit > 0 && totauxSel.credit > 0 && (
                  <button className={styles.secondaryButton} disabled={actionEnCours}
                    onClick={() => lettrer({ partiel: true })}
                    title="Règlement partiel : le code restera ouvert jusqu'à son équilibre">
                    <i className="ti ti-link" /> Lettrage partiel
                  </button>
                )}
                {partielsCompatibles.map(code => (
                  <button key={code} className={styles.secondaryButton} disabled={actionEnCours}
                    onClick={() => lettrer({ code })} title={`Ajouter la sélection au lettrage partiel ${code}`}>
                    <i className="ti ti-link-plus" /> Compléter {code}
                  </button>
                ))}
              </>
            )}
            <button className={styles.clearButton} onClick={() => setSelection(new Set())}>Annuler la sélection</button>
          </div>
        )}

        <div className={`${styles.card} ${styles.cardMain}`}>
          {chargement ? (
            <div className={styles.vide}>Chargement…</div>
          ) : lignesFiltrees.length === 0 ? (
            <div className={styles.vide}>
              <i className="ti ti-link-off" />
              <span>Aucune ligne comptable ne correspond aux filtres.</span>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th className={styles.checkCol} />
                    <th>Date</th>
                    <th>Journal</th>
                    <th>N° écriture</th>
                    <th>Référence</th>
                    <th>Compte</th>
                    <th>Tiers</th>
                    <th>Libellé écriture</th>
                    <th className={styles.amount}>Débit</th>
                    <th className={styles.amount}>Crédit</th>
                    <th>Code</th>
                    <th>Date lettrage</th>
                    <th className={styles.actionCol}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {lignesFiltrees.map((l) => {
                    const sel = selection.has(l.ligne_id)
                    const lettree = Boolean(l.code_lettrage)
                    const compatible = ligneCompatible(l)
                    const disabled = lectureSeule || actionEnCours || lettree || !compatible
                    return (
                      <tr
                        key={l.ligne_id}
                        className={`${sel ? styles.rowSelected : ''} ${lettree ? styles.rowMatched : ''} ${!compatible ? styles.rowIncompatible : ''}`}
                        onClick={() => !disabled && toggle(l)}
                        title={!compatible ? (auxiliaireIdentifiable(l) ? 'Sélection incompatible : choisissez le même compte et le même tiers.' : 'Tiers non identifié sur ce compte collectif.') : undefined}
                      >
                        <td className={styles.checkCol}>
                          {lettree ? (
                            <i className="ti ti-circle-check" title="Ligne lettrée" />
                          ) : (
                            <input
                              type="checkbox"
                              readOnly
                              checked={sel}
                              disabled={disabled}
                              aria-label={`Sélectionner la ligne ${l.numero_ecriture || l.ligne_id}`}
                            />
                          )}
                        </td>
                        <td className={styles.nowrap}>{formatDate(l.date)}</td>
                        <td className={styles.nowrap}>{l.journal}</td>
                        <td className={styles.nowrap}>{l.numero_ecriture || '—'}</td>
                        <td className={styles.nowrap}>{l.reference || '—'}</td>
                        <td className={styles.nowrap}>{l.compte}</td>
                        <td className={styles.tiersCell}>{tiersLigne(l) || <span className={styles.warningText}>Tiers non identifié</span>}</td>
                        <td className={styles.libelleCell}>
                          <div>{l.libelle || '—'}</div>
                          {l.ligne_libelle && l.ligne_libelle !== l.libelle && (
                            <div className={styles.secondaryText}>{l.ligne_libelle}</div>
                          )}
                        </td>
                        <td className={`${styles.amount} ${styles.debit}`}>{Number(l.debit) > 0 ? formatMAD(l.debit) : '—'}</td>
                        <td className={`${styles.amount} ${styles.credit}`}>{Number(l.credit) > 0 ? formatMAD(l.credit) : '—'}</td>
                        <td><BadgeCode code={l.code_lettrage} partiel={l.lettrage_partiel} /></td>
                        <td className={styles.nowrap}>{l.date_lettrage ? formatDate(l.date_lettrage) : '—'}</td>
                        <td className={styles.actionCol}>
                          {lettree && (
                            <button
                              className={styles.iconButton}
                              onClick={e => { e.stopPropagation(); delettrer(l.code_lettrage) }}
                              title={lectureSeule ? 'Exercice clôturé' : `Délettrer le code ${l.code_lettrage}`}
                              disabled={lectureSeule || actionEnCours}
                            ><i className="ti ti-unlink" /><span className="libelle-action" aria-hidden="true">Délettrer</span></button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
