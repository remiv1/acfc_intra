/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour le module Commandes
 * ====================================================================
 * 
 * Fonctionnalités JavaScript pour la gestion des commandes :
 * - Formulaire dynamique de commande
 * - Gestion de la fenêtre modale du catalogue
 * - Filtrage des produits
 * - Calcul automatique des montants
 * - Actions par lot
 * - Validation côté client
 * 
 * Dépendances : Bootstrap 5, Font Awesome 6
 * ====================================================================
 */

// Variables globales
let commandeData = {
    produits: [],
    total: 0
};

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeFormHandlers();
    initializeCatalogueModal();
    initializeProductTable();
    initializeBulkActions();
    initializeStatusUpdates();
    loadExistingProducts();
});

// ====================================================================
// GESTIONNAIRES DU FORMULAIRE PRINCIPAL
// ====================================================================

function initializeFormHandlers() {
    // Gestion de l'affichage conditionnel des champs
    const isAdLivraison = document.getElementById('is_ad_livraison');
    const adresseLivraisonGroup = document.getElementById('adresse_livraison_group');
    
    if (isAdLivraison && adresseLivraisonGroup) {
        isAdLivraison.addEventListener('change', function() {
            adresseLivraisonGroup.style.display = this.checked ? 'block' : 'none';
            if (this.checked) {
                loadClientAddresses();
            }
        });
    }

    // Gestion de l'affichage des dates selon les statuts
    const isFacture = document.getElementById('is_facture');
    const dateFacturationGroup = document.getElementById('date_facturation_group');
    
    if (isFacture && dateFacturationGroup) {
        isFacture.addEventListener('change', function() {
            dateFacturationGroup.style.display = this.checked ? 'block' : 'none';
            if (this.checked && !document.getElementById('date_facturation').value) {
                document.getElementById('date_facturation').value = new Date().toISOString().split('T')[0];
            }
        });
    }

    const isExpedie = document.getElementById('is_expedie');
    const dateExpeditionGroup = document.getElementById('date_expedition_group');
    const idSuiviGroup = document.getElementById('id_suivi_group');
    
    if (isExpedie && dateExpeditionGroup && idSuiviGroup) {
        isExpedie.addEventListener('change', function() {
            const display = this.checked ? 'block' : 'none';
            dateExpeditionGroup.style.display = display;
            idSuiviGroup.style.display = display;
            
            if (this.checked && !document.getElementById('date_expedition').value) {
                document.getElementById('date_expedition').value = new Date().toISOString().split('T')[0];
            }
        });
    }

    // Sélection du client
    const clientSelect = document.getElementById('id_client');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            loadClientAddresses();
        });
    }

    // Validation du formulaire
    const form = document.getElementById('commandeForm');
    if (form) {
        form.addEventListener('submit', validateCommandeForm);
    }
}

// ====================================================================
// GESTION DE LA FENÊTRE MODALE DU CATALOGUE
// ====================================================================

function initializeCatalogueModal() {
    // Filtres du catalogue
    const filterMillesime = document.getElementById('filter_millesime');
    const filterTypeProduit = document.getElementById('filter_type_produit');
    const filterGeographie = document.getElementById('filter_geographie');
    
    if (filterMillesime) {
        filterMillesime.addEventListener('change', filterCatalogueProducts);
    }
    if (filterTypeProduit) {
        filterTypeProduit.addEventListener('change', filterCatalogueProducts);
    }
    if (filterGeographie) {
        filterGeographie.addEventListener('change', filterCatalogueProducts);
    }

    // Sélection de tous les produits
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.product-checkbox:not(:disabled)');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                toggleQuantityInput(checkbox);
                toggleRowSelection(checkbox.closest('tr'), this.checked);
            });
        });
    }

    // Gestion des checkboxes individuels
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('product-checkbox')) {
            toggleQuantityInput(e.target);
            toggleRowSelection(e.target.closest('tr'), e.target.checked);
            updateSelectAllState();
        }
    });

    // Bouton d'ajout des produits sélectionnés
    const addSelectedBtn = document.getElementById('addSelectedProducts');
    if (addSelectedBtn) {
        addSelectedBtn.addEventListener('click', addSelectedProducts);
    }
}

