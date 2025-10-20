// =====================================================================
// Variables globales
// =====================================================================
let ligneCounter = 1000000000; // Compteur pour les nouvelles lignes

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
    const filters = getFilterValues();
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    let visibleCount = 0;
    
    for (const row of rows) {
        const rowData = extractRowData(row);
        const visible = isRowVisible(rowData, filters);
        
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    }
    
    updateNoProductMessage(visibleCount);
}

function getFilterValues() {
    return {
        recherche: document.getElementById('rechercheProductsInput')?.value.toLowerCase() || '',
        millesime: document.getElementById('modalFilterMillesime')?.value || '',
        type: document.getElementById('modalFilterType')?.value || '',
        geographie: document.getElementById('modalFilterGeographie')?.value || ''
    };
}

function extractRowData(row) {
    return {
        millesime: row.dataset.millesime || '',
        type: row.dataset.type || '',
        geographie: row.dataset.geographie || '',
        reference: (row.dataset.reference || '').toLowerCase(),
        designation: (row.dataset.designation || '').toLowerCase()
    };
}

function isRowVisible(rowData, filters) {
    if (filters.recherche && !matchesSearchFilter(rowData, filters.recherche)) {
        return false;
    }
    
    return matchesSpecificFilters(rowData, filters);
}

function matchesSearchFilter(rowData, searchTerm) {
    return rowData.reference.includes(searchTerm) || rowData.designation.includes(searchTerm);
}

function matchesSpecificFilters(rowData, filters) {
    if (filters.millesime && rowData.millesime !== filters.millesime) return false;
    if (filters.type && rowData.type !== filters.type) return false;
    if (filters.geographie && rowData.geographie !== filters.geographie) return false;
    return true;
}

function updateNoProductMessage(visibleCount) {
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
    
    for (const element of elementsToReset) {
        const el = document.getElementById(element.id);
        if (el) el.value = element.value;
    }
    
    filtrerProduitsCatalogue();
}

// =====================================================================
// Ajouter un produit du catalogue à la commande
// =====================================================================
function ajouterProduitsSelectionnes() {
    const checkboxes = document.querySelectorAll('#modalCatalogueBody .modal-product-checkbox:checked');
    const remiseParDefaut = Number.parseFloat(document.getElementById('remise_client')?.value) || 0.1; // Valeur par défaut de la remise
    
    if (checkboxes.length === 0) {
        showAlert('Veuillez sélectionner au moins un produit.', 'warning');
        return;
    }
    
    let ajouts = 0;
    
    for (const checkbox of checkboxes) {
        const row = checkbox.closest('.modal-catalogue-row');
        // Récupération des données produits pour chaque ligne sélectionnée
        const reference = row.dataset.reference || '';
        const designation = row.dataset.designation || '';
        const prix = row.cells[6];
        const quantiteInput = row.querySelector('.modal-qte-input');
        const quantite = Number.parseInt(quantiteInput?.value) || 1;
        
        const produit = {
            reference: reference,
            designation: designation,
            prix: prix ? Number.parseFloat(prix.textContent.replace(' €', '').replace(',', '.')) : 0
        };
        
        ajouterLigneProduit(produit, quantite, remiseParDefaut);
        checkbox.checked = false;
        if (quantiteInput) quantiteInput.value = 1;
        ajouts++;
    }
    
    if (ajouts > 0) {
        calculerTotalOrder();
        
        // Fermer la modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('selectionProduitsModal'));
        if (modal) modal.hide();
        
        showAlert(`${ajouts} produit(s) ajouté(s) avec succès !`, 'success');
    }
}

