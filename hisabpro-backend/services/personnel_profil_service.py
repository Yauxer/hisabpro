"""Confinement fermé du profil Personnel seul, après résolution du rôle en base."""
import re
from fastapi import HTTPException
from sqlalchemy import text

GET_COMMUNS={'/api/auth/me','/api/societes/mes-societes','/api/employes/securite/acces'}
LECTURES=re.compile(r'/api/employes/personnel(?:/(?:contexte|options|demandes(?:/[1-9][0-9]*)?|[1-9][0-9]*(?:/historique)?))?/?\Z')
MUTATIONS=re.compile(r'/api/employes/personnel(?:/reprises|/[1-9][0-9]*/modifications|/demandes/[1-9][0-9]*/(?:soumettre|approuver|rejeter))?/?\Z')
SWITCH=re.compile(r'/api/societes/switcher/[1-9][0-9]*/?\Z')
COFFRE_LECTURE=re.compile(r'/api/employes/personnel/coffre(?:/[1-9][0-9]*/(?:pieces(?:/[1-9][0-9]*)?|banque/[1-9][0-9]*/reveler))?/?\Z')
COFFRE_DEPOT=re.compile(r'/api/employes/personnel/coffre/[1-9][0-9]*/pieces/?\Z')
PAIE_LECTURE=re.compile(r'/api/employes/personnel/elements(?:/[1-9][0-9]*)?/?\Z')
PAIE_MUTATION=re.compile(r'/api/employes/personnel/elements(?:/[1-9][0-9]*/versions|/versions/[1-9][0-9]*/(?:approuver|rejeter|apercu))?/?\Z')
VARIABLES_LECTURE=re.compile(r'/api/employes/personnel/elements/variables(?:/(?:options|[1-9][0-9]*))?/?\Z')
VARIABLES_MUTATION=re.compile(r'/api/employes/personnel/elements/variables(?:/[1-9][0-9]*/(?:soumettre|annuler|approuver|rejeter))?/?\Z')
TRAITEMENT_LECTURE=re.compile(r'/api/employes/personnel/traitement(?:/options|/simulations/[1-9][0-9]*|/campagnes/[1-9][0-9]*/historique)?/?\Z')
SOCIAL_LECTURE=re.compile(r'/api/employes/personnel/social(?:/[1-9][0-9]*)?/?\Z')
SOCIAL_MUTATION=re.compile(r'/api/employes/personnel/social(?:/[1-9][0-9]*/versions|/versions/[1-9][0-9]*/(?:approuver|rejeter))?/?\Z')
SOCIAL_SIMULATION=re.compile(r'/api/employes/personnel/social/simulations(?:/options|/[1-9][0-9]*)?/?\Z')
FRAIS_ANNUELS_LECTURE=re.compile(r'/api/employes/personnel/fiscalite/frais-annuels(?:/options|/[1-9][0-9]*)?/?\Z')
BASES_FISCALES_LECTURE=re.compile(r'/api/employes/personnel/fiscalite/preparations(?:/options|/[1-9][0-9]*)?/?\Z')
IR_ANNUEL_LECTURE=re.compile(r'/api/employes/personnel/fiscalite(?:/referentiel|/[1-9][0-9]*)?/?\Z')
IR_ANNUEL_EXPORT=re.compile(r'/api/employes/personnel/fiscalite/[1-9][0-9]*/export/(?:pdf|xlsx)/?\Z')
IR_MENSUEL_LECTURE=re.compile(r'/api/employes/personnel/fiscalite/mensuel(?:/[1-9][0-9]*)?/?\Z')
# 968 : bulletins et avances ; comptabilisation et paiements restent réservés à la comptabilité.
PAIE968_LECTURE=re.compile(r'/api/employes/personnel/paie/(?:bulletins(?:/apercu|/[1-9][0-9]*)?|etats|salaries|avances)/?\Z')
PAIE968_MUTATION=re.compile(r'/api/employes/personnel/paie/(?:bulletins(?:/[1-9][0-9]*/annuler)?|avances(?:/[1-9][0-9]*/annuler)?|calculer-mois)/?\Z')

def exiger_chemin_personnel(role,request):
    if role!='personnel':return
    chemin=request.url.path if request is not None else ''
    methode=request.method if request is not None else ''
    if methode=='GET' and FRAIS_ANNUELS_LECTURE.fullmatch(chemin):return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/fiscalite/frais-annuels':return
    if methode=='GET' and BASES_FISCALES_LECTURE.fullmatch(chemin):return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/fiscalite/preparations':return
    if methode=='GET' and IR_ANNUEL_LECTURE.fullmatch(chemin):return
    if methode=='GET' and IR_ANNUEL_EXPORT.fullmatch(chemin):return
    if methode=='GET' and IR_MENSUEL_LECTURE.fullmatch(chemin):return
    if methode=='GET' and PAIE968_LECTURE.fullmatch(chemin):return
    if methode=='POST' and PAIE968_MUTATION.fullmatch(chemin):return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/fiscalite/mensuel':return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/fiscalite':return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/fiscalite/depuis-frais-annuels':return
    if methode=='GET' and SOCIAL_SIMULATION.fullmatch(chemin):return
    if methode=='POST' and chemin.rstrip('/')=='/api/employes/personnel/social/simulations':return
    if methode=='GET' and SOCIAL_LECTURE.fullmatch(chemin):return
    if methode=='POST' and SOCIAL_MUTATION.fullmatch(chemin):return
    if methode=='GET' and (chemin.rstrip('/') in GET_COMMUNS or LECTURES.fullmatch(chemin) or COFFRE_LECTURE.fullmatch(chemin) or PAIE_LECTURE.fullmatch(chemin) or VARIABLES_LECTURE.fullmatch(chemin) or TRAITEMENT_LECTURE.fullmatch(chemin)):return
    if methode=='POST' and (chemin.rstrip('/')=='/api/auth/mot-de-passe' or MUTATIONS.fullmatch(chemin) or SWITCH.fullmatch(chemin) or COFFRE_DEPOT.fullmatch(chemin) or PAIE_MUTATION.fullmatch(chemin) or VARIABLES_MUTATION.fullmatch(chemin) or chemin.rstrip('/')=='/api/employes/personnel/traitement/simulations'):return
    raise HTTPException(403,'Ce profil est réservé au Personnel ; accès aux autres modules interdit.')

def verifier_installation(db):
    definition=db.scalar(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
      "WHERE conrelid='public.utilisateurs'::regclass AND conname='ck_utilisateurs_role_hisabpro'")) if db.bind.dialect.name=='postgresql' else None
    if not definition or "'personnel'" not in definition:
        raise HTTPException(503,'Installer la migration109 avant d’attribuer le profil Personnel seul.')
