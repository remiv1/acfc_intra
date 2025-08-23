/**
 * JavaScript pour la gestion des clients - Recherche et détails
 */

// Variables globales
let currentClient = null;
let clientData = null;

document.addEventListener('DOMContentLoaded', function() {
    initClientSearch();
    initClientDetails();
    initLegacyClientSearch(); // Pour compatibilité avec l'ancien système
});

// Ancien système de recherche (pour compatibilité)
function initLegacyClientSearch() {
    const clientRechercheInput = document.getElementById('client_recherche');
    if (clientRechercheInput) {
        clientRechercheInput.addEventListener('input', async function () {
            const query = this.value;
            if (query.length < 2) return;

            const res = await fetch(`/clients/clients?query=${encodeURIComponent(query)}`);
            const clients = await res.json();

            const list = document.getElementById('clients_suggestions');
            list.innerHTML = '';

            clients.forEach(client => {
                const li = document.createElement('li');
                li.textContent = `${client.global_name} (${client.id})`;
                li.addEventListener('click', () => {
                    document.getElementById('client_recherche').value = client.global_name;
                    document.getElementById('client').value = client.id;
                    list.innerHTML = '';
                });
                list.appendChild(li);
            });
        });
    }
}

/**
 * Initialise la recherche de clients
 */
function initClientSearch() {
    const searchForm = document.getElementById('client-search-form');
    if (!searchForm) return;

    const searchResults = document.getElementById('search-results');
    const searchLoading = document.getElementById('search-loading');
    const noResults = document.getElementById('no-results');
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Récupération des données du formulaire
        const formData = new FormData(searchForm);
        const searchParams = new URLSearchParams();
        
        // Ajout des paramètres non vides
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                searchParams.append(key, value.trim());
            }
        }
        
        // Affichage du loading
        hideAllResults();
        searchLoading.classList.remove('d-none');
        
        try {
            // Appel à l'API de recherche
            const response = await fetch(`/api/clients/search?${searchParams.toString()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            searchLoading.classList.add('d-none');
            
            if (data.success && data.clients && data.clients.length > 0) {
                displaySearchResults(data.clients);
                searchResults.classList.remove('d-none');
            } else {
                noResults.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Erreur lors de la recherche:', error);
            searchLoading.classList.add('d-none');
            showError('Erreur lors de la recherche. Veuillez réessayer.');
        }
    });
    
    // Reset du formulaire
    searchForm.addEventListener('reset', function() {
        hideAllResults();
    });
}

/**
 * Cache tous les résultats de recherche
 */
function hideAllResults() {
    document.getElementById('search-results')?.classList.add('d-none');
    document.getElementById('no-results')?.classList.add('d-none');
    document.getElementById('search-loading')?.classList.add('d-none');
}

/**
 * Affiche les résultats de recherche
 */
function displaySearchResults(clients) {
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');
    
    if (!resultsList || !resultsCount) return;
    
    resultsList.innerHTML = '';
    resultsCount.textContent = clients.length;
    
    clients.forEach(client => {
        const listItem = document.createElement('a');
        listItem.href = '#';
        listItem.className = 'list-group-item list-group-item-action';
        listItem.onclick = (e) => {
            e.preventDefault();
            loadClientDetails(client.id);
        };
        
        const clientName = getClientDisplayName(client);
        const clientType = client.type_client === 1 ? 'Particulier' : 'Professionnel';
        const badgeClass = client.type_client === 1 ? 'bg-success' : 'bg-primary';
        
        listItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${escapeHtml(clientName)}</h6>
                <span class="badge ${badgeClass}">${clientType}</span>
            </div>
            <p class="mb-1">
                ${client.email ? `<i class="fas fa-envelope text-muted me-1"></i>${escapeHtml(client.email)}` : ''}
                ${client.telephone ? `<i class="fas fa-phone text-muted me-2 ms-3"></i>${escapeHtml(client.telephone)}` : ''}
            </p>
            <small class="text-muted">Client depuis le ${formatDate(client.created_at)}</small>
        `;
        
        resultsList.appendChild(listItem);
    });
}

