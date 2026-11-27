import { API_BASE } from './api.js'

// Lot 982 : sur la version de test (offre gratuite de Render), le serveur se met
// en veille après une période sans utilisation et met jusqu'à une minute à
// redémarrer ; la base Neon suspend aussi son calcul. On les réveille dès
// l'ouverture de l'application, pendant que l'utilisateur saisit ses
// identifiants. Un seul appel est partagé ; en cas d'échec, le suivant réessaie.
let enCours = null

export function reveillerServeur() {
  if (!enCours) {
    const debut = Date.now()
    enCours = fetch(`${API_BASE}/api/health/reveil`, { cache: 'no-store' })
      .then(r => ({ ok: r.ok, duree: Date.now() - debut }))
      .catch(() => ({ ok: false, duree: Date.now() - debut }))
      .then(resultat => { if (!resultat.ok) enCours = null; return resultat })
  }
  return enCours
}
