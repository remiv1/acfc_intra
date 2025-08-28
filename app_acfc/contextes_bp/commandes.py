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
from sqlalchemy.orm import Session as SessionBdDType
from werkzeug.exceptions import NotFound
from app_acfc.modeles import SessionBdD, Commande, DevisesFactures, Catalogue, Client, Expeditions
from app_acfc.habilitations import validate_habilitation, CLIENTS
from logs.logger import acfc_log, ERROR, DEBUG
from typing import List, Dict, Optional, Any
import qrcode
from io import BytesIO
import base64

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
            acfc_log.log_to_file(level=DEBUG, message=f'Action reçue: {action}', zone_log=LOG_FILE_COMMANDES)
            
            # Actions spéciales pour facturation et expédition
            if action in ['facturer', 'expedier']:
                return handle_special_action(client=client, commande=None, action=action, form_data=request.form, session_db=session_db)
            
            # Sauvegarde de commande (toutes les autres actions)
            acfc_log.log_to_file(level=DEBUG, message='Sauvegarde de la commande en cours', zone_log=LOG_FILE_COMMANDES)
            return save_commande(client=client, commande=None, form_data=request.form, session_db=session_db)

        # GET - Afficher le formulaire
        return render_commande_form(client=client, commande=None, session_db=session_db)
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de la création de commande pour client {id_client}: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        flash('Erreur lors de la création de la commande', 'error')
        return redirect(url_for(DETAIL_CLIENT, id_client=id_client))
    finally:
        if 'session_db' in locals(): session_db.close()


@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/modifier', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def commande_modify(id_client: int, id_commande: int):
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
            
            # Actions spéciales pour facturation et expédition
            if action in ['facturer', 'expedier']:
                return handle_special_action(client=client, commande=commande, action=action, form_data=request.form, session_db=session_db)
            
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
        # Récupérer l'année en cours pour les filtres par défaut
        current_year = datetime.now().year
        
        # Récupérer TOUT le catalogue - filtrage côté JavaScript
        catalogue_complet = session_db.query(Catalogue).order_by(Catalogue.id.desc()).all()
        acfc_log.log_to_file(level=DEBUG, message=f'Catalogue complet chargé: {len(catalogue_complet)} produits', zone_log=LOG_FILE_COMMANDES)
        
        # Récupérer les valeurs distinctes pour les filtres
        millesimes = session_db.query(Catalogue.millesime).distinct().filter(Catalogue.millesime.isnot(None)).order_by(Catalogue.millesime.desc()).all()
        millesimes = [m[0] for m in millesimes if m[0]]
        
        types_produit = session_db.query(Catalogue.type_produit).distinct().filter(Catalogue.type_produit.isnot(None)).order_by(Catalogue.type_produit).all()
        types_produit = [t[0] for t in types_produit if t[0]]
        
        geographies = session_db.query(Catalogue.geographie).distinct().filter(Catalogue.geographie.isnot(None)).order_by(Catalogue.geographie).all()
        geographies = [g[0] for g in geographies if g[0]]
        
        acfc_log.log_to_file(level=DEBUG, message=f'Valeurs distinctes pour les filtres: millésimes={millesimes}, types_produit={types_produit}, geographies={geographies}', zone_log=LOG_FILE_COMMANDES)
        # Si on modifie une commande, récupérer les produits déjà sélectionnés
        produits_commande: Dict[int, Any] = {}
        produits_id_commandes: List[int] = []
        lignes_devis: List[Dict[str, Any]] = []
        
        if commande:
            devises = session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == commande.id).all()
            ligne_counter = 1
            
            for devise in devises:
                # Trouver le produit correspondant par sa référence
                produit_correspondant = None
                for p in catalogue_complet:
                    if p.ref_auto == devise.reference:
                        produit_correspondant = p
                        break
                
                if produit_correspondant:
                    # Ajouter à la structure pour compatibilité avec l'ancien système
                    if produit_correspondant.id not in produits_commande:
                        produits_commande[produit_correspondant.id] = devise
                        produits_id_commandes.append(produit_correspondant.id)
                    
                    # Nouvelle structure pour les lignes de devis
                    lignes_devis.append({
                        'ligne_id': ligne_counter,
                        'produit_id': produit_correspondant.id,
                        'produit': produit_correspondant,
                        'devise': devise,
                        'total_ligne': devise.qte * devise.prix_unitaire * (1 - (devise.remise or 0))
                    })
                    ligne_counter += 1
        else:
            # Pour une nouvelle commande, restaurer les sélections temporaires
            temp_produits = session.get('temp_produits_selectionnes', [])
            temp_data = session.get('temp_commande_data', {})
            
            for produit_id in temp_produits:
                produit_id_int = int(produit_id)
                produits_id_commandes.append(produit_id_int)
                
                # Créer un objet temporaire avec les données sauvées
                class TempDevise:
                    def __init__(self):
                        self.qte = int(temp_data.get(f'qte_{produit_id}', 1))
                        self.prix_unitaire = float(temp_data.get(f'prix_{produit_id}', 0))
                
                produits_commande[produit_id_int] = TempDevise()
            
            acfc_log.log_to_file(level=DEBUG, message=f'Sélections temporaires restaurées: {temp_produits}', zone_log=LOG_FILE_COMMANDES)
        
        # Déterminer le sous-contexte
        sub_context = 'form'
        form_sub_context = 'create' if commande is None else 'edit'
        acfc_log.log_to_file(level=DEBUG, message=f'Sous-contexte de commande: {sub_context}', zone_log=LOG_FILE_COMMANDES)

        return render_template('base.html',
                               context='commandes',
                               sub_context=sub_context,
                               form_sub_context=form_sub_context,
                               client=client,
                               commande=commande,
                               catalogue_complet=catalogue_complet,
                               millesimes=millesimes,
                               types_produit=types_produit,
                               geographies=geographies,
                               current_year=current_year,
                               produits_commande=produits_commande,
                               produits_id_commandes=produits_id_commandes,
                               lignes_devis=lignes_devis,
                               today=date.today())
    
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors du rendu du formulaire de commande: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        raise