/**
 * Retourne le nom d'affichage du client
 */
function getClientDisplayName(client) {
    if (client.type_client === 1) {
        return `${client.prenom || ''} ${client.nom || ''}`.trim();
    } else {
        return client.raison_sociale || 'Nom non disponible';
    }
}

/**
 * Charge les détails d'un client
 */
async function loadClientDetails(clientId) {
    if (!clientId) return;
    
    const detailsContainer = document.getElementById('client-details');
    const detailsLoading = document.getElementById('details-loading');
    
    if (!detailsContainer || !detailsLoading) return;
    
    // Affichage du loading
    detailsContainer.classList.add('d-none');
    detailsLoading.classList.remove('d-none');
    
    try {
        // Appel à l'API pour récupérer les détails
        const response = await fetch(`/api/clients/${clientId}/details`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.client) {
            currentClient = clientId;
            clientData = data.client;
            
            // Affichage des détails
            displayClientDetails(data.client);
            
            detailsLoading.classList.add('d-none');
            detailsContainer.classList.remove('d-none');
            
            // Masquer la recherche
            hideSearchContainer();
        } else {
            throw new Error(data.message || 'Données client non disponibles');
        }
    } catch (error) {
        console.error('Erreur lors du chargement des détails:', error);
        detailsLoading.classList.add('d-none');
        showError('Erreur lors du chargement des détails du client.');
    }
}

/**
 * Affiche les détails du client
 */
function displayClientDetails(client) {
    // En-tête du client
    displayClientHeader(client);
    
    // Informations selon le type
    if (client.type_client === 1) {
        displayParticulierInfo(client.particulier);
    } else {
        displayProfessionnelInfo(client.professionnel);
    }
    
    // Onglets avec données
    displayAddresses(client.adresses || []);
    displayEmails(client.emails || []);
    displayPhones(client.telephones || []);
    displayOrders(client.commandes || []);
}

/**
 * Affiche l'en-tête du client
 */
function displayClientHeader(client) {
    const clientName = getClientDisplayName(client);
    const clientType = client.type_client === 1 ? 'Particulier' : 'Professionnel';
    const badgeClass = client.type_client === 1 ? 'bg-success' : 'bg-primary';
    const status = client.is_active ? 'Actif' : 'Inactif';
    const statusClass = client.is_active ? 'text-success' : 'text-danger';
    
    document.getElementById('client-name').textContent = clientName;
    document.getElementById('client-type-badge').textContent = clientType;
    document.getElementById('client-type-badge').className = `badge ${badgeClass} ms-2`;
    document.getElementById('client-id').textContent = client.id;
    document.getElementById('client-created').textContent = formatDate(client.created_at);
    
    const statusElement = document.getElementById('client-status');
    statusElement.textContent = status;
    statusElement.className = statusClass;
    
    // Notes
    const notesContainer = document.getElementById('client-notes-container');
    const notesElement = document.getElementById('client-notes');
    if (client.notes && client.notes.trim()) {
        notesElement.textContent = client.notes;
        notesContainer.classList.remove('d-none');
    } else {
        notesContainer.classList.add('d-none');
    }
}

/**
 * Affiche les informations particulier
 */
function displayParticulierInfo(particulier) {
    document.getElementById('client-particulier').classList.remove('d-none');
    document.getElementById('client-professionnel').classList.add('d-none');
    
    if (particulier) {
        document.getElementById('part-prenom').textContent = particulier.prenom || '';
        document.getElementById('part-nom').textContent = particulier.nom || '';
        document.getElementById('part-naissance').textContent = formatDate(particulier.date_naissance);
        document.getElementById('part-lieu').textContent = particulier.lieu_naissance || '';
    }
}

/**
 * Affiche les informations professionnel
 */
