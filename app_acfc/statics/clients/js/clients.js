/* ====================================================================
   FONCTIONNALITÉS POUR LA PAGE DÉTAILS CLIENT
   ====================================================================
   
   JavaScript pour la gestion des détails client :
   - Gestion des scripts au chargement de la page
   - fillPhoneModal : Remplissage du modal téléphone avec données si édition, vide sinon.
   - editPhone : Actions pour l'édition des numéros de téléphones.
   - deletePhoneWithConfirm : Suppression avec confirmation d'un numéro de téléphone. (suppression logique)
   - updateIndic : Met à jour la liste des indicatifs en fonction du pays saisi.
==================================================================== */

// Initialiser les fonctionnalités spécifiques aux détails client si on est sur cette page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('clientTabs')) {
        initClientDetailsPage();
    }
    
    // Initialiser la recherche de clients si on est sur cette page
    if (document.getElementById('client-search-form')) {
        initClientSearchPage();
    }
});

// Récupération du Token CSRF depuis la meta injectée par le serveur
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Remplissage du modal téléphone avec données si édition, vide sinon.
function fillPhoneModal(data, mode = 'create') {
    // Création des constantes pour les éléments du modal
    const form = document.getElementById('addPhoneForm');
    const modalTitle = document.querySelector('#addPhoneModal .modal-title');
    const submitButton = document.querySelector('#addPhoneForm button[type="submit"]');
    const indicatifInput = document.getElementById('indicatif');
    if (mode === 'edit' || mode === 'create') {
        // Vider le menu déroulant des indicatifs avant de le remplir
        if (indicatifInput) {
            indicatifInput.options.length = 0;
        }
    }
    
    if (mode === 'edit') {
        // Mode édition
        modalTitle.innerHTML = '<i class="bi bi-telephone me-2"></i>Modifier le numéro de téléphone';
        submitButton.innerHTML = '<i class="bi bi-check me-1"></i>Modifier';
        submitButton.className = 'btn btn-warning';
        
        // Modifier l'action du formulaire pour pointer vers la route de modification
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/modify-phone/${data.id}/`;
        
        // Remplir les champs avec les données existantes
        const telephoneInput = document.getElementById('telephone');
        const typeSelect = document.getElementById('type_telephone');
        const indicatifInput = document.getElementById('indicatif');
        const detailInput = document.getElementById('detail_phone');
        const principalCheckbox = document.getElementById('is_principal_phone');
        
        if (telephoneInput) telephoneInput.value = data.telephone || '';
        if (typeSelect) typeSelect.value = data.type_telephone || 'mobile_pro';
        if (indicatifInput) {
            // Ajoute une option avec la valeur actuelle si elle n'existe pas déjà
            const option = document.createElement('option');
            option.value = data.indicatif || '+33';
            option.textContent = data.indicatif || '+33';
            option.selected = true;
            indicatifInput.appendChild(option);
            indicatifInput.value = data.indicatif || '+33';
        }
        if (detailInput) detailInput.value = data.detail || '';
        if (principalCheckbox) principalCheckbox.checked = data.is_principal || false;
        
    } else {
        // Mode création
        modalTitle.innerHTML = '<i class="bi bi-telephone me-2"></i>Ajouter un numéro de téléphone';
        submitButton.innerHTML = '<i class="bi bi-plus me-1"></i>Ajouter';
        submitButton.className = 'btn btn-success';
        
        // Remettre l'action du formulaire pour la création
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/add-phone/`;
        
        // Vider les champs
        form.reset();
        form.classList.remove('was-validated');
    }
}

// Actions pour l'édition des téléphones
function editPhone(phoneId, buttonElement) {

    // Récupérer les données depuis les attributs data-* du bouton
    if (!buttonElement?.dataset) {
        return;
    }
    
    // Méthode principale avec dataset
    let phonesData = {
        id: phoneId,
        telephone: buttonElement.dataset.phoneTelephone,
        type_telephone: buttonElement.dataset.phoneType,
        indicatif: buttonElement.dataset.phoneIndicatif,
        detail: buttonElement.dataset.phoneDetail,
        is_principal: buttonElement.dataset.phonePrincipal === 'true'
    };
    
    // Remplir le modal avec les données existantes
    fillPhoneModal(phonesData, 'edit');

    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('addPhoneModal'));
    modal.show();
}

