import {useEffect,useRef,useState,useId,cloneElement} from 'react'
import {Link,useLocation,useNavigate,useParams} from 'react-router-dom'
import Modal from '../components/Modal.jsx'
import {useModules} from '../data/ModulesContext.jsx'
import {usePersonnelAcces,useValidationUnique} from '../data/PersonnelAccesContext.jsx'
import {personnelAPI,utilisateursAPI} from '../services/api.js'
import EtatVide from '../components/EtatVide.jsx'
import s from './Personnel.module.css'
import PersonnelCoffre,{ConfigurationCoffre,telechargerPiecePrivee} from '../components/PersonnelCoffre.jsx'

const BASE='/personnel-paie'
const ETATS={BROUILLON:'Brouillon',A_VALIDER:'À valider',ACTIF:'Actif',SUSPENDU:'Suspendu',SORTI:'Sorti',SOUMIS:'Soumise',APPROUVE:'Approuvée',REJETE:'Rejetée'}
const NATURES={DOSSIER:'Identité',CONTRAT:'Contrat',REMUNERATION:'Rémunération',SORTIE:'Sortie',BANQUE:'Coordonnées bancaires'}
const DROITS={'personnel.lire_identite':'Consulter les identités','personnel.lire_remuneration':'Consulter les rémunérations',
  'personnel.lire_identifiants_sensibles':'Consulter les identifiants sensibles','personnel.audit_lire':'Consulter l’historique',
  'personnel.proposer':'Créer et proposer','personnel.soumettre':'Soumettre ses demandes','personnel.approuver':'Approuver ou rejeter',
  'personnel.valider_regles_paie':'Qualifier les règles réglementaires de paie'}
function aujourdHui(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const jour=v=>v ? String(v).slice(0,10).split('-').reverse().join('/') : '—'
function montant(v){if(v==null)return 'À confirmer';const [a,b='00']=String(v).split('.');return `${a.replace(/\B(?=(\d{3})+(?!\d))/g,'\u202f')},${b.padEnd(2,'0')} MAD`}
function Badge({etat}){return <span className={`${s.badge} ${['ACTIF','APPROUVE'].includes(etat)?s.vert:''}`}>{ETATS[etat]||etat}</span>}
function Erreur({message}){return message ? <p role="alert" className={s.erreur}>{message}</p> : null}
function Champ({label,children}){const id=useId();return <div className={s.champ}><label htmlFor={id}>{label}</label>{cloneElement(children,{id})}</div>}
const FAMILLES={celiba:'Célibataire',marie:'Marié(e)',veuf:'Veuf/veuve',divorce:'Divorcé(e)'}
const REGIMES={regime_amo:'Régime AMO déclaré',regime_retraite:'Régime retraite déclaré',regime_mutuelle:'Régime mutuelle déclaré'}
function champsPersonnels(v,droits,initial=null){
  const champs=['date_embauche','email','telephone',...(droits.cap('lire_identifiants_sensibles')?['numero_cnss']:[]),
    ...(droits.cap('lire_remuneration')?['situation_familiale','nb_enfants','personnes_charge_ir']:[])]
  const r={};for(const k of champs){if(initial&&String(initial[k]??'')===String(v[k]??''))continue
    if(v[k]!==''&&v[k]!=null)r[k]=['nb_enfants','personnes_charge_ir'].includes(k)?Number(v[k]):v[k]
    else if(initial&&initial[k]!=null)r[k]=null}return r
}
function DonneesPersonnelles({v,setV,droits}){
  const c=(k,label,props={})=><Champ label={label}><input {...props} value={v[k]??''} onChange={e=>setV(p=>({...p,[k]:e.target.value}))}/></Champ>
  return <details className={s.donnees}><summary>Coordonnées et informations personnelles (facultatif)</summary><div className={s.grille}>
    {c('email','Adresse e-mail',{type:'email',maxLength:254})}{c('telephone','Téléphone',{type:'tel',maxLength:50})}
    {c('date_embauche','Date d’entrée connue',{type:'date'})}
    {droits.cap('lire_identifiants_sensibles')&&c('numero_cnss','Numéro CNSS',{maxLength:50})}
    {droits.cap('lire_remuneration')&&<><Champ label="Situation familiale"><select value={v.situation_familiale??''} onChange={e=>setV(p=>({...p,situation_familiale:e.target.value}))}>
      <option value="">Non renseignée</option>{Object.entries(FAMILLES).map(([k,label])=><option key={k} value={k}>{label}</option>)}</select></Champ>
      {c('nb_enfants','Nombre d’enfants',{type:'number',min:0,max:2147483647,step:1})}
      {c('personnes_charge_ir','Personnes à charge IR confirmées',{type:'number',min:0,max:6,step:1})}</>}
  </div><p className={s.discret}>Renseignez uniquement les informations connues. Ces données seront appliquées après l’approbation du dossier.</p></details>
}
function Attente({lecture}){return <><Erreur message={lecture.erreur}/>{lecture.chargement&&<p role="status">Chargement…</p>}</>}
function useLecture(lire,deps){
  const [etat,setEtat]=useState({data:null,chargement:true,erreur:''})
  useEffect(()=>{let vivant=true;setEtat({data:null,chargement:true,erreur:''});Promise.resolve().then(lire)
    .then(data=>{if(vivant)setEtat({data,chargement:false,erreur:''})})
    .catch(e=>{if(vivant)setEtat({data:null,chargement:false,erreur:e.message})});return()=>{vivant=false}},deps)
  return etat
}
function Pagination({total,decalage,setDecalage,limite=25}){return <div className={s.pagination}>
  <span>{total?`${decalage+1}–${Math.min(decalage+limite,total)} sur ${total}`:'Aucun résultat'}</span>
  <button className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-limite))}>Précédent</button>
  <button className={s.secondaire} disabled={decalage+limite>=total} onClick={()=>setDecalage(decalage+limite)}>Suivant</button>
