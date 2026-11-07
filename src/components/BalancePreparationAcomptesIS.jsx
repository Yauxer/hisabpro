import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
const LIBELLES = {
  versements_declares: 'Versements effectifs déclarés', excedent_anterieur_impute: 'Excédent antérieur affecté aux acomptes',
  retenues_affectees: 'Retenues affectées aux acomptes', excedent_anterieur_disponible: 'Excédent antérieur disponible avant affectations',
  excedent_anterieur_restant: 'Excédent antérieur restant après affectations', ecart_retenues: 'Écart retenues affectées moins déjà utilisées côté crédits',
  acomptes_proposes: 'Acomptes imputables proposés après qualifications', total_echeances_calcule: 'Total des échéances calculées',
  ecart_arrondi_reference: 'Écart total échéances moins référence annuelle',
}
const STATUTS = { a_qualifier: 'À qualifier', couvert_declare: 'Couvert selon justificatifs déclarés', partiel_en_retard: 'Partiel — en retard',
  en_retard: 'En retard', partiel: 'Partiel', a_venir: 'À venir' }
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`
function Controle({ data }) {
  const c = data.controle_acomptes
  return <section aria-label="Contrôles acomptes IS conservés" className={styles.detail}>
    {!c ? <p>Aucune qualification acomptes conservée. La saisie reste un brouillon.</p> : <>
      <p>Période source : {c.periode_source.debut} au {c.periode_source.fin} · Date de contrôle déclarée : {c.date_controle || 'À qualifier'}</p>
      {Object.entries(LIBELLES).map(([k, label]) => <p key={k}>{label} : <strong>{argent(c.montants[k])}</strong></p>)}
      <section aria-label="Rapprochement des retenues affectées" className={styles.detail}>
        <h4>Retenues rapprochées par justificatif</h4>
        {c.rapprochement_retenues.map(r => <p key={r.reference}>{r.reference} · Déjà utilisé côté crédits : {argent(r.attendu)} · Affecté aux acomptes : {argent(r.affecte)} · {r.coherent ? 'Cohérent' : 'À revoir'}</p>)}
      </section>
      <section aria-label="Échéancier déclaré des acomptes IS" className={styles.detail}>
        <h4>Échéancier selon la référence qualifiée</h4>
        {!c.calendrier_disponible && <p>Calendrier à qualifier ; les versements ne sont pas déduits des échéances.</p>}
        {c.echeancier.map(r => <p key={r.numero}>Acompte {r.numero} · {r.date_echeance} · Dû : {argent(r.du)} · Couverture déclarée : {argent(r.couverture_declaree)} · Reste : {argent(r.reste)} · <strong>{STATUTS[r.statut] || 'À qualifier'}</strong></p>)}
      </section>
      {c.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      <p>{c.reference_juridique.titre}, pages {c.reference_juridique.pages_imprimees}. <a href={c.reference_juridique.notice_url} target="_blank" rel="noreferrer">Document DGI publié par le CRI</a></p>
      <p>Aucun paiement, affectation ou liquidation confirmé. CSS distincte.</p>
    </>}
  </section>
}
const CONFIG = {
  resume: 'Qualifier les acomptes IS — 2026', titre: 'Versements et affectations des acomptes', region: 'Acomptes IS de la préparation',
  lire: etatsAPI.preparationBalanceAcomptesIS, conserver: etatsAPI.conserverBalanceAcomptesIS,
  maxLignes: code => code === 'AP-PROFIL' ? 1 : 50,
  libelleSelection: 'Qualification acomptes à documenter', libelleChargement: 'Chargement des acomptes IS…',
  libelleConserver: 'Conserver les acomptes IS dans une nouvelle version',
  noteNombres: 'Référence annuelle ajustée2026 et justificatifs à vérifier ; affectations déclarées exactement, jamais réparties automatiquement. Une référence de retenue doit désigner son justificatif crédits.',
  options: (_d, _s, c) => c.cle === 'regime' ? ['Société relevant de l’IS'] : c.cle === 'mode'
    ? ['Quatre acomptes — exercice de douze mois', 'Minimum CM3000 — versement unique'] : c.cle === 'numero' ? ['1', '2', '3', '4']
    : ['reference_qualifiee', 'dernier_clos_confirme', 'excedent_qualifie', 'exhaustivite', 'absence_mouvements', 'rattachement_confirme'].includes(c.cle) ? ['oui', 'non'] : null,
  placeholder: () => 'À qualifier', complement: data => <Controle data={data} />,
}
export default function BalancePreparationAcomptesIS(props) { return <Tables {...props} configuration={CONFIG} /> }
