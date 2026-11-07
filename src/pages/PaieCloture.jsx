import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePersonnelAcces } from '../data/PersonnelAccesContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { useEcritures } from '../data/EcrituresContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { paieBulletinsAPI as api, paieIRMensuelAPI } from '../services/api.js'
import { notifier } from '../services/notifications.js'
import { Champ, Erreur, Formulaire } from '../components/PaieVariables.jsx'
import PaieAccesRequis,{accesPaieManquant} from '../components/PaieAccesRequis.jsx'
import EtatVide from '../components/EtatVide.jsx'
import s from './Personnel.module.css'
import { mad, moisLibelle } from '../utils/formatPaie.js'

// Lot 968 : bulletins, avances & prêts, paiements, comptabilisation et états de paie.
const mois = p => String(p || '').slice(0, 7)
const aujourdhui = () => new Date().toISOString().slice(0, 10)
const finDeMois = p => { const [a, m] = mois(p).split('-').map(Number); return new Date(Date.UTC(a, m, 0)).toISOString().slice(0, 10) }
const SECTIONS = {
  bulletins: { titre: 'Bulletins de paie', sous: 'Net à payer et bulletin figé par salarié et par mois' },
  avances: { titre: 'Avances & prêts', sous: 'Registre des avances et prêts au personnel, retenues sur bulletins' },
  paiements: { titre: 'Paiements', sous: 'Versement des nets et organismes à régler' },
  comptabilisation: { titre: 'Comptabilisation', sous: 'Écriture de paie mensuelle au journal des salaires' },
  etats: { titre: 'États & reporting', sous: 'Livre de paie et récapitulatifs annuels' },
}

function useRechargement() {
  const [revision, setRevision] = useState(0)
  return [revision, () => setRevision(v => v + 1)]
}

