import { useState, useEffect } from 'react'
import { useExercice } from './ExerciceContext.jsx'
import { etatsAPI } from '../services/api.js'

// Source unique des états : agrégation PostgreSQL de TOUTES les écritures
// validées. Elle ne dépend ni de la pagination du Journal ni des brouillons.
export function useDonneesEtats(exerciceForce = null) {
  const { annee } = useExercice()
  const exercice = exerciceForce ?? annee
  const [etat, setEtat] = useState({
    soldes: {}, disponible: false, chargement: true, erreur: null,
    source: null, controle: null, modele: null, fluxFinancement: {},
  })

  useEffect(() => {
    let annule = false
    setEtat(prev => ({ ...prev, chargement: true, erreur: null }))
    etatsAPI.source(exercice)
      .then(data => {
        if (annule) return
        setEtat({
          soldes: data?.soldes || {},
          disponible: Boolean(data?.disponible),
          chargement: false,
          erreur: null,
          source: data?.source || null,
          controle: data?.controle || null,
          modele: data?.modele || null,
          fluxFinancement: data?.flux_financement || {},
        })
      })
      .catch(err => {
        if (annule) return
        setEtat({ soldes: {}, disponible: false, chargement: false,
          erreur: err?.message || 'Impossible de charger les états de synthèse',
          source: null, controle: null, modele: null, fluxFinancement: {} })
      })
    return () => { annule = true }
  }, [exercice])

  return etat
}

// Compatibilité avec les pages existantes.
export function useSoldesComptes() {
  return useDonneesEtats().soldes
}

export function useSoldesComptesN1() {
  const { annee } = useExercice()
  return useDonneesEtats(annee - 1)
}

// Somme en sens DÉBITEUR (actif, charges) : Σ (débit − crédit)
export function sd(soldes, prefixes) {
  let total = 0
  for (const [cpt, v] of Object.entries(soldes)) {
    if (prefixes.some(p => cpt.startsWith(p))) total += v.debit - v.credit
  }
  return total
}

// Somme en sens CRÉDITEUR (passif, produits) : Σ (crédit − débit)
export function sc(soldes, prefixes) {
  let total = 0
  for (const [cpt, v] of Object.entries(soldes)) {
    if (prefixes.some(p => cpt.startsWith(p))) total += v.credit - v.debit
  }
  return total
}

// ─── CPC — Modèle Normal CGNC (rubriques I à XV) ─────────────────────────────
export function calculerCPC(soldes) {
  const produitsExploitation = {
    ventesMarchandises:  sc(soldes, ['711']),
    ventesBiensServices: sc(soldes, ['712']),
    variationStocks:     sc(soldes, ['713']),   // signé : peut être négatif
    immobilisationsProduites: sc(soldes, ['714']),
    subventions:         sc(soldes, ['716']),
    autresProduits:      sc(soldes, ['718']),
    reprisesTransferts:  sc(soldes, ['719']),
  }
  const I = Object.values(produitsExploitation).reduce((a, b) => a + b, 0)

  const chargesExploitation = {
    achatsRevendus:      sd(soldes, ['611']),
    achatsConsommes:     sd(soldes, ['612']),
    autresChargesExternes: sd(soldes, ['613', '614']),
    impotsTaxes:         sd(soldes, ['616']),
    chargesPersonnel:    sd(soldes, ['617']),
    autresCharges:       sd(soldes, ['618']),
    dotations:           sd(soldes, ['619']),
  }
  const II = Object.values(chargesExploitation).reduce((a, b) => a + b, 0)
  const III = I - II   // Résultat d'exploitation

  const produitsFinanciers = {
    produitsTitres:      sc(soldes, ['732']),
    gainsChange:         sc(soldes, ['733']),
    interetsAutres:      sc(soldes, ['738']),
    reprisesFinancieres: sc(soldes, ['739']),
  }
  const IV = Object.values(produitsFinanciers).reduce((a, b) => a + b, 0)

  const chargesFinancieres = {
    chargesInterets:     sd(soldes, ['631']),
    pertesChange:        sd(soldes, ['633']),
    autresChargesFin:    sd(soldes, ['638']),
    dotationsFinancieres: sd(soldes, ['639']),
  }
  const V = Object.values(chargesFinancieres).reduce((a, b) => a + b, 0)
  const VI  = IV - V    // Résultat financier
  const VII = III + VI  // Résultat courant

  const produitsNonCourants = {
    cessionsImmobilisations: sc(soldes, ['751']),
    subventionsEquilibre: sc(soldes, ['756']),
    reprisesSubventions:  sc(soldes, ['757']),
    autresProduitsNC:     sc(soldes, ['758']),
    reprisesNC:           sc(soldes, ['759']),
  }
  const VIII = Object.values(produitsNonCourants).reduce((a, b) => a + b, 0)

  const chargesNonCourantes = {
    vnaImmobilisationsCedees: sd(soldes, ['651']),
    subventionsAccordees: sd(soldes, ['656']),
    autresChargesNC:      sd(soldes, ['658']),
    dotationsNC:          sd(soldes, ['659']),
  }
  const IX = Object.values(chargesNonCourantes).reduce((a, b) => a + b, 0)
  const X   = VIII - IX  // Résultat non courant
  const XI  = VII + X    // Résultat avant impôts
  const XII = sd(soldes, ['67'])  // Impôts sur les résultats
  const resultatNet = XI - XII

  return {
    produitsExploitation, I,
    chargesExploitation, II, III,
    produitsFinanciers, IV,
    chargesFinancieres, V, VI, VII,
    produitsNonCourants, VIII,
    chargesNonCourantes, IX, X, XI, XII,
    resultatNet,
  }
}

