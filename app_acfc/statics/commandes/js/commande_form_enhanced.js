/**
 * ACFC - S// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger le catalogue depuis les données du template
    chargerCatalogueFromTemplate();
    
    // Initialiser les événements
    initialiserEvenements();
    
    // Vérifier la présence de produits
    verifierPresenceProduits();
    
    // Le montant initial est déjà correctement affiché via Jinja2
    console.log('Interface de commande initialisée');
}); pour Formulaire de Commande
 * ==================================================
 * 
 * Gestion avancée du formulaire de commande avec :
 * - Modal de sélection des produits avec recherche
 * - Tableau des produits sélectionnés éditable
 * - Duplication de lignes
 * - Calcul automatique des totaux
 * - Gestion des remises
 */

// Variables globales
let ligneCounter = 1000; // Compteur pour les nouvelles lignes
let catalogueComplet = [];

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger le catalogue depuis les données du template
    chargerCatalogueFromTemplate();
    
    // Initialiser les événements
    initialiserEvenements();
    
    // Vérifier la présence de produits
    verifierPresenceProduits();
    
    // Ne recalculer le total que si on est en mode création (pas de montant existant)
    // En mode modification, on garde le montant existant de la commande
    const montantInput = document.getElementById('montant');
    const isModification = montantInput && montantInput.value && parseFloat(montantInput.value) > 0;
    
    if (!isModification) {
        // Mode création : calculer le total depuis les lignes
        calculerTotalCommande();
    } else {
        // Mode modification : conserver le montant existant et l'afficher
        const totalElement = document.getElementById('totalCommande');
        if (totalElement && montantInput.value) {
            totalElement.textContent = parseFloat(montantInput.value).toFixed(2) + ' €';
        }
    }
    
    console.log('Interface de commande initialisée');
});

/**
 * Charger le catalogue depuis les données du template
 */
function chargerCatalogueFromTemplate() {
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    catalogueComplet = [];
    
    rows.forEach(row => {
        const produitId = row.querySelector('.modal-product-checkbox').getAttribute('data-produit-id');
        const cells = row.querySelectorAll('td');
        
        catalogueComplet.push({
            id: parseInt(produitId),
            reference: cells[1].textContent.trim(),
            designation: cells[2].textContent.trim(),
            type: cells[3].textContent.trim(),
            millesime: cells[4].textContent.trim(),
            geographie: cells[5].textContent.trim(),
            prix: parseFloat(cells[6].textContent.replace(' €', '').replace(',', '.'))
        });
    });
}

/**
 * Initialiser les événements
 */
function initialiserEvenements() {
    // Event listener pour la remise client
    const remiseClientInput = document.getElementById('remise_client');
    if (remiseClientInput) {
        remiseClientInput.addEventListener('change', function() {
            // Optionnel : appliquer la nouvelle remise aux lignes existantes
            // appliquerRemiseParDefaut();
        });
    }
    
    // Event listeners pour les modales
    const selectionModal = document.getElementById('selectionProduitsModal');
    if (selectionModal) {
        selectionModal.addEventListener('shown.bs.modal', function() {
            reinitialiserFiltresModal();
            document.getElementById('rechercheProductsInput').focus();
        });
    }
}

/**
 * Filtrer les produits dans le modal
 */
