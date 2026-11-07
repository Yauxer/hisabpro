// Projection de présentation : les agrégats du moteur comptable restent la source
// des montants. Les sous-postes sont informatifs et ne sont jamais additionnés
// une seconde fois aux rubriques mères.
import rubriques from './bilanRubriques.json'

const debit = (soldes, prefixes) => Object.entries(soldes || {}).reduce((total, [compte, valeur]) =>
  prefixes.some(prefixe => compte.startsWith(prefixe))
    ? total + Number(valeur.debit || 0) - Number(valeur.credit || 0)
    : total, 0)

const arrondi = montant => Math.round(montant * 100) / 100

export function presenterBilan(bilan, soldes, bilanN1, soldesN1, n1Disponible) {
  return rubriques.map(section => {
    const racine = bilan
    const racineN1 = bilanN1
    const lignes = racine[section.key === 'immobilise' ? 'actifImmobilise'
      : section.key === 'circulant' ? 'actifCirculant'
      : section.key === 'capitaux_propres' ? 'capitauxPropres'
      : section.key === 'financement_permanent' ? 'financementPermanent'
      : section.key === 'passif_circulant' ? 'passifCirculant'
      : section.key === 'tresorerie' && section.side === 'actif' ? 'tresorerieActif' : 'tresoreriePassif']
    const cle = section.key === 'immobilise' ? 'actifImmobilise'
      : section.key === 'circulant' ? 'actifCirculant'
      : section.key === 'capitaux_propres' ? 'capitauxPropres'
      : section.key === 'financement_permanent' ? 'financementPermanent'
      : section.key === 'passif_circulant' ? 'passifCirculant'
      : section.side === 'actif' ? 'tresorerieActif' : 'tresoreriePassif'
    const lignesN1 = racineN1[cle]
    if (lignes.length !== section.groups.length || lignesN1.length !== section.groups.length) {
      throw new Error(`Rubriques du bilan incompatibles avec ${section.key}`)
    }
    const groups = section.groups.map((group, index) => {
      const parent = lignes[index]
      const precedent = n1Disponible ? lignesN1[index] : null
      const details = group.details.map(detail => ({
        ...detail,
        brut: arrondi(debit(soldes, detail.prefixes)),
        brutN1: n1Disponible ? arrondi(debit(soldesN1, detail.prefixes)) : null,
      }))
      const reste = arrondi((parent.brut || 0) - details.reduce((sum, d) => sum + d.brut, 0))
      const resteN1 = precedent ? arrondi((precedent.brut || 0) - details.reduce((sum, d) => sum + d.brutN1, 0)) : null
      if (details.length && (Math.abs(reste) >= 0.005 || (resteN1 !== null && Math.abs(resteN1) >= 0.005))) {
        details.push({ code: '…', label: 'Autres comptes de la rubrique', brut: reste, brutN1: resteN1 })
      }
      return { ...group, montant: parent.montant, brut: parent.brut, amort: parent.amort, net: parent.net,
        n1: precedent ? (section.side === 'actif' ? precedent.net : precedent.montant) : null,
        details: details.map(detail => ({ ...detail,
          // En présence de dépréciations, le net du sous-poste n'est pas ventilé
          // sans une attribution explicite des comptes correcteurs.
          net: Math.abs(parent.amort || 0) < 0.005 ? detail.brut : null,
          netN1: precedent && Math.abs(precedent.amort || 0) < 0.005 ? detail.brutN1 : null,
        })) }
    })
    const totaux = section.side === 'actif'
      ? (section.key === 'immobilise' ? bilan.totalActifImmobilise
        : section.key === 'circulant' ? bilan.totalActifCirculant : bilan.totalTresorerieActif)
      : groups.reduce((s, g) => s + g.montant, 0)
    const totauxN1 = section.side === 'actif'
      ? (section.key === 'immobilise' ? bilanN1.totalActifImmobilise
        : section.key === 'circulant' ? bilanN1.totalActifCirculant : bilanN1.totalTresorerieActif)
      : groups.reduce((s, g) => s + (g.n1 || 0), 0)
    // Le financement permanent inclut les capitaux propres dans l'agrégat final.
    const total = section.key === 'financement_permanent'
      ? bilan.totalFinancementPermanent
      : section.side === 'passif' && section.key === 'capitaux_propres' ? bilan.totalCapitauxPropres : totaux
    const totalN1 = section.key === 'financement_permanent'
      ? bilanN1.totalFinancementPermanent
      : section.side === 'passif' && section.key === 'capitaux_propres' ? bilanN1.totalCapitauxPropres : totauxN1
    return { ...section, totalLabel: section.total, groups, total, totalN1: n1Disponible ? totalN1 : null }
  })
}
