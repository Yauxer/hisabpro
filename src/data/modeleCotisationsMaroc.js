// Lot 975 : modèle de départ des cotisations sociales du secteur privé (salariés).
// Valeurs relevées le 31/10/2026 sur les pages officielles de la CNSS (cnss.ma) citées
// ci-dessous. Elles sont créées comme PROPOSITIONS « à vérifier » : l'utilisateur les relit,
// les corrige si besoin et les approuve. Aucune n'est présentée comme certifiée.
// Déductibilité IR : CGI 2026, article 59-II-A (retenues de retraite du régime de sécurité
// sociale) et 59-III (cotisations de prévoyance sociale et prestations à court terme), lus le
// 31/10/2026 dans l'édition consolidée conservée (empreinte ci-dessous, pages imprimées 99-100).
// Non incluse faute de source officielle consultée : taxe de formation professionnelle.
const SOURCE_PAIEMENT = 'https://www.cnss.ma/fr/content/paiement-de-vos-cotisations-sociales'
const SOURCE_AMO = 'https://www.cnss.ma/fr/faq-page/34'
const CONSULTATION = '2026-10-31'
export const REGIME_MODELE = 'CNSS'
const CGI = 'https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf'
const CGI_EMPREINTE = 'fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'
const deductible = (article, extrait) => ({
  traitement: 'DEDUCTIBLE', statut_reglementaire: 'VALIDE', conditions: 'Part salariale retenue par l’employeur et versée à la CNSS.',
  source_reference: 'Code général des impôts 2026 (édition consolidée conservée), ' + article, texte_reference: extrait,
  article, url_source: CGI, empreinte_preuve: CGI_EMPREINTE, date_consultation: CONSULTATION,
})
const ART_59_III = deductible('article 59-III', 'Cotisations aux organismes marocains de prévoyance sociale et cotisations salariales de sécurité sociale pour les prestations à court terme')

const commun = (source, reference) => ({
  organisme: 'CNSS', applicabilite: 'APPLICABLE', calcul_mode: 'TAUX', unite: 'mensuel',
  date_debut: '2026-01-01', source_nature: 'REGLEMENTAIRE', statut_reglementaire: 'A_VERIFIER',
  source_reference: reference, url_source: source, date_consultation: CONSULTATION,
})

export const MODELE_COTISATIONS_MAROC = [
  { code: 'CNSS_PS_COURT_TERME', contenu: { ...commun(SOURCE_PAIEMENT, 'CNSS — paiement des cotisations sociales : prestations sociales à court terme'),
    libelle: 'Prestations sociales à court terme', assiette: 'CNSS', taux_salarial: '0.52', taux_patronal: '1.05',
    plafond_mode: 'MONTANT', plafond: '6000.00', composants: ['PS_COURT_TERME'],
    conditions: 'Salariés du secteur privé assujettis à la CNSS. Salaire plafonné à 6 000 DH par mois.', deductibilite_ir: ART_59_III } },
  { code: 'CNSS_PS_LONG_TERME', contenu: { ...commun(SOURCE_PAIEMENT, 'CNSS — paiement des cotisations sociales : prestations sociales à long terme'),
    libelle: 'Prestations sociales à long terme (retraite)', assiette: 'CNSS', taux_salarial: '3.96', taux_patronal: '7.93',
    plafond_mode: 'MONTANT', plafond: '6000.00', composants: ['PS_LONG_TERME'],
    conditions: 'Salariés du secteur privé assujettis à la CNSS. Salaire plafonné à 6 000 DH par mois.',
    deductibilite_ir: deductible('article 59-II-A', 'Retenues supportées pour la constitution de pensions ou de retraites du régime de sécurité sociale (dahir n° 1-72-184)') } },
  { code: 'CNSS_ALLOCATIONS_FAMILIALES', contenu: { ...commun(SOURCE_PAIEMENT, 'CNSS — paiement des cotisations sociales : prestations familiales'),
    libelle: 'Prestations familiales', assiette: 'CNSS', taux_salarial: '0', taux_patronal: '6.40',
    plafond_mode: 'SANS', plafond: null, composants: ['ALLOCATIONS_FAMILIALES'],
    conditions: 'À la charge de l’employeur, sur l’ensemble du salaire soumis, sans plafond.', deductibilite_ir: ART_59_III } },
  { code: 'CNSS_AMO', contenu: { ...commun(SOURCE_AMO, 'CNSS — FAQ régime assurance maladie : taux de cotisation AMO des salariés'),
    libelle: 'Assurance maladie obligatoire (AMO)', assiette: 'AMO', taux_salarial: '2.26', taux_patronal: '2.26',
    plafond_mode: 'SANS', plafond: null, composants: ['AMO'],
    conditions: 'Sur l’ensemble des rémunérations, sans plafond.', deductibilite_ir: ART_59_III } },
  { code: 'CNSS_AMO_SOLIDARITE', contenu: { ...commun(SOURCE_AMO, 'CNSS — FAQ régime assurance maladie : participation de solidarité AMO'),
    libelle: 'Participation AMO (solidarité)', assiette: 'AMO', taux_salarial: '0', taux_patronal: '1.85',
    plafond_mode: 'SANS', plafond: null, composants: ['AMO_SOLIDARITE'],
    conditions: 'À la charge de l’employeur, sur l’ensemble des rémunérations, sans plafond.', deductibilite_ir: ART_59_III } },
]
