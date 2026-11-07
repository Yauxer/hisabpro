import {useState,useEffect} from 'react'
import {personnelAPI} from '../services/api.js'
import s from '../pages/Personnel.module.css'

export async function telechargerPiecePrivee(eid,ident){
  const {blob,filename}=await personnelAPI.telechargerPiece(eid,ident)
  const url=URL.createObjectURL(blob),lien=document.createElement('a');lien.href=url;lien.download=filename;lien.click()
  setTimeout(()=>URL.revokeObjectURL(url),1000)
}

function useCoffre(id=null){
  const [etat,setEtat]=useState(null),[pieces,setPieces]=useState([]),[erreur,setErreur]=useState(''),[revision,setRevision]=useState(0)
  useEffect(()=>{let vivant=true;setEtat(null);setPieces([]);setErreur('')
    personnelAPI.coffreEtat().then(async e=>{const p=id&&e.schema_installe?await personnelAPI.pieces(id):[];if(vivant){setEtat(e);setPieces(p)}})
      .catch(e=>{if(vivant)setErreur(e.message)});return()=>{vivant=false}},[id,revision])
  return {etat,pieces,erreur,recharger:()=>setRevision(n=>n+1)}
}

export function ConfigurationCoffre({droits,ui}){
  const {Champ,Formulaire,Erreur}=ui,c=useCoffre(),[ouvert,setOuvert]=useState(false)
  const [v,setV]=useState({reference_garde_cles:'',reference_conservation:'',reference_rotation_sauvegarde:'',motif:''}),[confirme,setConfirme]=useState(false)
  return <section className={s.carte}><h2>Coffre RH — configuration</h2><Erreur message={c.erreur}/>
    {!c.etat&&!c.erreur&&<p role="status">Chargement du coffre…</p>}
    {c.etat&&!c.etat.schema_installe&&<p>Installer les migrations111 et112 pour activer les pièces et coordonnées bancaires privées.</p>}
    {c.etat?.schema_installe&&<><p>Clés du serveur : {c.etat.cles_configurees?'Configurées':'À configurer'} · Politique : {c.etat.politique_declaree?'Déclarée':'À déclarer'}</p>
      <p className={s.discret}>Les clés restent hors de l’interface et de la base. Ne collez jamais une clé dans ces champs. Les références ci-dessous attestent vos procédures ;elles ne les valident pas automatiquement.</p>
      {c.etat.politique&&<dl><dt>Garde des clés</dt><dd>{c.etat.politique.reference_garde_cles}</dd><dt>Conservation</dt><dd>{c.etat.politique.reference_conservation}</dd><dt>Rotation et sauvegarde</dt><dd>{c.etat.politique.reference_rotation_sauvegarde}</dd></dl>}
      <button className={s.secondaire} disabled={!c.etat.cles_configurees} onClick={()=>setOuvert(true)}>Déclarer la politique du coffre</button>
      {!c.etat.cles_configurees&&<p className={s.notice}>Faire configurer le trousseau privé sur le serveur avant toute collecte.</p>}</>}
    {c.erreur&&<button className={s.secondaire} onClick={c.recharger}>Réessayer le coffre</button>}
    {ouvert&&<Formulaire titre="Déclarer la politique du coffre" libelle="Enregistrer la déclaration" onFermer={()=>setOuvert(false)} onEnvoyer={async()=>{
      if(!confirme)throw new Error('Confirmez les procédures de garde,conservation et sauvegarde.')
      await personnelAPI.coffrePolitique({...v,confirmation:'DECLARER_POLITIQUE_COFFRE_RH'});await droits.recharger()
    }}>{[['reference_garde_cles','Référence de la procédure de garde des clés'],['reference_conservation','Référence de la politique de conservation'],['reference_rotation_sauvegarde','Référence de rotation et sauvegarde']].map(([k,label])=><Champ key={k} label={label}><input required maxLength={200} value={v[k]} onChange={e=>setV(p=>({...p,[k]:e.target.value}))}/></Champ>)}
      <Champ label="Motif de la déclaration"><textarea required maxLength={500} value={v.motif} onChange={e=>setV(p=>({...p,motif:e.target.value}))}/></Champ>
      <label className={s.coche}><input required type="checkbox" checked={confirme} onChange={e=>setConfirme(e.target.checked)}/>Je confirme disposer de procédures de garde des clés,de conservation et de sauvegarde/restauration.</label>
    </Formulaire>}
  </section>
}