// ====================================================================
// GESTION DU TABLEAU DES PRODUITS
// ====================================================================

function initializeProductTable() {
    // Gestion des modifications en temps réel
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('qte-input') || 
            e.target.classList.contains('prix-input') || 
            e.target.classList.contains('remise-input')) {
            updateProductTotal(e.target.closest('tr'));
            updateCommandeTotal();
        }
    });

    // Gestion de la suppression de produits
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-product') || 
            e.target.parentElement.classList.contains('remove-product')) {
            removeProduct(e.target.closest('tr'));
        }
    });
}

// ====================================================================
// ACTIONS PAR LOT
// ====================================================================

function initializeBulkActions() {
    // Sélection/désélection de toutes les commandes
    const selectAllCommandes = document.getElementById('selectAll');
    if (selectAllCommandes) {
        selectAllCommandes.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.commande-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });
    }

    // Gestion des checkboxes individuels
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('commande-checkbox')) {
            updateBulkActionsVisibility();
            updateSelectAllCommandesState();
        }
    });

    // Actions par lot
    const bulkFacture = document.getElementById('bulk_facture');
    const bulkExpedie = document.getElementById('bulk_expedie');
    const clearSelection = document.getElementById('clear_selection');

    if (bulkFacture) {
        bulkFacture.addEventListener('click', () => bulkUpdateStatus('facture'));
    }
    if (bulkExpedie) {
        bulkExpedie.addEventListener('click', () => bulkUpdateStatus('expedie'));
    }
    if (clearSelection) {
        clearSelection.addEventListener('click', clearAllSelections);
    }
}

// ====================================================================
// GESTION DES MISES À JOUR DE STATUT
// ====================================================================

function initializeStatusUpdates() {
    // Génération de facture individuelle
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('generate-facture') || 
            e.target.parentElement.classList.contains('generate-facture')) {
            const commandeId = e.target.dataset.commandeId || e.target.parentElement.dataset.commandeId;
            showFactureModal(commandeId);
        }
    });

    // Marquage comme expédiée
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('mark-expedie') || 
            e.target.parentElement.classList.contains('mark-expedie')) {
            const commandeId = e.target.dataset.commandeId || e.target.parentElement.dataset.commandeId;
            showExpeditionModal(commandeId);
        }
    });

    // Suppression de commande
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-commande') || 
            e.target.parentElement.classList.contains('delete-commande')) {
            const commandeId = e.target.dataset.commandeId || e.target.parentElement.dataset.commandeId;
            confirmDeleteCommande(commandeId);
        }
    });

    // Confirmations des modales
    const confirmFacture = document.getElementById('confirmFacture');
    const confirmExpedition = document.getElementById('confirmExpedition');

    if (confirmFacture) {
        confirmFacture.addEventListener('click', processFactureGeneration);
    }
    if (confirmExpedition) {
        confirmExpedition.addEventListener('click', processExpeditionUpdate);
    }
}

// ====================================================================
// FONCTIONS UTILITAIRES - FILTRAGE DU CATALOGUE
// ====================================================================

function filterCatalogueProducts() {
    const millesime = document.getElementById('filter_millesime').value;
    const typeProduit = document.getElementById('filter_type_produit').value;
    const geographie = document.getElementById('filter_geographie').value;

    const rows = document.querySelectorAll('#catalogueTable tbody tr');
    
    rows.forEach(row => {
        const rowMillesime = row.dataset.millesime;
        const rowType = row.dataset.type;
        const rowGeographie = row.dataset.geographie;

        const showRow = (
            (!millesime || rowMillesime === millesime) &&
            (!typeProduit || rowType === typeProduit) &&
            (!geographie || rowGeographie === geographie)
        );

        row.style.display = showRow ? '' : 'none';
        
        // Décocher les produits masqués
        if (!showRow) {
            const checkbox = row.querySelector('.product-checkbox');
            if (checkbox && checkbox.checked) {
                checkbox.checked = false;
                toggleQuantityInput(checkbox);
                toggleRowSelection(row, false);
            }
        }
    });

    updateSelectAllState();
}

