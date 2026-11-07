-- Lettrage partiel explicite (959). Additive et rejouable ; 049 et 089 sont conservées.
-- Une ligne est déclarée partielle à sa création (colonne immuable comme le reste
-- de la ligne, cf. 089). Un code actif déséquilibré n'est admis que si TOUTES ses
-- lignes actives sont partielles ; sinon l'équilibre au centime reste exigé.
-- Les lettrages historiques (partiel = FALSE) restent soumis à la règle de 049.
-- À exécuter avec le rôle de migration, après sauvegarde.
BEGIN;
ALTER TABLE public.lettrages_comptables
    ADD COLUMN IF NOT EXISTS partiel boolean NOT NULL DEFAULT FALSE;

CREATE OR REPLACE FUNCTION hisabpro_check_lettrage_equilibre()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_sid INTEGER;
    v_code VARCHAR(10);
    v_nb INTEGER;
    v_debit NUMERIC(24,2);
    v_credit NUMERIC(24,2);
    v_tous_partiels BOOLEAN;
BEGIN
    v_sid := NEW.societe_id;
    v_code := NEW.code;

    SELECT COUNT(*),
           COALESCE(SUM(l.debit), 0)::NUMERIC(24,2),
           COALESCE(SUM(l.credit), 0)::NUMERIC(24,2),
           COALESCE(bool_and(lc.partiel), FALSE)
      INTO v_nb, v_debit, v_credit, v_tous_partiels
      FROM lettrages_comptables lc
      JOIN lignes_ecriture l ON l.id = lc.ligne_ecriture_id
     WHERE lc.societe_id = v_sid
       AND lc.code = v_code
       AND lc.actif = TRUE;

    IF v_nb = 0 THEN
        RETURN NEW;
    END IF;
    IF v_nb < 2 THEN
        RAISE EXCEPTION 'Le code % doit contenir au moins deux lignes actives', v_code USING ERRCODE='23514';
    END IF;
    IF v_debit <> v_credit THEN
        IF v_tous_partiels AND v_debit > 0 AND v_credit > 0 THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'Lettrage % déséquilibré : débit % / crédit %', v_code, v_debit, v_credit USING ERRCODE='23514';
    END IF;

    RETURN NEW;
END;
$$;
COMMIT;
