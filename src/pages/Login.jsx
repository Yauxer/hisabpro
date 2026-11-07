import { useState } from 'react'
import { authAPI } from '../services/api.js'
import styles from './Login.module.css'

export default function Login({ onConnecte }) {
  const [mode,      setMode]      = useState('login') // 'login' | 'register'
  const [loading,   setLoading]   = useState(false)
  const [erreur,    setErreur]    = useState('')

  // Champs login
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')

  // Champs register
  const [nom,            setNom]            = useState('')
  const [raisonSociale,  setRaisonSociale]  = useState('')
  const [ville,          setVille]          = useState('')

  async function handleLogin(e) {
    e.preventDefault()
    setErreur('')
    setLoading(true)
    try {
      await authAPI.login(email, password)
      onConnecte()
    } catch (err) {
      setErreur(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setErreur('')
    setLoading(true)
    try {
      await authAPI.register(nom, email, password, raisonSociale, ville)
      onConnecte()
    } catch (err) {
      setErreur(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.card}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoName}>HisabPro</div>
          <div className={styles.logoSub}>Comptabilité Marocaine</div>
        </div>

        {/* Toggle login / register */}
        <div className={styles.toggle}>
          <button
            className={`${styles.toggleBtn} ${mode === 'login' ? styles.toggleActif : ''}`}
            onClick={() => { setMode('login'); setErreur('') }}
          >
            Connexion
          </button>
          <button
            className={`${styles.toggleBtn} ${mode === 'register' ? styles.toggleActif : ''}`}
            onClick={() => { setMode('register'); setErreur('') }}
          >
            Créer un compte
          </button>
        </div>

        {/* Formulaire connexion */}
        {mode === 'login' && (
          <form onSubmit={handleLogin} className={styles.form}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Email</label>
              <input
                className={styles.input}
                type="email"
                placeholder="admin@societe.ma"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Mot de passe</label>
              <input
                className={styles.input}
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" aria-hidden="true" /> {erreur}</div>}
            <button className={styles.btnSubmit} type="submit" disabled={loading}>
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>
        )}

        {/* Formulaire inscription */}
        {mode === 'register' && (
          <form onSubmit={handleRegister} className={styles.form}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Votre nom</label>
              <input
                className={styles.input}
                type="text"
                placeholder="Prénom NOM"
                value={nom}
                onChange={e => setNom(e.target.value)}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Raison sociale</label>
              <input
                className={styles.input}
                type="text"
                placeholder="Ma Société SARL"
                value={raisonSociale}
                onChange={e => setRaisonSociale(e.target.value)}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Ville</label>
              <input
                className={styles.input}
                type="text"
                placeholder="Casablanca"
                value={ville}
                onChange={e => setVille(e.target.value)}
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Email</label>
              <input
                className={styles.input}
                type="email"
                placeholder="admin@societe.ma"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Mot de passe</label>
              <input
                className={styles.input}
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            {erreur && <div className={styles.erreur}><i className="ti ti-alert-circle" aria-hidden="true" /> {erreur}</div>}
            <button className={styles.btnSubmit} type="submit" disabled={loading}>
              {loading ? 'Création...' : 'Créer mon compte'}
            </button>
          </form>
        )}

        <div className={styles.footer}>
          HisabPro v1.0 — Conforme CGNC Maroc
        </div>
      </div>
    </div>
  )
}
