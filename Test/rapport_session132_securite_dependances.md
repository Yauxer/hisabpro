# Contrôle ciblé des dépendances backend et JWT

Date : 6 octobre 2026. Ce contrôle ne constitue pas une validation de sécurité
globale ni une autorisation de mise en production.

## Modifications et vérifications exécutées

- `python-jose[cryptography]` : 3.3.0 → 3.5.0. Correctifs annoncés par le
  mainteneur pour CVE-2024-33663/33664 ; vérification locale du refus des clés
  publiques OpenSSH comme secret HMAC, des algorithmes inattendus, des JWT
  expirés/non signés et des en-têtes malformés.
- `python-multipart` : 0.0.12 → 0.0.31. Compatibilité d'un véritable upload
  FastAPI avec fichier et champ de formulaire vérifiée dans une API isolée.
- `python-dotenv` : 1.0.1 → 1.2.2. Lecture d'une configuration synthétique et
  interpolation testées sans écriture de fichier `.env`.
- JWT limités à 8 192 caractères ; profondeur JSON invalide traitée en 401.
- Les sessions récentes possèdent une version HMAC opaque du mot de passe.
  Un changement du mot de passe invalide ces sessions dans toutes les sociétés.
  Aucun hash de connexion ni mot de passe n'est exposé dans le token.
- Hashs nouveaux en `bcrypt_sha256` ; compatibilité des anciens hash bcrypt
  conservée, sans mutation automatique des comptes réels.

## Audit automatisé réellement exécuté

Commande, après installation locale de `pip-audit==2.9.0` :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m pip_audit --disable-pip --no-deps -r hisabpro-backend/requirements.txt -f json -o Test/rapport_session132_dependances_directes.json
```

Résultat après mise à jour : **1 avis connu sur 1 dépendance directe** ; code de
sortie 1 du scanner. Le résultat n'est pas présenté comme un audit vert.
L'audit précédent, après la seule mise à jour de jose, signalait 9 avis dans
3 dépendances directes. Ce mode ne résout pas les dépendances transitives.

Avis restant : GHSA-3qf3-8w2g-rqmx / CVE-2026-85394, confusion de clé publique
DER et secret HMAC dans python-jose ≤ 3.5.0 ; pas de version correctrice indiquée
par la source au moment du contrôle. HisabPro fournit explicitement une liste
d'un seul algorithme configuré à la vérification et utilise par défaut HS256
avec un secret privé. Ne pas configurer une clé publique comme `SECRET_KEY`, ni
mélanger algorithmes asymétriques et HMAC. La dépendance reste à surveiller.

## Limites encore à qualifier

- Les JWT historiques sans `pwd_version` gardent leur expiration initiale ;
  ils ne sont pas invalidés rétroactivement par le nouveau mécanisme.
- Les anciens hash bcrypt ont la troncation historique de 72 octets ; un
  changement explicite du mot de passe emploie le nouveau format. Aucune
  réparation ni changement silencieux d'un compte existant n'a été effectué.
- Audit transitif, politique de rotation des secrets, anti-abus au niveau
  infrastructure, reset de mot de passe et MFA restent à traiter avant une
  validation complète de production.
- Les tests PostgreSQL de cette session utilisent un cluster dédié éphémère,
  jamais l'instance comptable réelle. Le parcours utilisateur connecté sur
  l'installation finale reste à effectuer.

## Sources primaires consultées

- [Changelog python-jose](https://github.com/mpdavis/python-jose/blob/master/CHANGELOG.md)
- [Avis jose DER](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx)
- [Changelog python-multipart](https://github.com/Kludex/python-multipart/blob/main/CHANGELOG.md)
- [Avis python-dotenv](https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94)
- [Passlib bcrypt_sha256](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt_sha256.html)
