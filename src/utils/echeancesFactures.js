import { dateLocaleISO } from './formUtils.js'

// Dates calendaires : une échéance du jour ne devient pas en retard à midi.
function jourUTC(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const [y, m, d] = value.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1, d))
  return dt.toISOString().slice(0, 10) === value ? dt : null
}

// La date contractuelle est conservée pour l'édition. La lecture API fournit
// séparément la prochaine échéance ouverte selon les imputations réelles.
export function dateEcheanceAffichee(facture) {
  if (!facture) return null
  if (Object.prototype.hasOwnProperty.call(facture, 'date_prochaine_echeance')) {
    return facture.date_prochaine_echeance
  }
  // Un ancien objet sans situation d'imputation ne permet pas de choisir une
  // échéance dans un échéancier multiple : ne pas afficher une date supposée.
  if (facture.echeances?.length > 1) return null
  if (facture.date_echeance) return facture.date_echeance
  const debut = jourUTC(facture.date)
  const delai = Number(facture.delai_paiement ?? 60)
  if (!debut || !Number.isFinite(delai) || !Number.isInteger(delai) || delai < 0) return null
  debut.setUTCDate(debut.getUTCDate() + delai)
  return debut.toISOString().slice(0, 10)
}

export function joursCalendairesAvant(date, maintenant = new Date()) {
  const echeance = jourUTC(date)
  const aujourd = jourUTC(dateLocaleISO(maintenant))
  return echeance && aujourd ? (echeance - aujourd) / 86400000 : null
}

export function joursAvantEcheance(facture, maintenant = new Date()) {
  if (!facture || ['payee', 'annulee', 'brouillon'].includes(facture.statut)
      || facture.est_proforma || facture.est_validee === false) return null
  return joursCalendairesAvant(dateEcheanceAffichee(facture), maintenant)
}

export function factureEnRetard(facture, maintenant = new Date()) {
  const jours = joursAvantEcheance(facture, maintenant)
  return jours !== null && jours < 0
}