</div>}

function Dialogue({titre,onFermer,children}){
  const ref=useRef(null)
  useEffect(()=>{
    const avant=document.activeElement,p=ref.current?.closest('[role="dialog"]')
    const controles=()=>[...p.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]')].filter(e=>e.getClientRects().length)
    const champ=p.querySelector('input:not([type="hidden"]),select,textarea');(champ||controles()[0])?.focus()
    function clavier(e){if(e.key!=='Tab')return;const c=controles(),premier=c[0],dernier=c.at(-1)
      if(e.shiftKey&&document.activeElement===premier){e.preventDefault();dernier?.focus()}
      else if(!e.shiftKey&&document.activeElement===dernier){e.preventDefault();premier?.focus()}}
    p.addEventListener('keydown',clavier)
    return()=>{p.removeEventListener('keydown',clavier);if(avant?.isConnected)avant.focus()}
  },[])
  return <Modal titre={titre} onFermer={onFermer} largeur="md"><div ref={ref}>{children}</div></Modal>
}

function Formulaire({titre,onFermer,onEnvoyer,children,libelle='Enregistrer'}){
  const [occupe,setOccupe]=useState(false),[erreur,setErreur]=useState('')
  return <Dialogue titre={titre} onFermer={()=>{if(!occupe)onFermer()}}><form aria-label={titre} className={s.formulaire}
    onSubmit={async e=>{e.preventDefault();if(occupe)return;setOccupe(true);setErreur('');try{await onEnvoyer()}catch(err){setErreur(err.message)}finally{setOccupe(false)}}}>
    <fieldset disabled={occupe}>{children}</fieldset><Erreur message={erreur}/>
    <div className={s.actions}><button type="button" className={s.secondaire} disabled={occupe} onClick={onFermer}>Annuler</button>
      <button className={s.primaire} disabled={occupe}>{occupe?'Enregistrement…':libelle}</button></div>
  </form></Dialogue>
}
const UI_COFFRE={Champ,Formulaire,Erreur,jour}

export default function Personnel({indisponible=false}){
  const contexte=usePersonnelAcces(),{aGRH,societe}=useModules(),location=useLocation(),params=useParams()
  const [au,setAu]=useState(aujourdHui)
  const admin=contexte.user?.role==='admin',cap=c=>contexte.acces?.capacites.includes('personnel.'+c)
  const ecriture=['admin','comptable','personnel'].includes(contexte.user?.role)
  const droits={cap,ecriture,admin,user:contexte.user,au,recharger:contexte.recharger}
  let corps
  if(contexte.chargement)corps=<p role="status">Chargement des accès Personnel…</p>
  else if(!aGRH)corps=<div className={s.notice}>Le module Personnel & Paie est désactivé pour cette société.</div>
  else if(contexte.erreur)corps=<Erreur message={contexte.erreur}/>
  else if(location.pathname.endsWith('/acces')&&admin)corps=<Acces droits={droits} acces={contexte.acces}/>
  else if(!contexte.acces || contexte.acces.mode!=='protege')corps=<div className={s.notice}><h2>Préparer l’accès au Personnel</h2>
    <p>Le nouveau circuit demande une activation explicite et des habilitations. L’espace historique reste disponible.</p>
    {admin?<Link className={s.lien} to={`${BASE}/acces`}>Préparer les habilitations</Link>:<p>Contactez un administrateur de la société.</p>}</div>
  else if(!cap('lire_identite'))corps=<div role="alert" className={s.notice}>Accès Personnel restreint. Demandez une habilitation de consultation.</div>
  else if(indisponible)corps=<div className={s.notice}><h2>Rubrique à venir</h2><p>Cette rubrique n’est pas encore disponible.</p><Link to={`${BASE}/personnel`} className={s.lien}>Revenir au Personnel</Link></div>
  else if(location.pathname.endsWith('/demandes'))corps=<Demandes droits={droits}/>
  else if(params.employeId)corps=<Fiche key={params.employeId} id={params.employeId} droits={droits}/>
  else corps=<Dossiers droits={droits}/>
  return <div className={s.page}><header className={s.entete}><div><h1>Personnel & Paie</h1><p>{societe?.raison_sociale} · Salariés, contrats et salaires</p></div>
    <button className={s.secondaire} disabled={contexte.chargement} onClick={contexte.recharger}><i className="ti ti-refresh" aria-hidden="true"/>Actualiser</button></header>
    <nav className={s.onglets} aria-label="Rubrique Personnel">
      <Link className={location.pathname.includes('/personnel')&&!location.pathname.endsWith('/demandes')&&!location.pathname.endsWith('/acces')?s.actif:''} to={`${BASE}/personnel`}>Salariés</Link>
      {cap('lire_identite')&&<Link className={location.pathname.endsWith('/demandes')?s.actif:''} to={`${BASE}/demandes`}>Demandes à traiter</Link>}
      {admin&&<Link className={location.pathname.endsWith('/acces')?s.actif:''} to={`${BASE}/acces`}>Habilitations</Link>}
      {contexte.user?.role!=='personnel'&&<Link to="/cnss">Espace historique</Link>}
    </nav><div className={s.contenu} key={contexte.version}>
      {contexte.acces?.mode==='protege'&&cap('lire_identite')&&!location.pathname.endsWith('/acces')&&<div className={s.filtres}>
        <Champ label="Consulter les conditions au"><input type="date" value={au} onChange={e=>setAu(e.target.value||aujourdHui())}/></Champ>
        <p className={s.discret}>Les propositions restent séparées des conditions approuvées. La création d’un dossier ne génère pas d’écriture comptable.</p>
      </div>}{corps}
    </div></div>
}

