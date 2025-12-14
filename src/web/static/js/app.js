/**
 * Main App JavaScript
 * Mobile menu, modals, interactions
 */

class TattooApp {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.mobileOverlay = document.querySelector('.mobile-overlay');
        this.menuToggle = document.querySelector('.topbar-menu-toggle');

        this.init();
    }

    init() {
        this.setupMobileMenu();
        this.setupModals();
        // Ensure any modals present in the DOM are moved to the document body
        this.attachModalElements();
        this.setupForms();
        this.setupTooltips();
        this.setupSPANavigation();
    }

    // Mobile menu toggle
    setupMobileMenu() {
        if (!this.menuToggle) return;

        this.menuToggle.addEventListener('click', () => {
            this.toggleSidebar();
        });

        if (this.mobileOverlay) {
            this.mobileOverlay.addEventListener('click', () => {
                this.closeSidebar();
            });
        }

        // Close sidebar when clicking a link on mobile
        const sidebarLinks = document.querySelectorAll('.sidebar-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 1024) {
                    this.closeSidebar();
                }
            });
        });

        // Close sidebar on resize if window becomes large
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1024) {
                this.closeSidebar();
            }
        });
    }

    toggleSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('open');
        }
        if (this.mobileOverlay) {
            this.mobileOverlay.classList.toggle('show');
        }
    }

    closeSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('open');
        }
        if (this.mobileOverlay) {
            this.mobileOverlay.classList.remove('show');
        }
    }

    // Modal management
    setupModals() {
        // Use event delegation so dynamically-added modal triggers still work (SPA tabs)
        document.body.addEventListener('click', (e) => {
            const openBtn = e.target.closest('[data-modal-open]');
            if (openBtn) {
                const modalId = openBtn.getAttribute('data-modal-open');
                if (modalId) this.openModal(modalId);
                return;
            }
            const closeBtn = e.target.closest('[data-modal-close]');
            if (closeBtn) {
                const overlay = closeBtn.closest('.modal-overlay');
                if (overlay) {
                    this.closeModal(overlay);
                }
                return;
            }
            // Click on overlay background to close
            const overlay = e.target.closest('.modal-overlay');
            if (overlay && e.target === overlay) {
                this.closeModal(overlay);
                return;
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal-overlay:not([style*="display: none"])');
                if (openModal) {
                    this.closeModal(openModal);
                }
            }
        });
    }

    openModal(modalId) {
        const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    attachModalElements() {
        // Ensure any modal-overlays are attached to document.body so SPA navigation doesn't remove them
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            try {
                if (modal.parentElement !== document.body) {
                    document.body.appendChild(modal);
                }
            } catch (e) {
                // ignore
            }
        });
    }

    // Form enhancements
    setupForms() {
        // Auto-grow textareas
        document.querySelectorAll('.textarea').forEach(textarea => {
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            });
        });

        // Form validation styling
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const inputs = form.querySelectorAll('[required]');
                let isValid = true;

                inputs.forEach(input => {
                    if (!input.value.trim()) {
                        input.classList.add('error');
                        isValid = false;
                    } else {
                        input.classList.remove('error');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    this.showAlert('Пожалуйста, заполните все обязательные поля', 'error');
                }
            });
        });
    }

    // Tooltips
    setupTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background-color: var(--bg-elevated);
                color: var(--text-primary);
                padding: var(--spacing-xs) var(--spacing-sm);
                border-radius: var(--border-radius-md);
                font-size: 0.875rem;
                box-shadow: var(--shadow-lg);
                pointer-events: none;
                opacity: 0;
                transition: opacity var(--transition-fast);
                z-index: 1000;
                white-space: nowrap;
            `;

            element.style.position = 'relative';

            element.addEventListener('mouseenter', () => {
                document.body.appendChild(tooltip);
                const rect = element.getBoundingClientRect();
                tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
                tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
                tooltip.style.opacity = '1';
            });

            element.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    if (tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            });
        });
    }

    // Alert system
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.style.cssText = `
            position: fixed;
            top: var(--spacing-lg);
            right: var(--spacing-lg);
            max-width: 400px;
            z-index: 2000;
            animation: slideIn 0.3s ease-out;
        `;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        alert.innerHTML = `
            <div class="alert-icon">${icons[type] || icons.info}</div>
            <div class="alert-content">${message}</div>
        `;

        document.body.appendChild(alert);

        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, 5000);
    }

    // SPA Navigation for sidebar links
    setupSPANavigation() {
        // Handle sidebar links with data-spa-tab attribute
        document.querySelectorAll('[data-spa-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = link.getAttribute('data-spa-tab');

                // Check if we're on the SPA dashboard page
                const tabNav = document.querySelector('.tab-nav');
                if (!tabNav) {
                    // Navigate to root (SPA dashboard) first
                    window.location.href = '/?tab=' + tabName;
                    return;
                }

                // Find the tab button and trigger click
                const tabButton = document.querySelector(`[data-tab="${tabName}"]`);
                if (tabButton) {
                    tabButton.click();
                }

                // Update active state on sidebar
                document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                // Close sidebar on mobile after click
                if (window.innerWidth <= 1024) {
                    this.closeSidebar();
                }
                // After SPA tab navigation possibly new DOM is inserted; ensure modal overlays are attached
                this.attachModalElements();
            });
        });
    }

    // Copy to clipboard
    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showAlert('Скопировано в буфер обмена', 'success');
            });
        } else {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.showAlert('Скопировано в буфер обмена', 'success');
        }
    }
}

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is ready
let app;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app = new TattooApp();
    });
} else {
    app = new TattooApp();
}

// Export for use in other scripts
window.TattooApp = TattooApp;
window.app = app;
