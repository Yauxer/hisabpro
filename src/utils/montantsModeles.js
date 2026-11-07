// Calcul des modèles simples : mêmes règles pour la saisie et la proposition.
// L'appelant conserve le contrôle des modèles complexes non automatisables.
export function calculerMontantsModele(modele, ligneSource, montant) {
  if (!ligneSource || !Number.isFinite(montant)) return null
  const lignes = modele?.lignes || []
  const principale = lignes.find(l => l.est_principal)
  if (!principale) return null
  const ligneTVA = lignes.find(l => l.est_tva)
  const tauxTVA = ligneTVA ? ligneTVA.taux_tva : 0
  if (!Number.isFinite(tauxTVA) || tauxTVA < 0 || tauxTVA > 100) return null
  if (!ligneTVA || tauxTVA <= 0) {
    return { montantHT: montant, montantTVA: 0, montantTTC: montant }
  }
  const estVente = principale.compte.startsWith('3421')
  let montantHT, montantTVA, montantTTC
  if (ligneSource.est_principal) {
    if (estVente) {
      montantTTC = montant
      montantHT = montantTTC / (1 + tauxTVA / 100)
    } else {
      montantHT = montant
      montantTTC = montantHT * (1 + tauxTVA / 100)
    }
    montantTVA = montantTTC - montantHT
  } else if (ligneSource.est_tva) {
    montantTVA = montant
    montantHT = montantTVA / (tauxTVA / 100)
    montantTTC = montantHT + montantTVA
  } else if (estVente) {
    montantHT = montant
    montantTVA = montantHT * tauxTVA / 100
    montantTTC = montantHT + montantTVA
  } else {
    montantTTC = montant
    montantHT = montantTTC / (1 + tauxTVA / 100)
    montantTVA = montantTTC - montantHT
  }
  if (![montantHT, montantTVA, montantTTC].every(Number.isFinite)) return null
  return { montantHT, montantTVA, montantTTC }
}

export function montantLigneModele(modele, ligne, montants) {
  if (ligne.est_tva) return montants.montantTVA
  const estVente = modele.lignes.find(l => l.est_principal)?.compte.startsWith('3421')
  if (ligne.est_principal) return estVente ? montants.montantTTC : montants.montantHT
  return estVente ? montants.montantHT : montants.montantTTC
}

// Changer un taux conserve la base HT, y compris quand la principale est3421(TTC).
export function recalculerTauxModele(modele, montantPrincipal, nouveauTaux) {
  if (!Number.isFinite(nouveauTaux) || nouveauTaux < 0 || nouveauTaux > 100) return null
  const principale = modele?.lignes?.find(l => l.est_principal)
  if (!principale || !modele.lignes.some(l => l.est_tva)) return null
  const anciens = calculerMontantsModele(modele, principale, montantPrincipal)
  if (!anciens) return null
  const nouveauModele = { ...modele, lignes: modele.lignes.map(l => l.est_tva ? { ...l, taux_tva: nouveauTaux } : { ...l }) }
  const sourceHT = principale.compte.startsWith('3421')
    ? nouveauModele.lignes.find(l => !l.est_principal && !l.est_tva)
    : nouveauModele.lignes.find(l => l.est_principal)
  const montants = calculerMontantsModele(nouveauModele, sourceHT, anciens.montantHT)
  return montants ? { modele: nouveauModele, montants } : null
}
