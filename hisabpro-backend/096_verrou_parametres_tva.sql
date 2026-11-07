-- Après095. Renforce094 sans modifier son fichier ni les données existantes.
-- Un exercice existant reste stable pendant la mutation SQL de ses paramètres.
BEGIN;
CREATE OR REPLACE FUNCTION public.hisabpro_proteger_parametres_tva_clotures()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
    ancien_societe INTEGER;
    ancien_exercice INTEGER;
    nouveau_societe INTEGER;
    nouveau_exercice INTEGER;
    exercice_verrouille RECORD;
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        ancien_societe:=OLD.societe_id;
        ancien_exercice:=OLD.exercice;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        nouveau_societe:=NEW.societe_id;
        nouveau_exercice:=NEW.exercice;
    END IF;
    -- Verrou partagé : empêche le changement de statut jusqu'au commit tout
    -- en restant compatible avec les autres lecteurs du statut (API incluse).
    -- Une relocation propriétaire protège les deux périmètres dans le même ordre.
    FOR exercice_verrouille IN
        SELECT e.statut FROM public.exercices_comptables e
        WHERE (e.societe_id=ancien_societe AND e.annee=ancien_exercice)
           OR (e.societe_id=nouveau_societe AND e.annee=nouveau_exercice)
        ORDER BY e.societe_id,e.annee
        FOR SHARE
    LOOP
        IF exercice_verrouille.statut='cloture' THEN
            RAISE EXCEPTION 'Exercice clôturé : paramètres TVA verrouillés.'
                USING ERRCODE='23514', CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END LOOP;
    -- Conserver le refus094, notamment la trace de clôture sans ligne exercice.
    IF TG_OP IN ('UPDATE','DELETE') THEN
        IF public.hisabpro_tva_exercice_clos(OLD.societe_id,OLD.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.', OLD.exercice
                USING ERRCODE='23514', CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') THEN
        IF public.hisabpro_tva_exercice_clos(NEW.societe_id,NEW.exercice) THEN
            RAISE EXCEPTION 'Exercice % clôturé : paramètres TVA verrouillés.', NEW.exercice
                USING ERRCODE='23514', CONSTRAINT='ck_tva_parametres_exercice_ouvert';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;
-- CREATE OR REPLACE conserve le propriétaire, le trigger et ses ACL existantes.
-- Aucun nouveau privilège, taux ou montant n'est installé par096.
COMMIT;
