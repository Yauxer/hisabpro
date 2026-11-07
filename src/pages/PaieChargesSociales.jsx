import {useEffect,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {QualificationIRForm,QualificationIRResume} from '../components/PaieQualificationIR.jsx'
import PaieSimulationsSociales from '../components/PaieSimulationsSociales.jsx'
import {Champ,Erreur,Formulaire} from '../components/PaieVariables.jsx'
import {useModules} from '../data/ModulesContext.jsx'
import {paieSocialAPI as api} from '../services/api.js'
import PaieAccesRequis,{accesPaieManquant} from '../components/PaieAccesRequis.jsx'
import EtatVide from '../components/EtatVide.jsx'
import {MODELE_COTISATIONS_MAROC,REGIME_MODELE} from '../data/modeleCotisationsMaroc.js'
import {notifier} from '../services/notifications.js'
import {pluriel} from '../utils/formatPaie.js'
import {usePersonnelAcces,useValidationUnique} from '../data/PersonnelAccesContext.jsx'
import s from './Personnel.module.css'

const ETATS={PROPOSEE:'Proposée',APPROUVEE:'Approuvée',REJETEE:'Rejetée'}
const jour=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
const inconnu=v=>v==null?'À qualifier':v
function vide(){return {libelle:'',organisme:'',applicabilite:'A_VERIFIER',calcul_mode:'A_QUALIFIER',assiette:'A_QUALIFIER',taux_salarial:null,taux_patronal:null,forfait_salarial:null,forfait_patronal:null,plafond_mode:'A_VERIFIER',plafond:null,unite:'mensuel',composants:[],conditions:'',date_debut:'',date_fin:null,source_nature:'REGLEMENTAIRE',statut_reglementaire:'A_VERIFIER',source_reference:null,texte_reference:null,article:null,url_source:null,empreinte_preuve:null,date_consultation:null}}

export default function PaieChargesSociales(){
  const ctx=usePersonnelAcces(),{societe,aGRH}=useModules(),cap=k=>ctx.acces?.capacites.includes('personnel.'+k)
  const simulations=useLocation().pathname.endsWith('/simulations')
  let contenu
  if(ctx.chargement)contenu=<p role="status">Chargement des accès…</p>
  else if(ctx.erreur)contenu=<Erreur message={ctx.erreur}/>
  else if(accesPaieManquant(ctx,aGRH))contenu=<PaieAccesRequis ctx={ctx}/>
  else contenu=simulations?<PaieSimulationsSociales key={`${societe?.id}:${ctx.version}`} peutSimuler={cap('proposer')&&['admin','comptable','personnel'].includes(ctx.user?.role)}/>:<Referentiel key={`${societe?.id}:${ctx.version}`} cap={cap} user={ctx.user}/>
  return <div className={s.page} data-form-page><header className={s.entete}><div><h1>Charges sociales</h1><p>{societe?.raison_sociale} · Taux de cotisation et calcul des charges</p></div><button className={s.secondaire} onClick={ctx.recharger} disabled={ctx.chargement}>Actualiser</button></header>
    <nav className={s.onglets} aria-label="Sous-parties : Charges sociales"><Link className={!simulations?s.actif:''} to="/personnel-paie/charges-sociales">Taux et plafonds</Link><Link className={simulations?s.actif:''} to="/personnel-paie/charges-sociales/simulations">Calcul des cotisations</Link></nav><div className={s.contenu}>{contenu}</div></div>
}
function Referentiel({cap,user}){
  const [au,setAu]=useState(jour),[texte,setTexte]=useState(''),[recherche,setRecherche]=useState(''),[regime,setRegime]=useState(''),[filtre,setFiltre]=useState(''),[decalage,setDecalage]=useState(0),[revision,setRevision]=useState(0)
  const [etat,setEtat]=useState({data:null,erreur:'',chargement:true}),[detail,setDetail]=useState(null),[form,setForm]=useState(null),[erreur,setErreur]=useState('')
  useEffect(()=>{let actif=true;setEtat({data:null,erreur:'',chargement:true});api.lister({au,recherche,regime:filtre,decalage}).then(data=>{if(actif)setEtat({data,erreur:'',chargement:false})}).catch(e=>{if(actif)setEtat({data:null,erreur:e.message,chargement:false})});return()=>{actif=false}},[au,recherche,filtre,decalage,revision])
  const ecriture=['admin','comptable','personnel'].includes(user?.role)
  const muter=async action=>{await action();setForm(null);setRevision(v=>v+1);if(detail)setDetail(await api.lire(detail.id))}
  const [chargementModele,setChargementModele]=useState(false)
  async function chargerModele(){
    const liste=MODELE_COTISATIONS_MAROC.map(m=>`• ${m.contenu.libelle} : ${m.contenu.taux_salarial} % salarié, ${m.contenu.taux_patronal} % employeur${m.contenu.plafond?` (plafond ${m.contenu.plafond} DH)`:''}`).join('\n')
    if(!window.confirm(`Créer ces cotisations en propositions, relevées sur cnss.ma le 31/10/2026 :\n\n${liste}\n\nVérifiez-les puis approuvez-les une par une. La taxe de formation professionnelle n’est pas incluse.`))return
    setChargementModele(true);setErreur('');let n=0
    try{for(const m of MODELE_COTISATIONS_MAROC){try{await api.creer({code:m.code,regime:REGIME_MODELE,contenu:m.contenu,motif:'Modèle CNSS HisabPro (sources cnss.ma, à vérifier)'});n++}catch(e){if(!/existe|déjà|conflit/i.test(e.message))throw e}}
      notifier.succes(`${n} cotisation(s) proposée(s) : ouvrez chacune pour la vérifier et l’approuver.`);setRevision(v=>v+1)}
    catch(e){setErreur(e.message)}finally{setChargementModele(false)}
  }
  return <><p className={s.notice}>Taux et plafonds de vos cotisations (CNSS, AMO…). Chaque cotisation proposée doit être vérifiée puis approuvée avant d’entrer dans le calcul.</p>
    <div className={s.barre}><Champ label="Applicables au"><input type="date" required value={au} onChange={e=>setAu(e.target.value||jour())}/></Champ>
      <form className={s.recherche} onSubmit={e=>{e.preventDefault();setRecherche(texte);setFiltre(regime);setDecalage(0)}}><Champ label="Rechercher une branche"><input value={texte} maxLength={150} onChange={e=>setTexte(e.target.value)}/></Champ><Champ label="Code régime (facultatif)"><input value={regime} maxLength={80} pattern="[A-Z][A-Z0-9_]{1,79}" onChange={e=>setRegime(e.target.value.toUpperCase())}/></Champ><button className={s.secondaire}>Rechercher</button></form>
      {ecriture&&cap('proposer')&&<button className={s.primaire} onClick={()=>setForm({type:'creation'})}>Créer une branche</button>}</div>
    <Erreur message={etat.erreur||erreur}/>{etat.chargement&&<p role="status">Chargement du référentiel…</p>}
    {etat.data?.elements.map(r=><section key={r.id} className={s.carte} aria-label={`Branche ${r.regime} ${r.code}`}><div className={s.titreFiche}><div><h2>{r.code} · {r.dernier_contenu.libelle}</h2><p>Régime {r.regime} · Version {r.derniere_numero} · {ETATS[r.derniere_statut]}</p></div><button className={s.secondaire} onClick={async()=>{setErreur('');try{setDetail(await api.lire(r.id))}catch(e){setErreur(e.message)}}}>Consulter {r.code}</button></div><p className={s.discret}>{r.courante_id?`Version approuvée applicable : ${r.contenu_applicable.libelle}`:'Aucune version approuvée applicable à cette date.'}</p></section>)}
    {etat.data&&!etat.data.total&&<EtatVide icone="ti-building-community" titre="Paramétrez vos cotisations sociales" action={ecriture&&cap('proposer')?(chargementModele?'Chargement…':'Charger le modèle CNSS (à vérifier)'):null} onAction={chargerModele} action2={ecriture&&cap('proposer')?'Saisir une cotisation à la main':null} onAction2={()=>setForm({type:'creation'})}>Ajoutez chaque cotisation (CNSS prestations sociales, AMO…) avec son taux salarial, son taux patronal et son plafond. HisabPro propose un modèle avec les taux relevés sur cnss.ma : vérifiez-les avant de les approuver.</EtatVide>}
    {etat.data&&<div className={s.pagination}><span>{etat.data.total?pluriel(etat.data.total,'cotisation'):''}</span><button className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-25))}>Précédent</button><button className={s.secondaire} disabled={decalage+25>=etat.data.total} onClick={()=>setDecalage(decalage+25)}>Suivant</button></div>}
    {detail&&<section className={s.carte} aria-label={`Versions ${detail.code}`}><div className={s.titreFiche}><h2>Versions de {detail.code} · {detail.regime}</h2><div className={s.actions}><button className={s.secondaire} onClick={()=>setDetail(null)}>Fermer le détail</button>{ecriture&&cap('proposer')&&<button className={s.primaire} onClick={()=>setForm({type:'version',initial:detail})}>Proposer une nouvelle version</button>}</div></div>{detail.versions.map(v=><article className={s.donnees} key={v.id}><h3>Version {v.numero} · {ETATS[v.statut]} · {v.date_debut}{v.date_fin?` au ${v.date_fin}`:''}</h3><Resume c={v.contenu}/><p className={s.discret}>Préparateur #{v.prepare_par} · {v.motif}{v.decision_par?` · Décideur #${v.decision_par} · ${v.motif_decision} · ${v.reference_controle}`:''}</p>
      {v.statut==='PROPOSEE'&&ecriture&&cap('approuver')&&<div className={s.actions}><button className={s.secondaire} onClick={()=>setForm({type:'decision',v,approbation:false})}>Rejeter la version {v.numero}</button><button className={s.primaire} disabled={v.prepare_par===user?.id||(v.contenu.statut_reglementaire==='VALIDE'||v.contenu.deductibilite_ir?.statut_reglementaire==='VALIDE')&&!cap('valider_regles_paie')} onClick={()=>setForm({type:'decision',v,approbation:true})}>Approuver la version {v.numero}</button></div>}</article>)}</section>}
    {form&&form.type!=='decision'&&<Edition initial={form.initial} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>form.type==='creation'?api.creer(data):api.proposer(form.initial.id,data))}/>}
    {form?.type==='decision'&&<Decision {...form} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>api.decider(form.v.id,form.approbation,data))}/>}
  </>
}
function Resume({c}){return <><p>{c.organisme} · {c.applicabilite} · {c.statut_reglementaire} · {c.source_nature}</p><p>Mode {c.calcul_mode} · Assiette {c.assiette} · Plafond {c.plafond_mode}{c.plafond!=null?` : ${c.plafond} MAD / ${c.unite}`:''}</p><p>Part salariale : {c.calcul_mode==='FORFAIT'?`${inconnu(c.forfait_salarial)} MAD`:`${inconnu(c.taux_salarial)} %`} · Part patronale : {c.calcul_mode==='FORFAIT'?`${inconnu(c.forfait_patronal)} MAD`:`${inconnu(c.taux_patronal)} %`}</p><p>Composants : {c.composants.join(', ')||'À qualifier'}</p><p className={s.discret}>{c.conditions}</p><p className={s.discret}>{c.source_reference||'Référence à documenter'} · {c.texte_reference} · {c.article} · Consultation {c.date_consultation||'à renseigner'}</p>{c.url_source&&<a className={s.lien} href={c.url_source} target="_blank" rel="noopener noreferrer">Consulter la source officielle</a>}{c.empreinte_preuve&&<p className={s.discret} style={{overflowWrap:'anywhere'}}>SHA-256 déclaré : {c.empreinte_preuve}</p>}<QualificationIRResume mode="DEDUCTION" valeur={c.deductibilite_ir}/></>}
function Edition({initial,onFermer,onEnvoyer}){
  const [c,setC]=useState(()=>initial?{...structuredClone(initial.versions[0].contenu),date_debut:'',date_fin:null}:vide()),[code,setCode]=useState(''),[regime,setRegime]=useState(''),[motif,setMotif]=useState(''),[composants,setComposants]=useState(()=>c.composants.join(', '))
  const changer=(k,v)=>setC(p=>({...p,[k]:v,...(k==='calcul_mode'?{taux_salarial:null,taux_patronal:null,forfait_salarial:null,forfait_patronal:null,...(v==='FORFAIT'?{assiette:'A_QUALIFIER',plafond_mode:'SANS',plafond:null}:{})}:{}),...(k==='plafond_mode'&&v!=='MONTANT'?{plafond:null}:{})}))
  const champ=(k,label,props={})=><Champ label={label}><input {...props} value={c[k]??''} onChange={e=>changer(k,e.target.value||null)}/></Champ>
  const choix=(k,label,options)=><Champ label={label}><select value={c[k]} onChange={e=>changer(k,e.target.value)}>{Object.entries(options).map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></Champ>
  const qualifie=c.statut_reglementaire==='VALIDE'
  return <Formulaire titre={initial?'Nouvelle version sociale':'Nouvelle branche sociale'} libelle="Enregistrer la proposition" onFermer={onFermer} onEnvoyer={()=>onEnvoyer({...(initial?{version_attendue:initial.versions[0].numero}:{code,regime}),contenu:{...c,composants:composants.split(',').map(x=>x.trim()).filter(Boolean)},motif})}>
    <p className={s.notice}>Un régime regroupe les cotisations qui s’appliquent ensemble (par exemple « CNSS »).</p>
    <div className={s.grille}>{!initial&&<><Champ label="Code de branche"><input required pattern="[A-Z][A-Z0-9_]{1,39}" maxLength={40} value={code} onChange={e=>setCode(e.target.value.toUpperCase())}/></Champ><Champ label="Code régime"><input required pattern="[A-Z][A-Z0-9_]{1,79}" maxLength={80} value={regime} onChange={e=>setRegime(e.target.value.toUpperCase())}/></Champ></>}
      {champ('libelle','Libellé de branche',{required:true,maxLength:150})}{champ('organisme','Organisme',{required:true,maxLength:150})}
      {choix('applicabilite','Applicabilité',{A_VERIFIER:'À vérifier',APPLICABLE:'Applicable sous les conditions déclarées',NON_APPLICABLE:'Non applicable, justification requise'})}
      {choix('calcul_mode','Mode de calcul',{A_QUALIFIER:'À qualifier',TAUX:'Taux en pourcentage',FORFAIT:'Forfait exact'})}
      {c.calcul_mode==='TAUX'&&<>{choix('assiette','Assiette de la branche',{A_QUALIFIER:'À qualifier',CNSS:'Assiette CNSS',AMO:'Assiette AMO',BRUT:'Brut'})}{champ('taux_salarial','Taux salarial (%)',{inputMode:'decimal',pattern:'[0-9]+([.][0-9]{1,6})?'})}{champ('taux_patronal','Taux patronal (%)',{inputMode:'decimal',pattern:'[0-9]+([.][0-9]{1,6})?'})}</>}
      {c.calcul_mode==='FORFAIT'&&<>{champ('forfait_salarial','Forfait salarial (MAD)',{inputMode:'decimal',pattern:'[0-9]+([.][0-9]{1,2})?'})}{champ('forfait_patronal','Forfait patronal (MAD)',{inputMode:'decimal',pattern:'[0-9]+([.][0-9]{1,2})?'})}</>}
      {c.calcul_mode!=='FORFAIT'&&choix('plafond_mode','Plafonnement',{A_VERIFIER:'À vérifier',SANS:'Sans plafond déclaré',MONTANT:'Plafond en montant'})}
      {c.plafond_mode==='MONTANT'&&<>{champ('plafond','Plafond (MAD)',{required:true,inputMode:'decimal',pattern:'[0-9]+([.][0-9]{1,2})?'})}{choix('unite','Unité du plafond',{mensuel:'Mensuelle',annuel:'Annuelle',journalier:'Journalière'})}</>}
      <Champ label="Composants couverts (codes séparés par virgules)"><input maxLength={1250} value={composants} onChange={e=>setComposants(e.target.value.toUpperCase())}/></Champ>
      {champ('date_debut','Début d’application',{required:true,type:'date'})}{champ('date_fin','Fin d’application (facultatif)',{type:'date'})}
      {choix('source_nature','Nature de la source',{REGLEMENTAIRE:'Réglementaire',CONTRACTUELLE:'Contractuelle'})}{choix('statut_reglementaire','Qualification de la règle',{A_VERIFIER:'À vérifier',VALIDE:'Validée après contrôle humain',OBSOLETE:'Obsolète'})}
    </div><Champ label="Conditions et justification d’applicabilité"><textarea required maxLength={2000} value={c.conditions} onChange={e=>changer('conditions',e.target.value)}/></Champ>
    <div className={s.grille}>{champ('source_reference','Référence du justificatif',{required:qualifie,maxLength:300})}{champ('texte_reference','Texte ou convention',{required:qualifie,maxLength:300})}{champ('article','Article',{required:qualifie&&c.source_nature==='REGLEMENTAIRE',maxLength:150})}{champ('url_source','URL officielle (HTTPS)',{required:qualifie&&c.source_nature==='REGLEMENTAIRE',type:'url',maxLength:2000})}{champ('empreinte_preuve','Empreinte SHA-256 de la preuve',{required:qualifie,pattern:'[a-f0-9]{64}',maxLength:64})}{champ('date_consultation','Date de consultation',{required:qualifie,type:'date',max:jour()})}</div>
    <QualificationIRForm mode="DEDUCTION" valeur={c.deductibilite_ir} onChange={v=>setC(p=>({...p,deductibilite_ir:v}))}/>
    <Champ label="Motif de la proposition"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
  </Formulaire>
}
function Decision({v,approbation,onFermer,onEnvoyer}){
  const seul=useValidationUnique(),[motif,setMotif]=useState(''),[reference,setReference]=useState(''),[indep,setIndep]=useState(seul),[preuve,setPreuve]=useState(false)
  return <Formulaire titre={approbation?'Approbation sociale':'Rejet social'} onFermer={onFermer} libelle={approbation?'Confirmer l’approbation':'Confirmer le rejet'} onEnvoyer={()=>onEnvoyer({motif,reference_controle:reference,independance_confirmee:indep,verification_reglementaire_confirmee:preuve})}>
    <Resume c={v.contenu}/><Champ label="Motif de la décision"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ><Champ label="Référence du contrôle"><input required maxLength={200} value={reference} onChange={e=>setReference(e.target.value)}/></Champ>
    {approbation&&<>{seul?<p className={s.discret}><i className="ti ti-user-check" aria-hidden="true"/> Validation par une seule personne (petite entreprise) : votre nom est enregistré comme décideur.</p>:<label className={s.coche}><input type="checkbox" required checked={indep} onChange={e=>setIndep(e.target.checked)}/>Je confirme être indépendant du préparateur.</label>}<label className={s.coche}><input type="checkbox" required={v.contenu.statut_reglementaire==='VALIDE'||v.contenu.deductibilite_ir?.statut_reglementaire==='VALIDE'} checked={preuve} onChange={e=>setPreuve(e.target.checked)}/>J’ai vérifié les textes, preuves et conditions de la règle déclarée validée.</label></>}
  </Formulaire>
}