// Supprimer un téléphone avec confirmation
function deletePhoneWithConfirm(button) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce numéro de téléphone ?')) {
        const idClient = button.getAttribute('data-client-id');
        const idPhone = button.getAttribute('data-phone-id');

        // Effectuer la requête de suppression
        const url = `/clients/${idClient}/delete-phone/${idPhone}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            }
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}

// Modifie la liste en fonction de ce qui est inscrit dans l'outil de recherche
function updateIndic() {
    const selectList = document.getElementById('indicatif');
    // Envoie la requête au serveur pour obtenir les indicatifs
    fetch(`/api/indic-tel`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(indicatifs => {
        indicatifs.forEach(indicatif => {
            const option = document.createElement('option');
            option.value = indicatif.value;
            option.textContent = indicatif.label;
            selectList.appendChild(option);
        });
    })
    .catch(error => {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = `Erreur lors de la récupération des indicatifs : ${error}`;
        selectList.appendChild(option);
    });
}

// Initialisation des fonctionnalités de la page détails client
function initClientDetailsPage() {
    // Gestion des formulaires dans les modals
    const phoneForm = document.getElementById('addPhoneForm');
    const emailForm = document.getElementById('addEmailForm');
    const addressForm = document.getElementById('addAddressForm');
    
    // Listener de validation des formulaires modaux
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
    
    // Reset des formulaires quand les modaux se ferment
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        });
    });
    
    // Gestionnaire spécifique pour le modal d'email - réinitialisation en mode création
    const emailModal = document.getElementById('addEmailModal');
    if (emailModal) {
        emailModal.addEventListener('show.bs.modal', function(event) {
            
            // Ne faire la réinitialisation que si c'est explicitement un bouton d'ajout
            const isAddButton = event.relatedTarget && 
            (event.relatedTarget.textContent.includes('Ajouter') ||
            event.relatedTarget.classList.contains('btn-success'));
            
            if (isAddButton) {
                fillEmailModal({}, 'create');
            } 
        });
    }
    
    // Gestionnaire spécifique pour le modal de téléphone - réinitialisation en mode création
    const phoneModal = document.getElementById('addPhoneModal');
    if (phoneModal) {
        phoneModal.addEventListener('show.bs.modal', function(event) {
            // Ne faire la réinitialisation que si c'est explicitement un bouton d'ajout
            const isAddButton = event.relatedTarget && 
            (event.relatedTarget.textContent.includes('Ajouter') ||
            event.relatedTarget.classList.contains('btn-success'));
            
            if (isAddButton) {
                fillPhoneModal({}, 'create');
            }
        });
    }

    // Gestionnaire spécifique pour le modal d'adresse - réinitialisation en mode création
    const addressModal = document.getElementById('addAddressModal');
    if (addressModal) {
        addressModal.addEventListener('show.bs.modal', function(event) {
            // Ne faire la réinitialisation que si c'est explicitement un bouton d'ajout
            const isAddButton = event.relatedTarget && 
            (event.relatedTarget.textContent.includes('Ajouter') ||
            event.relatedTarget.classList.contains('btn-success'));
            
            if (isAddButton) {
                fillAddressModal({}, 'create');
            }
        });
    }
    
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

// Actions pour l'édition/suppression des emails
function editEmail(emailId, buttonElement) {
    
    // Récupérer les données depuis les attributs data-* du bouton et gestion d'erreur
    if (!buttonElement?.dataset) {
        return;
    }
    
    // Méthode principale avec dataset
    let data = {
        id: emailId,
        mail: buttonElement.dataset.emailMail,
        type_mail: buttonElement.dataset.emailType,
        detail: buttonElement.dataset.emailDetail,
        is_principal: buttonElement.dataset.emailPrincipal === 'true'
    };
    
    // Si les données sont vides, essayer avec getAttribute (méthode de fallback)
    if (!data.mail) {
        data = {
            id: emailId,
            mail: buttonElement.getAttribute('data-email-mail'),
            type_mail: buttonElement.getAttribute('data-email-type'),
            detail: buttonElement.getAttribute('data-email-detail'),
            is_principal: buttonElement.getAttribute('data-email-principal') === 'true'
        };
    }
    
    // Remplir le modal avec les données existantes
    fillEmailModal(data, 'edit');
    
    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('addEmailModal'));
    modal.show();
}

// Fonction pour remplir le modal d'email avec les données
function fillEmailModal(data, mode = 'create') {
    const form = document.getElementById('addEmailForm');
    const modalTitle = document.querySelector('#addEmailModal .modal-title');
    const submitButton = document.querySelector('#addEmailForm button[type="submit"]');
    
    if (mode === 'edit') {
        
        // Mode édition
        modalTitle.innerHTML = '<i class="bi bi-envelope me-2"></i>Modifier l\'adresse email';
        submitButton.innerHTML = '<i class="bi bi-check me-1"></i>Modifier';
        submitButton.className = 'btn btn-warning';
        
        // Modifier l'action du formulaire pour pointer vers la route de modification
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/modify-email/${data.id}/`;
        
        // Vérifier que les éléments existent avant de les remplir
        const mailInput = document.getElementById('mail');
        const typeMailSelect = document.getElementById('type_mail');
        const detailInput = document.getElementById('detail_mail');
        const principalCheckbox = document.getElementById('is_principal_mail');
        
        // Remplir les champs avec les données existantes
        if (mailInput) {
            mailInput.value = data.mail || '';
        }
        if (typeMailSelect) {
            typeMailSelect.value = data.type_mail || 'professionnel';
        }
        if (detailInput) {
            detailInput.value = data.detail || '';
        }
        if (principalCheckbox) {
            principalCheckbox.checked = data.is_principal || false;
        }
        
    } else {
        // Mode création
        modalTitle.innerHTML = '<i class="bi bi-envelope me-2"></i>Ajouter une adresse email';
        submitButton.innerHTML = '<i class="bi bi-plus me-1"></i>Ajouter';
        submitButton.className = 'btn btn-success';
        
        // Remettre l'action du formulaire pour la création
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/add-email/`;
        
        // Vider les champs
        form.reset();
        form.classList.remove('was-validated');
    }
}

// Fonction de suppression d'un email
function deleteEmailWithConfirm(emailId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse email ?')) {
        const clientId = document.getElementById('client-id').value;
        const url = `/clients/${clientId}/delete-email/${emailId}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            }
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}

