-- Patch 101 — Réparation append-only de l'IS 2026 clôturé avant comptabilisation
--
-- Contexte : certaines bases de recette ont clôturé 2026 puis confirmé la
-- liquidation IS avant que HisabPro ne comptabilise automatiquement l'impôt
-- courant. La liquidation fiscale est immuable et les écritures définitives le
-- sont également : ce patch NE MODIFIE donc aucune écriture existante et NE
-- réécrit pas clotures_exercice.
--
-- Pour chaque société concernée, uniquement si toutes les conditions de sûreté
-- sont réunies, il ajoute :
--   1) OD 2026 : charge d'impôt 6701 (ou CM 6705) / dette 4453 ;
--   2) CL 2026 : correction technique de clôture via 8800 et 1191/1199 ;
--   3) AN 2027 : correction des à-nouveaux résultat / 4453.
--
-- Le trigger de période est désactivé uniquement pendant les INSERT de cette
-- réparation contrôlée, car 2026 est déjà définitivement clôturé. Tous les
-- autres garde-fous (numérotation, immutabilité, journal CL, équilibre, audit)
-- restent actifs.

BEGIN;

DO $$
DECLARE
    r RECORD;
    v_compte_charge VARCHAR(10);
    v_montant NUMERIC(18,2);
    v_resultat_ancien NUMERIC(18,2);
    v_resultat_nouveau NUMERIC(18,2);
    v_resultat_economique NUMERIC(18,2);
    v_date_fin DATE;
    v_date_debut_suiv DATE;
    v_statut_suiv VARCHAR(20);
    v_id_is INTEGER;
    v_id_cl INTEGER;
    v_id_an INTEGER;
    v_nb_refs INTEGER;
    v_nb_impot_existant INTEGER;
BEGIN
    -- Pré-contrôles AVANT de lever ponctuellement le verrou de période.
    FOR r IN
        SELECT liq.societe_id,
               liq.exercice,
               liq.impot_du,
               liq.nature_impot,
               liq.confirmee_par,
               cl.resultat_net AS resultat_cloture
          FROM fiscal_liquidations_is liq
          JOIN clotures_exercice cl
            ON cl.societe_id = liq.societe_id
           AND cl.exercice = liq.exercice
         WHERE liq.exercice = 2026
           AND liq.impot_du > 0
         ORDER BY liq.societe_id
    LOOP
        v_montant := ROUND(r.impot_du::numeric, 2);
        v_compte_charge := CASE WHEN r.nature_impot = 'CM' THEN '6705' ELSE '6701' END;
        v_resultat_ancien := ROUND(r.resultat_cloture::numeric, 2);
        v_resultat_nouveau := ROUND(v_resultat_ancien - v_montant, 2);

        SELECT COUNT(*) INTO v_nb_refs
          FROM ecritures
         WHERE societe_id = r.societe_id
           AND reference IN (
                'REGUL-IS-2026',
                'CLOTURE-2026-CORR-IS',
                'AN-CORR-IS-2027'
           );

        IF v_nb_refs = 3 THEN
            RAISE NOTICE 'Patch 101 : société %, réparation IS 2026 déjà présente — aucune action.', r.societe_id;
            CONTINUE;
        ELSIF v_nb_refs <> 0 THEN
            RAISE EXCEPTION
                'Patch 101 interrompu pour la société % : réparation partielle détectée (% référence(s) sur 3). Vérification manuelle requise.',
                r.societe_id, v_nb_refs;
        END IF;

        SELECT ex.date_fin
          INTO v_date_fin
          FROM exercices_comptables ex
         WHERE ex.societe_id = r.societe_id
           AND ex.annee = 2026
           AND ex.statut = 'cloture'
         LIMIT 1;
        IF v_date_fin IS NULL THEN
            RAISE EXCEPTION 'Patch 101 : exercice comptable 2026 clôturé introuvable pour la société %.', r.societe_id;
        END IF;

        SELECT ex.date_debut, ex.statut
          INTO v_date_debut_suiv, v_statut_suiv
          FROM exercices_comptables ex
         WHERE ex.societe_id = r.societe_id
           AND ex.annee = 2027
         LIMIT 1;
        IF v_date_debut_suiv IS NULL THEN
            RAISE EXCEPTION 'Patch 101 : exercice 2027 introuvable pour la société % ; correction des à-nouveaux impossible.', r.societe_id;
        END IF;
        IF v_statut_suiv = 'cloture' THEN
            RAISE EXCEPTION 'Patch 101 : exercice 2027 déjà clôturé pour la société % ; aucune réparation automatique en cascade.', r.societe_id;
        END IF;

        -- Sûreté : aucune écriture économique 6701/6705 ne doit déjà exister.
        SELECT COUNT(*) INTO v_nb_impot_existant
          FROM ecritures e
          JOIN lignes_ecriture l ON l.ecriture_id = e.id
         WHERE e.societe_id = r.societe_id
           AND e.exercice = 2026
           AND e.est_validee = TRUE
           AND COALESCE(e.source, '') <> 'cloture'
           AND e.journal::text <> 'CL'
           AND COALESCE(e.reference, '') NOT LIKE 'CLOTURE-2026%'
           AND (l.compte LIKE '6701%' OR l.compte LIKE '6705%')
           AND ABS(COALESCE(l.debit,0) - COALESCE(l.credit,0)) > 0.005;
        IF v_nb_impot_existant > 0 THEN
            RAISE EXCEPTION
                'Patch 101 : société % possède déjà % mouvement(s) économique(s) 6701/6705 en 2026. Réparation automatique refusée.',
                r.societe_id, v_nb_impot_existant;
        END IF;

        -- Le résultat figé à l'ancienne clôture doit encore recouper exactement
        -- les écritures économiques avant IS ; sinon on ne peut pas attribuer
        -- l'écart au seul impôt oublié.
        SELECT ROUND(COALESCE(SUM(
                   CASE
                     WHEN l.compte LIKE '7%' THEN COALESCE(l.credit,0) - COALESCE(l.debit,0)
                     WHEN l.compte LIKE '6%' THEN -(COALESCE(l.debit,0) - COALESCE(l.credit,0))
                     ELSE 0
                   END
               ),0)::numeric, 2)
          INTO v_resultat_economique
          FROM ecritures e
          JOIN lignes_ecriture l ON l.ecriture_id = e.id
         WHERE e.societe_id = r.societe_id
           AND e.exercice = 2026
           AND e.est_validee = TRUE
           AND e.journal::text <> 'CL'
           AND COALESCE(e.source, '') <> 'cloture'
           AND COALESCE(e.reference, '') NOT LIKE 'CLOTURE-2026%';

        IF ABS(v_resultat_economique - v_resultat_ancien) > 0.01 THEN
            RAISE EXCEPTION
                'Patch 101 : société % — résultat économique 2026 (%.2f) différent de la clôture historique (%.2f). Réparation automatique refusée.',
                r.societe_id, v_resultat_economique, v_resultat_ancien;
        END IF;
    END LOOP;
