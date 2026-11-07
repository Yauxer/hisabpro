import { useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { API_BASE, getToken, estAdmin, formatErreurAPI } from '../services/api.js'

const champ = { width: '100%', minWidth: 0, padding: '8px 10px', borderRadius: 6,
  border: '1px solid var(--border-light)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }
const bouton = { ...champ, width: 'auto', cursor: 'pointer', fontSize: 12 }

export default function GestionExercices() {
  const { annee, setAnnee, exercices, rechargerExercices } = useExercice()
  const [form, setForm] = useState(null)
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState('')
  const [message, setMessage] = useState('')

  async function modifierCalendrier(path, body, selectionner = false) {
    setErreur(''); setMessage(''); setEnCours(true)
    try {
      const response = await fetch(`${API_BASE}/api/exercices${path}`, {
        method: 'POST', headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        ...(body ? { body: JSON.stringify(body) } : {}),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(formatErreurAPI(data.detail) || `Erreur HTTP ${response.status}`)
      await rechargerExercices(selectionner ? data.annee : null)
      setForm(null)
      setMessage(selectionner ? `Exercice ${data.annee} disponible.` : 'Calendrier synchronisé.')
    } catch (error) { setErreur(error.message) }
    finally { setEnCours(false) }
  }

  function ouvrirCreation() {
    const suivante = Math.min(2200, Math.max(new Date().getFullYear() - 1, ...exercices.map(ex => ex.annee)) + 1)
    setErreur(''); setMessage('')
    setForm({ annee: suivante, date_debut: `${suivante}-01-01`, date_fin: `${suivante}-12-31` })
  }

  function creer(event) {
    event.preventDefault()
    modifierCalendrier('', { ...form, annee: Number(form.annee) }, true)
  }

  return (
    <section aria-label="Gestion des exercices" style={{ maxWidth: 780, margin: '0 auto 16px',
      padding: 18, border: '1px solid var(--border-light)', borderRadius: 10, background: 'var(--bg-primary)' }}>
      <h2 style={{ fontSize: 14, margin: '0 0 12px' }}>Gestion des exercices</h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <label htmlFor="gestion-exercice-selection">Exercice actif</label>
        <select id="gestion-exercice-selection" value={exercices.some(ex => ex.annee === annee) ? annee : ''}
          onChange={event => setAnnee(Number(event.target.value))} disabled={enCours || !exercices.length}
          style={{ ...champ, width: 'auto' }}>
          {!exercices.length && <option value="">Aucun exercice préparé</option>}
          {exercices.map(ex => <option key={ex.id} value={ex.annee}>{ex.libelle || ex.annee} · {ex.statut}</option>)}
        </select>
        {estAdmin() && <>
          <button type="button" style={bouton} disabled={enCours} onClick={ouvrirCreation}>Créer un exercice</button>
          <button type="button" style={bouton} disabled={enCours || !exercices.some(ex => ex.annee === annee)}
            onClick={() => modifierCalendrier(`/${annee}/preparer-suivant`, null, true)}>Préparer l'exercice suivant</button>
          <button type="button" style={bouton} disabled={enCours}
            onClick={() => modifierCalendrier('/synchroniser')}>Synchroniser le calendrier</button>
        </>}
      </div>
      {form && <form onSubmit={creer} style={{ marginTop: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
          <label>Année de clôture
            <input aria-label="Année de clôture du nouvel exercice" type="number" min="1900" max="2200" required
              value={form.annee} onChange={event => setForm({ ...form, annee: event.target.value })} style={champ} />
          </label>
          <label>Date de début
            <input aria-label="Date de début du nouvel exercice" type="date" required value={form.date_debut}
              onChange={event => setForm({ ...form, date_debut: event.target.value })} style={champ} />
          </label>
          <label>Date de clôture
            <input aria-label="Date de clôture du nouvel exercice" type="date" required value={form.date_fin}
              onChange={event => setForm({ ...form, date_fin: event.target.value })} style={champ} />
          </label>
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Vérifiez les dates avant création : la référence correspond à l'année de clôture. Le serveur contrôle la durée et les chevauchements.</p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" style={bouton} disabled={enCours}>Créer cet exercice</button>
          <button type="button" style={bouton} disabled={enCours} onClick={() => setForm(null)}>Annuler</button>
        </div>
      </form>}
      {erreur && <p role="alert" style={{ color: 'var(--red)', marginBottom: 0 }}>{erreur}</p>}
      {message && <p role="status" style={{ color: 'var(--text-secondary)', marginBottom: 0 }}>{message}</p>}
    </section>
  )
}
