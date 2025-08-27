"""
Exemple d'implémentation des endpoints API pour la gestion des clients
À intégrer dans votre application Flask

Ce fichier montre comment implémenter les endpoints requis pour 
l'interface de gestion des clients.
"""

from typing import Literal
from flask import Blueprint, Response, request, jsonify
from app_acfc.modeles import Client, Part, Pro, Mail, Telephone, Adresse, Commande
from sqlalchemy import or_, and_

# Blueprint pour les API clients
clients_api = Blueprint('clients_api', __name__, url_prefix='/api/clients')

@clients_api.route('/search', methods=['GET'])
def search_clients() -> Response | tuple[Response, Literal[500]]:
    """
    Endpoint de recherche de clients
    Paramètres de requête possibles:
    - nom: nom/prénom pour particuliers, raison sociale pour pros
    - email: adresse email
    - telephone: numéro de téléphone
    - type_client: 1 (particulier) ou 2 (professionnel)
    - ville: ville de l'adresse
    - code_postal: code postal
    """
    try:
        # Récupération des paramètres de recherche
        nom = request.args.get('nom', '').strip()
        email = request.args.get('email', '').strip()
        telephone = request.args.get('telephone', '').strip()
        type_client = request.args.get('type_client', '').strip()
        ville = request.args.get('ville', '').strip()
        code_postal = request.args.get('code_postal', '').strip()
        
        # Construction de la requête de base
        query = Client.query
        
        # Filtres conditionnels
        conditions = []
        
        # Filtre par type de client
        if type_client and type_client in ['1', '2']:
            conditions.append(Client.type_client == int(type_client))
        
        # Filtre par nom/raison sociale
        if nom:
            if type_client == '1':  # Particulier
                query = query.join(Part, Client.id == Part.client_id, isouter=True)
                conditions.append(
                    or_(
                        Part.nom.ilike(f'%{nom}%'),
                        Part.prenom.ilike(f'%{nom}%')
                    )
                )
            elif type_client == '2':  # Professionnel
                query = query.join(Pro, Client.id == Pro.client_id, isouter=True)
                conditions.append(Pro.raison_sociale.ilike(f'%{nom}%'))
            else:  # Recherche dans les deux types
                query = query.outerjoin(Part, Client.id == Part.client_id)\
                            .outerjoin(Pro, Client.id == Pro.client_id)
                conditions.append(
                    or_(
                        Part.nom.ilike(f'%{nom}%'),
                        Part.prenom.ilike(f'%{nom}%'),
                        Pro.raison_sociale.ilike(f'%{nom}%')
                    )
                )
        
        # Filtre par email
        if email:
            query = query.join(Mail, Client.id == Mail.client_id, isouter=True)
            conditions.append(Mail.mail.ilike(f'%{email}%'))
        
        # Filtre par téléphone
        if telephone:
            query = query.join(Telephone, Client.id == Telephone.client_id, isouter=True)
            conditions.append(Telephone.telephone.ilike(f'%{telephone}%'))
        
        # Filtre par ville
        if ville:
            query = query.join(Adresse, Client.id == Adresse.client_id, isouter=True)
            conditions.append(Adresse.ville.ilike(f'%{ville}%'))
        
        # Filtre par code postal
        if code_postal:
            if 'Adresse' not in [str(j) for j in query.column_descriptions]:
                query = query.join(Adresse, Client.id == Adresse.client_id, isouter=True)
            conditions.append(Adresse.code_postal.ilike(f'%{code_postal}%'))
        
        # Application des conditions
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Limitation des résultats et exécution
        clients = query.distinct().limit(50).all()
        
        # Formatage des résultats
        results = []
        for client in clients:
            # Récupération des données associées
            particulier = Part.query.filter_by(client_id=client.id).first()
            professionnel = Pro.query.filter_by(client_id=client.id).first()
            email_principal = Mail.query.filter_by(client_id=client.id, is_principal=True).first()
            tel_principal = Telephone.query.filter_by(client_id=client.id, is_principal=True).first()
            
            # Nom d'affichage selon le type
            if client.type_client == 1 and particulier:
                display_name = f"{particulier.prenom or ''} {particulier.nom or ''}".strip()
            elif client.type_client == 2 and professionnel:
                display_name = professionnel.raison_sociale or 'Nom non disponible'
            else:
                display_name = 'Nom non disponible'
            
            client_data = {
                'id': client.id,
                'type_client': client.type_client,
                'nom': display_name,
                'prenom': particulier.prenom if particulier else None,
                'raison_sociale': professionnel.raison_sociale if professionnel else None,
                'email': email_principal.mail if email_principal else None,
                'telephone': tel_principal.telephone if tel_principal else None,
                'created_at': client.created_at.isoformat() if client.created_at else None,
                'is_active': getattr(client, 'is_active', True)
            }
            results.append(client_data)
        
        return jsonify({
            'success': True,
            'clients': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}'
        }), 500