END $$;

-- Seul ce garde-fou est levé temporairement : l'insertion sur 2026 clôturé (et
-- l'AN 2027 éventuellement encore en période à venir) serait sinon refusée.
ALTER TABLE ecritures DISABLE TRIGGER trg_hisabpro_verifier_periode_ecriture;

DO $$
DECLARE
    r RECORD;
    v_compte_charge VARCHAR(10);
    v_montant NUMERIC(18,2);
    v_resultat_ancien NUMERIC(18,2);
    v_resultat_nouveau NUMERIC(18,2);
    v_date_fin DATE;
    v_date_debut_suiv DATE;
    v_id_is INTEGER;
    v_id_cl INTEGER;
    v_id_an INTEGER;
    v_nb_refs INTEGER;
    v_libelle TEXT;
BEGIN
    FOR r IN
        SELECT liq.societe_id,
               liq.exercice,
               liq.impot_du,
               liq.nature_impot,
               liq.confirmee_par,
               cl.resultat_net AS resultat_cloture
          FROM fiscal_liquidations_is liq
          JOIN clotures_exercice cl
            ON cl.societe_id = liq.societe_id
           AND cl.exercice = liq.exercice
         WHERE liq.exercice = 2026
           AND liq.impot_du > 0
         ORDER BY liq.societe_id
    LOOP
        SELECT COUNT(*) INTO v_nb_refs
          FROM ecritures
         WHERE societe_id = r.societe_id
           AND reference IN ('REGUL-IS-2026','CLOTURE-2026-CORR-IS','AN-CORR-IS-2027');
        IF v_nb_refs = 3 THEN
            CONTINUE;
        END IF;

        SELECT date_fin INTO v_date_fin
          FROM exercices_comptables
         WHERE societe_id = r.societe_id AND annee = 2026
         LIMIT 1;
        SELECT date_debut INTO v_date_debut_suiv
          FROM exercices_comptables
         WHERE societe_id = r.societe_id AND annee = 2027
         LIMIT 1;

        v_montant := ROUND(r.impot_du::numeric, 2);
        v_compte_charge := CASE WHEN r.nature_impot = 'CM' THEN '6705' ELSE '6701' END;
        v_resultat_ancien := ROUND(r.resultat_cloture::numeric, 2);
        v_resultat_nouveau := ROUND(v_resultat_ancien - v_montant, 2);
        v_libelle := CASE WHEN r.nature_impot = 'CM'
            THEN 'Régularisation cotisation minimale — exercice 2026'
            ELSE 'Régularisation impôt sur les bénéfices — exercice 2026'
        END;

        PERFORM set_config('hisabpro.audit_actor_id', COALESCE(r.confirmee_par::text, ''), true);
        PERFORM set_config('hisabpro.audit_motif',
            'Patch 101 — comptabilisation append-only de l''impôt courant omis avant clôture 2026', true);

        -- 1) Écriture économique d'impôt : 6701/6705 -> 4453.
        INSERT INTO ecritures (
            societe_id, date, journal, libelle, reference, date_piece,
            exercice, source, est_validee, validee_par
        ) VALUES (
            r.societe_id, v_date_fin, 'OD', v_libelle, 'REGUL-IS-2026', v_date_fin,
            2026, 'fiscalite_is', FALSE, NULL
        ) RETURNING id INTO v_id_is;

        INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
        VALUES
            (v_id_is, v_compte_charge, v_libelle, v_montant, 0),
            (v_id_is, '4453', v_libelle, 0, v_montant);

        UPDATE ecritures
           SET est_validee = TRUE,
               date_validation = NOW(),
               validee_par = r.confirmee_par
         WHERE id = v_id_is;

        -- 2) Correction technique de clôture : on solde la nouvelle charge via
        -- 8800 puis on ajuste le compte de résultat sans toucher à CLOTURE-2026.
        INSERT INTO ecritures (
            societe_id, date, journal, libelle, reference, date_piece,
            exercice, source, est_validee, validee_par
        ) VALUES (
            r.societe_id, v_date_fin, 'CL',
            'Correction de clôture — IS 2026', 'CLOTURE-2026-CORR-IS', v_date_fin,
            2026, 'cloture', FALSE, NULL
        ) RETURNING id INTO v_id_cl;

        INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
        VALUES
            (v_id_cl, '8800', 'Transfert impôt courant au résultat', v_montant, 0),
            (v_id_cl, v_compte_charge, 'Soldage impôt courant', 0, v_montant);

        IF v_resultat_ancien > 0 AND v_resultat_nouveau >= 0 THEN
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_cl, '1191', 'Correction résultat bénéficiaire après IS', v_montant, 0),
                (v_id_cl, '8800', 'Correction résultat bénéficiaire après IS', 0, v_montant);
        ELSIF v_resultat_ancien <= 0 THEN
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_cl, '1199', 'Correction perte après IS', v_montant, 0),
                (v_id_cl, '8800', 'Correction perte après IS', 0, v_montant);
        ELSE
            -- Le montant d'IS transforme un bénéfice historique en perte.
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_cl, '1191', 'Annulation bénéfice historique', v_resultat_ancien, 0),
                (v_id_cl, '1199', 'Constatation perte après IS', -v_resultat_nouveau, 0),
                (v_id_cl, '8800', 'Correction résultat après IS', 0, v_montant);
        END IF;

        UPDATE ecritures
           SET est_validee = TRUE,
               date_validation = NOW(),
               validee_par = r.confirmee_par
         WHERE id = v_id_cl;

        -- 3) Correction des à-nouveaux 2027 : même dette fiscale, résultat N
        -- corrigé. L'écriture AN d'origine reste intacte.
        INSERT INTO ecritures (
            societe_id, date, journal, libelle, reference, date_piece,
            exercice, source, est_validee, validee_par
        ) VALUES (
            r.societe_id, v_date_debut_suiv, 'AN',
            'Correction à-nouveaux — IS 2026', 'AN-CORR-IS-2027', v_date_debut_suiv,
            2027, 'cloture', FALSE, NULL
        ) RETURNING id INTO v_id_an;

        IF v_resultat_ancien > 0 AND v_resultat_nouveau >= 0 THEN
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_an, '1191', 'Correction report résultat 2026 après IS', v_montant, 0),
                (v_id_an, '4453', 'Report dette IS 2026', 0, v_montant);
        ELSIF v_resultat_ancien <= 0 THEN
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_an, '1199', 'Correction report perte 2026 après IS', v_montant, 0),
                (v_id_an, '4453', 'Report dette IS 2026', 0, v_montant);
        ELSE
            INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
            VALUES
                (v_id_an, '1191', 'Annulation report bénéfice 2026', v_resultat_ancien, 0),
                (v_id_an, '1199', 'Report perte 2026 après IS', -v_resultat_nouveau, 0),
                (v_id_an, '4453', 'Report dette IS 2026', 0, v_montant);
        END IF;

        UPDATE ecritures
           SET est_validee = TRUE,
               date_validation = NOW(),
               validee_par = r.confirmee_par
         WHERE id = v_id_an;

        RAISE NOTICE
            'Patch 101 : société % réparée — impôt %.2f sur %, résultat %.2f -> %.2f.',
            r.societe_id, v_montant, v_compte_charge, v_resultat_ancien, v_resultat_nouveau;
    END LOOP;
END $$;

ALTER TABLE ecritures ENABLE TRIGGER trg_hisabpro_verifier_periode_ecriture;

COMMIT;
