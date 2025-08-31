"""
ACFC - Exemple d'utilisation des Fixtures de Logging
====================================================

Ce fichier montre comment utiliser les fixtures et mocks de logging
dans vos tests unitaires. Il sert de documentation pratique.

Utilisation principale :
1. Tests avec SQLite au lieu de MongoDB
2. Tests de gestion d'erreurs de connexion
3. Tests de performance et de volume
4. Vérification des entrées de logs

Exécution : python tests_rebuild/example_logging_tests.py
"""

import pytest
from datetime import datetime, timezone
from tests_rebuild.logging_fixtures import (
    LoggerFixtures, 
    LogEntryFixtures, 
    LogEntryFactory,
    LoggingScenarioFixtures,
    LogTestUtils,
    SQLiteLogDatabase,
    ERROR, WARNING, INFO, DEBUG
)


class TestLoggingExamples:
    """Exemples de tests pour le système de logging."""
    
    def test_basic_logging_with_sqlite(self):
        """Test basique d'écriture de logs avec SQLite."""
        # Arrangement
        logger, database = LoggerFixtures.create_test_logger_with_sqlite()
        
        # Action
        logger.log_to_file(ERROR, "Test error message", zone_log="test", db_log=True)
        logger.log_to_file(INFO, "Test info message", zone_log="api", db_log=True)
        
        # Vérification
        error_count = LogTestUtils.count_logs_by_level(database, ERROR)
        info_count = LogTestUtils.count_logs_by_level(database, INFO)
        latest_log = LogTestUtils.get_latest_log(database)
        
        assert error_count == 1
        assert info_count == 1
        assert latest_log is not None
        assert latest_log['message'] == "Test info message"
        assert latest_log['zone'] == "api"
        
        # Nettoyage
        database.close()
    
    def test_log_entry_fixtures(self):
        """Test des fixtures d'entrées de logs prédéfinies."""
        # Test de différents types d'entrées
        error_entry = LogEntryFixtures.error_entry()
        warning_entry = LogEntryFixtures.warning_entry()
        auth_error = LogEntryFixtures.auth_error_entry()
        
        # Vérifications de structure
        LogTestUtils.assert_log_entry_structure(error_entry)
        LogTestUtils.assert_log_entry_structure(warning_entry)
        LogTestUtils.assert_log_entry_structure(auth_error)
        
        # Vérifications de contenu
        assert error_entry['level'] == ERROR
        assert warning_entry['level'] == WARNING
        assert auth_error['zone'] == 'authentification'
    
    def test_factory_functions(self):
        """Test des factory functions pour créer des logs personnalisés."""
        # Création d'une entrée personnalisée
        custom_entry = LogEntryFactory.create_log_entry(
            level=WARNING,
            message="Message personnalisé",
            zone="commandes",
            custom_field="valeur_custom"
        )
        
        assert custom_entry['level'] == WARNING
        assert custom_entry['message'] == "Message personnalisé"
        assert custom_entry['zone'] == "commandes"
        assert custom_entry['custom_field'] == "valeur_custom"
        
        # Création d'un lot d'entrées
        batch_entries = LogEntryFactory.create_batch_entries(10, "Batch test")
        assert len(batch_entries) == 10
        assert all("Batch test" in entry['message'] for entry in batch_entries)
    
    def test_complete_logging_scenario(self):
        """Test d'un scénario complet de logging."""
        # Configuration de l'environnement
        env = LoggingScenarioFixtures.setup_complete_logging_environment()
        logger = env['logger']
        database = env['database']
        
        # Vérification des données pré-remplies
        initial_count = database.count_documents()
        assert initial_count == 5  # 5 entrées de setup
        
        # Ajout de nouvelles entrées
        logger.log_to_file(ERROR, "Nouvelle erreur", zone_log="facturation", db_log=True)
        logger.log_to_file(INFO, "Nouvelle info", zone_log="session", db_log=True)
        
        # Vérifications finales
        final_count = database.count_documents()
        assert final_count == 7  # 5 + 2 nouvelles
        
        # Recherche spécifique
        error_logs = database.find({'level': ERROR})
        facturation_logs = database.find({'zone': 'facturation'})
        
        assert len(error_logs) >= 1
        assert len(facturation_logs) >= 1
        
        # Nettoyage
        database.close()
    
    def test_error_handling_scenario(self):
        """Test de la gestion d'erreurs de connexion."""
        # Configuration d'un scénario d'erreur
        env = LoggingScenarioFixtures.setup_error_handling_scenario()
        logger = env['logger']
        
        # Vérification que le logger fonctionne même sans MongoDB
        assert logger.mongodb_available is False
        
        # Test que l'écriture dans les fichiers fonctionne toujours
        try:
            logger.log_to_file(ERROR, "Test error sans MongoDB")
            # Si on arrive ici, c'est bon (pas d'exception)
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_sqlite_database_operations(self):
        """Test des opérations de base SQLite."""
        # Création d'une base temporaire
        database = SQLiteLogDatabase()
        
        # Test d'insertion
        entry = LogEntryFixtures.info_entry()
        insert_id = database.insert_one(entry)
        assert insert_id > 0
        
        # Test de recherche
        all_logs = database.find()
        assert len(all_logs) == 1
        assert all_logs[0]['message'] == entry['message']
        
        # Test de recherche avec critères
        info_logs = database.find({'level': INFO})
        assert len(info_logs) == 1
        
        # Test de comptage
        count = database.count_documents()
        assert count == 1
        
        # Test de suppression
        database.drop()
        count_after_drop = database.count_documents()
        assert count_after_drop == 0
        
        # Nettoyage
        database.close()
    
    def test_mock_logger_isolation(self):
        """Test avec un logger complètement mocké pour isolation."""
        # Création d'un mock logger
        mock_logger = LoggerFixtures.create_mock_logger()
        
        # Simulation d'utilisation
        mock_logger.log_to_file(ERROR, "Test error")
        mock_logger.log_to_file(INFO, "Test info", zone_log="api", db_log=True)
        
        # Vérifications des appels
        assert mock_logger.log_to_file.call_count == 2
        
        # Vérification des arguments du premier appel
        first_call = mock_logger.log_to_file.call_args_list[0]
        assert first_call[0][0] == ERROR  # Premier argument
        assert first_call[0][1] == "Test error"  # Deuxième argument
        
        # Vérification des arguments du second appel
        second_call = mock_logger.log_to_file.call_args_list[1]
        assert second_call[1]['zone_log'] == "api"  # Argument nommé
        assert second_call[1]['db_log'] is True


