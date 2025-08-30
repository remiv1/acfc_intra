"""
ACFC - Fixtures et Mocks pour les Tests
=======================================

Module contenant les fixtures, mocks et factory functions pour les tests unitaires.
Ce module fournit des objets de test réutilisables basés sur les modèles SQLAlchemy
définis dans app_acfc.modeles.

Types d'objets fournis :
- Fixtures : Objets de test avec données prédéfinies
- Mocks : Objets simulés pour isolation des tests
- Factories : Fonctions pour créer facilement des instances de test
- Data Builders : Constructeurs avec pattern Builder

Auteur : ACFC Development Team
Version : 1.0
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from unittest.mock import Mock
import pytest

# Import du service de gestion des mots de passe
from app_acfc.services import PasswordService

# Import des modèles (pour typage et référence)
try:
    from app_acfc.modeles import (
        User, Client, Part, Pro, Mail, Telephone, Adresse,  # type: ignore
        Commande, DevisesFactures, Facture, Expeditions,    # type: ignore
        Catalogue, Operations, Ventilations, Documents,     # type: ignore
        Stock, Villes, IndicatifsTel, Moi                   # type: ignore
    )
    # Import spécial pour PCG pour éviter l'erreur de constante
    from app_acfc.modeles import PCG as PcgModel            # type: ignore
except ImportError:
    # Pour les tests isolés sans dépendances
    User = Client = Part = Pro = Mail = Telephone = Adresse = None
    Commande = DevisesFactures = Facture = Expeditions = None
    Catalogue = None
    Operations = Ventilations = Documents = None
    Stock = Villes = IndicatifsTel = Moi = None
    PcgModel = None


# ====================================================================
# CONSTANTES DE MOTS DE PASSE POUR LES TESTS
# ====================================================================

# Instance du service de mots de passe pour les tests
_password_service = PasswordService()

# Mots de passe hachés précomputés pour les tests
# Utilisés pour éviter de recalculer les hashs à chaque test
TEST_PASSWORDS = {
    'admin': _password_service.hash_password('admin123!'),
    'user': _password_service.hash_password('user123!'),
    'test': _password_service.hash_password('test123!'),
    'commercial': _password_service.hash_password('commercial123!'),
    'comptable': _password_service.hash_password('comptable123!'),
}

# ====================================================================
# FIXTURES - UTILISATEURS ET AUTHENTIFICATION
# ====================================================================

class UserFixtures:
    """Fixtures pour les objets User."""
    
    @staticmethod
    def user_admin() -> Mock:
        """Utilisateur administrateur avec tous les droits."""
        user = Mock()
        user.id = 1
        user.prenom = "Admin"
        user.nom = "SYSTÈME"
        user.pseudo = "admin"
        user.email = "admin@acfc.local"
        user.telephone = "0123456789"
        user.sha_mdp = TEST_PASSWORDS['admin']
        user.is_chg_mdp = False
        user.date_chg_mdp = date(2024, 1, 1)
        user.nb_errors = 0
        user.is_locked = False
        user.permission = "ADMIN"
        user.created_at = date(2024, 1, 1)
        user.is_active = True
        user.debut = date(2024, 1, 1)
        user.fin = None
        return user
    
    @staticmethod
    def user_commercial() -> Mock:
        """Utilisateur commercial standard."""
        user = Mock()
        user.id = 2
        user.prenom = "Jean"
        user.nom = "COMMERCIAL"
        user.pseudo = "jcommercial"
        user.email = "commercial@acfc.local"
        user.telephone = "0123456790"
        user.sha_mdp = TEST_PASSWORDS['commercial']
        user.is_chg_mdp = False
        user.date_chg_mdp = date(2024, 6, 1)
        user.nb_errors = 0
        user.is_locked = False
        user.permission = "COMMERCIAL"
        user.created_at = date(2024, 6, 1)
        user.is_active = True
        user.debut = date(2024, 6, 1)
        user.fin = None
        return user
    
    @staticmethod
    def user_locked() -> Mock:
        """Utilisateur verrouillé pour tests de sécurité."""
        user = Mock()
        user.id = 3
        user.prenom = "Bloqué"
        user.nom = "UTILISATEUR"
        user.pseudo = "bloque"
        user.email = "bloque@acfc.local"
        user.telephone = "0123456791"
        user.sha_mdp = TEST_PASSWORDS['user']
        user.is_chg_mdp = True
        user.date_chg_mdp = date(2024, 1, 1)
        user.nb_errors = 5
        user.is_locked = True
        user.permission = "USER"
        user.created_at = date(2024, 1, 1)
        user.is_active = False
        user.debut = date(2024, 1, 1)
        user.fin = date(2024, 12, 31)
        return user
    
    @staticmethod
    def create_user_with_password(pseudo: str, password_key: str = 'test', **kwargs: Any) -> Mock:
        """
        Crée un utilisateur avec un mot de passe haché sécurisé.
        
        Args:
            pseudo: Nom d'utilisateur
            password_key: Clé du mot de passe dans TEST_PASSWORDS
            **kwargs: Autres attributs à définir
            
        Returns:
            Mock: Utilisateur de test avec mot de passe haché
        """
        user = Mock()
        user.id = kwargs.get('id', 999)
        user.prenom = kwargs.get('prenom', 'Test')
        user.nom = kwargs.get('nom', 'USER')
        user.pseudo = pseudo
        user.email = kwargs.get('email', f"{pseudo}@acfc.local")
        user.telephone = kwargs.get('telephone', "0123456999")
        user.sha_mdp = TEST_PASSWORDS.get(password_key, TEST_PASSWORDS['test'])
        user.is_chg_mdp = kwargs.get('is_chg_mdp', False)
        user.date_chg_mdp = kwargs.get('date_chg_mdp', date.today())
        user.nb_errors = kwargs.get('nb_errors', 0)
        user.is_locked = kwargs.get('is_locked', False)
        user.permission = kwargs.get('permission', 'USER')
        user.created_at = kwargs.get('created_at', date.today())
        user.is_active = kwargs.get('is_active', True)
        user.debut = kwargs.get('debut', date.today())
        user.fin = kwargs.get('fin', None)
        return user


# ====================================================================
# FIXTURES - CLIENTS ET CRM
# ====================================================================

class ClientFixtures:
    """Fixtures pour les objets Client et relations."""
    
    @staticmethod
    def client_particulier() -> Mock:
        """Client particulier avec données complètes."""
        client = Mock()
        client.id = 1
        client.type_client = 1
        client.created_at = date(2024, 1, 15)
        client.is_active = True
        client.notes = "Client fidèle depuis 2020"
        client.reduces = Decimal('0.05')  # 5% de réduction
        
        # Relation Part
        client.part = PartFixtures.part_standard()
        client.pro = None
        
        # Relations de contact
        client.mails = [MailFixtures.mail_principal()]
        client.tels = [TelephoneFixtures.telephone_mobile()]
        client.adresses = [AdresseFixtures.adresse_principale()]
        client.commandes = []
        client.factures = []
        
        # Propriété calculée
        client.nom_affichage = "Jean DUPONT"
        
        # Méthode to_dict mockée
        client.to_dict.return_value = {
            'id': 1,
            'nom_affichage': 'Jean DUPONT',
            'type_client': 1,
            'type_client_libelle': 'Particulier',
            'code_postal': '75001',
            'ville': 'PARIS',
            'is_active': True,
            'created_at': '2024-01-15'
        }
        
        return client
    
    @staticmethod
    def client_professionnel() -> Mock:
        """Client professionnel avec données complètes."""
        client = Mock()
        client.id = 2
        client.type_client = 2
        client.created_at = date(2024, 2, 1)
        client.is_active = True
        client.notes = "Entreprise tech en croissance"
        client.reduces = Decimal('0.10')  # 10% de réduction
        
        # Relation Pro
        client.part = None
        client.pro = ProFixtures.pro_entreprise()
        
        # Relations de contact
        client.mails = [MailFixtures.mail_professionnel()]
        client.tels = [TelephoneFixtures.telephone_fixe_pro()]
        client.adresses = [AdresseFixtures.adresse_entreprise()]
        client.commandes = []
        client.factures = []
        
        # Propriété calculée
        client.nom_affichage = "TECH SOLUTIONS SARL"
        
        # Méthode to_dict mockée
        client.to_dict.return_value = {
            'id': 2,
            'nom_affichage': 'TECH SOLUTIONS SARL',
            'type_client': 2,
            'type_client_libelle': 'Professionnel',
            'code_postal': '69000',
            'ville': 'LYON',
            'is_active': True,
            'created_at': '2024-02-01'
        }
        
        return client
    
    @staticmethod
    def client_inactif() -> Mock:
        """Client inactif pour tests de filtrage."""
        client = Mock()
        client.id = 3
        client.type_client = 1
        client.created_at = date(2023, 6, 1)
        client.is_active = False
        client.notes = "Client désactivé - impayés"
        client.reduces = Decimal('0.00')
        
        client.part = PartFixtures.part_simple()
        client.pro = None
        client.mails = []
        client.tels = []
        client.adresses = []
        client.commandes = []
        client.factures = []
        
        client.nom_affichage = "Marie MARTIN"
        
        return client


class PartFixtures:
    """Fixtures pour les objets Part (particuliers)."""
    
    @staticmethod
    def part_standard() -> Mock:
        """Particulier avec données complètes."""
        part = Mock()
        part.id = 1
        part.id_client = 1
        part.prenom = "Jean"
        part.nom = "DUPONT"
        part.date_naissance = date(1985, 3, 15)
        part.lieu_naissance = "PARIS 12e"
        return part
    
    @staticmethod
    def part_simple() -> Mock:
        """Particulier avec données minimales."""
        part = Mock()
        part.id = 2
        part.id_client = 3
        part.prenom = "Marie"
        part.nom = "MARTIN"
        part.date_naissance = None
        part.lieu_naissance = None
        return part


class ProFixtures:
    """Fixtures pour les objets Pro (professionnels)."""
    
    @staticmethod
    def pro_entreprise() -> Mock:
        """Entreprise avec SIREN."""
        pro = Mock()
        pro.id = 1
        pro.id_client = 2
        pro.raison_sociale = "TECH SOLUTIONS SARL"
        pro.type_pro = 1  # Entreprise
        pro.siren = "123456789"
        pro.rna = None
        return pro
    
    @staticmethod
    def pro_association() -> Mock:
        """Association avec RNA."""
        pro = Mock()
        pro.id = 2
        pro.id_client = 4
        pro.raison_sociale = "ASSOCIATION CULTURELLE LOCALE"
        pro.type_pro = 2  # Association
        pro.siren = None
        pro.rna = "W751234567"
        return pro


# ====================================================================
# FIXTURES - CONTACTS
# ====================================================================

class MailFixtures:
    """Fixtures pour les objets Mail."""
    
    @staticmethod
    def mail_principal() -> Mock:
        """Email principal d'un particulier."""
        mail = Mock()
        mail.id = 1
        mail.id_client = 1
        mail.type_mail = "personnel"
        mail.detail = "Email principal"
        mail.mail = "jean.dupont@email.com"
        mail.is_principal = True
        return mail
    
    @staticmethod
    def mail_professionnel() -> Mock:
        """Email professionnel."""
        mail = Mock()
        mail.id = 2
        mail.id_client = 2
        mail.type_mail = "professionnel"
        mail.detail = "Contact commercial"
        mail.mail = "contact@techsolutions.fr"
        mail.is_principal = True
        return mail
    
    @staticmethod
    def mail_facturation() -> Mock:
        """Email pour facturation."""
        mail = Mock()
        mail.id = 3
        mail.id_client = 1
        mail.type_mail = "facturation"
        mail.detail = "Factures et relances"
        mail.mail = "factures@email.com"
        mail.is_principal = False
        return mail


