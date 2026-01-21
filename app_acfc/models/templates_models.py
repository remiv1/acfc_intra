"""
Module des modèles pour la gestion des templates de l'application ACFC.
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from flask import render_template, session, Request
from logs.logger import INFO, ERROR, acfc_log
from app_acfc.db_models.orders import Facture
from app_acfc.models.orders_models import OrdersModel
from app_acfc.models.products_models import ProductsModel

class Constants:
    '''
    Classe contenant des constantes utilisées dans l'application.
        - log_files(type_log: str) -> str
    '''
    @staticmethod
    def messages(type_msg: str, second_type_message: str) -> str:
        """
        Retourne le message en fonction du type.

        Args:
            type_msg (str): Catégorie du message:
                'error_400', 'error_500', 'client', 'phone', 'email', 'address',
                'user', 'security', 'commandes', 'factures', 'comptabilite', 'stock',
                'commercial', 'warning', 'debug', 'info'
            second_type_message (str): Sous-catégorie du message:
                Si type_msg == 'error_400':
                  - 'wrong_road', 'not_found', 'default'
                Si type_msg == 'error_500':
                  - 'default'
                Si type_msg == 'client':
                  - 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search', 'delete_forbidden'
                Si type_msg == 'phone':
                  - 'missing', 'invalid', 'exists', 'valid', 'default'
                Si type_msg == 'email':
                  - 'missing', 'invalid', 'exists', 'valid', 'default'
                Si type_msg == 'address':
                  - 'missing', 'invalid', 'exists', 'valid', 'default'
                Si type_msg == 'user':
                  - 'create', 'update', 'to_update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'security':
                  - 'default'
                Si type_msg == 'commandes':
                  - 'create', 'created', 'updated', 'deleted', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'factures':
                  - 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'comptabilite':
                  - 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'stock':
                  - 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'commercial':
                  - 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                Si type_msg == 'warning':
                  - 'default'
                Si type_msg == 'debug':
                  - 'default'
                Si type_msg == 'info':
                  - 'default'
        Returns:
            str: Message formaté
        """
        with open('./jsons/messages.json', 'r', encoding='utf-8') as file:
            messages: Dict[str, Dict[str, str]] = json.load(file)
        type_messages = messages.get(type_msg, {})
        return type_messages.get(second_type_message, "Action effectuée.")

    @staticmethod
    def log_files(type_log: str) -> str:
        """
        Retourne le nom du fichier de log en fonction du type.

        Args:
            type_log (str):
                - '400'
                - '500'
                - 'client'
                - 'user'
                - 'security'
                - 'commandes'
                - 'factures'
                - 'comptabilite'
                - 'stock'
                - 'commercial'
                - 'warning'
                - 'debug'
                - 'info'
        Returns:
            str: Nom du fichier de log
        """
        with open('./jsons/logs.json', 'r', encoding='utf-8') as file:
            log_files: Dict[str, str] = json.load(file)
        return log_files.get(type_log, 'general.log')

    @staticmethod
    def templates(name: str) -> str:
        """
        Retourne le nom du template en fonction du nom fourni.

        Args:
            name (str):
                - 'base' + '400' + '500' + 'default' + 'footer' + 'header' + 'login' + 'main'
                - 'admin' + 'adm-chg-pwd' + 'adm-users'
                - 'catalogue'
                - 'clients' + 'client-detail' + 'client-form' + 'client-search'
                - 'commandes' + 'commande-detail' + 'commande-form' + 'commande-print' + 'factures'
                              + 'facture-print'
                - 'commercial' + 'commercial-clt-target'
                - 'comptabilite'
                - 'dashboard' + 'dashboard-cmd' + 'dashboard-fact' + 'dashboard-stock'
                              + 'dashboard-commercial'
                - 'users'
        Returns:
            str: Nom du template
        """
        with open('./jsons/templates.json', 'r', encoding='utf-8') as file:
            templates: Dict[str, str] = json.load(file)
        return templates.get(name, '')

    @staticmethod
    def return_pages(domain: str, sub_domain: str) -> str:
        """
        Retourne le nom du template de la page en fonction du domaine et du sous-domaine.

        Args:
            domain (str): Domaine principal. Valeurs possibles :
                - 'admin'
                - 'clients'
                - 'commandes'
                - 'comptabilite'
                - 'commercial'
                - 'factures'
                - 'stock'
                - 'users'
                - 'catalogue'
            sub_domain (str): Sous-domaine dépendant du domaine choisi :
                Si domain == 'admin' :
                    - 'accueil'
                    - 'logs-dashboard'
                    - 'logs-export'
                Si domain == 'clients' :
                    - 'recherche'
                    - 'recherche-api'
                    - 'creation'
                    - 'detail'
                    - 'modifier-get'
                    - 'modifier-post'
                    - 'phone-add'
                    - 'mail-add'
                Si domain == 'commandes' :
                    - 'nouvelle'
                    - 'detail'
                    - 'modifier'
                    - 'formulaire'
                    - 'annuler'
                    - 'imprimer'
                    - 'factures'
                Si domain == 'commercial' :
                    - 'accueil'
                    - 'filtrage'
                    - 'filtrage-api'
                Si domain == 'comptabilite' :
                    - 'accueil'
                Si domain == 'factures' :
                    - 'detail'
                    - 'imprimer'
                Si domain == 'users' :
                    Aucun sous-domaine
                Si domain == 'stock', 'catalogue' :
                    - 'accueil'
        Returns:
            str: Nom du template de la page
        """
        with open('./jsons/pages.json', 'r', encoding='utf-8') as file:
            pages: Dict[str, Dict[str, str]] = json.load(file)
        return pages.get(domain, {}).get(sub_domain, '')

class PrepareTemplates:
    """
    Classe statique pour la préparation des templates de pages.
    Fournit des méthodes pour générer les templates de différentes pages.
    Utilisation:
        - PrepareTemplates.login(message="Bienvenue", context="login")
        - PrepareTemplates.clients(message="Liste des clients")
        - PrepareTemplates.users(message="Gestion des utilisateurs", objects=user_list)
    """
    BASE: str = Constants.templates('base')

    @staticmethod
    def login(*, message: Optional[str]=None, subcontext: str='login', next_url: Optional[str]=None,
              log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page de login.

        Args:
            message (Optional[str]): Message à afficher sur la page de login.
        Returns:
            str: Template de la page de login
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('user'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Authentification',
                               context='login',
                               subcontext=subcontext,
                               message=message,
                               next=next_url,
                               **kwargs)

    @staticmethod
    def admin(*, message: Optional[str]=None, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page d'administration.

        Args:
            message (Optional[str]): Message à afficher sur la page d'administration.
        Returns:
            str: Template de la page d'administration
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('security'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Administration',
                               context='admin',
                               today=datetime.now().strftime('%Y-%m-%d'),
                               **kwargs)

    @staticmethod
    def clients(*, sub_context: Optional[str]=None, tab: Optional[str]=None,
                log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page clients.

        Args:
            sub_context (Optional[str]): Sous-contexte de la page clients :
                - 'research' : Recherche de clients
                - 'create' : Création d'un nouveau client
                - 'edit' : Modification d'un client
                - 'detail' : Détails d'un client
            tab (Optional[str]): Onglet actif de la page détail du clients :
                - 'info' : Informations générales
                - 'phone' : Téléphones
                - 'mail' : Emails
                - 'add' : Adresses
                - 'order' : Commandes
                - 'bill' : Factures
            log (bool): Indique si l'action doit être loggée.
            message (Optional[str]): Message à afficher sur la page clients.
            success_message (Optional[str]): Message de succès à afficher.
            error_message (Optional[str]): Message d'erreur à afficher.
        Returns:
            str: Template de la page clients
        '''
        if log:
            acfc_log.log(level=INFO, message=kwargs.get('message', ''),
                         specific_logger=Constants.log_files('client'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Gestion Clients', context='clients',
                               sub_context=sub_context, tab=tab, **kwargs)

    @staticmethod
    def orders(*, subcontext: str, order: Optional[OrdersModel]=None, log: bool=False,
               **kwargs: Any) -> str:
        '''
        Génère le template de la page commandes.

        Args:
            subcontext (str): Sous-contexte de la page commandes :
                - 'form' : Formulaire de création/modification de commande
                - 'detail' : Détails d'une commande
                - 'bill_details' : Détails d'une facture
            message (Optional[str]): Message à afficher sur la page commandes.
            success_message (Optional[str]): Message de succès à afficher.
            error_message (Optional[str]): Message d'erreur à afficher.
        Returns:
            str: Template de la page commandes
        '''
        # Gestion des logs
        if log:
            acfc_log.log(level=INFO, message=kwargs.get('message', ''),
                         specific_logger=Constants.log_files('commandes'),
                         user=session.get('pseudo', 'N/A'), db_log=True)

        # Récupération du catalogue filtres et autre paramètres
        catalogue_object = ProductsModel().get_all_products().get_context_catalogue()

        # Retour du template
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Gestion des Commandes',
                               context='commandes',
                               sub_context=subcontext,
                               commande=order,
                               current_year=datetime.now().year,
                               catalogue=catalogue_object.catalogue,
                               millesimes=catalogue_object.millesimes,
                               types_produit=catalogue_object.product_types,
                               geographies=catalogue_object.geo_areas,
                               today=datetime.now().strftime('%Y-%m-%d'),
                               **kwargs)

    @staticmethod
    def bill(*, bill: Facture, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page facture.

        Args:
            bill (Facture): Facture à afficher.
            log (bool): Indique si l'action doit être loggée.
        Returns:
            str: Template de la page facture
        '''
        if log:
            acfc_log.log(level=INFO, message=f'Affichage de la facture ID : {bill.id}',
                         specific_logger=Constants.log_files('factures'),
                         user=session.get('pseudo', 'N/A'), db_log=True)

        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Facture',
                               context='factures',
                               bill_id=bill.id,
                               bill=bill,
                               **kwargs)

    @staticmethod
    def bill_pdf(*, bill: Facture, qr_code_base64: str) -> str:
        '''
        Génère le template PDF de la page facture.

        Args:
            bill (Facture): Facture à afficher.
            qr_code_base64 (str): Code QR en base64 à inclure dans la facture.
        Returns:
            str: Template PDF de la page facture
        '''
        return render_template('orders/bill_print.html',
                               bill=bill,
                               qr_code_base64=qr_code_base64)

    @staticmethod
    def users(*, subcontext: Optional[str]=None, message: Optional[str]=None, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page utilisateurs.

        Args:
            subcontext (Optional[str]): Sous-contexte de la page utilisateurs.
            log (bool): Indique si l'action doit être loggée.
            message (Optional[str]): Message à afficher sur la page utilisateurs.
        Returns:
            str: Template de la page utilisateurs
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('user'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Administration Utilisateurs',
                               context='user',
                               message=message,
                               subcontext=subcontext,
                               **kwargs)

    @staticmethod
    def default(*, objects: Optional[List[Any]], message: Optional[str]=None) -> str:
        '''
        Génère le template de la page par défaut.

        Args:
            objects (Optional[List[Any]]): Liste d'objets à afficher sur la page par défaut.
            message (Optional[str]): Message à afficher sur la page par défaut.
        Returns:
            str: Template de la page par défaut
        '''
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Accueil',
                               context='default',
                               message=message,
                               objects=objects)

    @staticmethod
    def error_4xx(*, status_code: int, status_message: str, request: Request | None=None, log: bool=False, specific_log: Optional[str]=None) -> str:
        '''
        Génère le template de la page d'erreur 4xx.

        Args:
            status_code (int): Code d'erreur HTTP (400, 403, 404, 405).
            status_message (str): Message décrivant l'erreur.
            log (bool): Indique si l'action doit être loggée.
            specific_log (Optional[str]): Nom spécifique du fichier de log (par défaut '400.log').
            message (Optional[str]): Message à afficher sur la page d'erreur.
        Returns:
            str: Template de la page d'erreur 4xx
        '''
        username = session.get('pseudo', 'N/A')
        if status_code == 404 and request:
            adresse = request.url or 'N/A'
        else:
            adresse = 'N/A'
        message = Constants.messages('error_400', 'default') \
                    + f'\ncode erreur : {status_code}' \
                    + f'\ndescription : {status_message}' \
                    + f'\nadresse : {adresse}'
        if log:
            acfc_log.log(level=ERROR, message=message,
                         specific_logger=Constants.log_files(specific_log or '400.log'),
                         db_log=True, user=username or 'N/A')
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Erreur chez vous',
                               context='400', message=message,
                               status_code=status_code,
                               status_message=status_message)

    @staticmethod
    def error_5xx(*, status_code: int, status_message: str, log: bool=False, specific_log: Optional[str]=None) -> str:
        '''
        Génère le template de la page d'erreur 5xx.

        Args:
            status_code (int): Code d'erreur HTTP (500, 501, 502, 503, 504).
            status_message (str): Message décrivant l'erreur.
            log (bool): Indique si l'action doit être loggée.
            specific_log (Optional[str]): Nom spécifique du fichier de log (par défaut '500.log').
        Returns:
            str: Template de la page d'erreur 5xx
        '''
        username = session.get('pseudo', 'N/A')
        message = Constants.messages('error_500', 'default') \
                    + f'\ncode erreur : {status_code}' \
                    + f'\ndescription : {status_message}'
        if log:
            acfc_log.log(level=ERROR, message=message or '',
                         specific_logger=Constants.log_files(specific_log or '500'),
                         db_log=True, user=username)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Erreur chez nous',
                               context='500', message=message,
                               status_code=status_code,
                               status_message=status_message)

    @staticmethod
    def notes(*,template:str, **kwargs: Any) -> str:
        '''
        Génère le template de la page notes.

        Args:
            kwargs (Any): Arguments supplémentaires pour le template.
        Returns:
            str: Template de la page notes
        '''
        return render_template(template_name_or_list=template,
                               **kwargs)
    