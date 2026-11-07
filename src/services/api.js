// URL de l'API — configurable via .env (VITE_API_URL), avec repli sur le dev local.
import { collecterPages } from '../utils/collecterPages.js'
// En production : créer un fichier .env avec VITE_API_URL=https://api.mondomaine.ma
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '0.1.0'
const BASE_URL = API_BASE

export function getToken()        { return localStorage.getItem('hisabpro_token') }
export function setToken(token)   { localStorage.setItem('hisabpro_token', token) }
export function removeToken() {
  localStorage.removeItem('hisabpro_token')
  localStorage.removeItem('hisabpro_role')
  // Effacer les copies temporaires des plans de toutes les sociétés du compte.
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      const cle = sessionStorage.key(i)
      if (cle?.startsWith('hisabpro_plan_societe_v1:')) sessionStorage.removeItem(cle)
    }
  } catch { /* stockage désactivé : aucun cache à effacer */ }
}

// ─── Rôle de l'utilisateur connecté (admin | comptable | lecture) ────────────
export function getRole()         { return localStorage.getItem('hisabpro_role') || 'comptable' }
export function setRole(role)     { if (role) localStorage.setItem('hisabpro_role', role) }
// Droits dérivés, utilisés pour masquer/désactiver les actions dans l'interface
export function peutEcrire()      { return ['admin', 'comptable'].includes(getRole()) }
export function estAdmin()        { return getRole() === 'admin' }
export const LIBELLE_ROLE = {
  admin: 'Administrateur', comptable: 'Comptable', lecture: 'Consultation seule',
  personnel: 'Personnel seul',
}
export function isConnecte()      { return !!getToken() }


// Formate le champ `detail` d'une erreur FastAPI en message lisible.
// Un 422 (validation Pydantic) renvoie un tableau d'objets {loc, msg, ...} :
// sans ce formatage, l'utilisateur voit "[object Object]".
export function formatErreurAPI(detail) {
  if (!detail) return 'Erreur serveur'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map(e => {
      const champ = Array.isArray(e.loc) ? e.loc.filter(x => x !== 'body').join('.') : ''
      return champ ? `${champ} : ${e.msg}` : (e.msg || JSON.stringify(e))
    }).join(' — ')
  }
  if (typeof detail === 'object') return detail.msg || JSON.stringify(detail)
  return String(detail)
}

function verifierJetonReponse(token) {
  if (token && getToken() !== token) {
    throw new Error('La session a changé ; cette réponse de l’ancienne session a été ignorée.')
  }
}

function verifierReponseSession(response, token) {
  verifierJetonReponse(token)
  if (response.status !== 401 || !token) return
  removeToken()
  window.location.reload()
  throw new Error('Session expirée : reconnectez-vous.')
}

// Une panne de transport doit rester distincte des refus HTTP du serveur.
async function fetchAvecErreurReseau(url, options) {
  try {
    return await fetch(url, options)
  } catch (erreur) {
    if (erreur instanceof TypeError) {
      throw new Error('Connexion au serveur indisponible. Vérifiez votre connexion puis réessayez.', { cause: erreur })
    }
    throw erreur
  }
}

async function request(method, path, body = null, requiresAuth = true) {
  const headers = { 'Content-Type': 'application/json' }
  const binaire=typeof Blob!=='undefined'&&body instanceof Blob
  if(binaire)headers['Content-Type']='application/octet-stream'
  const token = requiresAuth ? getToken() : null
  if (requiresAuth) {
    if (!token) throw new Error('Non connecté')
    headers['Authorization'] = `Bearer ${token}`
  }
  const options = { method, headers }
  if (body) options.body = binaire?body:JSON.stringify(body)
  const response = await fetchAvecErreurReseau(`${BASE_URL}${path}`, options)
  verifierReponseSession(response, token)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur serveur' }))
    verifierJetonReponse(token)
    throw new Error(formatErreurAPI(error.detail))
  }
  if (response.status === 204) return null
  const data = await response.json()
  verifierJetonReponse(token)
  return data
}


async function downloadRequest(path, body = null) {
  const headers = {}
  const token = getToken()
  if (!token) throw new Error('Non connecté')
  headers['Authorization'] = `Bearer ${token}`
  const options = { method: body === null ? 'GET' : 'POST', headers }
  if (body !== null) { headers['Content-Type'] = 'application/json'; options.body = JSON.stringify(body) }
  const response = await fetchAvecErreurReseau(`${BASE_URL}${path}`, options)
  verifierReponseSession(response, token)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erreur serveur' }))
    verifierJetonReponse(token)
    const detail = error?.detail?.message || error?.detail
    throw new Error(formatErreurAPI(detail))
  }
  const disposition = response.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  const blob = await response.blob()
  verifierJetonReponse(token)
  return { blob, filename: match?.[1] || 'export.bin' }
}

export const facturesConservationAPI = {
  consulter(id) { return request('GET', `/api/factures/${id}/copie-conservee`) },
  conserver(id, body) { return request('POST', `/api/factures/${id}/copie-conservee`, body) },
  telecharger(id) { return downloadRequest(`/api/factures/${id}/copie-conservee/pdf`) },
}

