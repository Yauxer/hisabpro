// Lot 980 : liste unique des modes de règlement, identique à `ModeReglement`
// côté API (hisabpro-backend/schemas.py). Tous les écrans (facture, règlement,
// avoir, acompte, filtres) l'utilisent : un mode ne peut plus manquer quelque part.
export const MODES_REGLEMENT = [
  { val: 'virement', label: 'Virement' },
  { val: 'cheque', label: 'Chèque' },
  { val: 'especes', label: 'Espèces' },
  { val: 'effet', label: 'Effet' },
  { val: 'carte', label: 'Carte' },
  { val: 'prelevement', label: 'Prélèvement' },
  { val: 'autre', label: 'Autre' },
]

export const LIBELLES_MODES = Object.fromEntries(MODES_REGLEMENT.map(m => [m.val, m.label]))

export const libelleMode = mode => LIBELLES_MODES[mode] || mode || ''