function filtrerProduitsCatalogue() {
    const recherche = document.getElementById('rechercheProductsInput').value.toLowerCase();
    const millesime = document.getElementById('modalFilterMillesime').value;
    const type = document.getElementById('modalFilterType').value;
    const geographie = document.getElementById('modalFilterGeographie').value;
    
    const rows = document.querySelectorAll('#modalCatalogueBody .modal-catalogue-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const rowMillesime = row.getAttribute('data-millesime');
        const rowType = row.getAttribute('data-type');
        const rowGeographie = row.getAttribute('data-geographie');
        const rowReference = row.getAttribute('data-reference');
        const rowDesignation = row.getAttribute('data-designation');
        
        let visible = true;
        
        // Filtre par recherche
        if (recherche && !rowReference.includes(recherche) && !rowDesignation.includes(recherche)) {
            visible = false;
        }
        
        // Filtre par millésime
        if (millesime && rowMillesime !== millesime) {
            visible = false;
        }
        
        // Filtre par type
        if (type && rowType !== type) {
            visible = false;
        }
        
        // Filtre par géographie
        if (geographie && rowGeographie !== geographie) {
            visible = false;
        }
        
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });
    
    // Afficher/masquer le message "aucun produit"
    const messageDiv = document.getElementById('modalAucunProduitMessage');
    if (messageDiv) {
        messageDiv.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

/**
 * Réinitialiser la recherche
 */
function reinitialiserRecherche() {
    document.getElementById('rechercheProductsInput').value = '';
    filtrerProduitsCatalogue();
}

/**
 * Réinitialiser les filtres du modal
 */
function reinitialiserFiltresModal() {
    const currentYear = new Date().getFullYear();
    document.getElementById('rechercheProductsInput').value = '';
    document.getElementById('modalFilterMillesime').value = currentYear;
    document.getElementById('modalFilterType').value = 'Courrier';
    document.getElementById('modalFilterGeographie').value = 'FRANCE';
    filtrerProduitsCatalogue();
}

/**
 * Ajouter les produits sélectionnés au tableau principal
 */
function ajouterProduitsSelectionnes() {
    const checkboxes = document.querySelectorAll('#modalCatalogueBody .modal-product-checkbox:checked');
    const remiseParDefaut = parseFloat(document.getElementById('remise_client').value) || 0;
    
    let ajouts = 0;
    
    checkboxes.forEach(checkbox => {
        const produitId = parseInt(checkbox.getAttribute('data-produit-id'));
        const qteInput = document.getElementById(`modalQte_${produitId}`);
        const quantite = parseInt(qteInput.value) || 1;
        
        // Trouver les infos du produit
        const produit = catalogueComplet.find(p => p.id === produitId);
        if (produit) {
            ajouterLigneProduit(produit, quantite, remiseParDefaut);
            ajouts++;
        }
        
        // Réinitialiser la checkbox et la quantité
        checkbox.checked = false;
        qteInput.value = 1;
    });
    
    if (ajouts > 0) {
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('selectionProduitsModal'));
        modal.hide();
        
        // Recalculer le total
        calculerTotalCommande();
        
        // Vérifier la présence de produits
        verifierPresenceProduits();
        
        // Message de confirmation
        console.log(`${ajouts} produit(s) ajouté(s) à la commande`);
    }
}

/**
 * Ajouter une ligne de produit au tableau principal
 */
