// Création de variables globales
let modaleName = '';
let total = 0;

// Création d'un listener sur l'ouverture d'une modale
document.addEventListener('DOMContentLoaded', function() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function(event) {
            modaleName = event.target.getAttribute('data-modale-name');
            setupModalListeners(modaleName);
        });
    });
});

// Fonction pour générer les écouteurs sur les différentes modales
function setupModalListeners(modaleName) {
    if (modaleName === 'facturation') {
        //Ajout d'un écouteur sur le checkbox en header du tableau des entrées
        const selectAllCheckbox = document.getElementById('check-all');
        const checkboxes = document.querySelectorAll('.ligne-facturation-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                calculateTotalFacture();
            });
        }
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                verifySelectAllCheckbox();
                calculateTotalFacture();
            });
        });
        // Calcul initial du total facturé
        calculateTotalFacture();
    } else if (modaleName === 'livraison') {

    } else if (modaleName === 'annulation') {

    }
}

// Vérification de l'état de l'ensemble des checkbox
function verifySelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('check-all');
    const checkboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
    const allUnchecked = Array.from(checkboxes).every(checkbox => !checkbox.checked);
    if (allUnchecked) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (!allChecked) {
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    }
    selectAllCheckbox.checked = allChecked;
}

// Calcul du total facturé
function calculateTotalFacture() {
    total = 0;
    const checkboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const totalDisplay = document.getElementById('totalFacturation');
    const selectAllCheckbox = document.getElementById('check-all');
    checkboxes.forEach(checkbox => {
        if (checkbox.id !== 'check-all' && checkbox.checked) {
            const montant = parseFloat(checkbox.value) || 0;
            total += montant;
        }
    });
    totalDisplay.textContent = `${total.toFixed(2)} €`;
    // Mise à jour dans value de la checkbox "Tout sélectionner"
    if (selectAllCheckbox) {
        selectAllCheckbox.value = total.toFixed(2);
    }
}

// Fonction de récupération des IDs des lignes facturées
function updateHiddenFactureIds() {
    const checkboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const ids = [];
    checkboxes.forEach(checkbox => {
        if (checkbox.id !== 'check-all' && checkbox.checked) {
            const idLigne = checkbox.getAttribute('data-ligne-id');
            // Récupère l'id à partir de l'id du checkbox, ex: "fact_123"
            if (idLigne) {
                ids.push(idLigne);
            }
        }
    });
    document.getElementById('ids_lignes_facturees').value = ids.join(',');
}

// Ajout de l'écouteur sur le formulaire de facturation pour mettre à jour les IDs avant soumission
document.addEventListener('DOMContentLoaded', function() {
    const facturationForm = document.getElementById('facturationForm');
    if (facturationForm) {
        facturationForm.addEventListener('submit', function(event) {
            updateHiddenFactureIds();
            
            // Vérifier qu'au moins une ligne est sélectionnée
            const idsLignesFacturees = document.getElementById('ids_lignes_facturees').value;
            if (!idsLignesFacturees || idsLignesFacturees.trim() === '') {
                event.preventDefault();
                alert('Veuillez sélectionner au moins une ligne à facturer.');
                return false;
            }
        });
    }
});
