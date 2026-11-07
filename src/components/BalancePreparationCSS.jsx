import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const LIBELLES = {
  benefice_reference: 'Bénéfice net fiscal de référence déclaré', css_proposee: 'CSS proposée selon qualifications déclarées',
  css_declaree_contexte: 'CSS déclarée dans le contexte fiscal conservé', ecart_css_declaree: 'Écart CSS proposée moins CSS déclarée',
}
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
const pourcentage = v => v == null ? 'Indisponible' : /^\d+\.\d{3}$/.test(v) ? `${v.replace('.', ',')} %` : 'À vérifier'
function Controle({ data }) {
  const c = data.controle_css
  return <section aria-label="Contrôles CSS conservés" className={styles.detail}>
    {!c ? <p>Aucune qualification CSS conservée. Les données saisies restent un brouillon.</p> : <>
      <p>Année CSS : {c.annee_css} · Exercice fiscal de référence déclaré : {c.exercice_reference_declare ?? 'À qualifier'}</p>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      <p>Taux proportionnel : <strong>{pourcentage(c.taux_proportionnel)}</strong></p>
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>Référence du contexte fiscal conservée : {c.source_contexte_fiscal?.cle || 'Absente'}</p>
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Document DGI publié par le CRI</a></p>
      <p>CSS distincte de l’IS/CM. Échéance à qualifier depuis la clôture source ; aucun paiement ni liquidation confirmé.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Calculer la CSS — 2026', titre: 'CSS sur bénéfice fiscal de référence déclaré', region: 'CSS de la préparation',
  lire: etatsAPI.preparationBalanceCSS, conserver: etatsAPI.conserverBalanceCSS, maxLignes: 1,
  libelleSelection: 'Qualification CSS à documenter', libelleChargement: 'Chargement de la CSS…',
  libelleConserver: 'Conserver le calcul CSS dans une nouvelle version',
  noteNombres: 'Bénéfice fiscal du dernier exercice clos à justifier ; jamais le résultat comptable N repris automatiquement. Exercice, source et exonération permanente à qualifier explicitement.',
  options: (_d, _s, c) => c.cle === 'regime' ? ['Société relevant de l’IS'] : ['dernier_clos_confirme', 'exoneration_permanente'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationCSS(props) { return <Tables {...props} configuration={CONFIG} /> }
