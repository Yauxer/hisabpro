import {useEffect,useState} from 'react'
import {Link} from 'react-router-dom'
import {usePersonnelAcces} from '../data/PersonnelAccesContext.jsx'
import {useModules} from '../data/ModulesContext.jsx'
import {paieCampagnesAPI as api} from '../services/api.js'
import {Champ,Erreur,Formulaire} from '../components/PaieVariables.jsx'
import PaieAccesRequis,{accesPaieManquant} from '../components/PaieAccesRequis.jsx'
import {mad,moisLibelle,pluriel} from '../utils/formatPaie.js'
import EtatVide from '../components/EtatVide.jsx'
import s from './Personnel.module.css'

const moisCourant=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`}
export default function PaieTraitement(){
  const ctx=usePersonnelAcces(),{societe,aGRH}=useModules(),cap=k=>ctx.acces?.capacites.includes('personnel.'+k)
  let contenu
  if(ctx.chargement)contenu=<p role="status">Chargement des accès…</p>
  else if(ctx.erreur)contenu=<Erreur message={ctx.erreur}/>
  else if(accesPaieManquant(ctx,aGRH))contenu=<PaieAccesRequis ctx={ctx}/>
  else contenu=<Campagnes key={`${societe?.id}:${ctx.version}`} peutSimuler={cap('proposer')&&['admin','comptable','personnel'].includes(ctx.user?.role)}/>
  return <div className={s.page} data-form-page><header className={s.entete}><div><h1>Traitement de la paie</h1><p>{societe?.raison_sociale} · Calcul du salaire brut, mois par mois</p></div><button className={s.secondaire} onClick={ctx.recharger} disabled={ctx.chargement}>Actualiser</button></header><div className={s.contenu}>{contenu}</div></div>
}
function Campagnes({peutSimuler}){
  const [revision,setRevision]=useState(0),[decalage,setDecalage]=useState(0),[etat,setEtat]=useState({data:null,erreur:'',chargement:true}),[form,setForm]=useState(false),[detail,setDetail]=useState(null),[hist,setHist]=useState(null),[erreur,setErreur]=useState('')
  useEffect(()=>{let vivant=true;setEtat({data:null,erreur:'',chargement:true});api.lister(decalage).then(data=>{if(vivant)setEtat({data,erreur:'',chargement:false})}).catch(e=>{if(vivant)setEtat({data:null,erreur:e.message,chargement:false})});return()=>{vivant=false}},[revision,decalage])
  const ouvrir=async id=>{setErreur('');try{setDetail(await api.lire(id))}catch(e){setErreur(e.message)}}
  return <><p className={s.notice}>Étape 1 du mois : le salaire brut (salaire de base + primes approuvées). Ensuite : cotisations, IR, puis <Link className={s.lien} to="/personnel-paie/bulletins">bulletins de paie</Link>.</p>
    {peutSimuler&&<div className={s.actions}><button className={s.primaire} onClick={()=>setForm(true)}>Calculer le brut du mois</button></div>}
    <Erreur message={etat.erreur||erreur}/>{etat.chargement&&<p role="status">Chargement…</p>}
    {etat.data?.elements.map(c=><section className={s.carte} key={c.id} aria-label={`Paie ${moisLibelle(c.periode)}`}><div className={s.titreFiche}><div><h2>Paie de {moisLibelle(c.periode)}</h2><p>{pluriel(c.nombre_salaries,'salarié')} · calcul n° {c.derniere_version} · {c.complet_pour_brut?'Complet':'Anomalies à traiter'}</p></div><strong className={s.montant}>{mad(c.brut)}</strong></div><div className={s.actions}>
      <button className={s.secondaire} aria-label={`Voir le détail du calcul ${c.derniere_simulation_id}`} onClick={()=>ouvrir(c.derniere_simulation_id)}>Voir le détail</button><button className={s.secondaire} onClick={async()=>{setErreur('');try{setHist({id:c.id,decalage:0,versions:await api.historique(c.id,0)})}catch(e){setErreur(e.message)}}} aria-label={`Historique des calculs ${c.id}`}>Historique</button>
    </div></section>)}
    {etat.data&&!etat.data.total&&<EtatVide icone="ti-calculator" titre="Aucune paie calculée" action={peutSimuler?'Calculer la paie d’un mois':null} onAction={()=>setForm(true)} lien="/personnel-paie/paie-du-mois" libelleLien="Voir toutes les étapes du mois">Le calcul du brut est la première étape de la paie du mois : salaire de base et primes approuvées de chaque salarié.</EtatVide>}
    {etat.data&&<div className={s.pagination}><span>{pluriel(etat.data.total,'mois calculé','mois calculés')}</span><button className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-25))}>Précédent</button><button className={s.secondaire} disabled={decalage+25>=etat.data.total} onClick={()=>setDecalage(decalage+25)}>Suivant</button></div>}
    {hist&&<section className={s.carte}><div className={s.titreFiche}><h2>Historique des calculs</h2><button className={s.secondaire} onClick={()=>setHist(null)}>Fermer l’historique</button></div><ul className={s.historique}>{hist.versions.map(v=><li key={v.id}><button className={s.lien} onClick={()=>ouvrir(v.id)}>Ouvrir la version {v.numero}</button> · {new Date(v.cree_at).toLocaleString('fr-FR')}</li>)}</ul><div className={s.actions}>{[-25,25].map(pas=><button className={s.secondaire} key={pas} disabled={pas<0?!hist.decalage:hist.versions.length<25} onClick={async()=>{try{const o=hist.decalage+pas;setHist({...hist,decalage:o,versions:await api.historique(hist.id,o)})}catch(e){setErreur(e.message)}}}>{pas<0?'Versions précédentes':'Versions suivantes'}</button>)}</div></section>}
    {detail&&<><Resultat detail={detail} onFermer={()=>setDetail(null)}/><Link className={s.lien} to={`/personnel-paie/charges-sociales/simulations?brut_id=${detail.id}`}>Préparer les cotisations de ce brut</Link></>}
    {form&&<Nouvelle onFermer={()=>setForm(false)} onEnvoyer={async data=>{const q=await api.simuler(data);setDetail(q);setHist(null);setForm(false);setRevision(v=>v+1)}}/>}
  </>
}
function Resultat({detail,onFermer}){
  const c=detail.contenu
  return <section className={s.carte} aria-label={`Résultat simulation ${detail.id}`}><div className={s.titreFiche}><div><h2>Calcul du brut · version {detail.numero}</h2><p>{moisLibelle(c.periode)} · {pluriel(c.employes.length,'salarié')}</p></div><button className={s.secondaire} onClick={onFermer}>Fermer le résultat</button></div>
    <p className={s.notice}>{c.complet_pour_brut?'Brut calculé pour tous les salariés sélectionnés.':'Calcul incomplet : traitez les anomalies ci-dessous avant de continuer.'}</p>
    <div className={s.grille}><div><h3>Base de la sélection</h3><p className={s.montant}>{mad(c.totaux.base)}</p></div><div><h3>Gains approuvés de la sélection</h3><p className={s.montant}>{mad(c.totaux.gains)}</p></div><div><h3>Brut de la sélection</h3><p className={s.montant} data-testid="brut-simulation">{mad(c.totaux.brut)}</p></div></div>
    <p className={s.discret}>Cotisations salariales : Non calculées · Cotisations patronales : Non calculées · IR : Non calculé · Net à payer : Non calculé · Coût employeur : Non calculé.</p>
    {c.employes.map(e=><article className={s.donnees} style={{marginTop:16}} key={e.employe_id}><h3>{e.nom} · {e.matricule}</h3><div className={s.grille}><p>Base : {mad(e.base)}</p><p>Gains : {mad(e.gains)}</p><p>Brut : {mad(e.brut)}</p></div>
      {!!e.anomalies.length&&<ul className={s.historique}>{e.anomalies.map((a,i)=><li key={a.code+':'+i}>{a.message}</li>)}</ul>}
      <p className={s.discret}>Contrat #{e.sources.contrat?.id??'À compléter'} · Rémunération #{e.sources.remuneration?.id??'À compléter'} · Entrée connue : {e.sources.date_entree||'À compléter'}</p>
      {!!e.variables.length&&<details className={s.donnees}><summary>{e.variables.length} variable(s) approuvée(s) conservée(s) dans le snapshot</summary><ul className={s.historique}>{e.variables.map(v=><li key={v.id}>Variable #{v.id} · {v.code} · {mad(v.montant)} · version de rubrique #{v.rubrique_version_id}</li>)}</ul><Link className={s.lien} to="/personnel-paie/elements/variables">Consulter les sources dans les variables</Link></details>}
    </article>)}
    <p className={s.discret}>Auteur #{detail.auteur_id} · Motif : {detail.motif||'Masqué selon vos habilitations'} · Empreinte SHA-256 du snapshot : {detail.empreinte}</p><p className={s.discret}>Un nouveau calcul conserve une nouvelle version ; les anciennes simulations restent consultables.</p>
  </section>
}
function Nouvelle({onFermer,onEnvoyer}){
  const [periode,setPeriode]=useState(moisCourant),[recherche,setRecherche]=useState(''),[texte,setTexte]=useState(''),[decalage,setDecalage]=useState(0),[selection,setSelection]=useState({}),[confirme,setConfirme]=useState(false),[motif,setMotif]=useState(''),[cle,setCle]=useState(()=>crypto.randomUUID()),[options,setOptions]=useState({data:null,erreur:'',chargement:true})
  const changer=()=>setCle(crypto.randomUUID())
  useEffect(()=>{if(!periode){setOptions({data:null,erreur:'',chargement:false});return}let vivant=true;setOptions({data:null,erreur:'',chargement:true});api.options({au:periode+'-01',recherche,decalage}).then(data=>{if(vivant)setOptions({data,erreur:'',chargement:false})}).catch(e=>{if(vivant)setOptions({data:null,erreur:e.message,chargement:false})});return()=>{vivant=false}},[periode,recherche,decalage])
  return <Formulaire titre="Calculer le brut du mois" onFermer={onFermer} libelle="Calculer" onEnvoyer={()=>{if(!Object.keys(selection).length)throw new Error('Sélectionnez au moins un salarié.');return onEnvoyer({periode:periode+'-01',employe_ids:Object.keys(selection).map(Number),mois_complets_confirmes:confirme,cle_idempotence:cle,motif})}}>
    <Champ label="Mois de la simulation"><input required type="month" value={periode} onChange={e=>{setPeriode(e.target.value);setSelection({});setDecalage(0);changer()}}/></Champ>
    <div className={s.recherche}><Champ label="Rechercher un salarié à simuler"><input maxLength={150} value={texte} onChange={e=>setTexte(e.target.value)}/></Champ><button type="button" className={s.secondaire} onClick={()=>{setRecherche(texte);setDecalage(0)}}>Rechercher les salariés</button></div>
    <Erreur message={options.erreur}/>{options.chargement&&<p role="status">Chargement des salariés…</p>}
    {options.data&&<><p className={s.discret}>Sélection : {Object.keys(selection).length} salarié(s), maximum50. Les anomalies individuelles resteront visibles ; aucun salarié incomplet ne sera remplacé par un montant nul.</p>
      {options.data.elements.map(e=><label key={e.id} className={s.coche}><input type="checkbox" checked={!!selection[e.id]} disabled={!selection[e.id]&&Object.keys(selection).length>=50} onChange={ev=>{const checked=ev.target.checked;setSelection(p=>{const n={...p};if(checked)n[e.id]=e.nom;else delete n[e.id];return n});changer()}}/>{e.matricule} · {e.nom} · Base : {e.remuneration?mad(e.remuneration.montant):'À compléter'}</label>)}
      <div className={s.actions}><button type="button" className={s.secondaire} disabled={!decalage} onClick={()=>setDecalage(Math.max(0,decalage-25))}>Salariés précédents</button><button type="button" className={s.secondaire} disabled={decalage+25>=options.data.total} onClick={()=>setDecalage(decalage+25)}>Salariés suivants</button><button type="button" className={s.secondaire} onClick={()=>{setSelection({});changer()}}>Vider la sélection</button></div>
    </>}
    <Champ label="Motif de la simulation"><textarea required maxLength={500} value={motif} onChange={e=>{setMotif(e.target.value);changer()}}/></Champ>
    <label className={s.coche}><input type="checkbox" required checked={confirme} onChange={e=>{setConfirme(e.target.checked);changer()}}/>Je confirme que la sélection concerne des mois complets et que les variables de ce mois ont été préparées.</label>
    <p className={s.notice}>Calcul sur mois complet : salaire mensuel et primes approuvées. Une entrée ou une sortie en cours de mois, un changement de salaire ou une variable non approuvée sont signalés comme anomalie.</p>
  </Formulaire>
}