// ─── Bilan — Modèle Normal CGNC (Actif : Brut / Amort. & prov. / Net) ────────
export function calculerBilan(soldes, resultatNet) {
  // Chaque ligne d'actif : { label, brut, amort } → net = brut − amort
  const ligne = (label, brut, amort = 0) => ({ label, brut, amort, net: brut - amort })

  const actifImmobilise = [
    ligne('Immobilisations en non-valeurs', sd(soldes, ['21']), sc(soldes, ['281'])),
    ligne('Immobilisations incorporelles',  sd(soldes, ['22']), sc(soldes, ['282', '292'])),
    ligne('Immobilisations corporelles',    sd(soldes, ['23']), sc(soldes, ['283', '293'])),
    ligne('Immobilisations financières',    sd(soldes, ['24', '25']), sc(soldes, ['294', '295'])),
    ligne('Écarts de conversion — actif',   sd(soldes, ['27'])),
  ]
  const actifCirculant = [
    ligne('Stocks',                          sd(soldes, ['31']), sc(soldes, ['391'])),
    ligne('Fournisseurs débiteurs, avances', sd(soldes, ['341']), 0),
    ligne('Clients et comptes rattachés',    sd(soldes, ['342']), sc(soldes, ['3942'])),
    ligne('Personnel — débiteur',            sd(soldes, ['343']), sc(soldes, ['3943'])),
    ligne('État — débiteur',                 sd(soldes, ['345'])),
    ligne('Comptes d\'associés — débiteurs', sd(soldes, ['346']), sc(soldes, ['3946'])),
    ligne('Autres débiteurs',                sd(soldes, ['348']), sc(soldes, ['3948'])),
    ligne('Comptes de régularisation — actif', sd(soldes, ['349'])),
    ligne('Titres et valeurs de placement',  sd(soldes, ['350']), sc(soldes, ['395'])),
    ligne('Écarts de conversion — actif circulant', sd(soldes, ['37'])),
  ]
  const tresorerieActif = [
    ligne('Chèques et valeurs à encaisser',  sd(soldes, ['511'])),
    ligne('Banques, TG et CCP',              sd(soldes, ['514'])),
    ligne('Caisses, régies d\'avances',      sd(soldes, ['516']), sc(soldes, ['59'])),
  ]

  const totaux = lignes => ({
    brut:  lignes.reduce((s, l) => s + l.brut, 0),
    amort: lignes.reduce((s, l) => s + l.amort, 0),
    net:   lignes.reduce((s, l) => s + l.net, 0),
  })
  const totalActifImmobilise = totaux(actifImmobilise)
  const totalActifCirculant  = totaux(actifCirculant)
  const totalTresorerieActif = totaux(tresorerieActif)
  const totalActif = {
    brut:  totalActifImmobilise.brut  + totalActifCirculant.brut  + totalTresorerieActif.brut,
    amort: totalActifImmobilise.amort + totalActifCirculant.amort + totalTresorerieActif.amort,
    net:   totalActifImmobilise.net   + totalActifCirculant.net   + totalTresorerieActif.net,
  }

  // ── Passif (une colonne) ────────────────────────────────────────────────────
  const capitauxPropres = [
    { label: 'Capital social ou personnel', montant: sc(soldes, ['111']) },
    { label: 'Primes d\'émission, de fusion, d\'apport', montant: sc(soldes, ['112', '113']) },
    { label: 'Réserves (légale et autres)', montant: sc(soldes, ['114', '115']) },
    { label: 'Report à nouveau (±)',        montant: sc(soldes, ['116']) },
    { label: 'Résultats nets en instance d\'affectation (±)', montant: sc(soldes, ['118']) },
    { label: 'Résultat antérieur en attente d\'affectation (119)', montant: sc(soldes, ['119']) },
    { label: 'Résultat net de l\'exercice (±)', montant: resultatNet, injecte: true },
  ]
  const financementPermanent = [
    { label: 'Capitaux propres assimilés (subventions, prov. réglementées)', montant: sc(soldes, ['131', '135']) },
    { label: 'Dettes de financement',       montant: sc(soldes, ['141', '148']) },
    { label: 'Provisions durables pour risques et charges', montant: sc(soldes, ['151', '155']) },
    { label: 'Écarts de conversion — passif', montant: sc(soldes, ['17']) },
  ]
  const passifCirculant = [
    { label: 'Fournisseurs et comptes rattachés', montant: sc(soldes, ['441']) },
    { label: 'Clients créditeurs, avances et acomptes', montant: sc(soldes, ['442']) },
    { label: 'Personnel — créditeur',       montant: sc(soldes, ['443']) },
    { label: 'Organismes sociaux',          montant: sc(soldes, ['444']) },
    { label: 'État — créditeur',            montant: sc(soldes, ['445']) },
    { label: 'Comptes d\'associés — créditeurs', montant: sc(soldes, ['446']) },
    { label: 'Autres créanciers',           montant: sc(soldes, ['448']) },
    { label: 'Comptes de régularisation — passif', montant: sc(soldes, ['449']) },
    { label: 'Autres provisions pour risques et charges', montant: sc(soldes, ['45']) },
    { label: 'Écarts de conversion — passif circulant', montant: sc(soldes, ['47']) },
  ]
  const tresoreriePassif = [
    { label: 'Crédits d\'escompte et de trésorerie', montant: sc(soldes, ['552', '553']) },
    { label: 'Banques (soldes créditeurs)', montant: sc(soldes, ['554']) },
  ]

  const totalCapitauxPropres     = capitauxPropres.reduce((s, l) => s + l.montant, 0)
  const totalFinancementPermanent = totalCapitauxPropres + financementPermanent.reduce((s, l) => s + l.montant, 0)
  const totalPassifCirculant     = passifCirculant.reduce((s, l) => s + l.montant, 0)
  const totalTresoreriePassif    = tresoreriePassif.reduce((s, l) => s + l.montant, 0)
  const totalPassif = totalFinancementPermanent + totalPassifCirculant + totalTresoreriePassif

  return {
    actifImmobilise, totalActifImmobilise,
    actifCirculant, totalActifCirculant,
    tresorerieActif, totalTresorerieActif,
    totalActif,
    capitauxPropres, totalCapitauxPropres,
    financementPermanent, totalFinancementPermanent,
    passifCirculant, totalPassifCirculant,
    tresoreriePassif, totalTresoreriePassif,
    totalPassif,
    equilibre: Math.abs(totalActif.net - totalPassif) < 0.01,
    ecart: totalActif.net - totalPassif,
  }
}

