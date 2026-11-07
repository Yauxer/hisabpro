import { API_BASE } from './api.js'

function token() { return localStorage.getItem('hisabpro_token') }

export async function telechargerDocumentPDF(endpoint, nomFichier) {
  const res = await fetch(`${API_BASE}${endpoint}`, { headers: { Authorization: `Bearer ${token()}` } })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Erreur lors de la génération du PDF')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nomFichier
  document.body.appendChild(a)
  a.click()
  a.remove()
  // Révocation différée : immédiate, elle peut annuler le téléchargement.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return blob
}

async function emailTiers(tiersId) {
  if (!tiersId) return ''
  try {
    const res = await fetch(`${API_BASE}/api/tiers/${tiersId}`, { headers: { Authorization: `Bearer ${token()}` } })
    if (!res.ok) return ''
    const tiers = await res.json()
    return tiers.email || ''
  } catch {
    return ''
  }
}

export async function preparerEmailDocument({ endpoint, nomFichier, typeDocument, numero, tiers, tiersId }) {
  // Les navigateurs ne peuvent pas joindre automatiquement un fichier à un mailto.
  // On télécharge donc le PDF puis on ouvre un brouillon e-mail prérempli.
  await telechargerDocumentPDF(endpoint, nomFichier)
  const destinataire = await emailTiers(tiersId)
  const objet = `${typeDocument} ${numero || ''}`.trim()
  const corps = [
    `Bonjour${tiers ? ` ${tiers}` : ''},`,
    '',
    `Veuillez trouver ci-joint ${typeDocument.toLowerCase()} ${numero || ''}.`,
    '',
    `Le PDF vient d’être téléchargé : ${nomFichier}. Pensez à le joindre à ce message.`,
    '',
    'Cordialement,',
  ].join('\n')
  window.location.href = `mailto:${encodeURIComponent(destinataire)}?subject=${encodeURIComponent(objet)}&body=${encodeURIComponent(corps)}`
}
