document.addEventListener('DOMContentLoaded', function () {
    // 1. Cargar estado de modo oscuro guardado
    if (localStorage.getItem('jazzmin_dark_mode') === 'true') {
        document.body.classList.add('dark-mode');
    }

    // 2. Escuchar el clic en el botón de "π Modo Oscuro"
    document.addEventListener('click', function (e) {
        const toggleBtn = e.target.closest('a[href*="dark-mode-toggle"]');
        if (toggleBtn) {
            e.preventDefault(); // Evita cambiar la URL
            
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('jazzmin_dark_mode', isDark ? 'true' : 'false');
        }
    });
});