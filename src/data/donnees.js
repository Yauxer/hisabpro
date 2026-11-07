// Données de démonstration pour le prototype
// Ces données viendront de l'API backend plus tard

export const KPI_DATA = {
  chiffreAffaires: { valeur: 842500, evolution: 12.4, sens: 'hausse' },
  charges:         { valeur: 614200, evolution: 8.1,  sens: 'hausse' },
  resultatNet:     { valeur: 228300, evolution: 23.7, sens: 'hausse' },
  tvaADeclarer:    { valeur: 34600, echeance: '31/05/2025' },
}

export const ECRITURES_RECENTES = [
  {
    id: 1,
    date: '2025-05-02',
    libelle: 'Facture fournisseur SOMACA',
    journal: 'AC',
    lignes: [
      { compte: '6111', libelle: 'Achats de marchandises', debit: 12400, credit: 0 },
      { compte: '3455', libelle: 'TVA récupérable 20%',    debit: 2480,  credit: 0 },
      { compte: '4411', libelle: 'Fournisseur SOMACA',     debit: 0,     credit: 14880 },
    ],
  },
  {
    id: 2,
    date: '2025-04-29',
    libelle: 'Vente client SAMIR SA',
    journal: 'VT',
    lignes: [
      { compte: '3421', libelle: 'Client SAMIR SA',          debit: 60000, credit: 0 },
      { compte: '7111', libelle: 'Ventes de marchandises',   debit: 0,     credit: 50000 },
      { compte: '4455', libelle: 'TVA facturée 20%',         debit: 0,     credit: 10000 },
    ],
  },
  {
    id: 3,
    date: '2025-04-28',
    libelle: 'Rémunérations avril 2025',
    journal: 'SA',
    lignes: [
      { compte: '6171', libelle: 'Rémunérations du personnel', debit: 85000, credit: 0 },
      { compte: '4441', libelle: 'CNSS à payer',               debit: 0,     credit: 8500  },
      { compte: '44525', libelle: 'IR à payer',                debit: 0,     credit: 12000 },
      { compte: '4432', libelle: 'Net à payer au personnel',   debit: 0,     credit: 64500 },
    ],
  },
  {
    id: 4,
    date: '2025-04-25',
    libelle: 'Loyer bureau avril 2025',
    journal: 'AC',
    lignes: [
      { compte: '6132', libelle: "Locations et charges locatives", debit: 15000, credit: 0 },
      { compte: '3455', libelle: 'TVA récupérable 20%',            debit: 3000,  credit: 0 },
      { compte: '5141', libelle: 'Banque',                         debit: 0,     credit: 18000 },
    ],
  },
]

export const JOURNAUX = [
  // ── Journaux standards ──────────────────────────────────────────
  { code: 'AC',  label: 'Achats',                 groupe: 'standard' },
  { code: 'VT',  label: 'Ventes',                 groupe: 'standard' },
  { code: 'BQ',  label: 'Banque',                 groupe: 'standard' },
  { code: 'CA',  label: 'Caisse',                 groupe: 'standard' },
  { code: 'OD',  label: 'Opérations diverses',    groupe: 'standard' },
  { code: 'AV',  label: 'Avoirs',                 groupe: 'standard' },
  // ── Journaux spéciaux ───────────────────────────────────────────
  { code: 'AN',  label: 'À nouveau',              groupe: 'special'  },
  { code: 'EN',  label: 'Encours',                groupe: 'special'  },
  { code: 'AE',  label: 'À encaisser',            groupe: 'special'  },
  { code: 'AM',  label: 'Amortissements',         groupe: 'special'  },
  { code: 'SA',  label: 'Rémunérations',               groupe: 'special'  },
  { code: 'TV',  label: 'TVA',                    groupe: 'special'  },
  { code: 'PR',  label: 'Provisions',             groupe: 'special'  },
  // Journal système : visible dans le Journal/FEC, jamais proposé en saisie manuelle.
  { code: 'CL',  label: 'Clôture',                groupe: 'system'   },
]

export const TAUX_TVA = [0, 7, 10, 14, 20]

// Formatage monétaire MAD
export function formatMAD(montant) {
  return new Intl.NumberFormat('fr-MA', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(montant)
}

// Formatage date
export function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('fr-MA', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}
