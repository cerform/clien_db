import os


def test_theme_switcher_has_probe_logic():
    base = os.path.dirname(os.path.dirname(__file__))
    js_path = os.path.join(base, 'src', 'web', 'static', 'theme-switcher.js')
    assert os.path.exists(js_path), "theme-switcher.js should exist"
    content = open(js_path, 'r', encoding='utf-8').read()
    # Ensure updateIcons probes for themed files and falls back
    assert 'probe.onload' in content
    assert 'probe.onerror' in content
    assert '/static/icons/icon-${name}-${theme}.svg' not in content, "should use template strings correctly"


def test_referenced_icon_files_exist():
    # Ensure all icon src references in app/pages point to existing files
    base = os.path.dirname(os.path.dirname(__file__))
    icons_dir = os.path.join(base, 'src', 'web', 'static', 'icons')
    src_files = [
        os.path.join(base, 'src', 'web', 'app.py'),
        os.path.join(base, 'src', 'web', 'pages.py'),
    ]
    missing = []
    import re
    IMG_SRC_RE = re.compile(r'src="/static/icons/([\w\-]+\.svg)"')
    for sf in src_files:
        txt = open(sf, 'r', encoding='utf-8').read()
        for m in IMG_SRC_RE.finditer(txt):
            fname = m.group(1)
            if not os.path.exists(os.path.join(icons_dir, fname)):
                missing.append(fname)
    assert not missing, f"Missing icon files referenced in pages: {missing}"