function Dossiers({droits}){
  const [texte,setTexte]=useState(''),[recherche,setRecherche]=useState(''),[statut,setStatut]=useState(''),[decalage,setDecalage]=useState(0),[form,setForm]=useState(null)
  const params={au:droits.au,recherche,decalage,limite:25,...(statut?{statut}:{})}
  const lecture=useLecture(()=>personnelAPI.lister(params),[JSON.stringify(params)]),navigate=useNavigate()
  return <><div className={s.barre}><form className={s.recherche} onSubmit={e=>{e.preventDefault();setDecalage(0);setRecherche(texte)}}>
    <Champ label="Rechercher un salarié"><input value={texte} maxLength={150} onChange={e=>setTexte(e.target.value)} placeholder="Nom ou matricule"/></Champ>
    <button className={s.secondaire}>Rechercher</button></form>
    <Champ label="Statut du dossier"><select value={statut} onChange={e=>{setStatut(e.target.value);setDecalage(0)}}><option value="">Tous les statuts</option>{['BROUILLON','A_VALIDER','ACTIF','SUSPENDU','SORTI'].map(k=><option key={k} value={k}>{ETATS[k]}</option>)}</select></Champ>
    {droits.ecriture&&droits.cap('proposer')&&<div className={s.actions}><button className={s.secondaire} onClick={()=>setForm('reprise')}>Reprendre une fiche existante</button><button className={s.primaire} onClick={()=>setForm('creation')}>Créer un salarié</button></div>}
  </div><Attente lecture={lecture}/>{lecture.data&&<section className={s.carte} aria-label="Liste des salariés"><div className={s.tableau}><table>
    {lecture.data.total>0&&<thead><tr><th>Salarié</th><th>Statut</th><th>Entrée connue</th><th>Contrat à cette date</th><th>Rémunération</th><th>Fiche</th></tr></thead>}
    <tbody>{lecture.data.elements.map(d=><tr key={d.employe_id}><td><strong>{d.nom}</strong><small>{d.matricule}{d.poste?` · ${d.poste}`:''}</small></td><td><Badge etat={d.statut}/></td>
      <td>{jour(d.date_embauche)}</td><td>{d.contrat?.type_contrat||'À confirmer'}</td><td>{d.remuneration_masquee?'Masquée':montant(d.remuneration?.montant)}</td>
      <td><Link className={s.lien} to={`${BASE}/personnel/${d.employe_id}`} aria-label={`Consulter ${d.nom}`}>Consulter</Link></td></tr>)}</tbody>
  </table></div>{!lecture.data.total&&<EtatVide icone="ti-users" titre="Ajoutez vos salariés" action={droits.ecriture&&droits.cap('proposer')?'Ajouter mon premier salarié':null} onAction={()=>setForm('creation')} action2={droits.ecriture&&droits.cap('proposer')?'Reprendre un salarié déjà enregistré':null} onAction2={()=>setForm('reprise')}>Aucun dossier salarié. Chaque salarié a une fiche avec son contrat et son salaire : c’est la base de la paie. Si vos salariés existent déjà dans HisabPro, reprenez-les au lieu de les ressaisir.</EtatVide>}
    <Pagination total={lecture.data.total} decalage={decalage} setDecalage={setDecalage}/></section>}
    {form&&<Creation droits={droits} reprise={form==='reprise'} onFermer={()=>setForm(null)} onSucces={async r=>{await droits.recharger();navigate(`${BASE}/personnel/${r.employe_id}`)}}/>}
  </>
}