function displayProfessionnelInfo(professionnel) {
    document.getElementById('client-professionnel').classList.remove('d-none');
    document.getElementById('client-particulier').classList.add('d-none');
    
    if (professionnel) {
        document.getElementById('pro-raison').textContent = professionnel.raison_sociale || '';
        
        const typeTexts = {1: 'Entreprise', 2: 'Association', 3: 'Administration'};
        document.getElementById('pro-type').textContent = typeTexts[professionnel.type_pro] || 'Non défini';
        
        document.getElementById('pro-siren').textContent = professionnel.siren || 'Non renseigné';
        document.getElementById('pro-rna').textContent = professionnel.rna || 'Non renseigné';
    }
}

/**
 * Affiche les adresses
 */
function displayAddresses(addresses) {
    const container = document.getElementById('addresses-list');
    const count = document.getElementById('addresses-count');
    
    count.textContent = addresses.length;
    container.innerHTML = '';
    
    if (addresses.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Aucune adresse enregistrée</p>';
        return;
    }
    
    addresses.forEach((address, index) => {
        const addressHtml = `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">Adresse ${index + 1}</h6>
                            <p class="mb-1">${escapeHtml(address.adresse_l1)}</p>
                            ${address.adresse_l2 ? `<p class="mb-1">${escapeHtml(address.adresse_l2)}</p>` : ''}
                            <p class="mb-0">${escapeHtml(address.code_postal)} ${escapeHtml(address.ville)}</p>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editAddress(${address.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteAddress(${address.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <small class="text-muted">Créée le ${formatDate(address.created_at)}</small>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', addressHtml);
    });
}

/**
 * Affiche les emails
 */
function displayEmails(emails) {
    const container = document.getElementById('emails-list');
    const count = document.getElementById('emails-count');
    
    count.textContent = emails.length;
    container.innerHTML = '';
    
    if (emails.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Aucun email enregistré</p>';
        return;
    }
    
    emails.forEach(email => {
        const isPrincipal = email.is_principal;
        const emailHtml = `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                ${escapeHtml(email.type_mail)}
                                ${isPrincipal ? '<span class="badge bg-success ms-2">Principal</span>' : ''}
                            </h6>
                            <p class="mb-1">
                                <a href="mailto:${escapeHtml(email.mail)}" class="text-decoration-none">
                                    <i class="fas fa-envelope me-1"></i>${escapeHtml(email.mail)}
                                </a>
                            </p>
                            ${email.detail ? `<p class="mb-0 text-muted">${escapeHtml(email.detail)}</p>` : ''}
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editEmail(${email.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteEmail(${email.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', emailHtml);
    });
}

/**
 * Affiche les téléphones
 */
function displayPhones(phones) {
    const container = document.getElementById('phones-list');
    const count = document.getElementById('phones-count');
    
    count.textContent = phones.length;
    container.innerHTML = '';
    
    if (phones.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Aucun téléphone enregistré</p>';
        return;
    }
    
    phones.forEach(phone => {
        const isPrincipal = phone.is_principal;
        const fullNumber = `${phone.indicatif || ''}${phone.telephone}`;
        
        const phoneHtml = `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                ${escapeHtml(phone.type_telephone)}
                                ${isPrincipal ? '<span class="badge bg-success ms-2">Principal</span>' : ''}
                            </h6>
                            <p class="mb-1">
                                <a href="tel:${escapeHtml(fullNumber)}" class="text-decoration-none">
                                    <i class="fas fa-phone me-1"></i>${escapeHtml(fullNumber)}
                                </a>
                            </p>
                            ${phone.detail ? `<p class="mb-0 text-muted">${escapeHtml(phone.detail)}</p>` : ''}
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editPhone(${phone.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deletePhone(${phone.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', phoneHtml);
    });
}

/**
 * Affiche les commandes (ordre anti-chronologique)
 */
function displayOrders(orders) {
    const container = document.getElementById('orders-list');
    const count = document.getElementById('orders-count');
    
    count.textContent = orders.length;
    container.innerHTML = '';
    
    if (orders.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Aucune commande enregistrée</p>';
        return;
    }
    
    // Tri anti-chronologique
    orders.sort((a, b) => new Date(b.date_commande) - new Date(a.date_commande));
    
    orders.forEach(order => {
        const statusIcons = {
            factured: order.is_facture ? '<i class="fas fa-file-invoice text-success me-1" title="Facturée"></i>' : '',
            shipped: order.is_expedie ? '<i class="fas fa-shipping-fast text-info me-1" title="Expédiée"></i>' : ''
        };
        
        const orderHtml = `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                Commande #${order.id}
                                ${statusIcons.factured}
                                ${statusIcons.shipped}
                            </h6>
                            <p class="mb-1">
                                <strong>Date :</strong> ${formatDate(order.date_commande)}
                                <span class="ms-3"><strong>Montant :</strong> ${formatCurrency(order.montant)}</span>
                            </p>
                            ${order.descriptif ? `<p class="mb-1 text-muted">${escapeHtml(order.descriptif)}</p>` : ''}
                            ${order.date_facturation ? `<small class="text-success">Facturée le ${formatDate(order.date_facturation)}</small>` : ''}
                            ${order.date_expedition ? `<small class="text-info d-block">Expédiée le ${formatDate(order.date_expedition)}</small>` : ''}
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewOrder(${order.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="editOrder(${order.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', orderHtml);
    });
}

/**
 * Fonctions utilitaires
 */
function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('fr-FR');
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '0,00 €';
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
    errorAlert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.clients-search-container') || document.body;
    container.insertBefore(errorAlert, container.firstChild);
    
    setTimeout(() => errorAlert.remove(), 5000);
}

/**
 * Fonctions de navigation et actions
 */
function hideSearchContainer() {
    const searchContainer = document.querySelector('.clients-search-container');
    if (searchContainer) {
        searchContainer.style.display = 'none';
    }
}

function showSearchContainer() {
    const searchContainer = document.querySelector('.clients-search-container');
    if (searchContainer) {
        searchContainer.style.display = 'block';
    }
}

function backToSearch() {
    const detailsContainer = document.getElementById('client-details');
    if (detailsContainer) {
        detailsContainer.classList.add('d-none');
    }
    showSearchContainer();
    currentClient = null;
    clientData = null;
}

/**
 * Fonctions d'actions (à implémenter selon vos besoins)
 */
function editClient() {
    if (currentClient) {
        // Redirection vers le formulaire d'édition
        window.location.href = `/clients/edit/${currentClient}`;
    }
}

function addAddress() {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/addresses/add`;
    }
}

function editAddress(addressId) {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/addresses/edit/${addressId}`;
    }
}

function deleteAddress(addressId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette adresse ?')) {
        // Appel API pour supprimer
        console.log('Suppression adresse:', addressId);
    }
}

function addEmail() {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/emails/add`;
    }
}

function editEmail(emailId) {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/emails/edit/${emailId}`;
    }
}

function deleteEmail(emailId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet email ?')) {
        // Appel API pour supprimer
        console.log('Suppression email:', emailId);
    }
}

function addPhone() {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/phones/add`;
    }
}

function editPhone(phoneId) {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/phones/edit/${phoneId}`;
    }
}

function deletePhone(phoneId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce téléphone ?')) {
        // Appel API pour supprimer
        console.log('Suppression téléphone:', phoneId);
    }
}

function addOrder() {
    if (currentClient) {
        window.location.href = `/clients/${currentClient}/orders/add`;
    }
}

function viewOrder(orderId) {
    window.location.href = `/orders/view/${orderId}`;
}

function editOrder(orderId) {
    window.location.href = `/orders/edit/${orderId}`;
}

/**
 * Initialisation des détails client (si on arrive directement sur une page de détails)
 */
function initClientDetails() {
    // Si on a un ID client dans l'URL, charger les détails directement
    const urlParts = window.location.pathname.split('/');
    if (urlParts.includes('clients') && urlParts.includes('details')) {
        const clientId = urlParts[urlParts.indexOf('details') + 1];
        if (clientId && !isNaN(clientId)) {
            loadClientDetails(parseInt(clientId));
        }
    }
}