import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './BalancePreparationDetail.module.css'
export default function BalancePreparationComparatifN2({ dossier, onConserve }) {
  const [ouvert,setOuvert]=useState(false),[data,setData]=useState(null)
  const [attente,setAttente]=useState(false),[erreur,setErreur]=useState('')
  const [selection,setSelection]=useState(''),[reference,setReference]=useState(''),[confirme,setConfirme]=useState(false)
  const generation=useRef(0),vivant=useRef(true),cle=useRef(null)
  const token=getToken(),ecriture=peutEcrire()
  const actuel=n=>vivant.current && n===generation.current && getToken()===token
  useEffect(()=>{vivant.current=true;if(ouvert)charger();return()=>{vivant.current=false;generation.current+=1}},[ouvert])
  async function charger() {
    const n=++generation.current;setAttente(true);setErreur('');setData(null);setConfirme(false);cle.current=null
    try {
      const d=await etatsAPI.preparationBalanceComparatifN2(dossier.id)
      if(!actuel(n))return
      if(d.id!==dossier.id || d.empreinte_sha256!==dossier.empreinte_sha256)throw new Error('Version reçue différente de la préparation sélectionnée.')
      setData(d);setSelection(d.source_preparation ? String(d.source_preparation.id) : '');setReference(d.reference_source || '')
    }catch(e){if(actuel(n))setErreur(e.message)}finally{if(actuel(n))setAttente(false)}
  }
  function modifier(fn,v){cle.current=null;setConfirme(false);fn(v)}
  async function conserver(e) {
    e.preventDefault();const n=++generation.current;setAttente(true);setErreur('')
    try {
      const source=data.candidats.find(r=>String(r.id)===selection)
      if(!source || !reference.trim())throw new Error('Choisissez une préparation N-2 et sa référence explicite.')
      cle.current ||= cleIdempotence()
      const d=await etatsAPI.conserverBalanceComparatifN2(dossier.id,{empreinte_parent:dossier.empreinte_sha256,cle:cle.current,
        source_preparation_id:source.id,source_empreinte_sha256:source.empreinte_sha256,reference_source:reference})
      if(actuel(n))onConserve(d)
    }catch(e){if(actuel(n))setErreur(e.message)}finally{if(actuel(n))setAttente(false)}
  }
  return <details className={styles.detail} onToggle={e=>setOuvert(e.currentTarget.open)}>
    <summary>Rattacher une source N-2 aux indicateurs C3</summary>
    {ouvert && <section aria-label="Source comparative N-2 de la préparation" className={styles.detail}>
      <h3>Source N-2 — exercice {dossier.exercice-2}</h3>
      {attente && <p role="status">Chargement de la source N-2…</p>}
      {erreur && <div role="alert" className={styles.erreur}>{erreur}</div>}
      <button type="button" className={styles.bouton} disabled={attente} onClick={charger}>Relire la source N-2 conservée</button>
      {data && <>
        <p>{data.note}</p>
        {!data.conserve ? <p>Aucune source N-2 rattachée dans cette version.</p> : <section aria-label="Source N-2 conservée" className={styles.detail}>
          <p>Préparation source {data.source_preparation.id} · exercice {data.source_preparation.exercice} · version {data.source_preparation.version}</p>
          <p>Empreinte source : {data.source_preparation.empreinte_sha256}</p><p>Référence conservée : {data.reference_source}</p>
          <p>{data.totaux_exacts.comptes} comptes · débit {montantDecimalExact(data.totaux_exacts.debit)} MAD · crédit {montantDecimalExact(data.totaux_exacts.credit)} MAD</p>
          <p>Rattachée par {data.auteur.nom} le {data.conserve_le_utc} · version parent {data.parent.version}</p>
          <p>Le brouillon ne modifie pas cette source. Conservez les indicateurs C3 pour inclure N-2 dans un nouveau contrôle.</p>
        </section>}
        {!data.candidats.length && <p>Importer d’abord la balance N dans une préparation de l’exercice {dossier.exercice-2}, puis revenir ici. Aucun historique du Journal ne sera repris.</p>}
        {ecriture && <form className={styles.detail} onSubmit={conserver}>
          <label className={styles.champ}>Préparation N-2 à rattacher<select aria-label="Préparation N-2 à rattacher" disabled={attente} value={selection} onChange={e=>modifier(setSelection,e.target.value)}>
            <option value="">Choisir une préparation conservée</option>
            {data.candidats.map(r=><option key={r.id} value={r.id}>{r.exercice} · version {r.version} · préparation {r.id}</option>)}
          </select></label>
          <label className={styles.champ}>Référence explicite de la source N-2<textarea aria-label="Référence explicite de la source N-2" maxLength={2000} disabled={attente} value={reference} onChange={e=>modifier(setReference,e.target.value)} /></label>
          <label><input type="checkbox" disabled={attente} checked={confirme} onChange={e=>setConfirme(e.target.checked)} /> Je confirme la source et son exercice N-2, sans validation fiscale.</label>
          <button className={styles.bouton} disabled={attente || !confirme || !selection || !reference.trim()}>Rattacher N-2 dans une nouvelle version</button>
        </form>}
      </>}
    </section>}
  </details>
}
