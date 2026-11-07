import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const CHAMPS = [['effectif_moyen','Effectif moyen déclaré','personnes'],['benefices_distribues','Bénéfices distribués déclarés','MAD'],['resultat_par_titre','Résultat par titre déclaré','MAD / titre'],['distribution_par_titre','Distribution par titre déclarée','MAD / titre']]
function Controle({ data, selection }) {
  const p = {'C3-N':'n','C3-N1':'n1','C3-N2':'n2'}[selection]
  const r = data.declarations_c3?.[p]
  return <section aria-label="Déclarations C3 conservées" className={styles.detail}>
    {!r ? <p>Aucune déclaration extra-comptable conservée pour cette période.</p> : <>
      <p>Déclarations de la version conservée ; le brouillon ne les modifie pas.</p>
      {CHAMPS.map(([k,label,unite]) => <p key={k}>{label} : <strong>{r[k] == null ? 'Indisponible' : `${montantDecimalExact(r[k])} ${unite}`}</strong></p>)}
      <p>Référence : {r.reference_source || 'À documenter'}</p>
      <p>Décisions et affectations : {r.affectations_justifiees || 'À documenter'}</p>
      <p>Conserver les indicateurs C3 dans une nouvelle version pour inclure ces déclarations.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Documenter les données extra-comptables C3',titre: 'Déclarations extra-comptables C3 sourcées',
  region: 'Données extra-comptables C3 de la préparation',lire: etatsAPI.preparationBalanceC3Extra,
  conserver: etatsAPI.conserverBalanceC3Extra,maxLignes:1,
  noteNombres:'Une synthèse par période, deux décimales maximum. Effectif en personnes ; résultat par titre signé. Aucun montant par titre ou effectif calculé depuis le net, le capital ou la paie.',
  complement:(data,selection)=><Controle data={data} selection={selection} />,
}
export default function BalancePreparationC3Extra(props) { return <Tables {...props} configuration={CONFIG} /> }