export const utilisateursAPI = {
  lister()            { return request('GET',    '/api/utilisateurs') },
  roles()             { return request('GET',    '/api/utilisateurs/roles') },
  creer(data)         { return request('POST',   '/api/utilisateurs', data) },
  modifier(id, data)  { return request('PATCH',  `/api/utilisateurs/${id}`, data) },
  supprimer(id)       { return request('DELETE', `/api/utilisateurs/${id}`) },
}

const PERSONNEL = '/api/employes/personnel'
export const personnelAPI = {
  coffreEtat() { return request('GET',`${PERSONNEL}/coffre`) },
  coffrePolitique(data) { return request('POST',`${PERSONNEL}/coffre/politique`,data) },
  pieces(id) { return request('GET',`${PERSONNEL}/coffre/${id}/pieces`) },
  deposerPiece(id,categorie,fichier) { return request('POST',`${PERSONNEL}/coffre/${id}/pieces?${new URLSearchParams({categorie})}`,fichier) },
  telechargerPiece(id,piece) { return downloadRequest(`${PERSONNEL}/coffre/${id}/pieces/${piece}`) },
  revelerBanque(id,demande) { return request('GET',`${PERSONNEL}/coffre/${id}/banque/${demande}/reveler`) },
  contexte() { return request('GET',`${PERSONNEL}/contexte`) },
  acces() { return request('GET','/api/employes/securite/acces') },
  lister(params) { return request('GET',`${PERSONNEL}?${new URLSearchParams(params)}`) },
  lire(id, au) { return request('GET',`${PERSONNEL}/${id}?${new URLSearchParams({au})}`) },
  options() { return request('GET',`${PERSONNEL}/options`) },
  creer(data) { return request('POST',PERSONNEL,data) },
  reprendre(data) { return request('POST',`${PERSONNEL}/reprises`,data) },
  proposer(id,data) { return request('POST',`${PERSONNEL}/${id}/modifications`,data) },
  demandes(params) { return request('GET',`${PERSONNEL}/demandes?${new URLSearchParams(params)}`) },
  soumettre(id,data) { return request('POST',`${PERSONNEL}/demandes/${id}/soumettre`,data) },
  decider(id,action,data) { return request('POST',`${PERSONNEL}/demandes/${id}/${action}`,data) },
  historique(id,params) { return request('GET',`${PERSONNEL}/${id}/historique?${new URLSearchParams(params)}`) },
  habilitations() { return request('GET','/api/employes/securite/habilitations') },
  accorder(data) { return request('POST','/api/employes/securite/habilitations',data) },
  revoquer(id,motif) { return request('POST',`/api/employes/securite/habilitations/${id}/revoquer`,{motif}) },
  activer(motif) { return request('POST','/api/employes/securite/activation',{confirmation:'PROTEGER_PERSONNEL',motif}) },
  validationUnique(active,motif) { return request('POST','/api/employes/securite/validation-unique',{active,motif}) },
}

export const societesLieesAPI = {
  lister() { return request('GET', '/api/societes/liaisons') },
  societes() { return request('GET', '/api/societes/mes-societes') },
  options(id) { return request('GET', `/api/societes/liaisons/options/${id}`) },
  creer(data) { return request('POST', '/api/societes/liaisons', data) },
  retirer(id, motif) { return request('POST', `/api/societes/liaisons/${id}/retirer`, { motif }) },
}

export const facturesLieesAPI = {
  lister(lid, page = 1) { return request('GET', `/api/societes/liaisons/${lid}/correspondances?page=${page}`) },
  suivre(fid) { return request('GET', `/api/societes/liaisons/factures/${fid}/correspondance`) },
  options(lid, fid) { return request('GET', `/api/societes/liaisons/${lid}/factures/${fid}/options`) },
  apercu(lid, fid, data) { return request('POST', `/api/societes/liaisons/${lid}/factures/${fid}/apercu`, data) },
  creer(lid, fid, data) { return request('POST', `/api/societes/liaisons/${lid}/factures/${fid}`, data) },
}

export const avancesSalariesAPI = {
  lister() { return request('GET', '/api/employes/avances') },
  affecter(data) { return request('POST', '/api/employes/avances', data) },
  annuler(id, motif) { return request('POST', `/api/employes/avances/${id}/annuler`, { motif }) },
}

export const authAPI = {
  changerMotDePasse(mot_de_passe_actuel, nouveau_mot_de_passe) {
    return request('POST', '/api/auth/mot-de-passe', { mot_de_passe_actuel, nouveau_mot_de_passe })
  },
  async login(email, password) {
    const data = await request('POST', '/api/auth/login', { email, password }, false)
    setToken(data.access_token)
    setRole(data.role)
    return data
  },
  async register(nom, email, password, raison_sociale, ville = '') {
    const data = await request('POST', '/api/auth/register',
      { nom, email, password, raison_sociale, ville }, false)
    setToken(data.access_token)
    setRole(data.role)
    return data
  },
  async me() {
    const token = getToken()
    const data = await request('GET', '/api/auth/me')
    verifierJetonReponse(token)
    // Le serveur reste la source de vérité : toute lecture du profil
    // resynchronise le rôle local utilisé uniquement pour l'UX.
    setRole(data?.role)
    window.dispatchEvent(new CustomEvent('hisabpro-profil-relu',{detail:{role:data?.role}}))
    return data
  },
  logout()   { removeToken(); window.location.reload() },
}