function Creation({reprise,onFermer,onSucces,droits}){
  const options=useLecture(()=>personnelAPI.options(),[])
  const [val,setVal]=useState({nom:'',poste:'',matricule:'',employe_id:'',beneficiaire:'',reference_beneficiaire:'',motif:''})
  const [atteste,setAtteste]=useState(false)
  const champ=(nom,label,props={})=><Champ label={label}><input {...props} value={val[nom]} onChange={e=>setVal(p=>({...p,[nom]:e.target.value}))}/></Champ>
  return <Formulaire titre={reprise?'Reprendre une fiche historique':'Créer un salarié'} onFermer={onFermer} libelle="Créer le brouillon" onEnvoyer={async()=>{
    if(!options.data)throw new Error('Les choix de saisie ne sont pas encore disponibles.')
    const data={motif:val.motif,reference_beneficiaire:val.reference_beneficiaire,beneficiaire_sans_compte_confirme:val.beneficiaire==='sans',
      ...(val.beneficiaire!=='sans'?{utilisateur_beneficiaire_id:Number(val.beneficiaire)}:{})}
    if(val.beneficiaire==='sans'&&!atteste)throw new Error('Confirmez que le salarié ne possède pas de compte dans cette société.')
    const r=reprise?await personnelAPI.reprendre({...data,employe_id:Number(val.employe_id)}):await personnelAPI.creer({...data,nom:val.nom,poste:val.poste||null,matricule:val.matricule,...champsPersonnels(val,droits)})
    await onSucces(r)
  }}><Attente lecture={options}/><p className={s.discret}>Le dossier commence au brouillon. Contrat et rémunération seront proposés et approuvés séparément.</p>
    {reprise?<Champ label="Fiche historique"><select required value={val.employe_id} onChange={e=>setVal(p=>({...p,employe_id:e.target.value}))}><option value="">Choisir une fiche</option>
      {options.data?.historiques.map(e=><option key={e.id} value={e.id} disabled={!!e.blocage}>{e.nom} · {e.matricule||'Sans matricule'}{e.blocage?` — ${e.blocage}`:''}</option>)}</select></Champ>:
      <div className={s.grille}>{champ('matricule','Matricule',{required:true,maxLength:50})}{champ('nom','Nom complet',{required:true,maxLength:150})}{champ('poste','Poste',{maxLength:150})}</div>}
    {!reprise&&<DonneesPersonnelles v={val} setV={setVal} droits={droits}/>}
    {reprise&&<p className={s.discret}>Seules les fiches non encore reprises sont proposées. Les matricules manquants ou ambigus nécessitent un examen préalable.</p>}
    <Champ label="Compte utilisateur du salarié"><select required value={val.beneficiaire} onChange={e=>{setVal(p=>({...p,beneficiaire:e.target.value}));setAtteste(false)}}><option value="">Choisir le rattachement</option>
      <option value="sans">Le salarié ne possède pas de compte</option>{options.data?.beneficiaires.map(u=><option key={u.id} value={u.id}>{u.nom} — {u.email}</option>)}</select></Champ>
    {val.beneficiaire==='sans'&&<label className={s.coche}><input type="checkbox" required checked={atteste} onChange={e=>setAtteste(e.target.checked)}/>Je confirme l’absence de compte utilisateur pour ce salarié.</label>}
    {champ('reference_beneficiaire','Référence du contrôle de rattachement',{required:true,maxLength:200})}
    {champ('motif','Motif de création ou de reprise',{required:true,maxLength:500})}
  </Formulaire>
}

function Fiche({id,droits}){
  const lecture=useLecture(()=>personnelAPI.lire(id,droits.au),[id,droits.au])
  const [form,setForm]=useState(false),[onglet,setOnglet]=useState('demandes')
  const d=lecture.data
  return <><Link className={s.lien} to={`${BASE}/personnel`}>← Tous les salariés</Link><Attente lecture={lecture}/>{d&&<>
    <section className={s.carte}><div className={s.titreFiche}><div><h2>{d.nom}</h2><p>{d.matricule} · {d.poste||'Poste non renseigné'}</p></div><Badge etat={d.statut}/>
      {droits.ecriture&&droits.cap('proposer')&&d.statut!=='SORTI'&&<button className={s.primaire} onClick={()=>setForm(true)}>Proposer une modification</button>}</div>
      <div className={s.grille}><div><h3>Contrat au {jour(droits.au)}</h3><p>{d.contrat?.type_contrat||'À confirmer'}</p><small>Début : {jour(d.contrat?.date_debut)} · Fin : {jour(d.contrat?.date_fin)}</small></div>
        <div><h3>Rémunération contractuelle</h3><p className={s.montant}>{d.remuneration_masquee?'Masquée':montant(d.remuneration?.montant)}</p><small>{d.remuneration?.periodicite||'Montant approuvé à confirmer'} · Effet : {jour(d.remuneration?.date_effet)}</small></div>
        <div><h3>Suivi du dossier</h3><p>{d.dossier_complet_a_date?'Conditions complètes à cette date':'Conditions à compléter ou à valider'}</p><small>Révision {d.revision}{d.date_sortie_approuvee?` · Sortie : ${jour(d.date_sortie_approuvee)}`:''}</small></div></div>
      <p className={s.discret}>L’identité approuvée et les conditions contractuelles ne constituent pas une paie calculée ou payée.</p></section>
    {d.contrat&&<section className={s.carte}><h2>Régimes sociaux déclarés du contrat</h2><div className={s.grille}>{Object.entries(REGIMES).map(([k,label])=><div key={k}><h3>{label}</h3><p>{d.contrat.regimes_masques?'Masqué':d.contrat.regimes?.[k]||'À confirmer'}</p></div>)}</div><p className={s.discret}>Informations déclarées et approuvées, sans affiliation ni calcul de cotisation automatique.</p></section>}
    <PersonnelCoffre dossier={d} droits={droits} ui={UI_COFFRE}/>
    <section className={s.carte}><h2>Coordonnées et dossier personnel</h2><div className={s.grille}>
      <div><h3>Contact</h3><p>{d.email||'E-mail non renseigné'}</p><p>{d.telephone||'Téléphone non renseigné'}</p><p>Entrée connue : {jour(d.date_embauche)}</p></div>
      <div><h3>Numéro CNSS</h3><p>{d.cnss_masque?'Masqué':d.numero_cnss||'À renseigner'}</p></div>
      <div><h3>Données fiscales personnelles</h3>{d.donnees_fiscales?<><p>{FAMILLES[d.donnees_fiscales.situation_familiale]||'Situation à confirmer'}</p>
        <p>Enfants : {d.donnees_fiscales.nb_enfants??'À confirmer'}</p><p>Personnes à charge IR : {d.donnees_fiscales.personnes_charge_ir??'À confirmer'}</p></>:<p>Masquées</p>}</div>
    </div></section>
    <div className={s.actions}><button className={onglet==='demandes'?s.primaire:s.secondaire} onClick={()=>setOnglet('demandes')}>Propositions et décisions</button>
      {droits.cap('audit_lire')&&<button className={onglet==='historique'?s.primaire:s.secondaire} onClick={()=>setOnglet('historique')}>Historique</button>}</div>
    {onglet==='historique'?<Historique id={id}/>:<Demandes droits={droits} id={id} dossier={d}/>}
    {form&&<Proposition dossier={d} droits={droits} onFermer={()=>setForm(false)}/>}
  </>}</>
}

