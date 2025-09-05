# Changelog

## [1.2.0] - 2025-09-05

- Ajout des métadonnées :
  - `created_by` dans les tables :
    - `01_clients`
    - `02_mails`
    - `03_telephones`
    - `04_adresses`
    - `11_commandes`
    - `13_factures`
    - `21_catalogue`
    - `31_operations`
    - `32_ventilations`
    - `33_documents`
  - `created_at` dans les tables :
    - `02_mails`
    - `03_telephones`
    - `11_commandes`
    - `13_factures`
    - `14_expeditions`
    - `31_operations`
    - `32_ventilations`
    - `33_documents`
  - `modified_at` dans les tables :
    - `01_clients`
    - `02_mails`
    - `03_telephones`
    - `04_adresses`
    - `11_commandes`
    - `12_devises_factures` (anciennement `updated_at`)
    - `14_expeditions`
    - `21_catalogue`
    - `31_operations`
    - `32_ventilations`
    - `33_documents`
  - `modified_by` dans les tables :
    - `01_clients`
    - `02_mails`
    - `03_telephones`
    - `04_adresses`
    - `11_commandes`
    - `12_devises_factures` (anciennement `updated_by`)
    - `14_expeditions`
    - `21_catalogue`
    - `31_operations`
    - `32_ventilations`
    - `33_documents`
  - `is_inactive` dans les tables :
    - `02_mails`
    - `03_telephones`
    - `04_adresses`
    - `31_operations`
    - `32_ventilations`
    - `33_documents`
- Modification des colonnes `created_at` pour utiliser `func.now()` au lieu de `func.now()`.
- Modification des colonnes `modified_at` pour utiliser `func.now()` au lieu de `func.now()`.
- Modification du modèle python et SQLAlchemy pour refléter les changements de la base de données.

## [1.1.0] - 2025-08-28

- Ajout des colonnes `ref_auto` et `des_auto` dans la table `21_catalogue` (gérées par un trigger).
- Modification de `updated_at` pour utiliser `CURRENT_TIMESTAMP`.
- Modification du modèle python et SQLAlchemy pour refléter les changements de la base de données.

## [1.0.0] - 2025-08-20

- Initialisation du projet avec les tables `99_users`, `21_catalogue`, etc.