export const dashboardAPI = {
  async commercial(exercice, dateReference = null) {
    const p = new URLSearchParams({ exercice })
    if (dateReference) p.append('date_reference', dateReference)
    return request('GET', `/api/dashboard/commercial?${p}`)
  },
}

export const ecrituresAPI = {
  async lister(exercice, { journal, dateFrom, dateTo, recherche, skip = null, limit = null } = {}) {
    const p = new URLSearchParams({ exercice })
    if (journal)   p.append('journal',   journal)
    if (dateFrom)  p.append('date_from', dateFrom)
    if (dateTo)    p.append('date_to',   dateTo)
    if (recherche) p.append('recherche', recherche)
    if (skip !== null && skip !== undefined) p.append('skip', skip)
    if (limit !== null && limit !== undefined) p.append('limit', limit)
    return request('GET', `/api/ecritures?${p}`)
  },
  async creer(ecriture)  { return request('POST',   '/api/ecritures', ecriture) },
  async modifier(id, ecriture) { return request('PATCH', `/api/ecritures/${id}`, ecriture) },
  async valider(id)      { return request('POST', `/api/ecritures/${id}/valider`) },
  async contrepasser(id, payload = {}) { return request('POST', `/api/ecritures/${id}/contrepasser`, payload) },
  async validerLot(ids)  { return request('POST', '/api/ecritures/valider-lot', { ids }) },
  async compteurAValider(exercice) { return request('GET', `/api/ecritures/a-valider/compteur?exercice=${exercice}`) },
  async supprimer(id)    { return request('DELETE', `/api/ecritures/${id}`) },
  async kpi(exercice)    { return request('GET',    `/api/ecritures/stats/kpi?exercice=${exercice}`) },
  async audit(id)        { return request('GET',    `/api/ecritures/${id}/audit`) },
  async auditJournal(exercice, limit = 200) { return request('GET', `/api/ecritures/audit/journal?exercice=${exercice}&limit=${limit}`) },
  async justificatifs(id) { return request('GET', `/api/ecritures/${id}/justificatifs`) },
  async ajouterJustificatif(id, data) { return request('POST', `/api/ecritures/${id}/justificatifs`, data) },
  async ajouterAuxiliaireComplement(id, ligneId, data) { return request('POST', `/api/ecritures/${id}/lignes/${ligneId}/auxiliaire-complement`, data) },
  async rechercherParPiece(reference, datePiece = null) {
    const p = new URLSearchParams({ reference })
    if (datePiece) p.append('date_piece', datePiece)
    return request('GET', `/api/ecritures/par-piece?${p}`)
  },
}

export const comptabiliteAPI = {
  balance(exercice, { dateFrom, dateTo } = {}) {
    const p = new URLSearchParams({ exercice })
    if (dateFrom) p.append('date_from', dateFrom)
    if (dateTo) p.append('date_to', dateTo)
    return request('GET', `/api/ecritures/reporting/balance?${p}`)
  },
  grandLivre(exercice, { dateFrom, dateTo } = {}) {
    const p = new URLSearchParams({ exercice })
    if (dateFrom) p.append('date_from', dateFrom)
    if (dateTo) p.append('date_to', dateTo)
    return request('GET', `/api/ecritures/reporting/grand-livre?${p}`)
  },
}

export const lettrageAPI = {
  lignes(exercice, compte) {
    const p = new URLSearchParams({ exercice, compte })
    return request('GET', `/api/lettrage/comptable?${p}`)
  },
  lettrer(ligneIds, code = null, partiel = false) {
    return request('POST', '/api/lettrage/comptable/lettrer', { ligne_ids: ligneIds, code, partiel })
  },
  delettrer(code) {
    return request('POST', `/api/lettrage/comptable/delettrer/${encodeURIComponent(code)}`)
  },
  auto(exercice, compte, tiers = '') {
    const p = new URLSearchParams({ exercice, compte })
    if (tiers) p.append('tiers', tiers)
    return request('POST', `/api/lettrage/comptable/auto?${p}`)
  },
}