// ─── ESG — État des Soldes de Gestion (TFR + CAF) ─────────────────────────────
export function calculerESG(soldes) {
  // ── Tableau de Formation des Résultats ──
  const ventesMarchandises   = sc(soldes, ['711'])
  const achatsRevendus       = sd(soldes, ['611'])
  const margeBrute           = ventesMarchandises - achatsRevendus            // I

  const ventesBiensServices  = sc(soldes, ['712'])
  const variationStocksProd  = sc(soldes, ['713'])
  const immobProduites       = sc(soldes, ['714'])
  const production           = ventesBiensServices + variationStocksProd + immobProduites  // II

  const achatsConsommes      = sd(soldes, ['612'])
  const autresChargesExternes = sd(soldes, ['613', '614'])
  const consommation         = achatsConsommes + autresChargesExternes        // III

  const valeurAjoutee        = margeBrute + production - consommation         // IV

  const subventionsExploitation = sc(soldes, ['716'])
  const impotsTaxes          = sd(soldes, ['616'])
  const chargesPersonnel     = sd(soldes, ['617'])
  const ebe                  = valeurAjoutee + subventionsExploitation - impotsTaxes - chargesPersonnel  // V

  const autresProduitsExpl   = sc(soldes, ['718'])
  const autresChargesExpl    = sd(soldes, ['618'])
  const reprisesExploitation = sc(soldes, ['719'])
  const dotationsExploitation = sd(soldes, ['619'])
  const resultatExploitation = ebe + autresProduitsExpl - autresChargesExpl
                             + reprisesExploitation - dotationsExploitation   // VI

  const resultatFinancier    = sc(soldes, ['73']) - sd(soldes, ['63'])        // VII
  const resultatCourant      = resultatExploitation + resultatFinancier       // VIII
  const resultatNonCourant   = sc(soldes, ['75']) - sd(soldes, ['65'])        // IX
  const impotsResultats      = sd(soldes, ['67'])
  const resultatNet          = resultatCourant + resultatNonCourant - impotsResultats  // X

  // ── CAF (méthode additive, à partir du résultat net) ──
  // Dotations et reprises retenues : uniquement les éléments DURABLES
  // (amortissements, provisions sur actif immobilisé et provisions durables) ;
  // celles relatives aux actifs et passifs circulants sont exclues conformément au CGNC.
  const dotationsDurables = sd(soldes, ['6191', '6192', '6193', '6194', '61955'])
                          + sd(soldes, ['6391', '6392', '6393'])
                          + sd(soldes, ['6591', '6594', '65955', '65962'])
  const reprisesDurables  = sc(soldes, ['7191', '7192', '7193', '7194', '71955'])
                          + sc(soldes, ['7391', '7392', '7393'])
                          + sc(soldes, ['7591', '7594', '75955', '75962'])
                          + sc(soldes, ['757'])   // reprises sur subventions d'investissement
  const produitsCessions  = sc(soldes, ['751'])
  const vnaCessions       = sd(soldes, ['651'])

  const caf = resultatNet + dotationsDurables - reprisesDurables
            - produitsCessions + vnaCessions

  return {
    // TFR
    ventesMarchandises, achatsRevendus, margeBrute,
    ventesBiensServices, variationStocksProd, immobProduites, production,
    achatsConsommes, autresChargesExternes, consommation,
    valeurAjoutee,
    subventionsExploitation, impotsTaxes, chargesPersonnel, ebe,
    autresProduitsExpl, autresChargesExpl, reprisesExploitation, dotationsExploitation,
    resultatExploitation, resultatFinancier, resultatCourant,
    resultatNonCourant, impotsResultats, resultatNet,
    // CAF
    dotationsDurables, reprisesDurables, produitsCessions, vnaCessions, caf,
  }
}

