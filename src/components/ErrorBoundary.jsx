import React from 'react'

/**
 * Filet de sécurité global : capture toute erreur de rendu React et affiche
 * un écran d'erreur exploitable au lieu d'une page blanche.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { erreur: null }
  }

  static getDerivedStateFromError(erreur) {
    return { erreur }
  }

  componentDidCatch(erreur, info) {
    console.error('Erreur de rendu interceptée :', erreur, info?.componentStack)
  }

  render() {
    if (this.state.erreur) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#F5F6F8', fontFamily: 'system-ui, sans-serif', padding: 24,
        }}>
          <div style={{
            maxWidth: 520, background: '#fff', borderRadius: 12, padding: '32px 36px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.08)', textAlign: 'center',
          }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
            <h1 style={{ fontSize: 18, margin: '0 0 8px 0', color: '#1E2A3A' }}>
              Une erreur inattendue s'est produite
            </h1>
            <p style={{ fontSize: 13, color: '#6B7280', margin: '0 0 16px 0' }}>
              La page n'a pas pu s'afficher. Vous pouvez recharger l'application —
              vos données enregistrées ne sont pas affectées.
            </p>
            <details style={{ textAlign: 'left', marginBottom: 20 }}>
              <summary style={{ fontSize: 12, color: '#6B7280', cursor: 'pointer' }}>
                Détail technique
              </summary>
              <pre style={{
                fontSize: 11, background: '#F5F6F8', padding: 10, borderRadius: 6,
                overflow: 'auto', maxHeight: 140, whiteSpace: 'pre-wrap',
              }}>
                {String(this.state.erreur?.stack || this.state.erreur)}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '9px 22px', borderRadius: 8, border: 'none',
                background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 500,
                cursor: 'pointer',
              }}>
              Recharger l'application
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