def handle_filters(client: Client, commande: Optional[Commande], form_data: Any, session_db: SessionBdDType):
    """Gérer les filtres du catalogue"""
    try:
        action = form_data.get('action')
        current_year = datetime.now().year
        
        # Sauvegarder les sélections temporairement pour une nouvelle commande
        if commande is None:
            # Sauver les produits sélectionnés et leurs quantités/prix
            produits_selectionnes = form_data.getlist('produits_selectionnes')
            session['temp_produits_selectionnes'] = produits_selectionnes
            
            # Sauver les quantités et prix personnalisés
            temp_data = {}
            for produit_id in produits_selectionnes:
                qte_key = f'qte_{produit_id}'
                prix_key = f'prix_{produit_id}'
                if form_data.get(qte_key):
                    temp_data[qte_key] = form_data.get(qte_key)
                if form_data.get(prix_key):
                    temp_data[prix_key] = form_data.get(prix_key)
            session['temp_commande_data'] = temp_data
            acfc_log.log_to_file(level=DEBUG, message=f'Sélections temporaires sauvées: {produits_selectionnes}', zone_log=LOG_FILE_COMMANDES)
        
        if action == 'clear_filters':
            # Remettre les filtres par défaut
            session['commande_filter_millesime'] = str(current_year)
            session['commande_filter_type_produit'] = 'Courrier'
            session['commande_filter_geographie'] = 'FRANCE'
        else:
            # Sauvegarder les filtres en session
            session['commande_filter_millesime'] = form_data.get('filter_millesime', str(current_year))
            session['commande_filter_type_produit'] = form_data.get('filter_type_produit', 'Courrier')
            session['commande_filter_geographie'] = form_data.get('filter_geographie', 'FRANCE')
        
        # Re-rendre le formulaire avec les nouveaux filtres
        return render_commande_form(client, commande, session_db)
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de la gestion des filtres: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        return render_commande_form(client, commande, session_db)


