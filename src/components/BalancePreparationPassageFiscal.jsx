import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_passage_fiscal
  return <section aria-label="Contrôles du passage fiscal conservés" className={styles.detail}>
    {!c ? <p>Aucun contrôle conservé. Enregistrer pour figer les sources et hypothèses.</p> : <>
      <p>Contrôles de la version conservée ; le brouillon ne les modifie pas.</p>
      {!c.disponible && <p role="note">{c.motif}</p>}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      {[
        ['resultat_net_comptable', 'Résultat net comptable'], ['impots_comptabilises_67', 'Impôts comptabilisés67'],
        ['resultat_avant_impots', 'Résultat avant impôts reconstitué'], ['autres_reintegrations', 'Autres réintégrations hors67'],
        ['reintegrations_depuis_net', 'Total des réintégrations depuis le net'], ['deductions', 'Déductions déclarées'],
        ['resultat_fiscal_avant_deficit', 'Résultat fiscal avant déficits'], ['deficit_disponible_declare', 'Déficit disponible déclaré'],
        ['deficit_impute_propose', 'Déficit imputé proposé'], ['deficit_restant', 'Déficit disponible restant'],
        ['deficit_genere', 'Déficit généré indicatif'], ['benefice_fiscal_propose', 'Bénéfice fiscal proposé'],
        ['is_theorique_taux_declare', 'IS théorique selon taux déclaré'],
      ].map(([k,label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      <p>Taux IS déclaré : <strong>{c.montants.taux_is_declare == null ? 'Indisponible' : `${c.montants.taux_is_declare} %`}</strong></p>
      <p>À compléter : {c.a_completer.join(' ; ')}. Solde final : Indisponible.</p>
      <p>L’IS théorique affiché ne constitue pas le montant à payer.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Préparer le passage fiscal B12 depuis la balance', titre: 'Passage fiscal et IS selon taux déclaré',
  region: 'Passage fiscal de la préparation', lire: etatsAPI.preparationBalancePassageFiscal,
  conserver: etatsAPI.conserverBalancePassageFiscal, maxLignes: 1,
  autorise: data => !!data?.sources?.n?.disponible,
  noteNombres: 'Une synthèse sourcée. Montants positifs ou nuls à deux décimales ; taux de0 à100, trois décimales. Aucun déficit ou taux inconnu remplacé par0.',
  complement: data => <Controle data={data} />,
}
export default function BalancePreparationPassageFiscal(props) {
  return <Tables {...props} configuration={CONFIG} />
}
