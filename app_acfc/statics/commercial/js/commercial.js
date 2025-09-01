/**
 * ACFC - JavaScript Module Commercial (Version Simplifiée)
 */

document.addEventListener('DOMContentLoaded', function() {
    // Si on est sur la page de liste des clients
    if (window.COMMERCIAL_SUBCONTEXT === 'filter_list') {
        initClientsList();
    }
});

function initClientsList() {
    // Chargement initial des clients
    loadClients();
    
    // Événement de soumission du formulaire
    document.getElementById('filtersForm').addEventListener('submit', function(e) {
        e.preventDefault();
        loadClients();
    });
    
    // Bouton de réinitialisation
    document.getElementById('resetFilters').addEventListener('click', function() {
        document.getElementById('filtersForm').reset();
        loadClients();
    });
}

async function loadClients() {
    try {
        // Afficher le loading
        document.getElementById('loadingMessage').classList.remove('hidden');
        document.getElementById('clientsTableContainer').classList.add('hidden');
        document.getElementById('errorMessage').classList.add('hidden');
        
        // Récupérer les données du formulaire
        const formData = new FormData(document.getElementById('filtersForm'));
        const params = new URLSearchParams(formData);
        
        // Appel API
        const response = await fetch(`/commercial/clients/api/search?${params}`);
        const data = await response.json();
        
        // Cacher le loading
        document.getElementById('loadingMessage').classList.add('hidden');
        
        if (data.success) {
            displayClients(data.clients);
            updateSummary(data.pagination.total);
        } else {
            showError('Erreur lors du chargement des clients');
        }
        
    } catch (error) {
        console.error('Erreur lors du chargement des clients:', error);
        document.getElementById('loadingMessage').classList.add('hidden');
        showError('Erreur de connexion');
    }
}

function displayClients(clients) {
    const tbody = document.getElementById('clientsTableBody');
    const tableContainer = document.getElementById('clientsTableContainer');
    
    if (clients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Aucun client trouvé</td></tr>';
    } else {
        tbody.innerHTML = clients.map(client => `
            <tr>
                <td><strong>${client.nom_affichage}</strong></td>
                <td>
                    <span class="badge ${client.type_client === 1 ? 'bg-primary' : 'bg-info'}">
                        ${client.type_client === 1 ? 'Particulier' : 'Professionnel'}
                    </span>
                </td>
                <td>
                    ${client.has_phone ? '📞' : '❌'} 
                    ${client.has_email ? '📧' : '❌'}
                </td>
                <td>${client.departement || 'N/A'}</td>
                <td>
                    <span class="badge ${client.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${client.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </td>
                <td>${new Date(client.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                    <a href="/clients/${client.id}" class="btn btn-sm btn-primary">Voir</a>
                </td>
            </tr>
        `).join('');
    }
    
    tableContainer.classList.remove('hidden');
}

function updateSummary(total) {
    document.getElementById('resultsSummary').innerHTML = `<strong>${total}</strong> client(s) trouvé(s)`;
    document.getElementById('resultsSummary').classList.remove('hidden');
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorMessage').classList.remove('hidden');
    document.getElementById('clientsTableContainer').classList.add('hidden');
    document.getElementById('resultsSummary').classList.add('hidden');
}
