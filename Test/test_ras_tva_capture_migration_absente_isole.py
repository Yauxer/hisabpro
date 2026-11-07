"""Ancienne installation : routes existantes utilisables,099 jamais auto-appliquée."""
from contextlib import closing
from test_e2e_facturation_isole import application
from test_ras_tva_capture_isole import preparer, demande
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier


def test_571_absence_099_explicitement_signalee_sans_ddl(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api)
        avant=donnees_metier(application)
        lecture=ok(api.get(f"/api/reglements/{r['id']}/ras-tva"))
        assert lecture=={'disponible':False,'migration_requise':'099_ras_tva_details.sql','dossier':None}
        refus=api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=demande())
        assert refus.status_code==409 and '099' in refus.text
        assert donnees_metier(application)==avant
