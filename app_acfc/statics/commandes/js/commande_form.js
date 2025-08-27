/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour le formulaire de commande
 * ====================================================================
 * 
 * Fonctionnalités JavaScript spécifiques au formulaire de commande simple :
 * - Gestion des champs conditionnels (facturation, expédition)
 * - Initialisation des dates
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
