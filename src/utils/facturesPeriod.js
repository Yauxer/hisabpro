import { tvaEffective } from './tvaUtils.js'

const nombre = value => Number.isFinite(Number(value)) ? Number(value) : 0
const arrondi = value => Math.round((value + Number.EPSILON) * 100) / 100
export const periodeInversee = (du, au) => Boolean(du && au && du > au)
export function dansPeriode(piece, du = '', au = '') {
  if (periodeInversee(du, au)) return false
  const date = String(piece?.date || '').slice(0, 10)
  if (!du && !au) return true
  return Boolean(date && (!du || date >= du) && (!au || date <= au))
}
export const facturePubliee = f => Boolean(f.est_validee && !f.est_proforma && f.statut !== 'annulee')
export const avoirPublie = a => ['emis', 'utilise', 'rembourse'].includes(a.statut)

export function totauxFacturation(factures, avoirs) {
  const somme = (pieces, type, champ) => pieces.filter(p => p.type === type).reduce((total, p) => total + nombre(p[champ]), 0)
  return {
    caNetHT: arrondi(somme(factures, 'vente', 'total_ht') - somme(avoirs, 'vente', 'total_ht')),
    ventesNettesTTC: arrondi(somme(factures, 'vente', 'total_ttc') - somme(avoirs, 'vente', 'total_ttc')),
    achatsNetsTTC: arrondi(somme(factures, 'achat', 'total_ttc') - somme(avoirs, 'achat', 'total_ttc')),
  }
}

export function ventilationCA(factures, avoirs, prixAchatMoyen = {}) {
  const map = {}
  const ligne = key => (map[key] ||= { designation: key, quantite: 0, ca_ht: 0, ca_ttc: 0, cout: 0 })
  for (const f of factures.filter(f => f.type === 'vente')) {
    let htLignes = 0; let ttcLignes = 0
    for (const l of f.lignes || []) {
      const key = l.description || 'Article sans désignation'; const r = ligne(key)
      const q = nombre(l.quantite)
      const base = Math.max(0, q * nombre(l.prix_unitaire) * (1 - nombre(l.remise) / 100) * (1 - nombre(l.remise2) / 100) - q * nombre(l.rabais))
      const ht = arrondi(base * (1 - nombre(f.remise_globale) / 100) * (1 - nombre(f.ristourne) / 100))
      const ttc = arrondi(ht * (1 - nombre(f.escompte) / 100) * (1 + tvaEffective(l) / 100))
      r.quantite += q; r.ca_ht += ht; r.ca_ttc += ttc; r.cout += q * (prixAchatMoyen[key] || 0)
      htLignes += ht; ttcLignes += ttc
    }
    const depot = f.frais_emballage_mode === 'consigne' ? nombre(f.frais_emballage_ht) : 0
    if (depot) {
      const r = ligne('Dépôts de consignation'); r.hors_article = true; r.ca_ht += depot; r.ca_ttc += depot
    }
    const htFrais = arrondi(nombre(f.total_ht) - htLignes - depot); const ttcFrais = arrondi(nombre(f.total_ttc) - ttcLignes - depot)
    if (htFrais || ttcFrais) {
      const r = ligne('Frais et écarts d’arrondi'); r.ca_ht += htFrais; r.ca_ttc += ttcFrais
    }
  }
  for (const a of avoirs.filter(a => a.type === 'vente')) {
    let htLignes = 0; let ttcLignes = 0
    for (const l of a.lignes || []) {
      const key = l.description || 'Article sans désignation'; const r = ligne(key)
      const q = nombre(l.quantite); const ht = nombre(l.montant_ht); const ttc = nombre(l.montant_ttc)
      r.quantite -= q; r.ca_ht -= ht; r.ca_ttc -= ttc; r.cout -= q * (prixAchatMoyen[key] || 0)
      htLignes += ht; ttcLignes += ttc
    }
    const htFrais = arrondi(nombre(a.total_ht) - htLignes); const ttcFrais = arrondi(nombre(a.total_ttc) - ttcLignes)
    if (htFrais || ttcFrais) {
      const r = ligne('Frais et écarts d’arrondi'); r.ca_ht -= htFrais; r.ca_ttc -= ttcFrais
    }
  }
  const totalHT = Object.values(map).reduce((total, r) => total + r.ca_ht, 0)
  return Object.values(map).sort((a, b) => b.ca_ht - a.ca_ht).map(r => ({ ...r,
    ca_ht: arrondi(r.ca_ht), ca_ttc: arrondi(r.ca_ttc), pct: totalHT > 0 ? r.ca_ht / totalHT * 100 : 0,
    marge: arrondi(r.ca_ht - r.cout), taux_marge: r.ca_ht > 0 ? (r.ca_ht - r.cout) / r.ca_ht * 100 : null,
  }))
}
