import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PaieElements from './pages/PaieElements.jsx'
import PaieChargesSociales from './pages/PaieChargesSociales.jsx'
import PaieFiscalite from './pages/PaieFiscalite.jsx'
import PaieTraitement from './pages/PaieTraitement.jsx'
import PaieCloture from './pages/PaieCloture.jsx'
import PaieDuMois from './pages/PaieDuMois.jsx'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Journal from './pages/Journal.jsx'
import PlanComptes from './pages/PlanComptes.jsx'
import Factures from './pages/Factures.jsx'
import Avoirs from './pages/Avoirs.jsx'
import Acomptes from './pages/Acomptes.jsx'
import Effets from './pages/Effets.jsx'
import DeclarationTVA from './pages/DeclarationTVA.jsx'
import GrandLivre from './pages/GrandLivre.jsx'
import Bilan from './pages/Bilan.jsx'
import Etic from './pages/Etic.jsx'
import CNSS from './pages/CNSS.jsx'
import Personnel from './pages/Personnel.jsx'
import LiasseFiscale from './pages/LiasseFiscale.jsx'
import FiscaliteIS from './pages/FiscaliteIS.jsx'
import Parametres from './pages/Parametres.jsx'

import Tiers from './pages/Tiers.jsx'
import Articles from './pages/Articles.jsx'
import Inventaire from './pages/Inventaire.jsx'
import Commercial from './pages/Commercial.jsx'
import DelaisPaiement from './pages/DelaisPaiement.jsx'
import RapprochementBancaire from './pages/RapprochementBancaire.jsx'
import Lettrage from './pages/Lettrage.jsx'
import Balances from './pages/Balances.jsx'
import SituationFinanciere from './pages/SituationFinanciere.jsx'
import Immobilisations from './pages/Immobilisations.jsx'
import Cloture from './pages/Cloture.jsx'
import LivreInventaire from './pages/LivreInventaire.jsx'
function Placeholder({ titre }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ background: 'var(--bg-primary)', borderBottom: '0.5px solid var(--border-light)', padding: '14px 24px' }}>
        <h1 style={{ fontSize: 15, fontWeight: 500 }}>{titre}</h1>
      </div>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', flexDirection: 'column', gap: 10 }}>
        <i className="ti ti-tools" style={{ fontSize: 32 }} aria-hidden="true" />
        <span style={{ fontSize: 13 }}>Module en cours de développement</span>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"       element={<Dashboard />} />
          <Route path="journal"         element={<Journal />} />
          <Route path="plan-comptes"    element={<PlanComptes />} />
          <Route path="factures"        element={<Factures />} />
          <Route path="avoirs"          element={<Avoirs />} />
          <Route path="acomptes"        element={<Acomptes />} />
          <Route path="effets"          element={<Effets />} />
          <Route path="tiers"           element={<Tiers />} />
          <Route path="inventaire"        element={<Inventaire />} />
          <Route path="articles"        element={<Articles />} />
          <Route path="commercial"      element={<Commercial />} />
          <Route path="delais-paiement" element={<DelaisPaiement />} />
          <Route path="declaration-tva" element={<DeclarationTVA />} />
          <Route path="liasse-fiscale"  element={<LiasseFiscale />} />
          <Route path="fiscalite-is"    element={<FiscaliteIS />} />
          <Route path="cnss"            element={<CNSS />} />
          <Route path="personnel-paie/personnel" element={<Personnel />} />
          <Route path="personnel-paie/personnel/:employeId" element={<Personnel />} />
          <Route path="personnel-paie/demandes" element={<Personnel />} />
          <Route path="personnel-paie/acces" element={<Personnel />} />
          <Route path="personnel-paie/elements" element={<PaieElements />} />
          <Route path="personnel-paie/charges-sociales" element={<PaieChargesSociales />} />
          <Route path="personnel-paie/fiscalite" element={<PaieFiscalite />} />
          <Route path="personnel-paie/charges-sociales/simulations" element={<PaieChargesSociales />} />
          <Route path="personnel-paie/elements/variables" element={<PaieElements />} />
          <Route path="personnel-paie/traitement" element={<PaieTraitement />} />
          <Route path="personnel-paie/paie-du-mois" element={<PaieDuMois />} />
          <Route path="personnel-paie/bulletins" element={<PaieCloture section="bulletins" />} />
          <Route path="personnel-paie/avances" element={<PaieCloture section="avances" />} />
          <Route path="personnel-paie/paiements" element={<PaieCloture section="paiements" />} />
          <Route path="personnel-paie/comptabilisation" element={<PaieCloture section="comptabilisation" />} />
          <Route path="personnel-paie/etats" element={<PaieCloture section="etats" />} />
          <Route path="personnel-paie/*" element={<Personnel indisponible />} />
          <Route path="grand-livre"     element={<GrandLivre />} />
          <Route path="bilan"           element={<Bilan />} />
          <Route path="cpc"             element={<Bilan />} />
          <Route path="etic"            element={<Etic />} />
          <Route path="rapprochement"   element={<RapprochementBancaire />} />
          <Route path="lettrage"          element={<Lettrage />} />
          <Route path="balances"          element={<Balances />} />
          <Route path="situation"         element={<SituationFinanciere />} />
          <Route path="immobilisations"    element={<Immobilisations />} />
          <Route path="cloture"           element={<Cloture />} />
          <Route path="livre-inventaire"  element={<LivreInventaire />} />
          <Route path="parametres"      element={<Parametres />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
