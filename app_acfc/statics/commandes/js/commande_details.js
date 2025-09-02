/**
 * ====================================================================
 * ACFC - Scripts JavaScript pour les détails de commande
 * ====================================================================
 * 
 * Fonctionnalités JavaScript pour la page de détails de commande :
 * - Gestion de la modale de facturation unifiée
 * - Gestion des modales d'expédition  
 * - Gestion des checkboxes de sélection
 * - Validation des formulaires
 * - Calcul automatique des totaux
 * 
 * Dépendances : Bootstrap 5
 * ====================================================================
 */

// ====================================================================
// INITIALISATION GÉNÉRALE
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Initialisation des détails de commande...');
    
    // Initialiser tous les modules
    initializeFacturationFeatures();
    initializeExpeditionFeatures();
    initializeGeneralFeatures();
    
    console.log('✅ Initialisation terminée');
});

// ====================================================================
// FONCTIONNALITÉS DE FACTURATION UNIFIÉE
// ====================================================================

function initializeFacturationFeatures() {
    console.log('📄 Initialisation des fonctionnalités de facturation...');
    
    // Gérer la sélection globale dans le tableau principal
    initializeMainTableSelection();
    
    // Gérer la modale de facturation unifiée
    initializeFacturationModal();
    
    // Gérer les calculs automatiques
    initializeFacturationCalculations();
    
    // Gérer la validation du formulaire de facturation
    initializeFacturationFormValidation();
}

function initializeMainTableSelection() {
    const selectAllMain = document.getElementById('selectAllLines');
    const lignesCheckboxes = document.querySelectorAll('.ligne-checkbox');
    
    if (selectAllMain && lignesCheckboxes.length > 0) {
        console.log(`📋 ${lignesCheckboxes.length} lignes trouvées dans le tableau principal`);
        
        // Gérer la sélection/désélection globale
        selectAllMain.addEventListener('change', function() {
            console.log(`🔄 Sélection globale: ${this.checked ? 'Tout sélectionner' : 'Tout désélectionner'}`);
            lignesCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        
        // Mettre à jour l'état de la case globale quand on change une ligne
        lignesCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateMainSelectAllState();
            });
        });
        
        // Initialiser l'état
        updateMainSelectAllState();
    }
}

function updateMainSelectAllState() {
    const selectAllMain = document.getElementById('selectAllLines');
    const lignesCheckboxes = document.querySelectorAll('.ligne-checkbox');
    const checkedCount = document.querySelectorAll('.ligne-checkbox:checked').length;
    
    if (selectAllMain) {
        selectAllMain.checked = checkedCount === lignesCheckboxes.length && lignesCheckboxes.length > 0;
        selectAllMain.indeterminate = checkedCount > 0 && checkedCount < lignesCheckboxes.length;
    }
}

function initializeFacturationModal() {
    console.log('📄 Initialisation de la modale de facturation unifiée...');
    
    const modal = document.getElementById('facturationModal');
    const selectAllFacturation = document.getElementById('selectAllFacturation');
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const qteInputs = document.querySelectorAll('.qte-facturer');
    
    console.log('🔍 DEBUG éléments trouvés:');
    console.log('  - modal:', modal ? 'Trouvée' : 'NON TROUVÉE');
    console.log('  - selectAllFacturation:', selectAllFacturation ? 'Trouvée' : 'NON TROUVÉE'); 
    console.log('  - lignesCheckboxes:', lignesCheckboxes.length, 'éléments');
    console.log('  - qteInputs:', qteInputs.length, 'éléments');
    
    if (!modal) {
        console.warn('⚠️ Modale de facturation non trouvée');
        return;
    }
    
    console.log(`💰 Modale de facturation trouvée avec ${lignesCheckboxes.length} lignes`);
    
    // Gestion du "Tout sélectionner"
    if (selectAllFacturation) {
        console.log('✅ Configuration du "Tout sélectionner"');
        selectAllFacturation.addEventListener('change', function() {
            console.log(`🔄 Tout sélectionner activé: ${this.checked}`);
            lignesCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                
                // Activer/désactiver l'input quantité selon la sélection
                const row = checkbox.closest('tr');
                const qteInput = row.querySelector('.qte-facturer');
                if (qteInput) {
                    qteInput.disabled = !this.checked;
                }
            });
            
            updateFacturationUI();
            calculateFacturationTotal();
        });
    } else {
        console.warn('⚠️ Checkbox "Tout sélectionner" non trouvée');
    }
    
    // Gestion des checkboxes individuelles
    lignesCheckboxes.forEach((checkbox, index) => {
        console.log(`✅ Configuration checkbox ligne ${index + 1}`);
        checkbox.addEventListener('change', function() {
            console.log(`🔄 Checkbox ligne modifiée: ${this.checked}`);
            const row = this.closest('tr');
            const qteInput = row.querySelector('.qte-facturer');
            
            // Activer/désactiver l'input quantité
            if (qteInput) {
                qteInput.disabled = !this.checked;
                if (!this.checked) {
                    qteInput.value = qteInput.getAttribute('max'); // Reset à la quantité max
                }
            }
            
            // Mettre à jour le "Tout sélectionner"
            const allChecked = Array.from(lignesCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(lignesCheckboxes).some(cb => cb.checked);
            
            if (selectAllFacturation) {
                selectAllFacturation.checked = allChecked;
                selectAllFacturation.indeterminate = someChecked && !allChecked;
            }
            
            updateFacturationUI();
            calculateFacturationTotal();
        });
    });
    
    // Gestion des inputs quantité
    qteInputs.forEach((input, index) => {
        console.log(`✅ Configuration input quantité ${index + 1}`);
        input.addEventListener('input', function() {
            console.log(`🔄 Quantité modifiée: ${this.value}`);
            calculateFacturationTotal();
            updateFacturationUI();
        });
    });
    
    // Initialiser l'état au chargement de la modale
    modal.addEventListener('shown.bs.modal', function() {
        console.log('📄 Modale de facturation ouverte');
        updateFacturationUI();
        calculateFacturationTotal();
    });
}

