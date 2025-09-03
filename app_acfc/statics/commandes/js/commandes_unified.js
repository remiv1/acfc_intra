/**
 * ====================================================================
 * ACFC - Module JavaScript Unifié pour les Commandes
 * ====================================================================
 * 
 * Module unique regroupant toutes les fonctionnalités JavaScript 
 * relatives aux commandes :
 * - Formulaire de création/modification de commande
 * - Gestion des détails de commande
 * - Modal de sélection des produits avec recherche
 * - Tableau des produits sélectionnés éditable
 * - Duplication et suppression de lignes
 * - Calcul automatique des totaux
 * - Gestion des remises
 * - Gestion de la facturation et expédition
 * - Actions par lot
 * 
 * Dépendances : Bootstrap 5, Font Awesome 6
 * ====================================================================
 */

// ====================================================================
// VARIABLES GLOBALES
// ====================================================================

let ligneCounter = 1000; // Compteur pour les nouvelles lignes
let catalogueComplet = [];

// ====================================================================
// INITIALISATION PRINCIPALE
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Déterminer le contexte de la page
    const context = detectPageContext();
    
    console.log('Initialisation du module commandes - Contexte:', context);
    
    // Initialiser les fonctionnalités communes
    initializeCommonFeatures();
    
    // Initialiser selon le contexte
    switch(context) {
        case 'form':
            initializeFormFeatures();
            break;
        case 'details':
            initializeDetailsFeatures();
            break;
        case 'list':
            initializeListFeatures();
            break;
        default:
            console.log('Contexte non reconnu, initialisation des fonctionnalités de base');
    }
    
    console.log('Module commandes initialisé avec succès');
});

/**
 * Détecter le contexte de la page
 */
function detectPageContext() {
    if (document.getElementById('commandeForm')) return 'form';
    if (document.querySelector('.commande-details') || document.getElementById('facturationModal')) return 'details';
    if (document.querySelector('.commandes-list')) return 'list';
    return 'unknown';
}

// ====================================================================
// FONCTIONNALITÉS COMMUNES
// ====================================================================

function initializeCommonFeatures() {
    initializeDateFields();
    initializeUtilityFunctions();
}

function initializeDateFields() {
    // Initialiser la date du jour si nécessaire
    const dateCommandeInput = document.getElementById('date_commande');
    if (dateCommandeInput && !dateCommandeInput.value) {
        const today = new Date();
        const formattedDate = today.getFullYear() + '-' + 
                             (today.getMonth() + 1).toString().padStart(2, '0') + '-' + 
                             today.getDate().toString().padStart(2, '0');
        dateCommandeInput.value = formattedDate;
    }
}

function initializeUtilityFunctions() {
    // Fonction de copie de numéro de suivi
    window.copierNumeroSuivi = function(numero) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(numero).then(() => {
                showAlert('Numéro de suivi copié : ' + numero, 'success');
            }).catch(err => {
                console.error('Erreur lors de la copie:', err);
                fallbackCopyToClipboard(numero);
            });
        } else {
            fallbackCopyToClipboard(numero);
        }
    };
    
    // Fonction de copie fallback pour les navigateurs plus anciens
    function fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('Numéro de suivi copié : ' + text, 'success');
        } catch (err) {
            console.error('Impossible de copier le texte:', err);
            showAlert('Impossible de copier automatiquement. Numéro: ' + text, 'error');
        }
        document.body.removeChild(textArea);
    }
}

// ====================================================================
// FONCTIONNALITÉS DU FORMULAIRE
// ====================================================================

function initializeFormFeatures() {
    // Charger le catalogue depuis les données du template
    chargerCatalogueFromTemplate();
    
    // Initialiser les événements du formulaire
    initializeFormHandlers();
    
    // Initialiser la modal de catalogue
    initializeCatalogueModal();
    
    // Initialiser le tableau des produits
    initializeProductTable();
    
    // Initialiser les champs conditionnels
    initializeConditionalFields();
    
    // Vérifier la présence de produits
    verifierPresenceProduits();
    
    // Initialiser le calcul des totaux selon le mode
    initializeTotalCalculation();
}

function initializeTotalCalculation() {
    const montantInput = document.getElementById('montant');
    const totalElement = document.getElementById('totalCommande');
    
    if (!montantInput || !totalElement) return;
    
    console.log('Montant initial:', montantInput.value);
    console.log('Total initial:', totalElement.textContent);
    
    // Déterminer si on est en mode modification ou création
    const lignesExistantes = document.querySelectorAll('#produitsSelectionnesBody tr');
    const hasLignesExistantes = lignesExistantes.length > 0;
    
    const isModification = hasLignesExistantes || 
                          (montantInput.value && montantInput.value !== '' && montantInput.value !== '0.00');
    
    console.log('Mode détecté:', isModification ? 'modification' : 'création');
    console.log('Lignes existantes:', hasLignesExistantes, '- Nombre:', lignesExistantes.length);
    
    if (isModification && hasLignesExistantes) {
        // En mode modification avec des lignes : recalculer depuis les lignes
        calculerTotalCommande();
    } else if (isModification && !hasLignesExistantes) {
        // En mode modification sans lignes : afficher le montant sauvé
        if (totalElement && montantInput.value) {
            totalElement.textContent = parseFloat(montantInput.value).toFixed(2) + ' €';
        }
    } else {
        // En mode création : le total sera calculé quand on ajoutera des produits
        calculerTotalCommande();
    }
}