function toggleQuantityInput(checkbox) {
    const row = checkbox.closest('tr');
    const quantityInput = row.querySelector('.quantity-input');
    
    if (quantityInput) {
        quantityInput.disabled = !checkbox.checked;
        if (!checkbox.checked) {
            quantityInput.value = 1;
        }
    }
}

function toggleRowSelection(row, selected) {
    if (selected) {
        row.classList.add('selected');
    } else {
        row.classList.remove('selected');
    }
}

function updateSelectAllState() {
    const selectAll = document.getElementById('selectAll');
    const visibleCheckboxes = document.querySelectorAll('#catalogueTable tbody tr:not([style*="display: none"]) .product-checkbox');
    const checkedVisibleCheckboxes = document.querySelectorAll('#catalogueTable tbody tr:not([style*="display: none"]) .product-checkbox:checked');
    
    if (selectAll && visibleCheckboxes.length > 0) {
        selectAll.checked = visibleCheckboxes.length === checkedVisibleCheckboxes.length;
        selectAll.indeterminate = checkedVisibleCheckboxes.length > 0 && checkedVisibleCheckboxes.length < visibleCheckboxes.length;
    }
}

// ====================================================================
// FONCTIONS UTILITAIRES - GESTION DES PRODUITS
// ====================================================================

function addSelectedProducts() {
    const selectedCheckboxes = document.querySelectorAll('.product-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        showAlert('Veuillez sélectionner au moins un produit.', 'warning');
        return;
    }

    selectedCheckboxes.forEach(checkbox => {
        const row = checkbox.closest('tr');
        const quantityInput = row.querySelector('.quantity-input');
        
        const produit = {
            id: checkbox.dataset.id,
            reference: checkbox.dataset.ref,
            designation: checkbox.dataset.designation,
            prix_unitaire: parseFloat(checkbox.dataset.prix),
            quantite: parseInt(quantityInput.value) || 1,
            remise: 0.10 // Remise par défaut
        };

        addProductToTable(produit);
    });

    // Fermer la modale et réinitialiser les sélections
    const modal = bootstrap.Modal.getInstance(document.getElementById('catalogueModal'));
    modal.hide();
    clearCatalogueSelection();
    
    updateCommandeTotal();
    showAlert('Produits ajoutés avec succès !', 'success');
}

