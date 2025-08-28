/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour la gestion des comptes utilisateurs
 * ====================================================================
 * 
 * Fonctionnalités JavaScript pour la gestion des comptes :
 * - Activation des onglets
 * - Validation des formulaires
 * - Gestion du changement de mot de passe
 * - Validation en temps réel des champs
 * 
 * Dépendances : Bootstrap 5
 * ====================================================================
 */

// ====================================================================
// GESTION DES ONGLETS
// ====================================================================

function activateSecurityTab() {
    document.addEventListener('DOMContentLoaded', function() {
        const securityTab = document.getElementById('security-tab');
        if (securityTab && typeof bootstrap !== 'undefined') {
            const tab = new bootstrap.Tab(securityTab);
            tab.show();
        }
    });
}

// ====================================================================
// VALIDATION DES FORMULAIRES
// ====================================================================

function initializeFormValidation() {
    document.addEventListener('DOMContentLoaded', function() {
        // Validation Bootstrap
        const forms = document.querySelectorAll('.needs-validation');
        
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
        
        // Validation en temps réel pour l'email
        initializeEmailValidation();
        
        // Validation en temps réel pour le téléphone
        initializeTelephoneValidation();
        
        // Confirmation avant annulation si des modifications ont été apportées
        initializeCancelConfirmation();
    });
}

function initializeEmailValidation() {
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (emailRegex.test(this.value)) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    }
}

function initializeTelephoneValidation() {
    const telInput = document.getElementById('telephone');
    if (telInput) {
        telInput.addEventListener('input', function() {
            // Regex simple pour les numéros français
            const telRegex = /^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$/;
            if (telRegex.test(this.value) || this.value.length >= 10) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    }
}

function initializeCancelConfirmation() {
    const form = document.querySelector('.needs-validation');
    const cancelBtn = document.querySelector('.btn-outline-secondary');
    
    if (form && cancelBtn) {
        let initialFormData = new FormData(form);
        
        cancelBtn.addEventListener('click', function(e) {
            const currentFormData = new FormData(form);
            let hasChanges = false;
            
            for (let [key, value] of currentFormData.entries()) {
                if (initialFormData.get(key) !== value) {
                    hasChanges = true;
                    break;
                }
            }
            
            if (hasChanges) {
                if (!confirm('Vous avez des modifications non sauvegardées. Êtes-vous sûr de vouloir annuler ?')) {
                    e.preventDefault();
                }
            }
        });
    }
}

// ====================================================================
// GESTION DU CHANGEMENT DE MOT DE PASSE
// ====================================================================

function initializePasswordChangeModal() {
    document.addEventListener('DOMContentLoaded', function() {
        // Variables spécifiques au modal
        const newPasswordInput = document.getElementById("new_password_modal");
        const oldPasswordInput = document.getElementById("old_password_modal");
        const confirmPasswordInput = document.getElementById("confirm_password_modal");
        const matchIndicator = document.getElementById("password_match_modal");
        const form = document.getElementById("changePasswordForm");
        const submitButton = document.getElementById("submitPasswordChange");

        // Conditions de validation du mot de passe (identiques à admin.js)
        const conditions = {
            cond1_modal: (password) => password.length >= 15,
            cond2_modal: (password) => /[A-Z]/.test(password),
            cond3_modal: (password) => /[a-z]/.test(password),
            cond4_modal: (password) => /\d/.test(password),
            cond5_modal: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
        };

        // Mise à jour des indicateurs de conditions
        const updateConditions = (password) => {
            for (const [cond, check] of Object.entries(conditions)) {
                const span = document.querySelector(`.${cond}`);
                if (span) {
                    span.textContent = check(password) ? "✅" : "❌";
                    span.classList.toggle('text-success', check(password));
                    span.classList.toggle('text-danger', !check(password));
                }
            }
        };

        // Mise à jour de l'indicateur de correspondance des mots de passe
        const updateMatchIndicator = () => {
            if (!matchIndicator || !newPasswordInput || !confirmPasswordInput) return;
            matchIndicator.innerHTML = "";
            
            if (newPasswordInput.value === "" && confirmPasswordInput.value === "") {
                return; // Rien à afficher si les champs sont vides
            }
            
            const alertDiv = document.createElement("div");
            const isMatch = newPasswordInput.value === confirmPasswordInput.value;
            
            alertDiv.className = `alert ${isMatch ? 'alert-success' : 'alert-danger'} py-2 px-3 mb-0`;
            alertDiv.innerHTML = `
                <i class="bi ${isMatch ? 'bi-check-circle' : 'bi-x-circle'} me-2"></i>
                ${isMatch ? 'Les mots de passe correspondent' : 'Les mots de passe ne correspondent pas'}
            `;
            
            matchIndicator.appendChild(alertDiv);
        };

        // Activation/désactivation du bouton de soumission
        const toggleSubmitButton = () => {
            if (!submitButton) return;
            
            const isFormValid = (
                oldPasswordInput && oldPasswordInput.value.trim() !== "" &&
                newPasswordInput && newPasswordInput.value.trim() !== "" &&
                confirmPasswordInput && confirmPasswordInput.value.trim() !== ""
            );
            
            const allConditionsMet = newPasswordInput ? 
                Object.values(conditions).every((check) => check(newPasswordInput.value)) : false;
            
            const passwordsMatch = (newPasswordInput && confirmPasswordInput) ? 
                newPasswordInput.value === confirmPasswordInput.value : false;
            
            const isValid = isFormValid && allConditionsMet && passwordsMatch;
            
            submitButton.disabled = !isValid;
            
            // Visual feedback pour le bouton
            if (isValid) {
                submitButton.classList.remove('btn-outline-primary');
                submitButton.classList.add('btn-primary');
            } else {
                submitButton.classList.remove('btn-primary');
                submitButton.classList.add('btn-outline-primary');
            }
        };

        // Événements pour le nouveau mot de passe
        if (newPasswordInput) {
            newPasswordInput.addEventListener("input", () => {
                updateConditions(newPasswordInput.value);
                updateMatchIndicator();
                toggleSubmitButton();
            });
            // Mise à jour initiale
            updateConditions(newPasswordInput.value);
        }

        // Événements pour la confirmation du mot de passe
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener("input", () => {
                updateMatchIndicator();
                toggleSubmitButton();
            });
        }

        // Événements pour l'ancien mot de passe
        if (oldPasswordInput) {
            oldPasswordInput.addEventListener("input", toggleSubmitButton);
        }

        // Réinitialisation du formulaire quand le modal se ferme
        const modal = document.getElementById('changePasswordModal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', function () {
                // Reset du formulaire
                if (form) form.reset();
                
                // Reset des indicateurs
                updateConditions("");
                if (matchIndicator) matchIndicator.innerHTML = "";
                
                // Reset du bouton
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.classList.remove('btn-primary');
                    submitButton.classList.add('btn-outline-primary');
                }
            });
        }

        // État initial du bouton (désactivé)
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add('btn-outline-primary');
        }
    });
}

// ====================================================================
// INITIALISATION GLOBALE
// ====================================================================

// Initialiser toutes les fonctionnalités
initializeFormValidation();
initializePasswordChangeModal();
