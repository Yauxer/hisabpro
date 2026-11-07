import Detail from './BalancePreparationDetailAutomatique.jsx'
const configuration = {
  charger: 'preparationBalanceIndicateurs', conserver: 'conserverBalanceIndicateurs',
  resume: 'Consulter les indicateurs comptables C3 depuis les balances', region: 'Indicateurs C3 de la préparation',
  titre: 'Indicateurs comptables et historiques disponibles', chargement: 'Chargement des indicateurs…',
  relire: 'Relire les indicateurs conservés',
  absent: 'Aucun indicateur C3 conservé dans cette version. Conserver une nouvelle version pour figer ses sources et ses indisponibilités.',
  periode: 'Période des indicateurs', periodes: [['n', 'N'], ['n1', 'N-1'], ['n2', 'N-2']],
  reference: 'états figés', prefixe: 'reference_',
  indicateurs: [['situation_nette', 'Situation nette'], ['chiffre_affaires_ht', 'Chiffre d’affaires711/712', false],
    ['resultat_avant_impots', 'Résultat avant impôts'], ['impots_resultats', 'Impôts comptabilisés'],
    ['resultat_net', 'Résultat net comptable'], ['salaires_bruts', 'Rémunérations comptabilisées6171', false]],
  extraIndicateurs: [['effectif_moyen','Effectif moyen déclaré','personnes'], ['benefices_distribues','Bénéfices distribués déclarés','MAD'], ['resultat_par_titre','Résultat par titre déclaré','MAD / titre'], ['distribution_par_titre','Distribution par titre déclarée','MAD / titre']],
  aucun: 'Aucun solde non nul du périmètre C3 dans cette source.',
  bouton: 'Conserver les indicateurs C3 dans une nouvelle version',
}
export default function BalancePreparationIndicateurs(props) {
  const source = props.dossier.contenu.comparatif_n2_documentaire
  const incluse = props.dossier.contenu.indicateurs_comptables_documentaires?.vue?.provenance_n2
  const extra = props.dossier.contenu.extra_c3_documentaire
  const extraIncluse = props.dossier.contenu.indicateurs_comptables_documentaires?.vue?.provenance_extra_c3
  return <><Detail {...props} configuration={configuration} />
    {extra && extra.cle !== extraIncluse?.cle && <p role="note">Un complément extra-comptable C3 est conservé. Conservez une nouvelle version des indicateurs C3 pour l’inclure ; l’ancien contrôle reste inchangé.</p>}
    {source && source.cle !== incluse?.cle && <p role="note">Une source N-2 est rattachée. Conservez une nouvelle version des indicateurs C3 pour l’inclure ; le contrôle C3 déjà conservé reste inchangé.</p>}
  </>
}
