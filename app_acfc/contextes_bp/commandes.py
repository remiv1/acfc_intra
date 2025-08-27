"""
ACFC - Module Commandes - Gestion des Commandes Clients
=======================================================

Blueprint Flask pour la gestion des commandes clients.
Ce module gère la création, modification et suivi des commandes.

Fonctionnalités principales :
- Création de commandes à partir de la fiche client
- Sélection de produits du catalogue avec filtres
- Gestion des états (facturation, expédition)
- Calcul automatique des montants

Auteur : Développement ACFC
Version : 1.0
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session as SessionBdDType
from app_acfc.modeles import SessionBdD, Commande, DevisesFactures, Catalogue, Client, Adresse
from app_acfc.habilitations import validate_habilitation, CLIENTS
from logs.logger import acfc_log, ERROR, DEBUG
from typing import List, Dict, Optional, Any

# Création du blueprint
commandes_bp = Blueprint(name='commandes',
                         import_name=__name__,
                         url_prefix='/commandes')

# Création des constantes
DETAIL_CLIENT = 'clients.get_client'
LOG_FILE_COMMANDES = 'commandes.log'

@commandes_bp.route('/client/<int:id_client>/commandes/nouvelle', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def nouvelle_commande(id_client: int):
    """Créer une nouvelle commande pour un client"""
    session_db = SessionBdD()
    try:
        # Récupérer le client
        client = session_db.query(Client).filter(Client.id == id_client).first()
        if not client:
            acfc_log.log_to_file(level=ERROR, message=f'Client {id_client} non trouvé')
            return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
        
        if request.method == 'POST':
            action = request.form.get('action', 'save')
            
            # Si c'est une action de filtrage, on traite les filtres
            if action in ['clear_filters'] or any(key.startswith('filter_') for key in request.form.keys()):
                return handle_filters(client, None, request.form, session_db)
            
            # Sinon, c'est une sauvegarde de commande
            return save_commande(client, None, request.form, session_db)
        
        # GET - Afficher le formulaire
        return render_commande_form(client, None, session_db)
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de la création de commande pour client {id_client}: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        flash('Erreur lors de la création de la commande', 'error')
        return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
    finally:
        if 'session_db' in locals(): session_db.close()


@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/modifier', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def modifier_commande(id_client: int, id_commande: int):
    """Modifier une commande existante"""
    session_db = SessionBdD()
    try:
        # Récupérer la commande et le client
        commande = session_db.query(Commande).filter(Commande.id == id_commande).first()
        if not commande:
            acfc_log.log_to_file(level=ERROR, message=f'Commande {id_commande} non trouvée', zone_log=LOG_FILE_COMMANDES)
            return redirect(url_for(DETAIL_CLIENT, id_client=id_client))

        client = commande.client
        
        if request.method == 'POST':
            action = request.form.get('action', 'save')
            
            # Si c'est une action de filtrage, on traite les filtres
            if action in ['clear_filters'] or any(key.startswith('filter_') for key in request.form.keys()):
                return handle_filters(client, commande, request.form, session_db)
            
            # Sinon, c'est une sauvegarde de commande
            return save_commande(client, commande, request.form, session_db)
        
        # GET - Afficher le formulaire
        return render_commande_form(client, commande, session_db)
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de la modification de commande {id_commande}: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
    finally:
        if 'session_db' in locals(): session_db.close()


def render_commande_form(client: Client, commande: Optional[Commande], session_db: SessionBdDType):
    """Rendre le formulaire de commande avec toutes les données nécessaires"""
    try:
        # Récupérer les filtres depuis la session ou les initialiser
        selected_filters = {
            'millesime': session.get('commande_filter_millesime', ''),
            'type_produit': session.get('commande_filter_type_produit', ''),
            'geographie': session.get('commande_filter_geographie', '')
        }
        
        # Construire la requête de base pour le catalogue
        catalogue_query = session_db.query(Catalogue)
        
        # Appliquer les filtres
        if selected_filters['millesime']:
            catalogue_query = catalogue_query.filter(Catalogue.millesime == selected_filters['millesime'])
        if selected_filters['type_produit']:
            catalogue_query = catalogue_query.filter(Catalogue.type_produit == selected_filters['type_produit'])
        if selected_filters['geographie']:
            catalogue_query = catalogue_query.filter(Catalogue.geographie == selected_filters['geographie'])
        
        # Récupérer les produits filtrés
        catalogue_filtered = catalogue_query.order_by(Catalogue.ref_auto).all()
        
        # Récupérer les valeurs pour les filtres
        millesimes = session_db.query(Catalogue.millesime).distinct().filter(Catalogue.millesime.isnot(None)).order_by(Catalogue.millesime.desc()).all()
        millesimes = [m[0] for m in millesimes if m[0]]
        
        types_produit = session_db.query(Catalogue.type_produit).distinct().filter(Catalogue.type_produit.isnot(None)).order_by(Catalogue.type_produit).all()
        types_produit = [t[0] for t in types_produit if t[0]]
        
        geographies = session_db.query(Catalogue.geographie).distinct().filter(Catalogue.geographie.isnot(None)).order_by(Catalogue.geographie).all()
        geographies = [g[0] for g in geographies if g[0]]
        
        # Si on modifie une commande, récupérer les produits déjà sélectionnés
        produits_commande: Dict[str, DevisesFactures] = {}
        produits_id_commandes: List[DevisesFactures] = []
        if commande:
            devises = session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == commande.id).all()
            for devise in devises:
                produits_commande[devise.id_catalogue] = devise
                produits_id_commandes.append(devise.id_catalogue)
        
        # Déterminer le sous-contexte
        sub_context = 'create' if commande is None else 'edit'
        
        return render_template('commandes/commande_form.html',
                               client=client,
                               commande=commande,
                               sub_context=sub_context,
                               catalogue_filtered=catalogue_filtered,
                               millesimes=millesimes,
                               types_produit=types_produit,
                               geographies=geographies,
                               selected_filters=selected_filters,
                               produits_commande=produits_commande,
                               produits_id_commandes=produits_id_commandes)
    
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors du rendu du formulaire de commande: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        raise


def handle_filters(client: Client, commande: Optional[Commande], form_data: Any, session_db: SessionBdDType):
    """Gérer les filtres du catalogue"""
    try:
        action = form_data.get('action')
        
        if action == 'clear_filters':
            # Effacer tous les filtres
            session.pop('commande_filter_millesime', None)
            session.pop('commande_filter_type_produit', None)
            session.pop('commande_filter_geographie', None)
        else:
            # Sauvegarder les filtres en session
            session['commande_filter_millesime'] = form_data.get('filter_millesime', '')
            session['commande_filter_type_produit'] = form_data.get('filter_type_produit', '')
            session['commande_filter_geographie'] = form_data.get('filter_geographie', '')
        
        # Re-rendre le formulaire avec les nouveaux filtres
        return render_commande_form(client, commande, session_db)
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de la gestion des filtres: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        return render_commande_form(client, commande, session_db)


def save_commande(client: Client, commande: Optional[Commande], form_data: Any, session_db: SessionBdDType):
    """Sauvegarder une commande (création ou modification)"""
    try:
        is_new = commande is None
        
        if is_new:
            commande = Commande()
            commande.id_client = client.id
        
        # Récupérer les données du formulaire
        commande.date_commande = datetime.strptime(form_data.get('date_commande'), '%Y-%m-%d').date()
        commande.descriptif = form_data.get('descriptif', '')
        commande.id_adresse = int(form_data.get('id_adresse')) if form_data.get('id_adresse') else None
        
        # États de la commande
        commande.is_facture = 'is_facture' in form_data
        commande.is_expedie = 'is_expedie' in form_data
        
        # Dates conditionnelles
        if commande.is_facture and form_data.get('date_facturation'):
            commande.date_facturation = datetime.strptime(form_data.get('date_facturation'), '%Y-%m-%d').date()
        else:
            commande.date_facturation = None
            
        if commande.is_expedie and form_data.get('date_expedition'):
            commande.date_expedition = datetime.strptime(form_data.get('date_expedition'), '%Y-%m-%d').date()
        else:
            commande.date_expedition = None
            
        commande.id_suivi = form_data.get('id_suivi', '') if commande.is_expedie else ''
        
        # Sauvegarder la commande pour obtenir l'ID
        if is_new:
            session_db.add(commande)
            session_db.flush()  # Pour obtenir l'ID
        
        # Traiter les produits sélectionnés
        produits_selectionnes = form_data.getlist('produits_selectionnes')
        
        if not is_new:
            # Supprimer les anciens produits
            session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == commande.id).delete()
        
        montant_total = 0.0
        
        for produit_id in produits_selectionnes:
            produit_id = int(produit_id)
            qte_key = f'qte_{produit_id}'
            qte = int(form_data.get(qte_key, 1))
            
            # Récupérer les infos du produit
            produit = session_db.query(Catalogue).filter(Catalogue.id == produit_id).first()
            if produit:
                devise = DevisesFactures()
                devise.id_commande = commande.id
                devise.id_catalogue = produit_id
                devise.reference = produit.ref_auto
                devise.designation = produit.des_auto
                devise.qte = qte
                devise.prix_unitaire = float(produit.prix_unitaire_ht)
                devise.remise = 0.0  # Pas de remise par défaut
                devise.prix_total = devise.qte * devise.prix_unitaire * (1 - devise.remise)
                
                montant_total += devise.prix_total
                
                session_db.add(devise)
        
        # Mettre à jour le montant total
        commande.montant = montant_total
        
        # Sauvegarder tout
        session_db.commit()
        
        # Message de succès
        if is_new:
            flash(f'Commande créée avec succès pour {client.nom_affichage}', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Nouvelle commande créée (ID: {commande.id}) pour le client {client.nom_affichage}', zone_log=LOG_FILE_COMMANDES)
        else:
            flash(f'Commande #{commande.id} modifiée avec succès', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Commande {commande.id} modifiée pour le client {client.nom_affichage}', zone_log=LOG_FILE_COMMANDES)

        # Rediriger vers la fiche client
        return redirect(url_for('clients.client_details', id=client.id))
        
    except Exception as e:
        session_db.rollback()
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de la sauvegarde de commande: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        return render_commande_form(client, commande, session_db)


@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/annuler', methods=['POST'])
@validate_habilitation(CLIENTS)
def annuler_commande(id_commande: int, id_client: int):
    """Annuler une commande (soft delete)"""
    session_db = SessionBdD()
    try:
        commande = session_db.query(Commande).filter(Commande.id == id_commande).first()
        if not commande:
            acfc_log.log_to_file(level=ERROR, message=f'Commande {id_commande} non trouvée', zone_log=LOG_FILE_COMMANDES)
            flash('Commande non trouvée', 'error')
            return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
        
        # Vérifier que la commande n'est pas déjà annulée
        if commande.is_annulee:
            flash('Cette commande est déjà annulée', 'warning')
            return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
        
        # Vérifier que la commande n'est pas expédiée (on ne peut pas annuler une commande expédiée)
        if commande.is_expedie:
            flash('Impossible d\'annuler une commande déjà expédiée', 'error')
            return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
        
        # Marquer la commande comme annulée
        commande.is_annulee = True
        session_db.commit()
        
        acfc_log.log_to_file(level=DEBUG, message=f'Commande {id_commande} annulée par utilisateur', zone_log=LOG_FILE_COMMANDES)
        
        return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
        
    except Exception as e:
        session_db.rollback()
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de l\'annulation de commande {id_commande}: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
    finally:
        if 'session_db' in locals():
            session_db.close()


@commandes_bp.route('clients/<int:id_client>/commandes/<int:id_commande>/details')
@validate_habilitation(CLIENTS)
def commande_details(id_commande: int, id_client: int):
    """Afficher les détails d'une commande"""
    session_db = SessionBdD()
    try:
        commande = session_db.query(Commande).filter(Commande.id == id_commande).first()
        if not commande:
            acfc_log.log_to_file(level=ERROR, message=f"Commande {id_commande} non trouvée", zone_log=LOG_FILE_COMMANDES)
            return redirect(url_for('clients.client_list'))
        
        # Récupérer les produits de la commande
        devises_factures = session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == id_commande).all()
        
        return render_template('commandes/commande_details.html',
                             commande=commande,
                             devises_factures=devises_factures,
                             sub_context='details')
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de l'affichage des détails de commande {id_commande}: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        return redirect(url_for('clients.client_list'))
    finally:
        if 'session_db' in locals(): session_db.close()


# Route pour obtenir les adresses d'un client (AJAX)
@commandes_bp.route('/api/client/<int:id_client>/adresses')
@validate_habilitation(CLIENTS)
def get_client_adresses(id_client: int):
    """API pour récupérer les adresses d'un client"""
    session_db = SessionBdD()
    try:
        client = session_db.query(Client).filter(Client.id == id_client).first()
        if not client:
            return jsonify({'error': 'Client non trouvé'}), 404

        adresses: List[Dict[str, Any]] = []

        for adresse in client.adresses:
            adresses.append({
                'id': adresse.id,
                'designation': adresse.designation or 'Adresse principale',
                'voie': adresse.voie,
                'cp': adresse.cp,
                'ville': adresse.ville,
                'display': f"{adresse.voie}, {adresse.cp} {adresse.ville}"
            })
        
        return jsonify({'adresses': adresses})
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de la récupération des adresses du client {id_client}: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        return jsonify({'error': 'Erreur lors de la récupération des adresses'}), 500
    finally:
        if 'session_db' in locals(): session_db.close()
