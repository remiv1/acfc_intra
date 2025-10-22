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

