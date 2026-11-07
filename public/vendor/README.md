# Polices locales de HisabPro

Inter (graisses400,500,600 et sept sous-ensembles) et Tabler Icons2.47.0
sont servis par HisabPro. Aucune requête CDN n’est nécessaire au chargement.
Tabler conserve la version et les valeurs visuelles des glyphes du CSS auparavant
chargé. Les chemins des fontes utilisent les fichiers locaux WOFF2. Les
déclarations `content` des icônes ajoutent une alternative textuelle vide
(` / ""`) : ces glyphes décoratifs ne polluent plus le nom accessible des
boutons et liens. Leur texte visible ou leur `aria-label` reste le nom du
contrôle. Les contrôles composés seulement d’une icône doivent conserver
leur libellé accessible explicite. Cette adaptation est testée dans Edge
aux largeurs bureau et mobile, sans changer les sélecteurs des scénarios.

Licences incluses : Inter SIL Open Font License dans `inter/OFL.txt` ;
Tabler MIT dans `tabler/LICENSE.txt`. Sources des projets :
[Inter dans Google Fonts](https://github.com/google/fonts/tree/main/ofl/inter),
[Tabler Icons](https://github.com/tabler/tabler-icons).

`MANIFEST.json` consigne les URL de téléchargement, tailles et SHA256 des
fichiers effectivement livrés, après adaptation des chemins CSS. Les fontes
ne sont pas téléchargées au démarrage de l’application. Aucun taux métier,
document comptable ou donnée utilisateur n’est contenu dans ces fichiers.
