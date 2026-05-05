/**
 * ==========================================================================
 * GONAC CORE - Lógica Global (Modo Oscuro y Utilidades)
 * ==========================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeManager();
});

function initThemeManager() {
    const themeToggleBtn = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;

    // Recuperar el tema guardado; si no existe, respetar el tema del SO.
    // Importante: esto corre aunque la página no tenga botón (ej. login),
    // para que el modo oscuro aplique globalmente.
    const savedTheme = localStorage.getItem('gonac-theme');
    const prefersDark =
        window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    htmlElement.setAttribute('data-theme', currentTheme);

    // Si no hay botón en la página, no hay nada más que hacer.
    if (!themeToggleBtn) return;

    const icon = themeToggleBtn.querySelector('i');
    updateThemeIcon(currentTheme, icon);

    themeToggleBtn.addEventListener('click', () => {
        const theme = htmlElement.getAttribute('data-theme');
        const newTheme = theme === 'light' ? 'dark' : 'light';

        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('gonac-theme', newTheme);
        updateThemeIcon(newTheme, icon);

        window.dispatchEvent(new CustomEvent('gonacThemeChanged', { detail: newTheme }));
    });
}

function updateThemeIcon(theme, iconElement) {
    if (!iconElement) return;
    iconElement.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}
