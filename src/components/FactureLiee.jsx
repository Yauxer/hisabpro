import { useEffect, useRef, useState } from 'react'
import { useModules } from '../data/ModulesContext.jsx'
import { facturesLieesAPI, societesLieesAPI, getToken, peutEcrire } from '../services/api.js'
import { cleIdempotence } from '../utils/cleIdempotence.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './SocietesLiees.module.css'

export default function FactureLiee({ facture }) {
  const { societe } = useModules()
  return <Panneau key={`${societe?.id}|${facture.id}|${getToken()}`} facture={facture} societeId={societe?.id} />
}

function Panneau({ facture, societeId }) {
  const token = getToken(), vivant = useRef(true), sequence = useRef(0), faitsActuels = useRef('')
  const [ouvert, setOuvert] = useState(false), [attente, setAttente] = useState(false)
  const [suivi, setSuivi] = useState(null), [liste, setListe] = useState([]), [charge, setCharge] = useState(false)
  const [selection, setSelection] = useState(''), [cfg, setCfg] = useState(null)
  const [mappings, setMappings] = useState({}), [nature, setNature] = useState(''), [pct, setPct] = useState('')
  const [apercu, setApercu] = useState(null), [verifie, setVerifie] = useState(false), [cle, setCle] = useState(cleIdempotence)
  const [erreur, setErreur] = useState('')
  const signature = JSON.stringify([selection, mappings, nature, pct]); faitsActuels.current = signature
  const actuel = () => vivant.current && getToken() === token
  useEffect(() => { vivant.current = true; return () => { vivant.current = false; sequence.current += 1 } }, [])
  useEffect(() => { if (ouvert) charger() }, [ouvert])

  function invalider() { setApercu(null); setVerifie(false); setErreur(''); setCle(cleIdempotence()) }
  async function charger() {
    const n = ++sequence.current
    setAttente(true); setErreur(''); setSuivi(null); setListe([]); setCharge(false); setCfg(null); setSelection(''); invalider()
    try {
      const [s, ls] = await Promise.all([facturesLieesAPI.suivre(facture.id), societesLieesAPI.lister()])
      if (actuel() && n === sequence.current) {
        setSuivi(s); setListe(ls.filter(l => l.active && l.vendeur_id === societeId && l.client_id === facture.tiers_id)); setCharge(true)
      }
    } catch (e) { if (actuel() && n === sequence.current) setErreur(e.message) }
    finally { if (actuel() && n === sequence.current) setAttente(false) }
  }
  async function choisir(id) {
    const n = ++sequence.current
    setSelection(id); setCfg(null); setMappings({}); setNature(''); setPct(''); invalider()
    if (!id) return
    setAttente(true)
    try { const c = await facturesLieesAPI.options(id, facture.id); if (actuel() && n === sequence.current) setCfg(c) }
    catch (e) { if (actuel() && n === sequence.current) setErreur(e.message) }
    finally { if (actuel() && n === sequence.current) setAttente(false) }
  }
  const corps = () => ({ nature_tva_achat: nature, tva_deductible_pct: pct, lignes: cfg.source.lignes.map(l => ({ source_ligne_id: l.id, article_id: Number(mappings[l.id]) })) })
  async function verifier(e) {
    e.preventDefault(); const s = signature
    setAttente(true); setErreur(''); setApercu(null)
    try { const p = await facturesLieesAPI.apercu(selection, facture.id, corps()); if (actuel() && faitsActuels.current === s) setApercu({ ...p, signature: s }) }
    catch (e) { if (actuel() && faitsActuels.current === s) setErreur(e.message) }
    finally { if (actuel()) setAttente(false) }
  }
  async function creer() {
    const s = signature
    if (!apercu || apercu.signature !== s || !verifie) return
    setAttente(true); setErreur('')
    try {
      const r = await facturesLieesAPI.creer(selection, facture.id, { ...corps(), cle, empreinte: apercu.empreinte, correspondance_verifiee: verifie })
      if (actuel() && faitsActuels.current === s) { setSuivi(r); setApercu(null); setCfg(null); setVerifie(false) }
    } catch (e) { if (actuel() && faitsActuels.current === s) setErreur(e.message) }
    finally { if (actuel()) setAttente(false) }
  }
  const eligible = facture.type === 'vente' && facture.est_validee && !facture.est_proforma && facture.statut !== 'annulee'
  return <details className={styles.card} onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Correspondance entre sociétés</summary>
    {ouvert && <section aria-label="Correspondance entre sociétés">
      <p>Chaque société conserve sa validation, son Journal, ses règlements et ses avoirs.</p>
      <button type="button" disabled={attente} onClick={charger}>Actualiser la correspondance</button>
      {attente && <p role="status">Chargement…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {suivi && <>
        <p role="status">Achat lié #{suivi.facture_achat_id} · Référence fournisseur {suivi.achat.reference} · Exercice {suivi.achat.exercice}</p>
        <p>Vente : {suivi.vente.validee ? 'validée' : 'brouillon'}, {suivi.vente.comptabilisee ? 'comptabilisée' : 'à comptabiliser'}. Achat : {suivi.achat.validee ? 'validé' : 'brouillon à vérifier'}, {suivi.achat.comptabilisee ? 'comptabilisé' : 'à comptabiliser'}.</p>
        {!suivi.liaison_active && <p>Liaison retirée ; correspondance historique conservée.</p>}
        {suivi.ecarts.length > 0 && <div role="alert"><strong>Écarts à vérifier</strong><ul>{suivi.ecarts.map(x => <li key={x}>{x}</li>)}</ul></div>}
        {suivi.ecarts.length === 0 && <p>Aucun écart documentaire détecté entre les deux factures.</p>}
        <p>{suivi.note}</p>
        <p>Pour poursuivre, basculez vers la société acheteuse, sélectionnez l’exercice {suivi.achat.exercice} puis ouvrez sa facture dans Achats. Vérifiez-la avant validation et comptabilisation.</p>
      </>}
      {charge && !suivi && <>
        {!eligible && <p>Aucune correspondance enregistrée. Seule une vente validée et active permet de préparer un achat lié.</p>}
        {eligible && !peutEcrire() && <p>Consultation seule : aucune commande de création disponible.</p>}
        {eligible && peutEcrire() && <>
          <label>Liaison de vente<select aria-label="Liaison de vente" disabled={attente} value={selection} onChange={e => choisir(e.target.value)}>
            <option value="">Choisir l’acheteur associé</option>{liste.map(l => <option key={l.id} value={l.id}>{l.acheteur} · Fournisseur {l.fournisseur}</option>)}
          </select></label>
          {liste.length === 0 && <p>Aucune liaison active pour ce client. Configurez-la dans Paramètres → Sociétés liées.</p>}
        </>}
      </>}
      {cfg && !suivi && <form onSubmit={verifier}><fieldset disabled={attente}>
        <h3>Brouillon d’achat chez {cfg.acheteur.nom}</h3>
        <p>Date {cfg.source.date} · Exercice acheteur {cfg.acheteur.exercice} · Fournisseur {cfg.acheteur.fournisseur}</p>
        {cfg.source.lignes.map(l => <label key={l.id}>{l.description} · {l.quantite} × {montantDecimalExact(l.prix_unitaire)} MAD
          <select aria-label={`Article acheteur pour la ligne ${l.id}`} required value={mappings[l.id] || ''} onChange={e => { setMappings(m => ({ ...m, [l.id]: e.target.value })); invalider() }}>
            <option value="">Choisir l’article de l’acheteur</option>{cfg.articles.map(a => <option key={a.id} value={a.id}>{a.code} · {a.designation} · Compte {a.compte_achat}</option>)}
          </select>
        </label>)}
        <div className={styles.grille}>
          <label>Nature TVA de l’achat<select aria-label="Nature TVA de l’achat" required value={nature} onChange={e => { setNature(e.target.value); if (e.target.value === 'non_deductible') setPct('0'); invalider() }}>
            <option value="">Choisir explicitement</option><option value="charge">Charge</option><option value="non_deductible">TVA non déductible</option>
          </select></label>
          <label>TVA déductible propre à la facture (%)<input type="number" required min="0" max="100" step="0.01" value={pct} onChange={e => { setPct(e.target.value); invalider() }} /></label>
        </div>
        <p>Les comptes affichés suivent le paramétrage des articles et seront figés à la validation. Le prorata annuel de l’acheteur sera appliqué par sa comptabilité ordinaire.</p>
        <button type="submit">Vérifier le brouillon d’achat</button>
        {apercu?.signature === signature && <>
          <p>HT {montantDecimalExact(apercu.source.total_ht)} · TVA {montantDecimalExact(apercu.source.total_tva)} · TTC {montantDecimalExact(apercu.source.total_ttc)} MAD</p>
          <p>{apercu.note}</p>
          <label className={styles.confirmation}><input type="checkbox" checked={verifie} onChange={e => setVerifie(e.target.checked)} />J’ai vérifié la société acheteuse, les articles, les montants et la TVA.</label>
          <button type="button" disabled={!verifie} onClick={creer}>Créer le brouillon chez l’acheteur</button>
        </>}
      </fieldset></form>}
    </section>}
  </details>
}
