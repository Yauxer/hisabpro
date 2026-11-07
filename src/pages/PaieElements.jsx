import {useEffect,useState,useId,useRef,cloneElement} from 'react'
import {Link,useLocation} from 'react-router-dom'
import PaieVariables from '../components/PaieVariables.jsx'
import {QualificationIRForm,QualificationIRResume} from '../components/PaieQualificationIR.jsx'
import Modal from '../components/Modal.jsx'
import {useModules} from '../data/ModulesContext.jsx'
import {paieCatalogueAPI as api} from '../services/api.js'
import PaieAccesRequis,{accesPaieManquant} from '../components/PaieAccesRequis.jsx'
import EtatVide from '../components/EtatVide.jsx'
import {pluriel} from '../utils/formatPaie.js'
import {usePersonnelAcces,useValidationUnique} from '../data/PersonnelAccesContext.jsx'
import s from './Personnel.module.css'

const REGIMES=['IR','CNSS','AMO']
const ETATS={PROPOSEE:'Proposée',APPROUVEE:'Approuvée',REJETEE:'Rejetée'}
const TRAITEMENTS={A_VERIFIER:'À vérifier',SOUMIS:'Soumis en totalité',EXONERE:'Exonéré sous conditions',PLAFOND_MONTANT:'Plafond en montant'}
const euro=v=>v==null?'À vérifier':`${v} MAD`
const dateLocale=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function Champ({label,children}){const id=useId();return <div className={s.champ}><label htmlFor={id}>{label}</label>{cloneElement(children,{id})}</div>}
function Erreur({message}){return message?<p role="alert" className={s.erreur}>{message}</p>:null}
function Formulaire({titre,onFermer,onEnvoyer,children,libelle='Enregistrer la proposition'}){
  const [occupe,setOccupe]=useState(false),[erreur,setErreur]=useState('')
  const ref=useRef(null)
  useEffect(()=>{const avant=document.activeElement,dialogue=ref.current.closest('[role="dialog"]')
    const controles=()=>[...dialogue.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]')].filter(e=>e.getClientRects().length)
    ;(ref.current.querySelector('input,select,textarea')||controles()[0])?.focus()
    const clavier=e=>{if(e.key!=='Tab')return;const c=controles();if(e.shiftKey&&document.activeElement===c[0]){e.preventDefault();c.at(-1)?.focus()}else if(!e.shiftKey&&document.activeElement===c.at(-1)){e.preventDefault();c[0]?.focus()}}
    dialogue.addEventListener('keydown',clavier);return()=>{dialogue.removeEventListener('keydown',clavier);if(avant?.isConnected)avant.focus()}},[])
  return <Modal titre={titre} onFermer={()=>{if(!occupe)onFermer()}} largeur="lg"><form ref={ref} className={s.formulaire} aria-label={titre} onSubmit={async e=>{e.preventDefault();if(occupe)return;setOccupe(true);setErreur('');try{await onEnvoyer()}catch(err){setErreur(err.message)}finally{setOccupe(false)}}}>
    <fieldset disabled={occupe}>{children}</fieldset><Erreur message={erreur}/><div className={s.actions}><button type="button" className={s.secondaire} disabled={occupe} onClick={onFermer}>Annuler</button><button className={s.primaire} disabled={occupe}>{occupe?'Enregistrement…':libelle}</button></div>
  </form></Modal>
}
function vide(){return {libelle:'',nature:'GAIN',periodicite:'mensuelle',formule:'MONTANT',date_debut:'',date_fin:'',compte_charge:'',justificatifs:[],incompatibilites:[],
  regles:Object.fromEntries(REGIMES.map(k=>[k,{traitement:'A_VERIFIER',statut_reglementaire:'A_VERIFIER',plafond:null,unite:'mensuel',conditions:'',texte_reference:null,article:null,url_source:null,empreinte_preuve:null}]))}}