// =====================================================================
// Ajouter une ligne produit dans le tableau de la commande
// =====================================================================
function ajouterLigneProduit(produit, quantite, remise, isDuplicate = false) {
    // Vérifier si le message "Aucun produit" est affiché
    let isNoneProduct = !!document.getElementById('aucunProduitMessage');
    // Incrémenter le compteur de lignes
    ligneCounter++;
    // Référence au tbody du tableau des produits sélectionnés
    const tbody = document.getElementById('produitsSelectionnesBody');
    // Si le tbody n'existe pas, sortir de la fonction
    if (!tbody) return;
    
    // Création de la nouvelle ligne
    const row = document.createElement('tr');

    // Attributs data pour la ligne
    row.dataset.ligneId = isDuplicate ? `new${ligneCounter}` : produit.id;
    row.dataset.sum = quantite * produit.prix * (1 - remise / 100);
    row.dataset.remise = remise;
    row.dataset.quantite = quantite;
    row.dataset.prix = produit.prix;

    // Création de l'objet produit pour stockage JSON
    let produitContent = {
        id: isDuplicate ? `new${ligneCounter}` : produit.id,
        reference: produit.reference.toUpperCase() || '',
        designation: produit.designation.toUpperCase() || '',
        prix_unitaire: produit.prix || 0,
        qte: quantite || 1,
        remise: remise || 10
    }
    
    // Calcul du total de la ligne
    const totalLigne = quantite * produit.prix * (1 - remise / 100);
    
    // Contenu HTML de la ligne
    row.innerHTML = `
        <td class="data-product d-none">
            <div class="data-product">
                <input type="hidden" name="lignes_${ligneCounter}" class="data-product" value='${JSON.stringify(produitContent)}'>
            </div>
        </td>
        <td class="reference">${produit.reference.toUpperCase()}</td>
        <td class="designation">${produit.designation.toUpperCase()}</td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control prix-input" 
                       name="prix_${ligneCounter}" 
                       value="${produit.prix.toFixed(2)}" 
                       step="0.01" min="0"
                       title="Prix unitaire HT"
                       onchange=updateSums('new${ligneCounter}')>
                <span class="input-group-text">€</span>
            </div>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${ligneCounter}" 
                   value="${quantite}" 
                   min="1"
                   title="Quantité"
                   onchange=updateSums('new${ligneCounter}')>
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control remise-input" 
                       name="remise_${ligneCounter}" 
                       value="${remise.toFixed(1)}" 
                       step="0.1" min="0" max="100"
                       title="Remise en pourcentage"
                       onchange=updateSums('new${ligneCounter}')>
                <span class="input-group-text">%</span>
            </div>
        </td>
        <td class="total-ligne fw-bold">
            ${totalLigne.toFixed(2)} €
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-primary me-1" onclick="dupliquerLigne(this)" title="Dupliquer">
                <i class="fas fa-copy"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="supprimerLigne(this)" title="Supprimer">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;

    // Suppression du message "Aucun produit"
    if (isNoneProduct) {
        const noneMessage = document.getElementById('aucunProduitMessage');
        if (noneMessage) noneMessage.className = 'd-none';
    }
    
    // Ajouter les gestionnaires d'événements pour les boutons
    tbody.appendChild(row);
}

// =====================================================================
// Calculer le total de la commande + MàJ des champs de totaux
// =====================================================================
function calculerTotalOrder() {
    const totalCells = document.querySelectorAll('#produitsSelectionnesBody .total-ligne');
    let total = 0;
    
    for (const cell of totalCells) {
        const cellText = cell.textContent.trim();
        
        // Nettoyer le texte pour extraire le nombre
        const cleanValue = cellText.replaceAll(/[€\s]/g, '').replaceAll(',', '.');
        const value = Number.parseFloat(cleanValue) || 0;
        
        total += value;
    }
    
    // Mettre à jour l'affichage du total dans le tableau
    const totalElement = document.getElementById('totalOrder');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
    
    // Mettre à jour le champ montant UNIQUEMENT si il y a des lignes de produits
    const montantInput = document.getElementById('montant');
    if (montantInput && totalCells.length > 0) {
        montantInput.value = total.toFixed(2);
    }
}

// Récupérer les données d'un produit existant dans la commande
function getExistingProduct(idProduct) {
    const productRow = document.querySelector(`#produitsSelectionnesBody tr[data-ligne-id="${idProduct}"]`);
    const productData = productRow ? productRow.querySelector(`input[name^="lignes_"]`).value : null;
    return productData ? JSON.parse(productData) : null;
}

