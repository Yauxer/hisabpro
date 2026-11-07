import {useEffect,useState} from 'react'
import {facturesConservationAPI as api} from '../services/api.js'
import s from '../pages/Factures.module.css'

export default function FactureConservation({facture,peutModifier}){
  const [copie,setCopie]=useState(null),[motif,setMotif]=useState(''),[confirme,setConfirme]=useState(false),[erreur,setErreur]=useState(''),[charge,setCharge]=useState(false),[pret,setPret]=useState(false),[message,setMessage]=useState(''),[revision,setRevision]=useState(0)
  useEffect(()=>{let actif=true;setCopie(null);setPret(false);setErreur('');setMessage('');api.consulter(facture.id).then(r=>{if(actif){setCopie(r.copie);setPret(r.disponible);setMessage(r.message||'')}}).catch(e=>{if(actif)setErreur(e.message)});return()=>{actif=false}},[facture.id,revision])
  async function conserver(e){e.preventDefault();setCharge(true);setErreur('');try{setCopie(await api.conserver(facture.id,{motif,conservation_confirmee:confirme}));setMotif('');setConfirme(false)}catch(e){setErreur(e.message)}finally{setCharge(false)}}
  async function telecharger(){setCharge(true);setErreur('');try{const {blob,filename}=await api.telecharger(facture.id),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){setErreur(e.message)}finally{setCharge(false)}}
  return <section aria-label="Conservation du PDF de facture" style={{borderTop:'1px solid var(--border-light)',paddingTop:12,overflowWrap:'anywhere'}}>
    <h3>Copie PDF conservée</h3><p>Conservez le PDF exact avec son empreinte et sa date. Cette copie ne change ni la facture, ni ses règlements, ni ses écritures. Elle ne constitue pas un archivage légal certifié.</p>
    {erreur&&<div role="alert">{erreur} <button className={s.btnSec} disabled={charge} onClick={()=>setRevision(x=>x+1)}>Réessayer la conservation</button></div>}
    {message&&<p role="status">{message}</p>}{!pret&&!erreur&&!message&&<p role="status">Chargement de la conservation…</p>}
    {copie?<><p role="status">PDF figé le {new Date(copie.cree_at).toLocaleString('fr-FR')} · Auteur #{copie.auteur_id} · {copie.octets} octets.</p><p>Motif : {copie.motif}</p><p>SHA-256 : <code>{copie.pdf_sha256}</code></p><button className={s.btnSec} disabled={charge} onClick={telecharger}>{charge?'Téléchargement…':'Télécharger la copie conservée'}</button></>:
      pret&&(peutModifier?<details><summary>Conserver une copie figée</summary><form onSubmit={conserver} style={{display:'grid',gap:10,marginTop:10}}><label>Motif de conservation<textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)} style={{display:'block',width:'100%',boxSizing:'border-box'}}/></label><label style={{display:'flex',gap:8,alignItems:'start'}}><input type="checkbox" required checked={confirme} onChange={e=>setConfirme(e.target.checked)}/>Je confirme la conservation de ce PDF. La copie ne pourra pas être remplacée ; les opérations commerciales restent disponibles.</label><button className={s.btnSec} type="submit" disabled={charge}>{charge?'Conservation…':'Conserver ce PDF'}</button></form></details>:<p>Aucune copie figée conservée. Un utilisateur habilité peut la constituer.</p>)}
  </section>
}
