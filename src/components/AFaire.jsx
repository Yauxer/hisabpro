import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { API_BASE } from '../services/api.js'
import { factureEnRetard } from '../utils/echeancesFactures.js'
import { formatMAD } from '../data/donnees.js'

// Lot UX 967 : ce qui demande une action, avant les indicateurs.
// Chaque source est indépendante : une donnée indisponible n'empêche pas les autres.
function lire(url) {
  const token = localStorage.getItem('hisabpro_token')
  return fetch(API_BASE + url, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => (r.ok ? r.json() : null))
    .catch(() => null)
}

function echeanceTVA(periodicite, maintenant = new Date()) {
  // Période close la plus récente, à déposer avant la fin du mois courant.
  const m = maintenant.getMonth() + 1
  const limite = new Date(maintenant.getFullYear(), maintenant.getMonth() + 1, 0)
  if (periodicite === 'trimestrielle') {
    if (![1, 4, 7, 10].includes(m)) return null
    const trimestre = m === 1 ? 4 : (m - 1) / 3
    return { annee: m === 1 ? maintenant.getFullYear() - 1 : maintenant.getFullYear(), trimestre, limite, libelle: `T${trimestre}` }
  }
  const mois = m === 1 ? 12 : m - 1
  const annee = m === 1 ? maintenant.getFullYear() - 1 : maintenant.getFullYear()
  return { annee, mois, limite, libelle: `${String(mois).padStart(2, '0')}` }
}

export default function AFaire({ annee, nbBrouillons, factures = [], periodiciteTVA = 'mensuelle' }) {
  const [reglements, setReglements] = useState(null)
  const [fec, setFec] = useState(null)
  const [declaration, setDeclaration] = useState(null)
  const tva = echeanceTVA(periodiciteTVA)

  useEffect(() => {
    let actif = true
    lire(`/api/reglements?exercice=${annee}`).then(d => actif && setReglements(Array.isArray(d) ? d : null))
    lire(`/api/fec/apercu?exercice=${annee}`).then(d => actif && setFec(d))
    // La consultation de la période indique si elle est déposée (avec ou sans migration 129).
    if (tva) lire(`/api/tva/declaration?exercice=${tva.annee}&${tva.trimestre ? `trimestre=${tva.trimestre}` : `mois=${tva.mois}`}`)
      .then(d => actif && setDeclaration(d))
    return () => { actif = false }
  }, [annee, tva?.annee, tva?.mois, tva?.trimestre])

  const enRetard = factures.filter(f => factureEnRetard(f))
  const portefeuille = (reglements || []).filter(r => ['portefeuille', 'encaissement'].includes(r.statut))
  const effetsAPayer = (reglements || []).filter(r => r.statut === 'a_payer')

  const elements = [
    nbBrouillons > 0 && { cle: 'brouillons', lien: '/journal', icone: 'ti-file-pencil', couleur: 'var(--amber)',
      texte: `${nbBrouillons} écriture(s) en brouillon à valider` },
    enRetard.length > 0 && { cle: 'retard', lien: '/factures', icone: 'ti-clock-exclamation', couleur: 'var(--red)',
      texte: `${enRetard.length} facture(s) échue(s) non soldée(s)` },
    portefeuille.length > 0 && { cle: 'portefeuille', lien: '/effets', icone: 'ti-receipt', couleur: 'var(--blue)',
      texte: `${portefeuille.length} chèque(s)/effet(s) à remettre ou à encaisser — ${formatMAD(portefeuille.reduce((s, r) => s + Number(r.montant || 0), 0))} MAD` },
    effetsAPayer.length > 0 && { cle: 'apayer', lien: '/effets', icone: 'ti-calendar-due', couleur: 'var(--amber)',
      texte: `${effetsAPayer.length} effet(s) fournisseur à payer` },
    fec && !fec.conforme_export && { cle: 'fec', lien: '/journal', icone: 'ti-file-alert', couleur: 'var(--red)',
      texte: `FEC ${annee} bloqué : ${fec.nb_bloquants || 0} anomalie(s) à traiter` },
    tva && declaration && !declaration.declaration_deposee && { cle: 'tva', lien: '/declaration-tva', icone: 'ti-calendar-event', couleur: 'var(--blue)',
      texte: `TVA ${tva.libelle}/${tva.annee} : dépôt à enregistrer avant le ${tva.limite.toLocaleDateString('fr-MA')}` },
  ].filter(Boolean)

  return (
    <section className="a-faire" aria-label="À faire">
      <h2 className="a-faire-titre"><i className="ti ti-list-check" aria-hidden="true" /> À faire</h2>
      {elements.length === 0
        ? <p className="a-faire-vide">Rien d'urgent : aucune action en attente détectée.</p>
        : <ul className="a-faire-liste">
            {elements.map(e => (
              <li key={e.cle}>
                <Link to={e.lien} className="a-faire-element">
                  <i className={`ti ${e.icone}`} aria-hidden="true" style={{ color: e.couleur }} />
                  <span>{e.texte}</span>
                  <i className="ti ti-chevron-right a-faire-fleche" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>}
    </section>
  )
}
