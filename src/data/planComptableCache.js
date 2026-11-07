// Patch 064 — cache de session exclusivement UI, jamais une autorité comptable.
// Le plan officiel et les droits d'écriture sont toujours vérifiés par l'API/DB.
// sessionStorage évite l'attente au rafraîchissement, sans garder les comptes
// sur le disque après fermeture de l'onglet ou déconnexion explicite.
import { remplacerPlanComptes } from './planComptes.js'

export const PREFIXE_CACHE_PLAN = 'hisabpro_plan_societe_v1:'
export const EVENEMENT_PLAN_MODIFIE = 'hisabpro:plan-comptable-modifie'
let lectureCle = null
let lectureComptes = []

function normaliserLecture(rows) {
  return rows.filter(c => c && (c.compte || c.numero)).map(c => ({
    compte: String(c.compte || c.numero), libelle: String(c.libelle || ''),
    classe: Number(c.classe), type: c.type || c.type_compte || 'SP',
    origine: c.origine || 'cgnc', actif: c.actif !== false,
  })).sort((a, b) => a.compte.localeCompare(b.compte))
}

function installerLecture(rows, cle) {
  const comptes = normaliserLecture(rows)
  const modifie = lectureCle !== cle || JSON.stringify(comptes) !== JSON.stringify(lectureComptes)
  lectureCle = cle; lectureComptes = comptes
  return modifie
}

// Lecture des comptes mouvementés, y compris désactivés. La sélection de
// nouveaux comptes continue d'utiliser exclusivement le PLAN_COMPTES actif.
export function trouverCompteLecture(numero, token) {
  const cle = cleCachePlan(token)
  if (!cle || cle !== lectureCle) return null
  return lectureComptes.find(c => c.compte === String(numero)) || null
}

export function cleCachePlan(token, societeId = null) {
  if (typeof token !== 'string') return null
  try {
    const encoded = token.split('.')[1]
    if (!encoded) return null
    // Le JWT n'est décodé QUE pour cloisonner une copie d'affichage locale ;
    // seul le backend authentifie les requêtes et valide les autorisations.
    const claims = JSON.parse(atob(encoded.replace(/-/g, '+').replace(/_/g, '/')))
    const uid = String(claims.sub || '')
    const sid = Number(claims.societe_id)
    if (!/^\d+$/.test(uid) || !Number.isSafeInteger(sid) || sid <= 0) return null
    if (societeId !== null && Number(societeId) !== sid) return null
    return `${PREFIXE_CACHE_PLAN}${uid}:${sid}`
  } catch {
    return null
  }
}

function stockageSession() {
  try { return window.sessionStorage } catch { return null }
}

export function restaurerPlanSociete(token, societeId = null) {
  const cle = cleCachePlan(token, societeId)
  const stockage = stockageSession()
  if (!cle || !stockage) return null
  try {
    const brut = stockage.getItem(cle)
    if (!brut) return null
    const cache = JSON.parse(brut)
    if (cache.version !== 1 || !Array.isArray(cache.comptes) || !cache.comptes.length) {
      stockage.removeItem(cle)
      return null
    }
    remplacerPlanComptes(cache.comptes)
    installerLecture(Array.isArray(cache.comptesLecture) ? cache.comptesLecture : cache.comptes, cle)
    return cle
  } catch {
    try { stockage.removeItem(cle) } catch { /* stockage indisponible */ }
    return null
  }
}

export function enregistrerPlanSociete(rows, token, societeId = null) {
  if (!Array.isArray(rows) || !rows.length) {
    throw new Error('Le serveur n’a renvoyé aucun compte pour cette société.')
  }
  const cle = cleCachePlan(token, societeId)
  if (!cle) throw new Error('Session société invalide : rechargez la page.')
  const comptesLecture = normaliserLecture(rows)
  const comptes = comptesLecture.filter(c => c.actif)
  if (!comptes.length) throw new Error('Le plan actif de cette société est vide.')
  const planModifie = remplacerPlanComptes(comptes)
  const lectureModifiee = installerLecture(comptesLecture, cle)
  const modifie = planModifie || lectureModifiee
  const stockage = stockageSession()
  try { stockage?.setItem(cle, JSON.stringify({ version: 1, comptes, comptesLecture })) }
  catch { /* quota/stockage privé : l'application fonctionne sans cache */ }
  return { cle, modifie }
}

export function notifierPlanModifie(cle) {
  if (cle && typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(EVENEMENT_PLAN_MODIFIE, { detail: { cle } }))
  }
}