function Proposition({dossier:d,droits,onFermer}){
  const initial={date_embauche:d.date_embauche,email:d.email,telephone:d.telephone,numero_cnss:d.numero_cnss,...(d.donnees_fiscales||{})}
  const [nature,setNature]=useState(d.date_sortie_approuvee?'CONTRAT':'DOSSIER'),[v,setV]=useState({...initial,...(d.contrat?.regimes||{}),nom:d.nom,poste:d.poste||'',type_contrat:'',date_effet:'',date_debut:'',date_fin:'',montant:'',periodicite:'mensuelle',reference_justificatif:'',date_sortie:'',motif:''})
  const champ=(nom,label,props={})=><Champ label={label}><input {...props} value={v[nom]} onChange={e=>setV(p=>({...p,[nom]:e.target.value}))}/></Champ>
  return <Formulaire titre="Proposer une modification" onFermer={onFermer} libelle="Enregistrer la proposition" onEnvoyer={async()=>{
    let contenu
    if(nature==='DOSSIER')contenu={nom:v.nom,poste:v.poste||null,...champsPersonnels(v,droits,initial)}
    else if(nature==='CONTRAT')contenu={type_contrat:v.type_contrat,date_effet:v.date_effet,date_debut:v.date_debut,date_fin:v.date_fin||null,reference_justificatif:v.reference_justificatif}
    else if(nature==='REMUNERATION')contenu={contrat_version_id:d.contrat.id,montant:v.montant.replace(',','.'),periodicite:v.periodicite,devise:'MAD',date_effet:v.date_effet,reference_justificatif:v.reference_justificatif}
    else contenu={date_sortie:v.date_sortie,reference_justificatif:v.reference_justificatif}
    if(nature==='CONTRAT'&&droits.cap('lire_identifiants_sensibles'))for(const k of Object.keys(REGIMES))if(v[k]||d.contrat?.regimes?.[k]!=null)contenu[k]=v[k]?.trim()||null
    await personnelAPI.proposer(d.employe_id,{nature,revision_attendue:d.revision,motif:v.motif,contenu});await droits.recharger()
  }}><p className={s.discret}>Les conditions actuelles restent applicables jusqu’à l’approbation. Une proposition périmée doit être préparée à nouveau.</p>
    <Champ label="Nature de la proposition"><select value={nature} onChange={e=>setNature(e.target.value)}>{!d.date_sortie_approuvee&&<option value="DOSSIER">Identité</option>}
      {['ACTIF','SUSPENDU'].includes(d.statut)&&<><option value="CONTRAT">Contrat</option>{droits.cap('lire_remuneration')&&d.contrat&&<option value="REMUNERATION">Rémunération</option>}{!d.date_sortie_approuvee&&<option value="SORTIE">Sortie</option>}</>}</select></Champ>
    {nature==='DOSSIER'&&<div className={s.grille}>{champ('nom','Nom complet',{required:true,maxLength:150})}{champ('poste','Poste',{maxLength:150})}</div>}
    {nature==='DOSSIER'&&<DonneesPersonnelles v={v} setV={setV} droits={droits}/>}
    {nature==='CONTRAT'&&<div className={s.grille}>{champ('type_contrat','Type de contrat',{required:true,maxLength:40,placeholder:'CDI, CDD ou autre type attesté'})}
      {champ('date_debut','Début du contrat',{required:true,type:'date'})}{champ('date_fin','Fin du contrat',{type:'date'})}</div>}
    {nature==='CONTRAT'&&droits.cap('lire_identifiants_sensibles')&&<><div className={s.grille}>{Object.entries(REGIMES).map(([k,label])=><Champ key={k} label={label}><input value={v[k]??''} maxLength={120} onChange={e=>setV(p=>({...p,[k]:e.target.value}))}/></Champ>)}</div><p className={s.discret}>Facultatif : noms des régimes attestés, sans numéro bancaire ni donnée médicale. Vérifiez les valeurs reprises avant soumission ; une valeur inconnue reste vide.</p></>}
    {nature==='REMUNERATION'&&<div className={s.grille}>{champ('montant','Montant en MAD',{required:true,inputMode:'decimal',pattern:'[0-9]+([.,][0-9]{1,2})?',placeholder:'Ex. 9000,10'})}
      <Champ label="Périodicité"><select value={v.periodicite} onChange={e=>setV(p=>({...p,periodicite:e.target.value}))}><option value="mensuelle">Mensuelle</option><option value="journaliere">Journalière</option><option value="horaire">Horaire</option></select></Champ></div>}
    {['CONTRAT','REMUNERATION'].includes(nature)&&champ('date_effet','Date d’effet',{required:true,type:'date'})}
    {nature==='SORTIE'&&champ('date_sortie','Date de sortie',{required:true,type:'date'})}
    {nature!=='DOSSIER'&&champ('reference_justificatif','Référence du justificatif',{required:true,maxLength:200})}
    {champ('motif','Motif de la proposition',{required:true,maxLength:500})}
  </Formulaire>
}