class TelephoneFixtures:
    """Fixtures pour les objets Telephone."""
    
    @staticmethod
    def telephone_mobile() -> Mock:
        """Téléphone mobile principal."""
        tel = Mock()
        tel.id = 1
        tel.id_client = 1
        tel.type_telephone = "mobile_perso"
        tel.detail = "Disponible 8h-20h"
        tel.indicatif = "+33"
        tel.telephone = "678901234"
        tel.is_principal = True
        return tel
    
    @staticmethod
    def telephone_fixe_pro() -> Mock:
        """Téléphone fixe professionnel."""
        tel = Mock()
        tel.id = 2
        tel.id_client = 2
        tel.type_telephone = "fixe_pro"
        tel.detail = "Standard entreprise"
        tel.indicatif = "+33"
        tel.telephone = "472345678"
        tel.is_principal = True
        return tel


class AdresseFixtures:
    """Fixtures pour les objets Adresse."""
    
    @staticmethod
    def adresse_principale() -> Mock:
        """Adresse principale d'un particulier."""
        adresse = Mock()
        adresse.id = 1
        adresse.id_client = 1
        adresse.adresse_l1 = "123 rue de la Paix"
        adresse.adresse_l2 = "Appartement 4B"
        adresse.code_postal = "75001"
        adresse.ville = "PARIS"
        adresse.is_principal = True
        adresse.created_at = date(2024, 1, 15)
        adresse.is_active = True
        return adresse
    
    @staticmethod
    def adresse_entreprise() -> Mock:
        """Adresse d'entreprise."""
        adresse = Mock()
        adresse.id = 2
        adresse.id_client = 2
        adresse.adresse_l1 = "45 avenue des Technologies"
        adresse.adresse_l2 = "Bâtiment A - 3ème étage"
        adresse.code_postal = "69000"
        adresse.ville = "LYON"
        adresse.is_principal = True
        adresse.created_at = date(2024, 2, 1)
        adresse.is_active = True
        return adresse


