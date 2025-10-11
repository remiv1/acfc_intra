let ligneCounter = 1000; // Compteur pour les nouvelles lignes

// =====================================================================
// Initialisations au chargement du DOM
// =====================================================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le filtrage au chargement
    filtrerProduitsCatalogue();
});

// =====================================================================
// Filtrer les produits dans le catalogue modal
// =====================================================================
function filtrerProduitsCatalogue() {
    const rechercheInput = document.getElementById('rechercheProductsInput')?.value.toLowerCase() || '';
    const millesimeInput = document.getElementById('modalFilterMillesime')?.value || '';
    const typeInput = document.getElementById('modalFilterType')?.value || '';
    const geographieInput = document.getElementById('modalFilterGeographie')?.value || '';
    
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        // Récupérer les données depuis la ligne et les cellules
        const millesime = row.dataset.millesime || '';
        const type = row.dataset.type || '';
        const geographie = row.dataset.geographie || '';
        const reference = row.dataset.reference || '';
        const designation = row.dataset.designation || '';
        const referenceContent = reference ? reference.toLowerCase() : '';
        const designationContent = designation ? designation.toLowerCase() : '';
        
        let visible = true;
        
        // Filtre de recherche
        if (rechercheInput && !referenceContent.includes(rechercheInput) && !designationContent.includes(rechercheInput)) {
            visible = false;
        }
        
        // Filtres spécifiques
        if (millesimeInput && millesime !== millesimeInput) visible = false;
        if (typeInput && type !== typeInput) visible = false;
        if (geographieInput && geographie !== geographieInput) visible = false;
        
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });
    
    // Afficher/masquer le message "aucun produit"
    const messageDiv = document.getElementById('modalAucunProduitMessage');
    if (messageDiv) {
        messageDiv.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

// =====================================================================
// Réinitialisation de la recherche
// =====================================================================
function reinitialiserRecherche() {
    document.getElementById('rechercheProductsInput').value = '';
    filtrerProduitsCatalogue();
};

// =====================================================================
// Réinitialiser les filtres dans le modal catalogue
// =====================================================================
function reinitialiserFiltresModal() {
    const currentYear = new Date().getFullYear();
    const elementsToReset = [
        { id: 'rechercheProductsInput', value: '' },
        { id: 'modalFilterMillesime', value: currentYear },
        { id: 'modalFilterType', value: 'Courrier' },
        { id: 'modalFilterGeographie', value: 'FRANCE' }
    ];
    
    elementsToReset.forEach(element => {
        const el = document.getElementById(element.id);
        if (el) el.value = element.value;
    });
    
    filtrerProduitsCatalogue();
}

// =====================================================================
// Ajouter un produit du catalogue à la commande
// =====================================================================
function ajouterProduitsSelectionnes() {
    const checkboxes = document.querySelectorAll('#modalCatalogueBody .modal-product-checkbox:checked');
    const remiseParDefaut = parseFloat(document.getElementById('remise_client')?.value) || 0.10; // Valeur par défaut de la remise
    
    if (checkboxes.length === 0) {
        showAlert('Veuillez sélectionner au moins un produit.', 'warning');
        return;
    }
    
    let ajouts = 0;
    
    checkboxes.forEach(checkbox => {
        const row = checkbox.closest('.modal-catalogue-row');
        // Récupération des données produits pour chaque ligne sélectionnée
        const reference = row.dataset.reference || '';
        const designation = row.dataset.designation || '';
        const prix = row.cells[6];
        const quantiteInput = row.querySelector('.modal-qte-input');
        const quantite = parseInt(quantiteInput?.value) || 1;
        
        const produit = {
            reference: reference,
            designation: designation,
            prix: prix ? parseFloat(prix.textContent.replace(' €', '').replace(',', '.')) : 0
        };
        
        ajouterLigneProduit(produit, quantite, remiseParDefaut);
        checkbox.checked = false;
        if (quantiteInput) quantiteInput.value = 1;
        ajouts++;
    });
    
    if (ajouts > 0) {
        calculerTotalCommande();
        
        // Fermer la modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('selectionProduitsModal'));
        if (modal) modal.hide();
        
        showAlert(`${ajouts} produit(s) ajouté(s) avec succès !`, 'success');
    }
}

// =====================================================================
// Ajouter une ligne produit dans le tableau de la commande
// =====================================================================
function ajouterLigneProduit(produit, quantite, remise) {
    ligneCounter++;
    const tbody = document.getElementById('produitsSelectionnesBody');
    
    if (!tbody) return;
    
    const row = document.createElement('tr');
    row.setAttribute('data-produit-id', produit.id);
    row.setAttribute('data-ligne-id', ligneCounter);
    
    const totalLigne = quantite * produit.prix * (1 - remise / 100);
    
    row.innerHTML = `
        <td class="reference">${produit.reference.toUpperCase()}</td>
        <td class="designation">${produit.designation.toUpperCase()}</td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control prix-input" 
                       name="prix_${produit.id}_${ligneCounter}" 
                       value="${produit.prix.toFixed(2)}" 
                       step="0.01" min="0"
                       title="Prix unitaire HT">
                <span class="input-group-text">€</span>
            </div>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${produit.id}_${ligneCounter}" 
                   value="${quantite}" 
                   min="1"
                   title="Quantité">
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control remise-input" 
                       name="remise_${produit.id}_${ligneCounter}" 
                       value="${remise.toFixed(1)}" 
                       step="0.1" min="0" max="100"
                       title="Remise en pourcentage">
                <span class="input-group-text">%</span>
            </div>
        </td>
        <td class="total-ligne fw-bold">
            ${totalLigne.toFixed(2)} €
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-primary me-1 btn-dupliquer" title="Dupliquer">
                <i class="fas fa-copy"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger btn-supprimer" title="Supprimer">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
}

// =====================================================================
// Calculer le total de la commande
// =====================================================================
function calculerTotalCommande() {
    const totalCells = document.querySelectorAll('#produitsSelectionnesBody .total-ligne');
    let total = 0;
    
    totalCells.forEach((cell, index) => {
        const cellText = cell.textContent.trim();
        
        // Nettoyer le texte pour extraire le nombre
        const cleanValue = cellText.replace(/[€\s]/g, '').replace(',', '.');
        const value = parseFloat(cleanValue) || 0;
        
        total += value;
    });
    
    // Mettre à jour l'affichage du total dans le tableau
    const totalElement = document.getElementById('totalCommande');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
    
    // Mettre à jour le champ montant UNIQUEMENT si il y a des lignes de produits
    const montantInput = document.getElementById('montant');
    if (montantInput && totalCells.length > 0) {
        montantInput.value = total.toFixed(2);
    }
}
