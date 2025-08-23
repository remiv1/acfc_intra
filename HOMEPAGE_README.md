# Page d'accueil ACFC - Guide d'utilisation

## Vue d'ensemble

La page d'accueil de l'application ACFC a été conçue pour offrir un aperçu complet et interactif du système de gestion. Elle est responsive et s'adapte automatiquement aux différentes tailles d'écran.

## Structure de la page

### 1. Section d'accueil (25% de la hauteur)
- Message de bienvenue prominent
- Présentation de la plateforme
- Design responsive avec animations

### 2. Dashboard principal (50% de la hauteur)
- **Colonne gauche (25%)** : Commandes en cours
- **Colonne centrale (50%)** : Logo de l'entreprise
- **Colonne droite (25%)** : Indicateurs commerciaux

### 3. Liens rapides (25% de la hauteur)
- Accès direct aux différents modules
- Icônes représentatives de chaque section
- Animations au survol

## Fichiers créés/modifiés

### Templates
- `app_acfc/templates/default.html` - Template principal de la page d'accueil
- `app_acfc/templates/dashboard/commandes_en_cours.html` - Composant des commandes
- `app_acfc/templates/dashboard/indicateurs_commerciaux.html` - Composant des indicateurs
- `app_acfc/templates/base.html` - Modifié pour inclure CSS et JS

### Assets statiques
- `app_acfc/statics/common/css/home.css` - Styles CSS pour la page d'accueil
- `app_acfc/statics/common/js/home.js` - JavaScript interactif
- `app_acfc/statics/common/img/Logo.svg` - Logo de l'entreprise

### Configuration
- `api_fast_dashboard_example.py` - Exemple d'API FastAPI pour les données

## Intégration avec l'API Fast

### Endpoints requis

La page d'accueil s'attend à recevoir des données depuis les endpoints suivants :

1. **`/api/fast/commandes-en-cours`**
   ```json
   {
     "success": true,
     "commandes": [
       {
         "numero": "CMD-2025-0001",
         "client": "Entreprise ABC", 
         "montant": 1250.00,
         "date": "2025-08-20"
       }
     ],
     "total_commandes": 3,
     "total_montant": 4291.25
   }
   ```

2. **`/api/fast/indicateurs-commerciaux`**
   ```json
   {
     "success": true,
     "indicateurs": {
       "ca_mensuel": 45230.75,
       "nb_commandes": 23,
       "nb_devis": 12,
       "nb_clients": 156
     }
   }
   ```

### Configuration du proxy

Assurez-vous que votre serveur web (nginx/apache) redirige les appels `/api/fast/*` vers votre application FastAPI.

Exemple de configuration nginx :
```nginx
location /api/fast/ {
    proxy_pass http://fastapi-server:8000/api/fast/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Fonctionnalités JavaScript

### Animations
- Fade-in des cartes au chargement
- Animations au survol du logo et des liens
- Effets de transition fluides

### Actualisation automatique
- Rafraîchissement des données toutes les 5 minutes
- Boutons de rafraîchissement manuel
- Notifications de statut

### Responsive Design
- Adaptation mobile-first
- Réorganisation des colonnes sur petits écrans
- Optimisation des tailles de police et espaces

## Personnalisation

### Couleurs et thème
Modifiez les variables CSS dans `home.css` :
```css
:root {
  --primary-color: #007bff;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
}
```

### Logo
Remplacez le fichier `Logo.svg` par votre propre logo en conservant les mêmes dimensions pour un rendu optimal.

### Liens rapides
Modifiez la section des liens rapides dans `default.html` pour ajouter/supprimer des modules selon vos besoins.

## Dépendances

### CSS
- Bootstrap 5.3.2
- Font Awesome 6.4.0

### JavaScript
- Bootstrap JS Bundle
- JavaScript vanilla (ES6+)

## Compatibilité

- **Navigateurs** : Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Résolutions** : 320px à 4K
- **Appareils** : Desktop, tablette, mobile

## Points d'attention

1. **Performance** : Les données sont rafraîchies automatiquement - surveillez la charge sur l'API
2. **Sécurité** : Assurez-vous que les endpoints de l'API sont sécurisés
3. **Fallback** : La page fonctionne même si l'API Fast n'est pas disponible
4. **SEO** : Optimisée pour les moteurs de recherche avec un markup sémantique

## Dépannage

### Problèmes courants

1. **Logo ne s'affiche pas**
   - Vérifiez que le fichier `Logo.svg` existe dans `statics/common/img/`
   - Contrôlez les permissions du fichier

2. **Données ne se chargent pas**
   - Vérifiez que l'API Fast est accessible
   - Consultez la console du navigateur pour les erreurs
   - Testez les endpoints manuellement

3. **Styles cassés**
   - Vérifiez que `home.css` est bien chargé
   - Contrôlez l'ordre de chargement des CSS

4. **JavaScript non fonctionnel**
   - Vérifiez la console pour les erreurs JS
   - Assurez-vous que Bootstrap JS est chargé avant `home.js`

## Support

Pour toute question ou problème, consultez :
- Les logs de l'application Flask
- Les logs de votre serveur web
- La console du navigateur (F12)
