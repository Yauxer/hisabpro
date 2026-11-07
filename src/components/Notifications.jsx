import { useEffect, useState } from 'react'
import { abonnerNotifications } from '../services/notifications.js'

const COULEURS = {
  info: { bord: 'var(--blue, #185FA5)', icone: 'ti-info-circle' },
  succes: { bord: 'var(--green, #3B6D11)', icone: 'ti-circle-check' },
  erreur: { bord: 'var(--red, #A32D2D)', icone: 'ti-alert-triangle' },
}

// Pile de notifications en bas à droite (pleine largeur sur mobile).
export default function Notifications() {
  const [liste, setListe] = useState([])

  useEffect(() => abonnerNotifications(n => {
    setListe(l => [...l.slice(-4), n])
    if (n.type !== 'erreur') setTimeout(() => setListe(l => l.filter(x => x.id !== n.id)), 6000)
  }), [])

  const fermer = id => setListe(l => l.filter(x => x.id !== id))
  if (!liste.length) return null
  return (
    <div className="notifications-pile">
      {liste.map(n => (
        // Région live sans rôle alert/status : annoncée par les lecteurs d'écran
        // sans interférer avec les messages alert/status propres à chaque écran.
        <div key={n.id} aria-live={n.type === 'erreur' ? 'assertive' : 'polite'} aria-atomic="true"
          data-notification={n.type} className="notification"
          style={{ borderLeftColor: COULEURS[n.type].bord }}>
          <i className={`ti ${COULEURS[n.type].icone}`} aria-hidden="true" style={{ color: COULEURS[n.type].bord }} />
          <span className="notification-texte">{n.texte}</span>
          <button type="button" className="notification-fermer" onClick={() => fermer(n.id)} aria-label="Fermer la notification">×</button>
        </div>
      ))}
    </div>
  )
}
