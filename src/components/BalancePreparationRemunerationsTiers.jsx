import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const MONTANTS = { comptabilise: 'Sommes comptabilisées nettes déclarées', soumis: 'Sommes soumises nettes déclarées', retenu: 'Retenues nettes déclarées' }
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_tiers
  return <section aria-label="Contrôles de préparation des tiers" className={styles.detail}>
    {!c ? <p>Aucune préparation tiers conservée. La saisie reste un brouillon.</p> : <>
      <p>{c.revue_documentaire_declaree ? 'Revue documentaire déclarée — contrôle fiscal à effectuer' : 'Préparation à compléter ou à qualifier'}</p>
      <p>Période comptable source : {c.periode_source.debut} au {c.periode_source.fin}</p>
      {Object.entries(MONTANTS).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      {c.beneficiaires.map(b => <p key={b.reference}>{b.reference} · {b.nom} · {b.champs_a_completer.length ? `À revoir : ${b.points_a_revoir.join(', ')}` : 'Identité renseignée et revue déclarée'}</p>)}
      {c.lignes.filter(l => l.champs_a_completer.length).map(l => <p key={l.ligne}>Mouvement {l.ligne} · {l.reference_source} : {l.points_a_revoir.join(', ')}</p>)}
      {c.regroupements.map((g, i) => <div key={i} className={styles.detail}><p>{g.beneficiaire_ref || 'Bénéficiaire à préciser'} · {g.categorie || 'Catégorie à qualifier'}</p>{Object.entries(MONTANTS).map(([k, label]) => <p key={k}>{label} : {argent(g.montants[k])}</p>)}</div>)}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Source DGI publiée par le CRI</a></p>
      <p>Préparation interne conservée, sans écriture générée ni déclaration ou dépôt officiel validé.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Préparer les rémunérations des tiers', titre: 'Bénéficiaires et rémunérations — préparation interne', region: 'Rémunérations des tiers de la préparation',
  lire: etatsAPI.preparationBalanceRemunerationsTiers, conserver: etatsAPI.conserverBalanceRemunerationsTiers,
  maxLignes: code => code === 'T151-P' ? 1 : code === 'T151-B' ? 50 : 100,
  libelleSelection: 'Rubrique tiers à documenter', libelleChargement: 'Chargement des rémunérations des tiers…',
  libelleConserver: 'Conserver les rémunérations des tiers dans une nouvelle version',
  noteNombres: 'Montants positifs ou nuls, deux décimales maximum. Pour soustraire une correction, choisir Correction documentée et référencer son origine. Aucun taux de retenue calculé.',
  options: (_d, _s, c) => c.cle === 'regime' ? ['Personne morale IS', 'Personne physique RNR ou RNS', 'CPU', 'Autoentrepreneur', 'Autre — à qualifier']
    : c.cle === 'categorie' ? ['Honoraires', 'Commissions, courtages et rémunérations similaires', 'Rabais, remises et ristournes après facturation', 'Produits de location — annexe à qualifier', 'Autre — à qualifier']
    : c.cle === 'sens' ? ['Allocation', 'Correction documentée']
    : c.cle === 'evenement' ? ['Versement', 'Mise à disposition', 'Inscription en compte', 'Aucune retenue déclarée']
    : ['periode_confirmee', 'exhaustivite', 'absence', 'identite_revue', 'source_revue'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationRemunerationsTiers(props) { return <Tables {...props} configuration={CONFIG} /> }