export const rapprochementAPI = {
  propositions(compte, dateDebut, dateFin) {
    const p = new URLSearchParams({ date_debut: dateDebut, date_fin: dateFin })
    return request('GET', `/api/rapprochement/${encodeURIComponent(compte)}/propositions?${p}`)
  },
  confirmerPropositions(compte, data) {
    return request('POST', `/api/rapprochement/${encodeURIComponent(compte)}/rapprocher-propositions`, data)
  },
  situation(compte, dateDebut, dateFin) {
    const p = new URLSearchParams({ date_debut: dateDebut, date_fin: dateFin })
    return request('GET', `/api/rapprochement/${encodeURIComponent(compte)}/situation?${p}`)
  },
  ajouter(data) { return request('POST', '/api/rapprochement', data) },
  modifier(id, data) { return request('PATCH', `/api/rapprochement/${id}`, data) },
  supprimer(id) { return request('DELETE', `/api/rapprochement/${id}`) },
  rapprocher(id, ecritureLigneId) {
    return request('POST', `/api/rapprochement/${id}/rapprocher`, { ecriture_ligne_id: ecritureLigneId })
  },
  rapprocherVentilation(id, operationId) {
    return request('POST', `/api/rapprochement/${id}/rapprocher-ventilation`, { operation_id: operationId })
  },
  derapprocher(id) { return request('POST', `/api/rapprochement/${id}/derapprocher`) },
  enregistrerEtat(compte, data) {
    return request('PUT', `/api/rapprochement/${encodeURIComponent(compte)}/etat`, data)
  },
  importer(compte, lignes) { return request('POST', '/api/rapprochement/import', { compte, lignes }) },
}

export const facturesAPI = {
  async listerTout(exercice) {
    const token = getToken()
    return collecterPages(async pagination => {
      if (getToken() !== token) throw new Error('La société active a changé. Rechargez les factures.')
      const page = await facturesAPI.lister(exercice, pagination)
      if (getToken() !== token) throw new Error('La société active a changé. Rechargez les factures.')
      return page
    })
  },
  async lister(exercice, { type, statut, recherche, skip = 0, limit = 100 } = {}) {
    const p = new URLSearchParams({ exercice })
    if (type)      p.append('type',      type)
    if (statut)    p.append('statut',    statut)
    if (recherche) p.append('recherche', recherche)
    p.append('skip', skip)
    p.append('limit', limit)
    return request('GET', `/api/factures?${p}`)
  },
  async creer(facture)         { return request('POST',   '/api/factures', facture) },
  async mettreAJour(id, data)  { return request('PATCH',  `/api/factures/${id}`, data) },
  async supprimer(id)          { return request('DELETE', `/api/factures/${id}`) },
}


export const tvaAPI = {
  async declaration(exercice, { mois, trimestre } = {}) {
    const p = new URLSearchParams({ exercice })
    if (mois) p.append('mois', mois)
    if (trimestre) p.append('trimestre', trimestre)
    return request('GET', `/api/tva/declaration?${p}`)
  },
  async parametres(exercice) {
    return request('GET', `/api/tva/parametres/${exercice}`)
  },
  async enregistrerParametres(exercice, data) {
    return request('PUT', `/api/tva/parametres/${exercice}`, data)
  },
  async declarationsDeposees(exercice) {
    return request('GET', `/api/tva/declarations-deposees?${new URLSearchParams({ exercice })}`)
  },
  async deposer(data) {
    return request('POST', '/api/tva/declarations-deposees', data)
  },
}

export const employesAPI = {
  async lister()          { return request('GET',    '/api/employes') },
  async creer(emp)        { return request('POST',   '/api/employes', emp) },
  async modifier(id, emp) { return request('PUT',    `/api/employes/${id}`, emp) },
  async supprimer(id)     { return request('DELETE', `/api/employes/${id}`) },
  async cotisations(annee = new Date().getFullYear()) {
    return request('GET', `/api/employes/cotisations?annee=${annee}`)
  },
}

export const tiersAPI = {
  async lister({ type, recherche, skip = 0, limit = 200 } = {}) {
    const p = new URLSearchParams()
    if (type)      p.append('type',      type)
    if (recherche) p.append('recherche', recherche)
    p.append('skip', skip)
    p.append('limit', limit)
    return request('GET', `/api/tiers?${p}`)
  },
  async creer(tiers)        { return request('POST',   '/api/tiers', tiers) },
  async modifier(id, tiers) { return request('PUT',    `/api/tiers/${id}`, tiers) },
  async supprimer(id)       { return request('DELETE', `/api/tiers/${id}`) },
}

export const modelesAPI = {
  async parCompte(compte) {
    return request('GET', `/api/modeles/par-compte/${compte}`)
  },
  async lister() {
    return request('GET', '/api/modeles')
  },
}

