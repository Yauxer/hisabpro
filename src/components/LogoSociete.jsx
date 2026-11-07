import { useState } from 'react'
import styles from '../pages/Parametres.module.css'

const MAX_LOGO_BYTES = 512 * 1024
const estLogoIntegre = value => /^data:image\/(png|jpeg);base64,[A-Za-z0-9+/]+={0,2}$/.test(value || '')

export default function LogoSociete({ value, onChange, disabled }) {
  const [erreur, setErreur] = useState('')
  const [lecture, setLecture] = useState(false)
  const [apercuErreur, setApercuErreur] = useState(null)

  async function choisir(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setErreur('')
    if (!['image/png', 'image/jpeg'].includes(file.type)) return setErreur('Choisissez une image PNG ou JPEG.')
    if (file.size > MAX_LOGO_BYTES) return setErreur('Le logo doit peser au maximum 512 Ko.')
    setLecture(true)
    try {
      const data = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = () => reject(new Error('Impossible de lire cette image.'))
        reader.readAsDataURL(file)
      })
      await new Promise((resolve, reject) => {
        const image = new Image()
        image.onload = () => image.naturalWidth * image.naturalHeight <= 4000000
          ? resolve() : reject(new Error('Le logo doit contenir au maximum 4 millions de pixels.'))
        image.onerror = () => reject(new Error('Le logo PNG/JPEG est illisible ou invalide.'))
        image.src = data
      })
      setApercuErreur(null)
      onChange(data)
    } catch (error) { setErreur(error.message) }
    finally { setLecture(false) }
  }

  const apercu = estLogoIntegre(value) && apercuErreur !== value
  return <div>
    <label htmlFor="societe-logo" style={{ display: 'block', marginBottom: 6 }}>Logo de la société</label>
    <p id="societe-logo-aide" style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 10px' }}>
      Facultatif · PNG ou JPEG · 512 Ko maximum. Le logo sera repris dans les documents PDF et Excel générés par HisabPro.
    </p>
    {apercu && <img src={value} alt="Aperçu du logo de la société" onError={() => setApercuErreur(value)}
      style={{ maxWidth: 180, maxHeight: 90, objectFit: 'contain', display: 'block', marginBottom: 10 }} />}
    {!!value && !apercu && <p role="status" style={{ fontSize: 12 }}>Logo existant enregistré. L'aperçu de ce format n'est pas disponible.</p>}
    <input id="societe-logo" className={styles.input} type="file" accept="image/png,image/jpeg" aria-describedby="societe-logo-aide"
      onChange={choisir} disabled={disabled || lecture} />
    {!!value && <button type="button" className={styles.btnSec} disabled={disabled || lecture}
      onClick={() => { setErreur(''); setApercuErreur(null); onChange('') }} style={{ marginTop: 8 }}>Retirer le logo</button>}
    {lecture && <p role="status">Lecture du logo…</p>}
    {erreur && <p role="alert" style={{ color: 'var(--red)', fontSize: 12 }}>{erreur}</p>}
    {disabled && <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Seul un administrateur peut modifier le logo.</p>}
  </div>
}
