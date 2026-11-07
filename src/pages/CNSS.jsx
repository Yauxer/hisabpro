import { useEffect, useMemo, useRef, useState } from 'react'
import { useEmployes } from '../data/EmployesContext.jsx'
import { useModules } from '../data/ModulesContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import { formatMAD, formatDate } from '../data/donnees.js'
import { peutEcrire } from '../services/api.js'
import { FormSection, InlineNotice } from '../components/FormUX.jsx'
import { dateLocaleISO } from '../utils/formUtils.js'
import styles from './CNSS.module.css'
import AvancesSalaries from '../components/AvancesSalaries.jsx'
import { telechargerDocumentPDF } from '../services/documentsCommerciaux.js'

const MOIS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
const SITUATIONS = [['celiba', 'Célibataire'], ['marie', 'Marié(e)'], ['veuf', 'Veuf / Veuve'], ['divorce', 'Divorcé(e)']]
const VIDE = { nom: '', poste: '', matricule: '', numero_cnss: '', type_contrat: '', date_embauche: '', date_sortie: '', email: '', telephone: '', salaire_brut: '', situation_familiale: 'celiba', nb_enfants: 0, personnes_charge_ir: '', actif: true }
const montant = valeur => typeof valeur === 'number' && Number.isFinite(valeur) ? formatMAD(valeur) : '—'
const texte = item => typeof item === 'string' ? item : item?.message || item?.libelle || item?.description || item?.titre || item?.code || ''
const ABSENCES = { conge: 'Congé', absence: 'Absence', autre: 'Autre' }
const ETATS_ABSENCE = { demande: 'Demandée', approuve: 'Approuvée', refuse: 'Refusée', annule: 'Annulée' }

function Champ({ nom, label, form, setForm, type = 'text', required = false, children, ...props }) {
  const id = `paie-${nom}`
  return <div className={styles.formGroup}><label htmlFor={id}>{label}{required && ' *'}</label>
    {children ? <select id={id} value={form[nom] ?? ''} onChange={e => setForm(p => ({ ...p, [nom]: e.target.value }))} {...props}>{children}</select>
      : <input id={id} type={type} required={required} value={form[nom] ?? ''} onChange={e => setForm(p => ({ ...p, [nom]: e.target.value }))} {...props} />}</div>
}