# ====================================================================
# FIXTURES - COMMANDES ET FACTURATION
# ====================================================================

class CommandeFixtures:
    """Fixtures pour les objets Commande."""
    
    @staticmethod
    def commande_simple() -> Mock:
        """Commande simple non facturée."""
        commande = Mock()
        commande.id = 1
        commande.id_client = 1
        commande.is_ad_livraison = False
        commande.id_adresse = 1
        commande.descriptif = "Commande timbres collection"
        commande.date_commande = date(2024, 8, 15)
        commande.montant = Decimal('125.50')
        commande.is_annulee = False
        commande.is_facture = False
        commande.is_expedie = False
        commande.date_facturation = None
        commande.date_expedition = None
        commande.id_suivi = None
        
        # Relations
        commande.client = ClientFixtures.client_particulier()
        commande.adresse = AdresseFixtures.adresse_principale()
        commande.devises = [DevisesFacturesFixtures.ligne_commande()]
        commande.facture = None
        
        return commande
    
    @staticmethod
    def commande_facturee() -> Mock:
        """Commande déjà facturée."""
        commande = Mock()
        commande.id = 2
        commande.id_client = 2
        commande.is_ad_livraison = True
        commande.id_adresse = 2
        commande.descriptif = "Commande entreprise - timbres courants"
        commande.date_commande = date(2024, 7, 1)
        commande.montant = Decimal('450.00')
        commande.is_annulee = False
        commande.is_facture = True
        commande.is_expedie = True
        commande.date_facturation = date(2024, 7, 5)
        commande.date_expedition = date(2024, 7, 8)
        commande.id_suivi = "FR123456789"
        
        # Relations
        commande.client = ClientFixtures.client_professionnel()
        commande.adresse = AdresseFixtures.adresse_entreprise()
        commande.devises = [DevisesFacturesFixtures.ligne_facturee()]
        commande.facture = [FactureFixtures.facture_simple()]
        
        return commande


