import { useState } from 'react'
import { authAPI, removeToken } from '../services/api.js'
import styles from '../pages/Parametres.module.css'

export default function CompteSecurite() {
  const [actuel, setActuel] = useState('')
  const [nouveau, setNouveau] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [erreur, setErreur] = useState('')
  const [occupe, setOccupe] = useState(false)
  const [termine, setTermine] = useState(false)

  async function enregistrer(event) {
    event.preventDefault()
    setErreur('')
    if (nouveau.length < 8) return setErreur('Le mot de passe doit contenir au moins 8 caractères.')
    if (nouveau !== confirmation) return setErreur('La confirmation ne correspond pas au nouveau mot de passe.')
    if (nouveau === actuel) return setErreur('Choisissez un mot de passe différent du mot de passe actuel.')
    setOccupe(true)
    try {
      await authAPI.changerMotDePasse(actuel, nouveau)
      removeToken()
      setActuel(''); setNouveau(''); setConfirmation(''); setTermine(true)
    } catch (error) { setErreur(error.message) }
    finally { setOccupe(false) }
  }

  return <section className={styles.card} aria-label="Sécurité du compte personnel">
    <div className={styles.cardHeader}><h2 className={styles.cardTitle}>Mot de passe personnel</h2></div>
    <div className={styles.cardBody}>
      <p>Ce mot de passe protège votre compte dans toutes vos sociétés. Après le changement, reconnectez-vous.</p>
      {termine ? <div role="status">
        <p>Votre mot de passe a été modifié. Reconnectez-vous avec le nouveau mot de passe.</p>
        <button type="button" onClick={() => window.location.reload()}>Revenir à la connexion</button>
      </div> : <form onSubmit={enregistrer} style={{maxWidth: 440, display: 'grid', gap: 12}}>
        {erreur && <div role="alert">{erreur}</div>}
        <label>Mot de passe actuel
          <input className={styles.input} type="password" autoComplete="current-password" required disabled={occupe}
            value={actuel} onChange={e => setActuel(e.target.value)} />
        </label>
        <label>Nouveau mot de passe
          <input className={styles.input} type="password" autoComplete="new-password" required disabled={occupe}
            value={nouveau} onChange={e => setNouveau(e.target.value)} />
        </label>
        <label>Confirmer le nouveau mot de passe
          <input className={styles.input} type="password" autoComplete="new-password" required disabled={occupe}
            value={confirmation} onChange={e => setConfirmation(e.target.value)} />
        </label>
        <button type="submit" disabled={occupe}>{occupe ? 'Enregistrement…' : 'Modifier mon mot de passe'}</button>
      </form>}
    </div>
  </section>
}
