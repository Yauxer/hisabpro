export const QUALIFICATIONS_TVA = [
  { value: 'taxable', label: 'Taxable' },
  { value: 'exonere_droit_deduction', label: 'Exonérée avec droit à déduction' },
  { value: 'exonere_sans_deduction', label: 'Exonérée sans droit à déduction' },
  { value: 'hors_champ', label: 'Hors champ TVA' },
  { value: 'suspension', label: 'Suspension de TVA' },
]

export function tauxTVAPourDate(dateISO) {
  const annee = Number(String(dateISO || '').slice(0, 4)) || new Date().getFullYear()
  if (annee <= 2023) return [0, 7, 10, 14, 20]
  if (annee === 2024) return [0, 8, 10, 11, 12, 13, 14, 16, 20]
  if (annee === 2025) return [0, 9, 10, 12, 15, 18, 20]
  return [0, 10, 20]
}

export function tvaEffective(ligne) {
  return ligne?.qualification_tva && ligne.qualification_tva !== 'taxable' ? 0 : (Number(ligne?.tva) || 0)
}

export function qualificationSansTVA(qualification) {
  return Boolean(qualification && qualification !== 'taxable')
}


export function tauxTVAAvecHistorique(dateISO, valeurCourante = null) {
  const taux = [...tauxTVAPourDate(dateISO)]
  const courant = Number(valeurCourante)
  if (Number.isFinite(courant) && !taux.includes(courant)) taux.push(courant)
  return taux.sort((a, b) => a - b)
}

export function qualificationParDefautPourTaux(taux, qualificationCourante = null) {
  const n = Number(taux)
  if (n === 0) {
    return qualificationCourante && qualificationCourante !== 'taxable'
      ? qualificationCourante
      : 'exonere_sans_deduction'
  }
  return 'taxable'
}
