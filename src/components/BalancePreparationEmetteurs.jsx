import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const periode = code => code === 'B4-N' ? 'n' : 'n1'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

function Controle({ data, selection }) {
  const p = periode(selection), controle = data.controle_emetteurs?.periodes[p]
  return <section aria-label="Contrôles des émetteurs conservés" className={styles.detail}>
    <p>Comptes251 de cette source : {data.sources[p].comptes.join(', ') || 'aucun'}.</p>
    {!data.sources[p].disponible && <p>Source détaillée absente ou incomplète : période indisponible à la saisie.</p>}
    {!controle ? <p>Aucun contrôle conservé. Enregistrer les déclarations pour figer leur rapprochement.</p> : <>
      <p>Ces contrôles concernent la version conservée, pas les modifications du brouillon.</p>
      {controle.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      {!controle.disponible && <p>Contrôle indisponible : source détaillée absente ou incomplète.</p>}
      {controle.comptes.map(r => <div key={r.compte} className={styles.detail}>
        <h5>Compte {r.compte} · {r.lignes} ligne(s) déclarée(s)</h5>
        <p>Brut251 source : <strong>{argent(r.solde_brut_source)}</strong></p>
        <p>Somme brute déclarée : <strong>{argent(r.somme_brute_declaree)}</strong></p>
        <p>Écart déclaré moins source : <strong>{argent(r.ecart_brut)}</strong></p>
      </div>)}
    </>}
  </section>
}

const CONFIG = {
  resume: 'Documenter les émetteurs des participations', titre: 'Émetteurs déclarés des participations',
  region: 'Déclarations des émetteurs de la préparation',
  lire: etatsAPI.preparationBalanceEmetteurs, conserver: etatsAPI.conserverBalanceEmetteurs,
  autorise: (data, selection) => !!data?.sources?.[periode(selection)]?.disponible,
  options: (data, selection, c) => c.cle === 'compte' ? data.sources[periode(selection)].comptes : undefined,
  noteNombres: 'Valeur brute251 et produits reçus signés, deux décimales. Capital non négatif en MAD ; quote-part de0 à100, au plus douze décimales.',
  complement: (data, selection) => <Controle data={data} selection={selection} />,
}

export default function BalancePreparationEmetteurs(props) {
  return <Tables {...props} configuration={CONFIG} />
}
