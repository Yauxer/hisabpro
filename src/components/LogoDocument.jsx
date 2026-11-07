import { useState } from 'react'

// Affichage uniquement : les nouvelles images sont validées par l'API société.
// Les anciennes URL/chemins restent ignorés, sans lecture réseau.
export default function LogoDocument({ societe }) {
  const [erreur, setErreur] = useState(null)
  const value = societe?.logo_url
  if (typeof value !== 'string' || value.length > 512 * 1024 * 4 / 3 + 40 || erreur === value ||
      !/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/]+={0,2}$/.test(value)) return null
  return <img src={value} alt={`Logo de ${societe?.raison_sociale || 'la société'}`}
    onError={() => setErreur(value)}
    style={{ width: '27mm', height: '14mm', objectFit: 'contain', objectPosition: 'left center', display: 'block', marginBottom: '2mm' }} />
}
