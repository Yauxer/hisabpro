// Formats d'affichage communs aux écrans Paie (lot 972) : mêmes montants et mêmes
// mois partout, comme dans les écrans comptables.
const MONTANT = new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 4 })

export function mad(v) {
  if (v == null || v === '') return 'À compléter'
  const n = Number(v)
  return Number.isFinite(n) ? `${MONTANT.format(n)} MAD` : 'À vérifier'
}

export function moisLibelle(periode) {
  const [a, m] = String(periode || '').slice(0, 7).split('-').map(Number)
  if (!a || !m) return String(periode || '')
  const t = new Date(Date.UTC(a, m - 1, 1)).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric', timeZone: 'UTC' })
  return t.charAt(0).toUpperCase() + t.slice(1)
}

export function pluriel(n, singulier, pluriel = singulier + 's') {
  return `${n} ${Number(n) > 1 ? pluriel : singulier}`
}
