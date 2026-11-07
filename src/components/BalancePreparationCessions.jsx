import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_cessions
  return <section aria-label="Contrôles des cessions conservés" className={styles.detail}>
    {!c ? <p>Aucun contrôle conservé. Enregistrer les déclarations pour figer leurs différences.</p> : <>
      <p>Ces contrôles concernent la version conservée, pas les modifications du brouillon.</p>
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      {c.lignes.map(r => <p key={r.ligne}>Ligne {r.ligne} · Différence prix moins VNA : <strong>{argent(r.difference_prix_vna)}</strong></p>)}
      <p>Total des différences connues seulement si toutes les lignes sont connues : <strong>{argent(c.total_difference_prix_vna)}</strong></p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Documenter les cessions et retraits d’immobilisations', titre: 'Cessions et retraits déclarés',
  region: 'Déclarations des cessions de la préparation',
  lire: etatsAPI.preparationBalanceCessions, conserver: etatsAPI.conserverBalanceCessions,
  placeholder: () => 'Choisir un type déclaré',
  options: (_data, _selection, c) => c.cle === 'type_sortie' ? ['cession', 'retrait', 'autre'] : undefined,
  noteNombres: 'Valeur d’entrée, VNA et prix déclarés en MAD, positifs ou nuls, deux décimales maximum. Leur différence peut être négative.',
  complement: data => <Controle data={data} />,
}
export default function BalancePreparationCessions(props) { return <Tables {...props} configuration={CONFIG} /> }