// ─── Tableau de financement (5e état de synthèse, art. 9 et 10 de la loi 9-88) ──
//
// « Le tableau de financement met en évidence l'évolution financière de l'entreprise
//   au cours de l'exercice en décrivant les ressources dont elle a disposé et les
//   emplois qu'elle en a effectués. » (art. 10)
//
// Il se construit par COMPARAISON entre deux bilans successifs : chaque variation
// de poste est un emploi (besoin de financement) ou une ressource (financement obtenu).
//
// Structure normalisée du CGNC :
//   I  — Synthèse des masses du bilan (variation du fonds de roulement, du BFR,
//        et de la trésorerie nette)
//   II — Emplois et ressources de l'exercice

export function calculerTableauFinancement(soldes, soldesN1, cpc, cpcN1, fluxFinancement = {}, fluxFinancementN1 = {}) {
  const masses = (s, resultatCourant) => {
    const financementPermanent = sc(s, ['11', '13', '14', '15', '16', '17']) + resultatCourant
    const actifImmobilise = sd(s, ['21', '22', '23', '24', '25', '26', '27', '28'])
    const actifCirculant = sd(s, ['31', '34', '35', '37', '39'])
    const passifCirculant = sc(s, ['44', '45', '46', '47', '49'])
    const tresorerieActif = sd(s, ['51'])
    const tresoreriePassif = sc(s, ['55'])
    return {
      financementPermanent,
      actifImmobilise,
      fondsRoulement: financementPermanent - actifImmobilise,
      actifCirculant,
      passifCirculant,
      bfg: actifCirculant - passifCirculant,
      tresorerieActif,
      tresoreriePassif,
      tresorerieNette: tresorerieActif - tresoreriePassif,
    }
  }

  const N = masses(soldes, cpc?.resultatNet || 0)
  const P = masses(soldesN1, cpcN1?.resultatNet || 0)
  const variation = (n, n1) => n - n1
  const varFR = variation(N.fondsRoulement, P.fondsRoulement)
  const varBFG = variation(N.bfg, P.bfg)
  const varTN = variation(N.tresorerieNette, P.tresorerieNette)

  const synthese = [
    { libelle: 'Financement permanent', n: N.financementPermanent, n1: P.financementPermanent,
      emploi: Math.max(-(N.financementPermanent - P.financementPermanent), 0), ressource: Math.max(N.financementPermanent - P.financementPermanent, 0) },
    { libelle: 'Moins actif immobilisé', n: N.actifImmobilise, n1: P.actifImmobilise,
      emploi: Math.max(N.actifImmobilise - P.actifImmobilise, 0), ressource: Math.max(-(N.actifImmobilise - P.actifImmobilise), 0) },
    { libelle: 'Fonds de roulement fonctionnel (A)', n: N.fondsRoulement, n1: P.fondsRoulement,
      emploi: Math.max(-varFR, 0), ressource: Math.max(varFR, 0), total: true },
    { libelle: 'Actif circulant hors trésorerie', n: N.actifCirculant, n1: P.actifCirculant,
      emploi: Math.max(N.actifCirculant - P.actifCirculant, 0), ressource: Math.max(-(N.actifCirculant - P.actifCirculant), 0) },
    { libelle: 'Moins passif circulant hors trésorerie', n: N.passifCirculant, n1: P.passifCirculant,
      emploi: Math.max(-(N.passifCirculant - P.passifCirculant), 0), ressource: Math.max(N.passifCirculant - P.passifCirculant, 0) },
    { libelle: 'Besoin de financement global (B)', n: N.bfg, n1: P.bfg,
      emploi: Math.max(varBFG, 0), ressource: Math.max(-varBFG, 0), total: true },
    { libelle: 'Trésorerie nette (A − B)', n: N.tresorerieNette, n1: P.tresorerieNette,
      emploi: Math.max(varTN, 0), ressource: Math.max(-varTN, 0), total: true },
  ]

  const val = (f, k) => Number(f?.[k] || 0)
  const presentation = (s, f = {}) => {
    const caf = calculerESG(s).caf
    const distributions = val(f, 'distributions_benefices')
    const autofinancement = caf - distributions
    const cessionIncorp = val(f, 'cessions_immobilisations_incorporelles')
    const cessionCorp = val(f, 'cessions_immobilisations_corporelles')
    const cessionFin = val(f, 'cessions_immobilisations_financieres')
    const cessionNV = val(f, 'cessions_immobilisations_non_ventilees')
    const recCreances = val(f, 'recuperations_creances_immobilisees')
    const cessionsReductions = cessionIncorp + cessionCorp + cessionFin + cessionNV + recCreances
    const augmentationCapital = val(f, 'augmentations_capitaux_propres')
    const subventions = val(f, 'subventions_investissement_recues')
    const augmentationCpAssimiles = augmentationCapital + subventions
    const augmentationDettes = val(f, 'augmentations_dettes_financement')

    let acquisitionIncorp = val(f, 'acquisitions_immobilisations_incorporelles')
    let acquisitionCorp = val(f, 'acquisitions_immobilisations_corporelles')
    let acquisitionFin = val(f, 'acquisitions_immobilisations_financieres')
    let augmentationCreances = val(f, 'augmentations_creances_immobilisees')
    const ancienAgregat = val(f, 'acquisitions_immobilisations')
    if ((acquisitionIncorp + acquisitionCorp + acquisitionFin + augmentationCreances) === 0 && ancienAgregat > 0) {
      acquisitionCorp = ancienAgregat
    }
    const acquisitions = acquisitionIncorp + acquisitionCorp + acquisitionFin + augmentationCreances
    const remboursementCapitaux = val(f, 'reductions_capitaux_propres')
    const remboursementDettes = val(f, 'remboursements_dettes_financement')
    const emploisNonValeurs = val(f, 'emplois_non_valeurs')
    return {
      caf, distributions, autofinancement,
      cessionIncorp, cessionCorp, cessionFin, cessionNV, recCreances, cessionsReductions,
      augmentationCapital, subventions, augmentationCpAssimiles, augmentationDettes,
      acquisitionIncorp, acquisitionCorp, acquisitionFin, augmentationCreances, acquisitions,
      remboursementCapitaux, remboursementDettes, emploisNonValeurs,
      totalRessources: autofinancement + cessionsReductions + augmentationCpAssimiles + augmentationDettes,
      totalEmplois: acquisitions + remboursementCapitaux + remboursementDettes + emploisNonValeurs,
    }
  }

  const F = presentation(soldes, fluxFinancement)
  const F1 = presentation(soldesN1, fluxFinancementN1)
  const rr = (code, libelle, key, total = false, niveau = 0, signe = null) => ({
    code, libelle, montant: F[key], n1: F1[key], total, niveau, signe,
  })

  const ressources = [
    rr('A', 'AUTOFINANCEMENT (A)', 'autofinancement', true),
    rr('A1', '+ Capacité d’autofinancement', 'caf', false, 1, '+'),
    rr('A2', '− Distributions de bénéfices', 'distributions', false, 1, '−'),
    rr('B', 'CESSIONS ET RÉDUCTIONS D’IMMOBILISATIONS (B)', 'cessionsReductions', true),
    rr('B1', '+ Cessions d’immobilisations incorporelles', 'cessionIncorp', false, 1, '+'),
    rr('B2', '+ Cessions d’immobilisations corporelles', 'cessionCorp', false, 1, '+'),
    rr('B3', '+ Cessions d’immobilisations financières', 'cessionFin', false, 1, '+'),
    rr('B4', '+ Récupérations sur créances immobilisées', 'recCreances', false, 1, '+'),
    rr('C', 'AUGMENTATION DES CAPITAUX PROPRES ET ASSIMILÉS (C)', 'augmentationCpAssimiles', true),
    rr('C1', '+ Augmentation du capital, apports', 'augmentationCapital', false, 1, '+'),
    rr('C2', '+ Subventions d’investissement', 'subventions', false, 1, '+'),
    rr('D', 'AUGMENTATION DES DETTES DE FINANCEMENT (D)', 'augmentationDettes', true),
  ]
  if (F.cessionNV || F1.cessionNV) {
    ressources.splice(8, 0, rr('B?', 'Cessions d’immobilisations non ventilées (7518) — à reclasser', 'cessionNV', false, 1, '+'))
  }

  const emplois = [
    rr('E', 'ACQUISITIONS ET AUGMENTATIONS D’IMMOBILISATIONS (E)', 'acquisitions', true),
    rr('E1', '+ Acquisitions d’immobilisations incorporelles', 'acquisitionIncorp', false, 1, '+'),
    rr('E2', '+ Acquisitions d’immobilisations corporelles', 'acquisitionCorp', false, 1, '+'),
    rr('E3', '+ Acquisitions d’immobilisations financières', 'acquisitionFin', false, 1, '+'),
    rr('E4', '+ Augmentation des créances immobilisées', 'augmentationCreances', false, 1, '+'),
    rr('F', 'REMBOURSEMENT DES CAPITAUX PROPRES (F)', 'remboursementCapitaux', true),
    rr('G', 'REMBOURSEMENT DES DETTES DE FINANCEMENT (G)', 'remboursementDettes', true),
    rr('H', 'EMPLOIS EN NON-VALEURS (H)', 'emploisNonValeurs', true),
  ]

  const totalRessources = F.totalRessources
  const totalEmplois = F.totalEmplois
  const ecartControle = (totalRessources - totalEmplois) - varFR
  const totalGeneralRessources = totalRessources + Math.max(-varBFG, 0) + Math.max(-varTN, 0)
  const totalGeneralEmplois = totalEmplois + Math.max(varBFG, 0) + Math.max(varTN, 0)
  const ecartTotalGeneral = totalGeneralRessources - totalGeneralEmplois

  return {
    synthese, ressources, emplois, totalRessources, totalEmplois,
    totalGeneralRessources, totalGeneralEmplois,
    variationFR: varFR, variationBFG: varBFG, variationTN: varTN,
    controle: Math.abs(ecartControle) < 1 && Math.abs(ecartTotalGeneral) < 1,
    ecartControle, ecartTotalGeneral, massesN: N, massesN1: P,
    sourceFlux: 'mouvements_valides_ventiles_cgnc_hors_an_cloture',
    avertissements: F.cessionNV > 0
      ? [`${F.cessionNV.toFixed(2)} MAD de cessions 7518 ne peuvent pas être ventilés automatiquement par nature.`]
      : [],
  }
}
