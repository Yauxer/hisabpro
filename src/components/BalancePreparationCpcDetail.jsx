import Detail from './BalancePreparationDetailAutomatique.jsx'

const configuration = {
  charger: 'preparationBalanceCpcDetail', conserver: 'conserverBalanceCpcDetail',
  resume: 'Détailler le CPC depuis les balances conservées', region: 'Détail CPC de la préparation',
  titre: 'Détail CPC', chargement: 'Chargement du détail CPC…', relire: 'Relire le détail CPC conservé',
  absent: 'Aucun détail CPC conservé dans cette version. Conserver une nouvelle version pour figer le calcul depuis ses sources.',
  periode: 'Période du détail CPC', reference: 'CPC figé', prefixe: 'cpc_',
  indicateurs: [['charges', 'Charges'], ['produits', 'Produits'], ['resultat', 'Résultat']],
  aucun: 'Aucun solde non nul des classes 6 et 7 dans cette source.',
  bouton: 'Conserver le détail CPC dans une nouvelle version',
}
export default function BalancePreparationCpcDetail(props) {
  return <Detail {...props} configuration={configuration} />
}
