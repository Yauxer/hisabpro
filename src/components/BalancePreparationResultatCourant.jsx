import Tables from './BalancePreparationEticTables.jsx'
import { etatsAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'

const periode = code => code === 'B13-N' ? 'n' : 'n1'
const argent = v => v == null ? 'Indisponible' : `${montantDecimalExact(v)} MAD`

function Controle({ data, selection }) {
  const detail = data.controle_resultat_courant?.periodes[periode(selection)]
  return <section aria-label="Contrôles du résultat courant conservés" className={styles.detail}>
    {!detail ? <p>Aucun contrôle conservé. Enregistrer pour figer les sources et les déclarations.</p> : <>
      <p>Contrôles de la version conservée ; le brouillon ne les modifie pas.</p>
      {!detail.disponible && <p role="note">{detail.motif}</p>}
      {detail.alertes.map(a => <p role="status" key={a}>{a}</p>)}
      {[
        ['resultat_courant', 'Résultat courant source71/73 −61/63'],
        ['cpc_resultat_courant', 'Résultat courant CPC VII figé'],
        ['ecart_courant', 'Écart source moins CPC VII'],
        ['impots_comptabilises_67', 'Impôts comptabilisés67 — pour mémoire'],
        ['reintegrations', 'Réintégrations courantes déclarées'],
        ['deductions', 'Déductions courantes déclarées'],
        ['base_courante_documentaire', 'Base courante documentaire'],
        ['impot_theorique_declare', 'Impôt théorique courant déclaré'],
        ['courant_apres_impot_declare', 'Courant après impôt déclaré'],
      ].map(([k, label]) => <p key={k}>{label} : <strong>{argent(detail[k])}</strong></p>)}
      <div className={styles.tableWrap}><table className={styles.sources}>
        <thead><tr><th>Compte source</th><th>Nature</th><th>Solde signé MAD</th></tr></thead>
        <tbody>{detail.lignes.map(r => <tr key={r.compte}><th>{r.compte}<small style={{ display: 'block' }}>Libellé non conservé</small></th><td>{r.nature}</td><td>{argent(r.montant)}</td></tr>)}</tbody>
      </table></div>
    </>}
  </section>
}

const CONFIG = {
  resume: 'Documenter le résultat courant B13 depuis les balances', titre: 'Résultat courant et hypothèses documentaires',
  region: 'Résultat courant de la préparation',
  lire: etatsAPI.preparationBalanceResultatCourant, conserver: etatsAPI.conserverBalanceResultatCourant,
  autorise: (data, selection) => !!data?.sources?.[periode(selection)]?.disponible,
  maxLignes: 1,
  noteNombres: 'Une synthèse sourcée par période. Montants déclarés positifs ou nuls à deux décimales. Aucun taux ni impôt déduit du compte67.',
  complement: (data, selection) => <Controle data={data} selection={selection} />,
}

export default function BalancePreparationResultatCourant(props) {
  return <Tables {...props} configuration={CONFIG} />
}