function useDonnees(charger, deps) {
  const [etat, setEtat] = useState({ data: null, erreur: '', chargement: true })
  useEffect(() => {
    let actif = true
    setEtat(e => ({ ...e, erreur: '', chargement: true }))
    charger().then(data => { if (actif) setEtat({ data, erreur: '', chargement: false }) })
      .catch(e => { if (actif) setEtat({ data: null, erreur: e.message, chargement: false }) })
    return () => { actif = false }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps
  return etat
}

export default function PaieCloture({ section = 'bulletins' }) {
  const ctx = usePersonnelAcces(), { societe, aGRH } = useModules(), cap = k => ctx.acces?.capacites.includes('personnel.' + k)
  const info = SECTIONS[section]
  let contenu
  if (ctx.chargement) contenu = <p role="status">Chargement des accès…</p>
  else if (ctx.erreur) contenu = <Erreur message={ctx.erreur} />
  else if(accesPaieManquant(ctx,aGRH))contenu=<PaieAccesRequis ctx={ctx}/>
  else {
    const props = { peutEcrire: cap('proposer') && ['admin', 'comptable', 'personnel'].includes(ctx.user?.role), comptable: ['admin', 'comptable'].includes(ctx.user?.role) }
    const Vue = { bulletins: Bulletins, avances: Avances, paiements: Paiements, comptabilisation: Comptabilisation, etats: Etats }[section]
    contenu = <Vue key={`${societe?.id}:${ctx.version}`} {...props} />
  }
  return <div className={s.page} data-form-page>
    <header className={s.entete}><div><h1>{info.titre}</h1><p>{societe?.raison_sociale} · {info.sous}</p></div>
      <button className={s.secondaire} onClick={ctx.recharger} disabled={ctx.chargement}>Actualiser</button></header>
    <div className={s.contenu}>{contenu}</div>
  </div>
}

// ── Bulletins ─────────────────────────────────────────────────────────────
function Bulletins({ peutEcrire }) {
  const [revision, recharger] = useRechargement()
  const [annee, setAnnee] = useState(new Date().getFullYear())
  const liste = useDonnees(() => api.lister({ annee }), [annee, revision])
  const [form, setForm] = useState(false), [detail, setDetail] = useState(null), [erreur, setErreur] = useState('')
  const ouvrir = async id => { setErreur(''); try { setDetail(await api.lire(id)) } catch (e) { setErreur(e.message) } }
  const annuler = async b => {
    const motif = window.prompt(`Annuler le bulletin ${mois(b.periode)} de ${b.nom} (net ${mad(b.net_a_payer)}) ? Indiquez le motif :`)
    if (!motif) return
    try { await api.annuler(b.id, { motif }); notifier.succes('Bulletin annulé.'); setDetail(null); recharger() } catch (e) { notifier.erreur(e.message) }
  }
  return <>
    <p className={s.notice}>Un bulletin validé est figé : pour le corriger, annulez-le puis établissez-le de nouveau. Vérifiez vos taux de cotisation avant de le remettre au salarié.</p>
    <div className={s.actions}>
      {peutEcrire && <button className={s.primaire} onClick={() => setForm(true)}>Établir un bulletin</button>}
      <Champ label="Année"><input type="number" min="2000" max="2100" value={annee} onChange={e => setAnnee(Number(e.target.value) || annee)} style={{ width: 110 }} /></Champ>
    </div>
    <Erreur message={liste.erreur || erreur} />
    {liste.chargement && <p role="status">Chargement des bulletins…</p>}
    {liste.data && <TableBulletins elements={liste.data.elements} ouvrir={ouvrir} annuler={peutEcrire ? annuler : null} />}
    {detail && <Bulletin b={detail} fermer={() => setDetail(null)} />}
    {form && <NouveauBulletin fermer={() => setForm(false)} cree={b => { setForm(false); recharger(); notifier.succes(`Bulletin établi : net à payer ${mad(b.contenu.net_a_payer)}.`); ouvrir(b.id) }} />}
  </>
}

function statutBulletin(b) {
  if (b.statut === 'ANNULE') return 'Annulé'
  if (b.paiement_date) return b.paiement_valide ? 'Payé' : 'Paiement en brouillon'
  if (b.ecriture_id) return b.ecriture_validee ? 'Comptabilisé' : 'Écriture en brouillon'
  return 'Validé'
}

function TableBulletins({ elements, ouvrir, annuler, selection, basculer }) {
  if (!elements.length) return <EtatVide icone="ti-file-invoice" titre="Aucun bulletin" lien="/personnel-paie/paie-du-mois" libelleLien="Voir les étapes de la paie du mois">Les bulletins s’établissent une fois le brut, les cotisations et l’IR du mois calculés.</EtatVide>
  return <div className={s.tableau}><table aria-label="Bulletins de paie"><thead><tr>
    {basculer && <th><span className="sr-only">Sélection</span></th>}
    <th>Mois</th><th>Salarié</th><th>Brut</th><th>Cotisations salariales</th><th>IR retenu</th><th>Avances</th><th>Net à payer</th><th>Statut</th><th>Actions</th>
  </tr></thead><tbody>{elements.map(b => <tr key={b.id}>
    {basculer && <td><input type="checkbox" aria-label={`Sélectionner ${b.nom} ${mois(b.periode)}`} checked={!!selection[b.id]} onChange={() => basculer(b.id)} /></td>}
    <td>{moisLibelle(b.periode)}</td><td>{b.nom}<small>{b.matricule}</small></td><td>{mad(b.brut)}</td><td>{mad(b.cotisations_salariales)}</td>
    <td>{mad(b.ir_retenu)}</td><td>{mad(b.total_avances)}</td><td><strong>{mad(b.net_a_payer)}</strong></td><td>{statutBulletin(b)}</td>
    <td><div className={s.actions}>
      {ouvrir && <button className={s.secondaire} onClick={() => ouvrir(b.id)}>Voir le bulletin</button>}
      {annuler && b.statut === 'VALIDE' && !b.ecriture_id && !b.paiement_date && <button className={s.secondaire} onClick={() => annuler(b)}>Annuler</button>}
    </div></td>
  </tr>)}</tbody></table></div>
}

function NouveauBulletin({ fermer, cree }) {
  const controles = useDonnees(() => paieIRMensuelAPI.lister(0), [])
  const [controle, setControle] = useState(''), [apercu, setApercu] = useState(null), [erreur, setErreur] = useState('')
  const [ir, setIr] = useState(''), [reference, setReference] = useState(''), [retenues, setRetenues] = useState({}), [motif, setMotif] = useState('')
  const [cle] = useState(() => crypto.randomUUID())
  useEffect(() => {
    if (!controle) { setApercu(null); return }
    let actif = true
    setErreur(''); setApercu(null)
    api.apercu(controle).then(a => {
      if (!actif) return
      setApercu(a); setIr(a.ir_propose)
      setRetenues(Object.fromEntries(a.avances.map(v => [v.id, v.retenue_mensuelle ? String(Math.min(Number(v.retenue_mensuelle), Number(v.solde)).toFixed(2)) : '0.00'])))
    }).catch(e => { if (actif) setErreur(e.message) })
    return () => { actif = false }
  }, [controle])
  const totalAvances = Object.values(retenues).reduce((t, v) => t + (Number(v) || 0), 0)
  const net = apercu ? Number(apercu.brut) - Number(apercu.cotisations_salariales) - (Number(ir) || 0) - totalAvances : null
  const ecartIR = apercu && Number(ir) !== Number(apercu.ir_propose)
  return <Formulaire titre="Établir un bulletin de paie" libelle="Valider le bulletin" onFermer={fermer} onEnvoyer={async () => {
    if (!apercu) throw new Error('Choisissez un contrôle IR mensuel.')
    if (apercu.deja_etabli) throw new Error('Un bulletin valide existe déjà pour ce salarié et ce mois.')
    const b = await api.creer({ controle_id: Number(controle), ir_retenu: Number(ir || 0).toFixed(2), reference_ecart_ir: ecartIR ? reference || null : null,
      retenues_avances: Object.entries(retenues).filter(([, v]) => Number(v) > 0).map(([id, v]) => ({ avance_id: Number(id), montant: Number(v).toFixed(2) })),
      cle_idempotence: cle, motif })
    cree(b)
  }}>
    <Champ label="Contrôle IR mensuel (salarié et mois)">
      <select required value={controle} onChange={e => setControle(e.target.value)}>
        <option value="">Choisir…</option>
        {(controles.data?.elements || []).map(c => <option key={c.id} value={c.id} disabled={c.ir == null}>{mois(c.periode)} · {c.nom} ({c.matricule}) · contrôle #{c.id}{c.ir == null ? ' — incomplet' : ''}</option>)}
      </select>
    </Champ>
    {controles.data && !controles.data.elements.length && <p className={s.notice}>Aucun contrôle IR mensuel : préparez-le dans <Link className={s.lien} to="/personnel-paie/fiscalite?vue=mensuel">Fiscalité salariale → RNI mensuel</Link>.</p>}
    <Erreur message={controles.erreur || erreur} />
    {apercu && <>
      {apercu.deja_etabli && <p role="alert" className={s.erreur}>Bulletin #{apercu.deja_etabli} déjà établi pour ce mois : annulez-le d'abord pour le refaire.</p>}
      <div className={s.grille}>
        <div><h3>Brut</h3><p className={s.montant}>{mad(apercu.brut)}</p></div>
        <div><h3>Cotisations salariales</h3><p className={s.montant}>{mad(apercu.cotisations_salariales)}</p></div>
        <div><h3>Net à payer (estimé)</h3><p className={s.montant} data-testid="net-estime">{mad(net?.toFixed(2))}</p></div>
      </div>
      <Champ label="IR à retenir (MAD)"><input required inputMode="decimal" value={ir} onChange={e => setIr(e.target.value)} /></Champ>
      <p className={s.discret}>Calcul du contrôle mensuel : {apercu.ir_arithmetique} MAD, arrondi au centime : {apercu.ir_propose} MAD.</p>
      {ecartIR && <Champ label="Référence justifiant l'écart d'IR"><input required maxLength={300} value={reference} onChange={e => setReference(e.target.value)} /></Champ>}
      {apercu.avances.length > 0 && <fieldset className={s.carte}><legend>Retenues sur avances et prêts</legend>
        {apercu.avances.map(v => <Champ key={v.id} label={`${v.nature === 'PRET' ? 'Prêt' : 'Avance'} #${v.id} — reste ${mad(v.solde)}`}>
          <input inputMode="decimal" value={retenues[v.id] ?? ''} onChange={e => setRetenues(r => ({ ...r, [v.id]: e.target.value }))} />
        </Champ>)}
      </fieldset>}
    </>}
    <Champ label="Motif"><textarea required maxLength={500} value={motif} onChange={e => setMotif(e.target.value)} /></Champ>
  </Formulaire>
}

export function Bulletin({ b, fermer }) {
  const c = b.contenu, soc = b.societe || {}, sal = b.salarie || {}
  const imprimer = () => { document.body.classList.add('impression-bulletin'); window.print(); document.body.classList.remove('impression-bulletin') }
  return <section className={`${s.carte} bulletin-imprimable`} aria-label={`Bulletin ${c.nom} ${mois(c.periode)}`}>
    <div className={s.titreFiche}><div><h2>Bulletin de paie · {moisLibelle(c.periode)}</h2><p>{soc.raison_sociale || '—'} · IF {soc.identifiant_fiscal || '—'} · ICE {soc.ice || '—'} · CNSS {soc.cnss_societe || '—'}</p></div>
      <div className={`${s.actions} no-print`}><button className={s.secondaire} onClick={imprimer}>Imprimer</button><button className={s.secondaire} onClick={fermer}>Fermer</button></div></div>
    <p><strong>{c.nom}</strong> · Matricule {c.matricule} · {sal.poste || 'Poste —'} · CNSS {sal.numero_cnss || '—'} · Entrée {sal.date_embauche || '—'}</p>
    {b.statut === 'ANNULE' && <p role="alert" className={s.erreur}>Bulletin annulé : {b.motif_annulation}</p>}
    <div className={s.tableau}><table aria-label="Détail du bulletin"><thead><tr><th>Rubrique</th><th>Montant</th><th>Base</th><th>Part salariale</th><th>Part patronale</th></tr></thead><tbody>
      {c.gains.map((g, i) => <tr key={'g' + i}><td>{g.libelle}</td><td>{mad(g.montant)}</td><td></td><td></td><td></td></tr>)}
      <tr><td><strong>Salaire brut</strong></td><td><strong>{mad(c.brut)}</strong></td><td></td><td></td><td></td></tr>
      {c.cotisations.map(x => <tr key={x.code}><td>{x.code}</td><td>-{mad(x.salarial)}</td><td>{mad(x.assiette)}</td><td>{mad(x.salarial)}</td><td>{mad(x.patronal)}</td></tr>)}
      <tr><td>Total cotisations</td><td>-{mad(c.cotisations_salariales)}</td><td></td><td>{mad(c.cotisations_salariales)}</td><td>{mad(c.cotisations_patronales)}</td></tr>
      <tr><td>Revenu net imposable</td><td></td><td>{mad(c.rni)}</td><td></td><td></td></tr>
      <tr><td>IR retenu à la source{c.reference_ecart_ir ? ` (réf. ${c.reference_ecart_ir})` : ''}</td><td>-{mad(c.ir_retenu)}</td><td></td><td></td><td></td></tr>
      {c.retenues_avances.map(r => <tr key={r.avance_id}><td>Retenue avance/prêt #{r.avance_id}</td><td>-{mad(r.montant)}</td><td></td><td></td><td></td></tr>)}
      <tr><td><strong>Net à payer</strong></td><td><strong data-testid="net-bulletin">{mad(c.net_a_payer)}</strong></td><td></td><td></td><td></td></tr>
    </tbody></table></div>
    <p className={s.discret}>Coût employeur : {mad(c.cout_employeur)} · Bulletin #{b.id} · Empreinte {b.empreinte.slice(0, 16)}…</p>
    <p className={s.discret}>{c.avertissement}</p>
  </section>
}

// ── Avances & prêts ───────────────────────────────────────────────────────
function Avances({ peutEcrire, comptable }) {
  const [revision, recharger] = useRechargement()
  const liste = useDonnees(() => api.avances(), [revision])
  const [form, setForm] = useState(false)
  const ecrituresCtx = useEcritures()
  const action = async (fn, message) => { try { await fn(); notifier.succes(message); await ecrituresCtx?.recharger?.(); recharger() } catch (e) { notifier.erreur(e.message) } }
  return <>
    <p className={s.notice}>Les avances et prêts se remboursent par des retenues sur les bulletins de paie.</p>
    {peutEcrire && <div className={s.actions}><button className={s.primaire} onClick={() => setForm(true)}>Nouvelle avance ou prêt</button></div>}
    <Erreur message={liste.erreur} />{liste.chargement && <p role="status">Chargement des avances…</p>}
    {liste.data && (liste.data.elements.length ? <div className={s.tableau}><table aria-label="Avances et prêts"><thead><tr><th>Date</th><th>Salarié</th><th>Nature</th><th>Montant</th><th>Remboursé</th><th>Reste</th><th>Retenue mensuelle</th><th>Comptabilisation</th><th>Actions</th></tr></thead><tbody>
      {liste.data.elements.map(a => <tr key={a.id}>
        <td>{a.date_octroi}</td><td>{a.nom_employe}</td><td>{a.nature === 'PRET' ? 'Prêt' : 'Avance'}{a.statut === 'ANNULEE' && <small>Annulée : {a.motif_annulation}</small>}</td>
        <td>{mad(a.montant)}</td><td>{mad(a.rembourse)}</td><td><strong>{mad(a.solde)}</strong></td><td>{a.retenue_mensuelle ? mad(a.retenue_mensuelle) : '—'}</td>
        <td>{a.ecriture_id ? (a.ecriture_validee ? 'Validée' : 'Brouillon au Journal') : 'Non comptabilisée'}</td>
        <td><div className={s.actions}>
          {comptable && a.statut === 'ACTIVE' && !a.ecriture_id && <button className={s.secondaire} onClick={() => action(() => api.comptabiliserAvance(a.id), 'Versement comptabilisé en brouillon.')}>Comptabiliser le versement</button>}
          {peutEcrire && a.statut === 'ACTIVE' && !a.ecriture_id && Number(a.rembourse) === 0 && <button className={s.secondaire} onClick={() => { const motif = window.prompt(`Annuler ${a.nature === 'PRET' ? 'le prêt' : "l'avance"} de ${mad(a.montant)} accordé(e) à ${a.nom_employe} ? Motif :`); if (motif) action(() => api.annulerAvance(a.id, { motif }), 'Avance annulée.') }}>Annuler</button>}
        </div></td>
      </tr>)}</tbody></table></div> : <EtatVide icone="ti-coins" titre="Aucune avance ni prêt" action={peutEcrire?'Accorder une avance':null} onAction={()=>setForm(true)}>Enregistrez les avances sur salaire et les prêts accordés : ils se remboursent ensuite par des retenues sur les bulletins.</EtatVide>)}
    {form && <NouvelleAvance fermer={() => setForm(false)} cree={() => { setForm(false); notifier.succes('Avance enregistrée.'); recharger() }} />}
  </>
}

function NouvelleAvance({ fermer, cree }) {
  const salaries = useDonnees(() => api.salaries(), [])
  const [d, setD] = useState({ employe_id: '', nature: 'AVANCE', date_octroi: aujourdhui(), montant: '', retenue_mensuelle: '', mode_versement: 'virement', motif: '' })
  const maj = k => e => setD(v => ({ ...v, [k]: e.target.value }))
  return <Formulaire titre="Nouvelle avance ou prêt" libelle="Enregistrer" onFermer={fermer} onEnvoyer={async () => {
    await api.creerAvance({ ...d, employe_id: Number(d.employe_id), montant: Number(d.montant).toFixed(2), retenue_mensuelle: d.retenue_mensuelle ? Number(d.retenue_mensuelle).toFixed(2) : null })
    cree()
  }}>
    <Erreur message={salaries.erreur} />
    <div className={s.grille}>
      <Champ label="Salarié"><select required value={d.employe_id} onChange={maj('employe_id')}><option value="">Choisir…</option>{(salaries.data || []).map(e => <option key={e.id} value={e.id}>{e.nom}{e.matricule ? ` (${e.matricule})` : ''}</option>)}</select></Champ>
      <Champ label="Nature"><select value={d.nature} onChange={maj('nature')}><option value="AVANCE">Avance sur salaire</option><option value="PRET">Prêt</option></select></Champ>
      <Champ label="Date de versement"><input required type="date" value={d.date_octroi} onChange={maj('date_octroi')} /></Champ>
      <Champ label="Montant (MAD)"><input required inputMode="decimal" value={d.montant} onChange={maj('montant')} /></Champ>
      <Champ label="Retenue mensuelle prévue (MAD)"><input inputMode="decimal" value={d.retenue_mensuelle} onChange={maj('retenue_mensuelle')} /></Champ>
      <Champ label="Mode de versement"><select value={d.mode_versement} onChange={maj('mode_versement')}><option value="virement">Virement</option><option value="cheque">Chèque</option><option value="especes">Espèces</option></select></Champ>
    </div>
    <Champ label="Motif"><textarea required maxLength={500} value={d.motif} onChange={maj('motif')} /></Champ>
  </Formulaire>
}

// ── Paiements ─────────────────────────────────────────────────────────────
function Paiements({ comptable }) {
  const [revision, recharger] = useRechargement()
  const liste = useDonnees(() => api.lister({}), [revision])
  const [selection, setSelection] = useState({}), [date, setDate] = useState(aujourdhui()), [mode, setMode] = useState('virement'), [reference, setReference] = useState(''), [occupe, setOccupe] = useState(false)
  const ecrituresCtx = useEcritures()
  const aPayer = (liste.data?.elements || []).filter(b => b.statut === 'VALIDE' && !b.paiement_date)
  const choisis = aPayer.filter(b => selection[b.id]), total = choisis.reduce((t, b) => t + Number(b.net_a_payer), 0)
  const payer = async () => {
    if (!choisis.length) return
    if (!window.confirm(`Enregistrer le paiement de ${choisis.length} bulletin(s) pour ${mad(total.toFixed(2))} par ${mode} le ${date} ?`)) return
    setOccupe(true)
    try {
      const r = await api.payer({ bulletin_ids: choisis.map(b => b.id), date_paiement: date, mode, reference: reference || null })
      notifier.succes(`Paiement enregistré en brouillon au Journal (${mad(r.total)}).`); setSelection({}); await ecrituresCtx?.recharger?.(); recharger()
    } catch (e) { notifier.erreur(e.message) } finally { setOccupe(false) }
  }
  return <>
    <p className={s.notice}>Sélectionnez les salariés à payer : HisabPro prépare l’écriture de virement, à valider dans le Journal. CNSS et IR se règlent depuis le Journal après vos déclarations Damancom et SIMPL.</p>
    <Erreur message={liste.erreur} />{liste.chargement && <p role="status">Chargement des bulletins…</p>}
    {liste.data && <>
      <h2>Nets à payer</h2>
      <TableBulletins elements={aPayer} selection={selection} basculer={comptable ? id => setSelection(v => ({ ...v, [id]: !v[id] })) : null} />
      {comptable && aPayer.length > 0 && <div className={s.actions}>
        <Champ label="Date de paiement"><input type="date" value={date} onChange={e => setDate(e.target.value)} /></Champ>
        <Champ label="Mode"><select value={mode} onChange={e => setMode(e.target.value)}><option value="virement">Virement</option><option value="cheque">Chèque</option><option value="especes">Espèces</option></select></Champ>
        <Champ label="Référence (ordre de virement…)"><input maxLength={100} value={reference} onChange={e => setReference(e.target.value)} /></Champ>
        <button className={s.primaire} disabled={!choisis.length || occupe} onClick={payer}>Payer la sélection ({mad(total.toFixed(2))})</button>
      </div>}
      {(liste.data.elements || []).some(b => b.paiement_date) && <>
        <h2>Bulletins payés</h2>
        <TableBulletins elements={(liste.data.elements || []).filter(b => b.paiement_date)} />
      </>}
    </>}
  </>
}

// ── Comptabilisation ──────────────────────────────────────────────────────
function Comptabilisation({ comptable }) {
  const [revision, recharger] = useRechargement()
  const liste = useDonnees(() => api.lister({}), [revision])
  const ecrituresCtx = useEcritures()
  const [occupe, setOccupe] = useState('')
  const parMois = {}
  for (const b of (liste.data?.elements || []).filter(x => x.statut === 'VALIDE')) {
    const m = parMois[mois(b.periode)] ||= { periode: b.periode, bulletins: [], brut: 0, net: 0 }
    m.bulletins.push(b); m.brut += Number(b.brut); m.net += Number(b.net_a_payer)
  }
  const comptabiliser = async m => {
    const restants = m.bulletins.filter(b => !b.ecriture_id)
    if (!window.confirm(`Comptabiliser ${restants.length} bulletin(s) de ${mois(m.periode)} au journal des salaires, à la date du ${finDeMois(m.periode)} ?`)) return
    setOccupe(mois(m.periode))
    try {
      const r = await api.comptabiliser({ periode: m.periode, date_ecriture: finDeMois(m.periode) })
      notifier.succes(`Écriture de paie créée en brouillon (net ${mad(r.totaux.net)}). Validez-la dans le Journal.`); await ecrituresCtx?.recharger?.(); recharger()
    } catch (e) { notifier.erreur(e.message) } finally { setOccupe('') }
  }
  const lignes = Object.values(parMois).sort((a, b) => String(b.periode).localeCompare(String(a.periode)))
  return <>
    <p className={s.notice}>Une écriture par mois au journal des salaires (SA), créée en brouillon : brut et charges patronales au débit ; CNSS/AMO, IR, retenues d’avances et nets à payer au crédit.</p>
    <Erreur message={liste.erreur} />{liste.chargement && <p role="status">Chargement…</p>}
    {liste.data && (lignes.length ? <div className={s.tableau}><table aria-label="Comptabilisation par mois"><thead><tr><th>Mois</th><th>Bulletins</th><th>Brut</th><th>Net</th><th>État</th><th>Action</th></tr></thead><tbody>
      {lignes.map(m => {
        const restants = m.bulletins.filter(b => !b.ecriture_id).length, ecrits = [...new Set(m.bulletins.filter(b => b.ecriture_id).map(b => b.numero_ecriture || `brouillon #${b.ecriture_id}`))]
        return <tr key={mois(m.periode)}><td>{mois(m.periode)}</td><td>{m.bulletins.length}</td><td>{mad(m.brut.toFixed(2))}</td><td>{mad(m.net.toFixed(2))}</td>
          <td>{restants ? `${restants} à comptabiliser` : 'Comptabilisé'}{ecrits.length > 0 && <small>Écriture(s) : {ecrits.join(', ')}</small>}</td>
          <td>{comptable && restants > 0 ? <button className={s.primaire} disabled={!!occupe} onClick={() => comptabiliser(m)}>Comptabiliser {mois(m.periode)}</button> : restants > 0 ? 'Réservé admin/comptable' : <Link className={s.lien} to="/journal">Voir le Journal</Link>}</td></tr>
      })}</tbody></table></div> : <EtatVide icone="ti-book" titre="Rien à comptabiliser" lien="/personnel-paie/bulletins" libelleLien="Établir les bulletins">L’écriture de paie du mois se passe une fois les bulletins établis.</EtatVide>)}
  </>
}

// ── États ─────────────────────────────────────────────────────────────────
function Etats() {
  const { annee: anneeExercice } = useExercice() || {}
  const [annee, setAnnee] = useState(anneeExercice || new Date().getFullYear())
  const etat = useDonnees(() => api.etats(annee), [annee])
  const exporter = () => {
    const d = etat.data, sep = ';', n = v => String(v ?? '').replace('.', ',')
    const lignes = [['Mois', 'Matricule', 'Salarié', 'Brut', 'Cotisations salariales', 'Cotisations patronales', 'IR retenu', 'Retenues avances', 'Net à payer', 'Coût employeur'].join(sep),
      ...d.bulletins.map(b => [mois(b.periode), b.matricule, `"${String(b.nom).replace(/"/g, '""')}"`, n(b.brut), n(b.cotisations_salariales), n(b.cotisations_patronales), n(b.ir_retenu), n(b.total_avances), n(b.net_a_payer), n(b.cout_employeur)].join(sep))]
    const url = URL.createObjectURL(new Blob(['﻿' + lignes.join('\r\n')], { type: 'text/csv;charset=utf-8' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: `livre_de_paie_${annee}.csv` }); a.click(); URL.revokeObjectURL(url)
  }
  const d = etat.data
  return <>
    <div className={s.actions}>
      <Champ label="Année"><input type="number" min="2000" max="2100" value={annee} onChange={e => setAnnee(Number(e.target.value) || annee)} style={{ width: 110 }} /></Champ>
      <button className={s.secondaire} disabled={!d?.bulletins.length} onClick={exporter}>Exporter le livre de paie (CSV)</button>
    </div>
    <Erreur message={etat.erreur} />{etat.chargement && <p role="status">Chargement des états…</p>}
    {d && <>
      <section className={s.carte} aria-label="Récapitulatif annuel"><h2>Récapitulatif {annee}</h2><div className={s.tableau}><table aria-label="Récapitulatif mensuel de la paie"><thead><tr>
        <th>Mois</th><th>Bulletins</th><th>Brut</th><th>CNSS/AMO à verser</th><th>IR à verser</th><th>Retenues avances</th><th>Nets</th><th>Coût employeur</th><th>Suivi</th></tr></thead><tbody>
        {d.mois.map(m => <tr key={m.periode}><td>{m.periode}</td><td>{m.bulletins}</td><td>{mad(m.brut)}</td><td>{mad(m.organismes_sociaux)}</td><td>{mad(m.ir_retenu)}</td><td>{mad(m.total_avances)}</td><td>{mad(m.net_a_payer)}</td><td>{mad(m.cout_employeur)}</td><td>{m.comptabilises}/{m.bulletins} comptabilisés · {m.payes}/{m.bulletins} payés</td></tr>)}
        {d.mois.length > 0 && <tr><td><strong>Total</strong></td><td></td><td><strong>{mad(d.totaux.brut)}</strong></td><td><strong>{mad(d.totaux.organismes_sociaux)}</strong></td><td><strong>{mad(d.totaux.ir_retenu)}</strong></td><td><strong>{mad(d.totaux.total_avances)}</strong></td><td><strong>{mad(d.totaux.net_a_payer)}</strong></td><td><strong>{mad(d.totaux.cout_employeur)}</strong></td><td></td></tr>}
      </tbody></table></div>{!d.mois.length && <EtatVide icone="ti-report" titre={`Aucune paie en ${annee}`}>Le livre de paie et les récapitulatifs CNSS / IR apparaissent dès le premier bulletin de l’année.</EtatVide>}<p className={s.discret}>{d.note}</p></section>
      {d.bulletins.length > 0 && <section className={s.carte} aria-label="Livre de paie"><h2>Livre de paie {annee}</h2><TableBulletins elements={d.bulletins} /></section>}
    </>}
  </>
}
