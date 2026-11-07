import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePersonnelAcces } from '../data/PersonnelAccesContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { personnelAPI, paieCatalogueAPI, paieSocialAPI, paieVariablesAPI, paieCampagnesAPI, paieSocialCalculAPI,
  paieBasesFiscalesAPI, paieIRMensuelAPI, paieBulletinsAPI } from '../services/api.js'
import PaieAccesRequis, { accesPaieManquant } from '../components/PaieAccesRequis.jsx'
import { Erreur } from '../components/PaieVariables.jsx'
import { pluriel, mad, moisLibelle } from '../utils/formatPaie.js'
import { notifier } from '../services/notifications.js'
import s from './Personnel.module.css'

// Page d'entrée de la paie : les étapes du mois dans l'ordre, leur état et le
// bouton qui ouvre le bon écran. Aucune donnée n'est calculée ici.
const moisCourant = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}` }
const sur = p => p.catch(() => null)
const ETATS = {
  fait: { libelle: 'Fait', icone: 'ti-circle-check', couleur: 'var(--green)' },
  encours: { libelle: 'En cours', icone: 'ti-progress', couleur: 'var(--blue)' },
  afaire: { libelle: 'À faire', icone: 'ti-circle-dashed', couleur: 'var(--amber)' },
  attente: { libelle: 'Après l’étape précédente', icone: 'ti-lock', couleur: 'var(--text-tertiary)' },
}

async function chargerEtat(mois) {
  const periode = mois + '-01'
  const [salaries, rubriques, branches, attente, soumises, campagnes, sociales, preparations, controles, bulletins] = await Promise.all([
    sur(personnelAPI.lister({ au: periode, statut: 'ACTIF', decalage: 0 })),
    sur(paieCatalogueAPI.lister({ au: periode })),
    sur(paieSocialAPI.lister({ au: periode })),
    sur(paieVariablesAPI.lister({ periode, statut: 'BROUILLON' })),
    sur(paieVariablesAPI.lister({ periode, statut: 'SOUMIS' })),
    sur(paieCampagnesAPI.lister(0)),
    sur(paieSocialCalculAPI.lister(0)),
    sur(paieBasesFiscalesAPI.lister(0)),
    sur(paieIRMensuelAPI.lister(0)),
    sur(paieBulletinsAPI.lister({ periode })),
  ])
  const campagne = (campagnes?.elements || []).find(c => String(c.periode).slice(0, 7) === mois)
  const brutId = campagne?.derniere_simulation_id
  const sociale = (sociales?.elements || []).find(x => x.brut_id === brutId)
  const preparation = sociale && (preparations?.elements || []).find(x => x.social_id === sociale.id)
  const ctrl = (controles?.elements || []).filter(x => String(x.periode).slice(0, 7) === mois)
  const ctrlComplets = new Set(ctrl.filter(x => x.ir != null).map(x => x.matricule)).size
  const valides = (bulletins?.elements || []).filter(b => b.statut === 'VALIDE')
  return {
    salaries: salaries?.total ?? 0, rubriques: rubriques?.total ?? 0, branches: branches?.total ?? 0,
    variablesEnAttente: (attente?.total ?? 0) + (soumises?.total ?? 0),
    campagne, sociale, preparation, nbSalariesBrut: campagne?.nombre_salaries ?? 0, ctrlComplets,
    bulletins: valides.length, comptabilises: valides.filter(b => b.ecriture_id).length, payes: valides.filter(b => b.paiement_date).length,
  }
}

function etapes(e) {
  const brutOk = e.campagne && e.campagne.complet_pour_brut
  const socialOk = e.sociale && String(e.sociale.complet) === 'true'
  const basesOk = e.preparation && String(e.preparation.complet) === 'true'
  const n = e.nbSalariesBrut
  const irOk = basesOk && n > 0 && e.ctrlComplets >= n
  const bulletinsOk = n > 0 && e.bulletins >= n
  return [
    { titre: 'Salariés', detail: e.salaries ? `${pluriel(e.salaries, 'salarié actif', 'salariés actifs')} ce mois-ci.` : 'Créez vos salariés avec leur contrat et leur salaire.',
      etat: e.salaries ? 'fait' : 'afaire', lien: '/personnel-paie/personnel', action: e.salaries ? 'Voir les salariés' : 'Créer un salarié' },
    { titre: 'Paramètres de paie', detail: e.rubriques || e.branches ? `${pluriel(e.rubriques, 'rubrique')} de paie · ${pluriel(e.branches, 'cotisation sociale', 'cotisations sociales')} (taux CNSS, AMO…).` : 'Paramétrez vos cotisations (taux CNSS, AMO…) et, si besoin, vos primes.',
      etat: e.branches ? 'fait' : 'afaire', lien: e.branches ? '/personnel-paie/elements' : '/personnel-paie/charges-sociales',
      action: e.branches ? 'Voir les rubriques' : 'Paramétrer les cotisations' },
    { titre: 'Primes et variables du mois', detail: e.variablesEnAttente ? `${pluriel(e.variablesEnAttente, 'variable')} à soumettre ou à approuver.` : 'Primes, heures supplémentaires… du mois (facultatif).',
      etat: !e.salaries ? 'attente' : e.variablesEnAttente ? 'encours' : 'fait', lien: '/personnel-paie/elements/variables', action: 'Saisir les variables' },
    { titre: 'Calcul du brut', detail: e.campagne ? (brutOk ? `Brut calculé pour ${pluriel(n, 'salarié')}.` : 'Calcul fait mais incomplet : ouvrez-le pour voir les anomalies.') : 'Calculez le salaire brut du mois.',
      etat: brutOk ? 'fait' : e.campagne ? 'encours' : 'afaire', lien: '/personnel-paie/traitement', action: e.campagne ? 'Ouvrir le calcul' : 'Calculer le brut', vu: 'Voir le calcul' },
    { titre: 'Cotisations sociales', detail: socialOk ? 'Cotisations salariales et patronales calculées.' : 'Calculez les cotisations à partir du brut.',
      etat: !brutOk ? 'attente' : socialOk ? 'fait' : e.sociale ? 'encours' : 'afaire',
      lien: `/personnel-paie/charges-sociales/simulations${!socialOk && e.campagne?.derniere_simulation_id ? `?brut_id=${e.campagne.derniere_simulation_id}` : ''}`, action: 'Calculer les cotisations', vu: 'Voir les cotisations' },
    { titre: 'Bases fiscales', detail: basesOk ? 'Salaire imposable préparé.' : 'Préparez le salaire imposable à partir des cotisations.',
      etat: !socialOk ? 'attente' : basesOk ? 'fait' : e.preparation ? 'encours' : 'afaire',
      lien: e.preparation ? `/personnel-paie/fiscalite?vue=bases&preparation_fiscale_id=${e.preparation.id}` : `/personnel-paie/fiscalite${e.sociale ? `?social_id=${e.sociale.id}` : '?vue=bases'}`,
      action: e.preparation ? 'Ouvrir les bases' : 'Préparer les bases' },
    { titre: 'Impôt sur le revenu (IR)', detail: basesOk ? `IR calculé : ${e.ctrlComplets} salarié sur ${n}. Ouvrez les bases fiscales puis « Préparer le RNI mensuel » pour chacun.` : 'Calculez l’IR de chaque salarié.',
      etat: !basesOk ? 'attente' : irOk ? 'fait' : e.ctrlComplets ? 'encours' : 'afaire',
      lien: e.preparation ? `/personnel-paie/fiscalite?vue=bases&preparation_fiscale_id=${e.preparation.id}` : '/personnel-paie/fiscalite?vue=mensuel', action: 'Calculer l’IR', vu: 'Voir l’IR' },
    { titre: 'Bulletins de paie', detail: n ? `Bulletins établis : ${e.bulletins} sur ${n}.` : 'Établissez un bulletin par salarié.',
      etat: !e.ctrlComplets ? 'attente' : bulletinsOk ? 'fait' : e.bulletins ? 'encours' : 'afaire', lien: '/personnel-paie/bulletins', action: 'Établir les bulletins', vu: 'Voir les bulletins' },
    { titre: 'Comptabilisation', detail: e.bulletins ? `Bulletins comptabilisés : ${e.comptabilises} sur ${e.bulletins}.` : 'Passez l’écriture de paie du mois.',
      etat: !e.bulletins ? 'attente' : e.comptabilises >= e.bulletins ? 'fait' : 'afaire', lien: '/personnel-paie/comptabilisation', action: 'Comptabiliser', vu: 'Voir l’écriture' },
    { titre: 'Paiement des salaires', detail: e.bulletins ? `Salariés payés : ${e.payes} sur ${e.bulletins}.` : 'Payez les nets à payer.',
      etat: !e.comptabilises ? 'attente' : e.payes >= e.bulletins ? 'fait' : 'afaire', lien: '/personnel-paie/paiements', action: 'Payer', vu: 'Voir les paiements' },
  ]
}

export default function PaieDuMois() {
  const ctx = usePersonnelAcces(), { societe, aGRH } = useModules()
  const [mois, setMois] = useState(moisCourant), [etat, setEtat] = useState({ data: null, erreur: '', chargement: true })
  const [calcul, setCalcul] = useState({ occupe: false, resultat: null, erreur: '' }), [revision, setRevision] = useState(0)
  const peutCalculer = ctx.acces?.capacites?.includes('personnel.proposer')
  async function calculerMois() {
    if (!window.confirm(`Calculer la paie de ${moisLibelle(mois)} pour tous les salariés actifs ?

