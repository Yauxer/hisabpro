import { Fragment, useEffect, useMemo, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { etatsAPI, peutEcrire } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from './Etic.module.css'

const GROUPES = {
  A: 'A — Principes et méthodes comptables',
  B: 'B — Compléments au Bilan et au CPC',
  C: 'C — Autres informations complémentaires',
}

const LABELS_AUTO = {
  compte: 'Compte', intitule: 'Intitulé', montant: 'Montant', debut: 'Début exercice',
  augmentations: 'Augmentations', diminutions: 'Diminutions', fin_module: 'Fin — suivi',
  solde_comptable_fin: 'Fin — comptabilité', ecart: 'Écart', cumul_debut: 'Cumul début',
  dotations: 'Dotations', amort_sorties: 'Amort. sur sorties', cumul_fin: 'Cumul fin',
  date: 'Date', designation: 'Désignation', type: 'Type', valeur_entree: 'Valeur d’entrée',
  vna: 'VNA', prix_cession: 'Prix de cession', plus_moins_value: '+ / - value',
  reprises_utilisations: 'Reprises / utilisations', fin: 'Fin exercice', nature: 'Nature',
  rubrique: 'Rubrique', solde_debut: 'Solde début', operations: 'Opérations comptables',
  declarations: 'Déclarations TVA', solde_fin: 'Solde fin', exercice: 'Exercice',
  situation_nette: 'Situation nette', chiffre_affaires_ht: 'CA HT', resultat_avant_impots: 'Résultat avant impôts',
  impots_resultats: 'Impôts sur résultats', resultat_net: 'Résultat net', salaires_bruts: 'Salaires bruts',
  effectif_indicatif: 'Effectif indicatif',
}

const LABELS_VENTILATION = {
  plus_un_an: "+ d’un an",
  moins_un_an: "- d’un an",
  devises: 'Devises',
  etat_organismes_publics: 'État / organismes publics',
  entreprises_liees: 'Entreprises liées',
  effets: 'Représenté par effets',
}

function estMontant(cle) {
  return ['montant','debut','augmentations','diminutions','fin_module','solde_comptable_fin','ecart',
    'cumul_debut','dotations','amort_sorties','cumul_fin','valeur_entree','vna','prix_cession',
    'plus_moins_value','reprises_utilisations','fin','solde_debut','operations','declarations','solde_fin',
    'situation_nette','chiffre_affaires_ht','resultat_avant_impots','impots_resultats','resultat_net','salaires_bruts'].includes(cle)
}

function afficherValeur(cle, valeur) {
  if (valeur === null || valeur === undefined || valeur === '') return '—'
  if (estMontant(cle) && Number.isFinite(Number(valeur))) {
    const n = Number(valeur)
    return n < 0 ? `(${formatMAD(Math.abs(n))})` : formatMAD(n)
  }
  return String(valeur)
}

function BadgeMode({ mode }) {
  const label = mode === 'auto' ? 'Automatique' : mode === 'assiste' ? 'À confirmer' : 'À renseigner'
  return <span className={`${styles.modeBadge} ${styles[`mode_${mode}`]}`}>{label}</span>
}

function TableauAuto({ data }) {
  const colonnes = data?.colonnes || []
  const lignes = data?.lignes || []
  if (!lignes.length) return <div className={styles.vide}>Aucune donnée comptable à présenter pour cette section.</div>
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead><tr>{colonnes.map(c => <th key={c}>{LABELS_AUTO[c] || c}</th>)}</tr></thead>
        <tbody>
          {lignes.map((ligne, i) => (
            <tr key={i}>{colonnes.map(c => <td key={c} className={estMontant(c) ? styles.num : ''}>{afficherValeur(c, ligne[c])}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


function TableauVentilation({ section, contenu, setContenu, ecriture }) {
  const lignes = section?.automatique?.lignes || []
  const code = section.code
  const libEchues = code === 'B6' ? 'Échues et non recouvrées' : 'Échues et non payées'

  function valeur(compte, cle) {
    const saved = contenu?.ventilations?.[compte]?.[cle]
    if (saved !== undefined && saved !== null && saved !== '') return saved
    const ligne = (section.ventilation || []).find(x => String(x.compte) === String(compte))
    if (ligne?.[cle] !== undefined && ligne?.[cle] !== null) return ligne[cle]
    if (contenu?.autres_analyses_neant && ['devises','etat_organismes_publics','entreprises_liees','effets'].includes(cle)) return 0
    return ''
  }

  function maj(compte, cle, value) {
    setContenu(prev => ({
      ...prev,
      ventilations: {
        ...(prev.ventilations || {}),
        [compte]: { ...((prev.ventilations || {})[compte] || {}), [cle]: value },
      },
    }))
  }

  return (
    <div className={styles.ventilationBlock}>
      <div className={styles.ventilationHint}>
        Les échéances des factures sont préremplies lorsqu’HisabPro peut les rapprocher exactement du solde comptable à la clôture.
        Les autres analyses ne sont jamais supposées nulles automatiquement ; les montants clairement portés sur des comptes État sont préremplis et restent modifiables.
      </div>
      <label className={styles.confirmCheck}>
        <input type="checkbox" checked={Boolean(contenu.autres_analyses_neant)} disabled={!ecriture}
          onChange={e => setContenu(prev => ({ ...prev, autres_analyses_neant: e.target.checked }))} />
        Autres analyses : je confirme qu’aucun montant en devises, entreprises liées ou effets, ni aucun autre montant envers l’État / organismes publics, n’est à ajouter aux montants préremplis.
      </label>
      <div className={styles.ventilationWrap}>
        <table className={styles.ventilationTable}>
          <thead>
            <tr>
              <th rowSpan="2">Compte</th><th rowSpan="2">Intitulé</th><th rowSpan="2" className={styles.num}>Total</th>
              <th colSpan="3">Analyse par échéance</th><th colSpan="4">Autres analyses</th>
            </tr>
            <tr>
              <th>+ d’un an</th><th>- d’un an</th><th>{libEchues}</th>
              <th>Devises</th><th>État / organismes publics</th><th>Entreprises liées</th><th>Effets</th>
            </tr>
          </thead>
          <tbody>
            {lignes.map(ligne => {
              const compte = String(ligne.compte)
              return (
                <Fragment key={compte}>
                  <tr>
                    <td className={styles.compteCell}>{compte}</td>
                    <td className={styles.intituleCell}>{ligne.intitule}</td>
                    <td className={styles.num}>{afficherValeur('montant', ligne.montant)}</td>
                    {['plus_un_an','moins_un_an','echues','devises','etat_organismes_publics','entreprises_liees','effets'].map(cle => (
                      <td key={cle}>
                        <input className={styles.ventilationInput} type="number" min="0" step="0.01" disabled={!ecriture}
                          aria-label={`${compte} ${LABELS_VENTILATION[cle] || (cle === 'echues' ? libEchues : cle)}`}
                          value={valeur(compte, cle)} onChange={e => maj(compte, cle, e.target.value)} />
                      </td>
                    ))}
                  </tr>
                  {ligne.echeance_auto_total !== undefined && ligne.echeance_auto_total !== null && (!ligne.echeance_auto || ligne.echeance_auto_anomalies_sources?.length > 0) && (
                    <tr>
                      <td colSpan="10">
                        <div className={styles.ventilationHint}>
                          {ligne.echeance_auto_partiel ? 'Préremplissage partiel appliqué pour' : 'Préremplissage non appliqué pour'} {compte} : les factures/échéanciers trouvés
                          ({ligne.echeance_auto_nb_factures || 0} facture(s)
                          {ligne.echeance_auto_nb_factures_historiques > 0 ? `, dont ${ligne.echeance_auto_nb_factures_historiques} retrouvée(s) via une écriture historique exacte` : ''})
                          totalisent {afficherValeur('montant', ligne.echeance_auto_total)} MAD,
                          contre {afficherValeur('montant', ligne.montant)} MAD en comptabilité
                          (écart {afficherValeur('montant', ligne.echeance_auto_ecart)} MAD).
                          {ligne.echeance_auto_non_qualifie > 0 && (
                            <> <strong>Échéance non justifiée : {afficherValeur('montant', ligne.echeance_auto_non_qualifie)} MAD restent à qualifier depuis les pièces sources.</strong></>
                          )}
                          {ligne.echeance_auto_partiel && ligne.echeance_auto_reliquat !== undefined && (
                            <> <strong>Reste à ventiler : {afficherValeur('montant', ligne.echeance_auto_reliquat)} MAD.</strong></>
                          )}
                          {ligne.echeance_auto_diagnostic && (
                            <> Répartition source certaine : + d’un an {afficherValeur('montant', ligne.echeance_auto_diagnostic.plus_un_an)} MAD,
                            - d’un an {afficherValeur('montant', ligne.echeance_auto_diagnostic.moins_un_an)} MAD,
                            échues {afficherValeur('montant', ligne.echeance_auto_diagnostic.echues)} MAD.</>
                          )}
                        </div>
                        {ligne.echeance_auto_anomalies_sources?.length > 0 && (
                          <details className={styles.ventilationHint}>
                            <summary>Sources à vérifier avant de qualifier les échéances ({ligne.echeance_auto_anomalies_sources.length})</summary>
                            {ligne.echeance_auto_anomalies_sources.map(a => (
                              <div key={a.facture_id}>
                                {a.numero || `Facture ${a.facture_id}`} · reste source {afficherValeur('montant', a.reste_du)} MAD · {(a.motifs || []).join(' ')}
                              </div>
                            ))}
                          </details>
                        )}
                        {ligne.echeance_auto_compta_diagnostic && (
                          <div className={styles.ventilationHint}>
                            <strong>Décomposition comptable du solde {compte} :</strong>{' '}
                            {(ligne.echeance_auto_compta_diagnostic.sources || []).map((s, i) => (
                              <Fragment key={`${compte}-${s.source}`}>
                                {i > 0 ? ' · ' : ''}{s.source} : {afficherValeur('montant', s.montant)} MAD ({s.nb_lignes} ligne(s))
                              </Fragment>
                            ))}
                            <details>
                              <summary>Voir les mouvements comptables du compte {compte}</summary>
                              {(ligne.echeance_auto_compta_diagnostic.mouvements || []).map((m, i) => (
                                <div key={`${compte}-mvt-${i}`}>
                                  {m.date || '—'} · {m.numero || m.journal || 'écriture'} · {m.source} · {m.reference || 'sans réf.'} · impact {afficherValeur('montant', m.impact_solde)} MAD
                                  {m.libelle ? ` · ${m.libelle}` : ''}
                                </div>
                              ))}
                            </details>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                  {ligne.echeance_auto_sources_hors_solde?.length > 0 && (
                    <tr>
                      <td colSpan="10">
                        <details className={styles.ventilationHint}>
                          <summary>Sources rattachées à un compte absent des soldes affichés : à vérifier</summary>
                          {ligne.echeance_auto_sources_hors_solde.map(source => (
                            <div key={source.compte}>
                              Compte source {source.compte} · {afficherValeur('montant', source.total_source)} MAD · aucune reclassification automatique.
                              {(source.anomalies_sources || []).map(a => (
                                <div key={a.facture_id}>{a.numero || `Facture ${a.facture_id}`} · {(a.motifs || []).join(' ')}</div>
                              ))}
                            </div>
                          ))}
                        </details>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
      {section.erreurs_ventilation?.length > 0 && contenu.confirme && (
        <div className={styles.errorList}>{section.erreurs_ventilation.join(' ')}</div>
      )}
    </div>
  )
}

function SectionETIC({ section, exercice, onSaved, verrouillee = false }) {
  const initial = section.contenu || {}
  const [contenu, setContenu] = useState(initial)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const ecriture = peutEcrire() && !verrouillee

  useEffect(() => { setContenu(section.contenu || {}) }, [section.code, section.contenu])

  function maj(cle, value) { setContenu(prev => ({ ...prev, [cle]: value })) }

  function ajouterLigne() {
    const vide = {}
    ;(section.colonnes_saisie || []).forEach(c => { vide[c.cle] = c.type === 'number' ? '' : '' })
    maj('lignes', [...(contenu.lignes || []), vide])
  }

  function majLigne(index, cle, value) {
    const lignes = [...(contenu.lignes || [])]
    lignes[index] = { ...lignes[index], [cle]: value }
    maj('lignes', lignes)
  }

  function supprimerLigne(index) {
    maj('lignes', (contenu.lignes || []).filter((_, i) => i !== index))
  }

  async function sauver() {
    setSaving(true); setMessage('')
    try {
      await etatsAPI.enregistrerSectionETIC(exercice, section.code, contenu)
      setMessage('Enregistré')
      await onSaved()
    } catch (e) { setMessage(e.message) }
    finally { setSaving(false) }
  }

  async function reinitialiser() {
    if (!window.confirm(`Réinitialiser les compléments de la section ${section.code} ?`)) return
    setSaving(true); setMessage('')
    try {
      await etatsAPI.reinitialiserSectionETIC(exercice, section.code)
      setContenu({}); await onSaved()
    } catch (e) { setMessage(e.message) }
    finally { setSaving(false) }
  }

  const auto = section.automatique || {}
  return (
    <section className={styles.sectionCard} id={`etic-${section.code}`}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleWrap}>
          <span className={styles.code}>{section.code}</span>
          <div><h3>{section.titre}</h3><BadgeMode mode={section.mode} /></div>
        </div>
        <span className={`${styles.status} ${section.complete ? styles.statusOk : styles.statusTodo}`}>
          <i className={`ti ${section.complete ? 'ti-circle-check' : 'ti-clock'}`} aria-hidden="true" />
          {section.complete ? 'Complet' : 'À compléter'}
        </span>
      </div>

      {section.type_saisie !== 'ventilation' && auto?.colonnes?.length > 0 && <TableauAuto data={auto} />}
      {auto?.avertissement && <div className={styles.warning}><i className="ti ti-alert-triangle" />{auto.avertissement}</div>}
      {auto?.source && <div className={styles.sourceLine}>Source : {auto.source}</div>}

      <div className={styles.manualZone}>
        {section.mode === 'manuel' && (
          <label className={styles.neantCheck}>
            <input type="checkbox" checked={Boolean(contenu.neant)} disabled={!ecriture}
              onChange={e => maj('neant', e.target.checked)} />
            Néant pour l'exercice {exercice}
          </label>
        )}

        {section.type_saisie === 'texte' && !contenu.neant && (
          <textarea className={styles.textarea} rows={5} value={contenu.texte || ''} disabled={!ecriture}
            placeholder={section.code === 'A1'
              ? "Décrivez les méthodes spécifiques : évaluation à l'entrée, amortissements, provisions, stocks, écarts de conversion…"
              : 'Informations complémentaires à publier dans cette section…'}
            onChange={e => maj('texte', e.target.value)} />
        )}

        {section.type_saisie === 'table' && !contenu.neant && (
          <div className={styles.manualTableBlock}>
            {(contenu.lignes || []).map((ligne, i) => (
              <div className={styles.manualRow} key={i}>
                {(section.colonnes_saisie || []).map(col => (
                  <label key={col.cle} className={styles.field}>
                    <span>{col.label}</span>
                    <input type={col.type || 'text'} disabled={!ecriture}
                      value={ligne[col.cle] ?? ''}
                      step={col.type === 'number' ? '0.01' : undefined}
                      onChange={e => majLigne(i, col.cle, e.target.value)} />
                  </label>
                ))}
                {ecriture && <button className={styles.iconBtn} title="Supprimer la ligne" onClick={() => supprimerLigne(i)}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">Supprimer la ligne</span></button>}
              </div>
            ))}
            {ecriture && <button className={styles.addBtn} onClick={ajouterLigne}><i className="ti ti-plus" /> Ajouter une ligne</button>}
          </div>
        )}

        {section.type_saisie === 'ventilation' && (
          <>
            <TableauVentilation section={section} contenu={contenu} setContenu={setContenu} ecriture={ecriture} />
            <textarea className={styles.textarea} rows={3} value={contenu.notes || ''} disabled={!ecriture}
              placeholder="Notes ou justification complémentaire (facultatif)…"
              onChange={e => maj('notes', e.target.value)} />
          </>
        )}

        {section.type_saisie === 'notes' && (
          <textarea className={styles.textarea} rows={3} value={contenu.notes || ''} disabled={!ecriture}
            placeholder="Notes, ventilation ou justification complémentaire (facultatif)…"
            onChange={e => maj('notes', e.target.value)} />
        )}

        {section.mode === 'assiste' && (
          <label className={styles.confirmCheck}>
            <input type="checkbox" checked={Boolean(contenu.confirme)} disabled={!ecriture}
              onChange={e => maj('confirme', e.target.checked)} />
            J'ai contrôlé les données automatiques et complété les informations extra-comptables nécessaires.
          </label>
        )}

        {ecriture && (
          <div className={styles.actions}>
            <button className={styles.saveBtn} disabled={saving} onClick={sauver}>
              <i className="ti ti-device-floppy" /> {saving ? 'Enregistrement…' : 'Enregistrer'}
            </button>
            {(section.contenu && Object.keys(section.contenu).length > 0) && (
              <button className={styles.resetBtn} disabled={saving} onClick={reinitialiser}>Réinitialiser</button>
            )}
            {message && <span className={message === 'Enregistré' ? styles.okMsg : styles.errMsg}>{message}</span>}
          </div>
        )}
      </div>
    </section>
  )
}

export default function Etic() {
  const { annee } = useExercice()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur] = useState('')
  const [groupe, setGroupe] = useState('A')

  async function charger() {
    setLoading(true); setErreur('')
    try { setData(await etatsAPI.etic(annee)) }
    catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [annee])

  const sections = useMemo(() => (data?.sections || []).filter(s => s.groupe === groupe), [data, groupe])

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <div>
          <h1>ETIC — État des Informations Complémentaires</h1>
          <p>Modèle normal CGNC · Exercice {annee}</p>
        </div>
        <div className={styles.topRight}>
          {data?.progression && <div className={styles.progressBadge}>{data.progression.completes}/{data.progression.total} sections complètes</div>}
          <div className={styles.exercice}><i className="ti ti-calendar" /> Exercice {annee}</div>
        </div>
      </div>

      <div className={styles.content}>
        {loading && <div className={styles.loading}>Chargement de l'ETIC…</div>}
        {erreur && <div className={styles.errorBanner}>{erreur}</div>}
        {!loading && data && (
          <>
            <div className={styles.summaryCard}>
              <div><strong>{data.societe?.raison_sociale}</strong><span>IF {data.societe?.identifiant_fiscal || '—'} · ICE {data.societe?.ice || '—'}</span></div>
              <div className={styles.summaryStats}>
                <span>{data.source?.ecritures_validees_incluses || 0} écritures validées</span>
                <span>{data.source?.brouillons_exclus || 0} brouillon(s) exclu(s)</span>
                <span>Capital : {formatMAD(data.societe?.capital_social || 0)} MAD</span>
              </div>
            </div>

            {data.verrouillee && (
              <div className={styles.warning}><i className="ti ti-lock" />{data.motif_verrouillage}</div>
            )}
            {(data.controle_source?.avertissements || []).map((a, i) => <div className={styles.warning} key={i}><i className="ti ti-alert-triangle" />{a}</div>)}

            <div className={styles.groupTabs}>
              {Object.entries(GROUPES).map(([id, label]) => (
                <button key={id} className={groupe === id ? styles.groupActive : ''} onClick={() => setGroupe(id)}>{label}</button>
              ))}
            </div>

            <div className={styles.sectionList}>
              {sections.map(section => <SectionETIC key={section.code} section={section} exercice={annee} onSaved={charger} verrouillee={data.verrouillee} />)}
            </div>

            <div className={styles.footerNote}>
              L'ETIC complète le Bilan, le CPC, l'ESG et le Tableau de financement. HisabPro ne déduit jamais une information extra-comptable absente : les rubriques assistées ou manuelles doivent être contrôlées avant l'arrêté définitif.
            </div>
          </>
        )}
      </div>
    </div>
  )
}