// ─── Fiscalité IS ────────────────────────────────────────────────────────────
export const fiscaliteAPI = {
  situationIS(exercice) {
    return request('GET', `/api/fiscalite/is/${exercice}`)
  },
  enregistrerParametresIS(exercice, data) {
    return request('PUT', `/api/fiscalite/is/${exercice}/parametres`, data)
  },
  ajouterRetraitement(exercice, data) {
    return request('POST', `/api/fiscalite/is/${exercice}/retraitements`, data)
  },
  modifierRetraitement(id, data) {
    return request('PATCH', `/api/fiscalite/is/retraitements/${id}`, data)
  },
  supprimerRetraitement(id) {
    return request('DELETE', `/api/fiscalite/is/retraitements/${id}`)
  },
  ajouterDeficit(data) {
    return request('POST', '/api/fiscalite/deficits', data)
  },
  modifierDeficit(id, data) {
    return request('PATCH', `/api/fiscalite/deficits/${id}`, data)
  },
  supprimerDeficit(id) {
    return request('DELETE', `/api/fiscalite/deficits/${id}`)
  },
  enregistrerDeficitGenere(exercice) {
    return request('POST', `/api/fiscalite/is/${exercice}/deficits/enregistrer-genere`)
  },
  confirmerImputationDeficits(exercice) {
    return request('POST', `/api/fiscalite/is/${exercice}/deficits/confirmer-imputation`)
  },
  annulerImputationDeficits(exercice) {
    return request('DELETE', `/api/fiscalite/is/${exercice}/deficits/imputation`)
  },
  enregistrerAcompteIS(exercice, numero, data) {
    return request('PUT', `/api/fiscalite/is/${exercice}/acomptes/${numero}`, data)
  },
  supprimerAcompteIS(exercice, numero) {
    return request('DELETE', `/api/fiscalite/is/${exercice}/acomptes/${numero}`)
  },
  confirmerLiquidationIS(exercice) {
    return request('POST', `/api/fiscalite/is/${exercice}/liquidation/confirmer`)
  },
  ajouterCreditIS(exercice, data) {
    return request('POST', `/api/fiscalite/is/${exercice}/credits`, data)
  },
  supprimerCreditIS(exercice, id) {
    return request('DELETE', `/api/fiscalite/is/${exercice}/credits/${id}`)
  },
  enregistrerPaiementCSS(annee, data) {
    return request('PUT', `/api/fiscalite/is/${annee}/css/paiement`, data)
  },
  supprimerPaiementCSS(annee) {
    return request('DELETE', `/api/fiscalite/is/${annee}/css/paiement`)
  },
}

