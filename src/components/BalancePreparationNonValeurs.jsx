import Detail from './BalancePreparationDetailAutomatique.jsx'

const configuration = {
  charger: 'preparationBalanceNonValeurs', conserver: 'conserverBalanceNonValeurs',
  resume: 'Détailler les non-valeurs depuis les balances conservées', region: 'Non-valeurs de la préparation',
  titre: 'Détail des non-valeurs', chargement: 'Chargement des non-valeurs…', relire: 'Relire les non-valeurs conservées',
  absent: 'Aucun détail des non-valeurs conservé dans cette version. Conserver une nouvelle version pour figer le calcul depuis ses sources.',
  periode: 'Période des non-valeurs', reference: 'bilan figé', prefixe: 'bilan_',
  indicateurs: [['brut', 'Brut des comptes21'], ['amortissements', 'Amortissements groupés281'], ['net', 'Net des non-valeurs']],
  aucun: 'Aucun solde non nul des comptes21 et281 dans cette source.',
  bouton: 'Conserver les non-valeurs dans une nouvelle version',
}
export default function BalancePreparationNonValeurs(props) {
  return <Detail {...props} configuration={configuration} />
}
