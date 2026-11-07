import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const NORMAL = 'Établissement avec local — hors régime particulier, exonération et réduction'
const LABELS = { valeur_locative_totale: 'Valeurs locatives saisies', brut_arithmetique: 'Somme des simulations brutes au centime', brut_propose: 'Brut simulé après revue documentaire déclarée', avis_comparables: 'Avis saisis et rattachés explicitement', ecart_brut_avis: 'Écart brut simulé moins avis déclarés' }
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
 const c = data.controle_tp
 return <section aria-label="Contrôles de préparation TP" className={styles.detail}>
  {!c ? <p>Aucune simulation TP conservée. La saisie reste un brouillon.</p> : <>
   <p>Année TP déclarée : {c.annee_tp_declaree || 'À qualifier'}</p>
   <p>{c.revue_documentaire_declaree ? 'Revue documentaire déclarée — imposition à vérifier' : 'Préparation TP à compléter ou à qualifier'}</p>
   {Object.entries(LABELS).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
   {c.etablissements.map(e => <div key={e.etablissement_ref} className={styles.detail}><p>{e.etablissement_ref} · {e.nom} · {e.classe || 'Classe à qualifier'}</p><p>Brut arithmétique : {argent(e.brut_arithmetique)}</p><p>Écart avec avis déclaré : {argent(e.ecart_avis)}</p>{e.points_a_revoir.length > 0 && <p>À revoir : {e.points_a_revoir.join(', ')}</p>}</div>)}
   {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
   <p>{c.reference_juridique.titre}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Références DGCT</a></p>
   <p>Aucun montant dû, émission, paiement ou dépôt confirmé. Les bases et classes restent à justifier.</p>
  </>}
 </section>
}
const CONFIG = {
 resume: 'Préparer la taxe professionnelle', titre: 'Taxe professionnelle — simulation interne', region: 'Taxe professionnelle de la préparation',
 lire: etatsAPI.preparationBalanceTaxeProfessionnelle, conserver: etatsAPI.conserverBalanceTaxeProfessionnelle,
 maxLignes: code => code === 'TP-P' ? 1 : 50,
 libelleSelection: 'Rubrique TP à documenter', libelleChargement: 'Chargement de la préparation TP…', libelleConserver: 'Conserver la préparation TP dans une nouvelle version',
 noteNombres: 'La VL annuelle et la classe viennent de pièces qualifiées ; aucun coût/loyer ou taux net d’amortissement ne les remplace. Le brut reste distinct du montant dû.',
 options: (_d, _s, c) => c.cle === 'classe' ? ['C3', 'C2', 'C1'] : c.cle === 'regime' ? [NORMAL, 'Situation particulière — à qualifier'] : ['periode_revue', 'exhaustivite', 'referentiel_revu', 'base_revue', 'classe_revue', 'situation_janvier_revue', 'avis_rattache'].includes(c.cle) ? ['oui', 'non'] : null,
 placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationTaxeProfessionnelle(props) { return <Tables {...props} configuration={CONFIG} /> }