function chargerCatalogueFromTemplate() {
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    catalogueComplet = [];
    
    rows.forEach(row => {
        const checkbox = row.querySelector('.modal-product-checkbox');
        if (checkbox) {
            // Les données sont dans la ligne <tr>, pas dans le checkbox
            const refCell = row.cells[1]; // Référence est dans la 2ème colonne
            const desCell = row.cells[2]; // Désignation est dans la 3ème colonne
            const typeCell = row.cells[3]; // Type est dans la 4ème colonne
            const prixCell = row.cells[6]; // Prix est dans la 7ème colonne
            
            const produit = {
                id: checkbox.value, // L'ID est dans la value du checkbox
                reference: refCell ? refCell.textContent.trim() : '',
                designation: desCell ? desCell.textContent.trim() : '',
                prix: prixCell ? parseFloat(prixCell.textContent.replace(' €', '').replace(',', '.')) : 0,
                millesime: row.dataset.millesime || '',
                type: row.dataset.type || '',
                geographie: row.dataset.geographie || ''
            };
            catalogueComplet.push(produit);
        }
    });
    
    console.log('Catalogue chargé:', catalogueComplet.length, 'produits');
}

function initializeFormHandlers() {
    // Gestion de l'affichage conditionnel des champs
    const isAdLivraison = document.getElementById('is_ad_livraison');
    const adresseLivraisonGroup = document.getElementById('adresse_livraison_group');
    
    if (isAdLivraison && adresseLivraisonGroup) {
        isAdLivraison.addEventListener('change', function() {
            adresseLivraisonGroup.style.display = this.checked ? 'block' : 'none';
        });
    }

    // Sélection du client
    const clientSelect = document.getElementById('id_client');
    if (clientSelect) {
        clientSelect.addEventListener('change', loadClientAddresses);
    }

    // Event listener pour la remise client
    const remiseClientInput = document.getElementById('remise_client');
    if (remiseClientInput) {
        remiseClientInput.addEventListener('change', function() {
            const remise = parseFloat(this.value) || 0;
            if (remise >= 0 && remise <= 100) {
                appliquerRemiseParDefaut();
            }
        });
    }

    // Validation du formulaire
    const form = document.getElementById('commandeForm');
    if (form) {
        form.addEventListener('submit', validateCommandeForm);
    }
}

function initializeConditionalFields() {
    initializeFacturationFields();
    initializeExpeditionFields();
}

function initializeFacturationFields() {
    const isFactureCheckbox = document.getElementById('is_facture');
    const dateFacturationGroup = document.getElementById('date_facturation_group');
    
    if (isFactureCheckbox && dateFacturationGroup) {
        isFactureCheckbox.addEventListener('change', function() {
            if (this.checked) {
                dateFacturationGroup.style.display = 'block';
                const dateFacturationInput = document.getElementById('date_facturation');
                if (dateFacturationInput && !dateFacturationInput.value) {
                    dateFacturationInput.value = new Date().toISOString().split('T')[0];
                }
            } else {
                dateFacturationGroup.style.display = 'none';
                const dateFacturationInput = document.getElementById('date_facturation');
                if (dateFacturationInput) {
                    dateFacturationInput.value = '';
                }
            }
        });
    }
}

function initializeExpeditionFields() {
    const isExpedieCheckbox = document.getElementById('is_expedie');
    const dateExpeditionGroup = document.getElementById('date_expedition_group');
    const idSuiviGroup = document.getElementById('id_suivi_group');
    
    if (isExpedieCheckbox) {
        isExpedieCheckbox.addEventListener('change', function() {
            if (this.checked) {
                if (dateExpeditionGroup) dateExpeditionGroup.style.display = 'block';
                if (idSuiviGroup) idSuiviGroup.style.display = 'block';
                
                const dateExpeditionInput = document.getElementById('date_expedition');
                if (dateExpeditionInput && !dateExpeditionInput.value) {
                    dateExpeditionInput.value = new Date().toISOString().split('T')[0];
                }
            } else {
                if (dateExpeditionGroup) dateExpeditionGroup.style.display = 'none';
                if (idSuiviGroup) idSuiviGroup.style.display = 'none';
                
                const dateExpeditionInput = document.getElementById('date_expedition');
                const idSuiviInput = document.getElementById('id_suivi');
                if (dateExpeditionInput) dateExpeditionInput.value = '';
                if (idSuiviInput) idSuiviInput.value = '';
            }
        });
    }
}

// ====================================================================
// GESTION DU CATALOGUE ET MODAL
// ====================================================================

