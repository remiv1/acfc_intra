


function initializeExpeditionModal() {
    const modalExpedition = document.getElementById('expeditionModal');
    const formExpedition = document.getElementById('expeditionForm');
    
    if (!modalExpedition || !formExpedition) {
        console.log('⚠️ Modale ou formulaire d\'expédition non trouvé');
        return;
    }
    
    console.log('✅ Modale d\'expédition trouvée');
    
    // Validation du formulaire d'expédition
    formExpedition.addEventListener('submit', function(e) {
        const checkedBoxes = formExpedition.querySelectorAll('input[name="lignes_expedier[]"]:checked');
        
        if (checkedBoxes.length === 0) {
            e.preventDefault();
            showAlert('Veuillez sélectionner au moins une ligne à expédier.', 'warning');
            return false;
        }
        
        // Vérifier le numéro de suivi si requis
        const selectedMode = document.querySelector('input[name="mode_expedition"]:checked')?.value;
        if (selectedMode === 'envoi_suivi') {
            const numeroSuivi = document.getElementById('numero_suivi_expedition');
            if (!numeroSuivi || !numeroSuivi.value.trim()) {
                e.preventDefault();
                showAlert('Veuillez saisir un numéro de suivi pour l\'envoi suivi.', 'warning');
                return false;
            }
        }
        
        return true;
    });
}

function initializeExpeditionModeHandling() {
    const envoisRadios = document.querySelectorAll('input[name="mode_expedition"]');
    const numeroSuiviContainer = document.getElementById('numero_suivi_container');
    const alertMontant80 = document.getElementById('alert_montant_80');
    
    if (envoisRadios.length === 0) {
        return;
    }
    
    console.log('📦 Gestion des modes d\'expédition configurée');
    
    function handleModeChange() {
        const selectedMode = document.querySelector('input[name="mode_expedition"]:checked')?.value;
        const montantCommande = parseFloat(document.querySelector('[data-montant-commande]')?.dataset.montantCommande || 0);
        const submitButton = document.querySelector('#expeditionForm button[type="submit"]');
        
        console.log(`📋 Mode d'expédition: ${selectedMode}, montant: ${montantCommande}€`);
        
        // Gérer l'affichage du numéro de suivi
        if (numeroSuiviContainer) {
            const numeroSuiviInput = document.getElementById('numero_suivi_expedition');
            if (selectedMode === 'envoi_suivi') {
                numeroSuiviContainer.style.display = 'block';
                if (numeroSuiviInput) numeroSuiviInput.required = true;
            } else {
                numeroSuiviContainer.style.display = 'none';
                if (numeroSuiviInput) numeroSuiviInput.required = false;
            }
        }
        
        // Gérer l'alerte pour montant > 80€
        if (montantCommande > 80 && selectedMode === 'envoi_simple') {
            if (alertMontant80) alertMontant80.style.display = 'block';
            if (submitButton) submitButton.disabled = true;
        } else {
            if (alertMontant80) alertMontant80.style.display = 'none';
            if (submitButton) submitButton.disabled = false;
        }
    }
    
    // Écouter les changements
    envoisRadios.forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });
    
    // Initialiser l'état
    handleModeChange();
}

// ====================================================================
// FONCTIONNALITÉS GÉNÉRALES
// ====================================================================

function initializeGeneralFeatures() {
    console.log('⚙️ Initialisation des fonctionnalités générales...');
    
    // Fonction de copie de numéro de suivi
    window.copierNumeroSuivi = function(numero) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(numero).then(function() {
                showAlert('Numéro de suivi copié !', 'success');
            }).catch(function(err) {
                console.error('Erreur lors de la copie :', err);
                showAlert('Erreur lors de la copie', 'error');
            });
        } else {
            // Fallback pour les navigateurs plus anciens
            const textArea = document.createElement('textarea');
            textArea.value = numero;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showAlert('Numéro de suivi copié !', 'success');
            } catch (err) {
                console.error('Erreur lors de la copie :', err);
                showAlert('Erreur lors de la copie', 'error');
            }
            document.body.removeChild(textArea);
        }
    };
}

// ====================================================================
// FONCTIONS UTILITAIRES
// ====================================================================

function showAlert(message, type = 'info') {
    // Supprimer les alertes existantes
    const existingAlerts = document.querySelectorAll('.alert-floating');
    existingAlerts.forEach(alert => alert.remove());
    
    // Créer la nouvelle alerte
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-floating position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    const icon = {
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'error': 'bi-x-circle',
        'info': 'bi-info-circle'
    }[type] || 'bi-info-circle';
    
    alert.innerHTML = `
        <i class="bi ${icon} me-2"></i>${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
    
    console.log(`🔔 Alert ${type}: ${message}`);
}

function debugFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.log(`❌ Formulaire ${formId} non trouvé`);
        return;
    }
    
    const formData = new FormData(form);
    console.log(`🔍 Debug formulaire ${formId}:`);
    
    for (let [key, value] of formData.entries()) {
        console.log(`  ${key}: ${value}`);
    }
    
    // Compter les checkboxes cochées
    const checkedBoxes = form.querySelectorAll('input[type="checkbox"]:checked');
    console.log(`  📋 Checkboxes cochées: ${checkedBoxes.length}`);
    
    checkedBoxes.forEach((checkbox, index) => {
        console.log(`    ${index + 1}. ${checkbox.name} = ${checkbox.value}`);
    });
}

// ====================================================================
// FONCTIONS DE DEBUG (à retirer en production)
// ====================================================================

// Fonction de debug accessible depuis la console
window.debugCommande = function() {
    console.log('🔧 === DEBUG COMMANDE ===');
    console.log('📋 Éléments du tableau principal:');
    console.log('  - selectAllLines:', document.getElementById('selectAllLines'));
    console.log('  - ligne-checkbox:', document.querySelectorAll('.ligne-checkbox').length);
    
    console.log('💰 Éléments de facturation:');
    console.log('  - facturationModal:', document.getElementById('facturationModal'));
    console.log('  - facturationForm:', document.getElementById('facturationForm'));
    console.log('  - selectAllFacturation:', document.getElementById('selectAllFacturation'));
    console.log('  - ligne-facturation:', document.querySelectorAll('.ligne-facturation').length);
    
    console.log('🚚 Éléments d\'expédition:');
    console.log('  - expeditionModal:', document.getElementById('expeditionModal'));
    console.log('  - expeditionForm:', document.getElementById('expeditionForm'));
    
    debugFormData('facturationForm');
    console.log('🔧 === FIN DEBUG ===');
};

console.log('💡 Tip: Tapez debugCommande() dans la console pour diagnostiquer les problèmes');

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

    // Gestion des modales d'expédition
    initializeExpeditionModals();

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
