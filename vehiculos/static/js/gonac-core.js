/**
 * ==========================================================================
 * GONAC CORE - Lógica Global (Modo Oscuro y Utilidades)
 * ==========================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicialización del Tema Claro/Oscuro
    initThemeManager();

    // Aquí puedes añadir más funciones globales en el futuro, como:
    // initTooltips();
    // initGlobalAlerts();
});

function initThemeManager() {
    const themeToggleBtn = document.getElementById('themeToggle');
    if (!themeToggleBtn) return; // Si no hay botón en la página, no hace nada

    const icon = themeToggleBtn.querySelector('i');
    const htmlElement = document.documentElement;

    // Recuperar el tema guardado o usar 'light' por defecto
    const currentTheme = localStorage.getItem('gonac-theme') || 'light';
    htmlElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme, icon);

    // Evento de clic en el botón de la luna/sol
    themeToggleBtn.addEventListener('click', () => {
        let theme = htmlElement.getAttribute('data-theme');
        let newTheme = theme === 'light' ? 'dark' : 'light';
        
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('gonac-theme', newTheme); 
        updateThemeIcon(newTheme, icon);
        
        // Disparar un evento personalizado. Esto es súper útil si tienes 
        // gráficos (como Chart.js) que necesitan redibujarse al cambiar de modo.
        window.dispatchEvent(new CustomEvent('gonacThemeChanged', { detail: newTheme }));
    });
}

function updateThemeIcon(theme, iconElement) {
    if (theme === 'dark') { 
        iconElement.className = 'fas fa-sun'; 
    } else { 
        iconElement.className = 'fas fa-moon'; 
    }
}