import { useEffect, useRef, useState } from 'react'
import { estAdmin, getToken, societesLieesAPI } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import styles from './SocietesLiees.module.css'
import SuiviCorrespondances from './SuiviCorrespondances.jsx'

export default function SocietesLiees({ societeId }) {
  return <Panneau key={`${societeId}|${getToken()}`} societeId={societeId} />
}

function Panneau({ societeId }) {
  const token = getToken(), vivant = useRef(true), sequence = useRef(0)
  const [liste, setListe] = useState(null), [societes, setSocietes] = useState([])
  const [options, setOptions] = useState(null), [attente, setAttente] = useState(false)
  const [erreur, setErreur] = useState(''), [message, setMessage] = useState('')
  const [form, setForm] = useState({ acheteur_id: '', client_id: '', fournisseur_id: '', justification: '', association_verifiee: false })
  const [cle, setCle] = useState(cleIdempotence), [retrait, setRetrait] = useState(null)
  const actuel = () => vivant.current && getToken() === token
  useEffect(() => {
    vivant.current = true; charger()
    return () => { vivant.current = false; sequence.current += 1 }
  }, [])

  async function charger() {
    const id = ++sequence.current
    setAttente(true); setErreur('')
    try {
      const [ls, ss] = await Promise.all([societesLieesAPI.lister(), societesLieesAPI.societes()])
      if (actuel() && sequence.current === id) {
        setListe(ls); setSocietes(ss.filter(s => s.id !== societeId && s.role === 'admin'))
      }
    } catch (e) { if (actuel() && sequence.current === id) setErreur(e.message) }
    finally { if (actuel() && sequence.current === id) setAttente(false) }
  }
  function modifier(nom, valeur) {
    setForm(f => ({ ...f, [nom]: valeur, ...(nom !== 'association_verifiee' ? { association_verifiee: false } : {}) }))
    setCle(cleIdempotence()); setMessage(''); setErreur('')
  }
  async function choisir(id) {
    const seq = ++sequence.current
    setForm(f => ({ ...f, acheteur_id: id, client_id: '', fournisseur_id: '', association_verifiee: false }))
    setCle(cleIdempotence()); setOptions(null); setErreur(''); setMessage('')
    if (!id) return
    setAttente(true)
    try { const o = await societesLieesAPI.options(id); if (actuel() && seq === sequence.current) setOptions(o) }
    catch (e) { if (actuel() && seq === sequence.current) setErreur(e.message) }
    finally { if (actuel() && seq === sequence.current) setAttente(false) }
  }
  async function creer(e) {
    e.preventDefault(); setAttente(true); setErreur(''); setMessage('')
    try {
      const d = await societesLieesAPI.creer({ ...form, cle, acheteur_id: Number(form.acheteur_id), client_id: Number(form.client_id), fournisseur_id: Number(form.fournisseur_id) })
      if (actuel()) {
        setListe(l => [d, ...l.filter(x => x.id !== d.id)])
        setForm({ acheteur_id: '', client_id: '', fournisseur_id: '', justification: '', association_verifiee: false })
        setOptions(null); setCle(cleIdempotence()); setMessage('Liaison enregistrée. Aucune facture ni écriture créée.')
      }
    } catch (e) { if (actuel()) setErreur(e.message) }
    finally { if (actuel()) setAttente(false) }
  }
  async function retirer(e) {
    e.preventDefault(); setAttente(true); setErreur(''); setMessage('')
    try {
      await societesLieesAPI.retirer(retrait.id, retrait.motif)
      if (actuel()) { setRetrait(null); setMessage('Liaison retirée. Historique conservé.'); await charger() }
    } catch (e) { if (actuel()) setErreur(e.message) }
    finally { if (actuel()) setAttente(false) }
  }
  return <section className={styles.card} aria-label="Sociétés liées">
    <h2>Sociétés liées</h2>
    <p>Associez explicitement un vendeur, un acheteur et leurs tiers respectifs. Cette liaison commerciale ne constitue pas une qualification fiscale de groupe.</p>
    <button type="button" disabled={attente} onClick={charger}>Actualiser les liaisons</button>
    {attente && <p role="status">Chargement…</p>}
    {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
    {message && <p role="status">{message}</p>}
    {estAdmin() && liste && <form onSubmit={creer}>
      <h3>Associer un acheteur à la société active vendeuse</h3>
      <p>Il faut être administrateur dans les deux sociétés. Créez d’abord le client chez le vendeur et le fournisseur chez l’acheteur.</p>
      <fieldset disabled={attente}>
        <div className={styles.grille}>
          <label>Société acheteuse<select aria-label="Société acheteuse" required value={form.acheteur_id} onChange={e => choisir(e.target.value)}>
            <option value="">Choisir une société</option>{societes.map(s => <option key={s.id} value={s.id}>{s.raison_sociale}</option>)}
          </select></label>
          {options && <>
            <label>Client chez le vendeur<select aria-label="Client chez le vendeur" required value={form.client_id} onChange={e => modifier('client_id', e.target.value)}>
              <option value="">Choisir le client représentant l’acheteur</option>{options.clients.map(t => <option key={t.id} value={t.id}>{t.nom}{t.ice ? ` · ICE ${t.ice}` : ''}</option>)}
            </select></label>
            <label>Fournisseur chez l’acheteur<select aria-label="Fournisseur chez l’acheteur" required value={form.fournisseur_id} onChange={e => modifier('fournisseur_id', e.target.value)}>
              <option value="">Choisir le fournisseur représentant le vendeur</option>{options.fournisseurs.map(t => <option key={t.id} value={t.id}>{t.nom}{t.ice ? ` · ICE ${t.ice}` : ''}</option>)}
            </select></label>
          </>}
        </div>
        <label>Justification de la liaison<textarea required maxLength={500} value={form.justification} onChange={e => modifier('justification', e.target.value)} /></label>
        <label className={styles.confirmation}><input type="checkbox" checked={form.association_verifiee} onChange={e => modifier('association_verifiee', e.target.checked)} />J’ai vérifié les deux sociétés et les tiers qui les représentent.</label>
        <button disabled={!form.association_verifiee || !options || !form.client_id || !form.fournisseur_id} type="submit">Enregistrer la liaison</button>
      </fieldset>
      {societes.length === 0 && <p>Aucune autre société n’est accessible avec un rôle administrateur.</p>}
    </form>}
    {liste?.length === 0 && <p>Aucune liaison accessible dans les deux sociétés.</p>}
    {liste?.map(l => <article key={l.id} className={styles.liaison}>
      <strong>{l.vendeur} → {l.acheteur}</strong>
      <p>Client : {l.client} · Fournisseur : {l.fournisseur}</p>
      <p>{l.justification} · {l.active ? 'Active' : `Retirée : ${l.motif_retrait}`}</p>
      <SuiviCorrespondances liaisonId={l.id} active={l.active} />
      {estAdmin() && l.active && <button type="button" disabled={attente} onClick={() => setRetrait({ id: l.id, motif: '' })}>Retirer la liaison {l.id}</button>}
    </article>)}
    {retrait && <form onSubmit={retirer} aria-label="Retrait de liaison"><fieldset disabled={attente}>
      <label>Motif du retrait<input required maxLength={500} value={retrait.motif} onChange={e => setRetrait(r => ({ ...r, motif: e.target.value }))} /></label>
      <div className={styles.actions}><button type="submit">Confirmer le retrait</button><button type="button" onClick={() => setRetrait(null)}>Annuler</button></div>
    </fieldset></form>}
  </section>
}