Hypothèses :
• salaire de base soumis à 100 % CNSS/AMO et imposable à 100 % (primes selon leur rubrique) ;
• frais professionnels : CGI 2026 art. 59-I-A (35 % ou 25 %), plafond 2 916,66 DH par mois ;
• personnes à charge : fiche de chaque salarié.

Les bulletins sont établis ; vous pourrez les annuler et les refaire.`)) return
    setCalcul({ occupe: true, resultat: null, erreur: '' })
    try {
      const r = await paieBulletinsAPI.calculerMois({ periode: mois + '-01', hypotheses_confirmees: true })
      setCalcul({ occupe: false, resultat: r, erreur: '' }); setRevision(v => v + 1)
      if (r.etablis) notifier.succes(`${pluriel(r.etablis, 'bulletin établi', 'bulletins établis')} pour ${moisLibelle(mois)}.`)
      if (r.bloques) notifier.erreur(`${pluriel(r.bloques, 'salarié', 'salariés')} à compléter : voir le détail.`)
    } catch (e) { setCalcul({ occupe: false, resultat: null, erreur: e.message }) }
  }
  const pret = !ctx.chargement && !ctx.erreur && !accesPaieManquant(ctx, aGRH)
  useEffect(() => {
    if (!pret || !mois) return
    let actif = true
    setEtat(e => ({ ...e, chargement: true, erreur: '' }))
    chargerEtat(mois).then(data => { if (actif) setEtat({ data, erreur: '', chargement: false }) })
      .catch(e => { if (actif) setEtat({ data: null, erreur: e.message, chargement: false }) })
    return () => { actif = false }
  }, [mois, pret, ctx.version, revision])
  let contenu
  if (ctx.chargement) contenu = <p role="status">Chargement des accès…</p>
  else if (ctx.erreur) contenu = <Erreur message={ctx.erreur} />
  else if (!pret) contenu = <PaieAccesRequis ctx={ctx} />
  else {
    const liste = etat.data ? etapes(etat.data) : []
    const prochaine = liste.find(x => x.etat === 'afaire' || x.etat === 'encours')
    contenu = <>
      <div className={s.actions}>
        <label className={s.champ} style={{ maxWidth: 220 }}><span>Mois de paie</span>
          <input type="month" value={mois} onChange={e => setMois(e.target.value)} /></label>
        {peutCalculer && <button className={s.primaire} disabled={calcul.occupe} onClick={calculerMois}>{calcul.occupe ? 'Calcul en cours…' : 'Calculer la paie du mois'}</button>}
        {prochaine && <Link className={s.secondaire} to={prochaine.lien}>Étape suivante : {prochaine.titre}</Link>}
      </div>
      <Erreur message={etat.erreur || calcul.erreur} />
      {calcul.resultat && <section className={s.carte} aria-label="Résultat du calcul du mois"><h2>Paie de {moisLibelle(calcul.resultat.periode)} · régime {calcul.resultat.regime}</h2>
        <p className={s.discret}>Bulletins établis : {calcul.resultat.etablis} · déjà établis : {calcul.resultat.deja_etablis} · à compléter : {calcul.resultat.bloques}</p>
        <div className={s.tableau}><table aria-label="Bulletins du mois"><thead><tr><th>Salarié</th><th>Résultat</th><th>Net à payer</th></tr></thead><tbody>
          {calcul.resultat.salaries.map(x => <tr key={x.employe_id}><td>{x.nom}</td>
            <td>{x.statut === 'bloque' ? <span style={{ color: 'var(--red)' }}>À compléter : {x.raison}</span> : x.statut === 'etabli' ? 'Bulletin établi' : 'Déjà établi'}</td>
            <td>{x.net_a_payer ? <strong>{mad(x.net_a_payer)}</strong> : '—'}</td></tr>)}
        </tbody></table></div>
        <div className={s.actions}><Link className={s.lien} to="/personnel-paie/bulletins">Voir les bulletins</Link></div></section>}
      {etat.chargement && <p role="status">Chargement de la paie du mois…</p>}
      {etat.data && <ol aria-label="Étapes de la paie du mois" style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 10 }}>
        {liste.map((x, i) => {
          const e = ETATS[x.etat]
          return <li key={x.titre} className={s.carte} style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', padding: 14, opacity: x.etat === 'attente' ? 0.65 : 1 }}>
            <span aria-hidden="true" style={{ fontWeight: 650, color: 'var(--text-secondary)', minWidth: 22 }}>{i + 1}</span>
            <div style={{ flex: '1 1 260px', minWidth: 0 }}>
              <h2 style={{ fontSize: 14 }}>{x.titre}</h2>
              <p className={s.discret} style={{ marginTop: 2 }}>{x.detail}</p>
            </div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: e.couleur, minWidth: 120 }}>
              <i className={`ti ${e.icone}`} aria-hidden="true" />{e.libelle}</span>
            {x.etat === 'attente'
              ? <span className={s.discret} style={{ minWidth: 150 }}>—</span>
              : <Link className={x === prochaine ? s.primaire : s.secondaire} style={{ minWidth: 150 }} to={x.lien}>{x.etat === 'fait' && x.vu ? x.vu : x.action}</Link>}
          </li>
        })}
      </ol>}
    </>
  }
  return <div className={s.page} data-form-page>
    <header className={s.entete}><div><h1>Paie du mois</h1><p>{societe?.raison_sociale} · Toutes les étapes, dans l’ordre</p></div>
      <button className={s.secondaire} onClick={ctx.recharger} disabled={ctx.chargement}>Actualiser</button></header>
    <div className={s.contenu}>{contenu}</div>
  </div>
}
