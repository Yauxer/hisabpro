import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './BalancePreparationDetail.module.css'

const taille = n => n < 1024 ? `${n} o` : n < 1024 * 1024
  ? `${(n / 1024).toLocaleString('fr-MA', { maximumFractionDigits: 2 })} Ko`
  : `${(n / 1024 / 1024).toLocaleString('fr-MA', { maximumFractionDigits: 2 })} Mo`

export default function BalancePreparationDocuments({ dossier }) {
  const [ouvert, setOuvert] = useState(false), [data, setData] = useState(null)
  const [erreur, setErreur] = useState(''), [info, setInfo] = useState(''), [attente, setAttente] = useState(false)
  const [fichier, setFichier] = useState(null), [reference, setReference] = useState('')
  const generation = useRef(0), vivant = useRef(true), cle = useRef(null), input = useRef(null)
  const token = getToken(), writable = peutEcrire()
  const actuel = n => vivant.current && generation.current === n && getToken() === token
  useEffect(() => () => { vivant.current = false; generation.current += 1 }, [])
  useEffect(() => {
    vivant.current = true
    if (ouvert) charger()
    return () => { generation.current += 1 }
  }, [ouvert])

  function verifier(d) {
    if (d.id !== dossier.id || d.empreinte_sha256 !== dossier.empreinte_sha256) throw new Error('Justificatifs reçus pour une préparation différente. Rouvrez la version.')
    return d
  }

  async function charger() {
    const n = ++generation.current
    setAttente(true); setErreur(''); setData(null)
    try {
      const d = await etatsAPI.preparationBalanceDocuments(dossier.id)
      if (actuel(n)) setData(verifier(d))
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function joindre(e) {
    e.preventDefault()
    if (!fichier) return
    const n = ++generation.current
    setAttente(true); setErreur(''); setInfo('')
    let ajoute = false
    try {
      if (fichier.size > data.limite_fichier) throw new Error(`Fichier limité à ${taille(data.limite_fichier)}.`)
      cle.current ||= cleIdempotence()
      const form = new FormData()
      form.append('file', fichier); form.append('cle', cle.current)
      form.append('empreinte', dossier.empreinte_sha256); form.append('reference', reference)
      const r = await etatsAPI.joindreDocumentBalance(dossier.id, form)
      if (!r || !actuel(n)) return
      if (r.preparation_id !== dossier.id || r.empreinte_preparation !== dossier.empreinte_sha256) throw new Error('Réponse de justificatif différente de la source attendue.')
      ajoute = true
      setData(prev => {
        const documents = [r, ...prev.documents.filter(d => d.id !== r.id)]
        return { ...prev, documents, taille_totale: documents.reduce((total, d) => total + d.taille, 0) }
      })
      setInfo('Justificatif conservé avec sa trace et son empreinte.')
      setFichier(null); setReference(''); cle.current = null
      if (input.current) input.current.value = ''
      const d = await etatsAPI.preparationBalanceDocuments(dossier.id)
      if (actuel(n)) setData(verifier(d))
    } catch (e) { if (actuel(n)) setErreur((ajoute ? 'Justificatif ajouté ; actualisation à reprendre : ' : '') + e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  async function telecharger(r) {
    const n = ++generation.current
    setAttente(true); setErreur('')
    try {
      const f = await etatsAPI.preparationBalanceDocument(dossier.id, r.id)
      if (!f || !actuel(n)) return
      const url = URL.createObjectURL(f.blob)
      const a = document.createElement('a'); a.href = url; a.download = f.filename; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) { if (actuel(n)) setErreur(e.message) }
    finally { if (actuel(n)) setAttente(false) }
  }

  return <details className={styles.detail} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Justificatifs complémentaires de cette version</summary>
    {ouvert && <section aria-label="Justificatifs de la préparation" className={styles.detail}>
      <h3>Documents de la version {dossier.version}</h3>
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Actualiser les justificatifs de préparation</button>
      {attente && <p role="status">Chargement des justificatifs…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {info && <p role="status">{info}</p>}
      {data && <>
        <p>{data.note}</p>
        <p>Fichier : {taille(data.limite_fichier)} maximum · Total de cette version : {taille(data.taille_totale)} sur {taille(data.limite_dossier)}.</p>
        <p>Les tailles et empreintes affichées sont celles conservées à l’ajout. Les octets sont contrôlés au téléchargement et dans le dossier ZIP. Un fichier absent ou modifié bloque sa délivrance.</p>
        {!data.documents.length && <p>Aucun justificatif complémentaire sur cette version.</p>}
        {data.documents.map(r => <article key={r.id} aria-label={`Justificatif ${r.id}`} className={styles.detail}>
          <strong>{r.nom_original}</strong>
          <p>{r.reference} · {taille(r.taille)} · ajouté le {r.created_at.slice(0, 10)} par {r.acteur_nom || `utilisateur #${r.created_by}`}</p>
          <p>SHA-256 conservé : {r.sha256}</p>
          <button type="button" className={styles.bouton} disabled={attente} onClick={() => telecharger(r)}>Télécharger le justificatif #{r.id}</button>
        </article>)}
        {writable && <form onSubmit={joindre} className={styles.detail}>
          <label className={styles.champ}>Fichier justificatif<input ref={input} aria-label="Fichier justificatif" type="file" required disabled={attente} accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx" onChange={e => { setFichier(e.target.files?.[0] || null); cle.current = null; setInfo('') }} /></label>
          <label className={styles.champ}>Référence documentaire facultative<input aria-label="Référence documentaire facultative" maxLength={500} value={reference} disabled={attente} onChange={e => { setReference(e.target.value); cle.current = null }} /></label>
          <button className={styles.bouton} disabled={attente || !fichier}>Joindre et conserver le justificatif</button>
          <p>Le nom du fichier sert de référence si le champ est vide. Les ajouts sont conservés dans l’historique de cette version.</p>
        </form>}
        <p>Le dossier de préparation ZIP inclut les justificatifs de cette version, leurs métadonnées et leurs empreintes. Il reste un dossier interne à compléter.</p>
      </>}
    </section>}
  </details>
}