function initializeCatalogueModal() {
    // Event listeners pour les modales
    const selectionModal = document.getElementById('selectionProduitsModal');
    if (selectionModal) {
        selectionModal.addEventListener('shown.bs.modal', function() {
            const searchInput = document.getElementById('rechercheProductsInput');
            if (searchInput) {
                searchInput.focus();
                filtrerProduitsCatalogue();
            }
        });
    }

    // Gestion de la recherche
    const rechercheInput = document.getElementById('rechercheProductsInput');
    if (rechercheInput) {
        rechercheInput.addEventListener('input', filtrerProduitsCatalogue);
    }

    // Gestion des filtres
    const filtres = ['modalFilterMillesime', 'modalFilterType', 'modalFilterGeographie'];
    filtres.forEach(filtreId => {
        const filtre = document.getElementById(filtreId);
        if (filtre) {
            filtre.addEventListener('change', filtrerProduitsCatalogue);
        }
    });

    // Boutons d'action
    const btnAjouter = document.getElementById('ajouterProduitsSelectionnes');
    if (btnAjouter) {
        btnAjouter.addEventListener('click', ajouterProduitsSelectionnes);
    }

    const btnReinitialiser = document.getElementById('reinitialiserFiltres');
    if (btnReinitialiser) {
        btnReinitialiser.addEventListener('click', reinitialiserFiltresModal);
    }
}

function filtrerProduitsCatalogue() {
    const recherche = document.getElementById('rechercheProductsInput')?.value.toLowerCase() || '';
    const millesime = document.getElementById('modalFilterMillesime')?.value || '';
    const type = document.getElementById('modalFilterType')?.value || '';
    const geographie = document.getElementById('modalFilterGeographie')?.value || '';
    
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        // Récupérer les données depuis la ligne et les cellules
        const refCell = row.cells[1];
        const desCell = row.cells[2];
        const reference = refCell ? refCell.textContent.toLowerCase() : '';
        const designation = desCell ? desCell.textContent.toLowerCase() : '';
        const produitMillesime = row.dataset.millesime || '';
        const produitType = row.dataset.type || '';
        const produitGeographie = row.dataset.geographie || '';
        
        let visible = true;
        
        // Filtre de recherche
        if (recherche && !reference.includes(recherche) && !designation.includes(recherche)) {
            visible = false;
        }
        
        // Filtres spécifiques
        if (millesime && produitMillesime !== millesime) visible = false;
        if (type && produitType !== type) visible = false;
        if (geographie && produitGeographie !== geographie) visible = false;
        
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });
    
    // Afficher/masquer le message "aucun produit"
    const messageDiv = document.getElementById('modalAucunProduitMessage');
    if (messageDiv) {
        messageDiv.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

function reinitialiserFiltresModal() {
    const currentYear = new Date().getFullYear();
    const elementsToReset = [
        { id: 'rechercheProductsInput', value: '' },
        { id: 'modalFilterMillesime', value: currentYear },
        { id: 'modalFilterType', value: 'Courrier' },
        { id: 'modalFilterGeographie', value: 'FRANCE' }
    ];
    
    elementsToReset.forEach(element => {
        const el = document.getElementById(element.id);
        if (el) el.value = element.value;
    });
    
    filtrerProduitsCatalogue();
}

function ajouterProduitsSelectionnes() {
    const checkboxes = document.querySelectorAll('#modalCatalogueBody .modal-product-checkbox:checked');
    const remiseParDefaut = parseFloat(document.getElementById('remise_client')?.value) || 0;
    
    if (checkboxes.length === 0) {
        showAlert('Veuillez sélectionner au moins un produit.', 'warning');
        return;
    }
    
    let ajouts = 0;
    
    checkboxes.forEach(checkbox => {
        const row = checkbox.closest('.modal-catalogue-row');
        // Récupérer la quantité depuis l'input avec la bonne classe
        const quantiteInput = row.querySelector('.modal-qte-input');
        const quantite = parseInt(quantiteInput?.value) || 1;
        
        // Récupérer les données depuis les cellules du tableau
        const refCell = row.cells[1];
        const desCell = row.cells[2];
        const prixCell = row.cells[6];
        
        const produit = {
            id: checkbox.value, // L'ID est dans la value du checkbox
            reference: refCell ? refCell.textContent.trim() : '',
            designation: desCell ? desCell.textContent.trim() : '',
            prix: prixCell ? parseFloat(prixCell.textContent.replace(' €', '').replace(',', '.')) : 0
        };
        
        ajouterLigneProduit(produit, quantite, remiseParDefaut);
        checkbox.checked = false;
        if (quantiteInput) quantiteInput.value = 1;
        ajouts++;
    });
    
    if (ajouts > 0) {
        verifierPresenceProduits();
        calculerTotalCommande();
        
        // Fermer la modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('selectionProduitsModal'));
        if (modal) modal.hide();
        
        showAlert(`${ajouts} produit(s) ajouté(s) avec succès !`, 'success');
    }
}

// ====================================================================
// GESTION DU TABLEAU DES PRODUITS
// ====================================================================

function initializeProductTable() {
    // Gestion des modifications en temps réel
    document.addEventListener('input', function(e) {
        if (e.target.matches('.prix-input, .qte-input, .remise-input')) {
            calculerTotalLigne(e.target);
        }
    });

    // Gestion de la suppression et duplication
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-supprimer')) {
            e.preventDefault();
            supprimerLigne(e.target.closest('button'));
        }
        if (e.target.closest('.btn-dupliquer')) {
            e.preventDefault();
            duppliquerLigne(e.target.closest('button'));
        }
    });
}

