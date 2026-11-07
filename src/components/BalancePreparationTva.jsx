import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
const LIBELLES = { solde_debut_declare: 'Solde de début déclaré', operations_declarees: 'Opérations déclarées', declarations_declarees: 'Déclarations justifiées', solde_fin_reconstitue: 'Solde de fin reconstitué', solde_fin_balance_n: 'Solde de fin balance N', solde_fin_balance_n1_memoire: 'Solde de fin N-1 pour mémoire', ecart_fin: 'Écart fin reconstituée moins balance N' }
function Controle({ data }) {
  const c = data.controle_tva
  return <section aria-label="Contrôles TVA conservés" className={styles.detail}>
    {!c ? <p>Aucun contrôle conservé. Enregistrer pour figer sources et flux déclarés.</p> : <>
      <p>Contrôles de la version conservée ; le brouillon ne les modifie pas. N-1 reste pour mémoire et ne préremplit pas le début N.</p>
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      {c.lignes.map(r => <section aria-label={r.titre} key={r.famille} className={styles.detail}>
        <h4>{r.titre}</h4>
        {Object.entries(LIBELLES).map(([k,label]) => <p key={k}>{label} : <strong>{argent(r.montants[k])}</strong></p>)}
        {r.references_declarations && <p>Références des déclarations : {r.references_declarations}</p>}
        {r.reference_source && <p>Référence de source : {r.reference_source}</p>}
      </section>)}
      <p>Aucun dépôt confirmé, aucune liquidation ou paiement déduit.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Documenter les flux TVA B14 depuis les balances', titre: 'Flux et soldes TVA documentaires',
  region: 'TVA documentaire de la préparation', lire: etatsAPI.preparationBalanceTva,
  conserver: etatsAPI.conserverBalanceTva, maxLignes: 3,
  autorise: data => !!data?.sources?.n?.disponible,
  options: (_data, _selection, c) => c.cle === 'nature' ? ['4455','34552','34551'] : null,
  placeholder: () => 'Choisir une famille TVA',
  noteNombres: 'Montants signés à deux décimales. Une ligne par famille :4455 collectée ;34552 récupérable sur charges ;34551 sur immobilisations. Références requises, même pour zéro. Aucun flux déduit de N-1.',
  complement: data => <Controle data={data} />,
}
export default function BalancePreparationTva(props) { return <Tables {...props} configuration={CONFIG} /> }
