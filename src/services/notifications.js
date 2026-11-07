// Lot UX 967 : notifications non bloquantes à la place de window.alert.
// Une erreur reste affichée jusqu'à sa fermeture ; une information disparaît seule.
const abonnes = new Set()
let suivant = 1

function publier(message, type) {
  const texte = String(message ?? '').trim()
  if (!texte) return
  const n = { id: suivant++, texte, type }
  abonnes.forEach(f => f(n))
}

export function notifier(message) { publier(message, 'info') }
notifier.succes = message => publier(message, 'succes')
notifier.erreur = message => publier(message, 'erreur')

export function abonnerNotifications(f) {
  abonnes.add(f)
  return () => abonnes.delete(f)
}
