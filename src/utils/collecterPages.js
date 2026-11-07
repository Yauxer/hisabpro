// Une page répétée serait un chargement tronqué : échouer plutôt que boucler.
export async function collecterPages(lirePage, taille = 100) {
  const resultat = []; const ids = new Set()
  for (let skip = 0; ; skip += taille) {
    const page = await lirePage({ skip, limit: taille })
    if (!Array.isArray(page)) throw new Error('Liste des factures indisponible.')
    for (const piece of page) {
      if (ids.has(piece.id)) throw new Error('La liste des factures a changé pendant son chargement. Rechargez-la.')
      ids.add(piece.id); resultat.push(piece)
    }
    if (page.length < taille) return resultat
  }
}
