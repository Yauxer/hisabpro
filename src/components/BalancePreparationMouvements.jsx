import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data, selection }) {
  const c = data.controle_mouvements?.tableaux[selection]
  return <section aria-label="Contrôles des mouvements conservés" className={styles.detail}>
    {!c ? <p>Aucun contrôle conservé. Enregistrer les mouvements pour figer leurs contrôles.</p> : <>
      <p>Ces contrôles concernent la version conservée, pas les modifications du brouillon.</p>
      {c.lignes.map(r => <div className={styles.detail} key={r.ligne}><h5>Ligne {r.ligne}</h5>
        <p>Clôture reconstituée : <strong>{argent(r.fin_reconstituee)}</strong></p>
        <p>Clôture déclarée : <strong>{argent(r.fin_declaree)}</strong></p>
        <p>Écart déclaré moins reconstitué : <strong>{argent(r.ecart_fin)}</strong></p>
      </div>)}
      <p>Total des écarts, disponible seulement si toutes les lignes sont connues : <strong>{argent(c.totaux.ecart_fin)}</strong></p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Documenter les mouvements d’immobilisations et provisions',titre: 'Mouvements B2, B2bis et B5 déclarés',
  region: 'Déclarations des mouvements de la préparation',
  lire: etatsAPI.preparationBalanceMouvements,conserver: etatsAPI.conserverBalanceMouvements,
  noteNombres: 'Ouverture et clôture signées ; augmentations et diminutions non négatives. Montants MAD à deux décimales maximum, inconnus distincts de zéro.',
  complement: (data, selection) => <Controle data={data} selection={selection} />,
}
export default function BalancePreparationMouvements(props) { return <Tables {...props} configuration={CONFIG} /> }