function updateSums(rowIndex) {
    // Récupérer la ligne correspondante
    const row = document.querySelector(`#produitsSelectionnesBody tr[data-ligne-id="${rowIndex}"]`);

    // Si la ligne n'existe pas, sortir de la fonction
    if (!row) return;

    // Récupérer les éléments de la ligne
    const prixUnitaire = Number.parseFloat(row.querySelector('.prix-input').value).toFixed(2);
    const quantite = Number.parseInt(row.querySelector('.qte-input').value);
    const remise = Number.parseFloat(row.querySelector('.remise-input').value).toFixed(2);
    const totalValue = (quantite * prixUnitaire * (1 - remise / 100)).toFixed(2);

    // Récupération des données actuelles du produit pour mise à jour
    let existingProduct = getExistingProduct(rowIndex);
    if (existingProduct === null) {
        existingProduct = {
            id: row.dataset.produitId || `new${rowIndex}`,
            reference: row.cells[1]?.textContent.toUpperCase() || '',
            designation: row.cells[2]?.textContent.toUpperCase() || '',
            prix_unitaire: Number.parseFloat(prixUnitaire) || 0,
            qte: quantite || 1,
            remise: Number.parseFloat(remise) || 0
        }
    } else {
        existingProduct.prix_unitaire = Number.parseFloat(prixUnitaire) || 0;
        existingProduct.qte = quantite || 1;
        existingProduct.remise = Number.parseFloat(remise) || 0;
    }

    // Mise à jour du formulaire
    row.querySelector(`input[name^="lignes_"]`).value = JSON.stringify(existingProduct);
    row.dataset.prix = prixUnitaire;
    row.dataset.quantite = quantite;
    row.dataset.remise = remise;
    row.dataset.sum = totalValue;

    // Mise à jour des totaux dans la ligne et la commande
    row.querySelector('.total-ligne').textContent = `${totalValue} €`;
    calculerTotalOrder();
}

function dupliquerLigne(button) {
    const row = button.closest('tr');
    const produitId = row.dataset.ligneId;
    
    // Récupérer les valeurs actuelles
    const prix = Number.parseFloat(row.querySelector('.prix-input').value) || 0;
    const qte = Number.parseInt(row.querySelector('.qte-input').value) || 1;
    const remise = Number.parseFloat(row.querySelector('.remise-input').value) || 0;
    const reference = row.querySelector('.reference').textContent;
    const designation = row.querySelector('.designation').textContent;
    const produit = {
        id: produitId,
        reference: reference,
        designation: designation,
        prix: prix
    };
    ajouterLigneProduit(produit, qte, remise, true);
    calculerTotalOrder();
    showAlert('Ligne dupliquée avec succès !', 'success');
}

function supprimerLigne(button) {
    const row = button.closest('tr');
    
    // Vérifier si la ligne est facturée
    if (row.dataset.ligneFacturee) {
        showAlert('Impossible de supprimer une ligne déjà facturée !', 'error');
        return;
    }
    
    if (confirm('Êtes-vous sûr de vouloir supprimer cette ligne ?')) {
        row.remove();
        verifierPresenceProduits();
        calculerTotalOrder();
        showAlert('Ligne supprimée avec succès !', 'success');
    }
}

function verifierPresenceProduits() {
    const tbody = document.getElementById('produitsSelectionnesBody');
    if (!tbody) return;
    
    const lignes = tbody.querySelectorAll('tr[data-ligne-id]');
    const messageVide = document.getElementById('aucunProduitMessage'); // Utiliser le message du template
    
    if (lignes.length === 0) {
        // Afficher le message existant dans le template
        if (messageVide) {
            messageVide.style.display = 'block';
        }
        
        // Supprimer tout message dans le tbody si il existe
        const messageInTbody = document.getElementById('messageAucunProduit');
        if (messageInTbody) {
            messageInTbody.remove();
        }
    } else if (messageVide) messageVide.style.display = 'none';
}
