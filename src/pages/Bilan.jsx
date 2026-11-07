import { useMemo, useState, useEffect, Fragment } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { useLocation } from 'react-router-dom'
import { formatMAD } from '../data/donnees.js'
import { useDonneesEtats, calculerCPC, calculerBilan, calculerESG, calculerTableauFinancement } from '../data/etatsSynthese.js'
import styles from './Bilan.module.css'
import { presenterBilan } from '../data/bilanPresentation.js'
import { API_BASE } from '../services/api.js'
import { notifier } from '../services/notifications.js'

const fmt = m => {
  if (Math.abs(m) < 0.005) return '—'
  return m < 0 ? `(${formatMAD(-m)})` : formatMAD(m)
}

// Ligne du CPC (rubrique numérotée ou détail)
function LigneCPC({ numero = null, label, montant, montantN1 = null, avecN1 = false, gras = false, niveau = 0, signe = false }) {
  return (
    <tr className={gras ? styles.rowTotal : styles.rowLigne}>
      <td style={{ width: 44, textAlign: 'center', fontWeight: 600, color: 'var(--text-tertiary)', fontSize: 11 }}>{numero || ''}</td>
      <td style={{ paddingLeft: 8 + niveau * 14 }}>{label}</td>
      <td className={`${styles.colNum} ${montant < 0 && signe ? styles.negatif : ''}`}>{fmt(montant)}</td>
      {avecN1 && (
        <td className={`${styles.colNum} ${montantN1 < 0 && signe ? styles.negatif : ''}`}
          style={{ color: 'var(--text-tertiary)' }}>
          {montantN1 === null ? '—' : fmt(montantN1)}
        </td>
      )}
    </tr>
  )
}