class DevisesFacturesFixtures:
    """Fixtures pour les objets DevisesFactures (lignes de commande)."""
    
    @staticmethod
    def ligne_commande() -> Mock:
        """Ligne de commande standard."""
        ligne = Mock()
        ligne.id = 1
        ligne.id_commande = 1
        ligne.reference = "EU0850"
        ligne.designation = "MARIANNE 0.85€ x20"
        ligne.qte = 5
        ligne.prix_unitaire = Decimal('17.00')
        ligne.remise = Decimal('0.05')  # 5%
        ligne.prix_total = Decimal('80.75')  # 5 * 17.00 * 0.95
        ligne.remise_euro = Decimal('4.25')   # 5 * 17.00 * 0.05
        
        # État
        ligne.is_facture = False
        ligne.id_facture = None
        ligne.facture_by = None
        ligne.is_expedie = False
        ligne.id_expedition = None
        ligne.expedie_by = None
        
        # Métadonnées
        ligne.created_by = "jcommercial"
        ligne.created_at = datetime(2024, 8, 15, 10, 30)
        ligne.updated_by = None
        ligne.updated_at = datetime(2024, 8, 15, 10, 30)
        
        return ligne
    
    @staticmethod
    def ligne_facturee() -> Mock:
        """Ligne déjà facturée et expédiée."""
        ligne = Mock()
        ligne.id = 2
        ligne.id_commande = 2
        ligne.reference = "VPF020"
        ligne.designation = "VALEUR PERMANENTE FRANCE x100"
        ligne.qte = 10
        ligne.prix_unitaire = Decimal('130.00')
        ligne.remise = Decimal('0.10')  # 10%
        ligne.prix_total = Decimal('1170.00')  # 10 * 130.00 * 0.90
        ligne.remise_euro = Decimal('130.00')   # 10 * 130.00 * 0.10
        
        # État
        ligne.is_facture = True
        ligne.id_facture = 1
        ligne.facture_by = "jcommercial"
        ligne.is_expedie = True
        ligne.id_expedition = 1
        ligne.expedie_by = "jcommercial"
        
        # Métadonnées
        ligne.created_by = "jcommercial"
        ligne.created_at = datetime(2024, 7, 1, 14, 15)
        ligne.updated_by = "jcommercial"
        ligne.updated_at = datetime(2024, 7, 8, 9, 45)
        
        return ligne


