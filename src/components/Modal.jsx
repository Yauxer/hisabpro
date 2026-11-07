import { useEffect } from 'react'
import styles from './Modal.module.css'

export default function Modal({ titre, icone, onFermer, children, largeur = 'md' }) {
  // Fermer avec Escape
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onFermer() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onFermer])

  // Empêcher le scroll du fond
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  return (
    <div className={styles.overlay} onClick={e => { if (e.target === e.currentTarget) onFermer() }}>
      <div className={`${styles.modal} ${styles[largeur]}`} role="dialog" aria-modal="true" aria-label={titre}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            {icone && <i className={`ti ${icone}`} aria-hidden="true" />}
            <span className={styles.titre}>{titre}</span>
          </div>
          <button className={styles.btnFermer} onClick={onFermer} aria-label="Fermer">
            <i className="ti ti-x" aria-hidden="true" />
          </button>
        </div>

        {/* Contenu */}
        <div className={styles.corps} data-form-surface>
          {children}
        </div>
      </div>
    </div>
  )
}