// ─── Page ──────────────────────────────────────────────────────────────────────
export default function Bilan() {
  const location = useLocation()
  const { annee } = useExercice()
  const [onglet, setOnglet] = useState(location.pathname === '/cpc' ? 'cpc' : 'bilan')

  useEffect(() => {
    setOnglet(location.pathname === '/cpc' ? 'cpc' : 'bilan')
  }, [location.pathname])

  const donneesN = useDonneesEtats(annee)
  const donneesN1 = useDonneesEtats(annee - 1)
  const soldes = donneesN.soldes
  const soldesN1 = donneesN1.soldes
  const n1Disponible = donneesN1.disponible
  const [afficherN1, setAfficherN1] = useState(false)

  const cpc = useMemo(() => calculerCPC(soldes), [soldes])
  const cpcN1 = useMemo(() => calculerCPC(soldesN1), [soldesN1])

  // Le résultat courant vient des classes 6/7. Un éventuel 119 reporté d'un
  // exercice antérieur est affiché séparément au passif par calculerBilan.
  const resultatNet = cpc.resultatNet
  const resultatNetN1 = cpcN1.resultatNet

  const bilan = useMemo(() => calculerBilan(soldes, resultatNet), [soldes, resultatNet])
  const bilanN1 = useMemo(() => calculerBilan(soldesN1, resultatNetN1), [soldesN1, resultatNetN1])
  const rubriquesBilan = useMemo(() => presenterBilan(bilan, soldes, bilanN1, soldesN1, n1Disponible), [bilan, soldes, bilanN1, soldesN1, n1Disponible])

  const esg = useMemo(() => calculerESG(soldes), [soldes])
  const esgN1 = useMemo(() => calculerESG(soldesN1), [soldesN1])
  // Tableau de financement : 5e état de synthèse (art. 9 loi 9-88).
  // Il compare deux bilans successifs — sans exercice N-1, il reste vide.
  const tf = useMemo(() => calculerTableauFinancement(
    soldes, soldesN1, cpc, cpcN1, donneesN.fluxFinancement, donneesN1.fluxFinancement
  ), [soldes, soldesN1, cpc, cpcN1, donneesN.fluxFinancement, donneesN1.fluxFinancement])
  const [exportEnCours, setExportEnCours] = useState(false)

  // N-1 affiché seulement si demandé ET disponible
  const n1 = afficherN1 && n1Disponible

  // ── Export PDF : les montants sont recalculés côté serveur ──────────────
  async function exporterPDF() {
    setExportEnCours(true)
    try {
      const token = localStorage.getItem('hisabpro_token')
      const etats = onglet === 'bilan'
        ? ['bilan_actif', 'bilan_passif']
        : [onglet === 'tf' ? 'tableau_financement' : onglet]

      for (const etat of etats) {
        const p = new URLSearchParams({ comparatif: onglet === 'bilan' || n1 ? 'true' : 'false' })
        const res = await fetch(`${API_BASE}/api/etats/pdf-officiel/${etat}/${annee}?${p}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) {
          let message = 'Erreur lors de la génération du PDF'
          try {
            const body = await res.json()
            message = body?.detail || message
          } catch {}
          throw new Error(typeof message === 'string' ? message : 'Erreur lors de la génération du PDF')
        }
        const blob = await res.blob()
        const cd = res.headers.get('content-disposition') || ''
        const m = cd.match(/filename="?([^";]+)"?/i)
        const noms = {
          bilan_actif: `bilan_actif_${annee}.pdf`,
          bilan_passif: `bilan_passif_${annee}.pdf`,
          cpc: `cpc_${annee}.pdf`,
          esg: `esg_${annee}.pdf`,
          tableau_financement: `tableau_financement_${annee}.pdf`,
        }
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = m ? m[1] : noms[etat]
        document.body.appendChild(a)
        a.click()
        a.remove()
        setTimeout(() => URL.revokeObjectURL(a.href), 1000)
      }
    } catch (e) {
      notifier.erreur(e.message)
    } finally {
      setExportEnCours(false)
    }
  }

  const LIGNES_CPC_PRODUITS = [
    ['Ventes de marchandises (en l\'état)', cpc.produitsExploitation.ventesMarchandises],
    ['Ventes de biens et services produits', cpc.produitsExploitation.ventesBiensServices],
    ['Variation de stocks de produits (±)', cpc.produitsExploitation.variationStocks],
    ['Immobilisations produites par l\'entreprise pour elle-même', cpc.produitsExploitation.immobilisationsProduites],
    ['Subventions d\'exploitation', cpc.produitsExploitation.subventions],
    ['Autres produits d\'exploitation', cpc.produitsExploitation.autresProduits],
    ['Reprises d\'exploitation, transferts de charges', cpc.produitsExploitation.reprisesTransferts],
  ]
  const LIGNES_CPC_CHARGES = [
    ['Achats revendus de marchandises', cpc.chargesExploitation.achatsRevendus],
    ['Achats consommés de matières et fournitures', cpc.chargesExploitation.achatsConsommes],
    ['Autres charges externes', cpc.chargesExploitation.autresChargesExternes],
    ['Impôts et taxes', cpc.chargesExploitation.impotsTaxes],
    ['Charges de personnel', cpc.chargesExploitation.chargesPersonnel],
    ['Autres charges d\'exploitation', cpc.chargesExploitation.autresCharges],
    ['Dotations d\'exploitation', cpc.chargesExploitation.dotations],
  ]

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>États de synthèse</h1>
        <div className={styles.topbarRight}>
          {n1Disponible && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer', marginRight: 4 }}>
              <input type="checkbox" checked={afficherN1} onChange={e => setAfficherN1(e.target.checked)} />
              Comparer à {annee - 1}
            </label>
          )}
          <button className={styles.btnSec} onClick={exporterPDF} disabled={exportEnCours}>
            <i className="ti ti-file-type-pdf" style={{ color: '#DC2626' }} aria-hidden="true" />
            {exportEnCours ? 'Génération...' : `Exporter ${onglet === 'bilan' ? 'le Bilan' : onglet === 'cpc' ? 'le CPC' : onglet === 'tf' ? 'le Tableau de financement' : 'l\'ESG'} en PDF`}
          </button>
        </div>
      </div>

      <div className={styles.content}>
        {donneesN.erreur && (
          <div className={`${styles.sourceBanner} ${styles.sourceErreur}`}>
            <i className="ti ti-alert-triangle" aria-hidden="true" />
            <div><strong>États indisponibles.</strong> {donneesN.erreur}</div>
          </div>
        )}

        {!donneesN.erreur && donneesN.controle?.avertissements?.length > 0 && (
          <div className={`${styles.sourceBanner} ${styles.sourceAlerte}`}>
            <i className="ti ti-info-circle" aria-hidden="true" />
            <div>
              <strong>Source comptable contrôlée.</strong>
              {donneesN.controle.avertissements.map((a, i) => <div key={i}>{a}</div>)}
            </div>
          </div>
        )}

        {!donneesN.chargement && donneesN.source && (
          <div className={styles.sourceMeta}>
            <span><i className="ti ti-lock-check" aria-hidden="true" /> {donneesN.source.ecritures_validees_incluses} écriture(s) validée(s)</span>
            <span>{donneesN.source.comptes_mouvementes} compte(s) mouvementé(s)</span>
            {donneesN.source.clotures_techniques_exclues > 0 && <span>{donneesN.source.clotures_techniques_exclues} écriture(s) de clôture technique exclue(s)</span>}
            {donneesN.modele?.eligible_modele_simplifie && <span>Éligible au modèle simplifié (CA indicatif ≤ 10 M MAD) — affichage normal conservé</span>}
          </div>
        )}

        {/* Onglets */}
        <div className={styles.onglets}>
          {[
            { id: 'bilan', label: 'Bilan', icon: 'ti-chart-bar' },
            { id: 'cpc',   label: 'CPC',   icon: 'ti-trending-up' },
            { id: 'esg',   label: 'ESG',   icon: 'ti-stairs' },
            { id: 'tf',    label: 'Tableau de financement', icon: 'ti-arrows-exchange' },
          ].map(o => (
            <button key={o.id}
              className={`${styles.ongletBtn} ${onglet === o.id ? styles.ongletBtnActif : ''}`}
              onClick={() => setOnglet(o.id)}>
              <i className={`ti ${o.icon}`} aria-hidden="true" />{o.label}
            </button>
          ))}
          <div className={styles.exerciceBadge}>
            <i className="ti ti-calendar" aria-hidden="true" /> Exercice {annee}
          </div>
          <div className={`${styles.equilibreBadge} ${bilan.equilibre ? styles.equilibreOk : styles.equilibreKo}`}>
            {bilan.equilibre
              ? <><i className="ti ti-check" aria-hidden="true" /> Bilan équilibré — Actif = Passif</>
              : <><i className="ti ti-alert-triangle" aria-hidden="true" /> Écart Actif − Passif : {formatMAD(bilan.ecart)} MAD</>}
          </div>
        </div>

        {/* Bilan détaillé : colonnes N et N-1 présentes même au premier exercice. */}
        {onglet === 'bilan' && (
          <div className={styles.bilanColonne}>
            {!n1Disponible && <p className={styles.noteBas}>Exercice précédent indisponible : sa colonne est volontairement laissée vide (aucun zéro fictif).</p>}
            {['actif', 'passif'].map(cote => (
              <section className={styles.card} key={cote} aria-label={`Bilan ${cote}`}>
                <div className={styles.cardHeader}>
                  <span className={styles.cardTitle}>BILAN — {cote.toUpperCase()} · Présentation détaillée</span>
                  <span className={styles.totalHeader}>{formatMAD(cote === 'actif' ? bilan.totalActif.net : bilan.totalPassif)} MAD</span>
                </div>
                <div className={styles.bilanTableScroll}>
                  <table className={`${styles.table} ${styles.bilanDetailTable} ${cote === 'actif' ? styles.bilanActif : styles.bilanPassif}`}>
                    <colgroup>
                      <col className={styles.bilanRefCol} /><col className={styles.bilanLibelleCol} />
                      {cote === 'actif' && <><col /><col /><col /><col /></>}
                      {cote === 'passif' && <><col /><col /></>}
                    </colgroup>
                    <thead>
                      <tr className={styles.rowEntete}>
                        <th scope="col">Réf.</th><th scope="col">{cote === 'actif' ? 'ACTIF' : 'PASSIF'}</th>
                        {cote === 'actif'
                          ? <><th className={styles.colNum}>Brut {annee}</th><th className={styles.colNum}>Amort. &amp; prov.</th><th className={styles.colNum}>Net {annee}</th><th className={styles.colNum}>Net {annee - 1}</th></>
                          : <><th className={styles.colNum}>{annee}</th><th className={styles.colNum}>{annee - 1}</th></>}
                      </tr>
                    </thead>
                    <tbody>
                      {rubriquesBilan.filter(section => section.side === cote).map(section => (
                        <Fragment key={`${cote}-${section.key}`}>
                          <tr className={styles.rowSousTitre}>
                            <td colSpan={cote === 'actif' ? 6 : 4}>{section.label}</td>
                          </tr>
                          {section.groups.map(group => (
                            <Fragment key={group.code}>
                              <tr className={styles.bilanGroup}>
                                <td className={styles.bilanRef}>{group.code}</td>
                                <td>{group.label}{group.code === 'R' && <span className={styles.badgeCalcule}>calculé</span>}</td>
                                {cote === 'actif'
                                  ? <><td className={styles.colNum}>{fmt(group.brut)}</td><td className={styles.colNum}>{fmt(group.amort)}</td><td className={styles.colNum}>{fmt(group.net)}</td><td className={styles.colNum}>{group.n1 === null ? '—' : fmt(group.n1)}</td></>
                                  : <><td className={styles.colNum}>{fmt(group.montant)}</td><td className={styles.colNum}>{group.n1 === null ? '—' : fmt(group.n1)}</td></>}
                              </tr>
                              {cote === 'actif' && group.details.map(detail => (
                                <tr className={styles.bilanDetail} key={`${group.code}-${detail.code}`}>
                                  <td className={styles.bilanRef}>{detail.code}</td><td>{detail.label}</td>
                                  <td className={styles.colNum}>{fmt(detail.brut)}</td><td className={styles.colNum}>—</td>
                                  <td className={styles.colNum}>{detail.net === null ? '—' : fmt(detail.net)}</td>
                                  <td className={styles.colNum}>{detail.netN1 === null ? '—' : fmt(detail.netN1)}</td>
                                </tr>
                              ))}
                            </Fragment>
                          ))}
                          <tr className={styles.rowTotal}>
                            <td></td><td>{section.totalLabel}</td>
                            {cote === 'actif'
                              ? <><td className={styles.colNum}>{fmt(section.total.brut)}</td><td className={styles.colNum}>{fmt(section.total.amort)}</td><td className={styles.colNum}>{fmt(section.total.net)}</td><td className={styles.colNum}>{section.totalN1 === null ? '—' : fmt(section.totalN1.net)}</td></>
                              : <><td className={styles.colNum}>{fmt(section.total)}</td><td className={styles.colNum}>{section.totalN1 === null ? '—' : fmt(section.totalN1)}</td></>}
                          </tr>
                        </Fragment>
                      ))}
                      <tr className={styles.bilanGrandTotal}>
                        <td></td><td>TOTAL GÉNÉRAL {cote.toUpperCase()}</td>
                        {cote === 'actif'
                          ? <><td className={styles.colNum}>{fmt(bilan.totalActif.brut)}</td><td className={styles.colNum}>{fmt(bilan.totalActif.amort)}</td><td className={styles.colNum}>{fmt(bilan.totalActif.net)}</td><td className={styles.colNum}>{n1Disponible ? fmt(bilanN1.totalActif.net) : '—'}</td></>
                          : <><td className={styles.colNum}>{fmt(bilan.totalPassif)}</td><td className={styles.colNum}>{n1Disponible ? fmt(bilanN1.totalPassif) : '—'}</td></>}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            ))}
            <p className={styles.noteBas}>Bilan de consultation · Exercice {annee} {donneesN.source?.exercice_clos ? 'clôturé' : 'en cours'} · Les sous-postes détaillent les rubriques sans être ajoutés aux totaux. En présence de dépréciations, leur net n’est pas ventilé arbitrairement.</p>
          </div>
        )}

        {/* ── CPC ── */}
        {onglet === 'cpc' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>Compte de Produits et Charges (CPC) — Modèle Normal</span>
              <span className={styles.totalHeader} style={{ color: cpc.resultatNet >= 0 ? 'var(--green)' : 'var(--red)' }}>
                Résultat net : {fmt(cpc.resultatNet)} MAD
              </span>
            </div>
            <table className={styles.table}>
              {n1 && (
                <thead>
                  <tr>
                    <th style={{ width: 44 }}></th>
                    <th style={{ textAlign: 'left' }}></th>
                    <th className={styles.colNum}>{annee}</th>
                    <th className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{annee - 1}</th>
                  </tr>
                </thead>
              )}
              <tbody>
                <tr className={styles.rowSousTitre}><td colSpan={n1 ? 4 : 3}>EXPLOITATION</td></tr>
                <LigneCPC numero="I" label="PRODUITS D'EXPLOITATION" montant={cpc.I} montantN1={cpcN1.I} avecN1={n1} gras />
                {LIGNES_CPC_PRODUITS.map(([label, montant]) => (
                  <LigneCPC key={label} label={label} montant={montant} niveau={1} signe />
                ))}
                <LigneCPC numero="II" label="CHARGES D'EXPLOITATION" montant={cpc.II} montantN1={cpcN1.II} avecN1={n1} gras />
                {LIGNES_CPC_CHARGES.map(([label, montant]) => (
                  <LigneCPC key={label} label={label} montant={montant} niveau={1} />
                ))}
                <LigneCPC numero="III" label="RÉSULTAT D'EXPLOITATION (I − II)" montant={cpc.III} montantN1={cpcN1.III} avecN1={n1} gras signe />

                <tr className={styles.rowSousTitre}><td colSpan={n1 ? 4 : 3}>FINANCIER</td></tr>
                <LigneCPC numero="IV" label="PRODUITS FINANCIERS" montant={cpc.IV} montantN1={cpcN1.IV} avecN1={n1} gras />
                <LigneCPC label="Produits des titres de participation et immobilisés" montant={cpc.produitsFinanciers.produitsTitres} niveau={1} />
                <LigneCPC label="Gains de change" montant={cpc.produitsFinanciers.gainsChange} niveau={1} />
                <LigneCPC label="Intérêts et autres produits financiers" montant={cpc.produitsFinanciers.interetsAutres} niveau={1} />
                <LigneCPC label="Reprises financières, transferts de charges" montant={cpc.produitsFinanciers.reprisesFinancieres} niveau={1} />
                <LigneCPC numero="V" label="CHARGES FINANCIÈRES" montant={cpc.V} montantN1={cpcN1.V} avecN1={n1} gras />
                <LigneCPC label="Charges d'intérêts" montant={cpc.chargesFinancieres.chargesInterets} niveau={1} />
                <LigneCPC label="Pertes de change" montant={cpc.chargesFinancieres.pertesChange} niveau={1} />
                <LigneCPC label="Autres charges financières" montant={cpc.chargesFinancieres.autresChargesFin} niveau={1} />
                <LigneCPC label="Dotations financières" montant={cpc.chargesFinancieres.dotationsFinancieres} niveau={1} />
                <LigneCPC numero="VI" label="RÉSULTAT FINANCIER (IV − V)" montant={cpc.VI} montantN1={cpcN1.VI} avecN1={n1} gras signe />
                <LigneCPC numero="VII" label="RÉSULTAT COURANT (III + VI)" montant={cpc.VII} montantN1={cpcN1.VII} avecN1={n1} gras signe />

                <tr className={styles.rowSousTitre}><td colSpan={n1 ? 4 : 3}>NON COURANT</td></tr>
                <LigneCPC numero="VIII" label="PRODUITS NON COURANTS" montant={cpc.VIII} montantN1={cpcN1.VIII} avecN1={n1} gras />
                <LigneCPC label="Produits des cessions d'immobilisations" montant={cpc.produitsNonCourants.cessionsImmobilisations} niveau={1} />
                <LigneCPC label="Subventions d'équilibre" montant={cpc.produitsNonCourants.subventionsEquilibre} niveau={1} />
                <LigneCPC label="Reprises sur subventions d'investissement" montant={cpc.produitsNonCourants.reprisesSubventions} niveau={1} />
                <LigneCPC label="Autres produits non courants" montant={cpc.produitsNonCourants.autresProduitsNC} niveau={1} />
                <LigneCPC label="Reprises non courantes, transferts de charges" montant={cpc.produitsNonCourants.reprisesNC} niveau={1} />
                <LigneCPC numero="IX" label="CHARGES NON COURANTES" montant={cpc.IX} montantN1={cpcN1.IX} avecN1={n1} gras />
                <LigneCPC label="VNA des immobilisations cédées" montant={cpc.chargesNonCourantes.vnaImmobilisationsCedees} niveau={1} />
                <LigneCPC label="Subventions accordées" montant={cpc.chargesNonCourantes.subventionsAccordees} niveau={1} />
                <LigneCPC label="Autres charges non courantes" montant={cpc.chargesNonCourantes.autresChargesNC} niveau={1} />
                <LigneCPC label="Dotations non courantes" montant={cpc.chargesNonCourantes.dotationsNC} niveau={1} />
                <LigneCPC numero="X" label="RÉSULTAT NON COURANT (VIII − IX)" montant={cpc.X} montantN1={cpcN1.X} avecN1={n1} gras signe />

                <tr className={styles.rowSousTitre}><td colSpan={n1 ? 4 : 3}>RÉSULTATS</td></tr>
                <LigneCPC numero="XI" label="RÉSULTAT AVANT IMPÔTS (VII + X)" montant={cpc.XI} montantN1={cpcN1.XI} avecN1={n1} gras signe />
                <LigneCPC numero="XII" label="IMPÔTS SUR LES RÉSULTATS" montant={cpc.XII} montantN1={cpcN1.XII} avecN1={n1} gras />
                <LigneCPC numero="XIII" label="RÉSULTAT NET (XI − XII)" montant={cpc.resultatNet} montantN1={cpcN1.resultatNet} avecN1={n1} gras signe />
                <LigneCPC numero="XIV" label="TOTAL DES PRODUITS (I + IV + VIII)" montant={cpc.I + cpc.IV + cpc.VIII} gras />
                <LigneCPC numero="XV" label="TOTAL DES CHARGES (II + V + IX + XII)" montant={cpc.II + cpc.V + cpc.IX + cpc.XII} gras />
              </tbody>
            </table>
          </div>
        )}

        {/* ── ESG ── */}
        {onglet === 'esg' && (
          <div className={styles.bilanColonne}>
            {/* TFR */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Tableau de Formation des Résultats (TFR)</span>
                <span className={styles.totalHeader} style={{ color: esg.resultatNet >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  Résultat net : {fmt(esg.resultatNet)} MAD
                </span>
              </div>
              <table className={styles.table}>
                {n1 && (
                  <thead>
                    <tr>
                      <th style={{ width: 44 }}></th>
                      <th style={{ textAlign: 'left' }}></th>
                      <th className={styles.colNum}>{annee}</th>
                      <th className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{annee - 1}</th>
                    </tr>
                  </thead>
                )}
                <tbody>
                  <LigneCPC label="Ventes de marchandises (en l'état)" montant={esg.ventesMarchandises} montantN1={esgN1.ventesMarchandises} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Achats revendus de marchandises" montant={esg.achatsRevendus} montantN1={esgN1.achatsRevendus} avecN1={n1} niveau={1} />
                  <LigneCPC label="MARGE BRUTE SUR VENTES EN L'ÉTAT" montant={esg.margeBrute} montantN1={esgN1.margeBrute} avecN1={n1} gras signe />
                  <LigneCPC label="Ventes de biens et services produits" montant={esg.ventesBiensServices} montantN1={esgN1.ventesBiensServices} avecN1={n1} niveau={1} />
                  <LigneCPC label="Variation de stocks de produits (±)" montant={esg.variationStocksProd} montantN1={esgN1.variationStocksProd} avecN1={n1} niveau={1} signe />
                  <LigneCPC label="Immobilisations produites par l'entreprise" montant={esg.immobProduites} montantN1={esgN1.immobProduites} avecN1={n1} niveau={1} />
                  <LigneCPC label="PRODUCTION DE L'EXERCICE" montant={esg.production} montantN1={esgN1.production} avecN1={n1} gras signe />
                  <LigneCPC label="Achats consommés de matières et fournitures" montant={esg.achatsConsommes} montantN1={esgN1.achatsConsommes} avecN1={n1} niveau={1} />
                  <LigneCPC label="Autres charges externes" montant={esg.autresChargesExternes} montantN1={esgN1.autresChargesExternes} avecN1={n1} niveau={1} />
                  <LigneCPC label="CONSOMMATION DE L'EXERCICE" montant={esg.consommation} montantN1={esgN1.consommation} avecN1={n1} gras />
                  <LigneCPC label="VALEUR AJOUTÉE" montant={esg.valeurAjoutee} montantN1={esgN1.valeurAjoutee} avecN1={n1} gras signe />
                  <LigneCPC label="+ Subventions d'exploitation" montant={esg.subventionsExploitation} montantN1={esgN1.subventionsExploitation} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Impôts et taxes" montant={esg.impotsTaxes} montantN1={esgN1.impotsTaxes} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Charges de personnel" montant={esg.chargesPersonnel} montantN1={esgN1.chargesPersonnel} avecN1={n1} niveau={1} />
                  <LigneCPC label="EXCÉDENT BRUT D'EXPLOITATION (EBE)" montant={esg.ebe} montantN1={esgN1.ebe} avecN1={n1} gras signe />
                  <LigneCPC label="+ Autres produits d'exploitation" montant={esg.autresProduitsExpl} montantN1={esgN1.autresProduitsExpl} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Autres charges d'exploitation" montant={esg.autresChargesExpl} montantN1={esgN1.autresChargesExpl} avecN1={n1} niveau={1} />
                  <LigneCPC label="+ Reprises d'exploitation, transferts de charges" montant={esg.reprisesExploitation} montantN1={esgN1.reprisesExploitation} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Dotations d'exploitation" montant={esg.dotationsExploitation} montantN1={esgN1.dotationsExploitation} avecN1={n1} niveau={1} />
                  <LigneCPC label="RÉSULTAT D'EXPLOITATION" montant={esg.resultatExploitation} montantN1={esgN1.resultatExploitation} avecN1={n1} gras signe />
                  <LigneCPC label="RÉSULTAT FINANCIER" montant={esg.resultatFinancier} montantN1={esgN1.resultatFinancier} avecN1={n1} gras signe />
                  <LigneCPC label="RÉSULTAT COURANT" montant={esg.resultatCourant} montantN1={esgN1.resultatCourant} avecN1={n1} gras signe />
                  <LigneCPC label="RÉSULTAT NON COURANT" montant={esg.resultatNonCourant} montantN1={esgN1.resultatNonCourant} avecN1={n1} gras signe />
                  <LigneCPC label="− Impôts sur les résultats" montant={esg.impotsResultats} montantN1={esgN1.impotsResultats} avecN1={n1} niveau={1} />
                  <LigneCPC label="RÉSULTAT NET DE L'EXERCICE" montant={esg.resultatNet} montantN1={esgN1.resultatNet} avecN1={n1} gras signe />
                </tbody>
              </table>
            </div>

            {/* CAF */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Capacité d'Autofinancement (CAF) — méthode additive</span>
                <span className={styles.totalHeader} style={{ color: esg.caf >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  CAF : {fmt(esg.caf)} MAD
                </span>
              </div>
              <table className={styles.table}>
                {n1 && (
                  <thead>
                    <tr>
                      <th style={{ width: 44 }}></th>
                      <th style={{ textAlign: 'left' }}></th>
                      <th className={styles.colNum}>{annee}</th>
                      <th className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{annee - 1}</th>
                    </tr>
                  </thead>
                )}
                <tbody>
                  <LigneCPC label="Résultat net de l'exercice" montant={esg.resultatNet} montantN1={esgN1.resultatNet} avecN1={n1} niveau={1} signe />
                  <LigneCPC label="+ Dotations d'exploitation, financières et non courantes (éléments durables)" montant={esg.dotationsDurables} montantN1={esgN1.dotationsDurables} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Reprises sur éléments durables (y c. subventions d'investissement)" montant={esg.reprisesDurables} montantN1={esgN1.reprisesDurables} avecN1={n1} niveau={1} />
                  <LigneCPC label="− Produits des cessions d'immobilisations" montant={esg.produitsCessions} montantN1={esgN1.produitsCessions} avecN1={n1} niveau={1} />
                  <LigneCPC label="+ VNA des immobilisations cédées" montant={esg.vnaCessions} montantN1={esgN1.vnaCessions} avecN1={n1} niveau={1} />
                  <LigneCPC label="CAPACITÉ D'AUTOFINANCEMENT" montant={esg.caf} montantN1={esgN1.caf} avecN1={n1} gras signe />
                </tbody>
              </table>
              <p style={{ fontSize: 10, color: 'var(--text-tertiary)', padding: '8px 16px', margin: 0 }}>
                Conformément au CGNC, les dotations et reprises relatives aux actifs et passifs circulants sont exclues du calcul de la CAF.
              </p>
            </div>
          </div>
        )}

        {/* ── Tableau de financement ── */}
        {onglet === 'tf' && (
          <div className={styles.bilanColonne}>
            {!n1Disponible ? (
              <div className={styles.card}>
                <div className={styles.cardBody} style={{ padding: 40, textAlign: 'center' }}>
                  <i className="ti ti-arrows-exchange" style={{ fontSize: 30, color: 'var(--text-tertiary)' }} />
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 12 }}>
                    Le tableau de financement compare deux bilans successifs.
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Aucune écriture n&apos;a été trouvée sur l&apos;exercice {annee - 1} :
                    il ne peut pas être établi pour {annee}.
                  </p>
                </div>
              </div>
            ) : (
              <>
                {/* I — Synthèse des masses du bilan */}
                <div className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardTitle}>
                      I — Synthèse des masses du bilan
                    </span>
                    <span className={styles.totalHeader}
                      style={{ color: tf.variationTN >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      Trésorerie {tf.variationTN >= 0 ? '+' : ''}{fmt(tf.variationTN)}
                    </span>
                  </div>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Masse</th>
                        <th className={styles.colNum}>{annee}</th>
                        <th className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{annee - 1}</th>
                        <th className={styles.colNum}>Emplois</th>
                        <th className={styles.colNum}>Ressources</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tf.synthese.map((l, i) => (
                        <tr key={i} className={l.total ? styles.rowTotal : styles.rowLigne}>
                          <td style={{ paddingLeft: l.total ? 8 : 22 }}>{l.libelle}</td>
                          <td className={styles.colNum}>{fmt(l.n)}</td>
                          <td className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{fmt(l.n1)}</td>
                          <td className={styles.colNum}>{l.emploi > 0.005 ? fmt(l.emploi) : '—'}</td>
                          <td className={styles.colNum}>{l.ressource > 0.005 ? fmt(l.ressource) : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* II — Emplois et ressources stables */}
                <div className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardTitle}>
                      II — Emplois et ressources stables de l&apos;exercice
                    </span>
                  </div>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Rubrique CGNC</th>
                        <th className={styles.colNum}>{annee}</th>
                        <th className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{annee - 1}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className={styles.rowSousTitre}><td colSpan={3}>I — RESSOURCES STABLES DE L&apos;EXERCICE (FLUX)</td></tr>
                      {tf.ressources.map((r, i) => (
                        <tr key={`r${i}`} className={r.total ? styles.rowTotal : styles.rowLigne}>
                          <td style={{ paddingLeft: r.niveau ? 28 : 10 }}>{r.libelle}</td>
                          <td className={styles.colNum}>{fmt(r.montant)}</td>
                          <td className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{fmt(r.n1)}</td>
                        </tr>
                      ))}
                      <tr className={styles.rowTotal}>
                        <td>TOTAL RESSOURCES STABLES (A+B+C+D)</td>
                        <td className={styles.colNum}>{fmt(tf.totalRessources)}</td>
                        <td className={styles.colNum}>—</td>
                      </tr>

                      <tr className={styles.rowSousTitre}><td colSpan={3}>II — EMPLOIS STABLES DE L&apos;EXERCICE (FLUX)</td></tr>
                      {tf.emplois.map((e, i) => (
                        <tr key={`e${i}`} className={e.total ? styles.rowTotal : styles.rowLigne}>
                          <td style={{ paddingLeft: e.niveau ? 28 : 10 }}>{e.libelle}</td>
                          <td className={styles.colNum}>{fmt(e.montant)}</td>
                          <td className={styles.colNum} style={{ color: 'var(--text-tertiary)' }}>{fmt(e.n1)}</td>
                        </tr>
                      ))}
                      <tr className={styles.rowTotal}>
                        <td>TOTAL EMPLOIS STABLES (E+F+G+H)</td>
                        <td className={styles.colNum}>{fmt(tf.totalEmplois)}</td>
                        <td className={styles.colNum}>—</td>
                      </tr>

                      <tr className={styles.rowTotal}>
                        <td>III — VARIATION DU BESOIN DE FINANCEMENT GLOBAL</td>
                        <td className={styles.colNum}>{fmt(tf.variationBFG)}</td>
                        <td className={styles.colNum}>—</td>
                      </tr>
                      <tr className={styles.rowTotal}>
                        <td>IV — VARIATION DE LA TRÉSORERIE</td>
                        <td className={styles.colNum}>{fmt(tf.variationTN)}</td>
                        <td className={styles.colNum}>—</td>
                      </tr>
                      <tr className={styles.rowTotal}>
                        <td>TOTAL GÉNÉRAL — EMPLOIS / RESSOURCES</td>
                        <td className={styles.colNum}>{fmt(tf.totalGeneralEmplois)} / {fmt(tf.totalGeneralRessources)}</td>
                        <td className={styles.colNum}>—</td>
                      </tr>
                    </tbody>
                  </table>
                  {tf.avertissements?.map((a, i) => (
                    <div key={i} style={{ padding: '8px 16px', fontSize: 11, color: '#8A5A00', borderTop: '0.5px solid var(--border-light)' }}>{a}</div>
                  ))}
                  <div style={{ padding: '10px 16px', fontSize: 11,
                    color: tf.controle ? 'var(--text-tertiary)' : '#A32D2D',
                    borderTop: '0.5px solid var(--border-light)' }}>
                    {tf.controle
                      ? 'Contrôle CGNC : ressources stables − emplois stables = variation du fonds de roulement, et le total général emplois/ressources est équilibré.'
                      : `Écart de contrôle : ${fmt(tf.ecartControle)} MAD sur le fonds de roulement ; ${fmt(tf.ecartTotalGeneral)} MAD sur le total général.`}
                  </div>
                </div>

                <p className={styles.noteBas}>
                  Le tableau de financement est le cinquième état de synthèse prévu par
                  l&apos;article 9 de la loi 9-88. Les entreprises réalisant un chiffre
                  d&apos;affaires inférieur ou égal à 10 millions de dirhams en sont
                  dispensées (article 21).
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
