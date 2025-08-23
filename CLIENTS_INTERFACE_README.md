# Documentation - Interface de gestion des clients

## Vue d'ensemble

Cette interface complète de gestion des clients permet de rechercher des clients et d'afficher leurs détails complets avec tous les éléments associés (adresses, emails, téléphones, commandes).

## Fichiers créés/modifiés

### Templates HTML

1. **`app_acfc/templates/clients/research.html`**
   - Interface de recherche multi-critères
   - Affichage des résultats de recherche
   - États de chargement et messages d'erreur

2. **`app_acfc/templates/clients/client_details.html`**
   - Interface détaillée avec onglets
   - Affichage des informations client (particulier/professionnel)
   - Onglets pour adresses, emails, téléphones, commandes
   - Boutons d'action pour CRUD

3. **`app_acfc/templates/clients/clients.html`** (modifié)
   - Inclut maintenant les deux templates ci-dessus

### JavaScript

4. **`app_acfc/statics/clients/js/clients.js`** (remplacé)
   - Gestion complète de la recherche et des détails
   - Fonctions utilitaires (formatage, validation)
   - Gestion des erreurs et des états de chargement
   - Compatibilité avec l'ancien système

### CSS

5. **`app_acfc/statics/clients/css/clients.css`** (nouveau)
   - Styles responsifs pour l'interface
   - Animations et transitions
   - Thème cohérent avec Bootstrap

### API Example

6. **`clients_api_example.py`** (nouveau)
   - Exemple d'implémentation des endpoints API
   - Documentation des paramètres et réponses

## Fonctionnalités

### Recherche de clients

- **Critères multiples :** nom, email, téléphone, type de client, ville, code postal
- **Types de clients :** Particulier ou Professionnel
- **Résultats paginés :** Limité à 50 résultats
- **Affichage enrichi :** Badges de type, icônes, informations contextuelles

### Détails du client

- **En-tête client :** Nom, type, statut, date de création, notes
- **Informations spécifiques :**
  - Particulier : nom, prénom, date et lieu de naissance
  - Professionnel : raison sociale, type, SIREN, RNA

### Onglets de données

1. **Adresses** : Liste des adresses avec actions d'édition
2. **Emails** : Emails avec indicateur principal
3. **Téléphones** : Numéros avec indicateur principal  
4. **Commandes** : Historique anti-chronologique avec statuts

### Actions disponibles

- Modification du client
- Ajout/modification/suppression d'adresses
- Ajout/modification/suppression d'emails
- Ajout/modification/suppression de téléphones
- Ajout de commandes
- Consultation/modification de commandes

## Intégration

### 1. Endpoints API requis

Vous devez implémenter ces endpoints dans votre application Flask :

```python
# Recherche de clients
GET /api/clients/search
# Paramètres : nom, email, telephone, type_client, ville, code_postal

# Détails d'un client
GET /api/clients/<id>/details
```

### 2. Structure de réponse

#### Recherche
```json
{
    "success": true,
    "clients": [
        {
            "id": 123,
            "type_client": 1,
            "nom": "Martin Dupont",
            "email": "martin@email.com",
            "telephone": "0123456789",
            "created_at": "2024-01-15T10:30:00",
            "is_active": true
        }
    ],
    "count": 1
}
```

#### Détails
```json
{
    "success": true,
    "client": {
        "id": 123,
        "type_client": 1,
        "created_at": "2024-01-15T10:30:00",
        "is_active": true,
        "notes": "Client fidèle",
        "particulier": {
            "nom": "Dupont",
            "prenom": "Martin",
            "date_naissance": "1980-05-15",
            "lieu_naissance": "Paris"
        },
        "emails": [...],
        "telephones": [...],
        "adresses": [...],
        "commandes": [...]
    }
}
```

### 3. Installation

1. **Copiez les fichiers** dans votre structure de projet

2. **Importez le CSS** dans votre template de base ou spécifiquement :
   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='clients/css/clients.css') }}">
   ```

3. **Implementez les API endpoints** en utilisant `clients_api_example.py` comme guide

4. **Testez l'interface** en accédant à `/clients?sub_context=research`

## Personnalisation

### CSS

Le fichier `clients.css` utilise des variables CSS qui peuvent être personnalisées :
- Couleurs principales : `#007bff`, `#28a745`
- Espacements et bordures
- Animations et transitions

### JavaScript

Les fonctions JavaScript peuvent être étendues :
- `displaySearchResults()` : Personnaliser l'affichage des résultats
- `displayClientDetails()` : Modifier l'affichage des détails
- Actions CRUD : Adapter selon vos endpoints

### Templates

Les templates utilisent Bootstrap 5 et peuvent être modifiés :
- Ajout de nouveaux champs de recherche
- Modification de la présentation des onglets
- Personnalisation des boutons d'action

## Responsive Design

L'interface est entièrement responsive :
- **Mobile** : Navigation simplifiée, onglets adaptés
- **Tablet** : Grille flexible pour les formulaires
- **Desktop** : Interface complète avec toutes les fonctionnalités

## Compatibilité

- **Navigateurs** : Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- **Bootstrap** : Version 5.3.2
- **Font Awesome** : Version 6.4.0
- **JavaScript** : ES6+ (async/await, modules)

## Sécurité

N'oubliez pas d'implémenter :
- Validation des paramètres d'entrée
- Authentification/autorisation
- Protection CSRF
- Sanitisation des données
- Limitation du taux de requêtes

## Support

Pour toute question ou modification, référez-vous aux commentaires dans le code JavaScript et aux exemples dans `clients_api_example.py`.
