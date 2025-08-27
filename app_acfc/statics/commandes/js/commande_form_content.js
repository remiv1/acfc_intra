/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour le formulaire de contenu de commande
 * ====================================================================
 * 
 * Fonctionnalités JavaScript spécifiques au formulaire de contenu de commande :
 * - Gestion des champs conditionnels (facturation, expédition)
 * - Gestion des modales de facturation et expédition
 * - Filtrage des produits du catalogue
 * - Activation/désactivation des champs de quantité
 * 
 * Dépendances : Bootstrap 5
 * ====================================================================
 */

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeDateFields();
    initializeConditionalFields();
    initializeProductTable();
    initializeModals();
    initializeFilters();
});

// ====================================================================
// GESTION DES CHAMPS DE DATE
// ====================================================================

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

// ====================================================================
// GESTION DES CHAMPS CONDITIONNELS
// ====================================================================

function initializeConditionalFields() {
    initializeFacturationFields();
    initializeExpeditionFields();
}

function initializeFacturationFields() {
    // Gestion de l'affichage de la date de facturation
    const isFactureCheckbox = document.getElementById('is_facture');
    const dateFacturationGroup = document.getElementById('date_facturation_group');
    
    if (isFactureCheckbox && dateFacturationGroup) {
        isFactureCheckbox.addEventListener('change', function() {
            if (this.checked) {
                dateFacturationGroup.style.display = 'block';
                if (!document.getElementById('date_facturation').value) {
                    document.getElementById('date_facturation').value = new Date().toISOString().split('T')[0];
                }
            } else {
                dateFacturationGroup.style.display = 'none';
                document.getElementById('date_facturation').value = '';
            }
        });
    }
}

function initializeExpeditionFields() {
    // Gestion de l'affichage des champs d'expédition
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
// GESTION DU TABLEAU DES PRODUITS
// ====================================================================

function initializeProductTable() {
    // Gestion des checkboxes de produits pour activer/désactiver les champs quantité
    document.querySelectorAll('.product-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const row = this.closest('tr');
            const quantityInput = row.querySelector('.quantity-input');
            
            if (this.checked) {
                row.classList.add('table-success');
                if (quantityInput) quantityInput.disabled = false;
            } else {
                row.classList.remove('table-success');
                if (quantityInput) quantityInput.disabled = true;
            }
        });
        
        // Initialiser l'état
        if (checkbox.checked) {
            const row = checkbox.closest('tr');
            row.classList.add('table-success');
            const quantityInput = row.querySelector('input[type="number"]');
            if (quantityInput) quantityInput.disabled = false;
        }
    });
}

// ====================================================================
// GESTION DES MODALES
// ====================================================================

function initializeModals() {
    initializeExpeditionModal();
    initializeFacturationModal();
}

function initializeExpeditionModal() {
    // Gestion du mode d'expédition
    const modeExpeditionRadios = document.querySelectorAll('input[name="mode_expedition"]');
    const numeroSuiviGroup = document.getElementById('numero_suivi_group');
    const numeroSuiviInput = document.getElementById('numero_suivi_modal');
    
    function toggleNumeroSuivi() {
        const selectedModeElement = document.querySelector('input[name="mode_expedition"]:checked');
        if (selectedModeElement) {
            const selectedMode = selectedModeElement.value;
            if (selectedMode === 'suivi') {
                if (numeroSuiviGroup) numeroSuiviGroup.style.display = 'block';
                if (numeroSuiviInput) numeroSuiviInput.required = true;
            } else {
                if (numeroSuiviGroup) numeroSuiviGroup.style.display = 'none';
                if (numeroSuiviInput) {
                    numeroSuiviInput.required = false;
                    numeroSuiviInput.value = '';
                }
            }
        }
    }
    
    modeExpeditionRadios.forEach(radio => {
        radio.addEventListener('change', toggleNumeroSuivi);
    });
    
    // Initialiser l'état
    toggleNumeroSuivi();
    
    // Gestion de la confirmation d'expédition
    const confirmerExpeditionBtn = document.getElementById('confirmerExpedition');
    if (confirmerExpeditionBtn) {
        confirmerExpeditionBtn.addEventListener('click', function() {
            const dateExpedition = document.getElementById('date_expedition_modal').value;
            const modeExpeditionElement = document.querySelector('input[name="mode_expedition"]:checked');
            const modeExpedition = modeExpeditionElement ? modeExpeditionElement.value : '';
            const numeroSuivi = document.getElementById('numero_suivi_modal').value;
            
            if (!dateExpedition) {
                alert('Veuillez sélectionner une date d\'expédition');
                return;
            }
            
            if (modeExpedition === 'suivi' && !numeroSuivi) {
                alert('Veuillez entrer un numéro de suivi pour l\'expédition avec suivi');
                return;
            }
            
            // Soumettre le formulaire avec l'action d'expédition
            const form = document.getElementById('commandeForm');
            if (form) {
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                actionInput.value = 'expedier';
                form.appendChild(actionInput);
                
                const dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'date_expedition';
                dateInput.value = dateExpedition;
                form.appendChild(dateInput);
                
                const modeInput = document.createElement('input');
                modeInput.type = 'hidden';
                modeInput.name = 'mode_expedition';
                modeInput.value = modeExpedition;
                form.appendChild(modeInput);
                
                if (numeroSuivi) {
                    const suiviInput = document.createElement('input');
                    suiviInput.type = 'hidden';
                    suiviInput.name = 'id_suivi';
                    suiviInput.value = numeroSuivi;
                    form.appendChild(suiviInput);
                }
                
                form.submit();
            }
        });
    }
}

