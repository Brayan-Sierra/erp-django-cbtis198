/* static/erp_custom.js - Control de Modo Oscuro para Jazzmin ERP */

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    var isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('jazzmin_dark_mode', isDark ? 'true' : 'false');
}

// 1. Restaurar preferencia guardada al cargar la página
document.addEventListener('DOMContentLoaded', function () {
    if (localStorage.getItem('jazzmin_dark_mode') === 'true') {
        document.body.classList.add('dark-mode');
    }
});

// 2. Interceptar el clic en cualquier elemento que contenga "Modo Oscuro" o "dark-mode-toggle"
document.addEventListener('click', function (e) {
    var target = e.target.closest('a');
    if (target) {
        var href = target.getAttribute('href') || '';
        var text = target.textContent || '';
        
        if (href.includes('dark-mode-toggle') || text.includes('Modo Oscuro') || text.includes('π')) {
            e.preventDefault();
            e.stopPropagation();
            toggleDarkMode();
            return false;
        }
    }
}, true); // Captura en fase inicial para adelantarse a Bootstrap