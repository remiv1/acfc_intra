/**
 * ACFC - JavaScript Module Commercial
 * ===================================
 */

// Configuration globale
const COMMERCIAL_CONFIG = {
    CLIENTS_PER_PAGE: 50,
    API_ENDPOINTS: {
        CLIENTS_SEARCH: '/commercial/clients/api/search'
    }
};

// Variables globales pour la liste des clients
let currentOffset = 0;
let currentFilters = {};
let totalResults = 0;

/**
 * Initialisation du module commercial
 */
document.addEventListener('DOMContentLoaded', function() {
    // Récupération du sous-contexte depuis une variable JavaScript ou un attribut
    const subcontext = window.COMMERCIAL_SUBCONTEXT || document.body.dataset.subcontext || '';
    
    switch(subcontext) {
        case 'filter_list':
            initClientsFilterList();
            break;
        default:
            initCommercialIndex();
            break;
    }
});

/**
 * Initialisation de la page d'accueil commercial
 */
function initCommercialIndex() {
    console.log('Module commercial initialisé');
    // Ici on peut ajouter des fonctionnalités pour la page d'accueil
}

/**
 * Initialisation de la liste des clients avec filtres
 */
function initClientsFilterList() {
    console.log('Liste des clients initialisée');
    initializeClientFilterEvents();
    loadClients(); // Chargement initial
}

/**
 * Initialisation des événements pour les filtres clients
 */
function initializeClientFilterEvents() {
    // Soumission du formulaire
    const filtersForm = document.getElementById('filtersForm');
    if (filtersForm) {
        filtersForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentOffset = 0;
            loadClients();
        });
    }
    
    // Réinitialisation des filtres
    const resetButton = document.getElementById('resetFilters');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            const form = document.getElementById('filtersForm');
            if (form) {
                form.reset();
                const isActiveSelect = document.getElementById('is_active');
                if (isActiveSelect) {
                    isActiveSelect.value = '1'; // Réactiver le filtre "actifs"
                }
                currentOffset = 0;
                loadClients();
            }
        });
    }
    
    // Pagination
    const prevButton = document.getElementById('prevPage');
    if (prevButton) {
        prevButton.addEventListener('click', function() {
            if (currentOffset > 0) {
                currentOffset = Math.max(0, currentOffset - COMMERCIAL_CONFIG.CLIENTS_PER_PAGE);
                loadClients();
            }
        });
    }
    
    const nextButton = document.getElementById('nextPage');
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            currentOffset += COMMERCIAL_CONFIG.CLIENTS_PER_PAGE;
            loadClients();
        });
    }
}

/**
 * Collecte les filtres depuis le formulaire
 */
function collectFilters() {
    const form = document.getElementById('filtersForm');
    if (!form) return {};
    
    const formData = new FormData(form);
    const filters = {};
    
    for (let [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            filters[key] = value.trim();
        }
    }
    
    filters.limit = COMMERCIAL_CONFIG.CLIENTS_PER_PAGE;
    filters.offset = currentOffset;
    
    return filters;
}

/**
 * Charge la liste des clients via l'API
 */
function loadClients() {
    currentFilters = collectFilters();
    
    // Afficher le loading
    showLoading();
    
    // Construire l'URL avec les paramètres
    const url = new URL(COMMERCIAL_CONFIG.API_ENDPOINTS.CLIENTS_SEARCH, window.location.origin);
    Object.keys(currentFilters).forEach(key => {
        url.searchParams.append(key, currentFilters[key]);
    });
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displayClients(data.clients);
                updatePagination(data.pagination);
                updateResultsSummary(data.pagination, data.filters_applied);
            } else {
                showError(data.error || 'Erreur lors du chargement des clients');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Erreur:', error);
            showError('Erreur de communication avec le serveur');
        });
}

/**
 * Affiche la liste des clients dans le tableau
 */
