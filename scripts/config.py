# Configuration et personnalisation du système de rapport automatique

## Variables de configuration

# Fréquence par défaut (en jours)
DEFAULT_DAYS = 7

# Nombre de rapports à conserver
MAX_REPORTS_TO_KEEP = 10

# Format de nom de fichier
REPORT_FILENAME_PATTERN = "suivi_realisation_auto_{date}.md"

# Branches surveillées par le workflow
MONITORED_BRANCHES = ["main", "sprint_*", "develop"]

## Messages de commit personnalisés

COMMIT_MESSAGES = {
    "automatic_report": "📊 Mise à jour automatique du rapport de suivi ({date})",
    "manual_report": "📋 Rapport de suivi généré manuellement ({date})",
    "cleanup": "🧹 Nettoyage des anciens rapports de suivi"
}

## Configuration du workflow GitHub Actions

WORKFLOW_CONFIG = {     # type: ignore
    # Heure d'exécution automatique (UTC)
    "cron_schedule": "0 20 * * 0",  # Dimanche 20h UTC
    
    # Runner à utiliser
    "runner": "ubuntu-latest",
    
    # Version Python
    "python_version": "3.11",
    
    # Permissions nécessaires
    "permissions": [
        "contents: write",
        "pull-requests: write"
    ]
}

## Personnalisation des catégories de travail

WORK_CATEGORIES = {
    "feat|feature|add": "Développement de fonctionnalités",
    "fix|bug|correct": "Correction de bugs", 
    "refactor|restructure|reorganize": "Refactoring",
    "doc|documentation|readme": "Documentation",
    "test|spec": "Tests",
    "style|format|css|ui": "Interface utilisateur",
    "config|setup|init": "Configuration",
    "chore|maintenance": "Maintenance",
    "perf|performance|optimize": "Optimisation",
    "security|sec": "Sécurité"
}

## Configuration des technologies détectées

TECH_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript", 
    ".ts": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SASS/SCSS",
    ".vue": "Vue.js",
    ".jsx": "React",
    ".tsx": "React TypeScript",
    ".yml": "YAML/Config",
    ".yaml": "YAML/Config",
    ".json": "JSON/Config",
    ".md": "Documentation",
    ".dockerfile": "Docker",
    ".sql": "SQL/Database",
    ".sh": "Shell Script",
    ".ps1": "PowerShell",
    ".bat": "Batch Script"
}

## Templates de rapport personnalisés

REPORT_SECTIONS = [
    "resume_executif",
    "commits_par_periode", 
    "analyse_par_activite",
    "technologies_utilisees",
    "metriques_productivite",
    "conclusion_automatique"
]

## Configuration des seuils d'analyse

ANALYSIS_THRESHOLDS: dict[str, int | dict[str, int]] = {
    "high_activity": 5,      # commits pour "très active"
    "medium_activity": 3,    # commits pour "active" 
    "addition_ratio": 2,     # ratio ajouts/suppressions pour "nouveau développement"
    "avg_lines_per_commit": {
        "small": 50,
        "medium": 200, 
        "large": 500
    }
}

## Configuration des notifications

NOTIFICATION_CONFIG = {     # type: ignore
    "discord_webhook": None,  # URL webhook Discord si souhaité
    "slack_webhook": None,    # URL webhook Slack si souhaité
    "email_recipients": [],   # Liste emails pour notifications
    "teams_webhook": None     # URL webhook Microsoft Teams si souhaité
}
