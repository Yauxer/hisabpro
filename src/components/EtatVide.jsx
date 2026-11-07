import { Link } from 'react-router-dom'

// État vide guidé (lot 973) : ce que contient la page, et par quoi commencer.
export default function EtatVide({ icone = 'ti-inbox', titre, children, action, onAction, action2, onAction2, lien, libelleLien }) {
  return <div className="etat-vide" role="note" aria-label={titre}>
    <i className={`ti ${icone} etat-vide-icone`} aria-hidden="true" />
    <h2 className="etat-vide-titre">{titre}</h2>
    {children && <p className="etat-vide-texte">{children}</p>}
    {(action || action2 || lien) && <div className="etat-vide-actions">
      {action && onAction && <button type="button" className="etat-vide-bouton" onClick={onAction}>{action}</button>}
      {action2 && onAction2 && <button type="button" className="etat-vide-bouton etat-vide-bouton-secondaire" onClick={onAction2}>{action2}</button>}
      {lien && <Link className="etat-vide-lien" to={lien}>{libelleLien}</Link>}
    </div>}
  </div>
}
