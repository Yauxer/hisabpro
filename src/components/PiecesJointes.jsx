import { useState, useEffect, useRef } from 'react'
import { API_BASE, getToken, formatErreurAPI } from '../services/api.js'

const API = API_BASE

function formatTaille(bytes) {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`
  return `${(bytes / 1024 / 1024).toFixed(1)} Mo`
}

function iconeExt(nom) {
  const ext = nom.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'ti-file-type-pdf'
  if (['jpg','jpeg','png'].includes(ext)) return 'ti-photo'
  if (['xlsx','xls'].includes(ext)) return 'ti-file-spreadsheet'
  if (['doc','docx'].includes(ext)) return 'ti-file-word'
  return 'ti-paperclip'
}

export default function PiecesJointes({ docType, docId, readOnly = false, preserveExisting = false, onChange = null }) {
  const [fichiers, setFichiers]   = useState([])
  const [loading,  setLoading]    = useState(false)
  const [uploading, setUploading] = useState(false)
  const [erreur,   setErreur]     = useState('')
  const [contexteLu, setContexteLu] = useState('')
  const inputRef = useRef(null)
  const generation = useRef(0)
  const lecture = useRef(0)
  const token = getToken()
  const contexte = `${token || ''}:${docType}:${docId}`
  const dernierContexte = useRef(contexte)
  dernierContexte.current = contexte
  const courant = id => id === generation.current && getToken() === token && dernierContexte.current === contexte
  const fichiersVisibles = contexteLu === contexte ? fichiers : []
  const erreurVisible = contexteLu === contexte ? erreur : ''

  async function verifier(res, repli) {
    if (!res.ok) {
      const data = await res.json().catch(() => null)
      throw new Error(data?.detail ? formatErreurAPI(data.detail) : repli)
    }
  }

  async function charger(id = generation.current) {
    if (!docId || !courant(id)) return
    const requete = ++lecture.current
    setLoading(true); setErreur('')
    try {
      const res = await fetch(`${API}/api/attachments/${docType}/${docId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await verifier(res, 'documents indisponibles. Réessayez.')
      const liste = await res.json()
      if (!Array.isArray(liste)) throw new Error('Liste de documents invalide. Réessayez.')
      if (courant(id) && requete === lecture.current) setFichiers(liste)
    } catch (e) {
      if (courant(id) && requete === lecture.current) { setFichiers([]); setErreur(`Chargement des pièces impossible : ${e.message}`) }
    } finally { if (courant(id) && requete === lecture.current) setLoading(false) }
  }

  useEffect(() => {
    const id = ++generation.current
    setContexteLu(contexte); setFichiers([]); setErreur(''); setUploading(false); setLoading(false)
    charger(id)
    return () => { generation.current += 1 }
  }, [docType, docId, token])

  async function handleUpload(e) {
    const file = e.target.files?.[0]
    const id = generation.current
    if (!file || readOnly || !courant(id)) return
    setUploading(true); setErreur('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API}/api/attachments/${docType}/${docId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      })
      await verifier(res, 'Envoi impossible. Réessayez.')
      if (!courant(id)) return
      await charger(id)
      if (courant(id) && onChange) await onChange()
    } catch (e) { if (courant(id)) setErreur(e.message) }
    finally { if (courant(id)) { setUploading(false); if (inputRef.current) inputRef.current.value = '' } }
  }

  async function supprimer(nom) {
    const id = generation.current
    if (readOnly || preserveExisting || !courant(id)) return
    if (!confirm(`Supprimer "${nom}" ?`)) return
    if (!courant(id)) return
    setErreur('')
    try {
      const res = await fetch(`${API}/api/attachments/${docType}/${docId}/${encodeURIComponent(nom)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      await verifier(res, 'le fichier est conservé. Réessayez ou contactez votre administrateur.')
      if (!courant(id)) return
      setFichiers(prev => prev.filter(f => f.nom !== nom))
      if (courant(id) && onChange) await onChange()
    } catch (e) { if (courant(id)) setErreur(`Suppression impossible : ${e.message || 'réessayez.'}`) }
  }

  async function telecharger(f) {
    const id = generation.current
    if (!courant(id)) return
    setErreur('')
    try {
      const res = await fetch(`${API}${f.url}`, { headers: { Authorization: `Bearer ${token}` } })
      await verifier(res, 'document indisponible. Réessayez.')
      const blob = await res.blob()
      if (!courant(id)) return
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      try {
        a.href = url
        a.download = f.nom
        document.body.appendChild(a)
        a.click()
      } finally {
        a.remove()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      }
    } catch (e) { if (courant(id)) setErreur(`Téléchargement impossible : ${e.message || 'réessayez.'}`) }
  }

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ flex: 1, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 5 }}>
          <i className="ti ti-paperclip" />
          Pièces jointes {fichiersVisibles.length > 0 && `(${fichiersVisibles.length})`}
        </span>
        <button type="button" aria-label="Actualiser les pièces jointes" title="Actualiser les pièces jointes"
          disabled={loading || uploading || contexteLu !== contexte}
          onClick={() => charger()}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 4 }}><i className="ti ti-refresh" /><span className="libelle-action" aria-hidden="true">Actualiser les pièces jointes</span></button>
        {!readOnly && (
          <>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading || loading || contexteLu !== contexte}
              style={{ fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '0.5px solid var(--border-medium)',
                background: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 4 }}>
              <i className="ti ti-upload" />
              {uploading ? 'Envoi...' : 'Joindre un fichier'}
            </button>
            <input ref={inputRef} type="file" style={{ display: 'none' }}
              accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx"
              onChange={handleUpload} />
          </>
        )}
      </div>

      {erreurVisible && (
        <div role="alert" style={{ fontSize: 11, color: '#A32D2D', marginBottom: 6 }}>
          <i className="ti ti-alert-circle" style={{ marginRight: 4 }} />{erreurVisible}
        </div>
      )}

      {loading ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Chargement...</div>
      ) : fichiersVisibles.length === 0 ? (!erreurVisible && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
          Aucune pièce jointe
        </div>
      )) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {fichiersVisibles.map(f => (
            <div key={f.nom} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px 10px', borderRadius: 6,
              background: 'var(--bg-secondary)', border: '0.5px solid var(--border-light)',
            }}>
              <i className={`ti ${iconeExt(f.nom)}`} style={{ fontSize: 14, color: 'var(--blue)' }} />
              <span style={{ flex: 1, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {f.nom}
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
                {formatTaille(f.taille)}
              </span>
              <button type="button" onClick={() => telecharger(f)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--blue)', padding: 2 }}
                title="Télécharger"><i className="ti ti-download" style={{ fontSize: 13 }} /><span className="libelle-action" aria-hidden="true">Télécharger</span></button>
              {!readOnly && !preserveExisting && (
                <button type="button" onClick={() => supprimer(f.nom)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', padding: 2 }}
                  title="Supprimer"><i className="ti ti-x" style={{ fontSize: 13 }} /><span className="libelle-action" aria-hidden="true">Supprimer</span></button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
