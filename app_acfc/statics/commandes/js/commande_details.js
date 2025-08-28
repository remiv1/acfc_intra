/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour les détails de commande
 * ====================================================================
 * 
 * Fonctionnalités JavaScript pour la page de détails de commande :
 * - Gestion des modales de facturation complète et partielle
 * - Gestion des modales d'expédition complète et partielle
 * - Calcul automatique des totaux dans les modales
 * - Validation des formulaires
 * 
 * Dépendances : Bootstrap 5
 * ====================================================================
 */

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeFacturationModals();
    initializeExpeditionModals();
});

// ====================================================================
// GESTION DES MODALES DE FACTURATION
// ====================================================================

function initializeFacturationModals() {
    // Modale de facturation complète
    const confirmerFacturationBtn = document.getElementById('confirmerFacturation');
    if (confirmerFacturationBtn) {
        confirmerFacturationBtn.addEventListener('click', function() {
            const form = document.getElementById('facturationForm');
            if (form.checkValidity()) {
                confirmerFacturationComplete();
            } else {
                form.reportValidity();
            }
        });
    }

    // Modale de facturation partielle
    const confirmerFacturationPartielleBtn = document.getElementById('confirmerFacturationPartielle');
    if (confirmerFacturationPartielleBtn) {
        confirmerFacturationPartielleBtn.addEventListener('click', function() {
            const form = document.getElementById('facturationPartielleForm');
            if (form.checkValidity() && validateFacturationPartielle()) {
                confirmerFacturationPartielle();
            } else {
                form.reportValidity();
            }
        });
    }

    // Gestion des checkboxes et quantités dans la facturation partielle
    const lignesChecks = document.querySelectorAll('.ligne-facturation-check');
    lignesChecks.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const qteInput = document.querySelector(`.qte-facturer[data-ligne-id="${this.dataset.ligneId}"]`);
            if (qteInput) {
                qteInput.disabled = !this.checked;
                if (!this.checked) {
                    qteInput.value = 0;
                }
            }
            recalculerTotalFacturation();
        });
    });

    const qteInputs = document.querySelectorAll('.qte-facturer');
    qteInputs.forEach(input => {
        input.addEventListener('change', recalculerTotalFacturation);
    });
}

function confirmerFacturationComplete() {
    const dateFacturation = document.getElementById('date_facturation_modal').value;
    const commentaire = document.getElementById('commentaire_facturation').value;
    
    // Ici, vous feriez un appel AJAX pour envoyer les données au serveur
    console.log('Facturation complète:', {
        date: dateFacturation,
        commentaire: commentaire,
        type: 'complete'
    });
    
    // Simulation de succès
    alert('Commande facturée avec succès !');
    location.reload(); // Recharger la page pour voir les changements
}

function confirmerFacturationPartielle() {
    const dateFacturation = document.getElementById('date_facturation_partielle').value;
    const commentaire = document.getElementById('commentaire_facturation_partielle').value;
    
    // Récupérer les lignes sélectionnées
    const lignesSelectionnees = [];
    const checks = document.querySelectorAll('.ligne-facturation-check:checked');
    
    checks.forEach(check => {
        const ligneId = check.dataset.ligneId;
        const qteInput = document.querySelector(`.qte-facturer[data-ligne-id="${ligneId}"]`);
        const qte = parseInt(qteInput.value);
        
        if (qte > 0) {
            lignesSelectionnees.push({
                ligneId: ligneId,
                quantite: qte
            });
        }
    });
    
    // Ici, vous feriez un appel AJAX pour envoyer les données au serveur
    console.log('Facturation partielle:', {
        date: dateFacturation,
        commentaire: commentaire,
        lignes: lignesSelectionnees,
        type: 'partielle'
    });
    
    // Simulation de succès
    alert(`${lignesSelectionnees.length} ligne(s) facturée(s) avec succès !`);
    location.reload(); // Recharger la page pour voir les changements
}

function validateFacturationPartielle() {
    const checks = document.querySelectorAll('.ligne-facturation-check:checked');
    let hasValidQuantity = false;
    
    checks.forEach(check => {
        const ligneId = check.dataset.ligneId;
        const qteInput = document.querySelector(`.qte-facturer[data-ligne-id="${ligneId}"]`);
        const qte = parseInt(qteInput.value);
        
        if (qte > 0) {
            hasValidQuantity = true;
        }
    });
    
    if (!hasValidQuantity) {
        alert('Veuillez sélectionner au moins une ligne avec une quantité valide.');
        return false;
    }
    
    return true;
}

function recalculerTotalFacturation() {
    let total = 0;
    const checks = document.querySelectorAll('.ligne-facturation-check:checked');
    
    checks.forEach(check => {
        const ligneId = check.dataset.ligneId;
        const qteInput = document.querySelector(`.qte-facturer[data-ligne-id="${ligneId}"]`);
        const qte = parseInt(qteInput.value) || 0;
        
        // Récupérer le prix unitaire depuis l'attribut data ou calculer
        // Pour simplifier, on peut utiliser le total affiché et le recalculer
        const totalCell = check.closest('tr').querySelector('.total-ligne-facturation');
        if (totalCell && qte > 0) {
            // Ici vous pourriez recalculer le total de la ligne
            // Pour l'exemple, on utilise la valeur existante
        }
    });
}