// ─── États de synthèse CGNC ────────────────────────────────────────────────
export const etatsAPI = {
  ventesPreparation(exercice) {
    return request('GET', `/api/etats/ventes/preparation/${exercice}`)
  },
  ventesPreparationExport(exercice, format, empreinte) {
    return downloadRequest(`/api/etats/ventes/preparation/${exercice}/export/${format}?empreinte=${encodeURIComponent(empreinte)}`)
  },
  preparationsBalance(exercice) {
    return request('GET', `/api/etats/liasse/balance/dossiers?exercice=${exercice}`)
  },
  preparationBalance(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}`)
  },
  preparationBalancePDF(id) {
    return downloadRequest(`/api/etats/liasse/balance/dossiers/${id}/pdf`)
  },
  preparationBalanceExcel(id) {
    return downloadRequest(`/api/etats/liasse/balance/dossiers/${id}/xlsx`)
  },
  preparationBalanceDossier(id) {
    return downloadRequest(`/api/etats/liasse/balance/dossiers/${id}/zip`)
  },
  preparationBalanceDocuments(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/documents`)
  },
  async joindreDocumentBalance(id, form) {
    const token = getToken()
    if (!token) throw new Error('Non connecté')
    const response = await fetch(`${BASE_URL}/api/etats/liasse/balance/dossiers/${id}/documents`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form,
    })
    verifierReponseSession(response, token)
    if (!response.ok) {
      const erreur = await response.json().catch(() => ({ detail: 'Envoi du justificatif impossible.' }))
      verifierJetonReponse(token)
      throw new Error(formatErreurAPI(erreur.detail))
    }
    const data = await response.json()
    verifierJetonReponse(token)
    return data
  },
  preparationBalanceDocument(id, documentId) {
    return downloadRequest(`/api/etats/liasse/balance/dossiers/${id}/documents/${documentId}`)
  },
  preparationBalanceDetail(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/detail`)
  },
  preparationBalanceEcheances(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/echeances`)
  },
  preparationBalanceRaccordsMouvements(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/raccords-mouvements`)
  },
  conserverBalanceRaccordsMouvements(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/raccords-mouvements`, data)
  },
  preparationBalanceMouvements(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/mouvements`)
  },
  conserverBalanceMouvements(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/mouvements`, data)
  },
  preparationBalanceCessions(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/cessions`)
  },
  conserverBalanceCessions(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/cessions`, data)
  },
  preparationBalanceEmetteurs(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/emetteurs`)
  },
  conserverBalanceEmetteurs(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/emetteurs`, data)
  },
  preparationBalanceC3Extra(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/c3-extra`)
  },
  conserverBalanceC3Extra(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/c3-extra`, data)
  },
  preparationBalanceComparatifN2(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/comparatif-n2`)
  },
  conserverBalanceComparatifN2(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/comparatif-n2`, data)
  },
  preparationBalanceIndicateurs(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/indicateurs-c3`)
  },
  conserverBalanceIndicateurs(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/indicateurs-c3`, data)
  },
  preparationBalanceTva(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/tva-documentaire`)
  },
  conserverBalanceTva(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/tva-documentaire`, data)
  },
  preparationBalanceLiquidationIS(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/liquidation-is`)
  },
  conserverBalanceLiquidationIS(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/liquidation-is`, data)
  },
  preparationBalanceAcomptesIS(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/acomptes-is`)
  },
  conserverBalanceAcomptesIS(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/acomptes-is`, data)
  },
  preparationBalanceTaxeProfessionnelle(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/taxe-professionnelle`)
  },
  conserverBalanceTaxeProfessionnelle(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/taxe-professionnelle`, data)
  },
  preparationBalanceRemunerationsTiers(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/remunerations-tiers`)
  },
  conserverBalanceRemunerationsTiers(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/remunerations-tiers`, data)
  },
  preparationBalanceCreditsIS(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/credits-is`)
  },
  conserverBalanceCreditsIS(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/credits-is`, data)
  },
  preparationBalanceCSS(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/css-documentaire`)
  },
  conserverBalanceCSS(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/css-documentaire`, data)
  },
  preparationBalanceCotisationMinimale(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/cotisation-minimale`)
  },
  conserverBalanceCotisationMinimale(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/cotisation-minimale`, data)
  },
  preparationBalanceContexteFiscal(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/contexte-fiscal`)
  },
  conserverBalanceContexteFiscal(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/contexte-fiscal`, data)
  },
  preparationBalancePassageFiscal(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/passage-fiscal`)
  },
  conserverBalancePassageFiscal(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/passage-fiscal`, data)
  },
  preparationBalanceResultatCourant(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/resultat-courant`)
  },
  conserverBalanceResultatCourant(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/resultat-courant`, data)
  },
  preparationBalanceParticipations(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/participations`)
  },
  conserverBalanceParticipations(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/participations`, data)
  },
  preparationBalanceNonValeurs(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/non-valeurs`)
  },
  conserverBalanceNonValeurs(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/non-valeurs`, data)
  },
  preparationBalanceCpcDetail(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/detail-cpc`)
  },
  conserverBalanceCpcDetail(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/detail-cpc`, data)
  },
  preparationBalanceAnnexesEtic(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/annexes-etic`)
  },
  conserverBalanceAnnexesEtic(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/annexes-etic`, data)
  },
  preparationBalanceTablesEtic(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/tables-etic`)
  },
  conserverBalanceTablesEtic(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/tables-etic`, data)
  },
  preparationBalanceNotesEtic(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/notes-etic`)
  },
  preparationBalanceFinancement(id) {
    return request('GET', `/api/etats/liasse/balance/dossiers/${id}/financement`)
  },
  conserverBalanceFinancement(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/financement`, data)
  },
  conserverBalanceNotesEtic(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/notes-etic`, data)
  },
  conserverBalanceEcheances(id, data) {
    return request('POST', `/api/etats/liasse/balance/dossiers/${id}/echeances`, data)
  },
  conserverBalance(data) {
    return request('POST', '/api/etats/liasse/balance/dossiers', data)
  },
  preparerBalance(lignes_n, lignes_n1 = null) {
    return request('POST', '/api/etats/liasse/balance/preview', { lignes_n, lignes_n1 })
  },
  source(exercice) {
    return request('GET', `/api/etats/source/${exercice}`)
  },
  etic(exercice) {
    return request('GET', `/api/etats/etic/${exercice}`)
  },
  enregistrerSectionETIC(exercice, code, contenu) {
    return request('PUT', `/api/etats/etic/${exercice}/${encodeURIComponent(code)}`, { contenu })
  },
  reinitialiserSectionETIC(exercice, code) {
    return request('DELETE', `/api/etats/etic/${exercice}/${encodeURIComponent(code)}`)
  },
  liasse(exercice) {
    return request('GET', `/api/etats/liasse/${exercice}`)
  },
  archiveLiasse(exercice) {
    return request('GET', `/api/etats/liasse/${exercice}/archive`)
  },
  finaliserLiasse(exercice) {
    return request('POST', `/api/etats/liasse/${exercice}/finaliser`)
  },
  telechargerLiassePDF(exercice, archive = false) {
    return downloadRequest(`/api/etats/liasse/${exercice}/pdf?archive=${archive ? 'true' : 'false'}`)
  },
}


export const delaisPaiementAPI = {
  rapport(annee, trimestre) {
    return request('GET', `/api/delais-paiement?annee=${annee}&trimestre=${trimestre}`)
  },
  completer(factureId, data) {
    return request('PATCH', `/api/delais-paiement/factures/${factureId}`, data)
  },
  exporterCSV(annee, trimestre) {
    return downloadRequest(`/api/delais-paiement/export.csv?annee=${annee}&trimestre=${trimestre}`)
  },
}


// ─── Plan comptable société / Exercices ───────────────────────────────────
export const planComptableAPI = {
  lister(inclureInactifs = true) {
    return request('GET', `/api/plan-comptable?inclure_inactifs=${inclureInactifs ? 'true' : 'false'}`)
  },
  creer(data) { return request('POST', '/api/plan-comptable', data) },
  modifier(numero, data) { return request('PATCH', `/api/plan-comptable/${encodeURIComponent(numero)}`, data) },
  supprimer(numero) { return request('DELETE', `/api/plan-comptable/${encodeURIComponent(numero)}`) },
}

export const exercicesAPI = {
  lister() { return request('GET', '/api/exercices') },
  modifier(annee, data) { return request('PATCH', `/api/exercices/${annee}`, data) },
  preparerSuivant(annee) { return request('POST', `/api/exercices/${annee}/preparer-suivant`) },
}

export const rasRapprochementsAPI = {
  lire(captureId) { return request('GET', `/api/tva/ras/captures/${captureId}/rapprochements`) },
  pdf(captureId) { return downloadRequest(`/api/tva/ras/captures/${captureId}/rapprochements/pdf`) },
  options(captureId, recherche = '', page = 1) {
    return request('GET', `/api/tva/ras/captures/${captureId}/rapprochements/options?recherche=${encodeURIComponent(recherche)}&page=${page}`)
  },
  creer(captureId, data) { return request('POST', `/api/tva/ras/captures/${captureId}/rapprochements`, data) },
  retirer(captureId, id, motif) { return request('POST', `/api/tva/ras/captures/${captureId}/rapprochements/${id}/retirer`, { motif }) },
}

export const rasTvaRegistreAPI = {
  lire(annee) { return request('GET', `/api/tva/ras/registre/${annee}`) },
  exporter(annee, format, empreinte) {
    return downloadRequest(`/api/tva/ras/registre/${annee}/export/${format}?empreinte=${encodeURIComponent(empreinte)}`)
  },
  preparation(annee, mois) { return request('GET', `/api/tva/ras/preparation/${annee}/${mois}`) },
  exporterPreparation(annee, mois, format, empreinte) {
    return downloadRequest(`/api/tva/ras/preparation/${annee}/${mois}/export/${format}?empreinte=${encodeURIComponent(empreinte)}`)
  },
}

export const clotureContrepassationsAPI = {
  lister(exercice, page = 1) { return request('GET', `/api/cloture/contrepassations?exercice=${exercice}&page=${page}`) },
}

export const reprisesProvisionsAPI = {
  preparation(id) { return request('GET', `/api/cloture/reprises-provisions/${id}/preparation`) },
  exporter(id, format, empreinte) { return downloadRequest(`/api/cloture/reprises-provisions/${id}/export/${format}?empreinte=${encodeURIComponent(empreinte)}`) },
  lister(page = 1) { return request('GET', `/api/cloture/reprises-provisions?page=${page}`) },
  apercu(id, faits) { return request('POST', `/api/cloture/reprises-provisions/${id}/apercu`, faits) },
  creer(id, faits) { return request('POST', `/api/cloture/reprises-provisions/${id}`, faits) },
  annuler(id, reprise, faits) { return request('POST', `/api/cloture/reprises-provisions/${id}/${reprise}/annuler`, faits) },
}

export const clotureProrataAPI = {
  calculer(exercice, faits) { return request('POST', `/api/cloture/ajustements/calcul-prorata?exercice=${exercice}`, faits) },
  pdf(exercice, faits, empreinte) {
    return downloadRequest(`/api/cloture/ajustements/calcul-prorata/pdf?exercice=${exercice}`, { ...faits, empreinte })
  },
}

export const paieFraisAnnuelsAPI = {
  lister(decalage=0) { return request('GET',`/api/employes/personnel/fiscalite/frais-annuels?decalage=${decalage}`) },
  lire(id) { return request('GET',`/api/employes/personnel/fiscalite/frais-annuels/${id}`) },
  options(id=null) { return request('GET','/api/employes/personnel/fiscalite/frais-annuels/options'+(id?`?employe_id=${encodeURIComponent(id)}`:'')) },
  simuler(data) { return request('POST','/api/employes/personnel/fiscalite/frais-annuels',data) },
}

export const paieBasesFiscalesAPI = {
  lister(decalage=0) { return request('GET',`/api/employes/personnel/fiscalite/preparations?decalage=${decalage}`) },
  lire(id) { return request('GET',`/api/employes/personnel/fiscalite/preparations/${id}`) },
  options(id) { return request('GET',`/api/employes/personnel/fiscalite/preparations/options?social_id=${encodeURIComponent(id)}`) },
  simuler(data) { return request('POST','/api/employes/personnel/fiscalite/preparations',data) },
}

export const paieIRAnnuelAPI = {
  depuisFrais(data) { return request('POST','/api/employes/personnel/fiscalite/depuis-frais-annuels',data) },
  exporter(id,format) { return downloadRequest(`/api/employes/personnel/fiscalite/${id}/export/${format}`) },
  lister(decalage=0) { return request('GET',`/api/employes/personnel/fiscalite?decalage=${decalage}`) },
  lire(id) { return request('GET',`/api/employes/personnel/fiscalite/${id}`) },
  referentiel() { return request('GET','/api/employes/personnel/fiscalite/referentiel') },
  simuler(data) { return request('POST','/api/employes/personnel/fiscalite',data) },
}

export const paieSocialCalculAPI = {
  lister(decalage=0) { return request('GET',`/api/employes/personnel/social/simulations?decalage=${decalage}`) },
  lire(id) { return request('GET',`/api/employes/personnel/social/simulations/${id}`) },
  options(id) { return request('GET',`/api/employes/personnel/social/simulations/options?brut_id=${encodeURIComponent(id)}`) },
  simuler(data) { return request('POST','/api/employes/personnel/social/simulations',data) },
}

export const paieSocialAPI = {
  lister({au,recherche='',regime='',decalage=0}) { const p=new URLSearchParams({au,recherche,decalage:String(decalage)});if(regime)p.set('regime',regime);return request('GET',`/api/employes/personnel/social?${p}`) },
  lire(id) { return request('GET',`/api/employes/personnel/social/${id}`) },
  creer(data) { return request('POST','/api/employes/personnel/social',data) },
  proposer(id,data) { return request('POST',`/api/employes/personnel/social/${id}/versions`,data) },
  decider(id,approbation,data) { return request('POST',`/api/employes/personnel/social/versions/${id}/${approbation?'approuver':'rejeter'}`,data) },
}

export const paieCatalogueAPI = {
  lister({au,recherche='',decalage=0}) { return request('GET', `/api/employes/personnel/elements?au=${encodeURIComponent(au)}&recherche=${encodeURIComponent(recherche)}&decalage=${decalage}`) },
  lire(id) { return request('GET', `/api/employes/personnel/elements/${id}`) },
  creer(data) { return request('POST', '/api/employes/personnel/elements', data) },
  proposer(id,data) { return request('POST', `/api/employes/personnel/elements/${id}/versions`, data) },
  decider(id,approbation,data) { return request('POST', `/api/employes/personnel/elements/versions/${id}/${approbation?'approuver':'rejeter'}`, data) },
  apercu(id,data) { return request('POST', `/api/employes/personnel/elements/versions/${id}/apercu`, data) },
}

export const paieVariablesAPI = {
  lister({periode=null,statut='',decalage=0}) { const p=new URLSearchParams({decalage:String(decalage)});if(periode)p.set('periode',periode);if(statut)p.set('statut',statut);return request('GET',`/api/employes/personnel/elements/variables?${p}`) },
  lire(id) { return request('GET',`/api/employes/personnel/elements/variables/${id}`) },
  options(params) { return request('GET',`/api/employes/personnel/elements/variables/options?${new URLSearchParams(params)}`) },
  creer(data) { return request('POST','/api/employes/personnel/elements/variables',data) },
  transition(id,action,data) { return request('POST',`/api/employes/personnel/elements/variables/${id}/${action}`,data) },
}

export const paieCampagnesAPI = {
  lister(decalage=0) { return request('GET',`/api/employes/personnel/traitement?decalage=${decalage}`) },
  options(params) { return request('GET',`/api/employes/personnel/traitement/options?${new URLSearchParams(params)}`) },
  simuler(data) { return request('POST','/api/employes/personnel/traitement/simulations',data) },
  lire(id) { return request('GET',`/api/employes/personnel/traitement/simulations/${id}`) },
  historique(id,decalage=0) { return request('GET',`/api/employes/personnel/traitement/campagnes/${id}/historique?decalage=${decalage}`) },
}

export const paieIRMensuelAPI = {
  lister(decalage=0) { return request('GET',`/api/employes/personnel/fiscalite/mensuel?decalage=${decalage}`) },
  lire(id) { return request('GET',`/api/employes/personnel/fiscalite/mensuel/${id}`) },
  simuler(data) { return request('POST','/api/employes/personnel/fiscalite/mensuel',data) },
}

// Lot 968 : bulletins, avances & prêts, paiements, comptabilisation, états de paie.
export const paieBulletinsAPI = {
  lister({ periode = null, annee = null } = {}) { const p = new URLSearchParams(); if (periode) p.set('periode', periode); if (annee) p.set('annee', String(annee)); return request('GET', `/api/employes/personnel/paie/bulletins?${p}`) },
  apercu(controleId) { return request('GET', `/api/employes/personnel/paie/bulletins/apercu?controle_id=${encodeURIComponent(controleId)}`) },
  lire(id) { return request('GET', `/api/employes/personnel/paie/bulletins/${id}`) },
  creer(data) { return request('POST', '/api/employes/personnel/paie/bulletins', data) },
  annuler(id, data) { return request('POST', `/api/employes/personnel/paie/bulletins/${id}/annuler`, data) },
  comptabiliser(data) { return request('POST', '/api/employes/personnel/paie/comptabiliser', data) },
  payer(data) { return request('POST', '/api/employes/personnel/paie/paiements', data) },
  etats(annee) { return request('GET', `/api/employes/personnel/paie/etats?annee=${encodeURIComponent(annee)}`) },
  calculerMois(data) { return request('POST', '/api/employes/personnel/paie/calculer-mois', data) },
  salaries() { return request('GET', '/api/employes/personnel/paie/salaries') },
  avances() { return request('GET', '/api/employes/personnel/paie/avances') },
  creerAvance(data) { return request('POST', '/api/employes/personnel/paie/avances', data) },
  annulerAvance(id, data) { return request('POST', `/api/employes/personnel/paie/avances/${id}/annuler`, data) },
  comptabiliserAvance(id) { return request('POST', `/api/employes/personnel/paie/avances/${id}/comptabiliser`) },
}
