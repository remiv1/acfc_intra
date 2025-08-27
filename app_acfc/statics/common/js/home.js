/**
 * JavaScript pour la page d'accueil ACFC
 * Gestion des interactions et de l'animation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des composants
    initAnimations();
    initQuickLinks();
    initDashboardRefresh();
    
    // Rafraîchissement automatique des données toutes les 5 minutes
    setInterval(refreshDashboardData, 5 * 60 * 1000);
});

/**
 * Initialise les animations de la page
 */
function initAnimations() {
    // Animation du logo au survol
    const logo = document.querySelector('.logo-main');
    if (logo) {
        logo.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) rotate(2deg)';
            this.style.transition = 'all 0.3s ease';
        });
        
        logo.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    }
    
    // Animation des cartes au chargement
    const cards = document.querySelectorAll('.card, .quick-link-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

/**
 * Gère les liens rapides
 */
function initQuickLinks() {
    const quickLinks = document.querySelectorAll('.quick-link-card');
    
    quickLinks.forEach(card => {
        card.addEventListener('click', function(e) {
            // Animation de clic
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
        
        // Effet de survol amélioré
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = 'scale(1.2) rotate(5deg)';
                icon.style.transition = 'all 0.3s ease';
            }
        });
        
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
}

/**
 * Initialise le bouton de rafraîchissement des données
 */
function initDashboardRefresh() {
    // Bouton de rafraîchissement pour les commandes
    const commandesCard = document.querySelector('.card-header:has(.fa-shopping-cart)');
    if (commandesCard) {
        addRefreshButton(commandesCard, refreshCommandes);
    }
    
    // Bouton de rafraîchissement pour les indicateurs
    const indicateursCard = document.querySelector('.card-header:has(.fa-chart-line)');
    if (indicateursCard) {
        addRefreshButton(indicateursCard, refreshIndicateurs);
    }
}

/**
 * Ajoute un bouton de rafraîchissement à un header de carte
 */
function addRefreshButton(header, refreshFunction) {
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn btn-sm btn-outline-light float-end';
    refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
    refreshBtn.setAttribute('title', 'Actualiser');
    refreshBtn.style.padding = '0.25rem 0.5rem';
    
    refreshBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Animation de rotation
        const icon = this.querySelector('i');
        icon.style.animation = 'spin 1s linear infinite';
        
        refreshFunction().finally(() => {
            icon.style.animation = '';
        });
    });
    
    header.appendChild(refreshBtn);
}

/**
 * Rafraîchit les données du dashboard
 */
async function refreshDashboardData() {
    try {
        await Promise.all([
            refreshCommandes(),
            refreshIndicateurs()
        ]);
        
        // Notification discrète
        showNotification('Données mises à jour', 'success');
    } catch (error) {
        console.error('Erreur lors du rafraîchissement:', error);
        showNotification('Erreur de mise à jour', 'error');
    }
}

/**
 * Rafraîchit les commandes en cours
 */
async function refreshCommandes() {
    if (typeof loadCommandesEnCours === 'function') {
        return loadCommandesEnCours();
    }
}

/**
 * Rafraîchit les indicateurs commerciaux
 */
async function refreshIndicateurs() {
    if (typeof loadIndicateursCommerciaux === 'function') {
        return loadIndicateursCommerciaux();
    }
}

/**
 * Affiche une notification temporaire
 */
function showNotification(message, type = 'info') {
    // Supprime les notifications existantes
    const existingNotifications = document.querySelectorAll('.acfc-notification');
    existingNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = `acfc-notification alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-suppression après 3 secondes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }
    }, 3000);
}

/**
 * Gestion des erreurs d'API
 */
function handleApiError(error, context = '') {
    console.error(`Erreur API ${context}:`, error);
    
    let message = 'Une erreur est survenue';
    if (error.message) {
        message += ': ' + error.message;
    }
    
    showNotification(message, 'error');
}

/**
 * Utilitaire pour formater les nombres
 */
function formatNumber(num, currency = false) {
    if (num === null || num === undefined) return '-';
    
    const formatted = new Intl.NumberFormat('fr-FR', {
        style: currency ? 'currency' : 'decimal',
        currency: currency ? 'EUR' : undefined,
        minimumFractionDigits: currency ? 2 : 0
    }).format(num);
    
    return formatted;
}

/**
 * Utilitaire pour formater les dates
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    }).format(date);
}

// CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .acfc-notification {
        transition: all 0.3s ease;
    }
    
    .card-header .btn {
        transition: all 0.2s ease;
    }
    
    .card-header .btn:hover {
        transform: scale(1.1);
    }
`;
document.head.appendChild(style);
