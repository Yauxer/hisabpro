import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const LIBELLES = {
  base_comptable_brute: 'Base CM comptable brute', base_exclue: 'Exclusions déclarées et justifiées',
  base_apres_exclusion: 'Base après exclusions', base_taux_reduit_015: 'Base déclarée au taux réduit 0,15 %',
  base_taux_standard_025: 'Base au taux standard 0,25 %', cm_part_standard: 'CM proportionnelle standard',
  cm_part_reduite: 'CM proportionnelle réduite', cm_calculee: 'CM proportionnelle totale',
  minimum_3000: 'Minimum de perception retenu', cm_exigible: 'CM proposée selon qualifications déclarées',
  is_theorique_b12: 'IS théorique B12 selon taux déclaré',
  impot_avant_imputations_propose: 'Maximum IS théorique / CM proposé avant imputations',
}
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

function Controle({ data }) {
  const c = data.controle_cm
  return <section aria-label="Contrôles CM conservés" className={styles.detail}>
    {!c ? <p>Aucun calcul CM conservé. Les paramètres saisis restent un brouillon.</p> : <>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>Référence B12 conservée : {c.source_b12?.cle || 'Absente'}</p>
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Document DGI publié par le CRI</a></p>
      <p>Solde final : Indisponible. Aucun paiement ni liquidation confirmé ; CSS et crédits distincts.</p>
      <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Comptes sources de la CM">
        <table className={styles.sources}><thead><tr><th>Compte</th><th>Solde créditeur net MAD</th><th>Base comptable CM</th></tr></thead>
          <tbody>{c.lignes_sources.map(r => <tr key={r.compte}><th scope="row">{r.compte}</th><td>{argent(r.montant)}</td><td style={{ whiteSpace: 'normal', textAlign: 'left' }}>{r.retenu_base ? 'Retenu' : 'Hors base'} · {r.famille}</td></tr>)}</tbody>
        </table>
      </div>
    </>}
  </section>
}

const CONFIG = {
  resume: 'Calculer la cotisation minimale — 2026', titre: 'Cotisation minimale sur balance conservée',
  region: 'Cotisation minimale de la préparation', lire: etatsAPI.preparationBalanceCotisationMinimale,
  conserver: etatsAPI.conserverBalanceCotisationMinimale, maxLignes: 1,
  libelleSelection: 'Qualification CM à documenter', libelleChargement: 'Chargement de la cotisation minimale…',
  libelleConserver: 'Conserver le calcul CM dans une nouvelle version',
  noteNombres: 'Exclusions et base réduite à justifier. Choisir explicitement le périmètre et oui/non pour les exonérations ; une sélection vide reste à qualifier.',
  options: (_data, _selection, c) => c.cle === 'regime' ? ['IS hors forfait non-résident'] : ['exoneration_totale', 'minimum_exonere'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationCotisationMinimale(props) { return <Tables {...props} configuration={CONFIG} /> }
