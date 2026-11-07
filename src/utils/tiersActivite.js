import { dateLocaleISO } from './formUtils.js'

function jour(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const [y, m, d] = value.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1, d))
  return dt.toISOString().slice(0, 10) === value ? dt.getTime() : null
}

export function joursDepuis(value, maintenant = new Date()) {
  const date = jour(value); const reference = jour(dateLocaleISO(maintenant))
  return date === null || reference === null ? null : (reference - date) / 86400000
}

export function factureActivite(f) {
  return f.est_validee === true && !f.est_proforma && f.statut !== 'annulee'
}

export function factureOuverte(f) {
  return factureActivite(f) && ['en_attente', 'partiellement_payee', 'retard'].includes(f.statut)
}

export function resumerActivite(tiers, factures, soldes) {
  const parTiers = {}; const ids = new Set(tiers.map(t => String(t.id)))
  let nonRattachees = 0
  for (const f of factures) {
    if (!factureActivite(f)) continue
    const id = f.tiers_id == null ? null : String(f.tiers_id)
    if (id === null || !ids.has(id)) { nonRattachees++; continue }
    const a = parTiers[id] ||= { nb: 0, derniere: null, creances: 0, dettes: 0, impaye: 0, indetermines: 0 }
    a.nb++
    if (jour(f.date) !== null && (!a.derniere || f.date > a.derniere)) a.derniere = f.date
    if (!factureOuverte(f)) continue
    const solde = soldes[f.id]?.solde_restant
    if (typeof solde !== 'number' || !Number.isFinite(solde) || solde < 0 || !['vente', 'achat'].includes(f.type)) {
      a.indetermines++; continue
    }
    if (f.type === 'vente') a.creances += solde
    else a.dettes += solde
    a.impaye += solde
  }
  return { parTiers, nonRattachees }
}

// Les requêtes de détail restent bornées, même avec un exercice volumineux.
export async function chargerSoldes(factures, lire, concurrence = 4) {
  const result = {}; let index = 0
  const ouvertes = factures.filter(factureOuverte)
  await Promise.all(Array.from({ length: Math.min(concurrence, ouvertes.length) }, async () => {
    while (index < ouvertes.length) {
      const facture = ouvertes[index++]
      try { result[facture.id] = await lire(facture.id) }
      catch (e) { result[facture.id] = { erreur: e.message || 'Solde indisponible' } }
    }
  }))
  return result
}

// Délai paramétré du tiers, sans inférer une échéance depuis ses factures.
export function categorieDelaiPaiement(valeur) {
  if (typeof valeur !== 'number' || !Number.isFinite(valeur) || !Number.isInteger(valeur) || valeur < 0) return 'a_verifier'
  if (valeur === 0) return 'comptant'
  if (valeur <= 30) return '1_30'
  if (valeur <= 60) return '31_60'
  return 'plus_60'
}

export function correspondDelaiPaiement(valeur, filtre) {
  return filtre === 'TOUS' || categorieDelaiPaiement(valeur) === filtre
}
