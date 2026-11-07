import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const LIBELLES = {
  cm_declaree: 'CM déclarée', css_declaree: 'CSS déclarée séparément',
  credits_total: 'Total des crédits déclarés',
  credits_deja_imputes: 'Crédits déjà imputés déclarés côté crédits',
  credits_restants: 'Crédits déclarés moins part déjà imputée',
  acomptes_verses: 'Acomptes effectivement versés déclarés',
  credit_anterieur_impute: 'Crédits antérieurs imputés déclarés',
  imputations_sur_acomptes: 'Crédits déjà imputés déclarés côté acomptes',
  ecart_imputations: 'Écart imputations côté acomptes moins côté crédits',
}
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

function Controle({ data }) {
  const c = data.controle_contexte_fiscal
  return <section aria-label="Contrôles du contexte fiscal conservés" className={styles.detail}>
    {!c ? <p>Aucun contexte conservé. Les données saisies restent un brouillon.</p> : <>
      <p>Totaux des seules lignes conservées ; exhaustivité et éligibilité à vérifier.</p>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>IS théorique B12 pour mémoire : <strong>{argent(c.source_b12?.is_theorique_taux_declare)}</strong></p>
      <p>Référence B12 conservée : {c.source_b12?.cle || 'Absente'}</p>
      <p>Impôt dû et solde final : Indisponibles. CSS séparée, aucune liquidation ni paiement confirmé.</p>
    </>}
  </section>
}

const CONFIG = {
  resume: 'Documenter CM, CSS, crédits et acomptes', titre: 'Contexte fiscal documentaire',
  region: 'Contexte fiscal de la préparation', lire: etatsAPI.preparationBalanceContexteFiscal,
  conserver: etatsAPI.conserverBalanceContexteFiscal,
  maxLignes: selection => ({ 'CF-CM': 1, 'CF-CSS': 1, 'CF-CREDITS': 50, 'CF-ACOMPTES': 20 }[selection] || 0),
  libelleSelection: 'Rubrique du contexte fiscal',
  libelleChargement: 'Chargement du contexte fiscal…',
  libelleConserver: 'Conserver le contexte fiscal dans une nouvelle version',
  noteNombres: 'Montants positifs ou nuls à deux décimales. Références justificatives requises ; versements et crédits déjà imputés restent distincts. Aucun solde fiscal calculé.',
  complement: data => <Controle data={data} />,
}

export default function BalancePreparationContexteFiscal(props) {
  return <Tables {...props} configuration={CONFIG} />
}