// Actions pour l'édition/suppression des adresses
function editAddress(addressId, buttonElement) {
    // Récupérer les données depuis les attributs data-* du bouton
    if (!buttonElement?.dataset) {
        return;
    }
    
    // Méthode principale avec dataset (camelCase)
    let data = {
        id: addressId,
        adresse_l1: buttonElement.dataset.addressL1,
        adresse_l2: buttonElement.dataset.addressL2,
        code_postal: buttonElement.dataset.addressPostal,
        ville: buttonElement.dataset.addressVille,
        is_principal: buttonElement.dataset.addressPrincipal === 'true'
    };
    
    // Si les données sont vides, essayer avec getAttribute (méthode de fallback)
    if (!data.adresse_l1) {
        data = {
            id: addressId,
            adresse_l1: buttonElement.getAttribute('data-address-l1'),
            adresse_l2: buttonElement.getAttribute('data-address-l2'),
            code_postal: buttonElement.getAttribute('data-address-postal'),
            ville: buttonElement.getAttribute('data-address-ville'),
            is_principal: buttonElement.getAttribute('data-address-principal') === 'true'
        };
    }
    
    // Remplir le modal avec les données existantes
    fillAddressModal(data, 'edit');
    
    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('addAddressModal'));
    modal.show();
}

// Fonction pour remplir le modal d'adresse avec les données
function fillAddressModal(data, mode = 'create') {
    const form = document.getElementById('addAddressForm');
    const modalTitle = document.querySelector('#addAddressModal .modal-title');
    const submitButton = document.querySelector('#addAddressForm button[type="submit"]');
    
    if (mode === 'edit') {        
        // Mode édition
        modalTitle.innerHTML = '<i class="bi bi-geo-alt me-2"></i>Modifier l\'adresse';
        submitButton.innerHTML = '<i class="bi bi-check me-1"></i>Modifier';
        submitButton.className = 'btn btn-warning';
        
        // Modifier l'action du formulaire pour pointer vers la route de modification
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/modify-address/${data.id}/`;
        
        // Remplir les champs avec les données existantes
        const adresseL1Input = document.getElementById('adresse_l1');
        const adresseL2Input = document.getElementById('adresse_l2');
        const codePostalInput = document.getElementById('code_postal');
        const villeInput = document.getElementById('ville');
        const principalCheckbox = document.getElementById('is_principal_adresse');
        
        if (adresseL1Input) adresseL1Input.value = data.adresse_l1 || '';
        if (adresseL2Input) adresseL2Input.value = data.adresse_l2 || '';
        if (codePostalInput) codePostalInput.value = data.code_postal || '';
        if (villeInput) villeInput.value = data.ville || '';
        if (principalCheckbox) principalCheckbox.checked = data.is_principal || false;
    } else {
        // Mode création
        modalTitle.innerHTML = '<i class="bi bi-geo-alt me-2"></i>Ajouter une adresse';
        submitButton.innerHTML = '<i class="bi bi-plus me-1"></i>Ajouter';
        submitButton.className = 'btn btn-success';
        
        // Remettre l'action du formulaire pour la création
        const clientId = document.getElementById('client-id').value;
        form.action = `/clients/${clientId}/add-address/`;
        
        // Vider les champs
        form.reset();
        form.classList.remove('was-validated');
    }
}

// Fonction pour supprimer une adresse
function deleteAddress(addressId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse ?')) {
        const clientId = document.getElementById('client-id').value;
        const url = `/clients/${clientId}/delete-address/${addressId}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            }
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}

