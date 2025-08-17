# Projet de Base de Données avec Interface

## Description

Ce projet est une application de gestion qui combine une base de données robuste et une interface utilisateur intuitive. Elle permet de gérer efficacement les **clients**, les **stocks**, les **commandes** et les **factures**.

## Fonctionnalités

- **Gestion des clients** : Ajout, modification, suppression et recherche de clients.
- **Gestion des stocks** : Suivi des produits, quantités disponibles et alertes de réapprovisionnement.
- **Gestion des commandes** : Création, suivi et mise à jour des commandes.
- **Gestion des factures** : Génération et archivage des factures.

## Technologies Utilisées

- **Backend** : [Nom du langage/framework] (ex. Python, Node.js)
- **Base de données** : [Nom du SGBD] (ex. MySQL, PostgreSQL)
- **Frontend** : [Nom du framework/bibliothèque] (ex. React, Angular)

## Installation

1. Clonez le dépôt :

    ```bash
    git clone https://github.com/votre-utilisateur/votre-projet.git
    ```

2. Installez les dépendances :

    ```bash
    npm install
    ```

3. Configurez la base de données dans le fichier `config/database.json`.

4. Lancez l'application :

    ```bash
    npm start
    ```

## Contribution

Les contributions sont les bienvenues ! Veuillez soumettre une *pull request* ou ouvrir une *issue* pour discuter des changements.

## Licence

Ce projet est sous licence Apache 2.0.

## Auteur

Rémi Verschuur

## Intégrer Bootstrap localement

Ce projet contient des fichiers placeholder pour Bootstrap dans `app_acfc/statics/vendor/bootstrap` afin de garder le dépôt léger.

Pour remplacer par les vrais fichiers Bootstrap (CSS et JS) :

1. Télécharge la distribution officielle depuis https://getbootstrap.com et copie `bootstrap.min.css` dans `app_acfc/statics/vendor/bootstrap/css/` et `bootstrap.bundle.min.js` dans `app_acfc/statics/vendor/bootstrap/js/`.

2. Exemple PowerShell pour télécharger la version 5.3 directement (exécute depuis la racine du projet) :

```powershell
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" -OutFile "app_acfc/statics/vendor/bootstrap/css/bootstrap.min.css"
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js" -OutFile "app_acfc/statics/vendor/bootstrap/js/bootstrap.bundle.min.js"
```

3. Modifie `app_acfc/statics/css/custom.css` pour tes overrides afin de ne pas éditer `bootstrap.min.css` directement.

Après ça, recharge ton application Flask et les styles/JS locaux seront utilisés.
