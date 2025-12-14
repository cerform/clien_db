/**
 * Theme Manager for Tattoo Salon
 * Handles light/dark/glow themes with persistence
 */

class ThemeManager {
    constructor() {
        this.themes = ['light', 'dark', 'glow'];
        this.currentTheme = this.getSavedTheme() || 'dark';
        this.init();
    }

    init() {
        // Apply saved theme immediately
        this.applyTheme(this.currentTheme);

        // Setup theme switcher buttons
        this.setupThemeSwitcher();

        // Listen for system theme changes
        this.watchSystemTheme();
    }

    getSavedTheme() {
        return localStorage.getItem('theme');
    }

    saveTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        if (!this.themes.includes(theme)) {
            theme = 'dark';
        }

        // Enforce single theme for admin panel (do not change theme dynamically)
        document.documentElement.setAttribute('data-theme', 'dark');
        this.currentTheme = theme;
        this.saveTheme(theme);
        this.updateThemeButtons();

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme }
        }));
    }

    setupThemeSwitcher() {
        const buttons = document.querySelectorAll('[data-theme-toggle]');
        // theme toggle UI disabled
    }

    updateThemeButtons() {
        const buttons = document.querySelectorAll('[data-theme-toggle]');
        buttons.forEach(button => {
            const theme = button.getAttribute('data-theme-toggle');
            if (theme === this.currentTheme) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    watchSystemTheme() {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

        // Only auto-switch if user hasn't manually selected a theme
        if (!this.getSavedTheme()) {
            this.applyTheme(darkModeQuery.matches ? 'dark' : 'light');
        }

        darkModeQuery.addEventListener('change', (e) => {
            if (!this.getSavedTheme()) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    toggle() {
        const currentIndex = this.themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % this.themes.length;
        this.applyTheme(this.themes[nextIndex]);
    }

    setTheme(theme) {
        this.applyTheme(theme);
    }

    getTheme() {
        return this.currentTheme;
    }
}

// Initialize theme manager when DOM is ready
let themeManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager = new ThemeManager();
    });
} else {
    themeManager = new ThemeManager();
}

// Export for use in other scripts
window.ThemeManager = ThemeManager;
window.themeManager = themeManager;
