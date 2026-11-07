import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const LIBELLES = {
  montant_total: 'Montant total des justificatifs saisis', deja_impute_acomptes: 'Part déjà imputée sur acomptes',
  autres_utilisations: 'Autres utilisations ou restitutions antérieures', disponible_arithmetique: 'Reliquat arithmétique des justificatifs saisis',
  credits_proposes: 'Crédits disponibles proposés après qualifications', ecart_montant_contexte: 'Écart total saisi moins total du contexte fiscal',
  ecart_imputations_contexte: 'Écart déjà imputé moins part du contexte fiscal',
}
const STATUTS = { exclu_declare: 'Exclu selon déclaration', qualifie_declare: 'Qualifié selon déclaration', a_qualifier: 'À qualifier' }
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_credits
  return <section aria-label="Contrôles crédits IS conservés" className={styles.detail}>
    {!c ? <p>Aucune qualification crédits conservée. La saisie reste un brouillon.</p> : <>
      <p>Période source conservée : {c.periode_source.debut} au {c.periode_source.fin}</p>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      {c.lignes.map(r => <p key={r.ligne}>Ligne {r.ligne} · {r.type_credit || 'Type à qualifier'} · {STATUTS[r.statut] || 'À qualifier'} · Reliquat : {argent(r.disponible_arithmetique)}</p>)}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Document DGI publié par le CRI</a></p>
      <p>Aucune imputation, restitution ou liquidation confirmée. CSS distincte.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Qualifier les crédits IS — 2026', titre: 'Crédits et utilisations antérieures', region: 'Crédits IS de la préparation',
  lire: etatsAPI.preparationBalanceCreditsIS, conserver: etatsAPI.conserverBalanceCreditsIS,
  maxLignes: code => code === 'CR-PROFIL' ? 1 : 50,
  libelleSelection: 'Qualification crédits à documenter', libelleChargement: 'Chargement des crédits IS…',
  libelleConserver: 'Conserver les crédits IS dans une nouvelle version',
  noteNombres: 'Chaque justificatif doit préciser les parts déjà utilisées. Un exercice antérieur ou un autre type reste à qualifier. Confirmer le profil et l’exhaustivité avant tout disponible proposé.',
  options: (_d, _s, c) => c.cle === 'regime' ? ['Société IS hors exonération totale'] : c.cle === 'type_credit'
    ? ['PPRF — CGI159', 'Sukuk — CGI159', 'Rémunérations de tiers — CGI157', 'Location — CGI157', 'Autre — à qualifier']
    : c.cle === 'categorie_payeur' ? ['Public ou filiale publique', 'Banque ou assurance', 'Entreprise privée CA au moins 500 millions MAD', 'Autre payeur — à qualifier']
    : ['periode_confirmee', 'exhaustivite', 'absence_credits', 'eligibilite_confirmee'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationCreditsIS(props) { return <Tables {...props} configuration={CONFIG} /> }