def example_performance_test():
    """Exemple de test de performance du logging."""
    logger, database = LoggerFixtures.create_test_logger_with_sqlite()
    
    # Test de volume
    import time
    start_time = time.time()
    
    # Insertion de 1000 logs
    batch_entries = LogEntryFactory.create_batch_entries(1000, "Performance test")
    for entry in batch_entries:
        database.insert_one(entry)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Insertion de 1000 logs en {duration:.2f} secondes")
    print(f"Soit {1000/duration:.0f} logs/seconde")
    
    # Vérification
    total_count = database.count_documents()
    assert total_count == 1000
    
    database.close()


def example_zone_filtering():
    """Exemple de filtrage par zones de logging."""
    logger, database = LoggerFixtures.create_test_logger_with_sqlite()
    
    # Création de logs dans différentes zones
    zones_test = ["authentification", "commandes", "facturation", "api"]
    for i, zone in enumerate(zones_test):
        logger.log_to_file(INFO, f"Log zone {zone}", zone_log=zone, db_log=True)
    
    # Test de filtrage par zone
    for zone in zones_test:
        zone_logs = database.find({'zone': zone})
        assert len(zone_logs) == 1
        assert zone_logs[0]['zone'] == zone
    
    # Comptage total
    total = database.count_documents()
    assert total == len(zones_test)
    
    database.close()


if __name__ == "__main__":
    # Exécution des exemples si le script est lancé directement
    print("=== Tests d'exemple du système de logging ===")
    
    test_instance = TestLoggingExamples()
    
    print("1. Test basique avec SQLite...")
    test_instance.test_basic_logging_with_sqlite()
    print("✓ Réussi")
    
    print("2. Test des fixtures d'entrées...")
    test_instance.test_log_entry_fixtures()
    print("✓ Réussi")
    
    print("3. Test des factory functions...")
    test_instance.test_factory_functions()
    print("✓ Réussi")
    
    print("4. Test de scénario complet...")
    test_instance.test_complete_logging_scenario()
    print("✓ Réussi")
    
    print("5. Test de gestion d'erreurs...")
    test_instance.test_error_handling_scenario()
    print("✓ Réussi")
    
    print("6. Test des opérations SQLite...")
    test_instance.test_sqlite_database_operations()
    print("✓ Réussi")
    
    print("7. Test avec mock logger...")
    test_instance.test_mock_logger_isolation()
    print("✓ Réussi")
    
    print("\n=== Tests de performance ===")
    example_performance_test()
    
    print("\n=== Test de filtrage par zones ===")
    example_zone_filtering()
    
    print("\n✅ Tous les tests sont passés avec succès !")
