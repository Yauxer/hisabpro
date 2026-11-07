import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useModules } from '../data/ModulesContext.jsx'
import { personnelAPI, authAPI, getRole } from '../services/api.js'
import { notifier } from '../services/notifications.js'
import s from '../pages/Personnel.module.css'

// Mise en service de la paie : au lieu d'un message bloquant, on montre ce qui
// manque et un administrateur peut tout activer en une fois pour lui-même.
const REQUISES = ['personnel.lire_identite', 'personnel.lire_remuneration', 'personnel.proposer']
const TOUTES = [...REQUISES, 'personnel.soumettre', 'personnel.approuver', 'personnel.valider_regles_paie', 'personnel.audit_lire']

export function accesPaieManquant(ctx, aGRH) {
  if (ctx.chargement || ctx.erreur) return false
  const caps = ctx.acces?.capacites || []
  return !aGRH || ctx.acces?.mode !== 'protege' || !REQUISES.slice(0, 2).every(c => caps.includes(c))
}

export default function PaieAccesRequis({ ctx }) {
  const { aGRH, toggleModule, recharger: rechargerModules } = useModules()
  const [occupe, setOccupe] = useState(false), [erreur, setErreur] = useState(''), [seul, setSeul] = useState(true)
  const caps = ctx.acces?.capacites || []
  const admin = (ctx.user?.role || getRole()) === 'admin'
  const etapes = [
    { ok: aGRH, texte: 'Module Personnel & Paie activé pour la société' },
    { ok: aGRH && ctx.acces?.mode === 'protege', texte: 'Protection des données du personnel activée' },
    { ok: aGRH && REQUISES.every(c => caps.includes(c)), texte: 'Vos habilitations : identité, rémunération et préparation de la paie' },
  ]
  async function mettreEnService() {
    setOccupe(true); setErreur('')
    try {
      if (!aGRH) await toggleModule('paie_grh', true)
      let acces = await personnelAPI.acces()
      if (acces.mode !== 'protege') { await personnelAPI.activer('Mise en service de la paie'); acces = await personnelAPI.acces() }
      const moi = await authAPI.me()
      for (const capacite of TOUTES.filter(c => !(acces.capacites || []).includes(c))) {
        await personnelAPI.accorder({ utilisateur_id: moi.id, capacite, motif: 'Mise en service de la paie' })
      }
      if (seul && !acces.validation_unique) await personnelAPI.validationUnique(true, 'Petite entreprise : validation par une seule personne')
      notifier.succes('Paie mise en service : vous pouvez travailler.')
      await rechargerModules?.()
      await ctx.recharger()
    } catch (e) { setErreur(e.message) } finally { setOccupe(false) }
  }
  return <section className={s.carte} aria-label="Mise en service de la paie">
    <h2>Mise en service de la paie</h2>
    <p className={s.discret}>Avant de traiter la paie, trois réglages sont nécessaires pour cette société.</p>
    {aGRH && ctx.acces?.mode === 'protege' && !REQUISES.slice(0, 2).every(c => caps.includes(c)) && <p role="alert" className={s.notice}>Les habilitations identité et rémunération sont requises pour la paie.</p>}
    <ul className={s.historique} style={{ listStyle: 'none', padding: 0 }}>
      {etapes.map(e => <li key={e.texte}><i className={`ti ${e.ok ? 'ti-circle-check' : 'ti-circle-dashed'}`} aria-hidden="true" style={{ color: e.ok ? 'var(--green)' : 'var(--amber)' }} /> {e.texte} — <strong>{e.ok ? 'fait' : 'à faire'}</strong></li>)}
    </ul>
    {erreur && <p role="alert" className={s.erreur}>{erreur}</p>}
    {admin
      ? <div className={s.actions}>
          <label className={s.coche}><input type="checkbox" checked={seul} onChange={e => setSeul(e.target.checked)} />Je gère seul la paie : je peux préparer et valider moi-même (petite entreprise)</label>
          <button className={s.primaire} disabled={occupe} onClick={mettreEnService}>{occupe ? 'Mise en service…' : 'Tout activer maintenant'}</button>
          <Link className={s.lien} to="/personnel-paie/acces">Gérer les habilitations des autres utilisateurs</Link>
        </div>
      : <p className={s.notice}>Demandez à un administrateur de la société d’ouvrir une page Paie et de cliquer sur « Tout activer maintenant », ou de vous accorder les habilitations Personnel.</p>}
  </section>
}