function addProductToTable(produit) {
    const tableBody = document.getElementById('produitsTableBody');
    const emptyRow = document.getElementById('emptyRow');
    
    // Supprimer la ligne vide si elle existe
    if (emptyRow) {
        emptyRow.remove();
    }

    // Vérifier si le produit existe déjà
    const existingRow = tableBody.querySelector(`tr[data-product-id="${produit.id}"]`);
    if (existingRow) {
        // Augmenter la quantité du produit existant
        const qteInput = existingRow.querySelector('.qte-input');
        qteInput.value = parseInt(qteInput.value) + produit.quantite;
        updateProductTotal(existingRow);
        return;
    }

    // Créer une nouvelle ligne
    const newRow = document.createElement('tr');
    newRow.dataset.productId = produit.id;
    
    const prixTotal = produit.quantite * produit.prix_unitaire * (1 - produit.remise);
    
    newRow.innerHTML = `
        <td><code>${produit.reference}</code></td>
        <td>${produit.designation}</td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${produit.id}" value="${produit.quantite}" min="1" style="width: 80px;">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm prix-input" 
                   name="prix_unitaire_${produit.id}" value="${produit.prix_unitaire.toFixed(4)}" step="0.0001" style="width: 100px;">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm remise-input" 
                   name="remise_${produit.id}" value="${(produit.remise * 100).toFixed(2)}" min="0" max="100" step="0.01" style="width: 80px;">
        </td>
        <td class="total-ht">${prixTotal.toFixed(2)} €</td>
        <td>
            <button type="button" class="btn btn-danger btn-sm remove-product">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tableBody.appendChild(newRow);
}

function removeProduct(row) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce produit de la commande ?')) {
        row.remove();
        
        // Réafficher la ligne vide si aucun produit
        const tableBody = document.getElementById('produitsTableBody');
        if (tableBody.children.length === 0) {
            tableBody.innerHTML = `
                <tr id="emptyRow">
                    <td colspan="7" class="text-center text-muted">
                        Aucun produit ajouté. Cliquez sur "Ajouter des produits" pour commencer.
                    </td>
                </tr>
            `;
        }
        
        updateCommandeTotal();
    }
}

function updateProductTotal(row) {
    const qteInput = row.querySelector('.qte-input');
    const prixInput = row.querySelector('.prix-input');
    const remiseInput = row.querySelector('.remise-input');
    const totalCell = row.querySelector('.total-ht');
    
    const quantite = parseInt(qteInput.value) || 0;
    const prixUnitaire = parseFloat(prixInput.value) || 0;
    const remise = parseFloat(remiseInput.value) / 100 || 0;
    
    const total = quantite * prixUnitaire * (1 - remise);
    totalCell.textContent = total.toFixed(2) + ' €';
}

function updateCommandeTotal() {
    const totalCells = document.querySelectorAll('#produitsTableBody .total-ht');
    let total = 0;
    
    totalCells.forEach(cell => {
        const value = parseFloat(cell.textContent.replace(' €', '')) || 0;
        total += value;
    });
    
    document.getElementById('totalCommande').textContent = total.toFixed(2) + ' €';
    document.getElementById('montant').value = total.toFixed(2);
}

function loadExistingProducts() {
    // Calculer le total si des produits existent déjà
    const existingRows = document.querySelectorAll('#produitsTableBody tr:not(#emptyRow)');
    existingRows.forEach(row => {
        updateProductTotal(row);
    });
    updateCommandeTotal();
}

// ====================================================================
// FONCTIONS UTILITAIRES - ADRESSES CLIENT
// ====================================================================

function loadClientAddresses() {
    const clientSelect = document.getElementById('id_client');
    const adresseSelect = document.getElementById('id_adresse');
    
    if (!clientSelect || !adresseSelect || !clientSelect.value) return;
    
    // Ici, vous devriez faire un appel AJAX pour récupérer les adresses du client
    // Pour l'exemple, on simule avec des données statiques
    fetch(`/api/clients/${clientSelect.value}/adresses`)
        .then(response => response.json())
        .then(adresses => {
            adresseSelect.innerHTML = '<option value="">Utiliser l\'adresse principale du client</option>';
            adresses.forEach(adresse => {
                const option = document.createElement('option');
                option.value = adresse.id;
                option.textContent = `${adresse.adresse_l1}, ${adresse.code_postal} ${adresse.ville}`;
                adresseSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erreur lors du chargement des adresses:', error);
        });
}

// ====================================================================
// FONCTIONS UTILITAIRES - ACTIONS PAR LOT
// ====================================================================

function updateBulkActionsVisibility() {
    const selectedCheckboxes = document.querySelectorAll('.commande-checkbox:checked');
    const bulkActions = document.getElementById('bulk_actions');
    const selectedCount = document.getElementById('selected_count');
    
    if (bulkActions && selectedCount) {
        if (selectedCheckboxes.length > 0) {
            selectedCount.textContent = selectedCheckboxes.length;
            bulkActions.style.display = 'block';
        } else {
            bulkActions.style.display = 'none';
        }
    }
}

function updateSelectAllCommandesState() {
    const selectAll = document.getElementById('selectAll');
    const allCheckboxes = document.querySelectorAll('.commande-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.commande-checkbox:checked');
    
    if (selectAll && allCheckboxes.length > 0) {
        selectAll.checked = allCheckboxes.length === checkedCheckboxes.length;
        selectAll.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
    }
}

function clearAllSelections() {
    const checkboxes = document.querySelectorAll('.commande-checkbox, #selectAll');
    checkboxes.forEach(checkbox => checkbox.checked = false);
    updateBulkActionsVisibility();
}

function bulkUpdateStatus(action) {
    const selectedIds = Array.from(document.querySelectorAll('.commande-checkbox:checked'))
                             .map(cb => cb.value);
    
    if (selectedIds.length === 0) return;
    
    const actionText = action === 'facture' ? 'facturer' : 'marquer comme expédiées';
    
    if (confirm(`Êtes-vous sûr de vouloir ${actionText} ${selectedIds.length} commande(s) ?`)) {
        // Ici, vous devriez faire un appel AJAX pour mettre à jour les commandes
        fetch(`/api/commandes/bulk-update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action,
                commande_ids: selectedIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`${selectedIds.length} commande(s) mise(s) à jour avec succès.`, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert('Erreur lors de la mise à jour.', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showAlert('Erreur lors de la mise à jour.', 'error');
        });
    }
}