def handle_special_action(client: Client, commande: Optional[Commande], action: str, form_data: Any, session_db: SessionBdDType):
    """Gérer les actions spéciales de facturation et d'expédition"""
    try:
        if action == 'facturer':
            # Pour une nouvelle commande, il faut d'abord la sauvegarder
            if commande is None:
                flash('Vous devez d\'abord créer la commande avant de la facturer', 'warning')
                return render_commande_form(client, commande, session_db)
            
            # Marquer comme facturée
            commande.is_facture = True
            commande.date_facturation = datetime.strptime(form_data.get('date_facturation'), '%Y-%m-%d').date()
            session_db.commit()
            
            flash(f'Commande #{commande.id} facturée avec succès', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Commande {commande.id} facturée', zone_log=LOG_FILE_COMMANDES)
            
        elif action == 'expedier':
            # Pour une nouvelle commande, il faut d'abord la sauvegarder
            if commande is None:
                flash('Vous devez d\'abord créer la commande avant de l\'expédier', 'warning')
                return render_commande_form(client, commande, session_db)
            
            # Vérifier que la commande est facturée
            if not commande.is_facture:
                flash('La commande doit être facturée avant d\'être expédiée', 'warning')
                return render_commande_form(client, commande, session_db)
            
            # Marquer comme expédiée
            commande.is_expedie = True
            commande.date_expedition = datetime.strptime(form_data.get('date_expedition'), '%Y-%m-%d').date()
            
            # Gérer le numéro de suivi selon le mode d'expédition
            mode_expedition = form_data.get('mode_expedition', 'sans_suivi')
            if mode_expedition == 'suivi':
                commande.id_suivi = form_data.get('id_suivi', '')
            else:
                commande.id_suivi = f'{mode_expedition.replace("_", " ").title()}'
            
            session_db.commit()
            
            flash(f'Commande #{commande.id} expédiée avec succès', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Commande {commande.id} expédiée', zone_log=LOG_FILE_COMMANDES)
        
        return redirect(url_for(DETAIL_CLIENT, id_client=client.id))
        
    except Exception as e:
        session_db.rollback()
        acfc_log.log_to_file(level=ERROR, message=f'Erreur lors de l\'action {action}: {str(e)}', zone_log=LOG_FILE_COMMANDES)
        flash(f'Erreur lors de l\'action {action}', 'error')
        return render_commande_form(client, commande, session_db)


def save_commande(client: Client, commande: Optional[Commande], form_data: Any, session_db: SessionBdDType):
    """Sauvegarder une commande (création ou modification)"""
    try:
        is_new = commande is None
        
        if is_new:
            commande = Commande()
            commande.id_client = client.id
        
        # Récupérer les données du formulaire
        acfc_log.log_to_file(level=DEBUG, message='Récupération des données du formulaire pour sauvegarde de commande', zone_log=LOG_FILE_COMMANDES)
        commande.date_commande = datetime.strptime(form_data.get('date_commande'), '%Y-%m-%d').date()
        commande.descriptif = form_data.get('descriptif', '')
        commande.id_adresse = int(form_data.get('id_adresse')) if form_data.get('id_adresse') else None
        
        # États de la commande
        acfc_log.log_to_file(level=DEBUG, message='Mise à jour des états de la commande', zone_log=LOG_FILE_COMMANDES)
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
            acfc_log.log_to_file(level=DEBUG, message='Nouvelle commande ajoutée à la session', zone_log=LOG_FILE_COMMANDES)
            session_db.flush()  # Pour obtenir l'ID
            acfc_log.log_to_file(level=DEBUG, message=f'ID de la nouvelle commande: {commande.id}', zone_log=LOG_FILE_COMMANDES)

        # Traiter les produits sélectionnés avec le nouveau format
        acfc_log.log_to_file(level=DEBUG, message='Traitement des produits avec nouveau format (lignes multiples)', zone_log=LOG_FILE_COMMANDES)

        if not is_new:
            # Supprimer les anciens produits
            session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == commande.id).delete()
        
        # Mettre à jour la remise par défaut du client si modifiée
        remise_client_form = form_data.get('remise_client')
        if remise_client_form:
            client.reduces = float(remise_client_form) / 100.0
            acfc_log.log_to_file(level=DEBUG, message=f'Remise client mise à jour: {client.reduces}', zone_log=LOG_FILE_COMMANDES)
        
        montant_total = 0.0
        
        # Parcourir tous les champs du formulaire pour trouver les lignes de produits
        # Format: prix_[produit_id]_[ligne_id], qte_[produit_id]_[ligne_id], remise_[produit_id]_[ligne_id]
        lignes_produits = {}
        
        for key in form_data.keys():
            if key.startswith(('prix_', 'qte_', 'remise_')):
                parts = key.split('_')
                if len(parts) >= 3:
                    field_type = parts[0]  # prix, qte, ou remise
                    produit_id = parts[1]
                    ligne_id = '_'.join(parts[2:])  # Au cas où l'ID de ligne contient des underscores
                    
                    # Créer la structure si elle n'existe pas
                    if ligne_id not in lignes_produits:
                        lignes_produits[ligne_id] = {}
                    if produit_id not in lignes_produits[ligne_id]:
                        lignes_produits[ligne_id][produit_id] = {}
                    
                    lignes_produits[ligne_id][produit_id][field_type] = form_data.get(key)
        
        acfc_log.log_to_file(level=DEBUG, message=f'Lignes de produits extraites: {len(lignes_produits)} lignes trouvées', zone_log=LOG_FILE_COMMANDES)
        
        # Traiter chaque ligne de produit
        for ligne_id, produits_ligne in lignes_produits.items():
            for produit_id_str, donnees in produits_ligne.items():
                try:
                    produit_id = int(produit_id_str)
                    
                    # Vérifier que toutes les données nécessaires sont présentes
                    if 'prix' not in donnees or 'qte' not in donnees:
                        continue
                    
                    # Récupérer les infos du produit depuis le catalogue
                    produit = session_db.query(Catalogue).filter(Catalogue.id == produit_id).first()
                    if not produit:
                        acfc_log.log_to_file(level=ERROR, message=f'Produit {produit_id} non trouvé dans le catalogue', zone_log=LOG_FILE_COMMANDES)
                        continue
                    
                    # Créer la ligne de devis/facture
                    devise = DevisesFactures()
                    devise.id_commande = commande.id
                    devise.reference = produit.ref_auto
                    devise.designation = produit.des_auto
                    devise.qte = int(donnees['qte'])
                    devise.prix_unitaire = float(donnees['prix'])
                    devise.remise = float(donnees.get('remise', '0')) / 100.0  # Convertir % en décimal
                    
                    # Calculer le montant total côté application
                    prix_ligne = devise.qte * devise.prix_unitaire * (1 - devise.remise)
                    montant_total += prix_ligne
                    
                    session_db.add(devise)
                    acfc_log.log_to_file(level=DEBUG, message=f'Ligne ajoutée: {devise.designation}, QTE: {devise.qte}, Prix: {devise.prix_unitaire}€, Remise: {devise.remise*100}%, Total: {prix_ligne:.2f}€', zone_log=LOG_FILE_COMMANDES)
                    
                except (ValueError, TypeError) as ve:
                    acfc_log.log_to_file(level=ERROR, message=f'Erreur lors du traitement de la ligne {ligne_id}, produit {produit_id_str}: {str(ve)}', zone_log=LOG_FILE_COMMANDES)
                    continue
        
        # Mettre à jour le montant total
        commande.montant = montant_total
        acfc_log.log_to_file(level=DEBUG, message=f'Montant total de la commande mis à jour: {commande.montant}', zone_log=LOG_FILE_COMMANDES)
        
        # Sauvegarder tout
        session_db.commit()
        acfc_log.log_to_file(level=DEBUG, message='Commande et produits sauvegardés avec succès', zone_log=LOG_FILE_COMMANDES)
        
        # Nettoyer les données temporaires après succès
        if is_new:
            session.pop('temp_produits_selectionnes', None)
            session.pop('temp_commande_data', None)
            acfc_log.log_to_file(level=DEBUG, message='Données temporaires nettoyées', zone_log=LOG_FILE_COMMANDES)
        
        # Message de succès
        if is_new:
            flash(f'Commande créée avec succès pour {client.nom_affichage}', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Nouvelle commande créée (ID: {commande.id}) pour le client {client.nom_affichage}', zone_log=LOG_FILE_COMMANDES)
        else:
            flash(f'Commande #{commande.id} modifiée avec succès', 'success')
            acfc_log.log_to_file(level=DEBUG, message=f'Commande {commande.id} modifiée pour le client {client.nom_affichage}', zone_log=LOG_FILE_COMMANDES)

        # Rediriger vers la fiche client
        return redirect(url_for('clients.get_client', id_client=client.id))
        
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


@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/details')
@validate_habilitation(CLIENTS)
def commande_details(id_commande: int, id_client: int):
    """Afficher les détails d'une commande"""
    session_db = SessionBdD()
    try:
        commande = session_db.query(Commande).filter(Commande.id == id_commande).first()
        if not commande:
            acfc_log.log_to_file(level=ERROR, message=f"Commande {id_commande} non trouvée", zone_log=LOG_FILE_COMMANDES)
            raise NotFound("Commande non trouvée")

        # Récupérer les produits de la commande
        devises_factures = session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == id_commande).all()
        
        return render_template('base.html',
                             context='commandes',
                             sub_context='details',
                             id_commande=id_commande,
                             commande=commande,
                             devises_factures=devises_factures,
                             now=datetime.now())
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de l'affichage des détails de commande {id_commande}: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        raise NotFound("Erreur lors de l'affichage des détails de la commande")
    finally:
        if 'session_db' in locals(): session_db.close()


@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/bon-impression')
@validate_habilitation(CLIENTS)
def commande_bon_impression(id_commande: int, id_client: int):
    """Afficher le bon de commande pour impression"""
    session_db = SessionBdD()
    try:
        commande = session_db.query(Commande).filter(Commande.id == id_commande).first()
        if not commande:
            acfc_log.log_to_file(level=ERROR, message=f"Commande {id_commande} non trouvée pour impression", zone_log=LOG_FILE_COMMANDES)
            raise NotFound("Commande non trouvée")

        # Récupérer les produits de la commande
        devises_factures = session_db.query(DevisesFactures).filter(DevisesFactures.id_commande == id_commande).all()
        
        # Générer le QR code côté serveur
        commande_url = url_for('commandes.commande_details', id_client=id_client, id_commande=id_commande, _external=True)
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(commande_url)
        qr.make(fit=True)
        
        # Générer l'image QR code en base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return render_template('commandes/commande_bon_impression.html',
                             commande=commande,
                             devises_factures=devises_factures,
                             commande_url=commande_url,
                             qr_code_base64=qr_code_base64,
                             now=datetime.now())
        
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de la génération du bon de commande {id_commande}: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        raise NotFound("Erreur lors de la génération du bon de commande")
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