function Demandes({droits,id,dossier:d}){
  const [statut,setStatut]=useState(id?'':'SOUMIS'),[decalage,setDecalage]=useState(0),[choix,setChoix]=useState(null)
  const p={decalage,limite:25,...(statut?{statut}:{}),...(id?{employe_id:id}:{})}
  const lecture=useLecture(()=>personnelAPI.demandes(p),[JSON.stringify(p)])
  return <><div className={s.barre}><h2>{id?'Propositions et décisions':'Demandes à traiter'}</h2><Champ label="État des demandes"><select value={statut} onChange={e=>{setStatut(e.target.value);setDecalage(0)}}>
    <option value="">Tous les états</option>{['BROUILLON','SOUMIS','APPROUVE','REJETE'].map(k=><option value={k} key={k}>{ETATS[k]}</option>)}</select></Champ></div>
    <Attente lecture={lecture}/>{lecture.data&&<section className={s.carte} aria-label="Demandes Personnel"><div className={s.tableau}><table><thead><tr><th>Demande</th><th>État</th><th>Préparation</th><th>Contenu et actions</th></tr></thead><tbody>
      {lecture.data.elements.map(r=><tr key={r.id}><td><strong>{NATURES[r.nature]}</strong><small>Demande {r.id} · <Link className={s.lien} to={`${BASE}/personnel/${r.employe_id}`}>Fiche salarié</Link></small></td>
        <td><Badge etat={r.statut}/></td><td>{r.prepare_par_nom||`Compte ${r.prepare_par}`}<small>{jour(r.cree_at)}</small></td>
        <td><Contenu demande={r}/><button className={s.secondaire} onClick={()=>setChoix({r,action:'consulter'})}>Consulter la demande {r.id}</button></td></tr>)}
    </tbody></table></div>{!lecture.data.total&&<p className={s.vide}>Aucune demande dans cet état.</p>}<Pagination total={lecture.data.total} decalage={decalage} setDecalage={setDecalage}/></section>}
    {choix&&<DecisionDemande demande={choix.r} droits={droits} dossier={d} onFermer={()=>setChoix(null)}/>}
  </>
}

function Contenu({demande:r}){
  if(!r.contenu)return <p className={s.discret}>Contenu masqué selon vos habilitations.</p>
  const c=r.contenu
  return <div className={s.resume}>{r.nature==='DOSSIER'?<p>{c.nom}{c.poste?` · ${c.poste}`:''}</p>:
    r.nature==='CONTRAT'?<p>{c.type_contrat} · Effet : {jour(c.date_effet)}<small>Du {jour(c.date_debut)}{c.date_fin?` au ${jour(c.date_fin)}`:''}</small></p>:
    r.nature==='REMUNERATION'?<p>{montant(c.montant)} · {c.periodicite}<small>Effet : {jour(c.date_effet)}</small></p>:
    r.nature==='BANQUE'?<p>Coordonnées chiffrées · {c.masque}<small>Effet : {jour(c.date_effet)} · {c.piece_id?`Pièce privée ${c.piece_id}`:'Justificatif externe référencé'}</small></p>:
    <p>Sortie au {jour(c.date_sortie)}</p>}{r.nature==='DOSSIER'&&<>
      {c.email&&<small>E-mail : {c.email}</small>}{c.telephone&&<small>Téléphone : {c.telephone}</small>}
      {'numero_cnss' in c&&<small>CNSS : {r.champs_masques?.includes('numero_cnss')?'Masqué':c.numero_cnss||'À effacer'}</small>}
      {['situation_familiale','nb_enfants','personnes_charge_ir'].some(k=>k in c)&&<small>Données fiscales : {r.champs_masques?.some(k=>k!=='numero_cnss')?'Masquées':
        `${FAMILLES[c.situation_familiale]||'Situation non modifiée'} · enfants ${c.nb_enfants??'—'} · personnes à charge IR ${c.personnes_charge_ir??'—'}`}</small>}
    </>}{r.nature==='CONTRAT'&&Object.entries(REGIMES).filter(([k])=>k in c).map(([k,label])=><small key={k}>{label} : {r.champs_masques?.includes(k)?'Masqué':c[k]||'À confirmer'}</small>)}{c.reference_justificatif&&<small>Justificatif : {c.reference_justificatif}</small>}</div>
}

