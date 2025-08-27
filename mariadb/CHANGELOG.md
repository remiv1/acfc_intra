# Changelog

## [1.1.0] - 2025-08-28

- Ajout des colonnes `ref_auto` et `des_auto` dans la table `21_catalogue` (gérées par un trigger).
- Modification de `updated_at` pour utiliser `CURRENT_TIMESTAMP`.
- Modification du modèle python et SQLAlchemy pour refléter les changements de la base de données.

## [1.0.0] - 2025-08-20

- Initialisation du projet avec les tables `99_users`, `21_catalogue`, etc.
