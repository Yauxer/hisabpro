import {Champ} from './PaieVariables.jsx'
import s from '../pages/Personnel.module.css'

const libelles={A_VERIFIER:'À vérifier',INCLUS:'Incluse dans la base des frais professionnels',EXCLUS:'Exclue de la base des frais professionnels',DEDUCTIBLE:'Déductible du revenu imposable',NON_DEDUCTIBLE:'Non déductible du revenu imposable'}
const titre=mode=>mode==='FRAIS'?'Frais professionnels':'Déductibilité IR'
const jour=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}

export function QualificationIRForm({valeur,onChange,mode}){
  const nom=titre(mode),options=mode==='FRAIS'?['A_VERIFIER','INCLUS','EXCLUS']:['A_VERIFIER','DEDUCTIBLE','NON_DEDUCTIBLE']
  const changer=(k,v)=>onChange({...valeur,[k]:v})
  return <section className={s.donnees}><h2>{nom}</h2><p className={s.discret}>{mode==='FRAIS'?'Qualification de la fraction imposable de cette rubrique pour la base des frais professionnels. Aucun pourcentage de déduction n’est appliqué ici.':'Qualification fiscale de la seule part salariale. Le calcul d’une cotisation sociale ne prouve pas sa déductibilité fiscale.'}</p>
    <label className={s.coche}><input type="checkbox" checked={!!valeur} onChange={e=>onChange(e.target.checked?{traitement:'A_VERIFIER',statut_reglementaire:'A_VERIFIER',conditions:''}:null)}/>Définir la qualification — {nom}</label>
    {valeur&&<div className={s.grille}><Champ label={`Traitement — ${nom}`}><select value={valeur.traitement} onChange={e=>changer('traitement',e.target.value)}>{options.map(k=><option key={k} value={k}>{libelles[k]}</option>)}</select></Champ>
      <Champ label={`Qualification — ${nom}`}><select value={valeur.statut_reglementaire} onChange={e=>changer('statut_reglementaire',e.target.value)}><option value="A_VERIFIER">À vérifier</option><option value="VALIDE">Validée après contrôle humain</option><option value="OBSOLETE">Obsolète</option></select></Champ>
      <Champ label={`Conditions — ${nom}`}><textarea required maxLength={2000} value={valeur.conditions} onChange={e=>changer('conditions',e.target.value)}/></Champ>
      {valeur.statut_reglementaire==='VALIDE'&&[['source_reference','Référence du justificatif'],['texte_reference','Texte'],['article','Article'],['url_source','URL officielle'],['empreinte_preuve','Empreinte SHA-256 de la preuve'],['date_consultation','Date de consultation']].map(([k,t])=><Champ key={k} label={`${t} — ${nom}`}><input required type={k==='url_source'?'url':k==='date_consultation'?'date':'text'} maxLength={k==='url_source'?2000:k==='empreinte_preuve'?64:k==='article'?150:300} {...(k==='date_consultation'?{max:jour()}:k==='empreinte_preuve'?{pattern:'[a-f0-9]{64}'}:{})} value={valeur[k]??''} onChange={e=>changer(k,e.target.value||null)}/></Champ>)}
    </div>}
    {!valeur&&<p className={s.discret}>Qualification non renseignée : aucune inclusion ou déduction présumée.</p>}
  </section>
}

export function QualificationIRResume({valeur,mode}){
  return <section className={s.donnees}><h3>{titre(mode)}</h3>{valeur?<><p>{libelles[valeur.traitement]} · {valeur.statut_reglementaire}</p><p className={s.discret}>{valeur.conditions}</p>{valeur.texte_reference&&<p className={s.discret}>{valeur.source_reference} · {valeur.texte_reference} · {valeur.article} · Consultation {valeur.date_consultation}</p>}{valeur.url_source&&<a className={s.lien} href={valeur.url_source} target="_blank" rel="noopener noreferrer">Source — {titre(mode)}</a>}{valeur.empreinte_preuve&&<p className={s.discret} style={{overflowWrap:'anywhere'}}>SHA-256 déclaré : {valeur.empreinte_preuve}</p>}</>:<p className={s.discret}>À vérifier — qualification non renseignée.</p>}</section>
}
