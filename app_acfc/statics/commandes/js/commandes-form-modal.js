// =====================================================================
// Variables globales
// =====================================================================
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
    row.setAttribute('data-produit-id', produit.id || 'new');
    row.setAttribute('data-ligne-id', ligneCounter);
    row.setAttribute('data-sum', quantite * produit.prix * (1 - remise / 100));
    row.setAttribute('data-remise', remise);
    row.setAttribute('data-quantite', quantite);
    row.setAttribute('data-prix', produit.prix);

    // Création de l'objet produit pour stockage JSON
    let produitContent = {
        id: produit.id || 'new',
        reference: produit.reference.toUpperCase() || '',
        designation: produit.designation.toUpperCase() || '',
        prix: produit.prix || 0,
        quantite: quantite || 1,
        remise: (remise/100).toFixed(2) || 0.10
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
                       onchange=updateSums(${ligneCounter})>
                <span class="input-group-text">€</span>
            </div>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${ligneCounter}" 
                   value="${quantite}" 
                   min="1"
                   title="Quantité"
                   onchange=updateSums(${ligneCounter})>
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control remise-input" 
                       name="remise_${ligneCounter}" 
                       value="${remise.toFixed(1)}" 
                       step="0.1" min="0" max="100"
                       title="Remise en pourcentage"
                       onchange=updateSums(${ligneCounter})>
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

function updateSums(rowIndex) {
    // Récupérer la ligne correspondante
    const row = document.querySelector(`#produitsSelectionnesBody tr[data-ligne-id="${rowIndex}"]`);
    const rowData = document.querySelector(`#produitsSelectionnesBody tr`);

    // Si la ligne n'existe pas, sortir de la fonction
    if (!row) return;

    // Récupérer les éléments de la ligne
    const prixUnitaire = parseFloat(row.querySelector('.prix-input').value).toFixed(2);
    const quantite = parseInt(row.querySelector('.qte-input').value);
    const remise = parseFloat(row.querySelector('.remise-input').value).toFixed(2);
    const totalValue = (quantite * prixUnitaire * (1 - remise / 100)).toFixed(2);
    let produitContent = {
        id: rowData.getAttribute('data-produit-id') || 'new',
        reference: row.cells[1]?.textContent.toUpperCase() || '',
        designation: row.cells[2]?.textContent.toUpperCase() || '',
        prix: parseFloat(prixUnitaire) || 0,
        quantite: quantite || 1,
        remise: parseFloat(remise) || 0
    }

    // Mise à jour du formulaire
    rowData.querySelector('.data-product').textContent = JSON.stringify(produitContent);
    rowData.setAttribute('data-prix', prixUnitaire);
    rowData.setAttribute('data-quantite', quantite);
    rowData.setAttribute('data-remise', remise);
    rowData.setAttribute('data-sum', totalValue);

    // Mise à jour des totaux dans la ligne et la commande
    row.querySelector('.total-ligne').textContent = `${totalValue} €`;
    calculerTotalCommande();
}
