import { API_BASE, getToken, formatErreurAPI } from './api.js'

import { telechargerXlsxAvecLogo } from './exportXlsxLogo.js'

export async function exporterBalanceExcel(nom, colonnes, lignes, { titre, societe, periode, filtre = '', totaux = [], synthese = [] }) {
  const XLSX = await import('xlsx')
  const data = [[titre], ['Société', (typeof societe === 'object' ? societe?.raison_sociale : societe) || 'À compléter'], ['Période / arrêté', periode], ['Devise', 'MAD'], ['Sélection', filtre], [], colonnes.map(c => c.label)]
  for (const ligne of lignes) {
    data.push(colonnes.map(c => {
      const value = c.get(ligne)
      if (c.type === 'nombre' || c.type === 'variation') {
        if (c.type === 'variation' && value == null) return 'N/A'
        if (value == null) return null
        const number = Number(value)
        if (!Number.isFinite(number)) throw new Error('Un montant non fini empêche cet export.')
        return number
      }
      return String(value ?? '') // Cellule texte, aucun champ de formule XLSX.
    }))
  }
  if (totaux.length) data.push(totaux)
  if (synthese.length) data.push([], ...synthese)
  const ws = XLSX.utils.aoa_to_sheet(data)
  ws['!cols'] = colonnes.map(c => ({ wch: c.type === 'nombre' ? 20 : c.label === 'Libellé' || c.label === 'Tiers' ? 36 : 24 }))
  for (let r = 7; r < data.length; r++) {
    for (let c = 0; c < colonnes.length; c++) {
      const cell = ws[XLSX.utils.encode_cell({ r, c })]
      if (cell?.t === 'n') cell.z = colonnes[c].type === 'variation' ? '0.0"%"' : '#,##0.00'
    }
  }
  ws['!autofilter'] = { ref: XLSX.utils.encode_range({ s: { r: 6, c: 0 }, e: { r: 6 + lignes.length, c: colonnes.length - 1 } }) }
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Balance')
  telechargerXlsxAvecLogo(XLSX, wb, `${nom}.xlsx`, societe)
}

export async function exporterBalancePDF({ genre, annee, dateDebut, dateFin, typeTiers = 'client' }) {
  const token = getToken()
  if (!token) throw new Error('Session expirée : reconnectez-vous.')
  const params = new URLSearchParams({ exercice: annee, genre, type_tiers: typeTiers, date_from: dateDebut, date_to: dateFin })
  const r = await fetch(`${API_BASE}/api/ecritures/reporting/balance/pdf?${params}`, { headers: { Authorization: `Bearer ${token}` } })
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(formatErreurAPI(body.detail || `Erreur HTTP ${r.status}`))
  }
  const url = URL.createObjectURL(await r.blob())
  const a = document.createElement('a')
  a.href = url; a.download = `balance_${genre}_${typeTiers}_${dateFin}.pdf`; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