// ====================================================================
// FONCTIONS UTILITAIRES - MODALES ET CONFIRMATIONS
// ====================================================================

function showFactureModal(commandeId) {
    const modal = new bootstrap.Modal(document.getElementById('confirmFactureModal'));
    document.getElementById('confirmFacture').dataset.commandeId = commandeId;
    modal.show();
}

function showExpeditionModal(commandeId) {
    const modal = new bootstrap.Modal(document.getElementById('confirmExpeditionModal'));
    document.getElementById('confirmExpedition').dataset.commandeId = commandeId;
    modal.show();
}

function processFactureGeneration() {
    const commandeId = document.getElementById('confirmFacture').dataset.commandeId;
    const dateFacturation = document.getElementById('date_facturation').value || new Date().toISOString().split('T')[0];
    
    // Appel AJAX pour générer la facture
    fetch(`/api/commandes/${commandeId}/generate-facture`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            date_facturation: dateFacturation
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Facture générée avec succès !', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert('Erreur lors de la génération de la facture.', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showAlert('Erreur lors de la génération de la facture.', 'error');
    });
    
    bootstrap.Modal.getInstance(document.getElementById('confirmFactureModal')).hide();
}

function processExpeditionUpdate() {
    const commandeId = document.getElementById('confirmExpedition').dataset.commandeId;
    const dateExpedition = document.getElementById('expedition_date').value || new Date().toISOString().split('T')[0];
    const trackingId = document.getElementById('tracking_id').value;
    
    // Appel AJAX pour marquer comme expédiée
    fetch(`/api/commandes/${commandeId}/mark-expedie`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            date_expedition: dateExpedition,
            id_suivi: trackingId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Commande marquée comme expédiée !', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert('Erreur lors de la mise à jour.', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showAlert('Erreur lors de la mise à jour.', 'error');
    });
    
    bootstrap.Modal.getInstance(document.getElementById('confirmExpeditionModal')).hide();
}