@commandes_bp.route('/traiter_facturation', methods=['POST'])
@validate_habilitation(CLIENTS)
def traiter_facturation():
    """Traiter la facturation de lignes sélectionnées"""
    session_db = SessionBdD()
    try:
        numero_commande = request.form.get('numero_commande')
        lignes_facturer = request.form.getlist('lignes_facturer[]')
        numero_facture = request.form.get('numero_facture')
        date_facture = request.form.get('date_facture')
        
        if not all([numero_commande, lignes_facturer, numero_facture, date_facture]):
            flash('Données manquantes pour la facturation', 'error')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Récupérer la commande
        commande = session_db.query(Commande).filter(Commande.numero_commande == numero_commande).first()
        if not commande:
            flash('Commande non trouvée', 'error')
            return redirect(url_for('commandes.liste_commandes'))
        
        # Mettre à jour les lignes sélectionnées
        lignes_ids = [int(ligne_id) for ligne_id in lignes_facturer]
        devises_a_facturer = session_db.query(DevisesFactures).filter(
            DevisesFactures.id.in_(lignes_ids),
            DevisesFactures.numero_commande == numero_commande,
            DevisesFactures.is_facture == False
        ).all()
        
        if not devises_a_facturer:
            flash('Aucune ligne valide à facturer', 'warning')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Convertir la date
        try:
            date_facturation = datetime.strptime(date_facture, '%Y-%m-%d').date()
        except ValueError:
            flash('Format de date invalide', 'error')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Facturer les lignes
        for devise in devises_a_facturer:
            devise.is_facture = True
            devise.date_facturation = date_facturation
            devise.numero_facture = numero_facture
            devise.facture_by = session.get('username', 'Utilisateur')
        
        session_db.commit()
        
        nb_lignes = len(devises_a_facturer)
        flash(f'{nb_lignes} ligne(s) facturée(s) avec succès (Facture: {numero_facture})', 'success')
        
        acfc_log.log_to_file(level=DEBUG, message=f'Facturation de {nb_lignes} lignes pour commande {numero_commande}', zone_log=LOG_FILE_COMMANDES)
        
    except Exception as e:
        session_db.rollback()
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de la facturation: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        flash('Erreur lors de la facturation', 'error')
    
    finally:
        if 'session_db' in locals(): session_db.close()
    
    return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))