function DecisionDemande({demande:r,droits,dossier:d,onFermer}){
  const lecture=useLecture(()=>d?Promise.resolve(d):personnelAPI.lire(r.employe_id,droits.au),[r.id])
  const seul=useValidationUnique(),[action,setAction]=useState(''),[motif,setMotif]=useState(''),[reference,setReference]=useState(seul?'Validation unique — petite entreprise':''),[confirme,setConfirme]=useState(seul)
  const [banqueVue,setBanqueVue]=useState(null),[banqueConfirmee,setBanqueConfirmee]=useState(false),[erreurBanque,setErreurBanque]=useState('')
  const auteur=r.prepare_par===droits.user.id,beneficiaire=r.beneficiaire_snapshot===droits.user.id
  const financier=r.nature==='REMUNERATION',sensible=r.champs_masques?.some(k=>k in REGIMES),possible=droits.ecriture&&(!financier||droits.cap('lire_remuneration'))&&!sensible&&(r.nature!=='BANQUE'||droits.cap('lire_identifiants_sensibles'))
  return <Formulaire titre={`Demande ${r.id} · ${NATURES[r.nature]}`} onFermer={onFermer} libelle={action==='soumettre'?'Soumettre':action==='approuver'?'Confirmer l’approbation':action==='rejeter'?'Confirmer le rejet':'Fermer'} onEnvoyer={async()=>{
    if(!action){onFermer();return}
    if(!lecture.data)throw new Error('Le dossier doit être actualisé avant cette action.')
    if(r.nature==='BANQUE'&&action==='approuver'&&(!banqueVue||!banqueConfirmee))throw new Error('Consultez les coordonnées proposées et confirmez leur contrôle avant approbation.')
    const data={revision_attendue:lecture.data.revision,motif}
    if(action==='soumettre')await personnelAPI.soumettre(r.id,data)
    else await personnelAPI.decider(r.id,action,{...data,independance_confirmee:confirme,reference_independance:reference,...(r.nature==='BANQUE'?{verification_bancaire_confirmee:banqueConfirmee}:{})})
    await droits.recharger()
  }}><Badge etat={r.statut}/><Contenu demande={r}/>{r.motif&&<p>Motif : {r.motif}</p>}{r.motif_decision&&<p>Décision : {r.motif_decision}</p>}
    {r.nature==='BANQUE'&&droits.cap('lire_identifiants_sensibles')&&<><button type="button" className={s.secondaire} onClick={async()=>{setErreurBanque('');try{setBanqueVue(await personnelAPI.revelerBanque(r.employe_id,r.id))}catch(e){setErreurBanque(e.message)}}}>Consulter les coordonnées proposées</button>
      {r.contenu?.piece_id&&<button type="button" className={s.secondaire} onClick={async()=>{setErreurBanque('');try{await telechargerPiecePrivee(r.employe_id,r.contenu.piece_id)}catch(e){setErreurBanque(e.message)}}}>Télécharger le justificatif associé</button>}
      <Erreur message={erreurBanque}/>{banqueVue&&<dl style={{overflowWrap:'anywhere'}}><dt>RIB / IBAN attesté</dt><dd>{banqueVue.rib_iban}</dd><dt>Banque</dt><dd>{banqueVue.banque||'Non renseignée'}</dd><dt>Titulaire</dt><dd>{banqueVue.titulaire||'Non renseigné'}</dd></dl>}</>}
    <Attente lecture={lecture}/>{lecture.data&&r.revision_attendue!==lecture.data.revision&&r.statut!=='APPROUVE'&&r.statut!=='REJETE'&&<p className={s.notice}>Cette proposition est périmée. Elle peut être rejetée, puis préparée à nouveau.</p>}
    <div className={s.actions}>{r.statut==='BROUILLON'&&auteur&&possible&&droits.cap('soumettre')&&<button type="button" className={s.secondaire} onClick={()=>setAction('soumettre')}>Préparer la soumission</button>}
      {r.statut==='SOUMIS'&&!auteur&&!beneficiaire&&possible&&droits.cap('approuver')&&<>
        <button type="button" className={s.secondaire} disabled={!lecture.data||r.revision_attendue!==lecture.data.revision} onClick={()=>setAction('approuver')}>Approuver</button>
        <button type="button" className={s.secondaire} onClick={()=>setAction('rejeter')}>Rejeter</button></>}
    </div>{r.statut==='SOUMIS'&&(auteur||beneficiaire)&&<p className={s.notice}>La décision doit être prise par un autre compte habilité, indépendant du préparateur et du bénéficiaire.</p>}
    {action&&<><Champ label={action==='soumettre'?'Motif de soumission':'Motif de la décision'}><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
      {action!=='soumettre'&&<>{!seul&&<Champ label="Référence du contrôle indépendant"><input required maxLength={200} value={reference} onChange={e=>setReference(e.target.value)}/></Champ>}
        {r.nature==='BANQUE'&&action==='approuver'&&<label className={s.coche}><input required type="checkbox" checked={banqueConfirmee} onChange={e=>setBanqueConfirmee(e.target.checked)}/>J’ai vérifié les coordonnées bancaires proposées et leur justificatif.</label>}
        {seul?<p className={s.discret}><i className="ti ti-user-check" aria-hidden="true"/> Validation par une seule personne (petite entreprise) : votre nom est enregistré comme décideur.</p>:<label className={s.coche}><input required type="checkbox" checked={confirme} onChange={e=>setConfirme(e.target.checked)}/>Je confirme être indépendant du préparateur et du bénéficiaire de cette demande.</label>}</>}</>}
  </Formulaire>
}

function Historique({id}){
  const [decalage,setDecalage]=useState(0),lecture=useLecture(()=>personnelAPI.historique(id,{decalage,limite:25}),[id,decalage])
  return <section className={s.carte} aria-label="Historique Personnel"><h2>Historique</h2><Attente lecture={lecture}/>{lecture.data&&<>
    <ol className={s.historique}>{lecture.data.elements.map(e=><li key={e.id}><strong>{e.nature.replaceAll('_',' ')}</strong><p>{e.motif||'Motif masqué selon vos habilitations.'}</p>
      <small>{e.auteur_nom||`Compte ${e.auteur_id}`} · {jour(e.cree_at)} · Révision {e.revision}</small></li>)}</ol>
    <Pagination total={lecture.data.total} decalage={decalage} setDecalage={setDecalage}/></>}</section>
}

