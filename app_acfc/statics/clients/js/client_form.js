/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour le formulaire client
 * ====================================================================
 * 
 * Fonctionnalités JavaScript spécifiques au formulaire client :
 * - Basculement entre client particulier et professionnel
 * - Validation des champs spécifiques (SIREN, RNA, réduction)
 * - Validation en temps réel
 * - Gestion des champs obligatoires
 * 
 * Dépendances : Bootstrap 5
 * ====================================================================
 */

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeClientTypeToggle();
    initializeFormValidation();
    initializeSpecificFieldsValidation();
});

// ====================================================================
// GESTION DU TYPE DE CLIENT
// ====================================================================

function initializeClientTypeToggle() {
    const typeParticulier = document.getElementById('type_particulier');
    const typeProfessionnel = document.getElementById('type_professionnel');
    const formParticulier = document.getElementById('form-particulier');
    const formProfessionnel = document.getElementById('form-professionnel');
    
    // Fonction pour basculer entre les types de formulaires
    function toggleClientType() {
        // Déterminer le type client actuel
        let isParticulier = false;
        
        if (typeParticulier && typeParticulier.checked) {
            isParticulier = true;
        } else if (typeProfessionnel && typeProfessionnel.checked) {
            isParticulier = false;
        } else {
            // Cas de modification : récupérer le type depuis le champ hidden
            const hiddenTypeClient = document.querySelector('input[name="type_client"][type="hidden"]');
            if (hiddenTypeClient) {
                isParticulier = hiddenTypeClient.value === '1';
            }
        }
        
        if (isParticulier) {
            if (formParticulier) formParticulier.style.display = 'block';
            if (formProfessionnel) formProfessionnel.style.display = 'none';
            
            // Activer la validation pour les champs particulier
            setRequiredFields('particulier', true);
            setRequiredFields('professionnel', false);
        } else {
            if (formParticulier) formParticulier.style.display = 'none';
            if (formProfessionnel) formProfessionnel.style.display = 'block';
            
            // Activer la validation pour les champs professionnel
            setRequiredFields('particulier', false);
            setRequiredFields('professionnel', true);
        }
    }
    
    // Fonction pour activer/désactiver les champs obligatoires
    function setRequiredFields(type, required) {
        const prefix = type === 'particulier' ? ['prenom', 'nom'] : 
                                                ['raison_sociale', 'type_pro'];
        
        prefix.forEach(fieldName => {
            const field = document.getElementById(fieldName);
            if (field) {
                field.required = required;
                if (!required) {
                    field.classList.remove('is-invalid');
                }
            }
        });
    }
    
    // Écouteurs d'événements pour le changement de type
    if (typeParticulier) {
        typeParticulier.addEventListener('change', toggleClientType);
    }
    if (typeProfessionnel) {
        typeProfessionnel.addEventListener('change', toggleClientType);
    }
    
    // Initialisation
    toggleClientType();
}

// ====================================================================
// VALIDATION DU FORMULAIRE
// ====================================================================

function initializeFormValidation() {
    // Validation du formulaire
    const form = document.getElementById('clientForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    }
}

// ====================================================================
// VALIDATION DES CHAMPS SPÉCIFIQUES
// ====================================================================

function initializeSpecificFieldsValidation() {
    initializeSirenValidation();
    initializeRnaValidation();
    initializeReductionValidation();
}

function initializeSirenValidation() {
    // Validation SIREN en temps réel
    const sirenField = document.getElementById('siren');
    if (sirenField) {
        sirenField.addEventListener('input', function() {
            // Supprime tout ce qui n'est pas un chiffre
            this.value = this.value.replace(/\D/g, '');
            
            // Validation de la longueur
            if (this.value.length === 9 || this.value.length === 0) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    }
}

function initializeRnaValidation() {
    // Validation RNA en temps réel
    const rnaField = document.getElementById('rna');
    if (rnaField) {
        rnaField.addEventListener('input', function() {
            // Format automatique RNA
            let value = this.value.toUpperCase();
            if (value.length > 0 && !value.startsWith('W')) {
                value = 'W' + value.replace(/\D/g, '');
            } else {
                value = value.replace(/[^W0-9]/g, '');
            }
            this.value = value;
            
            // Validation du format
            const rnaPattern = /^W[0-9]{9}$/;
            if (rnaPattern.test(this.value) || this.value.length === 0) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    }
}

function initializeReductionValidation() {
    // Gestion du champ réduction
    const reducesField = document.getElementById('reduces');
    if (reducesField) {
        // Validation en temps réel
        reducesField.addEventListener('input', function() {
            let value = parseFloat(this.value) || 0;
            
            // Validation de la plage
            if (value >= 0 && value <= 100) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    }
}
