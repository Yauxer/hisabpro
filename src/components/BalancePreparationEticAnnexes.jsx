import BalancePreparationControleCapital from './BalancePreparationControleCapital.jsx'
import BalancePreparationEticTables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'

const CONFIG = {
  resume: 'Documenter les autres annexes ETIC',
  titre: 'Annexes ETIC documentaires',
  noteNombres: 'Montants MAD positifs ou nuls : deux décimales ; titres : entiers ; pourcentages : au plus douze décimales.',
  region: 'Annexes documentaires ETIC de la préparation',
  lire: etatsAPI.preparationBalanceAnnexesEtic,
  complement: (data, selection) => selection === 'C1' ? <BalancePreparationControleCapital controle={data.controle_capital} /> : null,
  conserver: etatsAPI.conserverBalanceAnnexesEtic,
}

export default function BalancePreparationEticAnnexes(props) {
  return <BalancePreparationEticTables {...props} configuration={CONFIG} />
}
