import { useEffect, useRef, useState } from 'react'
import { clotureProrataAPI, getToken } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './CalculProrataInventaire.module.css'

export default function CalculProrataInventaire({ exercice, dateFin, peutReprendre, onReprendre }) {
  const [form, setForm] = useState({ type: 'cca', reference: '', montant: '', base: '', date_debut: '', date_fin: '' })
  const [resultat, setResultat] = useState(null)
  const [erreur, setErreur] = useState('')
  const [action, setAction] = useState('')
  const token = getToken()
  const cle = JSON.stringify([form, exercice, dateFin, token])
  const courante = useRef(cle)
  courante.current = cle
  const generation = useRef(0)
  const actuel = resultat?.cle === cle ? resultat.data : null
  useEffect(() => {
    generation.current += 1; setAction(''); setErreur(''); setResultat(null)
    return () => { generation.current += 1 }
  }, [cle])
  const faits = () => ({ ...form, montant: form.montant.trim().replace(',', '.'), convention: 'jours_calendaires_inclusifs' })
  const changer = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function calculer() {
    const id = ++generation.current, depart = cle
    setAction('calcul'); setErreur(''); setResultat(null)
    try {
      const d = await clotureProrataAPI.calculer(exercice, faits())
      if (id === generation.current && depart === courante.current && getToken() === token) setResultat({ cle: depart, data: d })
    } catch (e) { if (id === generation.current && depart === courante.current) setErreur(e.message) }
    finally { if (id === generation.current) setAction('') }
  }

  async function exporter() {
    if (!actuel || action) return
    const id = generation.current, depart = cle
    setAction('pdf'); setErreur('')
    try {
      const r = await clotureProrataAPI.pdf(exercice, faits(), actuel.empreinte_sha256)
      if (!r || id !== generation.current || depart !== courante.current || getToken() !== token) return
      const url = URL.createObjectURL(r.blob), lien = document.createElement('a')
      lien.href = url; lien.download = r.filename; document.body.appendChild(lien); lien.click(); lien.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      if (id === generation.current && depart === courante.current) { setErreur(e.message); setResultat(null) }
    } finally { if (id === generation.current) setAction('') }
  }

  async function reprendre() {
    if (!actuel || !peutReprendre || action || actuel.montant_reporte === '0.00') return
    const id = generation.current, depart = cle
    setAction('reprise'); setErreur('')
    try {
      const d = await clotureProrataAPI.calculer(exercice, faits())
      if (id !== generation.current || depart !== courante.current || getToken() !== token) return
      if (d.empreinte_sha256 !== actuel.empreinte_sha256) {
        setResultat(null); setErreur('Le calendrier ou les données ont changé. Recalculez avant de reprendre.'); return
      }
      onReprendre(d.faits.type, d.montant_reporte, d.libelle_propose)
    } catch (e) {
      if (id === generation.current && depart === courante.current) { setErreur(e.message); setResultat(null) }
    } finally { if (id === generation.current) setAction('') }
  }

  return <details className={styles.panel}>
    <summary>Calcul documentaire facultatif CCA / PCA</summary>
    <section className={styles.region} aria-label="Calcul documentaire CCA PCA">
      <p>Répartition choisie en jours calendaires inclusifs. Saisissez le montant déjà comptabilisé et la période justifiée par votre contrat. Aucun calcul de TVA ou de déductibilité fiscale.</p>
      <p>Clôture du calendrier sélectionné : <strong>{dateFin}</strong>. Ce calcul ne crée aucune écriture.</p>
      <div className={styles.champs}>
        <label>Type de report<select aria-label="Type de report" value={form.type} onChange={e => changer('type', e.target.value)}><option value="cca">CCA · charge</option><option value="pca">PCA · produit</option></select></label>
        <label>Référence du contrat ou de la pièce<input maxLength={80} value={form.reference} onChange={e => changer('reference', e.target.value)} /></label>
        <label>Montant déjà comptabilisé (MAD)<input inputMode="decimal" value={form.montant} onChange={e => changer('montant', e.target.value)} /></label>
        <label>Base du montant<select aria-label="Base du montant" value={form.base} onChange={e => changer('base', e.target.value)}><option value="">À préciser</option><option value="ht">HT déclaré</option><option value="ttc">TTC déclaré</option><option value="autre">Autre base déclarée</option></select></label>
        <label>Début de la période<input type="date" value={form.date_debut} onChange={e => changer('date_debut', e.target.value)} /></label>
        <label>Fin de la période<input type="date" value={form.date_fin} onChange={e => changer('date_fin', e.target.value)} /></label>
      </div>
      <div className={styles.actions}><button type="button" disabled={Boolean(action)} onClick={calculer}>{action === 'calcul' ? 'Calcul…' : 'Calculer en jours calendaires'}</button></div>
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {actuel && <section className={styles.resultat} aria-label="Résultat du calcul documentaire">
        <p>{actuel.jours_apres_cloture} / {actuel.jours_total} jours après la clôture · {actuel.arrondi}</p>
        <p><strong>Part à reporter : {montantDecimalExact(actuel.montant_reporte)} MAD</strong></p>
        <p>Part non reportée par ce calcul : {montantDecimalExact(actuel.montant_non_reporte)} MAD</p>
        <p>Libellé proposé : {actuel.libelle_propose}</p>
        <p>{actuel.note}</p>
        <div className={styles.actions}>
          <button type="button" onClick={exporter} disabled={Boolean(action)}>{action === 'pdf' ? 'Téléchargement…' : 'Télécharger la feuille PDF'}</button>
          <button type="button" disabled={!peutReprendre || Boolean(action) || actuel.montant_reporte === '0.00'} onClick={reprendre}>{action === 'reprise' ? 'Vérification…' : 'Utiliser le montant et le libellé'}</button>
        </div>
        {actuel.montant_reporte === '0.00' && <p>Montant nul : aucun ajustement proposé.</p>}
        <p>Les comptes restent à vérifier dans le formulaire. Toute modification du montant ou de la période nécessite une nouvelle vérification ; conservez la feuille correspondante avec vos pièces.</p>
      </section>}
    </section>
  </details>
}
