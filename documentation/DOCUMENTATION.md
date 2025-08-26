# ACFC - Documentation Technique Complète (au 21/08/2025)

## 📋 Vue d'ensemble

**ACFC** (Accounting, Customer Relationship Management, Billing & Stock Management) est une application web d'entreprise intégrée développée en Python Flask. Elle fournit une solution complète pour la gestion d'entreprise incluant la comptabilité, la gestion client (CRM), la facturation et la gestion des stocks pour l'entreprise ACFC.

### 🎯 Modules Métiers

- **👥 CRM (Clients)** : Gestion de la relation client, contacts, historique
- **📦 Catalogue** : Gestion des produits et services
- **💼 Commercial** : Devis, commandes, suivi commercial
- **💰 Comptabilité** : Facturation, plan comptable, écritures
- **📊 Stocks** : Inventaire, mouvements, valorisation

## 🏗️ Architecture Technique

### Stack Technologique

```ini
Frontend:  HTML5 + CSS3 + JavaScript + Jinja2
Backend:   Python 3.12 + Flask + SQLAlchemy
Database:  MariaDB (données) + MongoDB (logs)
Server:    Waitress WSGI + Nginx (reverse proxy)
Deploy:    Docker + Docker Compose
```

### Architecture en Couches

```ini
┌─────────────────────────────────────────┐
│           Nginx (Reverse Proxy)        │
├─────────────────────────────────────────┤
│         Flask Application (Port 5000)   │
│  ┌─────────────────────────────────────┐ │
│  │        Blueprints (Modules)        │ │
│  │  ┌─────┬─────┬─────┬─────┬─────┐   │ │
│  │  │ CRM │Cat. │Com. │Comp.│Stock│   │ │
│  │  └─────┴─────┴─────┴─────┴─────┘   │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │      Services (Security, etc.)     │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │        Models (SQLAlchemy)         │ │
│  └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│     MariaDB (Port 3306) │ MongoDB      │
│     Données métiers     │ (Port 27017) │
│                         │ Logs système │
└─────────────────────────────────────────┘
```

## 📁 Structure du Projet

```ini
acfc_base/
├── app_acfc/                    # Application principale
│   ├── application.py           # Point d'entrée Flask
│   ├── modeles.py              # Modèles SQLAlchemy
│   ├── services.py             # Services (sécurité, etc.)
│   ├── contextes_bp/           # Modules métiers (Blueprints)
│   │   ├── clients.py          # Module CRM
│   │   ├── catalogue.py        # Module Catalogue
│   │   ├── commercial.py       # Module Commercial
│   │   ├── comptabilite.py     # Module Comptabilité
│   │   └── stocks.py           # Module Stocks
│   ├── templates/              # Templates HTML
│   └── statics/                # Ressources statiques (CSS/JS)
├── mariadb/                    # Configuration base de données
│   ├── dockerfile.mariadb      # Dockerfile MariaDB
│   └── init_db.sql            # Script d'initialisation
├── nginx/                      # Configuration reverse proxy
├── mongo/                      # Configuration MongoDB
├── docker-compose.yml          # Orchestration des services
└── requirements-app.txt        # Dépendances Python
```

## 🔐 Sécurité Implémentée

### Authentification

- **Hachage Argon2** : Protection des mots de passe (résistant GPU)
- **Sessions sécurisées** : Stockage filesystem + chiffrement
- **Protection force brute** : Compteur d'erreurs + verrouillage
- **Expiration automatique** : Timeout 30 minutes

### Configuration Sécurisée

```python
# services.py - Configuration Argon2
PasswordHasher(
    time_cost=4,        # 4 itérations
    memory_cost=2**16,  # 64KB mémoire (anti-GPU)
    parallelism=3,      # 3 threads parallèles
    hash_len=32,        # Hash 256 bits
    salt_len=16         # Sel 128 bits
)
```

### Sessions

- **HTTPOnly cookies** : Protection XSS
- **Signature cryptographique** : Intégrité des données
- **Stockage filesystem** : Plus sécurisé que les cookies
- **Clé secrète** : Via variables d'environnement

## 🗄️ Modèle de Données

### Entités Principales

```sql
-- Utilisateurs et sécurité
99_users (id, pseudo, sha_mdp, email, role, is_active...)

-- CRM - Gestion clients
01_clients (id, type_client, id_part, id_pro, created_at...)
011_part (id, prenom, nom, date_naissance...)
012_pro (id, raison_sociale, siren, rna...)

-- Contacts
02_mail (id, id_client, type_mail, mail, is_principal...)
03_telephone (id, id_client, type_telephone, indicatif, telephone...)
04_adresse (id, id_client, type_adresse, adresse_complete...)

-- Commercial
11_commandes (id, id_client, montant_ht, tva, statut...)
12_lignes_commande (id, id_commande, id_produit, quantite, prix...)

-- Comptabilité
30_pcg (compte, libelle, type_compte...)
31_operations (id, date_operation, libelle, montant...)

-- Stocks
20_produits (id, reference, designation, prix_unitaire...)
21_mouvements_stock (id, id_produit, type_mouvement, quantite...)
```