function ValidationUnique({acces}){
  // Lot 974 : petite entreprise, une seule personne prépare et valide (tracé).
  const contexte=usePersonnelAcces(),[occupe,setOccupe]=useState(false),[erreur,setErreur]=useState(''),actif=!!acces?.validation_unique
  const basculer=async()=>{
    if(!window.confirm(actif?'Revenir à une validation par une seconde personne ? Les demandes devront être approuvées par un autre compte.':'Autoriser une seule personne à préparer et valider la paie (petite entreprise) ? Chaque décision restera enregistrée à son nom.'))return
    setOccupe(true);setErreur('')
    try{await personnelAPI.validationUnique(!actif,actif?'Retour à la double validation':'Petite entreprise : validation par une seule personne');await contexte.recharger()}catch(e){setErreur(e.message)}finally{setOccupe(false)}
  }
  return <section className={s.carte} aria-label="Mode de validation"><div className={s.titreFiche}><div><h2>Mode de validation</h2>
    <p>{actif?'Une seule personne prépare et valide (petite entreprise). Chaque décision est enregistrée au nom de son auteur.':'Double validation : une seconde personne approuve ce qu’une autre a préparé.'}</p></div>
    <button className={s.secondaire} disabled={occupe} onClick={basculer}>{actif?'Revenir à la double validation':'Activer la validation par une seule personne'}</button></div>
    {erreur&&<p role="alert" className={s.erreur}>{erreur}</p>}<p className={s.discret}>Un salarié ne peut jamais valider ses propres données, quel que soit le mode.</p></section>
}

function Acces({droits,acces}){
  const lecture=useLecture(async()=>{const [users,habs]=await Promise.all([utilisateursAPI.lister(),personnelAPI.habilitations()]);return {users,habs}},[])
  const [form,setForm]=useState(null),[uid,setUid]=useState(''),[capacite,setCapacite]=useState(''),[motif,setMotif]=useState(''),[confirme,setConfirme]=useState(false)
  return <><h2>Habilitations Personnel</h2><p className={s.discret}>Les accès sont accordés explicitement. Le rôle administrateur ne donne pas le droit d’approuver sa propre demande.</p>
    <ValidationUnique acces={acces}/>
    <ConfigurationCoffre droits={droits} ui={UI_COFFRE}/>
    <Attente lecture={lecture}/>{lecture.data&&<>
      <div className={s.actions}><button className={s.primaire} onClick={()=>{setMotif('');setForm('accorder')}}>Accorder un droit</button>
        {acces.mode!=='protege'&&<button className={s.secondaire} onClick={()=>{setMotif('');setConfirme(false);setForm('activer')}}>Activer la protection Personnel</button>}
        {acces.mode==='protege'&&<span className={s.badge}>Protection activée</span>}</div>
      <section className={s.carte} aria-label="Habilitations accordées"><div className={s.tableau}><table><thead><tr><th>Utilisateur</th><th>Droit</th><th>État</th><th>Action</th></tr></thead><tbody>
        {lecture.data.habs.map(h=><tr key={h.id}><td>{lecture.data.users.find(u=>u.id===h.utilisateur_id)?.nom||`Compte ${h.utilisateur_id}`}<small>{lecture.data.users.find(u=>u.id===h.utilisateur_id)?.email}</small></td><td>{DROITS[h.capacite]}</td><td>{h.revoquee_at?'Révoqué':'Actif'}</td>
          <td>{!h.revoquee_at&&<button className={s.secondaire} onClick={()=>{setMotif('');setForm(h)}}>Révoquer le droit {h.id}</button>}</td></tr>)}
      </tbody></table></div>{!lecture.data.habs.length&&<p className={s.vide}>Aucune habilitation. Préparez les accès avant d’activer la protection.</p>}</section>
    </>}
    {form&&<Formulaire titre={form==='accorder'?'Accorder un droit':form==='activer'?'Activer la protection Personnel':'Révoquer un droit'} onFermer={()=>setForm(null)} libelle="Confirmer" onEnvoyer={async()=>{
      if(form==='accorder')await personnelAPI.accorder({utilisateur_id:Number(uid),capacite,motif})
      else if(form==='activer'){if(!confirme)throw new Error('Confirmez les conséquences de cette activation.');await personnelAPI.activer(motif)}
      else await personnelAPI.revoquer(form.id,motif)
      await droits.recharger()
    }}>{form==='accorder'&&<><Champ label="Utilisateur à habiliter"><select required value={uid} onChange={e=>setUid(e.target.value)}><option value="">Choisir un utilisateur</option>{lecture.data.users.filter(u=>u.actif).map(u=><option key={u.id} value={u.id}>{u.nom} — {u.email}</option>)}</select></Champ>
      <Champ label="Droit à accorder"><select required value={capacite} onChange={e=>setCapacite(e.target.value)}><option value="">Choisir un droit</option>{Object.entries(DROITS).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></Champ></>}
      {form==='activer'&&<><p className={s.notice}>Cette activation impose le nouveau circuit et bloque les anciens formulaires Personnel, absences et avances. Préparez les habilitations du préparateur et d’un validateur indépendant. Cette activation ne peut pas être annulée depuis cet écran.</p>
        <label className={s.coche}><input required type="checkbox" checked={confirme} onChange={e=>setConfirme(e.target.checked)}/>J’ai compris et je souhaite activer la protection Personnel.</label></>}
      <Champ label="Motif de l’habilitation ou de l’activation"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
    </Formulaire>}
  </>
}
