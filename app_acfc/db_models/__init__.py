"""
ACFC - Modèles de Données
==========================

Module définissant l'architecture des données de l'application ACFC.
Contient les modèles SQLAlchemy pour tous les modules métiers :

Modules couverts :
- Gestion des utilisateurs et authentification
- CRM (Client Relationship Management)
- Gestion des contacts (emails, téléphones, adresses)
- Comptabilité et plan comptable
- Gestion des commandes et facturation
- Catalogue produits et stocks

Technologies :
- SQLAlchemy ORM : Mapping objet-relationnel
- MariaDB/MySQL : Base de données relationnelle
- Connecteur MySQL : Driver de connexion optimisé
- Variables d'environnement : Configuration sécurisée

Architecture :
- Modèle en couches avec séparation des responsabilités
- Relations cohérentes entre entités métiers
- Contraintes d'intégrité référentielle
- Optimisations de performance (index, types de données)

Auteur : ACFC Development Team
Version : 2.0
"""
