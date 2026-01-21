"""
Module de gestion du compte utilisateur et des paramètres.
Fournit des méthodes pour récupérer les informations utilisateur,
vérifier les permissions, valider les entrées de formulaire et gérer
les paramètres du compte.
"""

import re
from typing import Any, List
from flask import session
from werkzeug.exceptions import Forbidden
from werkzeug.wrappers import Request
from sqlalchemy.orm import Session as SessionBdDType
from app_acfc.db_models.users import User
from app_acfc.models.templates_models import PrepareTemplates, Constants

class MyAccount:
    """
    Classe de gestion du compte utilisateur et des paramètres.

    Fournit des méthodes pour récupérer les informations utilisateur,
    vérifier les permissions, valider les entrées de formulaire et gérer
    les paramètres du compte.
    """
    @staticmethod
    def get_user_or_error(db_session: SessionBdDType, pseudo: str) -> Any:
        """
        Récupère l'utilisateur par son pseudo ou retourne une page d'erreur 400 si non trouvé.
        Args:
            db_session (SessionBdDType): Session de base de données
            pseudo (str): Pseudo de l'utilisateur à récupérer
        Returns:
            User ou page d'erreur 400 si non trouvé
        """
        user: User = db_session.query(User).filter_by(pseudo=pseudo).first()
        if not user:
            return PrepareTemplates.error_4xx(status_code=404, log=True,
                                            status_message=Constants.messages('user', 'not_found'))
        return user

    @staticmethod
    def check_user_permission(pseudo: str) -> Any:
        """
        Vérifie que l'utilisateur connecté a la permission d'accéder au compte demandé.
        Args:
            pseudo (str): Pseudo de l'utilisateur à vérifier
        Raises:
            Forbidden: Si l'utilisateur n'a pas la permission d'accéder au compte
        """
        if session.get('pseudo') != pseudo:
            raise Forbidden("Vous n'êtes pas autorisé à accéder à ce compte.")

    @staticmethod
    def get_request_form(request: Request, user: User) -> str | List[str]:
        """
        Récupère les données du formulaire de la requête.
        Args:
            request (Request): Objet de requête Flask
        Returns:
            Liste des valeurs du formulaire [prenom, nom, email, telephone]
        """
        first_name = request.form.get('prenom', '').strip()
        last_name = request.form.get('nom', '').strip()
        mail = request.form.get('email', '').strip()
        phone = request.form.get('telephone', '').strip()
        _form_return = [first_name, last_name, mail, phone]

        # Retour à la page de paramètres si des champs obligatoires sont vides
        if '' in _form_return:
            return PrepareTemplates.users(subcontext='parameters', objects=[user],
                                              message="Tous les champs sont obligatoires.")
        return [first_name, last_name, mail, phone]

    @staticmethod
    def valid_mail(mail: str, user:User, db_session: SessionBdDType) -> Any:
        """
        Validation de l'adresse email. Retour de la page de paramètre avec un message si invalide.
        Validation que l'email n'est pas déjà utilisé par un autre compte.
        Args:
            mail (str): Adresse email à valider
            user (User): Instance de l'utilisateur actuel
            db_session (SessionBdDType): Session de base de données
        Returns:
            True si l'email est valide et non utilisé, sinon page de paramètre avec message d'erreur
                1. Format invalide
                2. Email déjà utilisé
        """
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, mail):
            return PrepareTemplates.users(message="Le format de l'adresse email n'est pas valide.",
                                          objects=[user], subcontext='parameters')
        elif mail != user.email:
            existing_user = db_session.query(User).filter_by(email=mail).first()
            if existing_user:
                return PrepareTemplates.users(message="Mail déjà utilisée par un autre compte.",
                                              objects=[user], subcontext='parameters')
        return re.match(email_pattern, mail) is not None

    @staticmethod
    def update_user_settings(user: User, data_list: str | List[str]):
        """
        Met à jour les paramètres de l'utilisateur connecté avec les données du formulaire.
        Retourne la page de paramètres avec un message de succès ou d'erreur.
        Returns:
            Page de paramètres avec message de succès ou d'erreur
        """
        # Mise à jour des données utilisateur et de la session
        session['first_name'] = user.prenom = data_list[0]
        session['last_name'] = user.nom = data_list[1]
        session['email'] = user.email = data_list[2]
        session['telephone'] = user.telephone = data_list[3]

        return user
