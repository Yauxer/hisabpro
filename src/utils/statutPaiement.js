// Le règlement commercial par chèque/effet ne prouve pas son encaissement.
export function statutPaiementAffiche(facture) {
  const enCours = Number(facture.total_reglement_en_cours || 0)
  return facture.statut === 'payee' && Number.isFinite(enCours) && enCours > 0
    ? 'reglement_en_cours'
    : facture.statut
}