function initializeFacturationModal() {
    // Gestion de la confirmation de facturation
    const confirmerFacturationBtn = document.getElementById('confirmerFacturation');
    if (confirmerFacturationBtn) {
        confirmerFacturationBtn.addEventListener('click', function() {
            const dateFacturation = document.getElementById('date_facturation_modal').value;
            if (!dateFacturation) {
                alert('Veuillez sélectionner une date de facturation');
                return;
            }
            
            // Soumettre le formulaire avec l'action de facturation
            const form = document.getElementById('commandeForm');
            if (form) {
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                actionInput.value = 'facturer';
                form.appendChild(actionInput);
                
                const dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'date_facturation';
                dateInput.value = dateFacturation;
                form.appendChild(dateInput);
                
                form.submit();
            }
        });
    }
}

// ====================================================================
// GESTION DES FILTRES
// ====================================================================

function initializeFilters() {
    // Appliquer les filtres par défaut au chargement
    appliquerFiltres();
}

// Fonctions de filtrage JavaScript côté client
function appliquerFiltres() {
    const millesimeFilter = document.getElementById('filter_millesime');
    const typeFilter = document.getElementById('filter_type_produit');
    const geographieFilter = document.getElementById('filter_geographie');
    
    if (!millesimeFilter || !typeFilter || !geographieFilter) {
        return;
    }
    
    const millesimeValue = millesimeFilter.value;
    const typeValue = typeFilter.value;
    const geographieValue = geographieFilter.value;
    
    const rows = document.querySelectorAll('.catalogue-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const millesime = row.getAttribute('data-millesime');
        const type = row.getAttribute('data-type');
        const geographie = row.getAttribute('data-geographie');
        
        let visible = true;
        
        // Appliquer les filtres
        if (millesimeValue && millesime !== millesimeValue) {
            visible = false;
        }
        if (typeValue && type !== typeValue) {
            visible = false;
        }
        if (geographieValue && geographie !== geographieValue) {
            visible = false;
        }
        
        // Afficher/cacher la ligne
        if (visible) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Afficher/cacher le message "aucun produit trouvé"
    const noProductsMessage = document.getElementById('no-products-message');
    if (noProductsMessage) {
        if (visibleCount === 0) {
            noProductsMessage.style.display = 'block';
        } else {
            noProductsMessage.style.display = 'none';
        }
    }
}

function reinitialiserFiltres() {
    // Remettre les valeurs par défaut
    const millesimeFilter = document.getElementById('filter_millesime');
    const typeFilter = document.getElementById('filter_type_produit');
    const geographieFilter = document.getElementById('filter_geographie');
    
    if (millesimeFilter) {
        // Récupérer l'année courante depuis un attribut data-current-year
        const currentYear = millesimeFilter.getAttribute('data-current-year');
        millesimeFilter.value = currentYear || '';
    }
    if (typeFilter) typeFilter.value = 'Courrier';
    if (geographieFilter) geographieFilter.value = 'FRANCE';
    
    // Appliquer les filtres
    appliquerFiltres();
}

// ====================================================================
// GESTION DES CASES À COCHER DE PRODUITS
// ====================================================================

function initializeProductCheckboxes() {
    const productCheckboxes = document.querySelectorAll('.product-checkbox');
    
    productCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const productId = this.value;
            const quantityInput = document.querySelector(`input[name="qte_${productId}"]`);
            const priceInput = document.querySelector(`input[name="prix_${productId}"]`);
            
            if (this.checked) {
                // Activer les champs
                if (quantityInput) quantityInput.disabled = false;
                if (priceInput) priceInput.disabled = false;
            } else {
                // Désactiver les champs
                if (quantityInput) quantityInput.disabled = true;
                if (priceInput) priceInput.disabled = true;
            }
        });
    });
}

// Initialiser les cases à cocher de produits
document.addEventListener('DOMContentLoaded', function() {
    initializeProductCheckboxes();
});
