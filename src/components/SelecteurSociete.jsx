import { useState, useEffect, useRef } from 'react'
import { API_BASE, getToken, setToken, setRole, formatErreurAPI } from '../services/api.js'
import styles from './SelecteurSociete.module.css'

export default function SelecteurSociete({ societeActuelle, onSwitch, peutCreer=true }) {
  const [ouvert,    setOuvert]    = useState(false)
  const [societes,  setSocietes]  = useState([])
  const [showForm,  setShowForm]  = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [nom,       setNom]       = useState('')
  const [ville,     setVille]     = useState('')
  const [erreur,    setErreur]    = useState('')
  const [switchEnCours, setSwitchEnCours] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    charger()
  }, [])

  useEffect(() => {
    function clickDehors(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOuvert(false)
        setShowForm(false)
      }
    }
    document.addEventListener('mousedown', clickDehors)
    return () => document.removeEventListener('mousedown', clickDehors)
  }, [])

  async function lireReponse(res) {
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: `Erreur HTTP ${res.status}` }))
      throw new Error(formatErreurAPI(body.detail))
    }
    return res.json()
  }

  async function charger() {
    const token = getToken()
    if (!token) return
    try {
      const res = await fetch(API_BASE + '/api/societes/mes-societes', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setSocietes(await lireReponse(res))
    } catch (e) {
      setErreur(e.message || 'Impossible de charger les sociétés.')
    }
  }

  async function switcher(societeId) {
    setErreur('')
    setSwitchEnCours(true)
    try {
      const token = getToken()
      if (!token) throw new Error('Session expirée : reconnectez-vous.')
      const res = await fetch(`${API_BASE}/api/societes/switcher/${societeId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await lireReponse(res)
      if (!data.access_token) throw new Error('Le serveur n’a pas retourné de session pour cette société.')
      setToken(data.access_token)
      setRole(data.role)
      // La sélection d'exercice est propre à chaque société. Ne pas hériter
      // de l'année choisie chez la précédente entreprise.
      localStorage.removeItem('hisabpro_exercice')
      setOuvert(false)
      onSwitch?.(data.societe)
      window.location.reload()
      return true
    } catch (e) {
      setErreur(e.message || 'Impossible de changer de société.')
      return false
    } finally {
      setSwitchEnCours(false)
    }
  }

  async function creerSociete() {
    if (!nom.trim()) return
    setErreur('')
    setLoading(true)
    try {
      const token = getToken()
      if (!token) throw new Error('Session expirée : reconnectez-vous.')
      const res = await fetch(API_BASE + '/api/societes/nouvelle', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ raison_sociale: nom.trim(), ville: ville.trim() || null }),
      })
      const data = await lireReponse(res)
      await charger()
      setShowForm(false)
      setNom(''); setVille('')
      await switcher(data.id)
    } catch (e) {
      setErreur(e.message || 'La création de la société a échoué.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.wrap} ref={ref}>
      <button className={styles.trigger} onClick={() => {
        if (!ouvert) { setErreur(''); charger() }
        setOuvert(p => !p)
      }}>
        <i className="ti ti-building" aria-hidden="true" />
        <span className={styles.nom}>{societeActuelle || 'Société'}</span>
        <i className={`ti ${ouvert ? 'ti-chevron-up' : 'ti-chevron-down'}`}
          style={{ fontSize: 12, opacity: 0.6 }} aria-hidden="true" />
      </button>

      {ouvert && (
        <div className={styles.dropdown}>
          <div className={styles.dropdownHeader}>Mes sociétés</div>

          {societes.map(s => (
            <button key={s.id} className={styles.societeItem}
              onClick={() => switcher(s.id)} disabled={loading || switchEnCours}>
              <div className={styles.societeIcone}>
                {s.raison_sociale.charAt(0).toUpperCase()}
              </div>
              <div className={styles.societeInfo}>
                <span className={styles.societeNom}>{s.raison_sociale}</span>
                {s.ville && <span className={styles.societeVille}>{s.ville}</span>}
              </div>
              {s.raison_sociale === societeActuelle && (
                <i className="ti ti-check" style={{ color: 'var(--blue)', fontSize: 14 }} aria-hidden="true" />
              )}
            </button>
          ))}

          <div className={styles.separator} />

          {erreur && <div role="alert" style={{ margin: '8px 10px', color: 'var(--red)', fontSize: 12, lineHeight: 1.45 }}>{erreur}</div>}

          {peutCreer&&(!showForm ? (
            <button className={styles.nouvelleSociete} onClick={() => { setErreur(''); setShowForm(true) }}>
              <i className="ti ti-plus" aria-hidden="true" />
              Nouvelle société
            </button>
          ) : (
            <div className={styles.miniForm} data-form-page>
              <input className={styles.miniInput} type="text"
                placeholder="Raison sociale *"
                value={nom} onChange={e => setNom(e.target.value)}
                autoFocus />
              <input className={styles.miniInput} type="text"
                placeholder="Ville"
                value={ville} onChange={e => setVille(e.target.value)} />
              <div className={styles.miniActions}>
                <button className={styles.miniAnnuler}
                  onClick={() => { setShowForm(false); setNom(''); setVille(''); setErreur('') }}>
                  Annuler
                </button>
                <button className={styles.miniCreer}
                  onClick={creerSociete}
                  disabled={!nom.trim() || loading || switchEnCours}>
                  {loading ? '...' : 'Créer'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
