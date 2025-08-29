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
 * - Gestion des éléments conditionnels (numéro de suivi, alertes)
 * - Gestion des checkboxes "Sélectionner tout"
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
    initializeCommandeDetailsFeatures();
});

// ====================================================================
// GESTION DES ÉLÉMENTS DE DÉTAILS DE COMMANDE
// ====================================================================

function initializeCommandeDetailsFeatures() {
    // Variables globales
    const montantCommande = parseFloat(document.querySelector('[data-montant-commande]')?.dataset.montantCommande || 0);
    const alertMontant80 = document.getElementById('alert_montant_80');
    const numeroSuiviContainer = document.getElementById('numero_suivi_container');
    const envoisRadios = document.querySelectorAll('input[name="mode_expedition"]');
    
    // Gestion de l'affichage du numéro de suivi et de l'alerte montant
    function handleModeExpeditionChange() {
        const selectedMode = document.querySelector('input[name="mode_expedition"]:checked')?.value;
        handleNumeroSuiviDisplay(selectedMode);
        handleMontantAlertAndSubmit(selectedMode);
    }

    function handleNumeroSuiviDisplay(selectedMode) {
        const numeroSuiviInput = document.getElementById('numero_suivi_expedition');
        if (numeroSuiviContainer) {
            if (selectedMode === 'envoi_suivi') {
                numeroSuiviContainer.style.display = 'block';
                if (numeroSuiviInput) numeroSuiviInput.required = true;
            } else {
                numeroSuiviContainer.style.display = 'none';
                if (numeroSuiviInput) numeroSuiviInput.required = false;
            }
        }
    }

    function handleMontantAlertAndSubmit(selectedMode) {
        const submitButton = document.querySelector('#expeditionForm button[type="submit"]');
        if (montantCommande > 80) {
            handleMontantSuperieurA80(selectedMode, submitButton);
        } else {
            hideMontantAlertAndEnableSubmit(submitButton);
        }
    }

    function handleMontantSuperieurA80(selectedMode, submitButton) {
        if (selectedMode === 'envoi_simple') {
            showMontantAlertAndDisableSubmit(submitButton);
        } else {
            hideMontantAlertAndEnableSubmit(submitButton);
        }
    }

    function showMontantAlertAndDisableSubmit(submitButton) {
        if (alertMontant80) alertMontant80.style.display = 'block';
        if (submitButton) submitButton.disabled = true;
    }

    function hideMontantAlertAndEnableSubmit(submitButton) {
        if (alertMontant80) alertMontant80.style.display = 'none';
        if (submitButton) submitButton.disabled = false;
    }
    
    // Écouter les changements de mode d'expédition
    envoisRadios.forEach(radio => {
        radio.addEventListener('change', handleModeExpeditionChange);
    });
    
    // Initialiser l'état au chargement
    handleModeExpeditionChange();
    
    // Gestion des cases à cocher "Sélectionner tout" pour la facturation
    initializeSelectAllCheckboxes('selectAllFacturation', '.ligne-facturation');
    
    // Gestion des cases à cocher "Sélectionner tout" pour l'expédition
    initializeSelectAllCheckboxes('selectAllExpedition', '.ligne-expedition');
    
    // Validation des formulaires avant soumission
    initializeFormValidation();
}

function initializeSelectAllCheckboxes(selectAllId, checkboxSelector) {
    const selectAll = document.getElementById(selectAllId);
    const checkboxes = document.querySelectorAll(checkboxSelector);
    
    if (selectAll && checkboxes.length > 0) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        
        // Mettre à jour l'état du "Sélectionner tout" quand une ligne change
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const checkedCount = document.querySelectorAll(checkboxSelector + ':checked').length;
                selectAll.checked = checkedCount === checkboxes.length;
                selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
            });
        });
    }
}

function initializeFormValidation() {
    const formFacturation = document.getElementById('facturationForm');
    const formExpedition = document.getElementById('expeditionForm');
    
    if (formFacturation) {
        formFacturation.addEventListener('submit', function(e) {
            const checkedBoxes = formFacturation.querySelectorAll('input[name="lignes_facturer[]"]:checked');
            if (checkedBoxes.length === 0) {
                e.preventDefault();
                alert('Veuillez sélectionner au moins une ligne à facturer.');
                return false;
            }
        });
    }
    
    if (formExpedition) {
        formExpedition.addEventListener('submit', function(e) {
            const checkedBoxes = formExpedition.querySelectorAll('input[name="lignes_expedier[]"]:checked');
            if (checkedBoxes.length === 0) {
                e.preventDefault();
                alert('Veuillez sélectionner au moins une ligne à expédier.');
                return false;
            }
            
            const selectedMode = document.querySelector('input[name="mode_expedition"]:checked')?.value;
            if (selectedMode === 'envoi_suivi') {
                const numeroSuivi = document.getElementById('numero_suivi_expedition');
                if (numeroSuivi && !numeroSuivi.value.trim()) {
                    e.preventDefault();
                    alert('Veuillez saisir un numéro de suivi pour l\'envoi suivi.');
                    return false;
                }
            }
        });
    }
}

// ====================================================================
// GESTION DES FONCTIONNALITÉS BON D'IMPRESSION
// ====================================================================

function initializeBonImpressionFeatures() {
    document.addEventListener('DOMContentLoaded', function() {
        const urlParams = new URLSearchParams(window.location.search);
        const autoPrint = urlParams.get('auto_print');
        const printDelay = parseInt(urlParams.get('delay') || '1500');
        
        // Fonction d'impression avec gestion d'erreurs
        function triggerPrint() {
            try {
                // Vérifier si l'impression est supportée
                if (window.print) {
                    window.print();
                    
                    // Si auto_print=close, fermer la fenêtre après impression
                    if (autoPrint === 'close') {
                        setTimeout(() => {
                            try {
                                window.close();
                            } catch (e) {
                                console.error('Impossible de fermer la fenêtre automatiquement', e);
                            }
                        }, 500);
                    }
                } else {
                    console.error('L\'impression n\'est pas supportée par ce navigateur');
                }
            } catch (error) {
                console.error('Erreur lors de l\'impression:', error);
            }
        }
        
        // Auto-impression selon les paramètres URL
        if (autoPrint) {
            setTimeout(triggerPrint, printDelay);
        }
        
        // Alternative : impression au clic n'importe où sur la page (mode debug)
        if (urlParams.get('click_print') === 'true') {
            document.addEventListener('click', triggerPrint, { once: true });
        }
        
        // Raccourci clavier alternatif (P pour Print)
        document.addEventListener('keydown', function(event) {
            if (event.key.toLowerCase() === 'p' && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();
                triggerPrint();
            }
        });
    });
}

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
            alert(total)
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