function VersionDocumentaire({ version }) {
  return <article className={styles.proofVersion}>
    <h3>Version {version.version} · {version.created_at ? formatDate(version.created_at) : 'Date non renseignée'}</h3>
    <p>Régime : {version.regime || 'À renseigner'} · Auteur : {version.created_by ?? 'Non renseigné'}</p>
    <p className={styles.hash}>Empreinte capturée : {version.empreinte || 'Non renseignée'}</p>
    {version.commentaire && <p>{version.commentaire}</p>}
    {(version.sources || []).length === 0 ? <p>Aucune preuve documentaire consignée.</p> : <ul>{version.sources.map((source, i) => <li key={i}>
      <strong>{source.titre}</strong>{source.url && /^https?:\/\//.test(source.url) && <> · <a href={source.url} target="_blank" rel="noreferrer">Consulter le document</a></>}
      <p>Article : {source.article || 'Non renseigné'} · Effet : {source.date_effet ? formatDate(source.date_effet) : 'Non renseigné'} · Consultation : {source.date_consultation ? formatDate(source.date_consultation) : 'Non renseignée'}</p>
      <p>Périmètre : {source.perimetre || 'À renseigner'}</p><p>Limites : {source.limite || 'À renseigner'}</p>
    </li>)}</ul>}
  </article>
}

export default function CNSS() {
  const { employes, cotisations, chargement, erreur, erreurCalcul, mois, setMois, annee, ajouterEmploye, modifierEmploye, supprimerEmploye, recharger, conges, erreurConges, demanderConge, deciderConge, referentiel, erreurReferentiel, consignerReferentiel, accesPersonnel, erreurAcces } = useEmployes()
  const { societe } = useModules()
  const { exercices, setAnnee } = useExercice()
  const writable = peutEcrire() && accesPersonnel?.modification_historique_autorisee === true
  const remunerationMasquee = accesPersonnel?.mode === 'protege' && !accesPersonnel.capacites.includes('personnel.lire_remuneration')
  const identifiantsMasques = accesPersonnel?.mode === 'protege' && !accesPersonnel.capacites.includes('personnel.lire_identifiants_sensibles')
  const [onglet, setOnglet] = useState('equipe')
  const [recherche, setRecherche] = useState('')
  const [etat, setEtat] = useState('actifs')
  const [selection, setSelection] = useState(null)
  const [edition, setEdition] = useState(null)
  const [form, setForm] = useState(VIDE)
  const [occupation, setOccupation] = useState(false)
  const [erreurAction, setErreurAction] = useState('')
  const [message, setMessage] = useState('')
  const [absenceForm, setAbsenceForm] = useState(null)
  const [decision, setDecision] = useState(null)
  const [historiqueId, setHistoriqueId] = useState(null)
  const [filtreAbsence, setFiltreAbsence] = useState('tous')
  const [exportRegistre, setExportRegistre] = useState(false)
  const [preuveForm, setPreuveForm] = useState(null)
  const [preuveErreur, setPreuveErreur] = useState('')
  const [preuveMessage, setPreuveMessage] = useState('')
  const [preuveOccupee, setPreuveOccupee] = useState(false)
  const perimetreAcces = `${societe?.id}:${accesPersonnel?.mode}:${accesPersonnel?.capacites.join('|')}`
  useEffect(() => {
    if (accesPersonnel?.mode !== 'protege') return
    setEdition(null); setForm({ ...VIDE }); setSelection(null)
    setPreuveForm(null); setAbsenceForm(null); setDecision(null); setHistoriqueId(null)
    setMessage(''); setErreurAction('')
  }, [perimetreAcces])
  const preuveVersion = useRef(0)
  const scopePreuve = `${societe?.id}:${annee}`
  const scopePreuveCourant = useRef(scopePreuve)
  scopePreuveCourant.current = scopePreuve
  useEffect(() => {
    scopePreuveCourant.current = scopePreuve
    setPreuveForm(null); setPreuveErreur(''); setPreuveMessage(''); setPreuveOccupee(false)
    return () => { preuveVersion.current += 1; scopePreuveCourant.current = null }
  }, [scopePreuve])
  useEffect(() => { setSelection(null); setEdition(null); setMessage(''); setErreurAction('') }, [societe?.id])
  useEffect(() => { setAbsenceForm(null); setDecision(null); setHistoriqueId(null) }, [societe?.id])
  useEffect(() => { setSelection(null) }, [annee, mois])
  const actifs = employes.filter(e => e.actif)
  const liste = cotisations?.employes || []
  const detail = liste.find(e => e.employe.id === selection)
  const complet = cotisations?.statut === 'simulation' && liste.every(e => e.cotisations)
  const totaux = complet ? cotisations.totaux : null
  const equipes = useMemo(() => [...employes].filter(e =>
    (etat === 'tous' || (etat === 'actifs' ? e.actif : !e.actif)) &&
    [e.nom, e.poste, e.matricule, e.numero_cnss].some(v => String(v || '').toLocaleLowerCase().includes(recherche.toLocaleLowerCase()))
  ).sort((a, b) => b.id - a.id), [employes, etat, recherche])
  const brutEquipe = actifs.every(e => typeof e.salaire_brut === 'number' && Number.isFinite(e.salaire_brut))
    ? actifs.reduce((total, e) => total + e.salaire_brut, 0) : null
  const avertissements = [...(cotisations?.blocages || []), ...(cotisations?.avertissements || [])]
  const absencesVisibles = conges.filter(a => filtreAbsence === 'tous' || a.statut === filtreAbsence)
  const historique = conges.find(a => a.id === historiqueId)
  const versionsPrecedentes = (referentiel?.historique || []).filter(v => v.id !== referentiel?.version_courante?.id)
  const statutReferentiel = { non_verifie: 'Non vérifié', preuves_partielles: 'Preuves partielles', perime: 'Périmé' }[referentiel?.statut] || 'Non vérifié'

  function ouvrirPreuve() {
    if (!referentiel?.peut_consigner || !referentiel.empreinte_actuelle) return
    setPreuveErreur(''); setPreuveMessage('')
    setPreuveForm({ scope: scopePreuve, empreinte_attendue: referentiel.empreinte_actuelle,
      titre: '', url: '', article: '', date_effet: '', date_consultation: '', perimetre: '', limite: '', regime: '', commentaire: '' })
  }
  async function enregistrerPreuve(e) {
    e.preventDefault()
    if (preuveOccupee || !referentiel?.peut_consigner || preuveForm?.scope !== scopePreuveCourant.current) return
    const version = ++preuveVersion.current
    const scope = preuveForm.scope
    const courant = () => version === preuveVersion.current && scope === scopePreuveCourant.current
    setPreuveOccupee(true); setPreuveErreur(''); setPreuveMessage('')
    try {
      const { empreinte_attendue, titre, url, article, date_effet, date_consultation, perimetre, limite, regime, commentaire } = preuveForm
      const resultat = await consignerReferentiel({ empreinte_attendue, regime, commentaire,
        sources: [{ titre, url: url || null, article, date_effet: date_effet || null, date_consultation: date_consultation || null, perimetre, limite }] })
      if (courant() && resultat) { setPreuveForm(null); setPreuveMessage('Preuve consignée ; la paie définitive reste indisponible.') }
    } catch (err) { if (courant()) setPreuveErreur(err.message) }
    finally { if (courant()) setPreuveOccupee(false) }
  }

  function ouvrir(employe) {
    setEdition(employe?.id || 'nouveau')
    setForm(employe ? { ...VIDE, ...employe, personnes_charge_ir: employe.personnes_charge_ir ?? '', type_contrat: employe.type_contrat || '' } : { ...VIDE })
    setErreurAction('')
  }
  function payload(donnees) {
    if (donnees.salaire_brut == null || donnees.salaire_brut === '') throw new Error('Le salaire brut est à compléter avant de modifier ou réactiver cette fiche.')
    return {
      ...Object.fromEntries(Object.keys(VIDE).map(k => [k, donnees[k]])),
      nom: donnees.nom.trim(), poste: String(donnees.poste || '').trim(), salaire_brut: Number(donnees.salaire_brut),
      nb_enfants: Number(donnees.nb_enfants), personnes_charge_ir: donnees.personnes_charge_ir === '' || donnees.personnes_charge_ir == null ? null : Number(donnees.personnes_charge_ir),
      type_contrat: donnees.type_contrat || null, date_embauche: donnees.date_embauche || null, date_sortie: donnees.date_sortie || null,
      email: donnees.email || null, telephone: donnees.telephone || null,
      matricule: donnees.matricule || null, numero_cnss: donnees.numero_cnss || null,
    }
  }
  async function sauvegarder(e) {
    e.preventDefault()
    if (!writable || occupation) return
    setOccupation(true); setErreurAction(''); setMessage('')
    try {
      const donnees = payload(form)
      if (!Number.isFinite(donnees.salaire_brut) || donnees.salaire_brut < 0) throw new Error('Le salaire brut doit être un montant positif ou nul.')
      if (edition === 'nouveau') await ajouterEmploye(donnees)
      else await modifierEmploye(edition, donnees)
      setEdition(null); setMessage('Fiche salariée enregistrée.')
    } catch (err) { setErreurAction(err.message) }
    finally { setOccupation(false) }
  }
  async function changerEtat(employe) {
    if (!writable || occupation) return
    const action = employe.actif ? 'Archiver' : 'Réactiver'
    if (!window.confirm(`${action} la fiche de ${employe.nom} ?\nLa fiche sera conservée dans le dossier de la société.`)) return
    setOccupation(true); setErreurAction(''); setMessage('')
    try {
      if (employe.actif) await supprimerEmploye(employe.id)
      else await modifierEmploye(employe.id, { ...payload({ ...VIDE, ...employe }), actif: true })
      setMessage(employe.actif ? 'Fiche archivée et conservée.' : 'Fiche réactivée.')
    } catch (err) { setErreurAction(err.message) }
    finally { setOccupation(false) }
  }
  function exporter() {
    if (!complet) return
    const lignes = [['Préparation de paie — simulation', `${MOIS[mois - 1]} ${annee}`, societe?.raison_sociale || ''],
      ['Salarié', 'Matricule', 'Brut MAD', 'CNSS / AMO salariales MAD', 'IR MAD', 'Net MAD', 'Charges patronales MAD', 'Coût employeur MAD'],
      ...liste.map(({ employe: e, cotisations: c }) => [e.nom, e.matricule || '', c.salaire_brut, c.total_retenues_sal, c.ir, c.salaire_net, c.total_charges_pat, c.cout_employeur])]
    // Le préfixe texte empêche les noms / matricules de devenir des formules Excel.
    const cellule = valeur => `"${String(valeur ?? '').replace(/^[=+@\-\t\r]/, "'$&").replaceAll('"', '""')}"`
    const blob = new Blob(['\uFEFF' + lignes.map(l => l.map(cellule).join(';')).join('\r\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `preparation-paie-${annee}-${String(mois).padStart(2, '0')}.csv`; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  async function enregistrerAbsence(e) {
    e.preventDefault()
    if (!writable || occupation) return
    setOccupation(true); setErreurAction(''); setMessage('')
    try {
      await demanderConge({ ...absenceForm, employe_id: Number(absenceForm.employe_id), motif: absenceForm.motif || null })
      setAbsenceForm(null); setMessage('Demande enregistrée dans le dossier salarié.')
    } catch (err) { setErreurAction(err.message) }
    finally { setOccupation(false) }
  }
  async function enregistrerDecision(e) {
    e.preventDefault()
    if (!writable || occupation) return
    setOccupation(true); setErreurAction(''); setMessage('')
    try {
      await deciderConge(decision.id, { statut: decision.statut, commentaire_decision: decision.commentaire || null })
      setDecision(null); setMessage('Décision enregistrée avec son historique.')
    } catch (err) { setErreurAction(err.message) }
    finally { setOccupation(false) }
  }
  async function exporterRegistreAbsences() {
    setExportRegistre(true); setErreurAction('')
    try {
      const filtre = filtreAbsence === 'tous' ? '' : `?statut=${encodeURIComponent(filtreAbsence)}`
      await telechargerDocumentPDF(`/api/employes/conges/export/pdf${filtre}`, `registre_absences_${filtreAbsence}.pdf`)
    } catch (e) { setErreurAction(e.message) }
    finally { setExportRegistre(false) }
  }

  async function annulerAbsence(absence) {
    if (!writable || occupation || !absence.peut_annuler) return
    if (!window.confirm(`Annuler la demande de ${absence.nom_employe} du ${absence.date_debut} au ${absence.date_fin} ?\nLa demande et son historique seront conservés.`)) return
    setOccupation(true); setErreurAction(''); setMessage('')
    try {
      await deciderConge(absence.id, { statut: 'annule' })
      setMessage('Demande annulée ; historique conservé.')
    } catch (err) { setErreurAction(err.message) }
    finally { setOccupation(false) }
  }

  return <div className={styles.page} data-form-page>
    <header className={styles.topbar}><div><h1 className={styles.pageTitle}>Paie & GRH</h1><p className={styles.pageSubtitle}>Dossiers salariés et préparation des rémunérations · {societe?.raison_sociale || 'Société'}</p></div>
      <div className={styles.actions}><button className={styles.btnSec} onClick={recharger} disabled={chargement}><i className="ti ti-refresh" aria-hidden="true" /> Actualiser</button>
        {writable && <button className={styles.btnPrim} disabled={!societe?.id || chargement || occupation} onClick={() => ouvrir(null)}><i className="ti ti-user-plus" aria-hidden="true" /> Ajouter un salarié</button>}</div></header>
    <div className={styles.content}>
      <div className={styles.kpiGrid}>
        {[
          ['Salariés actifs', actifs.length, 'ti-users', false],
          ['Brut contractuel mensuel', montant(brutEquipe), 'ti-wallet', true],
          ['Net simulé de la période', montant(totaux?.salaire_net), 'ti-currency-dirham', true],
          ['Coût employeur simulé', montant(totaux?.cout_employeur), 'ti-building-bank', true],
        ].map(([label, valeur, icon, mad]) => <div key={label} className={styles.kpiCard}><div className={styles.kpiLabel}><i className={`ti ${icon}`} aria-hidden="true" />{label}</div><div className={styles.kpiValeur}>{valeur}{mad && valeur !== '—' && <small> MAD</small>}</div></div>)}
      </div>
      <nav className={styles.tabs} aria-label="Gestion du personnel">
        <button className={onglet === 'equipe' ? styles.tabActive : ''} onClick={() => setOnglet('equipe')}><i className="ti ti-users" aria-hidden="true" /> Équipe</button>
        <button className={onglet === 'paie' ? styles.tabActive : ''} onClick={() => setOnglet('paie')}><i className="ti ti-receipt" aria-hidden="true" /> Préparation mensuelle</button>
        <button className={onglet === 'absences' ? styles.tabActive : ''} onClick={() => setOnglet('absences')}><i className="ti ti-calendar-event" aria-hidden="true" /> Congés & absences</button>
        <button className={onglet === 'avances' ? styles.tabActive : ''} aria-pressed={onglet === 'avances'} onClick={() => setOnglet('avances')}><i className="ti ti-wallet" aria-hidden="true" /> Avances des salariés</button>
      </nav>
      {onglet === 'avances' && <AvancesSalaries key={societe?.id || 'aucune'} employes={employes} writable={writable} />}
      {(erreur || erreurAction) && <div role="alert"><InlineNotice tone="danger">{erreurAction || erreur}</InlineNotice></div>}
      {message && <div role="status"><InlineNotice tone="success">{message}</InlineNotice></div>}
      {erreurAcces && <InlineNotice tone="warning">{erreurAcces}</InlineNotice>}
      {accesPersonnel?.mode === 'protege'
        ? <InlineNotice>Personnel protégé : les consultations dépendent de vos habilitations. Les modifications sont désactivées dans cet accès.</InlineNotice>
        : !writable && <InlineNotice>Consultation seule : les fiches et la préparation sont accessibles en lecture.</InlineNotice>}
      {edition && <form className={styles.formCard} onSubmit={sauvegarder}>
        <div className={styles.cardHeader}><h2>{edition === 'nouveau' ? 'Nouveau salarié' : writable ? 'Modifier la fiche salariée' : 'Fiche du salarié'}</h2><button type="button" className={styles.btnSec} onClick={() => setEdition(null)}>Fermer la fiche</button></div>
        <fieldset className={styles.formBody} disabled={!writable}><FormSection title="Identité et contrat" icon="ti-id"><div className={styles.formGrid}>
          <Champ nom="nom" label="Nom complet" form={form} setForm={setForm} required maxLength={150} />
          <Champ nom="poste" label="Poste" form={form} setForm={setForm} maxLength={150} />
          <Champ nom="matricule" label="Matricule interne" form={form} setForm={setForm} />
          <Champ nom="numero_cnss" label="Numéro CNSS" form={form} setForm={setForm} />
          <Champ nom="type_contrat" label="Type de contrat" form={form} setForm={setForm}>{[ ['', '? renseigner'], ['CDI', 'CDI'], ['CDD', 'CDD'], ['autre', 'Autre'] ].map(([v, label]) => <option key={v} value={v}>{label}</option>)}</Champ>
          <Champ nom="date_embauche" label="Date d’embauche" type="date" form={form} setForm={setForm} />
          <Champ nom="date_sortie" label="Date de sortie" type="date" form={form} setForm={setForm} />
          <Champ nom="email" label="Adresse e-mail" type="email" form={form} setForm={setForm} />
          <Champ nom="telephone" label="Téléphone" type="tel" form={form} setForm={setForm} />
        </div></FormSection>
        <FormSection title="Rémunération et situation personnelle" icon="ti-wallet"><div className={styles.formGrid}>
          <Champ nom="salaire_brut" label="Salaire brut mensuel (MAD)" type="number" min="0" step="0.01" required form={form} setForm={setForm} />
          <Champ nom="situation_familiale" label="Situation familiale" form={form} setForm={setForm}>{SITUATIONS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</Champ>
          <Champ nom="nb_enfants" label="Nombre d’enfants" type="number" min="0" step="1" form={form} setForm={setForm} />
          <Champ nom="personnes_charge_ir" label="Personnes à charge IR confirmées" form={form} setForm={setForm}><option value="">À confirmer</option>{[0, 1, 2, 3, 4, 5, 6].map(v => <option key={v} value={v}>{v}</option>)}</Champ>
        </div><p className={styles.note}>La situation familiale et le nombre d’enfants ne valent pas confirmation des personnes à charge pour l’IR.</p></FormSection></fieldset>
        <footer className={styles.formFooter}><button type="button" className={styles.btnSec} onClick={() => setEdition(null)}>Annuler</button>{writable && <button className={styles.btnPrim} disabled={occupation}>{occupation ? 'Enregistrement…' : 'Enregistrer la fiche'}</button>}</footer>
      </form>}
      {onglet === 'equipe' ? <section className={styles.card}>
        <div className={styles.cardHeader}><div><h2>Dossiers du personnel</h2><p>{equipes.length} fiche{equipes.length !== 1 && 's'} · ordre des ajouts les plus récents</p></div><div className={styles.actions}>
          <input aria-label="Rechercher un salarié" className={styles.search} placeholder="Nom, poste, matricule…" value={recherche} onChange={e => setRecherche(e.target.value)} />
          <select aria-label="Statut des salariés" value={etat} onChange={e => setEtat(e.target.value)}><option value="actifs">Actifs</option><option value="archives">Archivés</option><option value="tous">Tous les salariés</option></select></div></div>
        <div className={styles.tableWrapper}><table className={styles.table}><thead><tr><th>Salarié</th><th>Contrat / embauche</th><th>CNSS</th><th className={styles.numeric}>Brut mensuel</th><th>État</th><th>Fiche</th></tr></thead><tbody>
          {chargement ? <tr><td colSpan={6} className={styles.vide}>Chargement des dossiers…</td></tr> : equipes.length === 0 ? <tr><td colSpan={6} className={styles.vide}><i className="ti ti-users" aria-hidden="true" /><span>Aucun salarié dans cette sélection.</span>{writable && <button className={styles.btnSec} disabled={!societe?.id || chargement || occupation} onClick={() => ouvrir(null)}>Créer une fiche salariée</button>}</td></tr> : equipes.map(e => <tr key={e.id}><td><strong>{e.nom}</strong><small>{[e.matricule, e.poste].filter(Boolean).join(' · ') || 'Poste à compléter'}</small></td><td>{e.type_contrat || 'À compléter'}<small>{e.date_embauche || 'Date à compléter'}</small></td><td>{identifiantsMasques ? 'Masqué' : e.numero_cnss || 'À compléter'}</td><td className={styles.numeric}>{remunerationMasquee ? 'Masqué' : <>{montant(e.salaire_brut)} MAD</>}</td><td><span className={e.actif ? styles.badgeActive : styles.badge}>{e.actif ? 'Actif' : 'Archivé'}</span></td><td>{writable ? <div className={styles.rowActions}><button className={styles.btnText} onClick={() => ouvrir(e)} aria-label={`Modifier ${e.nom}`}>Modifier</button><button className={styles.btnText} disabled={occupation} onClick={() => changerEtat(e)} aria-label={`${e.actif ? 'Archiver' : 'Réactiver'} ${e.nom}`}>{e.actif ? 'Archiver' : 'Réactiver'}</button></div> : <button className={styles.btnText} onClick={() => ouvrir(e)} aria-label={`Consulter ${e.nom}`}>Consulter</button>}</td></tr>)}
        </tbody></table></div>
      </section> : onglet === 'paie' ? <>
        <section className={styles.card}><div className={styles.cardHeader}><div><h2>Préparation des rémunérations</h2><p>Simulation mensuelle depuis les paramètres de la société</p></div><div className={styles.actions}>
          <select aria-label="Année de paie" value={annee} onChange={e => setAnnee(e.target.value)}>{(exercices.length ? exercices : [{ annee }]).map(e => <option key={e.annee} value={e.annee}>{e.annee}</option>)}</select>
          <select aria-label="Mois de paie" value={mois} onChange={e => setMois(Number(e.target.value))}>{MOIS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</select>
          <button className={styles.btnSec} onClick={exporter} disabled={!complet || chargement || !liste.length}><i className="ti ti-download" aria-hidden="true" /> Exporter la préparation CSV</button></div></div>
          <div className={styles.preparationNotice}><InlineNotice tone={complet ? 'info' : 'warning'}>{chargement ? 'Chargement de la préparation…' : complet ? `Simulation disponible · ${MOIS[mois - 1]} ${annee} · paramètres ${cotisations.annee_taux}` : 'Préparation indisponible : compléter les paramètres et les fiches signalés.'}<p>{erreurCalcul || 'Cette préparation ne constitue pas un bulletin validé, une déclaration CNSS ou un paiement.'}</p></InlineNotice>
            {avertissements.length > 0 && <ul className={styles.notes}>{avertissements.map((a, i) => <li key={i}>{texte(a)}</li>)}</ul>}</div>
          <div className={styles.tableWrapper}><table className={styles.table}><thead><tr><th>Salarié</th><th className={styles.numeric}>Brut</th><th className={styles.numeric}>CNSS / AMO sal.</th><th className={styles.numeric}>IR</th><th className={styles.numeric}>Net simulé</th><th className={styles.numeric}>Charges pat.</th><th>Contrôle</th></tr></thead><tbody>
            {liste.length === 0 ? <tr><td colSpan={7} className={styles.vide}>{chargement ? 'Chargement…' : 'Aucun salarié éligible pour cette période.'}</td></tr> : liste.map(({ employe: e, cotisations: c, blocages = [] }) => <tr key={e.id} className={selection === e.id ? styles.rowSelected : ''}><td><button className={styles.personButton} onClick={() => setSelection(selection === e.id ? null : e.id)}>{e.nom}</button><small>{e.poste}</small></td><td className={styles.numeric}>{montant(c?.salaire_brut ?? e.salaire_brut)}</td><td className={styles.numeric}>{montant(c?.total_retenues_sal)}</td><td className={styles.numeric}>{montant(c?.ir)}</td><td className={styles.numeric}><strong>{montant(c?.salaire_net)}</strong></td><td className={styles.numeric}>{montant(c?.total_charges_pat)}</td><td><span className={c ? styles.badgeActive : styles.badge}>{c ? 'Simulation' : 'À compléter'}</span>{blocages.map((b, i) => <small key={i}>{texte(b)}</small>)}</td></tr>)}
          </tbody>{totaux && <tfoot><tr><td>Total simulé</td>{['salaire_brut', 'total_retenues_sal', 'ir', 'salaire_net', 'total_charges_pat'].map(k => <td key={k} className={styles.numeric}>{montant(totaux[k])}</td>)}<td>MAD</td></tr></tfoot>}</table></div>
        </section>
        {detail && <section className={styles.card}><div className={styles.cardHeader}><div><h2>{detail.employe.nom} · {MOIS[mois - 1]} {annee}</h2><p>Détail de la simulation mensuelle</p></div><button className={styles.btnSec} onClick={() => setSelection(null)}>Fermer le détail</button></div><div className={styles.detailGrid}>
          {detail.cotisations ? <>{[
            ['Rémunération', [['Brut mensuel', 'salaire_brut'], ['Net imposable annuel', 'revenu_net_imposable_annuel'], ['Frais professionnels annuels', 'frais_professionnels_annuels'], ['Net simulé', 'salaire_net']]],
            ['Retenues salariales', [['CNSS', 'cnss_retraite_sal'], ['AMO', 'amo_sal'], ['IR retenu', 'ir'], ['Total social salarial', 'total_retenues_sal']]],
            ['Charges patronales', [['CNSS', 'cnss_retraite_pat'], ['Prestations familiales', 'prestations_fam'], ['AMO', 'amo_pat'], ['Formation professionnelle', 'formation'], ['Total charges', 'total_charges_pat'], ['Coût employeur', 'cout_employeur']]],
          ].map(([titre, rubriques]) => <div className={styles.detailSection} key={titre}><h3>{titre}</h3>{rubriques.map(([label, cle]) => <div className={styles.detailLigne} key={cle}><span>{label}</span><strong>{montant(detail.cotisations[cle])} MAD</strong></div>)}</div>)}</> : <InlineNotice tone="warning">{(detail.blocages || []).map(texte).join(' · ') || 'Calcul indisponible pour cette fiche.'}</InlineNotice>}
        </div></section>}
        <section className={styles.card}><div className={styles.cardHeader}><h2>Paramètres et sources</h2><span className={styles.badge}>Millésime {cotisations?.annee_taux || annee}</span></div><div className={styles.sourceBody}>
          <section aria-label="Traçabilité annuelle du référentiel" className={styles.proofSection}>
            <div className={styles.proofHeading}><h3>Référentiel documentaire · {annee}</h3><span className={styles.badge}>{statutReferentiel}</span></div>
            <p>{societe?.raison_sociale || 'Société'} · Année {annee}</p>
            <InlineNotice tone="warning">Les preuves consignées ne valident pas les taux ni les calculs. La paie définitive reste indisponible.</InlineNotice>
            {erreurReferentiel && <p role="alert">{erreurReferentiel}</p>}
            {!referentiel && !erreurReferentiel && <p>Chargement de la traçabilité annuelle…</p>}
            {referentiel && <>
              <p className={styles.hash}>Empreinte actuelle : {referentiel.empreinte_actuelle || 'Non disponible'}</p>
              {(referentiel.limites || []).length > 0 && <ul>{referentiel.limites.map((limite, i) => <li key={i}>{texte(limite)}</li>)}</ul>}
              {(referentiel.diagnostics || []).length > 0 && <ul role="alert">{referentiel.diagnostics.map((diagnostic, i) => <li key={i}>{texte(diagnostic)}</li>)}</ul>}
              {referentiel.version_courante ? <VersionDocumentaire version={referentiel.version_courante} /> : <p>Aucune version documentaire pour cette société et cette année.</p>}
              {versionsPrecedentes.length > 0 && <details className={styles.proofHistory}><summary>Historique documentaire ({versionsPrecedentes.length})</summary>{versionsPrecedentes.map(version => <VersionDocumentaire key={version.id} version={version} />)}</details>}
              {referentiel.peut_consigner && <button className={styles.btnSec} disabled={preuveOccupee || chargement} onClick={ouvrirPreuve}>Consigner une preuve</button>}
            </>}
            {preuveMessage && <p role="status">{preuveMessage}</p>}
            {preuveForm && preuveForm.scope === scopePreuve && <form className={styles.proofForm} onSubmit={enregistrerPreuve} aria-label="Consigner une preuve documentaire">
              <h3>Nouvelle version documentaire · {annee}</h3>
              <p>Les paramètres actuels seront capturés par le serveur ; aucune valeur de taux ne peut être saisie ici.</p>
              <fieldset disabled={preuveOccupee} className={styles.formBody}><div className={styles.formGrid}>
                {[
                  ['titre', 'Titre du document', 'text', true], ['url', 'URL du document (facultative)', 'url', false], ['article', 'Article / référence', 'text', false],
                  ['date_effet', 'Date d’effet documentée', 'date', false], ['date_consultation', 'Date de consultation', 'date', false], ['regime', 'Régime / contexte', 'text', false],
                ].map(([nom, label, type, required]) => <Champ key={nom} nom={nom} label={label} type={type} required={required} form={preuveForm} setForm={setPreuveForm} />)}
                {[['perimetre', 'Périmètre documenté'], ['limite', 'Limites de la preuve'], ['commentaire', 'Commentaire']].map(([nom, label]) => <div className={styles.formGroup} key={nom}><label htmlFor={`preuve-${nom}`}>{label}</label><textarea id={`preuve-${nom}`} value={preuveForm[nom]} onChange={e => setPreuveForm(p => ({ ...p, [nom]: e.target.value }))} /></div>)}
              </div></fieldset>
              {preuveErreur && <p role="alert">{preuveErreur}</p>}
              <div className={styles.actions}><button type="button" className={styles.btnSec} disabled={preuveOccupee} onClick={() => setPreuveForm(null)}>Annuler la consignation</button><button className={styles.btnPrim} disabled={preuveOccupee}>{preuveOccupee ? 'Consignation…' : 'Enregistrer la preuve'}</button></div>
            </form>}
          </section>
          {(cotisations?.sources || []).length ? <ul>{cotisations.sources.map((source, i) => <li key={i}>{typeof source === 'string' ? source : <>{texte(source)}{source.statut && <small className={styles.note}> · {source.statut}</small>}{source.url && /^https?:\/\//.test(source.url) && <> · <a href={source.url} target="_blank" rel="noreferrer">Consulter la source</a></>}</>}</li>)}</ul> : <p>Aucune source réglementaire confirmée pour cette préparation.</p>}
          {cotisations?.parametres?.taux && <div className={styles.rateGrid}>{(Array.isArray(cotisations.parametres.taux) ? cotisations.parametres.taux : Object.entries(cotisations.parametres.taux).map(([code, t]) => ({ code, ...t }))).map((t, i) => <div key={i}><strong>{t.libelle || t.code}</strong><small>Salarial : {typeof t.taux_sal === 'number' ? `${(t.taux_sal * 100).toLocaleString('fr-MA')} %` : 'À confirmer'} · Patronal : {typeof t.taux_pat === 'number' ? `${(t.taux_pat * 100).toLocaleString('fr-MA')} %` : 'À confirmer'}</small></div>)}</div>}
          <p className={styles.note}>L’intégration des congés et absences aux calculs de paie, les variables, bulletins définitifs et déclarations sociales restent à compléter dans un prochain lot.</p>
        </div></section>
      </> : <>
        <section className={styles.card}><div className={styles.cardHeader}><div><h2>Demandes de congés et absences</h2><p>Périodes déclarées et décisions conservées dans le dossier de la société</p></div><div className={styles.actions}>
          <select aria-label="Filtrer les demandes" value={filtreAbsence} onChange={e => setFiltreAbsence(e.target.value)}><option value="tous">Toutes les demandes</option>{Object.entries(ETATS_ABSENCE).map(([v, t]) => <option value={v} key={v}>{t}</option>)}</select>
          <button className={styles.btnSec} disabled={chargement || !!erreurConges || exportRegistre || !absencesVisibles.length} onClick={exporterRegistreAbsences}><i className="ti ti-file-type-pdf" aria-hidden="true" /> {exportRegistre ? 'Export en cours…' : 'Exporter le registre PDF'}</button>
          {writable && <button className={styles.btnPrim} disabled={chargement || !actifs.length} onClick={() => { setAbsenceForm({ employe_id: '', type_absence: 'conge', date_debut: dateLocaleISO(), date_fin: dateLocaleISO(), motif: '' }); setErreurAction('') }}><i className="ti ti-plus" aria-hidden="true" /> Nouvelle demande</button>}</div></div>
          <div className={styles.preparationNotice}><InlineNotice>Les durées affichées sont des jours calendaires, dates de début et de fin incluses. Elles ne constituent pas un solde de congés acquis ni une retenue automatique sur salaire.</InlineNotice></div>
          {erreurConges && <div className={styles.preparationNotice} role="alert"><InlineNotice tone="danger">{erreurConges}</InlineNotice></div>}
          {absenceForm && writable && <form onSubmit={enregistrerAbsence} className={styles.absenceForm}><FormSection title="Nouvelle demande" icon="ti-calendar-plus"><div className={styles.formGrid}>
            <Champ nom="employe_id" label="Salarié concerné" form={absenceForm} setForm={setAbsenceForm} required><option value="">Sélectionner un salarié</option>{actifs.map(e => <option key={e.id} value={e.id}>{e.nom}</option>)}</Champ>
            <Champ nom="type_absence" label="Type de demande" form={absenceForm} setForm={setAbsenceForm}>{Object.entries(ABSENCES).map(([v, t]) => <option value={v} key={v}>{t}</option>)}</Champ>
            <Champ nom="date_debut" label="Début de l’absence" type="date" required form={absenceForm} setForm={setAbsenceForm} />
            <Champ nom="date_fin" label="Fin de l’absence" type="date" required form={absenceForm} setForm={setAbsenceForm} />
            <div className={`${styles.formGroup} ${styles.largeField}`}><label htmlFor="paie-absence-motif">Motif ou précision</label><textarea id="paie-absence-motif" rows={3} maxLength={1000} value={absenceForm.motif} onChange={e => setAbsenceForm(p => ({ ...p, motif: e.target.value }))} /></div>
          </div></FormSection><div className={styles.formFooter}><button type="button" className={styles.btnSec} onClick={() => setAbsenceForm(null)}>Fermer la demande</button><button className={styles.btnPrim} disabled={occupation}>Enregistrer la demande</button></div></form>}
          {decision && writable && <form className={styles.absenceForm} onSubmit={enregistrerDecision}><FormSection title={`${decision.statut === 'approuve' ? 'Approuver' : 'Refuser'} la demande de ${decision.nom}`} icon="ti-checklist"><div className={styles.formGroup}><label htmlFor="paie-commentaire-decision">Commentaire de décision</label><textarea id="paie-commentaire-decision" rows={2} maxLength={1000} value={decision.commentaire} onChange={e => setDecision(p => ({ ...p, commentaire: e.target.value }))} /></div></FormSection><div className={styles.formFooter}><button type="button" className={styles.btnSec} onClick={() => setDecision(null)}>Fermer la décision</button><button className={styles.btnPrim} disabled={occupation}>Confirmer la décision</button></div></form>}
          <div className={styles.tableWrapper}><table className={styles.table}><thead><tr><th>Salarié / motif</th><th>Type</th><th>Période</th><th className={styles.numeric}>Jours calendaires</th><th>Statut</th><th>Suivi</th></tr></thead><tbody>
            {!absencesVisibles.length ? <tr><td colSpan={6} className={styles.vide}>{chargement ? 'Chargement des demandes…' : 'Aucune demande dans cette sélection.'}</td></tr> : absencesVisibles.map(a => <tr key={a.id}><td><strong>{a.nom_employe}</strong><small>{a.motif || 'Sans précision'}{a.commentaire_decision && ` · Décision : ${a.commentaire_decision}`}</small></td><td>{ABSENCES[a.type_absence] || a.type_absence}</td><td>{a.date_debut}<small>au {a.date_fin}</small></td><td className={styles.numeric}>{a.jours_calendaires}</td><td><span className={a.statut === 'approuve' ? styles.badgeActive : styles.badge}>{ETATS_ABSENCE[a.statut] || a.statut}</span></td><td><div className={styles.rowActions}>
              <button className={styles.btnText} onClick={() => setHistoriqueId(a.id)} aria-label={`Historique demande ${a.id}`}>Historique</button>
              {writable && a.peut_decider && <><button className={styles.btnText} disabled={occupation} aria-label={`Approuver demande ${a.id}`} onClick={() => { setDecision({ id: a.id, nom: a.nom_employe, statut: 'approuve', commentaire: '' }); setErreurAction('') }}>Approuver</button><button className={styles.btnText} disabled={occupation} aria-label={`Refuser demande ${a.id}`} onClick={() => { setDecision({ id: a.id, nom: a.nom_employe, statut: 'refuse', commentaire: '' }); setErreurAction('') }}>Refuser</button></>}
              {writable && a.peut_annuler && <button className={styles.btnText} disabled={occupation} aria-label={`Annuler demande ${a.id}`} onClick={() => annulerAbsence(a)}>Annuler</button>}
            </div></td></tr>)}
          </tbody></table></div>
        </section>
        {historique && <section className={styles.card}><div className={styles.cardHeader}><div><h2>Historique de la demande #{historique.id}</h2><p>{historique.nom_employe} · {historique.date_debut} au {historique.date_fin}</p></div><button className={styles.btnSec} onClick={() => setHistoriqueId(null)}>Fermer l’historique</button></div><ol className={styles.timeline}>
          {(historique.historique || []).map((e, i) => <li key={e.id || i}><div className={styles.timelineDot} /><div><strong>{e.ancien_statut && `${ETATS_ABSENCE[e.ancien_statut] || e.ancien_statut} → `}{ETATS_ABSENCE[e.nouveau_statut] || e.nouveau_statut}</strong><small>{String(e.created_at || '').replace('T', ' ')} · Utilisateur #{e.acteur_id}</small>{e.commentaire && <p>{e.commentaire}</p>}</div></li>)}
        </ol></section>}
      </>}
    </div>
  </div>
}
