/**
 * Export CSV compatible Excel (français) :
 * - séparateur point-virgule (convention Excel FR/MA)
 * - BOM UTF-8 pour que les accents s'affichent correctement dans Excel
 * - nombres avec virgule décimale, sans séparateur de milliers
 * - échappement des guillemets et des retours à la ligne
 * - texte de formule protégé et montant invalide signalé « À vérifier »
 *
 * Usage :
 *   exporterCSV('factures_2026', [
 *     { label: 'Numéro',  get: f => f.numero },
 *     { label: 'Montant', get: f => f.total_ttc, type: 'nombre' },
 *   ], listeFactures)
 */
export function exporterCSV(nomFichier, colonnes, lignes) {
  const SEP = ';'

  function cellule(valeur, type) {
    if (valeur === null || valeur === undefined) return ''
    if (type === 'nombre') {
      const valide = typeof valeur === 'number' || (typeof valeur === 'string' &&
        /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(valeur.trim()))
      const n = valide ? Number(valeur) : NaN
      if (!Number.isFinite(n)) return 'À vérifier'
      return n.toFixed(2).replace('.', ',')
    }
    let s = String(valeur)
    // Les libellés et références restent des textes dans un tableur,
    // y compris lorsque le caractère de formule suit des espaces/tabulations.
    if (/^\s*[=+\-@]/.test(s)) s = "'" + s
    if (s.includes(SEP) || s.includes('"') || s.includes('\n') || s.includes('\r')) {
      s = '"' + s.replace(/"/g, '""') + '"'
    }
    return s
  }

  const entete = colonnes.map(c => cellule(c.label)).join(SEP)
  const corps = lignes.map(l =>
    colonnes.map(c => cellule(c.get(l), c.type)).join(SEP)
  ).join('\r\n')

  const contenu = '\uFEFF' + entete + '\r\n' + corps  // BOM UTF-8
  const blob = new Blob([contenu], { type: 'text/csv;charset=utf-8;' })
  const lien = document.createElement('a')
  lien.href = URL.createObjectURL(blob)
  lien.download = nomFichier.endsWith('.csv') ? nomFichier : `${nomFichier}.csv`
  // Lien attaché et URL révoquée après coup : une révocation immédiate peut
  // annuler le téléchargement avant que le navigateur ne l'ait démarré.
  lien.style.display = 'none'
  document.body.appendChild(lien)
  lien.click()
  setTimeout(() => { lien.remove(); URL.revokeObjectURL(lien.href) }, 1000)
}

/** Bouton d'export standard (icône + libellé) à styler par la page appelante. */
export function styleBoutonExport() {
  return {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '7px 14px', borderRadius: 8,
    border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)',
    color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 12, fontWeight: 500,
  }
}
