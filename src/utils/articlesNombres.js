// Les valeurs numériques absentes ne représentent jamais un zéro connu.
export const nombreArticleConnu = valeur => typeof valeur === 'number' && Number.isFinite(valeur) && valeur >= 0
export const nombreArticleSaisie = valeur => nombreArticleConnu(valeur) ? valeur : ''
export const nombreSaisieConnu = valeur => (typeof valeur === 'number' || (typeof valeur === 'string' && /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(valeur.trim()))) && Number.isFinite(Number(valeur)) && Number(valeur) >= 0
export const qualificationArticle = taux => nombreArticleConnu(taux) ? (taux === 0 ? 'exonere_sans_deduction' : 'taxable') : ''
export const montantArticle = (valeur, formatter) => nombreArticleConnu(valeur) ? formatter(valeur) : 'À vérifier'
export const margeArticle = article => nombreArticleConnu(article.prix_vente_ht) && nombreArticleConnu(article.prix_achat_ht) ? article.prix_vente_ht - article.prix_achat_ht : null
export const montantLignesSaisies = (valeur, lignes, formatter) => !Number.isFinite(valeur) || lignes.some(l => (l.description || '').trim() && (!nombreSaisieConnu(l.prix_unitaire) || !nombreSaisieConnu(l.tva))) ? 'À vérifier' : formatter(valeur)