function confirmDeleteCommande(commandeId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette commande ? Cette action est irréversible.')) {
        fetch(`/api/commandes/${commandeId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Commande supprimée avec succès.', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert('Erreur lors de la suppression.', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showAlert('Erreur lors de la suppression.', 'error');
        });
    }
}

// ====================================================================
// FONCTIONS UTILITAIRES - VALIDATION ET HELPERS
// ====================================================================

function validateCommandeForm(e) {
    const clientSelect = document.getElementById('id_client');
    const produitsTable = document.getElementById('produitsTableBody');
    
    // Vérifier qu'un client est sélectionné
    if (!clientSelect.value) {
        e.preventDefault();
        showAlert('Veuillez sélectionner un client.', 'error');
        clientSelect.focus();
        return false;
    }
    
    // Vérifier qu'au moins un produit est ajouté
    const productRows = produitsTable.querySelectorAll('tr:not(#emptyRow)');
    if (productRows.length === 0) {
        e.preventDefault();
        showAlert('Veuillez ajouter au moins un produit à la commande.', 'error');
        return false;
    }
    
    // Vérifier les quantités et prix
    let hasErrors = false;
    productRows.forEach(row => {
        const qteInput = row.querySelector('.qte-input');
        const prixInput = row.querySelector('.prix-input');
        
        if (!qteInput.value || parseInt(qteInput.value) <= 0) {
            hasErrors = true;
            qteInput.classList.add('is-invalid');
        } else {
            qteInput.classList.remove('is-invalid');
        }
        
        if (!prixInput.value || parseFloat(prixInput.value) <= 0) {
            hasErrors = true;
            prixInput.classList.add('is-invalid');
        } else {
            prixInput.classList.remove('is-invalid');
        }
    });
    
    if (hasErrors) {
        e.preventDefault();
        showAlert('Veuillez corriger les erreurs dans le tableau des produits.', 'error');
        return false;
    }
    
    return true;
}

function clearCatalogueSelection() {
    const checkboxes = document.querySelectorAll('.product-checkbox');
    const selectAll = document.getElementById('selectAll');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
        toggleQuantityInput(checkbox);
        toggleRowSelection(checkbox.closest('tr'), false);
    });
    
    if (selectAll) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
    }
}

function showAlert(message, type = 'info') {
    // Créer une alerte Bootstrap dynamique
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertContainer.style.top = '20px';
    alertContainer.style.right = '20px';
    alertContainer.style.zIndex = '9999';
    alertContainer.style.minWidth = '300px';
    
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertContainer);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.remove();
        }
    }, 5000);
}

// ====================================================================
// FONCTIONS POUR LES PAGES DE DÉTAILS
// ====================================================================

// Gestion des boutons sur la page de détails
document.addEventListener('DOMContentLoaded', function() {
    const generateFactureBtn = document.getElementById('generateFacture');
    const markExpeditionBtn = document.getElementById('markExpedition');
    
    if (generateFactureBtn) {
        generateFactureBtn.addEventListener('click', function() {
            const commandeId = this.dataset.commandeId;
            showFactureModal(commandeId);
        });
    }
    
    if (markExpeditionBtn) {
        markExpeditionBtn.addEventListener('click', function() {
            const commandeId = this.dataset.commandeId;
            showExpeditionModal(commandeId);
        });
    }
    
    // Gestion des confirmations sur la page de détails
    const confirmFactureGeneration = document.getElementById('confirmFactureGeneration');
    const confirmExpeditionAction = document.getElementById('confirmExpeditionAction');
    
    if (confirmFactureGeneration) {
        confirmFactureGeneration.addEventListener('click', function() {
            const commandeId = document.getElementById('generateFacture').dataset.commandeId;
            const dateFacturation = document.getElementById('date_facturation').value;
            
            fetch(`/api/commandes/${commandeId}/generate-facture`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date_facturation: dateFacturation })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Facture générée avec succès !', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showAlert('Erreur lors de la génération de la facture.', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showAlert('Erreur lors de la génération de la facture.', 'error');
            });
            
            bootstrap.Modal.getInstance(document.getElementById('confirmFactureModal')).hide();
        });
    }
    
    if (confirmExpeditionAction) {
        confirmExpeditionAction.addEventListener('click', function() {
            const commandeId = document.getElementById('markExpedition').dataset.commandeId;
            const dateExpedition = document.getElementById('date_expedition').value;
            const numeroSuivi = document.getElementById('numero_suivi').value;
            
            fetch(`/api/commandes/${commandeId}/mark-expedie`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    date_expedition: dateExpedition,
                    id_suivi: numeroSuivi 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Commande marquée comme expédiée !', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showAlert('Erreur lors de la mise à jour.', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showAlert('Erreur lors de la mise à jour.', 'error');
            });
            
            bootstrap.Modal.getInstance(document.getElementById('confirmExpeditionModal')).hide();
        });
    }
});