function ajouterLigneProduit(produit, quantite, remise) {
    ligneCounter++;
    const tbody = document.getElementById('produitsSelectionnesBody');
    
    const row = document.createElement('tr');
    row.setAttribute('data-produit-id', produit.id);
    row.setAttribute('data-ligne-id', ligneCounter);
    
    const totalLigne = quantite * produit.prix * (1 - remise / 100);
    
    row.innerHTML = `
        <td class="reference">${produit.reference}</td>
        <td class="designation">${produit.designation}</td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control prix-input" 
                       name="prix_${produit.id}_${ligneCounter}" 
                       value="${produit.prix.toFixed(2)}" 
                       step="0.01" min="0" onchange="calculerTotalLigne(this)"
                       title="Prix unitaire HT">
                <span class="input-group-text">€</span>
            </div>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm qte-input" 
                   name="qte_${produit.id}_${ligneCounter}" 
                   value="${quantite}" 
                   min="1" onchange="calculerTotalLigne(this)"
                   title="Quantité">
        </td>
        <td>
            <div class="input-group input-group-sm">
                <input type="number" class="form-control remise-input" 
                       name="remise_${produit.id}_${ligneCounter}" 
                       value="${remise.toFixed(1)}" 
                       step="0.1" min="0" max="100" onchange="calculerTotalLigne(this)"
                       title="Remise en pourcentage">
                <span class="input-group-text">%</span>
            </div>
        </td>
        <td class="total-ligne fw-bold">
            ${totalLigne.toFixed(2)} €
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-primary me-1" onclick="duppliquerLigne(this)" title="Dupliquer">
                <i class="fas fa-copy"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="supprimerLigne(this)" title="Supprimer">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
}

/**
 * Calculer le total d'une ligne
 */
function calculerTotalLigne(input) {
    const row = input.closest('tr');
    const prixInput = row.querySelector('.prix-input');
    const qteInput = row.querySelector('.qte-input');
    const remiseInput = row.querySelector('.remise-input');
    const totalCell = row.querySelector('.total-ligne');
    
    const prix = parseFloat(prixInput.value) || 0;
    const qte = parseInt(qteInput.value) || 1;
    const remise = parseFloat(remiseInput.value) || 0;
    
    const total = qte * prix * (1 - remise / 100);
    totalCell.textContent = total.toFixed(2) + ' €';
    
    // Recalculer le total de la commande
    calculerTotalCommande();
}

/**
 * Dupliquer une ligne
 */
function duppliquerLigne(button) {
    const row = button.closest('tr');
    const produitId = row.getAttribute('data-produit-id');
    
    // Récupérer les valeurs actuelles
    const prix = parseFloat(row.querySelector('.prix-input').value) || 0;
    const quantite = parseInt(row.querySelector('.qte-input').value) || 1;
    const remise = parseFloat(row.querySelector('.remise-input').value) || 0;
    const reference = row.querySelector('.reference').textContent;
    const designation = row.querySelector('.designation').textContent;
    
    // Créer un objet produit temporaire
    const produit = {
        id: parseInt(produitId),
        reference: reference,
        designation: designation,
        prix: prix
    };
    
    // Ajouter la nouvelle ligne
    ajouterLigneProduit(produit, quantite, remise);
    
    // Recalculer le total
    calculerTotalCommande();
}

/**
 * Supprimer une ligne
 */
function supprimerLigne(button) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette ligne ?')) {
        const row = button.closest('tr');
        row.remove();
        calculerTotalCommande();
        verifierPresenceProduits();
    }
}

/**
 * Calculer le total de la commande
 */
function calculerTotalCommande() {
    const totalCells = document.querySelectorAll('#produitsSelectionnesBody .total-ligne');
    let total = 0;
    
    totalCells.forEach(cell => {
        const value = parseFloat(cell.textContent.replace(' €', '').replace(',', '.')) || 0;
        total += value;
    });
    
    // Mettre à jour l'affichage du total dans le tableau
    const totalElement = document.getElementById('totalCommande');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' €';
    }
    
    // Mettre à jour le champ montant pour le formulaire
    const montantInput = document.getElementById('montant');
    if (montantInput) {
        montantInput.value = total.toFixed(2);
    }
    
    console.log(`Total calculé: ${total.toFixed(2)} €`);
}

/**
 * Vérifier la présence de produits et afficher/masquer le message approprié
 */
function verifierPresenceProduits() {
    const tbody = document.getElementById('produitsSelectionnesBody');
    const messageDiv = document.getElementById('aucunProduitMessage');
    
    if (tbody && messageDiv) {
        const hasProducts = tbody.children.length > 0;
        messageDiv.style.display = hasProducts ? 'none' : 'block';
    }
}

/**
 * Appliquer la remise par défaut à toutes les lignes existantes
 */
function appliquerRemiseParDefaut() {
    const remiseParDefaut = parseFloat(document.getElementById('remise_client').value) || 0;
    const remiseInputs = document.querySelectorAll('#produitsSelectionnesBody .remise-input');
    
    if (confirm(`Appliquer la remise de ${remiseParDefaut}% à toutes les lignes ?`)) {
        remiseInputs.forEach(input => {
            input.value = remiseParDefaut.toFixed(1);
            calculerTotalLigne(input);
        });
    }
}

// Fonctions existantes pour les modales de facturation et expédition
// (conservées du script original)

/**
 * Gestion du modal de facturation
 */
document.addEventListener('DOMContentLoaded', function() {
    const facturationModal = document.getElementById('facturationModal');
    if (facturationModal) {
        facturationModal.addEventListener('shown.bs.modal', function() {
            // Définir la date du jour par défaut
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('date_facturation').value = today;
        });
        
        // Gestion du bouton de confirmation
        const confirmerFacturation = document.getElementById('confirmerFacturation');
        if (confirmerFacturation) {
            confirmerFacturation.addEventListener('click', function() {
                const dateFacturation = document.getElementById('date_facturation').value;
                if (!dateFacturation) {
                    alert('Veuillez sélectionner une date de facturation');
                    return;
                }
                
                // Ajouter les champs au formulaire principal et soumettre
                const form = document.querySelector('form');
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                actionInput.value = 'facturer';
                form.appendChild(actionInput);
                
                const dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'date_facturation';
                dateInput.value = dateFacturation;
                form.appendChild(dateInput);
                
                form.submit();
            });
        }
    }
    
    const expeditionModal = document.getElementById('expeditionModal');
    if (expeditionModal) {
        expeditionModal.addEventListener('shown.bs.modal', function() {
            // Définir la date du jour par défaut
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('date_expedition').value = today;
            
            // Gérer l'affichage conditionnel du champ de suivi
            const modeExpedition = document.querySelector('input[name="mode_expedition"]:checked');
            toggleSuiviField(modeExpedition ? modeExpedition.value : 'sans_suivi');
        });
        
        // Event listeners pour les radio buttons du mode d'expédition
        const modeExpeditionRadios = document.querySelectorAll('input[name="mode_expedition"]');
        modeExpeditionRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                toggleSuiviField(this.value);
            });
        });
        
        // Gestion du bouton de confirmation
        const confirmerExpedition = document.getElementById('confirmerExpedition');
        if (confirmerExpedition) {
            confirmerExpedition.addEventListener('click', function() {
                const dateExpedition = document.getElementById('date_expedition').value;
                const modeExpedition = document.querySelector('input[name="mode_expedition"]:checked');
                
                if (!dateExpedition) {
                    alert('Veuillez sélectionner une date d\'expédition');
                    return;
                }
                
                if (!modeExpedition) {
                    alert('Veuillez sélectionner un mode d\'expédition');
                    return;
                }
                
                // Vérifier le numéro de suivi si nécessaire
                if (modeExpedition.value === 'suivi') {
                    const idSuivi = document.getElementById('id_suivi').value.trim();
                    if (!idSuivi) {
                        alert('Veuillez saisir le numéro de suivi');
                        return;
                    }
                }
                
                // Ajouter les champs au formulaire principal et soumettre
                const form = document.querySelector('form');
                
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'action';
                actionInput.value = 'expedier';
                form.appendChild(actionInput);
                
                const dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'date_expedition';
                dateInput.value = dateExpedition;
                form.appendChild(dateInput);
                
                const modeInput = document.createElement('input');
                modeInput.type = 'hidden';
                modeInput.name = 'mode_expedition';
                modeInput.value = modeExpedition.value;
                form.appendChild(modeInput);
                
                if (modeExpedition.value === 'suivi') {
                    const suiviInput = document.createElement('input');
                    suiviInput.type = 'hidden';
                    suiviInput.name = 'id_suivi';
                    suiviInput.value = document.getElementById('id_suivi').value;
                    form.appendChild(suiviInput);
                }
                
                form.submit();
            });
        }
    }
});

/**
 * Gérer l'affichage du champ de suivi selon le mode d'expédition
 */
function toggleSuiviField(mode) {
    const suiviGroup = document.getElementById('suiviGroup');
    if (suiviGroup) {
        suiviGroup.style.display = mode === 'suivi' ? 'block' : 'none';
    }
}
