(function () {
  const THEMES = ['light', 'dark', 'glow'];
  const THEME_CLASS_PREFIX = 'theme-';
  function setTheme(theme) {
    if (!THEMES.includes(theme)) theme = 'light';
    document.body.classList.remove(...THEMES.map(t => THEME_CLASS_PREFIX + t));
    document.body.classList.add(THEME_CLASS_PREFIX + theme);
    try { localStorage.setItem('ui_theme', theme); } catch (e) {}
    // Toggle existing legacy class for compat
    if (theme === 'dark') document.body.classList.add('blackwork-theme'); else document.body.classList.remove('blackwork-theme');
    // Update icons to match theme
    updateIcons(theme);
  }

  function initSelector() {
    const header = document.querySelector('.header') || document.querySelector('.header.dark') || document.querySelector('body > header');
    if (!header) return;
    // Avoid adding twice
    if (document.getElementById('themeSelector')) return;

    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.gap = '8px';
    container.id = 'themeSelectorContainer';

    const label = document.createElement('label');
    label.style.color = 'var(--muted)';
    label.style.fontSize = '12px';
    label.textContent = 'Тема:';

    const select = document.createElement('select');
    select.id = 'themeSelector';
    select.style.padding = '6px 10px';
    select.style.borderRadius = '8px';
    select.style.background = 'transparent';
    select.style.border = '1px solid var(--border)';
    select.style.color = 'var(--white)';

    const opts = [ {value: 'light', text: 'Светлая'}, {value: 'dark', text: 'Тёмная'}, {value: 'glow', text: 'Свечение'} ];
    opts.forEach(o => {
      const opt = document.createElement('option');
      opt.value = o.value; opt.text = o.text; select.appendChild(opt);
    });

    // Listen and set theme
    select.addEventListener('change', function (e) { setTheme(e.target.value); });

    container.appendChild(label);
    container.appendChild(select);

    // Place container on the right side of header
    header.appendChild(container);

    // Initialize value
    const saved = localStorage.getItem('ui_theme') || (document.body.classList.contains('blackwork-theme') ? 'dark' : 'light');
    select.value = saved;
    setTheme(saved);
  }

  function updateIcons(theme) {
    // Find all <img data-icon="name"> and update src to theme-specific file
    const imgs = document.querySelectorAll('img[data-icon]');
    imgs.forEach(img => {
      const name = img.getAttribute('data-icon');
      if (!name) return;
      const themedFile = '/static/icons/icon-' + name + '-' + theme + '.svg';
      const baseFile = '/static/icons/icon-' + name + '.svg';
      // Probe themed file and fall back to base file if it doesn't exist
      const probe = new Image();
      probe.onload = function () { img.src = themedFile; };
      probe.onerror = function () { img.src = baseFile; };
      probe.src = themedFile;
    });
  }

  // Auto-init
  document.addEventListener('DOMContentLoaded', function () {
    try { initSelector(); } catch (e) { console.warn('Theme selector init err', e); }
  });

  // Export function
  window.setTheme = setTheme;
})();
