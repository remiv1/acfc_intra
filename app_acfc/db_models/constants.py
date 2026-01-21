"""Modèles de constantes pour l'application ACFC."""

# ====================================================================
# CONSTANTES DE CLÉS PRIMAIRES POUR RÉFÉRENCES ÉTRANGÈRES
# ====================================================================
# Centralisation des références pour maintenir la cohérence du schéma

PK_CLIENTS = '01_clients.id'           # Référence vers la table clients
PK_ADRESSE = '04_adresse.id'           # Référence vers la table adresses
PK_COMMANDE = '11_commandes.id'        # Référence vers la table commandes
PK_FACTURE = '12_factures.id'          # Référence vers la table factures
PK_OPERATION = '31_operations.id'      # Référence vers la table opérations comptables
PK_COMPTE = '30_pcg.compte'            # Référence vers le plan comptable général
PK_EXPEDITION = '14_expeditions.id'     # Référence vers la table expéditions

# ====================================================================
# AUTRES CONSTANTES
# ====================================================================
# Centralisation des références pour maintenir la cohérence du schéma

UNIQUE_ID = 'Identifiant unique'
