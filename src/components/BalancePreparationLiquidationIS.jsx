import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const LIBELLES = {
  is_theorique: 'IS théorique au taux B12 déclaré', cm_proposee: 'CM proposée selon qualification conservée',
  impot_avant_imputations: 'Maximum IS/CM proposé avant imputations', credits_disponibles: 'Crédits qualifiés disponibles après utilisations antérieures',
  acomptes_imputables: 'Acomptes justifiés proposés', excedent_anterieur_restant: 'Excédent antérieur restant après acomptes',
  excedent_anterieur_annuel_demande: 'Excédent antérieur réservé à cette simulation annuelle',
  credits_appliques: 'Crédits et excédent annuel appliqués dans la simulation', acomptes_appliques: 'Acomptes appliqués dans la simulation',
  solde_is_propose: 'Solde IS/CM proposé à payer', excedent_arithmetique: 'Excédent arithmétique de la simulation',
  css_separee: 'CSS proposée séparément dans sa qualification conservée',
}
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_liquidation
  return <section aria-label="Contrôles de la proposition IS CM" className={styles.detail}>
    {!c ? <p>Aucune proposition conservée. La revue reste un brouillon.</p> : <>
      <p><strong>{data.sources_is_modifiees ? 'Proposition historique — sources modifiées' : c.proposition_disponible ? 'Proposition conditionnelle disponible' : 'Proposition indisponible — revue ou sources à compléter'}</strong></p>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      {c.sources_conservees.css && <p>CSS distincte : année {c.sources_conservees.css.controle.annee_css}, exercice fiscal de référence {c.sources_conservees.css.controle.exercice_reference_declare ?? 'À qualifier'}.</p>}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Document DGI publié par le CRI</a></p>
      <p>L’excédent arithmétique ne constitue pas un droit à remboursement ou report confirmé. Aucun total global IS+CSS, paiement ou liquidation définitive.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Proposer le solde IS/CM — 2026', titre: 'Revue du solde annuel proposé', region: 'Proposition IS CM de la préparation',
  lire: etatsAPI.preparationBalanceLiquidationIS, conserver: etatsAPI.conserverBalanceLiquidationIS, maxLignes: 1,
  libelleSelection: 'Revue fiscale à documenter', libelleChargement: 'Chargement de la proposition IS/CM…',
  libelleConserver: 'Conserver la proposition IS/CM dans une nouvelle version',
  noteNombres: 'Revoir les sources fiscales et leur cohérence. L’excédent antérieur demandé doit être explicite, même nul, et ne peut pas dépasser le restant justifié après acomptes.',
  options: (_d, _s, c) => ['b12_verifie', 'cm_verifiee', 'exhaustivite_verifiee', 'excedent_verifie', 'ordre_examine'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationLiquidationIS(props) { return <Tables {...props} configuration={CONFIG} /> }