@clients_api.route('/<int:client_id>/details', methods=['GET'])
def get_client_details(client_id):
    """
    Endpoint pour récupérer les détails complets d'un client
    """
    try:
        # Récupération du client
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'message': 'Client non trouvé'
            }), 404
        
        # Récupération des données associées
        particulier = Part.query.filter_by(client_id=client.id).first()
        professionnel = Pro.query.filter_by(client_id=client.id).first()
        emails = Mail.query.filter_by(client_id=client.id).order_by(Mail.is_principal.desc()).all()
        telephones = Telephone.query.filter_by(client_id=client.id).order_by(Telephone.is_principal.desc()).all()
        adresses = Adresse.query.filter_by(client_id=client.id).order_by(Adresse.created_at.desc()).all()
        commandes = Commande.query.filter_by(client_id=client.id).order_by(Commande.date_commande.desc()).all()
        
        # Formatage des données client
        client_data = {
            'id': client.id,
            'type_client': client.type_client,
            'created_at': client.created_at.isoformat() if client.created_at else None,
            'is_active': getattr(client, 'is_active', True),
            'notes': getattr(client, 'notes', None),
        }
        
        # Données particulier
        if particulier:
            client_data['particulier'] = {
                'nom': particulier.nom,
                'prenom': particulier.prenom,
                'date_naissance': particulier.date_naissance.isoformat() if particulier.date_naissance else None,
                'lieu_naissance': particulier.lieu_naissance
            }
        
        # Données professionnel
        if professionnel:
            client_data['professionnel'] = {
                'raison_sociale': professionnel.raison_sociale,
                'type_pro': professionnel.type_pro,
                'siren': professionnel.siren,
                'rna': professionnel.rna
            }
        
        # Emails
        client_data['emails'] = []
        for email in emails:
            client_data['emails'].append({
                'id': email.id,
                'mail': email.mail,
                'type_mail': email.type_mail,
                'is_principal': email.is_principal,
                'detail': email.detail,
                'created_at': email.created_at.isoformat() if email.created_at else None
            })
        
        # Téléphones
        client_data['telephones'] = []
        for tel in telephones:
            client_data['telephones'].append({
                'id': tel.id,
                'telephone': tel.telephone,
                'indicatif': tel.indicatif,
                'type_telephone': tel.type_telephone,
                'is_principal': tel.is_principal,
                'detail': tel.detail,
                'created_at': tel.created_at.isoformat() if tel.created_at else None
            })
        
        # Adresses
        client_data['adresses'] = []
        for adresse in adresses:
            client_data['adresses'].append({
                'id': adresse.id,
                'adresse_l1': adresse.adresse_l1,
                'adresse_l2': adresse.adresse_l2,
                'code_postal': adresse.code_postal,
                'ville': adresse.ville,
                'created_at': adresse.created_at.isoformat() if adresse.created_at else None
            })
        
        # Commandes
        client_data['commandes'] = []
        for commande in commandes:
            client_data['commandes'].append({
                'id': commande.id,
                'date_commande': commande.date_commande.isoformat() if commande.date_commande else None,
                'montant': float(commande.montant) if commande.montant else 0,
                'descriptif': commande.descriptif,
                'is_facture': getattr(commande, 'is_facture', False),
                'is_expedie': getattr(commande, 'is_expedie', False),
                'date_facturation': commande.date_facturation.isoformat() if getattr(commande, 'date_facturation', None) else None,
                'date_expedition': commande.date_expedition.isoformat() if getattr(commande, 'date_expedition', None) else None
            })
        
        return jsonify({
            'success': True,
            'client': client_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération des détails: {str(e)}'
        }), 500


# Fonction d'enregistrement du blueprint
def register_clients_api(app):
    """
    Fonction pour enregistrer le blueprint dans l'application Flask
    
    Usage dans votre application.py:
    from clients_api_example import register_clients_api
    register_clients_api(app)
    """
    app.register_blueprint(clients_api)


"""
Instructions d'intégration:

1. Copiez ce code dans un nouveau fichier dans votre projet (ex: clients_api.py)

2. Importez et enregistrez le blueprint dans votre application.py:
   
   from clients_api import register_clients_api
   register_clients_api(app)

3. Assurez-vous que vos modèles correspondent aux noms utilisés ici:
   - Client, Part, Pro, Mail, Telephone, Adresse, Commande

4. Adaptez les noms de champs selon votre base de données

5. Ajoutez la gestion d'erreurs et les validations selon vos besoins

6. Testez les endpoints avec curl ou un outil similaire:
   
   # Recherche
   curl "http://localhost:5000/api/clients/search?nom=Martin&type_client=1"
   
   # Détails
   curl "http://localhost:5000/api/clients/123/details"

Note: Ce code est un exemple et doit être adapté à votre structure exacte de base de données.
"""