export default function PaieElements(){
  const ctx=usePersonnelAcces(),{societe,aGRH}=useModules(),location=useLocation(),variables=location.pathname.endsWith('/variables')
  const [moisVariables,setMoisVariables]=useState(()=>dateLocale().slice(0,7))
  let bloc
  const cap=k=>ctx.acces?.capacites.includes('personnel.'+k)
  if(ctx.chargement)bloc=<p role="status">Chargement des accès…</p>
  else if(ctx.erreur)bloc=<Erreur message={ctx.erreur}/>
  else if(accesPaieManquant(ctx,aGRH))bloc=<PaieAccesRequis ctx={ctx}/>
  else bloc=variables?<PaieVariables key={`${societe?.id}:${ctx.version}`} cap={cap} user={ctx.user} mois={moisVariables} setMois={setMoisVariables}/>:<Catalogue key={`${societe?.id}:${ctx.version}`} cap={cap} user={ctx.user}/>
  return <div className={s.page}><header className={s.entete}><div><h1>Éléments de paie</h1><p>{societe?.raison_sociale} · Rubriques de paie et primes du mois</p></div><button className={s.secondaire} onClick={ctx.recharger} disabled={ctx.chargement}>Actualiser</button></header>
    <nav className={s.onglets} aria-label="Sous-parties : Éléments de paie"><Link className={!variables?s.actif:''} to="/personnel-paie/elements">Catalogue</Link><Link className={variables?s.actif:''} to="/personnel-paie/elements/variables">Variables mensuelles</Link></nav><div className={s.contenu}>{bloc}</div></div>
}
function Catalogue({cap,user}){
  const [date,setDate]=useState(dateLocale),[texte,setTexte]=useState(''),[recherche,setRecherche]=useState(''),[decalage,setDecalage]=useState(0),[version,setVersion]=useState(0)
  const [etat,setEtat]=useState({data:null,erreur:'',chargement:true}),[detail,setDetail]=useState(null),[form,setForm]=useState(null),[erreur,setErreur]=useState('')
  useEffect(()=>{let vivant=true;setEtat({data:null,erreur:'',chargement:true});api.lister({au:date,recherche,decalage}).then(data=>{if(vivant)setEtat({data,erreur:'',chargement:false})}).catch(e=>{if(vivant)setEtat({data:null,erreur:e.message,chargement:false})});return()=>{vivant=false}},[date,recherche,decalage,version])
  const muter=async action=>{await action();setForm(null);setVersion(v=>v+1);if(detail)setDetail(await api.lire(detail.id))}
  const ecriture=['admin','comptable','personnel'].includes(user?.role)
  return <><p className={s.notice}>Les rubriques décrivent vos primes et indemnités, et leur traitement CNSS, AMO et IR.</p>
    <div className={s.barre}><Champ label="Règles applicables au"><input type="date" required value={date} onChange={e=>setDate(e.target.value||dateLocale())}/></Champ>
      <form className={s.recherche} onSubmit={e=>{e.preventDefault();setDecalage(0);setRecherche(texte)}}><Champ label="Rechercher une rubrique"><input value={texte} maxLength={150} onChange={e=>setTexte(e.target.value)}/></Champ><button className={s.secondaire}>Rechercher</button></form>
      {ecriture&&cap('proposer')&&<button className={s.primaire} onClick={()=>setForm({nature:'creation'})}>Créer une rubrique</button>}</div>
    <Erreur message={etat.erreur||erreur}/>{etat.chargement&&<p role="status">Chargement du catalogue…</p>}
    {etat.data?.elements.map(r=><section key={r.id} className={s.carte} aria-label={`Rubrique ${r.code}`}><div className={s.titreFiche}><div><h2>{r.code} · {r.dernier_contenu.libelle}</h2><p>Version {r.derniere_numero} · {ETATS[r.derniere_statut]}</p></div><button className={s.secondaire} onClick={async()=>{setErreur('');try{setDetail(await api.lire(r.id))}catch(e){setErreur(e.message)}}}>Consulter {r.code}</button></div>
      <p className={s.discret}>{r.courante_id?`Version approuvée applicable à cette date : ${r.contenu_applicable.libelle}`:'Aucune version approuvée applicable à cette date.'}</p></section>)}
    {etat.data&&!etat.data.total&&<EtatVide icone="ti-list-details" titre="Créez vos rubriques de paie" action={ecriture&&cap('proposer')?'Créer ma première rubrique':null} onAction={()=>setForm({nature:'creation'})}>Les rubriques décrivent ce qui s’ajoute au salaire de base : primes, indemnités, heures supplémentaires… Pour chacune, vous indiquez si elle est soumise à la CNSS, à l’AMO et à l’IR.</EtatVide>}
    {etat.data&&<div className={s.pagination}><span>{etat.data.total?pluriel(etat.data.total,'rubrique'):''}</span><button className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-25))}>Précédent</button><button className={s.secondaire} disabled={decalage+25>=etat.data.total} onClick={()=>setDecalage(decalage+25)}>Suivant</button></div>}
    {detail&&<section className={s.carte} aria-label={`Versions ${detail.code}`}><div className={s.titreFiche}><h2>Versions de {detail.code}</h2><div className={s.actions}><button className={s.secondaire} onClick={()=>setDetail(null)}>Fermer le détail</button>{ecriture&&cap('proposer')&&<button className={s.primaire} onClick={()=>setForm({nature:'version',rubrique:detail})}>Proposer une nouvelle version</button>}</div></div>
      {detail.versions.map(v=><Version key={v.id} v={v} user={user} peutDecider={ecriture&&cap('approuver')} peutQualifier={cap('valider_regles_paie')} decider={approbation=>setForm({nature:'decision',v,approbation})}/>)}</section>}
    {form&&form.nature!=='decision'&&<Edition initial={form.rubrique} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>form.nature==='creation'?api.creer(data):api.proposer(form.rubrique.id,data))}/>}
    {form?.nature==='decision'&&<Decision v={form.v} approbation={form.approbation} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>api.decider(form.v.id,form.approbation,data))}/>}
  </>
}
function Edition({initial,onFermer,onEnvoyer}){
  const [c,setC]=useState(()=>initial?{...structuredClone(initial.versions[0].contenu),date_debut:'',date_fin:'',compte_charge:initial.versions[0].contenu.compte_charge||''}:vide()),[code,setCode]=useState(''),[motif,setMotif]=useState('')
  const [pieces,setPieces]=useState(()=>c.justificatifs.join(', ')),[incompatibles,setIncompatibles]=useState(()=>c.incompatibilites.join(', '))
  const champ=(k,label,props={})=><Champ label={label}><input {...props} value={c[k]??''} onChange={e=>setC(p=>({...p,[k]:e.target.value}))}/></Champ>
  const choix=(k,label,options)=><Champ label={label}><select value={c[k]} onChange={e=>setC(p=>({...p,[k]:e.target.value}))}>{Object.entries(options).map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></Champ>
  const changer=(reg,k,val)=>setC(p=>({...p,regles:{...p.regles,[reg]:{...p.regles[reg],[k]:val,...(k==='traitement'&&val!=='PLAFOND_MONTANT'?{plafond:null}:{})}}}))
  return <Formulaire titre={initial?'Nouvelle version de rubrique':'Nouvelle rubrique'} onFermer={onFermer} onEnvoyer={()=>onEnvoyer({...(initial?{version_attendue:initial.versions[0].numero}:{code}),contenu:{...c,date_fin:c.date_fin||null,compte_charge:c.compte_charge||null,justificatifs:pieces.split(',').map(v=>v.trim()).filter(Boolean),incompatibilites:incompatibles.split(',').map(v=>v.trim()).filter(Boolean)},motif})}>
    {!initial&&<Champ label="Code de rubrique"><input required pattern="[A-Z][A-Z0-9_]{1,39}" maxLength={40} value={code} onChange={e=>setCode(e.target.value.toUpperCase())}/></Champ>}
    <div className={s.grille}>{champ('libelle','Libellé de rubrique',{required:true,maxLength:150})}{choix('nature','Nature',{GAIN:'Gain',RETENUE:'Retenue',REMBOURSEMENT:'Remboursement'})}{choix('periodicite','Périodicité',{mensuelle:'Mensuelle',ponctuelle:'Ponctuelle',annuelle:'Annuelle'})}{choix('formule','Mode de saisie',{MONTANT:'Montant exact',QUANTITE_TAUX:'Quantité × taux'})}
      {champ('date_debut','Début d’application',{type:'date',required:true})}{champ('date_fin','Fin d’application (facultatif)',{type:'date'})}{champ('compte_charge','Compte de charge (facultatif)',{inputMode:'numeric',maxLength:10})}
      <Champ label="Justificatifs attendus (séparés par virgules)"><input maxLength={1000} value={pieces} onChange={e=>setPieces(e.target.value)}/></Champ>
      <Champ label="Codes incompatibles (séparés par virgules)"><input maxLength={1000} value={incompatibles} onChange={e=>setIncompatibles(e.target.value)}/></Champ></div>
    {REGIMES.map(reg=>{const r=c.regles[reg];return <section key={reg} className={s.donnees}><h2>Règle {reg}</h2><div className={s.grille}>
      <Champ label={`Traitement ${reg}`}><select value={r.traitement} onChange={e=>changer(reg,'traitement',e.target.value)}>{Object.entries(TRAITEMENTS).map(([k,t])=><option key={k} value={k}>{t}</option>)}</select></Champ>
      <Champ label={`Statut réglementaire ${reg}`}><select value={r.statut_reglementaire} onChange={e=>changer(reg,'statut_reglementaire',e.target.value)}><option value="A_VERIFIER">À vérifier</option><option value="VALIDE">Validé après contrôle humain</option><option value="OBSOLETE">Obsolète</option></select></Champ>
      {r.traitement==='PLAFOND_MONTANT'&&<Champ label={`Plafond ${reg} (MAD)`}><input required inputMode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" value={r.plafond??''} onChange={e=>changer(reg,'plafond',e.target.value)}/></Champ>}
      <Champ label={`Unité du plafond ${reg}`}><select value={r.unite} onChange={e=>changer(reg,'unite',e.target.value)}>{Object.entries({mensuel:'Mensuelle',journalier:'Journalière',annuel:'Annuelle',operation:'Par opération'}).map(([k,t])=><option key={k} value={k}>{t}</option>)}</select></Champ>
      <Champ label={`Conditions ${reg}`}><textarea required maxLength={2000} value={r.conditions} onChange={e=>changer(reg,'conditions',e.target.value)}/></Champ>
      {r.statut_reglementaire==='VALIDE'&&[['texte_reference','Texte'],['article','Article'],['url_source','URL officielle'],['empreinte_preuve','Empreinte SHA-256 de la preuve']].map(([k,t])=><Champ key={k} label={`${t} ${reg}`}><input required type={k==='url_source'?'url':'text'} maxLength={k==='url_source'?2000:k==='empreinte_preuve'?64:k==='article'?150:300} value={r[k]??''} onChange={e=>changer(reg,k,e.target.value||null)}/></Champ>)}
    </div></section>})}
    <QualificationIRForm mode="FRAIS" valeur={c.frais_professionnels} onChange={v=>setC(p=>({...p,frais_professionnels:v}))}/>
    <Champ label="Motif de la proposition"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
    <p className={s.discret}>Aucune formule libre n’est exécutée. Les dates et preuves restent attachées à cette version ; la proposition n’active pas une paie.</p>
  </Formulaire>
}
function Version({v,user,peutDecider,peutQualifier,decider}){
  const c=v.contenu,[montant,setMontant]=useState(''),[apercu,setApercu]=useState(null),[erreur,setErreur]=useState(''),[occupe,setOccupe]=useState(false)
  const qualificationRequise=Object.values(c.regles).some(r=>r.statut_reglementaire==='VALIDE')||c.frais_professionnels?.statut_reglementaire==='VALIDE'
  return <article className={s.donnees} style={{marginTop:16}}><h3>Version {v.numero} · {ETATS[v.statut]} · {v.date_debut}{v.date_fin?` au ${v.date_fin}`:''}</h3><p className={s.resume}>{c.libelle} · {c.nature} · {c.periodicite} · {c.formule}</p>
    <p className={s.discret}>Justificatifs : {c.justificatifs.join(', ')||'Aucun type déclaré'} · Incompatibilités : {c.incompatibilites.join(', ')||'Aucune déclarée'} · Compte : {c.compte_charge||'À paramétrer avant comptabilisation'}</p>
    <div className={s.grille}>{REGIMES.map(reg=>{const r=c.regles[reg];return <div key={reg}><h3>{reg}</h3><p>{TRAITEMENTS[r.traitement]}{r.plafond!=null?` · ${euro(r.plafond)} / ${r.unite}`:''}</p><p className={s.discret}>{r.statut_reglementaire} · {r.conditions}</p>{r.texte_reference&&<p className={s.discret}>{r.texte_reference} · {r.article}</p>}{r.url_source&&<a className={s.lien} href={r.url_source} target="_blank" rel="noopener noreferrer">Source {reg}</a>}</div>})}</div>
    <QualificationIRResume mode="FRAIS" valeur={c.frais_professionnels}/>
    <p className={s.discret}>Préparateur #{v.prepare_par} · {v.motif}{v.decision_par?` · Décideur #${v.decision_par} · ${v.motif_decision} · ${v.reference_controle}`:''}</p>
    {v.statut==='PROPOSEE'&&peutDecider&&<><div className={s.actions}><button className={s.secondaire} onClick={()=>decider(false)}>Rejeter la version {v.numero}</button><button className={s.primaire} disabled={v.prepare_par===user?.id||(qualificationRequise&&!peutQualifier)} onClick={()=>decider(true)}>Approuver la version {v.numero}</button></div>{qualificationRequise&&!peutQualifier&&<p className={s.discret}>L’habilitation dédiée à la qualification réglementaire est requise pour approuver ces règles.</p>}</>}
    <details className={s.donnees} style={{marginTop:12}}><summary>Aperçu pédagogique de ventilation · version {v.numero}</summary><form className={s.recherche} onSubmit={async e=>{e.preventDefault();if(occupe)return;setOccupe(true);setErreur('');try{setApercu(await api.apercu(v.id,{montant}))}catch(err){setApercu(null);setErreur(err.message)}finally{setOccupe(false)}}}><Champ label={`Montant à simuler version ${v.numero}`}><input required inputMode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" value={montant} onChange={e=>{setMontant(e.target.value);setApercu(null)}}/></Champ><button className={s.secondaire} disabled={occupe}>Simuler la ventilation</button></form><Erreur message={erreur}/>
      {apercu&&<div role="status"><p className={s.notice}>Aperçu indicatif, avant approbation.</p>{REGIMES.map(reg=><p key={reg} className={s.discret}>{reg} : soumis {euro(apercu.regimes[reg].soumis)} · exonéré {euro(apercu.regimes[reg].exonere)} · {apercu.regimes[reg].alerte}</p>)}</div>}</details>
  </article>
}
function Decision({v,approbation,onFermer,onEnvoyer}){
  const seul=useValidationUnique(),[motif,setMotif]=useState(''),[reference,setReference]=useState(''),[indep,setIndep]=useState(seul),[reglement,setReglement]=useState(false)
  const requis=Object.values(v.contenu.regles).some(r=>r.statut_reglementaire==='VALIDE')||v.contenu.frais_professionnels?.statut_reglementaire==='VALIDE'
  return <Formulaire titre={approbation?'Approbation de rubrique':'Rejet de rubrique'} onFermer={onFermer} libelle={approbation?'Confirmer l’approbation':'Confirmer le rejet'} onEnvoyer={()=>onEnvoyer({motif,reference_controle:reference,independance_confirmee:indep,verification_reglementaire_confirmee:reglement})}>
    <p className={s.notice}>Version {v.numero} : {v.contenu.libelle}. Contrôlez les règles et leurs preuves dans le détail. L’approbation ne calcule aucune paie.</p>
    <Champ label="Motif de la décision"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ><Champ label="Référence du contrôle"><input required maxLength={200} value={reference} onChange={e=>setReference(e.target.value)}/></Champ>
    {approbation&&<>{seul?<p className={s.discret}><i className="ti ti-user-check" aria-hidden="true"/> Validation par une seule personne (petite entreprise) : votre nom est enregistré comme décideur.</p>:<label className={s.coche}><input type="checkbox" required checked={indep} onChange={e=>setIndep(e.target.checked)}/>Je confirme être indépendant du préparateur.</label>}<label className={s.coche}><input type="checkbox" required={requis} checked={reglement} onChange={e=>setReglement(e.target.checked)}/>J’ai vérifié les textes, preuves et conditions des règles déclarées validées.</label></>}
  </Formulaire>
}
