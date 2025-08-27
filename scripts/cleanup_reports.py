#!/usr/bin/env python3
"""
Script de nettoyage des anciens rapports de suivi
Garde uniquement les N derniers rapports pour éviter l'encombrement
"""

import os
import glob
import re
from datetime import datetime
import argparse

def cleanup_old_reports(keep_count: int = 5, dry_run: bool = False) -> None:
    """
    Nettoie les anciens rapports automatiques
    
    Args:
        keep_count: Nombre de rapports à conserver
        dry_run: Si True, affiche seulement ce qui serait supprimé
    """
    
    # Pattern pour les rapports automatiques
    pattern = "suivi_realisation_auto_*.md"
    reports = glob.glob(pattern)
    
    if not reports:
        print("📄 Aucun rapport automatique trouvé")
        return
    
    # Extraction des dates et tri
    report_dates = []
    for report in reports:
        # Extraction de la date du nom de fichier
        match = re.search(r'suivi_realisation_auto_(\d{8})\.md', report)
        if match:
            date_str = match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                report_dates.append((date_obj, report))     # type: ignore
            except ValueError:
                print(f"⚠️  Format de date invalide dans {report}")
    
    # Tri par date décroissante (plus récent en premier)
    report_dates.sort(reverse=True)     # type: ignore

    print(f"📊 {len(report_dates)} rapports automatiques trouvés")  # type: ignore

    if len(report_dates) <= keep_count:     # type: ignore
        print(f"✅ Aucun nettoyage nécessaire (≤ {keep_count} rapports)")
        return
    
    # Identification des rapports à supprimer
    to_keep = report_dates[:keep_count]     # type: ignore
    to_delete = report_dates[keep_count:]   # type: ignore

    print(f"\n📋 Rapports à conserver ({keep_count}) :")
    for date_obj, report in to_keep:            # type: ignore
        size = os.path.getsize(report) / 1024  # type: ignore
        print(f"  ✅ {report} ({date_obj.strftime('%d/%m/%Y')}, {size:.1f} KB)")    # type: ignore

    print(f"\n🗑️  Rapports à supprimer ({len(to_delete)}) :")   # type: ignore
    for date_obj, report in to_delete:            # type: ignore
        size = os.path.getsize(report) / 1024  # type: ignore
        print(f"  ❌ {report} ({date_obj.strftime('%d/%m/%Y')}, {size:.1f} KB)")  # type: ignore

    if dry_run:
        print(f"\n🔍 Mode simulation activé - aucune suppression effectuée")
        return
    
    # Demande de confirmation
    if to_delete:
        response = input(f"\n❓ Confirmer la suppression de {len(to_delete)} rapports ? (y/N): ")   # type: ignore
        if response.lower() not in ['y', 'yes', 'o', 'oui']:
            print("❌ Suppression annulée")
            return
    
    # Suppression des fichiers
    deleted_count = 0
    for date_obj, report in to_delete:      # type: ignore
        try:
            os.remove(report)       # type: ignore
            print(f"🗑️  Supprimé: {report}")
            deleted_count += 1
        except OSError as e:
            print(f"❌ Erreur lors de la suppression de {report}: {e}")
    
    print(f"\n✅ Nettoyage terminé: {deleted_count} rapports supprimés")

def main():
    parser = argparse.ArgumentParser(description="Nettoie les anciens rapports de suivi automatiques")
    parser.add_argument("--keep", type=int, default=5, 
                       help="Nombre de rapports récents à conserver (défaut: 5)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Mode simulation - affiche seulement ce qui serait supprimé")
    
    args = parser.parse_args()
    
    print("🧹 Nettoyeur de Rapports de Suivi")
    print("=================================")
    
    cleanup_old_reports(keep_count=args.keep, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
