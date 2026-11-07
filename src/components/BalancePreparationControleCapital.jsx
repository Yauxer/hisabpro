import styles from './BalancePreparationDetail.module.css'

const valeur = (v, unite) => v == null ? 'Indisponible' : `${v} ${unite}`

export default function BalancePreparationControleCapital({ controle }) {
  return <details className={styles.detail}>
    <summary>Vérifier les données chiffrées du capital conservé</summary>
    <section aria-label="Contrôles arithmétiques du capital conservé" className={styles.detail}>
      {!controle ? <p>Aucun contrôle conservé dans cette version. Conserver les annexes dans une nouvelle version pour calculer les contrôles sur les données déclarées.</p> : <>
        <p>{controle.note}</p>
        <p>Ces contrôles concernent la version conservée, pas les modifications du brouillon.</p>
        <p>Somme des capitaux déclarés : <strong>{valeur(controle.somme_capital_declare, 'MAD')}</strong></p>
        <p>Capital des comptes 111 de la balance N : <strong>{valeur(controle.capital_balance_111, 'MAD')}</strong></p>
        <p>Écart capitaux déclarés moins balance 111 : <strong>{valeur(controle.ecart_capital_balance, 'MAD')}</strong></p>
        <p>Somme des pourcentages déclarés : <strong>{valeur(controle.somme_pourcentages, '%')}</strong></p>
        <p>Écart somme des pourcentages moins 100 : <strong>{valeur(controle.ecart_pourcentages_100, '%')}</strong></p>
        {controle.lignes.map(r => <div key={r.ligne} className={styles.detail}>
          <h5>Ligne {r.ligne} · {r.associe || 'Associé à compléter'}</h5>
          <p>Produit titres × nominal : <strong>{valeur(r.capital_calcule, 'MAD')}</strong></p>
          <p>Capital déclaré : <strong>{valeur(r.capital_declare, 'MAD')}</strong></p>
          <p>Écart capital déclaré moins produit : <strong>{valeur(r.ecart_capital, 'MAD')}</strong></p>
        </div>)}
      </>}
    </section>
  </details>
}