function ajouterLigneProduit(produit, quantite, remise) {
    ligneCounter++;
    const tbody = document.getElementById('produitsSelectionnesBody');
    
    if (!tbody) return;
    
    const row = document.createElement('tr');
    row.setAttribute('data-produit-id', produit.id);
    row.setAttribute('data-ligne-id', ligneCounter);
    
    const totalLigne = quantite * produit.prix * (1 - remise / 100);
    
    row.innerHTML = `
        <td class="reference">${produit.reference}</td>
        <td class="designation">${produit.designation}</td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control prix-input" 
                       name="prix_${produit.id}_${ligneCounter}" 
                       value="${produit.prix.toFixed(2)}" 
                       step="0.01" min="0"
                       title="Prix unitaire HT">
                <span class="input-group-text">€</span>
            </div>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${produit.id}_${ligneCounter}" 
                   value="${quantite}" 
                   min="1"
                   title="Quantité">
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control remise-input" 
                       name="remise_${produit.id}_${ligneCounter}" 
                       value="${remise.toFixed(1)}" 
                       step="0.1" min="0" max="100"
                       title="Remise en pourcentage">
                <span class="input-group-text">%</span>
            </div>
        </td>
        <td class="total-ligne fw-bold">
            ${totalLigne.toFixed(2)} €
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-primary me-1 btn-dupliquer" title="Dupliquer">
                <i class="fas fa-copy"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger btn-supprimer" title="Supprimer">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
}

function calculerTotalLigne(input) {
    const row = input.closest('tr');
    if (!row) return;
    
    // Empêcher la modification si la ligne est facturée
    if (row.hasAttribute('data-ligne-facturee') && !input.readOnly) {
        showAlert('Impossible de modifier une ligne déjà facturée !', 'warning');
        // Restaurer la valeur d'origine (on pourrait stocker dans data-original-value)
        return;
    }
    
    const prixInput = row.querySelector('.prix-input');
    const qteInput = row.querySelector('.qte-input');
    const remiseInput = row.querySelector('.remise-input');
    const totalCell = row.querySelector('.total-ligne');
    
    if (!prixInput || !qteInput || !remiseInput || !totalCell) return;
    
    const prix = parseFloat(prixInput.value) || 0;
    const qte = parseInt(qteInput.value) || 1;
    const remise = parseFloat(remiseInput.value) || 0;
    
    const total = qte * prix * (1 - remise / 100);
    totalCell.textContent = total.toFixed(2) + ' €';
    
    // Recalculer le total de la commande
    calculerTotalCommande();
}

function duppliquerLigne(button) {
    const row = button.closest('tr');
    const produitId = row.getAttribute('data-produit-id');
    
    // Récupérer les valeurs actuelles
    const prix = parseFloat(row.querySelector('.prix-input').value) || 0;
    const qte = parseInt(row.querySelector('.qte-input').value) || 1;
    const remise = parseFloat(row.querySelector('.remise-input').value) || 0;
    const reference = row.querySelector('.reference').textContent;
    const designation = row.querySelector('.designation').textContent;
    
    const produit = {
        id: produitId,
        reference: reference,
        designation: designation,
        prix: prix
    };
    
    ajouterLigneProduit(produit, qte, remise);
    calculerTotalCommande();
    showAlert('Ligne dupliquée avec succès !', 'success');
}

function supprimerLigne(button) {
    const row = button.closest('tr');
    
    // Vérifier si la ligne est facturée
    if (row.hasAttribute('data-ligne-facturee')) {
        showAlert('Impossible de supprimer une ligne déjà facturée !', 'error');
        return;
    }
    
    if (confirm('Êtes-vous sûr de vouloir supprimer cette ligne ?')) {
        row.remove();
        verifierPresenceProduits();
        calculerTotalCommande();
        showAlert('Ligne supprimée avec succès !', 'success');
    }
}

/**
 * Calculer le total de la commande - FONCTION UNIQUE
 */
function calculerTotalCommande() {
    const totalCells = document.querySelectorAll('#produitsSelectionnesBody .total-ligne');
    let total = 0;
    
    console.log('Calcul total - Cellules trouvées:', totalCells.length);
    
    totalCells.forEach((cell, index) => {
        const cellText = cell.textContent.trim();
        
        // Nettoyer le texte pour extraire le nombre
        const cleanValue = cellText.replace(/[€\s]/g, '').replace(',', '.');
        const value = parseFloat(cleanValue) || 0;
        
        if (value > 0) {
            console.log(`Ligne ${index + 1}: "${cellText}" -> ${value}`);
        }
        total += value;
    });
    
    console.log('Total calculé:', total.toFixed(2), '€');
    
    // Mettre à jour l'affichage du total dans le tableau
    const totalElement = document.getElementById('totalCommande');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
    
    // Mettre à jour le champ montant UNIQUEMENT si il y a des lignes de produits
    const montantInput = document.getElementById('montant');
    if (montantInput && totalCells.length > 0) {
        montantInput.value = total.toFixed(2);
    }
}

function verifierPresenceProduits() {
    const tbody = document.getElementById('produitsSelectionnesBody');
    if (!tbody) return;
    
    const lignes = tbody.querySelectorAll('tr[data-produit-id]');
    const messageVide = document.getElementById('aucunProduitMessage'); // Utiliser le message du template
    
    if (lignes.length === 0) {
        // Afficher le message existant dans le template
        if (messageVide) {
            messageVide.style.display = 'block';
        }
        
        // Supprimer tout message dans le tbody si il existe
        const messageInTbody = document.getElementById('messageAucunProduit');
        if (messageInTbody) {
            messageInTbody.remove();
        }
    } else {
        // Masquer le message du template
        if (messageVide) {
            messageVide.style.display = 'none';
        }
    }
}

function appliquerRemiseParDefaut() {
    const remiseClientInput = document.getElementById('remise_client');
    const remiseParDefaut = parseFloat(remiseClientInput?.value) || 0;
    
    const remiseInputs = document.querySelectorAll('.remise-input');
    remiseInputs.forEach(input => {
        input.value = remiseParDefaut.toFixed(1);
        calculerTotalLigne(input);
    });
    
    if (remiseInputs.length > 0) {
        showAlert(`Remise de ${remiseParDefaut}% appliquée à toutes les lignes`, 'success');
    }
}

// ====================================================================
// FONCTIONNALITÉS DES DÉTAILS
// ====================================================================

function initializeDetailsFeatures() {
    initializeFacturationFeatures();
    initializeExpeditionFeatures();
    initializeGeneralFeatures();
}

function initializeFacturationFeatures() {
    console.log('📄 Initialisation des fonctionnalités de facturation...');
    
    // Gérer la sélection globale dans le tableau principal
    initializeMainTableSelection();
    
    // Gérer la modale de facturation unifiée
    initializeFacturationModal();
    
    // Gérer les calculs automatiques
    initializeFacturationCalculations();
    
    // Gérer la validation du formulaire de facturation
    initializeFacturationFormValidation();
}

function initializeExpeditionFeatures() {
    console.log('🚚 Initialisation des fonctionnalités d\'expédition...');
    
    // Gérer la modale d'expédition si elle existe
    initializeExpeditionModal();
    
    // Gérer le mode d'expédition et numéro de suivi
    initializeExpeditionModeHandling();
}

function initializeGeneralFeatures() {
    // Code général des détails...
    console.log('Fonctionnalités générales initialisées');
}

// ====================================================================
// FONCTIONNALITÉS DE LA LISTE
// ====================================================================

function initializeListFeatures() {
    initializeBulkActions();
    initializeStatusUpdates();
    console.log('Fonctionnalités de liste initialisées');
}

function initializeBulkActions() {
    // Code des actions par lot...
    console.log('Actions par lot initialisées');
}

function initializeStatusUpdates() {
    // Code de mise à jour des statuts...
    console.log('Mises à jour de statuts initialisées');
}

// ====================================================================
// FONCTIONS UTILITAIRES
// ====================================================================

function loadClientAddresses() {
    const clientSelect = document.getElementById('id_client');
    const adresseSelect = document.getElementById('id_adresse');
    
    if (!clientSelect || !adresseSelect || !clientSelect.value) return;
    
    // Ici, vous devriez faire un appel AJAX pour récupérer les adresses du client
    fetch(`/api/clients/${clientSelect.value}/adresses`)
        .then(response => response.json())
        .then(adresses => {
            adresseSelect.innerHTML = '<option value="">Utiliser l\'adresse principale du client</option>';
            adresses.forEach(adresse => {
                const option = document.createElement('option');
                option.value = adresse.id;
                option.textContent = `${adresse.nom} - ${adresse.ville}`;
                adresseSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erreur lors du chargement des adresses:', error);
        });
}

function initializeMainTableSelection() {
    const selectAllMain = document.getElementById('selectAllLines');
    const lignesCheckboxes = document.querySelectorAll('.ligne-checkbox');
    
    if (selectAllMain && lignesCheckboxes.length > 0) {
        console.log(`📋 ${lignesCheckboxes.length} lignes trouvées dans le tableau principal`);
        
        // Gérer la sélection/désélection globale
        selectAllMain.addEventListener('change', function() {
            console.log(`🔄 Sélection globale: ${this.checked ? 'Tout sélectionner' : 'Tout désélectionner'}`);
            lignesCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        
        // Mettre à jour l'état de la case globale quand on change une ligne
        lignesCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateMainSelectAllState();
            });
        });
        
        // Initialiser l'état
        updateMainSelectAllState();
    }
}

function updateMainSelectAllState() {
    const selectAllMain = document.getElementById('selectAllLines');
    const lignesCheckboxes = document.querySelectorAll('.ligne-checkbox');
    const checkedCount = document.querySelectorAll('.ligne-checkbox:checked').length;
    
    if (selectAllMain) {
        selectAllMain.checked = checkedCount === lignesCheckboxes.length && lignesCheckboxes.length > 0;
        selectAllMain.indeterminate = checkedCount > 0 && checkedCount < lignesCheckboxes.length;
    }
}
function calculateFacturationTotal() {
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox:checked');
    let totalFacturation = 0;
    
    lignesCheckboxes.forEach(checkbox => {
        const row = checkbox.closest('tr');
        // Récupérer le total directement depuis la cellule affichée
        const totalCell = row.querySelector('.ligne-total strong');
        if (totalCell) {
            const totalText = totalCell.textContent.replace(' €', '').replace(',', '.');
            const totalLigne = parseFloat(totalText) || 0;
            totalFacturation += totalLigne;
        }
    });
    
    // Mettre à jour le total général
    const totalElement = document.getElementById('totalFacturation');
    if (totalElement) {
        totalElement.textContent = totalFacturation.toFixed(2) + ' €';
    }
    
    return totalFacturation;
}

function updateFacturationUI() {
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const lignesSelectionnees = document.querySelectorAll('.ligne-facturation-checkbox:checked');
    const totalLignes = lignesCheckboxes.length;
    const lignesChecked = lignesSelectionnees.length;
    
    // Éléments UI à mettre à jour
    const alertPartielle = document.getElementById('alertFacturationPartielle');
    const infoFacturation = document.getElementById('infoFacturation');
    const btnConfirmer = document.getElementById('btnConfirmerFacturation');
    
    // Déterminer si c'est une facturation partielle
    const isFacturationPartielle = lignesChecked > 0 && lignesChecked < totalLignes;
    
    // Mettre à jour l'alerte de facturation partielle
    if (alertPartielle) {
        if (isFacturationPartielle) {
            alertPartielle.style.display = 'block';
        } else {
            alertPartielle.style.display = 'none';
        }
    }
    
    // Mettre à jour le texte d'information
    if (infoFacturation) {
        if (lignesChecked === 0) {
            infoFacturation.textContent = 'Aucune ligne sélectionnée pour la facturation.';
        } else if (isFacturationPartielle) {
            infoFacturation.textContent = `Facturation partielle : ${lignesChecked} ligne(s) sur ${totalLignes} sélectionnée(s).`;
        } else {
            infoFacturation.textContent = 'Facturation complète : toutes les lignes seront facturées.';
        }
    }
    
    // Activer/désactiver le bouton de confirmation
    if (btnConfirmer) {
        btnConfirmer.disabled = lignesChecked === 0;
        
        if (lignesChecked === 0) {
            btnConfirmer.innerHTML = '<i class="bi bi-receipt me-1"></i>Aucune ligne sélectionnée';
        } else if (isFacturationPartielle) {
            btnConfirmer.innerHTML = `<i class="bi bi-receipt me-1"></i>Facturer ${lignesChecked} ligne(s)`;
        } else {
            btnConfirmer.innerHTML = '<i class="bi bi-receipt me-1"></i>Facturer toutes les lignes';
        }
    }
}

function initializeFacturationFormValidation() {
    const formFacturation = document.getElementById('facturationForm');
    
    if (!formFacturation) {
        console.log('⚠️ Formulaire de facturation non trouvé');
        return;
    }
    
    console.log('✅ Validation du formulaire de facturation configurée');
    
    formFacturation.addEventListener('submit', function(e) {
        const checkedBoxes = formFacturation.querySelectorAll('input[name="lignes_facturees"]:checked');
        const dateFacturation = document.getElementById('date_facturation');
        
        console.log(`🔍 Validation: ${checkedBoxes.length} ligne(s) sélectionnée(s)`);
        
        // Vérifier qu'au moins une ligne est sélectionnée
        if (checkedBoxes.length === 0) {
            e.preventDefault();
            console.log('❌ Aucune ligne sélectionnée');
            showAlert('Veuillez sélectionner au moins une ligne à facturer.', 'warning');
            return false;
        }
        
        // Vérifier la date de facturation
        if (!dateFacturation || !dateFacturation.value) {
            e.preventDefault();
            console.log('❌ Date de facturation manquante');
            showAlert('Veuillez saisir une date de facturation.', 'warning');
            return false;
        }
        
        console.log('✅ Formulaire valide, soumission...');
        
        // Optionnel : afficher un indicateur de chargement
        const submitBtn = formFacturation.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Facturation en cours...';
        }
        
        return true;
    });
}


function initializeFacturationModal() {
    console.log('📄 Initialisation de la modale de facturation simplifiée...');
    
    const modal = document.getElementById('facturationModal');
    const selectAllFacturation = document.getElementById('selectAllFacturation');
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    
    console.log('🔍 DEBUG éléments trouvés:');
    console.log('  - modal:', modal ? 'Trouvée' : 'NON TROUVÉE');
    console.log('  - selectAllFacturation:', selectAllFacturation ? 'Trouvée' : 'NON TROUVÉE'); 
    console.log('  - lignesCheckboxes:', lignesCheckboxes.length, 'éléments');
    
    if (!modal) {
        console.warn('⚠️ Modale de facturation non trouvée');
        return;
    }
    
    console.log(`💰 Modale de facturation trouvée avec ${lignesCheckboxes.length} lignes`);
    
    // Gestion du "Tout sélectionner"
    if (selectAllFacturation) {
        console.log('✅ Configuration du "Tout sélectionner"');
        selectAllFacturation.addEventListener('change', function() {
            console.log(`🔄 Tout sélectionner activé: ${this.checked}`);
            lignesCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            
            updateFacturationUI();
            calculateFacturationTotal();
        });
    } else {
        console.warn('⚠️ Checkbox "Tout sélectionner" non trouvée');
    }
    
    // Gestion des checkboxes individuelles
    lignesCheckboxes.forEach((checkbox, index) => {
        console.log(`✅ Configuration checkbox ligne ${index + 1}`);
        checkbox.addEventListener('change', function() {
            console.log(`🔄 Checkbox ligne modifiée: ${this.checked}`);
            
            // Mettre à jour le "Tout sélectionner"
            const allChecked = Array.from(lignesCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(lignesCheckboxes).some(cb => cb.checked);
            
            if (selectAllFacturation) {
                selectAllFacturation.checked = allChecked;
                selectAllFacturation.indeterminate = someChecked && !allChecked;
            }
            
            updateFacturationUI();
            calculateFacturationTotal();
        });
    });
    
    // Initialiser l'état au chargement de la modale
    modal.addEventListener('shown.bs.modal', function() {
        console.log('📄 Modale de facturation ouverte');
        updateFacturationUI();
        calculateFacturationTotal();
    });
}

function validateCommandeForm(e) {
    const form = e.target;
    const clientSelect = document.getElementById('id_client');
    const produitsRows = document.querySelectorAll('#produitsSelectionnesBody tr[data-produit-id]');
    
    let isValid = true;
    let errors = [];
    
    // Vérifier qu'un client est sélectionné
    if (!clientSelect || !clientSelect.value) {
        errors.push('Veuillez sélectionner un client.');
        isValid = false;
    }
    
    // Vérifier qu'au moins un produit est ajouté
    if (produitsRows.length === 0) {
        errors.push('Veuillez ajouter au moins un produit à la commande.');
        isValid = false;
    }
    
    if (!isValid) {
        e.preventDefault();
        showAlert(errors.join('<br>'), 'error');
        return false;
    }
    
    return true;
}

function showAlert(message, type = 'info') {
    // Supprimer les alertes existantes
    const existingAlerts = document.querySelectorAll('.alert-floating');
    existingAlerts.forEach(alert => alert.remove());
    
    // Créer la nouvelle alerte
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-floating position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    const icon = {
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'error': 'bi-x-circle',
        'info': 'bi-info-circle'
    }[type] || 'bi-info-circle';
    
    alert.innerHTML = `
        <i class="bi ${icon} me-2"></i>${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// ====================================================================
// FONCTIONS MANQUANTES POUR LES MODALES
// ====================================================================

function initializeExpeditionModeHandling() {
    console.log('🚚 Initialisation de la gestion des modes d\'expédition...');
    
    const envoisRadios = document.querySelectorAll('input[name="mode_expedition"]');
    const numeroSuiviContainer = document.getElementById('numero_suivi_container');
    const alertMontant80 = document.getElementById('alert_montant_80');
    
    if (envoisRadios.length === 0) {
        console.warn('⚠️ Aucun radio button mode_expedition trouvé');
        return;
    }
    
    function handleModeChange() {
        const selectedMode = document.querySelector('input[name="mode_expedition"]:checked')?.value;
        const montantCommande = parseFloat(document.querySelector('[data-montant-commande]')?.dataset.montantCommande || 0);
        const submitButton = document.querySelector('#expeditionForm button[type="submit"]');
        
        console.log(`📋 Mode d'expédition: ${selectedMode}, montant: ${montantCommande}€`);
        
        // Gérer l'affichage du numéro de suivi
        if (numeroSuiviContainer) {
            const numeroSuiviInput = document.getElementById('numero_suivi_expedition');
            if (selectedMode === 'envoi_suivi') {
                numeroSuiviContainer.style.display = 'block';
                if (numeroSuiviInput) numeroSuiviInput.required = true;
            } else {
                numeroSuiviContainer.style.display = 'none';
                if (numeroSuiviInput) numeroSuiviInput.required = false;
            }
        }
        
        // Gérer l'alerte pour montant > 80€
        if (montantCommande > 80 && selectedMode === 'envoi_simple') {
            if (alertMontant80) alertMontant80.style.display = 'block';
            if (submitButton) submitButton.disabled = true;
        } else {
            if (alertMontant80) alertMontant80.style.display = 'none';
            if (submitButton) submitButton.disabled = false;
        }
    }
    
    // Écouter les changements
    envoisRadios.forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });
    
    // Initialiser l'état
    handleModeChange();
}