class FactureFixtures:
    """Fixtures pour les objets Facture."""
    
    @staticmethod
    def facture_simple() -> Mock:
        """Facture simple avec ID fiscal."""
        facture = Mock()
        facture.id = 1
        facture.id_fiscal = "2024-07-000001-8"
        facture.id_client = 2
        facture.id_commande = 2
        facture.is_adresse_facturation = False
        facture.id_adresse = 2
        facture.date_facturation = date(2024, 7, 5)
        facture.montant_facture = Decimal('1170.00')
        facture.is_imprime = True
        facture.date_impression = date(2024, 7, 5)
        facture.is_prestation_facturee = True
        
        # Relations
        facture.client = ClientFixtures.client_professionnel()
        facture.commande = CommandeFixtures.commande_facturee()
        facture.composantes_factures = [DevisesFacturesFixtures.ligne_facturee()]
        
        # Méthodes mockées
        facture.generate_fiscal_id.return_value = "2024-07-000001-8"
        facture.cle_ean13.return_value = "8"
        
        return facture
    
    @staticmethod
    def facture_non_imprimee() -> Mock:
        """Facture créée mais pas encore imprimée."""
        facture = Mock()
        facture.id = 2
        facture.id_fiscal = "2024-08-000002-3"
        facture.id_client = 1
        facture.id_commande = 3
        facture.is_adresse_facturation = False
        facture.id_adresse = 1
        facture.date_facturation = date(2024, 8, 20)
        facture.montant_facture = Decimal('125.50')
        facture.is_imprime = False
        facture.date_impression = None
        facture.is_prestation_facturee = False
        
        return facture


# ====================================================================
# FIXTURES - CATALOGUE ET PRODUITS
# ====================================================================

class CatalogueFixtures:
    """Fixtures pour les objets Catalogue."""
    
    @staticmethod
    def timbre_marianne() -> Mock:
        """Timbre Marianne standard."""
        produit = Mock()
        produit.id = 1
        produit.type_produit = "MARIANNE"
        produit.stype_produit = "MARIANNE LETTRE VERTE 20 g FRANCE"
        produit.millesime = 2024
        produit.prix_unitaire_ht = Decimal('0.85')
        produit.geographie = "FRANCE"
        produit.poids = "20"
        produit.created_at = date(2024, 1, 1)
        produit.updated_at = datetime(2024, 1, 1, 12, 0)
        
        # Propriétés calculées
        produit.ref_auto = "24MARI01"
        produit.des_auto = "MARIANNE LETTRE VERTE 20 G FRANCE TARIF 2024"
        
        return produit
    
    @staticmethod
    def timbre_europe() -> Mock:
        """Timbre pour l'Europe."""
        produit = Mock()
        produit.id = 2
        produit.type_produit = "EUROPE"
        produit.stype_produit = "LETTRE PRIORITAIRE 20 g EUROPE"
        produit.millesime = 2024
        produit.prix_unitaire_ht = Decimal('1.50')
        produit.geographie = "EUROPE"
        produit.poids = "20"
        produit.created_at = date(2024, 1, 1)
        produit.updated_at = datetime(2024, 1, 1, 12, 0)
        
        # Propriétés calculées
        produit.ref_auto = "24EURO02"
        produit.des_auto = "LETTRE PRIORITAIRE 20 G EUROPE TARIF 2024"
        
        return produit


# ====================================================================
# FIXTURES - COMPTABILITÉ
# ====================================================================