function initializeFacturationCalculations() {
    console.log('🧮 Initialisation des calculs de facturation...');
    
    // Les calculs sont gérés dans calculateFacturationTotal()
    // et sont appelés lors des changements dans initializeFacturationModal()
}

function calculateFacturationTotal() {
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox:checked');
    let totalFacturation = 0;
    
    lignesCheckboxes.forEach(checkbox => {
        const row = checkbox.closest('tr');
        const qteInput = row.querySelector('.qte-facturer');
        const prixUnitaire = parseFloat(qteInput.getAttribute('data-prix-unitaire')) || 0;
        const remise = parseFloat(qteInput.getAttribute('data-remise')) || 0;
        const qte = parseInt(qteInput.value) || 0;
        
        const totalLigne = qte * prixUnitaire * (1 - remise);
        totalFacturation += totalLigne;
        
        // Mettre à jour le total de la ligne
        const totalCell = row.querySelector('.ligne-total strong');
        if (totalCell) {
            totalCell.textContent = totalLigne.toFixed(2) + ' €';
        }
    });
    
    // Mettre à jour le total général
    const totalElement = document.getElementById('totalFacturation');
    if (totalElement) {
        totalElement.textContent = totalFacturation.toFixed(2) + ' €';
    }
    
    return totalFacturation;
}

function updateFacturationUI() {
    const lignesCheckboxes = document.querySelectorAll('.ligne-facturation-checkbox');
    const lignesSelectionnees = document.querySelectorAll('.ligne-facturation-checkbox:checked');
    const totalLignes = lignesCheckboxes.length;
    const lignesChecked = lignesSelectionnees.length;
    
    // Éléments UI à mettre à jour
    const alertPartielle = document.getElementById('alertFacturationPartielle');
    const infoFacturation = document.getElementById('infoFacturation');
    const btnConfirmer = document.getElementById('btnConfirmerFacturation');
    
    // Déterminer si c'est une facturation partielle
    const isFacturationPartielle = lignesChecked > 0 && lignesChecked < totalLignes;
    
    // Mettre à jour l'alerte de facturation partielle
    if (alertPartielle) {
        if (isFacturationPartielle) {
            alertPartielle.style.display = 'block';
        } else {
            alertPartielle.style.display = 'none';
        }
    }
    
    // Mettre à jour le texte d'information
    if (infoFacturation) {
        if (lignesChecked === 0) {
            infoFacturation.textContent = 'Aucune ligne sélectionnée pour la facturation.';
        } else if (isFacturationPartielle) {
            infoFacturation.textContent = `Facturation partielle : ${lignesChecked} ligne(s) sur ${totalLignes} sélectionnée(s).`;
        } else {
            infoFacturation.textContent = 'Facturation complète : toutes les lignes seront facturées.';
        }
    }
    
    // Activer/désactiver le bouton de confirmation
    if (btnConfirmer) {
        btnConfirmer.disabled = lignesChecked === 0;
        
        if (lignesChecked === 0) {
            btnConfirmer.innerHTML = '<i class="bi bi-receipt me-1"></i>Aucune ligne sélectionnée';
        } else if (isFacturationPartielle) {
            btnConfirmer.innerHTML = `<i class="bi bi-receipt me-1"></i>Facturer ${lignesChecked} ligne(s)`;
        } else {
            btnConfirmer.innerHTML = '<i class="bi bi-receipt me-1"></i>Facturer toutes les lignes';
        }
    }
}

function initializeFacturationFormValidation() {
    const formFacturation = document.getElementById('facturationForm');
    
    if (!formFacturation) {
        console.log('⚠️ Formulaire de facturation non trouvé');
        return;
    }
    
    console.log('✅ Validation du formulaire de facturation configurée');
    
    formFacturation.addEventListener('submit', function(e) {
        const checkedBoxes = formFacturation.querySelectorAll('input[name="lignes_facturees"]:checked');
        const dateFacturation = document.getElementById('date_facturation');
        
        console.log(`🔍 Validation: ${checkedBoxes.length} ligne(s) sélectionnée(s)`);
        
        // Vérifier qu'au moins une ligne est sélectionnée
        if (checkedBoxes.length === 0) {
            e.preventDefault();
            console.log('❌ Aucune ligne sélectionnée');
            showAlert('Veuillez sélectionner au moins une ligne à facturer.', 'warning');
            return false;
        }
        
        // Vérifier la date de facturation
        if (!dateFacturation || !dateFacturation.value) {
            e.preventDefault();
            console.log('❌ Date de facturation manquante');
            showAlert('Veuillez saisir une date de facturation.', 'warning');
            return false;
        }
        
        console.log('✅ Formulaire valide, soumission...');
        
        // Optionnel : afficher un indicateur de chargement
        const submitBtn = formFacturation.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Facturation en cours...';
        }
        
        return true;
    });
}

// ====================================================================
// FONCTIONNALITÉS D'EXPÉDITION
// ====================================================================

function initializeExpeditionFeatures() {
    console.log('🚚 Initialisation des fonctionnalités d\'expédition...');
    
    // Gérer la modale d'expédition si elle existe
    initializeExpeditionModal();
    
    // Gérer le mode d'expédition et numéro de suivi
    initializeExpeditionModeHandling();
}

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
