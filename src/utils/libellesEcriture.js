// Le libellé de ligne est initialisé depuis le plan de la société active.
// Un compte collectif conserve au contraire la sélection explicite du tiers.
export function initialiserLibelleLigne(ligne, trouverCompte, natureCompteTiers) {
  const libelleCompte = trouverCompte(ligne.compte)?.libelle || ''
  const estTiers = Boolean(natureCompteTiers(ligne.compte))
  const libelle = ligne.libelle || (estTiers ? '' : libelleCompte)
  return {
    ...ligne,
    libelle,
    libelle_personnalise: !estTiers && Boolean(ligne.libelle && ligne.libelle !== libelleCompte),
  }
}

export function synchroniserLibelleCompte(ligne, numero, trouverCompte, natureCompteTiers) {
  if (numero === ligne.compte) return ligne
  const ancienneNature = natureCompteTiers(ligne.compte)
  const nouvelleNature = natureCompteTiers(numero)
  const tiersConserve = Boolean(nouvelleNature && ancienneNature === nouvelleNature)
  return {
    ...ligne,
    compte: numero,
    libelle: nouvelleNature
      ? (tiersConserve ? ligne.libelle : '')
      : (trouverCompte(numero)?.libelle || ''),
    tiers_id: tiersConserve ? (ligne.tiers_id || null) : null,
    libelle_personnalise: false,
  }
}

export function libelleEffectifLigne(ligne, trouverCompte, natureCompteTiers) {
  // Une actualisation du plan actif ne doit pas enregistrer un libellé standard
  // resté en mémoire depuis une autre société.
  if (!natureCompteTiers(ligne.compte) && !ligne.libelle_personnalise) {
    return trouverCompte(ligne.compte)?.libelle || ligne.libelle || ''
  }
  return ligne.libelle || trouverCompte(ligne.compte)?.libelle || ''
}
