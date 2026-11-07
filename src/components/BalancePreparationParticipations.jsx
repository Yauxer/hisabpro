import Detail from './BalancePreparationDetailAutomatique.jsx'
const configuration = {
  charger: 'preparationBalanceParticipations', conserver: 'conserverBalanceParticipations',
  resume: 'Détailler les titres de participation depuis les balances conservées', region: 'Participations de la préparation',
  titre: 'Titres de participation', chargement: 'Chargement des participations…', relire: 'Relire les participations conservées',
  absent: 'Aucun détail des participations conservé dans cette version. Conserver une nouvelle version pour figer le calcul depuis ses sources.',
  periode: 'Période des participations', reference: 'bilan figé24/25', prefixe: 'bilan_',
  indicateurs: [['participations', 'Soldes des titres251', false], ['autres_financieres', 'Autres soldes financiers24/25', false], ['financieres_brut', 'Brut financier entier24/25']],
  aucun: 'Aucun solde non nul des comptes251 dans cette source ; les informations extra-comptables restent à documenter.',
  bouton: 'Conserver les participations dans une nouvelle version',
}
export default function BalancePreparationParticipations(props) {
  return <Detail {...props} configuration={configuration} />
}