function initializeExpeditionModal() {
    console.log('🚚 Initialisation de la modale d\'expédition...');
    
    const modal = document.getElementById('expeditionModal');
    const selectAllExpedition = document.getElementById('selectAllExpedition');
    const lignesCheckboxes = document.querySelectorAll('.ligne-expedition');
    const formExpedition = document.getElementById('expeditionForm');
    
    console.log('🔍 DEBUG éléments trouvés:');
    console.log('  - modal:', modal ? 'Trouvée' : 'NON TROUVÉE');
    console.log('  - selectAllExpedition:', selectAllExpedition ? 'Trouvée' : 'NON TROUVÉE'); 
    console.log('  - lignesCheckboxes:', lignesCheckboxes.length, 'éléments');
    console.log('  - formExpedition:', formExpedition ? 'Trouvé' : 'NON TROUVÉ');
    
    if (!modal) {
        console.warn('⚠️ Modale d\'expédition non trouvée');
        return;
    }
    
    // Gestion du "Tout sélectionner" pour l'expédition
    if (selectAllExpedition && lignesCheckboxes.length > 0) {
        console.log('✅ Configuration du "Tout sélectionner" expédition');
        selectAllExpedition.addEventListener('change', function() {
            console.log(`🔄 Tout sélectionner expédition: ${this.checked}`);
            lignesCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        
        // Gestion des checkboxes individuelles
        lignesCheckboxes.forEach((checkbox, index) => {
            console.log(`✅ Configuration checkbox expédition ligne ${index + 1}`);
            checkbox.addEventListener('change', function() {
                console.log(`🔄 Checkbox expédition ligne modifiée: ${this.checked}`);
                
                // Mettre à jour le "Tout sélectionner"
                const allChecked = Array.from(lignesCheckboxes).every(cb => cb.checked);
                const someChecked = Array.from(lignesCheckboxes).some(cb => cb.checked);
                
                selectAllExpedition.checked = allChecked;
                selectAllExpedition.indeterminate = someChecked && !allChecked;
            });
        });
        
        // Initialiser l'état au chargement de la modale
        modal.addEventListener('shown.bs.modal', function() {
            console.log('🚚 Modale d\'expédition ouverte');
            // Vérifier l'état initial
            const allChecked = Array.from(lignesCheckboxes).every(cb => cb.checked);
            selectAllExpedition.checked = allChecked;
        });
    }
    
    if (!formExpedition) {
        console.warn('⚠️ Formulaire d\'expédition non trouvé');
        return;
    }
    
    // Validation du formulaire d'expédition
    formExpedition.addEventListener('submit', function(e) {
        const selectedMode = document.querySelector('input[name="mode_expedition"]:checked');
        const dateExpedition = document.getElementById('date_expedition_modale');
        
        if (!selectedMode) {
            e.preventDefault();
            showAlert('Veuillez sélectionner un mode d\'expédition.', 'error');
            return false;
        }
        
        if (!dateExpedition || !dateExpedition.value) {
            e.preventDefault();
            showAlert('Veuillez sélectionner une date d\'expédition.', 'error');
            return false;
        }
        
        if (selectedMode.value === 'envoi_suivi') {
            const numeroSuivi = document.getElementById('numero_suivi_expedition');
            if (!numeroSuivi || !numeroSuivi.value.trim()) {
                e.preventDefault();
                showAlert('Le numéro de suivi est obligatoire pour un envoi suivi.', 'error');
                return false;
            }
        }
        
        return true;
    });
}

function initializeFacturationCalculations() {
    console.log('💰 Initialisation des calculs de facturation...');
    
    // Les calculs sont déjà gérés dans calculateFacturationTotal()
    // Cette fonction peut être étendue si nécessaire
}

// ====================================================================
// EXPOSITION DES FONCTIONS GLOBALES (pour compatibilité)
// ====================================================================

// Exposition des fonctions nécessaires aux templates
window.calculerTotalLigne = calculerTotalLigne;
window.duppliquerLigne = duppliquerLigne;
window.supprimerLigne = supprimerLigne;
window.calculerTotalCommande = calculerTotalCommande;
window.filtrerProduitsCatalogue = filtrerProduitsCatalogue;
window.reinitialiserRecherche = function() {
    document.getElementById('rechercheProductsInput').value = '';
    filtrerProduitsCatalogue();
};
window.reinitialiserFiltresModal = reinitialiserFiltresModal;
window.ajouterProduitsSelectionnes = ajouterProduitsSelectionnes;

// Fonctions déjà exposées par initializeUtilityFunctions
// window.copierNumeroSuivi est défini dans initializeUtilityFunctions

// Fonction de debug
// window.debugCommande est défini plus haut

console.log('✅ Module commandes unifié chargé avec succès!');
