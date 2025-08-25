/* ====================================================================
   FONCTIONNALITÉS POUR LA PAGE DÉTAILS CLIENT
   ====================================================================
   
   JavaScript pour la gestion des détails client :
   - Gestion des modals d'ajout de contacts
   - Validation des formulaires
   - Actions d'édition/suppression
   - Formatage automatique des données
==================================================================== */

/**
 * Initialisation des fonctionnalités de la page détails client
 */
function initClientDetailsPage() {
    // Gestion des formulaires dans les modals
    const phoneForm = document.getElementById('addPhoneForm');
    const emailForm = document.getElementById('addEmailForm');
    const addressForm = document.getElementById('addAddressForm');

    // Validation des formulaires
    [phoneForm, emailForm, addressForm].forEach(form => {
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        }
    });

    // Reset des formulaires quand les modals se ferment
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        });
    });

    // Format automatique du téléphone
    const phoneInput = document.getElementById('telephone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            // Supprime tous les caractères non numériques
            let value = this.value.replace(/\D/g, '');
            
            // Format français : 01 23 45 67 89
            if (value.length >= 2) {
                value = value.replace(/(\d{2})(?=\d)/g, '$1 ');
            }
            
            this.value = value.trim();
        });
    }

    // Validation email en temps réel
    const emailInput = document.getElementById('mail');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (emailRegex.test(this.value)) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
}

/**
 * Actions pour l'édition/suppression des téléphones
 */
function editPhone(phoneId) {
    console.log('Edit phone:', phoneId);
    // TODO: Implémenter l'édition du téléphone
    // Peut ouvrir un modal d'édition ou rediriger vers une page
    alert('Fonctionnalité d\'édition à implémenter côté serveur');
}

function deletePhone(phoneId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce numéro de téléphone ?')) {
        // TODO: Envoyer une requête DELETE vers le serveur
        console.log('Delete phone:', phoneId);
        
        // Exemple d'implémentation avec fetch
        /*
        fetch(`/clients/phones/${phoneId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken() // Si vous utilisez CSRF
            }
        })
        .then(response => {
            if (response.ok) {
                // Recharger la page ou supprimer l'élément du DOM
                location.reload();
            } else {
                alert('Erreur lors de la suppression');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression');
        });
        */
        
        alert('Fonctionnalité de suppression à implémenter côté serveur');
    }
}

/**
 * Actions pour l'édition/suppression des emails
 */
function editEmail(emailId) {
    console.log('Edit email:', emailId);
    // TODO: Implémenter l'édition de l'email
    alert('Fonctionnalité d\'édition à implémenter côté serveur');
}

function deleteEmail(emailId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse email ?')) {
        // TODO: Envoyer une requête DELETE vers le serveur
        console.log('Delete email:', emailId);
        alert('Fonctionnalité de suppression à implémenter côté serveur');
    }
}

/**
 * Actions pour l'édition/suppression des adresses
 */
function editAddress(addressId) {
    console.log('Edit address:', addressId);
    // TODO: Implémenter l'édition de l'adresse
    alert('Fonctionnalité d\'édition à implémenter côté serveur');
}

function deleteAddress(addressId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse ?')) {
        // TODO: Envoyer une requête DELETE vers le serveur
        console.log('Delete address:', addressId);
        alert('Fonctionnalité de suppression à implémenter côté serveur');
    }
}

/**
 * Utilitaire pour obtenir le token CSRF (si utilisé)
 */
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

/**
 * Affichage de notifications toast (optionnel)
 */
function showToast(message, type = 'success') {
    // Si vous utilisez Bootstrap 5 toast
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toast = toastContainer.lastElementChild;
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Nettoyage après disparition
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialiser les fonctionnalités spécifiques aux détails client si on est sur cette page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('clientTabs')) {
        initClientDetailsPage();
    }
});