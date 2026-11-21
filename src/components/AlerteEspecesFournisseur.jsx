import { useEffect, useState } from 'react'
import { tresorerieAPI } from '../services/api.js'

// Lot 981 : avertissement non bloquant (CGI 2026 art. 11-II et 106-II) quand
// les espèces versées à un fournisseur dépassent 5 000 DH par jour ou
// 50 000 DH par mois, en comptant le paiement en cours de saisie.
export default function AlerteEspecesFournisseur({ actif = true, mode, date, montant, tiersId, tiers, exclureReglementId }) {
  const [info, setInfo] = useState(null)
  const valeur = Number(String(montant ?? '').replace(',', '.'))
  const pret = actif && mode === 'especes' && date && valeur > 0 && (tiersId || String(tiers || '').trim())
  useEffect(() => {
    if (!pret) { setInfo(null); return undefined }
    let annule = false
    const t = setTimeout(() => {
      tresorerieAPI.especesFournisseur({ date, montant: valeur.toFixed(2), tiers_id: tiersId || undefined, tiers: tiersId ? undefined : tiers, exclure_reglement_id: exclureReglementId || undefined })
        .then(r => { if (!annule) setInfo(r) })
        .catch(() => { if (!annule) setInfo(null) })
    }, 350)
    return () => { annule = true; clearTimeout(t) }
  }, [pret, date, valeur, tiersId, tiers, exclureReglementId])
  if (!pret || !info?.depassement) return null
  return <div role="alert" aria-label="Limite des paiements en espèces" style={{ fontSize: 12, lineHeight: 1.45, padding: '8px 10px', borderRadius: 6, background: '#FAEEDA', color: '#854F0B' }}>
    <strong><i className="ti ti-alert-triangle" aria-hidden="true" style={{ marginRight: 4 }} />Paiement en espèces au-delà des limites fiscales</strong>
    {info.alertes.map(a => <div key={a}>{a}</div>)}
    <div>{info.consequence} <span style={{ opacity: 0.8 }}>({info.reference})</span></div>
  </div>
}
