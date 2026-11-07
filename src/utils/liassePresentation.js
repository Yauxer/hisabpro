import numerotation from '../../hisabpro-backend/services/liasse_numerotation_interne.json'

// Repérage interne uniquement ; aucune modification des codes métier ETIC.
export const NOTE_NUMEROTATION = "T1 à T25 : numérotation interne HisabPro, distincte de la codification DGI. Codes ETIC d'origine conservés."
export function numeroTableau(code) { return Object.hasOwn(numerotation, code) ? numerotation[code] : (code || '') }
export function referenceEtic(code) {
  const numero = numeroTableau(code)
  return numero !== code ? `${numero} / ${code}` : (code || '')
}