class PcgFixtures:
    """Fixtures pour le Plan Comptable Général."""
    
    @staticmethod
    def compte_client() -> Mock:
        """Compte client (411)."""
        compte = Mock()
        compte.classe = 4
        compte.categorie_1 = 1
        compte.categorie_2 = 1
        compte.compte = 411000
        compte.denomination = "Clients"
        return compte
    
    @staticmethod
    def compte_caisse() -> Mock:
        """Compte caisse (530)."""
        compte = Mock()
        compte.classe = 5
        compte.categorie_1 = 3
        compte.categorie_2 = 0
        compte.compte = 530000
        compte.denomination = "Caisse"
        return compte


class OperationsFixtures:
    """Fixtures pour les opérations comptables."""
    
    @staticmethod
    def operation_vente() -> Mock:
        """Opération de vente."""
        operation = Mock()
        operation.id = 1
        operation.date_operation = date(2024, 8, 15)
        operation.libelle_operation = "Vente timbres - Facture 2024-07-000001-8"
        operation.montant_operation = Decimal('1170.00')
        operation.annee_comptable = 2024
        
        # Relations
        operation.ventilations = [VentilationsFixtures.ventilation_debit(), 
                                 VentilationsFixtures.ventilation_credit()]
        operation.documents = []
        
        return operation


class VentilationsFixtures:
    """Fixtures pour les ventilations comptables."""
    
    @staticmethod
    def ventilation_debit() -> Mock:
        """Ventilation au débit (client)."""
        ventilation = Mock()
        ventilation.id = 1
        ventilation.id_operation = 1
        ventilation.compte_id = 411000
        ventilation.sens = "DEBIT"
        ventilation.montant_debit = Decimal('1170.00')
        ventilation.montant_credit = None
        ventilation.banque = None
        ventilation.id_facture = "2024-07-000001-8"
        ventilation.id_cheque = None
        return ventilation
    
    @staticmethod
    def ventilation_credit() -> Mock:
        """Ventilation au crédit (vente)."""
        ventilation = Mock()
        ventilation.id = 2
        ventilation.id_operation = 1
        ventilation.compte_id = 707000
        ventilation.sens = "CREDIT"
        ventilation.montant_debit = None
        ventilation.montant_credit = Decimal('1170.00')
        ventilation.banque = None
        ventilation.id_facture = "2024-07-000001-8"
        ventilation.id_cheque = None
        return ventilation


# ====================================================================
# FACTORIES - GÉNÉRATEURS D'OBJETS DE TEST
# ====================================================================

class ClientFactory:
    """Factory pour créer des clients de test personnalisés."""
    
    @staticmethod
    def create_particulier(
        id_client: int = 1,
        prenom: str = "Test",
        nom: str = "UTILISATEUR",
        email: str = "test@example.com",
        **kwargs: Any
    ) -> Mock:
        """Crée un client particulier personnalisé."""
        client = Mock()
        client.id = id_client
        client.type_client = 1
        client.created_at = kwargs.get('created_at', date.today())
        client.is_active = kwargs.get('is_active', True)
        client.notes = kwargs.get('notes', "Client de test")
        client.reduces = kwargs.get('reduces', Decimal('0.00'))
        
        # Part associé
        part = Mock()
        part.id = id_client
        part.id_client = id_client
        part.prenom = prenom
        part.nom = nom
        part.date_naissance = kwargs.get('date_naissance')
        part.lieu_naissance = kwargs.get('lieu_naissance')
        
        client.part = part
        client.pro = None
        
        # Email principal
        if email:
            mail = Mock()
            mail.id = id_client
            mail.id_client = id_client
            mail.type_mail = "personnel"
            mail.mail = email
            mail.is_principal = True
            client.mails = [mail]
        else:
            client.mails = []
        
        client.tels = []
        client.adresses = []
        client.commandes = []
        client.factures = []
        
        client.nom_affichage = f"{prenom} {nom}"
        
        return client
    
    @staticmethod
    def create_professionnel(
        id_client: int = 1,
        raison_sociale: str = "ENTREPRISE TEST",
        siren: Optional[str] = "123456789",
        email: str = "contact@test.com",
        **kwargs: Any
    ) -> Mock:
        """Crée un client professionnel personnalisé."""
        client = Mock()
        client.id = id_client
        client.type_client = 2
        client.created_at = kwargs.get('created_at', date.today())
        client.is_active = kwargs.get('is_active', True)
        client.notes = kwargs.get('notes', "Entreprise de test")
        client.reduces = kwargs.get('reduces', Decimal('0.10'))
        
        # Pro associé
        pro = Mock()
        pro.id = id_client
        pro.id_client = id_client
        pro.raison_sociale = raison_sociale
        pro.type_pro = kwargs.get('type_pro', 1)  # Entreprise
        pro.siren = siren
        pro.rna = kwargs.get('rna')
        
        client.part = None
        client.pro = pro
        
        # Email principal
        if email:
            mail = Mock()
            mail.id = id_client
            mail.id_client = id_client
            mail.type_mail = "professionnel"
            mail.mail = email
            mail.is_principal = True
            client.mails = [mail]
        else:
            client.mails = []
        
        client.tels = []
        client.adresses = []
        client.commandes = []
        client.factures = []
        
        client.nom_affichage = raison_sociale
        
        return client


