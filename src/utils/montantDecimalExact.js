// Les montants fixes du serveur restent des chaînes : aucun passage par Number.
export function montantDecimalExact(valeur) {
  if (typeof valeur !== 'string') return 'À vérifier'
  const m = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(valeur)
  if (!m) return 'À vérifier'
  return `${m[1]}${m[2].replace(/\B(?=(\d{3})+(?!\d))/g, '.')},${(m[3] || '').padEnd(2, '0')}`
}