export default function PersonnelCoffre({dossier:d,droits,ui}){
  if(!droits.cap('lire_identifiants_sensibles'))return <section className={s.carte}><h2>Banque et pièces privées</h2><p>Masquées selon vos habilitations.</p></section>
  return <CoffreAutorise key={`${d.employe_id}:${droits.au}`} dossier={d} droits={droits} ui={ui}/>
}

function CoffreAutorise({dossier:d,droits,ui}){
  const {Champ,Formulaire,Erreur,jour}=ui,c=useCoffre(d.employe_id),[form,setForm]=useState(null),[erreur,setErreur]=useState(''),[occupe,setOccupe]=useState(false)
  const [revele,setRevele]=useState(null),[fichier,setFichier]=useState(null),[categorie,setCategorie]=useState('contrat')
  const [v,setV]=useState({date_effet:'',rib_iban:'',banque:'',titulaire:'',piece_id:'',reference_justificatif:'',motif:''})
  const peutProposer=droits.ecriture&&droits.cap('proposer'),collecte=c.etat?.collecte_autorisee
  const bancaire=peutProposer&&c.etat?.banque_disponible&&['ACTIF','SUSPENDU'].includes(d.statut)
  async function action(fn){if(occupe)return;setOccupe(true);setErreur('');try{await fn()}catch(e){setErreur(e.message)}finally{setOccupe(false)}}
  async function telecharger(p){await action(()=>telechargerPiecePrivee(d.employe_id,p.id))}
  return <section className={s.carte}><h2>Banque et pièces privées</h2><Erreur message={c.erreur||erreur}/>
    {!c.etat&&!c.erreur&&<p role="status">Chargement des pièces privées…</p>}
    {c.etat&&!c.etat.schema_installe&&<p>Le coffre privé nécessite les migrations111 et112.</p>}
    {c.etat?.schema_installe&&<>
      {!collecte&&<p className={s.notice}>La collecte est fermée tant que les clés,la politique et la protection du coffre ne sont pas prêtes. Contactez l’administrateur.</p>}
      <h3>Coordonnées bancaires approuvées au {jour(droits.au)}</h3>
      <p>{d.banque?`${d.banque.masque} · Effet : ${jour(d.banque.date_effet)}`:'À renseigner ou à faire approuver'}</p>
      {d.banque&&<div className={s.actions}><button className={s.secondaire} disabled={occupe||!c.etat.cles_configurees} onClick={()=>action(async()=>setRevele(await personnelAPI.revelerBanque(d.employe_id,d.banque.demande_id)))}>Consulter les coordonnées approuvées</button>
        {revele&&<button className={s.secondaire} onClick={()=>setRevele(null)}>Masquer les coordonnées</button>}</div>}
      {revele&&<dl style={{overflowWrap:'anywhere'}}><dt>RIB / IBAN attesté</dt><dd>{revele.rib_iban}</dd><dt>Banque</dt><dd>{revele.banque||'Non renseignée'}</dd><dt>Titulaire</dt><dd>{revele.titulaire||'Non renseigné'}</dd></dl>}
      {bancaire&&<button className={s.secondaire} disabled={!collecte} onClick={()=>setForm('banque')}>Proposer des coordonnées bancaires</button>}
      <p className={s.discret}>Aucun virement ni écriture comptable n’est créé par cette proposition. Le contrôle du justificatif bancaire reste humain.</p>
      <h3>Pièces privées du dossier</h3>
      {peutProposer&&<button className={s.secondaire} disabled={!collecte} onClick={()=>setForm('piece')}>Déposer une pièce privée</button>}
      {!c.pieces.length&&<p>Aucune pièce déposée.</p>}
      <ul className={s.historique}>{c.pieces.map(p=><li key={p.id}><strong>Pièce {p.id} · {p.categorie}</strong><p>{p.mime} · {Math.ceil(p.octets/1024)}Kio · {jour(p.deposee_at)}</p>
        <button className={s.secondaire} disabled={occupe||!c.etat.cles_configurees} onClick={()=>telecharger(p)}>Télécharger la pièce {p.id}</button><small>Déposée ;contenu à contrôler humainement.</small></li>)}</ul>
    </>}
    {c.erreur&&<button className={s.secondaire} onClick={c.recharger}>Réessayer les pièces privées</button>}
    {form==='piece'&&<Formulaire titre="Déposer une pièce privée" libelle="Chiffrer et déposer" onFermer={()=>{setForm(null);setFichier(null)}} onEnvoyer={async()=>{
      if(!fichier||fichier.size===0||fichier.size>4194304)throw new Error('Choisir une pièce non vide de4Mio maximum.')
      await personnelAPI.deposerPiece(d.employe_id,categorie,fichier);setFichier(null);await droits.recharger()
    }}><Champ label="Catégorie de la pièce"><select value={categorie} onChange={e=>setCategorie(e.target.value)}><option value="contrat">Contrat</option><option value="banque">Justificatif bancaire</option><option value="autre">Autre</option></select></Champ>
      <Champ label="Fichier privé PDF,PNG ouJPEG"><input required type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>setFichier(e.target.files?.[0]||null)}/></Champ>
      <p className={s.discret}>4Mio maximum. Le nom original n’est pas conservé. Ce dépôt ne vaut pas validation du contenu ;ne déposez pas de données médicales.</p>
    </Formulaire>}
    {form==='banque'&&<Formulaire titre="Proposer des coordonnées bancaires" libelle="Enregistrer la proposition bancaire" onFermer={()=>{setForm(null);setV(p=>({...p,rib_iban:''}))}} onEnvoyer={async()=>{
      await personnelAPI.proposer(d.employe_id,{nature:'BANQUE',revision_attendue:d.revision,motif:v.motif,contenu:{date_effet:v.date_effet,rib_iban:v.rib_iban,banque:v.banque||null,titulaire:v.titulaire||null,piece_id:v.piece_id?Number(v.piece_id):null,reference_justificatif:v.reference_justificatif}})
      setV(p=>({...p,rib_iban:''}));await droits.recharger()
    }}>{[['date_effet','Date d’effet bancaire','date',null],['rib_iban','RIB / IBAN attesté','text',120],['banque','Banque (facultatif)','text',120],['titulaire','Titulaire (facultatif)','text',150],['reference_justificatif','Référence du justificatif bancaire','text',200]].map(([k,label,type,max])=><Champ key={k} label={label}><input required={!['banque','titulaire'].includes(k)} type={type} maxLength={max||undefined} value={v[k]} autoComplete="off" onChange={e=>setV(p=>({...p,[k]:e.target.value}))}/></Champ>)}
      <Champ label="Pièce chiffrée associée (facultatif)"><select value={v.piece_id} onChange={e=>setV(p=>({...p,piece_id:e.target.value}))}><option value="">Justificatif externe référencé</option>{c.pieces.map(p=><option key={p.id} value={p.id}>Pièce {p.id} · {p.categorie}</option>)}</select></Champ>
      <Champ label="Motif de la proposition bancaire"><textarea required maxLength={500} value={v.motif} onChange={e=>setV(p=>({...p,motif:e.target.value}))}/></Champ>
      <p className={s.discret}>Saisissez les coordonnées telles qu’attestées. Ne les recopiez pas dans le motif ou la référence. La proposition doit être soumise puis contrôlée par un autre compte habilité.</p>
    </Formulaire>}
  </section>
}
