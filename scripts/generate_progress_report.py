#!/usr/bin/env python3
"""
Script de génération automatique de rapports de suivi de réalisation
Analyse les commits Git et génère un rapport Markdown détaillé
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import sys

class ProgressReportGenerator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.today = datetime.now()
        
    def run_git_command(self, command: List[str]) -> str:
        """Exécute une commande git et retourne le résultat"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Erreur Git: {e}")
            return ""
    
    def get_commits_since(self, days: int = 7) -> List[Dict[str, Any]]:
        """Récupère les commits des N derniers jours"""
        since_date = (self.today - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Format: hash|date|author|subject
        git_log = self.run_git_command([
            "log", 
            f"--since={since_date}",
            "--pretty=format:%h|%ai|%an|%s",
            "--stat"
        ])
        
        if not git_log:
            return []
        
        commits = []
        lines = git_log.split('\n')
        current_commit = None
        
        for line in lines:
            if '|' in line and len(line.split('|')) == 4:
                # Nouvelle ligne de commit
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split('|')
                current_commit = {
                    'hash': parts[0],
                    'date': parts[1],
                    'author': parts[2],
                    'subject': parts[3],
                    'stats': []
                }
            elif current_commit and ('changed' in line or 'insertion' in line or 'deletion' in line):
                # Ligne de statistiques
                current_commit['stats'].append(line.strip())
        
        if current_commit:
            commits.append(current_commit)
        
        return commits
    
    def get_commit_details(self, commit_hash: str) -> Dict[str, Any]:
        """Récupère les détails d'un commit spécifique"""
        # Statistiques détaillées
        stat_output = self.run_git_command(["show", "--stat", commit_hash])
        
        # Fichiers modifiés
        files_output = self.run_git_command(["show", "--name-only", commit_hash])
        files = files_output.split('\n')[1:]  # Skip commit message line
        
        # Analyse des additions/suppressions
        additions = 0
        deletions = 0
        for line in stat_output.split('\n'):
            if 'insertion' in line or 'deletion' in line:
                numbers = re.findall(r'(\d+)', line)
                if 'insertion' in line and numbers:
                    additions += int(numbers[-2] if len(numbers) >= 2 else numbers[-1])
                if 'deletion' in line and numbers:
                    deletions += int(numbers[-1])
        
        return {
            'files_changed': len([f for f in files if f.strip()]),
            'additions': additions,
            'deletions': deletions,
            'files': files
        }
    
    def analyze_technologies(self, commits: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyse les technologies utilisées basées sur les extensions de fichiers"""
        tech_count = {}
        
        for commit in commits:
            details = self.get_commit_details(commit['hash'])
            for file in details['files']:
                if not file.strip():
                    continue
                    
                ext = Path(file).suffix.lower()
                if ext == '.py':
                    tech_count['Python'] = tech_count.get('Python', 0) + 1
                elif ext in ['.html', '.htm']:
                    tech_count['HTML'] = tech_count.get('HTML', 0) + 1
                elif ext == '.css':
                    tech_count['CSS'] = tech_count.get('CSS', 0) + 1
                elif ext == '.js':
                    tech_count['JavaScript'] = tech_count.get('JavaScript', 0) + 1
                elif ext in ['.yml', '.yaml']:
                    tech_count['YAML/Config'] = tech_count.get('YAML/Config', 0) + 1
                elif ext == '.md':
                    tech_count['Documentation'] = tech_count.get('Documentation', 0) + 1
                elif 'dockerfile' in file.lower():
                    tech_count['Docker'] = tech_count.get('Docker', 0) + 1
        
        return tech_count
    
    def categorize_work(self, commit: Dict[str, Any]) -> str:
        """Catégorise le type de travail basé sur le message de commit"""
        subject = commit['subject'].lower()
        
        if any(word in subject for word in ['feat', 'feature', 'add']):
            return "Développement de fonctionnalités"
        elif any(word in subject for word in ['fix', 'bug', 'correct']):
            return "Correction de bugs"
        elif any(word in subject for word in ['refactor', 'restructure', 'reorganize']):
            return "Refactoring"
        elif any(word in subject for word in ['doc', 'documentation', 'readme']):
            return "Documentation"
        elif any(word in subject for word in ['test', 'spec']):
            return "Tests"
        elif any(word in subject for word in ['style', 'format', 'css', 'ui']):
            return "Interface utilisateur"
        elif any(word in subject for word in ['config', 'setup', 'init']):
            return "Configuration"
        else:
            return "Développement général"
    
    def generate_report(self, days: int = 7) -> str:
        """Génère le rapport complet"""
        commits = self.get_commits_since(days)
        
        if not commits:
            return self._generate_no_activity_report(days)
        
        # Analyse des données
        total_additions = 0
        total_deletions = 0
        total_files = 0
        work_categories = {}
        
        for commit in commits:
            details = self.get_commit_details(commit['hash'])
            total_additions += details['additions']
            total_deletions += details['deletions']
            total_files += details['files_changed']
            
            category = self.categorize_work(commit)
            work_categories[category] = work_categories.get(category, 0) + 1
        
        technologies = self.analyze_technologies(commits)
        
        # Génération du rapport
        report_date = self.today.strftime("%d %B %Y")
        period_start = (self.today - timedelta(days=days)).strftime("%d %B %Y")
        
        report = f"""# Rapport de Suivi de Réalisation - Automatique

**Date du rapport :** {report_date}  
**Période analysée :** {period_start} - {report_date} ({days} jours)  
**Nombre de commits :** {len(commits)}  
**Générateur :** Script automatique v1.0

---

## Résumé exécutif

**Activité de développement :** {len(commits)} commits sur {days} jours  
**Volume de code :** {total_additions} lignes ajoutées, {total_deletions} lignes supprimées  
**Fichiers impactés :** {total_files} fichiers modifiés  
**Productivité moyenne :** {total_additions // max(days, 1)} lignes/jour

---

## Analyse des commits par période

"""

        # Détail des commits par jour
        commits_by_date = {}
        for commit in commits:
            date_str = datetime.fromisoformat(commit['date'].replace('Z', '+00:00')).strftime("%Y-%m-%d")
            if date_str not in commits_by_date:
                commits_by_date[date_str] = []
            commits_by_date[date_str].append(commit)
        
        for date, day_commits in sorted(commits_by_date.items()):
            report += f"\n### {datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')}\n\n"
            
            for commit in day_commits:
                details = self.get_commit_details(commit['hash'])
                category = self.categorize_work(commit)
                commit_time = datetime.fromisoformat(commit['date'].replace('Z', '+00:00')).strftime("%H:%M")
                
                report += f"#### {commit_time} - {commit['hash'][:7]} - {commit['subject']}\n\n"
                report += f"**Catégorie :** {category}  \n"
                report += f"**Impact :** +{details['additions']} -{details['deletions']} lignes, {details['files_changed']} fichiers\n\n"
                
                if details['files']:
                    report += "**Fichiers modifiés :**\n"
                    for file in details['files'][:5]:  # Limite à 5 fichiers
                        if file.strip():
                            report += f"- `{file}`\n"
                    if len(details['files']) > 5:
                        report += f"- ... et {len(details['files']) - 5} autres fichiers\n"
                report += "\n"
        
        # Analyse par catégories
        report += "\n---\n\n## Analyse par type d'activité\n\n"
        for category, count in sorted(work_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(commits)) * 100
            report += f"- **{category}** : {count} commits ({percentage:.1f}%)\n"
        
        # Technologies utilisées
        if technologies:
            report += "\n---\n\n## Technologies et langages utilisés\n\n"
            for tech, count in sorted(technologies.items(), key=lambda x: x[1], reverse=True):
                report += f"- **{tech}** : {count} fichiers modifiés\n"
        
        # Métriques de productivité
        report += f"\n---\n\n## Métriques de productivité\n\n"
        report += f"- **Fréquence de commit :** {len(commits) / max(days, 1):.1f} commits/jour\n"
        report += f"- **Volume de code :** {total_additions + total_deletions} modifications totales\n"
        report += f"- **Ratio ajouts/suppressions :** {total_additions / max(total_deletions, 1):.2f}\n"
        report += f"- **Moyenne lignes par commit :** {(total_additions + total_deletions) / max(len(commits), 1):.0f}\n"
        
        # Conclusion automatique
        report += f"\n---\n\n## Conclusion automatique\n\n"
        
        if len(commits) >= 5:
            activity_level = "très active"
        elif len(commits) >= 3:
            activity_level = "active"
        else:
            activity_level = "modérée"
        
        main_category = max(work_categories.items(), key=lambda x: x[1])[0] if work_categories else "Développement général"
        
        report += f"Période de développement **{activity_level}** avec un focus principal sur **{main_category.lower()}**. "
        report += f"Le volume de {total_additions} lignes ajoutées témoigne d'un travail de développement substantiel. "
        
        if total_additions > total_deletions * 2:
            report += "La proportion élevée d'ajouts par rapport aux suppressions indique un développement de nouvelles fonctionnalités."
        else:
            report += "L'équilibre entre ajouts et suppressions suggère un travail de maintenance et d'amélioration du code existant."
        
        report += f"\n\n---\n*Rapport généré automatiquement le {report_date}*"
        
        return report
    
    def _generate_no_activity_report(self, days: int) -> str:
        """Génère un rapport pour une période sans activité"""
        report_date = self.today.strftime("%d %B %Y")
        period_start = (self.today - timedelta(days=days)).strftime("%d %B %Y")
        
        return f"""# Rapport de Suivi de Réalisation - Automatique

**Date du rapport :** {report_date}  
**Période analysée :** {period_start} - {report_date} ({days} jours)  
**Générateur :** Script automatique v1.0

---

## Résumé

Aucune activité de commit détectée sur la période analysée.

---

*Rapport généré automatiquement le {report_date}*
"""

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Génère un rapport de suivi de réalisation automatique")
    parser.add_argument("--days", type=int, default=7, help="Nombre de jours à analyser (défaut: 7)")
    parser.add_argument("--output", type=str, help="Fichier de sortie (défaut: suivi_realisation_auto.md)")
    parser.add_argument("--repo", type=str, default=".", help="Chemin vers le dépôt Git")
    
    args = parser.parse_args()
    
    # Détermination du fichier de sortie
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = Path(f"suivi_realisation_auto_{timestamp}.md")
    
    # Génération du rapport
    generator = ProgressReportGenerator(args.repo)
    report = generator.generate_report(args.days)
    
    # Écriture du fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Rapport généré : {output_file}")
    print(f"📊 Période analysée : {args.days} jours")

if __name__ == "__main__":
    main()