// Fonction pour afficher des notifications toast
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

 // Fonctionnalités pour la page de recherche avancée de clients
function initClientSearchPage() {
    const searchInput = document.getElementById('search-term');
    const searchTypeInputs = document.querySelectorAll('input[name="search_type"]');
    const resultsContainer = document.getElementById('search-results');
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');
    const loadingDiv = document.getElementById('search-loading');
    const noResultsDiv = document.getElementById('no-results');
    const inactiveCheckbox = document.getElementById('search-inactive');
    
    let searchTimeout;
    
    // Fonction de recherche
    function performSearch() {
        const searchTerm = searchInput.value.trim();
        const searchType = document.querySelector('input[name="search_type"]:checked').value;
        const searchInactive = inactiveCheckbox ? inactiveCheckbox.checked : false;
        
        // Masquer tous les éléments
        resultsContainer.classList.add('d-none');
        noResultsDiv.classList.add('d-none');
        loadingDiv.classList.add('d-none');
        
        // Vérifier la longueur minimale
        if (searchTerm.length < 3) {
            return;
        }
        
        // Afficher le loading
        loadingDiv.classList.remove('d-none');
        
        // Effectuer la recherche
        fetch(`/clients/recherche_avancee?q=${encodeURIComponent(searchTerm)}&type=${searchType}&search-inactive=${searchInactive}`)
            .then(response => response.json())
            .then(data => {
                loadingDiv.classList.add('d-none');
                
                if (data.length === 0) {
                    noResultsDiv.classList.remove('d-none');
                } else {
                    displayResults(data);
                }
            })
            .catch(error => {
                loadingDiv.classList.add('d-none');
                noResultsDiv.classList.remove('d-none');
            });
    }
    
    // Fonction d'affichage des résultats
    function displayResults(clients) {
        resultsList.innerHTML = '';
        resultsCount.textContent = clients.length;
        
        clients.forEach(client => {
            const listItem = document.createElement('a');
            listItem.href = `/clients/${client.id}`;
            listItem.className = 'list-group-item list-group-item-action';
            
            listItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <div>
                        <h6 class="mb-1">${client.nom_affichage}</h6>
                        <p class="mb-1">
                            <span class="badge bg-${client.type_client === 1 ? 'success' : 'primary'} me-2">
                                ${client.type_client_libelle}
                            </span>
                            ${client.code_postal} ${client.ville}
                        </p>
                    </div>
                    <small class="text-muted">
                        <i class="fas fa-arrow-right"></i>
                    </small>
                </div>
            `;
            
            resultsList.appendChild(listItem);
        });
        
        resultsContainer.classList.remove('d-none');
    }
    
    // Événements de recherche
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 300); // Debounce de 300ms
    });

    // Événement pour la case à cocher "inactifs"
    inactiveCheckbox.addEventListener('change', function() {
        if (searchInput.value.trim().length >= 3) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 100);
        }
    });

    // Événement de changement de type de recherche
    searchTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (searchInput.value.trim().length >= 3) {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(performSearch, 100);
            }
        });
    });
}

// Fonction de réactivation d'une adresse inactive
function reactivateAddress(addressId) {
    const clientId = document.getElementById('client-id').value;
    if (confirm('Êtes-vous sûr de vouloir réactiver cette adresse ?')) {
        const url = `/clients/${clientId}/activate-address-${addressId}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            },
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}

// Fonction de réactivation d'un téléphone inactif
function reactivatePhone(phoneId) {
    const clientId = document.getElementById('client-id').value;
    if (confirm('Êtes-vous sûr de vouloir réactiver ce téléphone ?')) {
        const url = `/clients/${clientId}/activate-phone-${phoneId}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            },
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}

// Fonction de réactivation d'un email inactif
function reactivateMail(emailId) {
    const clientId = document.getElementById('client-id').value;
    if (confirm('Êtes-vous sûr de vouloir réactiver cet email ?')) {
        const url = `/clients/${clientId}/activate-email-${emailId}`;
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-CSRF-Token': getCSRFToken()
            },
        }).then(resp => {
            // Recharge la page après la réponse du serveur
            if (resp.redirected) {
                window.location.href = resp.url;
            } else if (resp.ok) {
                location.reload();
            }
        });
    }
}
