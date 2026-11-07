import {useEffect,useState,useId,cloneElement,useRef} from 'react'
import Modal from './Modal.jsx'
import {paieVariablesAPI as api} from '../services/api.js'
import EtatVide from './EtatVide.jsx'
import {pluriel} from '../utils/formatPaie.js'
import {useValidationUnique} from '../data/PersonnelAccesContext.jsx'
import s from '../pages/Personnel.module.css'

const ETATS={BROUILLON:'Brouillon',SOUMIS:'Soumise',APPROUVE:'Approuvée',REJETE:'Rejetée',ANNULE:'Annulée'}
const moisCourant=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`}
export function Champ({label,children}){const id=useId();return <div className={s.champ}><label htmlFor={id}>{label}</label>{cloneElement(children,{id})}</div>}
export function Erreur({message}){return message?<p role="alert" className={s.erreur}>{message}</p>:null}
export function Formulaire({titre,onFermer,onEnvoyer,children,libelle}){
  const [occupe,setOccupe]=useState(false),[erreur,setErreur]=useState(''),ref=useRef(null)
  useEffect(()=>{const avant=document.activeElement,d=ref.current.closest('[role="dialog"]'),controles=()=>[...d.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled])')].filter(e=>e.getClientRects().length)
    ;(ref.current.querySelector('input,select,textarea')||controles()[0])?.focus()
    const clavier=e=>{if(e.key!=='Tab')return;const c=controles();if(e.shiftKey&&document.activeElement===c[0]){e.preventDefault();c.at(-1)?.focus()}else if(!e.shiftKey&&document.activeElement===c.at(-1)){e.preventDefault();c[0]?.focus()}}
    d.addEventListener('keydown',clavier);return()=>{d.removeEventListener('keydown',clavier);if(avant?.isConnected)avant.focus()}},[])
  return <Modal titre={titre} largeur="lg" onFermer={()=>{if(!occupe)onFermer()}}><form ref={ref} aria-label={titre} className={s.formulaire} onSubmit={async e=>{e.preventDefault();if(occupe)return;setOccupe(true);setErreur('');try{await onEnvoyer()}catch(err){setErreur(err.message)}finally{setOccupe(false)}}}>
    <fieldset disabled={occupe}>{children}</fieldset><Erreur message={erreur}/><div className={s.actions}><button className={s.secondaire} type="button" disabled={occupe} onClick={onFermer}>Annuler</button><button className={s.primaire} disabled={occupe}>{occupe?'Enregistrement…':libelle}</button></div>
  </form></Modal>
}

export default function PaieVariables({cap,user,mois,setMois}){
  const [statut,setStatut]=useState(''),[decalage,setDecalage]=useState(0),[revision,setRevision]=useState(0)
  const [etat,setEtat]=useState({data:null,chargement:true,erreur:''}),[detail,setDetail]=useState(null),[form,setForm]=useState(null),[erreur,setErreur]=useState('')
  const ecriture=['admin','comptable','personnel'].includes(user?.role)
  useEffect(()=>{let vivant=true;setEtat({data:null,chargement:true,erreur:''});api.lister({periode:mois?mois+'-01':null,statut,decalage}).then(data=>{if(vivant)setEtat({data,chargement:false,erreur:''})}).catch(e=>{if(vivant)setEtat({data:null,chargement:false,erreur:e.message})});return()=>{vivant=false}},[mois,statut,decalage,revision])
  const muter=async action=>{await action();setForm(null);setRevision(v=>v+1);if(detail)setDetail(await api.lire(detail.id))}
  return <><p className={s.notice}>Saisissez ici les primes et éléments variables du mois ; une fois approuvés, ils entrent dans le calcul du brut.</p>
    <div className={s.barre}><Champ label="Mois des variables"><input type="month" value={mois} onChange={e=>{setMois(e.target.value);setDecalage(0);setDetail(null)}}/></Champ><Champ label="Statut des variables"><select value={statut} onChange={e=>{setStatut(e.target.value);setDecalage(0)}}><option value="">Tous les statuts</option>{Object.entries(ETATS).map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></Champ>
      {ecriture&&cap('proposer')&&<button className={s.primaire} onClick={()=>setForm({type:'creation'})}>Saisir une variable</button>}</div>
    <Erreur message={etat.erreur||erreur}/>{etat.chargement&&<p role="status">Chargement des variables…</p>}
    {etat.data?.elements.map(v=><section key={v.id} className={s.carte} aria-label={`Variable ${v.id}`}><div className={s.titreFiche}><div><h2>{v.instantane.nom} · {v.instantane.code}</h2><p>{v.instantane.matricule} · {v.periode.slice(0,7)} · {ETATS[v.statut]}</p></div><strong className={s.montant}>{v.montant} MAD</strong></div><div className={s.actions}>
      <button className={s.secondaire} onClick={async()=>{setErreur('');try{setDetail(await api.lire(v.id))}catch(e){setErreur(e.message)}}}>Consulter la variable {v.id}</button>
      {v.statut==='BROUILLON'&&v.prepare_par===user?.id&&ecriture&&<>{cap('soumettre')&&<button className={s.primaire} onClick={()=>setForm({type:'soumettre',v})}>Soumettre la variable {v.id}</button>}{cap('proposer')&&<button className={s.secondaire} onClick={()=>setForm({type:'annuler',v})}>Annuler le brouillon {v.id}</button>}</>}
      {v.statut==='SOUMIS'&&ecriture&&cap('approuver')&&<><button className={s.primaire} disabled={[v.prepare_par,v.beneficiaire_snapshot].includes(user?.id)} onClick={()=>setForm({type:'approuver',v})}>Approuver la variable {v.id}</button><button className={s.secondaire} onClick={()=>setForm({type:'rejeter',v})}>Rejeter la variable {v.id}</button></>}
    </div></section>)}
    {etat.data&&!etat.data.total&&<EtatVide icone="ti-calendar-plus" titre="Aucune prime ni variable ce mois-ci" action={ecriture&&cap('proposer')?'Saisir une prime du mois':null} onAction={()=>setForm({type:'creation'})}>Saisissez ici les éléments qui changent d’un mois à l’autre : primes, heures supplémentaires, indemnités. Sans variable, le brut se calcule sur le seul salaire de base.</EtatVide>}
    {etat.data&&<div className={s.pagination}><span>{etat.data.total?pluriel(etat.data.total,'variable'):''}</span><button className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-25))}>Précédent</button><button className={s.secondaire} disabled={decalage+25>=etat.data.total} onClick={()=>setDecalage(decalage+25)}>Suivant</button></div>}
    {detail&&<section className={s.carte} aria-label={`Détail variable ${detail.id}`}><div className={s.titreFiche}><h2>Variable {detail.id} · {ETATS[detail.statut]}</h2><button className={s.secondaire} onClick={()=>setDetail(null)}>Fermer le détail</button></div>
      <p className={s.resume}>{detail.instantane.nom} · {detail.instantane.code} · {detail.montant} MAD · effet {detail.date_effet}</p><p className={s.discret}>Source : {detail.source_reference||'Masquée selon vos habilitations'} · préparateur #{detail.prepare_par} · référence de contrôle : {detail.reference_controle||'À renseigner'}</p>
      <p className={s.discret}>Rémunération contractuelle à cette date : {detail.instantane.remuneration.montant} MAD · {detail.instantane.remuneration.periodicite}. Cette base n’est pas une paie calculée.</p>
      <p className={s.discret}>{detail.instantane.arrondi}</p>
      <RattachementDetail valeur={detail.donnees.rattachement_revenus} masque={detail.historique_masque}/>
      {detail.donnees.justificatifs&&<ul className={s.historique}>{Object.entries(detail.donnees.justificatifs).map(([type,ref])=><li key={type}>{type} : {ref}</li>)}</ul>}
      {detail.historique_masque?<p className={s.discret}>Historique réservé aux habilitations utiles.</p>:<ol className={s.historique}>{detail.evenements.map(e=><li key={e.id}>{ETATS[e.statut]} · utilisateur #{e.auteur_id} · {e.motif}</li>)}</ol>}
    </section>}
    {form?.type==='creation'&&<Creation mois={mois||moisCourant()} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>api.creer(data))}/>}
    {form&&form.type!=='creation'&&<Action type={form.type} v={form.v} onFermer={()=>setForm(null)} onEnvoyer={data=>muter(()=>api.transition(form.v.id,form.type,data))}/>}
  </>
}

function Creation({mois,onFermer,onEnvoyer}){
  const [debut,setDebut]=useState(''),[fin,setFin]=useState(''),[justification,setJustification]=useState(''),[versement,setVersement]=useState(''),[preuveVersement,setPreuveVersement]=useState('')
  const [periode,setPeriode]=useState(mois),[effet,setEffet]=useState(''),[rechercheS,setRechercheS]=useState(''),[rechercheR,setRechercheR]=useState(''),[revision,setRevision]=useState(0)
  const [options,setOptions]=useState({data:null,erreur:'',chargement:false}),[eid,setEid]=useState(''),[rid,setRid]=useState(''),[montant,setMontant]=useState(''),[quantite,setQuantite]=useState(''),[taux,setTaux]=useState(''),[source,setSource]=useState(''),[motif,setMotif]=useState(''),[pieces,setPieces]=useState({})
  useEffect(()=>{if(!effet){setOptions({data:null,erreur:'',chargement:false});return}let vivant=true;setOptions({data:null,erreur:'',chargement:true});api.options({au:effet,recherche_salarie:rechercheS,recherche_rubrique:rechercheR}).then(data=>{if(vivant)setOptions({data,erreur:'',chargement:false})}).catch(e=>{if(vivant)setOptions({data:null,erreur:e.message,chargement:false})});return()=>{vivant=false}},[effet,revision])
  const rubrique=options.data?.rubriques.find(r=>String(r.id)===rid),salarie=options.data?.salaries.find(p=>String(p.id)===eid)
  return <Formulaire titre="Nouvelle variable mensuelle" onFermer={onFermer} libelle="Enregistrer le brouillon" onEnvoyer={()=>{if(!rubrique||!salarie?.complet)throw new Error('Choisissez un dossier complet et une rubrique approuvée à la date d’effet.');return onEnvoyer({employe_id:Number(eid),rubrique_id:Number(rid),periode:periode+'-01',date_effet:effet,mode:rubrique.contenu.formule,...(rubrique.contenu.formule==='MONTANT'?{montant}:{quantite,taux}),...(debut||fin||justification||versement||preuveVersement?{rattachement_revenus:{reference_debut:debut||null,reference_fin:fin||null,reference_justification:justification||null,versement_date:versement||null,versement_reference:preuveVersement||null}}:{}),source_reference:source,justificatifs:Object.fromEntries(rubrique.contenu.justificatifs.map(type=>[type,pieces[type]||''])),motif})}}>
    <div className={s.grille}><Champ label="Période de la variable"><input type="month" required value={periode} onChange={e=>setPeriode(e.target.value)}/></Champ><Champ label="Date d’effet de la variable"><input type="date" required value={effet} onChange={e=>{setEffet(e.target.value);setEid('');setRid('');setPieces({})}}/></Champ>
      <Champ label="Rechercher un salarié pour la variable"><input maxLength={150} value={rechercheS} onChange={e=>setRechercheS(e.target.value)}/></Champ><Champ label="Rechercher une rubrique pour la variable"><input maxLength={150} value={rechercheR} onChange={e=>setRechercheR(e.target.value)}/></Champ></div>
    <button className={s.secondaire} type="button" disabled={!effet||options.chargement} onClick={()=>{setEid('');setRid('');setPieces({});setRevision(v=>v+1)}}>Rechercher les conditions applicables</button>
    <Erreur message={options.erreur}/>{options.chargement&&<p role="status">Chargement des conditions approuvées…</p>}
    {options.data&&<><p className={s.discret}>30 résultats maximum par liste ;affinez la recherche si nécessaire. Seuls les dossiers complets sont sélectionnables. Les rubriques proposées sans approbation ne sont pas disponibles.</p>
      <div className={s.grille}><Champ label="Salarié de la variable"><select required value={eid} onChange={e=>setEid(e.target.value)}><option value="">Choisir un salarié</option>{options.data.salaries.map(p=><option key={p.id} value={p.id} disabled={!p.complet}>{p.nom} · {p.matricule}{p.complet?'':' · À compléter'}</option>)}</select></Champ>
        <Champ label="Rubrique de la variable"><select required value={rid} onChange={e=>{setRid(e.target.value);setPieces({})}}><option value="">Choisir une rubrique approuvée</option>{options.data.rubriques.map(r=><option key={r.id} value={r.id}>{r.code} · {r.contenu.libelle}</option>)}</select></Champ></div>
      {salarie?.complet&&<p className={s.discret}>Base contractuelle approuvée : {salarie.remuneration.montant} MAD · {salarie.remuneration.periodicite}. Aucun prorata automatique.</p>}
    </>}
    {rubrique&&<>{rubrique.contenu.formule==='MONTANT'?<Champ label="Montant de la variable (MAD)"><input required inputMode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" value={montant} onChange={e=>setMontant(e.target.value)}/></Champ>:<div className={s.grille}>
      <Champ label="Quantité de la variable"><input required inputMode="decimal" pattern="[0-9]+([.][0-9]{1,6})?" value={quantite} onChange={e=>setQuantite(e.target.value)}/></Champ><Champ label="Taux unitaire de la variable (MAD)"><input required inputMode="decimal" pattern="[0-9]+([.][0-9]{1,6})?" value={taux} onChange={e=>setTaux(e.target.value)}/></Champ></div>}
      {rubrique.contenu.justificatifs.map(type=><Champ key={type} label={`Référence justificatif ${type}`}><input required maxLength={200} value={pieces[type]||''} onChange={e=>setPieces(p=>({...p,[type]:e.target.value}))}/></Champ>)}
      <p className={s.discret}>La référence désigne une pièce à contrôler humainement. Elle ne prouve pas automatiquement son existence. Quantité × taux est arrondi une fois au centime, au plus proche avec demi-centime vers le haut.</p>
    </>}
    <details className={s.donnees}><summary>Période de référence et versement déclaré (facultatif)</summary><p>La période à laquelle le revenu se rapporte peut différer du mois de traitement et de la date de versement. Saisir uniquement les faits documentés ; ces informations ne confirment aucun paiement et ne déclenchent aucun prorata.</p><div className={s.grille}>
      <Champ label="Début de la période de référence"><input type="date" value={debut} onChange={e=>setDebut(e.target.value)}/></Champ><Champ label="Fin de la période de référence"><input type="date" min={debut||undefined} value={fin} onChange={e=>setFin(e.target.value)}/></Champ>
      <Champ label="Justification de la période de référence"><input maxLength={200} value={justification} onChange={e=>setJustification(e.target.value)}/></Champ><Champ label="Date de versement déclarée"><input type="date" value={versement} onChange={e=>setVersement(e.target.value)}/></Champ><Champ label="Référence du versement déclaré"><input maxLength={200} value={preuveVersement} onChange={e=>setPreuveVersement(e.target.value)}/></Champ></div></details>
    <Champ label="Référence de la source de la variable"><input required maxLength={200} value={source} onChange={e=>setSource(e.target.value)}/></Champ><Champ label="Motif de saisie de la variable"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
  </Formulaire>
}
function Action({type,v,onFermer,onEnvoyer}){
  const seul=useValidationUnique(),[motif,setMotif]=useState(''),[ref,setRef]=useState(''),[indep,setIndep]=useState(seul),[preuves,setPreuves]=useState(false)
  const titres={soumettre:'Soumission de variable',annuler:'Annulation de brouillon',approuver:'Approbation de variable',rejeter:'Rejet de variable'},decision=['approuver','rejeter'].includes(type)
  return <Formulaire titre={titres[type]} onFermer={onFermer} libelle="Confirmer l’action" onEnvoyer={()=>onEnvoyer({motif,...(decision?{reference_controle:ref,independance_confirmee:indep,justificatifs_verifies:preuves}:{})})}>
    <p className={s.resume}>Variable {v.id} · {v.instantane.nom} · {v.instantane.code} · {v.montant} MAD</p><p className={s.discret}>Consultez le détail et les références des justificatifs avant décision. Cette action ne génère aucune paie.</p>
    <Champ label="Motif de l’action sur la variable"><textarea required maxLength={500} value={motif} onChange={e=>setMotif(e.target.value)}/></Champ>
    {decision&&<Champ label="Référence du contrôle de la variable"><input required maxLength={200} value={ref} onChange={e=>setRef(e.target.value)}/></Champ>}
    {type==='approuver'&&<>{seul?<p className={s.discret}><i className="ti ti-user-check" aria-hidden="true"/> Validation par une seule personne (petite entreprise) : votre nom est enregistré comme décideur.</p>:<label className={s.coche}><input type="checkbox" required checked={indep} onChange={e=>setIndep(e.target.checked)}/>Je suis indépendant du préparateur et du bénéficiaire de cette variable.</label>}<label className={s.coche}><input type="checkbox" required checked={preuves} onChange={e=>setPreuves(e.target.checked)}/>J’ai vérifié la source et les justificatifs de cette variable.</label></>}
  </Formulaire>
}

function RattachementDetail({valeur:r,masque}){return <section className={s.donnees} aria-label="Rattachement documentaire du revenu"><h3>Période de référence et versement déclaré</h3><p>Période de référence : {r?.reference_debut&&r?.reference_fin?`${r.reference_debut} au ${r.reference_fin}`:'Non renseignée'}</p><p>Justification : {r?.reference_justification||(masque?'Masquée selon vos habilitations':'Non renseignée')}</p><p>Date de versement déclarée : {r?.versement_date||'Non renseignée'}</p><p>Référence du versement : {r?.versement_reference||(masque?'Masquée selon vos habilitations':'Non renseignée')}</p><p className={s.discret}>Déclarations conservées avec cette variable ; aucune date déduite du mois de traitement, aucun paiement confirmé ni calcul de régularisation automatique.</p></section>}