// ====================================================================
// GESTION DES MODALES D'EXPÉDITION
// ====================================================================

function initializeExpeditionModals() {
    // Modale d'expédition complète
    const confirmerExpeditionBtn = document.getElementById('confirmerExpedition');
    if (confirmerExpeditionBtn) {
        confirmerExpeditionBtn.addEventListener('click', function() {
            const form = document.getElementById('expeditionForm');
            if (form.checkValidity()) {
                confirmerExpeditionComplete();
            } else {
                form.reportValidity();
            }
        });
    }

    // Modale d'expédition partielle
    const confirmerExpeditionPartielleBtn = document.getElementById('confirmerExpeditionPartielle');
    if (confirmerExpeditionPartielleBtn) {
        confirmerExpeditionPartielleBtn.addEventListener('click', function() {
            const form = document.getElementById('expeditionPartielleForm');
            if (form.checkValidity() && validateExpeditionPartielle()) {
                confirmerExpeditionPartielle();
            } else {
                form.reportValidity();
            }
        });
    }

    // Gestion des checkboxes et quantités dans l'expédition partielle
    const lignesChecks = document.querySelectorAll('.ligne-expedition-check');
    lignesChecks.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const qteInput = document.querySelector(`.qte-expedier[data-ligne-id="${this.dataset.ligneId}"]`);
            if (qteInput) {
                qteInput.disabled = !this.checked;
                if (!this.checked) {
                    qteInput.value = 0;
                }
            }
        });
    });
}

function confirmerExpeditionComplete() {
    const dateExpedition = document.getElementById('date_expedition_modal').value;
    const transporteur = document.getElementById('transporteur').value;
    const numeroSuivi = document.getElementById('numero_suivi_modal').value;
    const commentaire = document.getElementById('commentaire_expedition').value;
    
    // Ici, vous feriez un appel AJAX pour envoyer les données au serveur
    console.log('Expédition complète:', {
        date: dateExpedition,
        transporteur: transporteur,
        numeroSuivi: numeroSuivi,
        commentaire: commentaire,
        type: 'complete'
    });
    
    // Simulation de succès
    alert('Commande expédiée avec succès !');
    location.reload(); // Recharger la page pour voir les changements
}

function confirmerExpeditionPartielle() {
    const dateExpedition = document.getElementById('date_expedition_partielle').value;
    const transporteur = document.getElementById('transporteur_partielle').value;
    const numeroSuivi = document.getElementById('numero_suivi_partielle').value;
    const commentaire = document.getElementById('commentaire_expedition_partielle').value;
    
    // Récupérer les lignes sélectionnées
    const lignesSelectionnees = [];
    const checks = document.querySelectorAll('.ligne-expedition-check:checked');
    
    checks.forEach(check => {
        const ligneId = check.dataset.ligneId;
        const qteInput = document.querySelector(`.qte-expedier[data-ligne-id="${ligneId}"]`);
        const qte = parseInt(qteInput.value);
        
        if (qte > 0) {
            lignesSelectionnees.push({
                ligneId: ligneId,
                quantite: qte
            });
        }
    });
    
    // Ici, vous feriez un appel AJAX pour envoyer les données au serveur
    console.log('Expédition partielle:', {
        date: dateExpedition,
        transporteur: transporteur,
        numeroSuivi: numeroSuivi,
        commentaire: commentaire,
        lignes: lignesSelectionnees,
        type: 'partielle'
    });
    
    // Simulation de succès
    alert(`${lignesSelectionnees.length} ligne(s) expédiée(s) avec succès !`);
    location.reload(); // Recharger la page pour voir les changements
}

function validateExpeditionPartielle() {
    const checks = document.querySelectorAll('.ligne-expedition-check:checked');
    let hasValidQuantity = false;
    
    checks.forEach(check => {
        const ligneId = check.dataset.ligneId;
        const qteInput = document.querySelector(`.qte-expedier[data-ligne-id="${ligneId}"]`);
        const qte = parseInt(qteInput.value);
        
        if (qte > 0) {
            hasValidQuantity = true;
        }
    });
    
    if (!hasValidQuantity) {
        alert('Veuillez sélectionner au moins une ligne avec une quantité valide.');
        return false;
    }
    
    return true;
}

// ====================================================================
// FONCTIONS UTILITAIRES
// ====================================================================

function copierNumeroSuivi(numero) {
    navigator.clipboard.writeText(numero).then(function() {
        // Afficher une notification de succès
        const notification = document.createElement('div');
        notification.className = 'alert alert-success position-fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = '<i class="bi bi-check-circle me-2"></i>Numéro de suivi copié !';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }).catch(function(err) {
        console.error('Erreur lors de la copie :', err);
    });
}