class CommandeFactory:
    """Factory pour créer des commandes de test personnalisées."""
    
    @staticmethod
    def create_commande(
        id_commande: int = 1,
        id_client: int = 1,
        montant: float = 100.0,
        date_commande: Optional[date] = None,
        **kwargs: Any
    ) -> Mock:
        """Crée une commande personnalisée."""
        commande = Mock()
        commande.id = id_commande
        commande.id_client = id_client
        commande.is_ad_livraison = kwargs.get('is_ad_livraison', False)
        commande.id_adresse = kwargs.get('id_adresse', 1)
        commande.descriptif = kwargs.get('descriptif', "Commande de test")
        commande.date_commande = date_commande or date.today()
        commande.montant = Decimal(str(montant))
        commande.is_annulee = kwargs.get('is_annulee', False)
        commande.is_facture = kwargs.get('is_facture', False)
        commande.is_expedie = kwargs.get('is_expedie', False)
        commande.date_facturation = kwargs.get('date_facturation')
        commande.date_expedition = kwargs.get('date_expedition')
        commande.id_suivi = kwargs.get('id_suivi')
        
        # Relations mockées
        commande.client = kwargs.get('client', Mock())
        commande.adresse = kwargs.get('adresse', Mock())
        commande.devises = kwargs.get('devises', [])
        commande.facture = kwargs.get('facture')
        
        return commande


# ====================================================================
# BUILDERS - PATTERN BUILDER POUR OBJETS COMPLEXES
# ====================================================================

class FactureBuilder:
    """Builder pour construire des factures complexes."""
    
    def __init__(self):
        self._facture = Mock()
        self._facture.id = 1
        self._facture.id_fiscal = "2024-08-000001-5"
        self._facture.id_client = 1
        self._facture.id_commande = 1
        self._facture.is_adresse_facturation = False
        self._facture.id_adresse = 1
        self._facture.date_facturation = date.today()
        self._facture.montant_facture = Decimal('0.00')
        self._facture.is_imprime = False
        self._facture.date_impression = None
        self._facture.is_prestation_facturee = False
        self._facture.composantes_factures = []
    
    def with_id(self, facture_id: int) -> 'FactureBuilder':
        """Définit l'ID de la facture."""
        self._facture.id = facture_id
        return self
    
    def with_client(self, client_id: int) -> 'FactureBuilder':
        """Définit le client de la facture."""
        self._facture.id_client = client_id
        return self
    
    def with_montant(self, montant: float) -> 'FactureBuilder':
        """Définit le montant de la facture."""
        self._facture.montant_facture = Decimal(str(montant))
        return self
    
    def with_date(self, date_facturation: date) -> 'FactureBuilder':
        """Définit la date de facturation."""
        self._facture.date_facturation = date_facturation
        return self
    
    def imprimee(self, date_impression: Optional[date] = None) -> 'FactureBuilder':
        """Marque la facture comme imprimée."""
        self._facture.is_imprime = True
        self._facture.date_impression = date_impression or date.today()
        return self
    
    def with_ligne(self, reference: str, designation: str, qte: int, prix_unitaire: float) -> 'FactureBuilder':
        """Ajoute une ligne à la facture."""
        ligne = Mock()
        ligne.reference = reference
        ligne.designation = designation
        ligne.qte = qte
        ligne.prix_unitaire = Decimal(str(prix_unitaire))
        ligne.remise = Decimal('0.00')
        ligne.prix_total = Decimal(str(qte * prix_unitaire))
        ligne.is_facture = True
        
        self._facture.composantes_factures.append(ligne)
        
        # Recalcul du montant total
        total = sum(ligne.prix_total for ligne in self._facture.composantes_factures)
        self._facture.montant_facture = total
        
        return self
    
    def build(self) -> Mock:
        """Construit la facture finale."""
        return self._facture