function displayClients(clients) {
    const tbody = document.getElementById('clientsTableBody');
    const tableContainer = document.getElementById('clientsTableContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');
    
    if (!tbody || !tableContainer || !noResultsMessage) return;
    
    if (clients.length === 0) {
        tableContainer.style.display = 'none';
        noResultsMessage.style.display = 'block';
        return;
    }
    
    noResultsMessage.style.display = 'none';
    tableContainer.style.display = 'block';
    
    tbody.innerHTML = '';
    
    clients.forEach(client => {
        const row = document.createElement('tr');
        
        // Contact icons
        const contactIcons = [];
        if (client.has_phone) {
            contactIcons.push('<i class="fas fa-phone contact-icon" title="Téléphone disponible"></i>');
        } else {
            contactIcons.push('<i class="fas fa-phone contact-icon missing" title="Pas de téléphone"></i>');
        }
        
        if (client.has_email) {
            contactIcons.push('<i class="fas fa-envelope contact-icon" title="Email disponible"></i>');
        } else {
            contactIcons.push('<i class="fas fa-envelope contact-icon missing" title="Pas d\'email"></i>');
        }
        
        // Localisation
        const localisation = [];
        if (client.departement) {
            localisation.push(`Dép. ${client.departement}`);
        }
        if (client.ville) {
            localisation.push(client.ville);
        }
        
        row.innerHTML = `
            <td><strong>${escapeHtml(client.nom_affichage)}</strong></td>
            <td>
                <span class="type-badge ${client.type_client === 1 ? 'type-particulier' : 'type-professionnel'}">
                    ${client.type_client_libelle}
                </span>
            </td>
            <td>
                <div class="contact-icons">
                    ${contactIcons.join('')}
                </div>
                <small>${client.telephones} tél. / ${client.emails} emails</small>
            </td>
            <td>${localisation.join('<br>') || '<em>Non renseigné</em>'}</td>
            <td>
                <span class="status-badge ${client.is_active ? 'status-active' : 'status-inactive'}">
                    ${client.is_active ? 'Actif' : 'Inactif'}
                </span>
            </td>
            <td>${formatDate(client.created_at)}</td>
            <td>
                <a href="/clients/${client.id}" class="btn btn-sm btn-outline-primary" title="Voir le détail">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="/commandes/create/client/${client.id}" class="btn btn-sm btn-outline-success" title="Nouvelle commande">
                    <i class="fas fa-plus"></i>
                </a>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Met à jour les contrôles de pagination
 */
function updatePagination(pagination) {
    const paginationContainer = document.getElementById('paginationContainer');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const paginationInfo = document.getElementById('paginationInfo');
    
    if (!paginationContainer || !prevButton || !nextButton || !paginationInfo) return;
    
    totalResults = pagination.total;
    
    if (pagination.total > COMMERCIAL_CONFIG.CLIENTS_PER_PAGE) {
        paginationContainer.style.display = 'flex';
        
        // Bouton précédent
        prevButton.disabled = pagination.offset === 0;
        
        // Bouton suivant
        nextButton.disabled = !pagination.has_more;
        
        // Information de pagination
        const start = pagination.offset + 1;
        const end = Math.min(pagination.offset + pagination.limit, pagination.total);
        paginationInfo.textContent = `${start} - ${end} sur ${pagination.total} résultats`;
    } else {
        paginationContainer.style.display = 'none';
    }
}

/**
 * Met à jour le résumé des résultats
 */
function updateResultsSummary(pagination, filters) {
    const summaryElement = document.getElementById('resultsSummary');
    if (!summaryElement) return;
    
    if (pagination.total === 0) {
        summaryElement.style.display = 'none';
        return;
    }
    
    let summary = `<strong>${pagination.total}</strong> client(s) trouvé(s)`;
    
    const activeFilters = [];
    if (filters.type_client) {
        activeFilters.push(`Type: ${filters.type_client === '1' ? 'Particulier' : 'Professionnel'}`);
    }
    if (filters.has_phone === '1') {
        activeFilters.push('Avec téléphone');
    } else if (filters.has_phone === '0') {
        activeFilters.push('Sans téléphone');
    }
    if (filters.has_email === '1') {
        activeFilters.push('Avec email');
    } else if (filters.has_email === '0') {
        activeFilters.push('Sans email');
    }
    if (filters.departement) {
        activeFilters.push(`Département: ${filters.departement}`);
    }
    if (filters.ville) {
        activeFilters.push(`Ville: ${filters.ville}`);
    }
    if (filters.is_active === '1') {
        activeFilters.push('Actifs uniquement');
    } else if (filters.is_active === '0') {
        activeFilters.push('Inactifs uniquement');
    }
    if (filters.search) {
        activeFilters.push(`Recherche: "${filters.search}"`);
    }
    
    if (activeFilters.length > 0) {
        summary += ` avec les filtres: ${activeFilters.join(', ')}`;
    }
    
    summaryElement.innerHTML = summary;
    summaryElement.style.display = 'block';
}

/**
 * Affiche l'indicateur de chargement
 */
function showLoading() {
    const elements = {
        loading: document.getElementById('loadingMessage'),
        table: document.getElementById('clientsTableContainer'),
        noResults: document.getElementById('noResultsMessage'),
        error: document.getElementById('errorMessage'),
        summary: document.getElementById('resultsSummary'),
        pagination: document.getElementById('paginationContainer')
    };
    
    if (elements.loading) elements.loading.style.display = 'block';
    if (elements.table) elements.table.style.display = 'none';
    if (elements.noResults) elements.noResults.style.display = 'none';
    if (elements.error) elements.error.style.display = 'none';
    if (elements.summary) elements.summary.style.display = 'none';
    if (elements.pagination) elements.pagination.style.display = 'none';
}

/**
 * Cache l'indicateur de chargement
 */
function hideLoading() {
    const loadingElement = document.getElementById('loadingMessage');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

/**
 * Affiche un message d'erreur
 */
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
    
    const elements = {
        table: document.getElementById('clientsTableContainer'),
        noResults: document.getElementById('noResultsMessage'),
        summary: document.getElementById('resultsSummary'),
        pagination: document.getElementById('paginationContainer')
    };
    
    if (elements.table) elements.table.style.display = 'none';
    if (elements.noResults) elements.noResults.style.display = 'none';
    if (elements.summary) elements.summary.style.display = 'none';
    if (elements.pagination) elements.pagination.style.display = 'none';
}

/**
 * Formate une date pour l'affichage
 */
function formatDate(dateString) {
    if (!dateString) return 'Non renseigné';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    } catch (e) {
        return 'Date invalide';
    }
}

/**
 * Échappement HTML pour éviter les injections XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}