### Relations Clés

- **Client polymorphe** : Part OU Pro selon type_client
- **Contacts multiples** : N emails/téléphones par client
- **Traçabilité complète** : created_at, updated_at sur toutes les entités
- **Soft delete** : is_active pour conservation historique

## 🐳 Déploiement Docker

### Services Déployés

```yaml
# docker-compose.yml
services:
  acfc-app:      # Application Flask (port 5000)
  acfc-nginx:    # Reverse proxy (port 80/443)
  acfc-db:       # MariaDB (port 3306)
  acfc-logs:     # MongoDB (port 27017)
```

### Variables d'Environnement (.env)

```bash
# Base de données
DB_HOST=localhost
DB_PORT=3306
DB_NAME=******
DB_USER=******
DB_PASSWORD=mot_de_passe_securise
DB_ROOT_PASSWORD=mot_de_passe_root_securise

# Sessions
SESSION_PASSKEY=cle_secrete_tres_longue_et_aleatoire

# MongoDB
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=mot_de_passe_mongo
MONGO_INITDB_DATABASE=******
```

### Commandes de Déploiement

```bash
# Développement
docker-compose up -d

# Production (avec rebuild)
docker-compose up -d --build

# Logs en temps réel
docker-compose logs -f

# Arrêt propre
docker-compose down

# Nettoyage complet (ATTENTION: perte de données)
docker-compose down -v
```

## 📊 Monitoring et Logs

### Health Checks

- **MariaDB** : Vérification connexion SQL
- **MongoDB** : Test ping base de données
- **Application** : Endpoint de santé (à implémenter)

### Logging

```python
# Configuration recommandée
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/acfc.log'),
        logging.StreamHandler()
    ]
)
```

## 🔧 Configuration de Développement

### Prérequis

- Python 3.12+
- Docker & Docker Compose
- Git

### Installation Locale

```bash
# Clone du projet
git clone <repository>
cd acfc_base

# Environnement virtuel Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installation des dépendances
pip install -r requirements-app.txt

# Configuration environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Démarrage des services
docker-compose up -d

# Test de l'application
curl http://localhost:5000
```

### Debug Mode

```python
# application.py - Mode développement
if __name__ == '__main__':
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True,        # Rechargement automatique
        use_reloader=True  # Surveillance des fichiers
    )
```

## 📈 Évolutions Futures

### Fonctionnalités Prévues

- [ ] **API REST complète** : Documentation OpenAPI/Swagger
- [ ] **Authentification OAuth2** : SSO entreprise
- [ ] **Tableau de bord** : Métriques temps réel
- [ ] **Export avancé** : PDF, Excel, CSV
- [ ] **Notifications** : Email, SMS, push
- [ ] **Audit trail** : Traçabilité complète des actions
- [ ] **Multi-tenant** : Support plusieurs entreprises

### Optimisations Techniques

- [ ] **Cache Redis** : Performance requêtes fréquentes
- [ ] **Migrations Alembic** : Évolution schéma base
- [ ] **Tests automatisés** : Coverage >80%
- [ ] **CI/CD Pipeline** : GitLab/GitHub Actions
- [ ] **Monitoring APM** : New Relic, DataDog
- [ ] **Load balancing** : Haute disponibilité

## 🤝 Contribution

### Standards de Code

- **PEP 8** : Style Python
- **Type hints** : Annotations obligatoires
- **Docstrings** : Documentation des fonctions
- **Tests unitaires** : Pytest

### Git Workflow

```bash
# Branche de feature
git checkout -b feature/nouvelle-fonctionnalite

# Commits atomiques et explicites
git commit -m "feat(clients): ajout recherche avancée clients"

# Pull request avec review
git push origin feature/nouvelle-fonctionnalite
```

## 📞 Support

### Contacts

- **Équipe de développement** : Rémi Verschuur
- **Documentation** : Ce fichier + commentaires code
- **Issues** : Tracker Git du projet

### Ressources

- [Documentation Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Docker Compose](https://docs.docker.com/compose/)
- [MariaDB](https://mariadb.org/documentation/)

---

*Documentation mise à jour : Août 2025*
*Version ACFC : 1.0*