# ====================================================================
# MOCKS POUR SERVICES ET SESSIONS
# ====================================================================

class SessionMock:
    """Mock pour les sessions SQLAlchemy."""
    
    def __init__(self):
        self.query_results: Dict[Any, Any] = {}
        self.add_called_with: List[Any] = []
        self.commit_called: int = 0
        self.rollback_called: int = 0
        self.flush_called: int = 0

    def query(self, model_class: str) -> Mock:
        """Mock pour query()."""
        mock_query = Mock()
        
        # Simulation des résultats selon le modèle
        if model_class in self.query_results:
            mock_query.all.return_value = self.query_results[model_class]
            mock_query.first.return_value = self.query_results[model_class][0] if self.query_results[model_class] else None
        else:
            mock_query.all.return_value = []
            mock_query.first.return_value = None
        
        # Chaînage des méthodes
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        
        return mock_query

    def add(self, obj: Mock):
        """Mock pour add()."""
        self.add_called_with.append(obj)
    
    def commit(self):
        """Mock pour commit()."""
        self.commit_called += 1
    
    def rollback(self):
        """Mock pour rollback()."""
        self.rollback_called += 1
    
    def flush(self):
        """Mock pour flush()."""
        self.flush_called += 1
    
    def close(self):
        """Mock pour close()."""
        pass

    def set_query_result(self, model_class: str, results: List[Mock]) -> None:
        """Définit les résultats pour un modèle donné."""
        self.query_results[model_class: str] = results


# ====================================================================
# FONCTIONS D'AIDE POUR LES TESTS
# ====================================================================

def create_test_session() -> SessionMock:
    """Crée une session de test mockée."""
    return SessionMock()

def setup_client_fixtures(session: SessionMock) -> None:
    """Configure les fixtures clients dans la session de test."""
    session.set_query_result('Client', [
        ClientFixtures.client_particulier(),
        ClientFixtures.client_professionnel()
    ])

def setup_catalogue_fixtures(session: SessionMock) -> None:
    """Configure les fixtures catalogue dans la session de test."""
    session.set_query_result('Catalogue', [
        CatalogueFixtures.timbre_marianne(),
        CatalogueFixtures.timbre_europe()
    ])

def assert_client_data(client_mock: Mock, expected_nom: str, expected_type: int) -> None:
    """Asserte les données d'un client mocké."""
    assert client_mock.nom_affichage == expected_nom
    assert client_mock.type_client == expected_type
    assert client_mock.is_active is True

def assert_commande_data(commande_mock: Mock, expected_montant: Decimal) -> None:
    """Asserte les données d'une commande mockée."""
    assert commande_mock.montant == expected_montant
    assert commande_mock.is_annulee is False

def assert_facture_data(facture_mock: Mock, expected_montant: Decimal) -> None:
    """Asserte les données d'une facture mockée."""
    assert facture_mock.montant_facture == expected_montant
    assert facture_mock.id_fiscal is not None


# ====================================================================
# PYTEST FIXTURES
# ====================================================================

@pytest.fixture
def mock_session():
    """Fixture pytest pour session mockée."""
    return create_test_session()

@pytest.fixture
def client_particulier():
    """Fixture pytest pour client particulier."""
    return ClientFixtures.client_particulier()

@pytest.fixture
def client_professionnel():
    """Fixture pytest pour client professionnel."""
    return ClientFixtures.client_professionnel()

@pytest.fixture
def commande_simple():
    """Fixture pytest pour commande simple."""
    return CommandeFixtures.commande_simple()

@pytest.fixture
def facture_simple():
    """Fixture pytest pour facture simple."""
    return FactureFixtures.facture_simple()

@pytest.fixture
def catalogue_timbres():
    """Fixture pytest pour catalogue de timbres."""
    return [
        CatalogueFixtures.timbre_marianne(),
        CatalogueFixtures.timbre_europe()
    ]
