# 📊 Système de Rapport de Suivi Automatique

Ce système génère automatiquement des rapports de suivi de réalisation basés sur l'analyse des commits Git du projet.

## 🎯 Objectifs

- **Traçabilité professionnelle** : Documentation automatique du travail effectué
- **Métriques de productivité** : Analyse quantitative des contributions
- **Communication** : Rapports formatés pour employeurs et équipes
- **Suivi de projet** : Évolution et tendances du développement

## 📁 Structure des fichiers

```
scripts/
├── generate_progress_report.py    # Script principal de génération
├── run_report.sh                 # Script de lancement Linux/macOS
├── run_report.ps1                # Script de lancement Windows
└── README.md                     # Cette documentation

.github/workflows/
└── progress_report.yml           # Workflow GitHub Actions automatique
```

## 🚀 Utilisation

### 1. Génération manuelle

#### Sur Windows (PowerShell)
```powershell
# Rapport des 7 derniers jours
.\scripts\run_report.ps1

# Rapport personnalisé
.\scripts\run_report.ps1 -Days 30 -Output "rapport_mensuel.md"

# Aide
.\scripts\run_report.ps1 -Help
```

#### Sur Linux/macOS (Bash)
```bash
# Rapport des 7 derniers jours
./scripts/run_report.sh

# Rapport personnalisé
./scripts/run_report.sh --days 30 --output "rapport_mensuel.md"

# Aide
./scripts/run_report.sh --help
```

#### Directement avec Python
```bash
python scripts/generate_progress_report.py --days 7
```

### 2. Génération automatique (GitHub Actions)

Le workflow se déclenche automatiquement :
- **Chaque dimanche à 20h** (rapport hebdomadaire)
- **Sur push vers main ou branches sprint_***
- **Manuellement** depuis l'interface GitHub

Pour déclencher manuellement :
1. Aller dans l'onglet "Actions" du dépôt GitHub
2. Sélectionner "📊 Génération Automatique de Rapport de Suivi"
3. Cliquer sur "Run workflow"
4. Optionnel : spécifier le nombre de jours à analyser

## 📊 Contenu des rapports

### Sections générées automatiquement

1. **Résumé exécutif**
   - Nombre de commits
   - Volume de code (lignes ajoutées/supprimées)
   - Productivité moyenne

2. **Analyse des commits par période**
   - Détail chronologique des contributions
   - Catégorisation automatique du travail
   - Fichiers impactés

3. **Analyse par type d'activité**
   - Répartition : Développement, Corrections, Documentation, etc.
   - Pourcentages et statistiques

4. **Technologies utilisées**
   - Langages et frameworks identifiés
   - Fréquence d'utilisation

5. **Métriques de productivité**
   - Fréquence de commit
   - Ratio ajouts/suppressions
   - Moyennes par commit

6. **Conclusion automatique**
   - Analyse qualitative basée sur les métriques
   - Identification des tendances

### Catégorisation automatique

Le système catégorise automatiquement le travail selon les messages de commit :

| Type de travail | Mots-clés détectés |
|---|---|
| **Développement de fonctionnalités** | feat, feature, add |
| **Correction de bugs** | fix, bug, correct |
| **Refactoring** | refactor, restructure, reorganize |
| **Documentation** | doc, documentation, readme |
| **Tests** | test, spec |
| **Interface utilisateur** | style, format, css, ui |
| **Configuration** | config, setup, init |

## 🔧 Configuration

### Variables d'environnement (optionnelles)

```bash
# Configuration Git (pour attribution correcte)
git config user.name "Votre Nom"
git config user.email "votre.email@example.com"
```

### Personnalisation du workflow

Modifier `.github/workflows/progress_report.yml` pour :
- Changer la fréquence d'exécution (ligne `cron`)
- Modifier les branches surveillées (ligne `branches`)
- Ajuster les permissions

### Options du script

```bash
python scripts/generate_progress_report.py --help
```

Options disponibles :
- `--days N` : Nombre de jours à analyser (défaut: 7)
- `--output FILE` : Fichier de sortie personnalisé
- `--repo PATH` : Chemin du dépôt Git (défaut: répertoire courant)

## 📈 Exemples d'utilisation

### Rapport hebdomadaire (défaut)
```bash
python scripts/generate_progress_report.py
```
→ Génère `suivi_realisation_auto_YYYYMMDD.md`

### Rapport mensuel
```bash
python scripts/generate_progress_report.py --days 30 --output rapport_mensuel.md
```

### Rapport d'une période spécifique
```bash
# Depuis une date spécifique (nécessite modification du script)
python scripts/generate_progress_report.py --days 14
```

## 🛠️ Maintenance

### Mise à jour du script
1. Modifier `scripts/generate_progress_report.py`
2. Tester localement avec `./scripts/run_report.sh`
3. Commiter les changements
4. Le workflow utilisera automatiquement la nouvelle version

### Dépannage

**Problème : "Aucune activité détectée"**
- Vérifier que les commits ont la bonne attribution (user.name, user.email)
- Augmenter le nombre de jours analysés

**Problème : "Script non trouvé"**
- Vérifier que vous êtes à la racine du projet
- Vérifier la présence du dossier `scripts/`

**Problème : "Erreur Git"**
- Vérifier que vous êtes dans un dépôt Git initialisé
- S'assurer d'avoir au moins un commit

## 🎯 Bonnes pratiques

1. **Messages de commit explicites** : Utiliser des préfixes clairs (feat:, fix:, doc:)
2. **Commits réguliers** : Éviter les gros commits monolithiques
3. **Branches descriptives** : Noms de branches explicites pour le contexte
4. **Documentation** : Maintenir ce README à jour

## 📝 Intégration avec d'autres outils

### Avec des outils de gestion de projet
- Export vers Jira/Trello via API
- Intégration avec Slack pour notifications
- Génération de PDF pour rapports formels

### Avec des métriques de qualité
- Intégration avec SonarQube
- Métriques de couverture de tests
- Analyses de performance

---

*Système développé pour le projet ACFC - Génération automatique de rapports de suivi professionnel*
