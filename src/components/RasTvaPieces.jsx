import { useState } from 'react'
import { getToken, peutEcrire } from '../services/api.js'
import PiecesJointes from './PiecesJointes.jsx'
import styles from './RasTvaRegistre.module.css'

export default function RasTvaPieces({ ligne, onChange }) {
  const [ouvert, setOuvert] = useState(false)
  const groupes = [
    ['Capture', ligne.ecriture_id, ligne.documents_od || []],
    ...(ligne.od_annulation_id ? [['Contrepassation', ligne.od_annulation_id, ligne.documents_annulation || []]] : []),
  ]
  return <details className={styles.documents} onToggle={e => { if (e.target === e.currentTarget) setOuvert(e.currentTarget.open) }}>
    <summary>Documents liés aux OD</summary>
    {ouvert && <section aria-label={`Documents de la capture TVA ${ligne.capture_id}`}>
      <p className={styles.note}>Références complémentaires et fichiers du Journal. Un document joint ne vaut pas à lui seul attestation contrôlée, versement ou crédit fiscal. Ici, les documents peuvent être consultés ou ajoutés ; les originaux sont conservés.</p>
      {groupes.map(([libelle, eid, documents]) => <section key={`${getToken()}:${eid}`} aria-label={`${libelle} · OD ${eid}`} className={styles.documentsOd}>
        <strong>{libelle} · OD #{eid}</strong>
        {documents.length ? <ul>{documents.map(j => <li key={j.id}>
          {j.reference || 'Référence non renseignée'} · {j.date_piece || 'Date non renseignée'}
          {j.fichier_nom ? ` · Fichier déclaré : ${j.fichier_nom}` : ' · Référence sans fichier'}
          {j.prioritaire && ' · Prioritaire pour le FEC'}
        </li>)}</ul> : <p>Aucun complément documentaire enregistré pour cette OD.</p>}
        <PiecesJointes docType="ecriture" docId={eid} readOnly={!peutEcrire()} preserveExisting onChange={onChange} />
      </section>)}
    </section>}
  </details>
}