@commandes_bp.route('/traiter_expedition', methods=['POST'])
@validate_habilitation(CLIENTS)
def traiter_expedition():
    """Traiter l'expédition de lignes sélectionnées"""
    session_db = SessionBdD()
    try:
        numero_commande = request.form.get('numero_commande')
        lignes_expedier = request.form.getlist('lignes_expedier[]')
        numero_expedition = request.form.get('numero_expedition')
        date_expedition = request.form.get('date_expedition')
        transporteur = request.form.get('transporteur', '')
        
        if not all([numero_commande, lignes_expedier, numero_expedition, date_expedition]):
            flash('Données manquantes pour l\'expédition', 'error')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Récupérer la commande
        commande = session_db.query(Commande).filter(Commande.numero_commande == numero_commande).first()
        if not commande:
            flash('Commande non trouvée', 'error')
            return redirect(url_for('commandes.liste_commandes'))
        
        # Mettre à jour les lignes sélectionnées
        lignes_ids = [int(ligne_id) for ligne_id in lignes_expedier]
        devises_a_expedier = session_db.query(DevisesFactures).filter(
            DevisesFactures.id.in_(lignes_ids),
            DevisesFactures.numero_commande == numero_commande,
            DevisesFactures.is_expedie == False
        ).all()
        
        if not devises_a_expedier:
            flash('Aucune ligne valide à expédier', 'warning')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Convertir la date
        try:
            date_expedition_obj = datetime.strptime(date_expedition, '%Y-%m-%d').date()
        except ValueError:
            flash('Format de date invalide', 'error')
            return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
        
        # Expédier les lignes
        for devise in devises_a_expedier:
            devise.is_expedie = True
            devise.date_expedition = date_expedition_obj
            devise.numero_expedition = numero_expedition
            devise.expedie_by = session.get('username', 'Utilisateur')
            if transporteur:
                devise.transporteur = transporteur
        
        session_db.commit()
        
        nb_lignes = len(devises_a_expedier)
        flash(f'{nb_lignes} ligne(s) expédiée(s) avec succès (Expédition: {numero_expedition})', 'success')
        
        acfc_log.log_to_file(level=DEBUG, message=f'Expédition de {nb_lignes} lignes pour commande {numero_commande}', zone_log=LOG_FILE_COMMANDES)
        
    except Exception as e:
        session_db.rollback()
        acfc_log.log_to_file(level=ERROR, message=f"Erreur lors de l'expédition: {str(e)}", zone_log=LOG_FILE_COMMANDES)
        flash('Erreur lors de l\'expédition', 'error')
    
    finally:
        if 'session_db' in locals(): session_db.close()
    
    return redirect(url_for('commandes.consulter_commande', numero_commande=numero_commande))
