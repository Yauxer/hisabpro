export function nombreInventaire(valeur) {
  if (typeof valeur !== 'number' && typeof valeur !== 'string') return null
  if (typeof valeur === 'string' && !valeur.trim()) return null
  const nombre = Number(valeur)
  return Number.isFinite(nombre) ? nombre : null
}

export function sourceInventaireConnue(article) {
  const cout = nombreInventaire(article.cmup)
  return nombreInventaire(article.stock_theorique) !== null && cout !== null && cout >= 0
}

export function ecartInventaire(article, valeur) {
  const reel = nombreInventaire(valeur)
  const theorie = nombreInventaire(article.stock_theorique)
  const cout = nombreInventaire(article.cmup)
  const difference = reel !== null && theorie !== null ? reel - theorie : null
  const ecart = Number.isFinite(difference) ? difference : null
  const montant = ecart !== null && cout !== null && cout >= 0 ? ecart * cout : null
  return { reel, ecart, valeur: Number.isFinite(montant) ? montant : null }
}

export function preparerLignesComptage(feuille, comptes, { complet = false } = {}) {
  const lignes = []
  for (const article of feuille) {
    const valeur = comptes[article.article_id]
    if (valeur !== undefined && valeur !== null && typeof valeur !== 'number' && typeof valeur !== 'string') {
      throw new Error(`Quantité invalide pour ${article.code || article.designation} : saisissez un nombre positif ou zéro.`)
    }
    if (valeur === undefined || valeur === null || String(valeur).trim() === '') {
      if (complet) {
        throw new Error(`Inventaire de clôture incomplet : renseignez la quantité de ${article.code || article.designation}.`)
      }
      continue
    }
    const quantite = nombreInventaire(valeur)
    if (quantite === null || quantite < 0) {
      throw new Error(`Quantité invalide pour ${article.code || article.designation} : saisissez un nombre positif ou zéro.`)
    }
    if (!sourceInventaireConnue(article) || ecartInventaire(article, quantite).valeur === null) {
      throw new Error(`À vérifier pour ${article.code || article.designation} : stock théorique ou coût moyen inconnu, invalide ou valeur non finie. Corrigez la source avant de simuler ou valider.`)
    }
    lignes.push({ article_id: article.article_id, quantite_reelle: quantite })
  }
  if (!lignes.length) throw new Error('Aucune ligne de comptage renseignée.')
  return lignes
}
