/** Le stock ne concerne que les articles physiques, jamais les services/frais. */
export function stockInsuffisantPourDevis(ligne) {
  if (!ligne?.article_id || ligne.is_stockable !== true) return false
  if (ligne.stock_actuel === null || ligne.stock_actuel === undefined) return false
  const disponible = Number(ligne.stock_actuel)
  const demande = Number(ligne.quantite)
  return Number.isFinite(disponible) && Number.isFinite(demande) && demande > disponible
}
