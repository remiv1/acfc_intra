// Fonction pour afficher une alerte flottante
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
}