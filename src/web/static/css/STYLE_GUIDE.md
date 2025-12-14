# 📐 Universal Style Guide - Tattoo Bot

## Система универсальных стилей для всех страниц

Это руководство по использованию универсальной системы стилей `universal.css`, которая применяется ко всем страницам проекта.

---

## 🎨 Порядок подключения CSS

```html
<!-- 1. Темы (CSS переменные) -->
<link rel="stylesheet" href="/static/css/themes.css">

<!-- 2. Универсальные стили (MAIN) -->
<link rel="stylesheet" href="/static/css/universal.css">

<!-- 3. Компоненты (дополнительно) -->
<link rel="stylesheet" href="/static/css/components.css">

<!-- 4. Layout (специфичные страницы) -->
<link rel="stylesheet" href="/static/css/layout.css">
```

**Важно**: `universal.css` всегда идёт **вторым**, после `themes.css`.

---

## 📦 Что включено в Universal.css

### 1. Layout & Grid
```html
<!-- Container -->
<div class="container">           <!-- Max-width: 1200px -->
<div class="container-sm">        <!-- Max-width: 800px -->
<div class="container-lg">        <!-- Max-width: 1400px -->

<!-- Grid System -->
<div class="grid grid-2">         <!-- 2 columns, responsive -->
<div class="grid grid-3">         <!-- 3 columns, responsive -->
<div class="grid grid-4">         <!-- 4 columns, responsive -->

<!-- Flexbox -->
<div class="flex items-center justify-between gap-md">
<div class="flex-col gap-sm">
```

### 2. Buttons
```html
<!-- Variants -->
<button class="btn btn-primary">Основная</button>
<button class="btn btn-secondary">Вторичная</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-danger">Удалить</button>
<button class="btn btn-success">Сохранить</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Маленькая</button>
<button class="btn btn-primary">Обычная</button>
<button class="btn btn-primary btn-lg">Большая</button>

<!-- Special -->
<button class="btn btn-primary btn-block">На всю ширину</button>
<button class="btn btn-icon">🔍</button>
```

### 3. Cards
```html
<!-- Basic Card -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Заголовок</h3>
    </div>
    <div class="card-body">
        <p>Содержимое карточки</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Действие</button>
    </div>
</div>

<!-- Interactive Card -->
<div class="card card-interactive">
    Кликабельная карточка
</div>

<!-- Compact Card -->
<div class="card card-compact">
    Компактная карточка
</div>
```

### 4. Forms
```html
<div class="form-group">
    <label class="form-label">Имя</label>
    <input type="text" class="form-input" placeholder="Введите имя">
    <div class="form-help">Подсказка для пользователя</div>
    <div class="form-error">Ошибка валидации</div>
</div>

<div class="form-group">
    <label class="form-label">Описание</label>
    <textarea class="form-textarea"></textarea>
</div>

<div class="form-group">
    <label class="form-label">Выбор</label>
    <select class="form-select">
        <option>Опция 1</option>
        <option>Опция 2</option>
    </select>
</div>
```

### 5. Alerts
```html
<div class="alert alert-info">ℹ️ Информация</div>
<div class="alert alert-success">✅ Успех</div>
<div class="alert alert-warning">⚠️ Предупреждение</div>
<div class="alert alert-danger">❌ Ошибка</div>
```

### 6. Badges
```html
<span class="badge badge-primary">Новое</span>
<span class="badge badge-success">Активен</span>
<span class="badge badge-warning">Ожидание</span>
<span class="badge badge-danger">Отменён</span>
<span class="badge badge-info">В процессе</span>
```

### 7. Modal
```html
<div class="modal-overlay">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Заголовок</h3>
            <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
            Содержимое модального окна
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary">Отмена</button>
            <button class="btn btn-primary">Сохранить</button>
        </div>
    </div>
</div>
```

### 8. Navigation
```html
<nav class="nav">
    <a href="/" class="nav-link active">Главная</a>
    <a href="/clients" class="nav-link">Клиенты</a>
    <a href="/masters" class="nav-link">Мастера</a>
</nav>
```

### 9. Tables
```html
<table class="table">
    <thead>
        <tr>
            <th>Имя</th>
            <th>Email</th>
            <th>Статус</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Иван Петров</td>
            <td>ivan@mail.com</td>
            <td><span class="badge badge-success">Активен</span></td>
        </tr>
    </tbody>
</table>

<!-- Striped variant -->
<table class="table table-striped">
    ...
</table>
```

### 10. Loading States
```html
<!-- Spinner -->
<div class="spinner"></div>
<div class="spinner spinner-sm"></div>
<div class="spinner spinner-lg"></div>

<!-- Skeleton Loading -->
<div class="skeleton" style="width: 100%; height: 20px;"></div>
<div class="skeleton" style="width: 60%; height: 20px;"></div>
```

---

## 🎨 CSS Variables (Themes)

### Доступные переменные:

```css
/* Spacing */
--spacing-xs, --spacing-sm, --spacing-md, --spacing-lg, --spacing-xl, --spacing-2xl

/* Colors */
--bg-primary, --bg-secondary, --bg-tertiary, --bg-elevated
--text-primary, --text-secondary, --text-tertiary
--accent-primary, --accent-hover
--success, --warning, --danger, --info

/* Borders */
--border-primary, --border-secondary
--border-radius-sm, --border-radius-md, --border-radius-lg, --border-radius-xl

/* Shadows */
--shadow-sm, --shadow-md, --shadow-lg, --shadow-xl

/* Transitions */
--transition-fast, --transition-base, --transition-slow
```

### Использование:
```css
.my-component {
    background: var(--bg-elevated);
    color: var(--text-primary);
    padding: var(--spacing-md);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-base);
}
```

---

## 🛠️ Utility Classes

### Text
```html
<p class="text-center">Центр</p>
<p class="text-left">Влево</p>
<p class="text-right">Вправо</p>

<p class="text-primary">Основной текст</p>
<p class="text-secondary">Второстепенный</p>
<p class="text-accent">Акцентный</p>
<p class="text-success">Успех</p>
<p class="text-danger">Опасность</p>
```

### Background
```html
<div class="bg-primary">Основной фон</div>
<div class="bg-secondary">Второстепенный фон</div>
<div class="bg-elevated">Приподнятый фон</div>
```

### Spacing
```html
<!-- Margins -->
<div class="mt-md">margin-top: 1rem</div>
<div class="mb-lg">margin-bottom: 1.5rem</div>

<!-- Paddings -->
<div class="pt-sm">padding-top: 0.5rem</div>
<div class="pb-xl">padding-bottom: 2rem</div>

<!-- Размеры: xs, sm, md, lg, xl -->
```

### Borders & Shadows
```html
<div class="rounded-sm">Border radius small</div>
<div class="rounded-md">Border radius medium</div>
<div class="rounded-lg">Border radius large</div>
<div class="rounded-full">Border radius full (pill)</div>

<div class="shadow-sm">Маленькая тень</div>
<div class="shadow-md">Средняя тень</div>
<div class="shadow-lg">Большая тень</div>
```

### Display
```html
<div class="hidden">display: none</div>
<div class="w-full">width: 100%</div>
<div class="h-full">height: 100%</div>
```

---

## 📱 Responsive Design

### Breakpoints:
- **Mobile**: < 768px
- **Desktop**: ≥ 768px

### Mobile-specific classes:
```html
<div class="mobile-hidden">Скрыто на мобильных</div>
<div class="desktop-hidden">Скрыто на десктопе</div>
```

### Auto-responsive grid:
```html
<!-- Автоматически становится 1 колонкой на мобильных -->
<div class="grid grid-3">
    <div class="card">1</div>
    <div class="card">2</div>
    <div class="card">3</div>
</div>
```

---

## 🎬 Animations

```html
<div class="fade-in">Плавное появление</div>
<div class="slide-in-up">Въезд снизу</div>
<div class="slide-in-down">Въезд сверху</div>
```

### Custom animations:
```css
@keyframes myAnimation {
    from { opacity: 0; }
    to { opacity: 1; }
}

.my-element {
    animation: myAnimation var(--transition-base);
}
```

---

## ✅ Пример полной страницы

```html
{% extends "base.html" %}

{% block title %}Мои клиенты{% endblock %}

{% block content %}
<div class="container">
    <div class="section">
        <h1>Список клиентов</h1>

        <!-- Alert -->
        <div class="alert alert-info">
            У вас 5 новых записей
        </div>

        <!-- Grid of cards -->
        <div class="grid grid-3">
            <div class="card card-interactive">
                <div class="card-header">
                    <h3 class="card-title">Иван Петров</h3>
                    <span class="badge badge-success">Активен</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary">+7 900 123-45-67</p>
                    <p class="text-secondary">ivan@mail.com</p>
                </div>
                <div class="card-footer">
                    <button class="btn btn-primary btn-sm">Открыть</button>
                </div>
            </div>

            <!-- More cards... -->
        </div>

        <!-- Table -->
        <div class="mt-xl">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Имя</th>
                        <th>Телефон</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Иван Петров</td>
                        <td>+7 900 123-45-67</td>
                        <td><span class="badge badge-success">Активен</span></td>
                        <td>
                            <button class="btn btn-sm btn-primary">Изменить</button>
                            <button class="btn btn-sm btn-danger">Удалить</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🎯 Best Practices

### 1. Используйте семантические классы
```html
<!-- ✅ Good -->
<button class="btn btn-primary">Сохранить</button>

<!-- ❌ Bad -->
<div style="background: blue; padding: 10px;">Сохранить</div>
```

### 2. Комбинируйте utility классы
```html
<div class="card shadow-md rounded-lg">
    <div class="flex items-center justify-between gap-md">
        ...
    </div>
</div>
```

### 3. Используйте CSS переменные для кастомизации
```css
.my-custom-component {
    background: var(--bg-elevated);
    padding: var(--spacing-lg);
    border-radius: var(--border-radius-md);
}
```

### 4. Mobile-first подход
```css
/* Сначала стили для мобильных */
.element {
    flex-direction: column;
}

/* Затем для десктопа */
@media (min-width: 769px) {
    .element {
        flex-direction: row;
    }
}
```

---

## 🔧 Кастомизация

### Переопределение переменных:
```css
:root {
    --accent-primary: #your-color;
    --spacing-md: 1.25rem;
}
```

### Создание новых вариантов:
```css
.btn-custom {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-custom:hover {
    transform: scale(1.05);
}
```

---

## 📚 Дополнительные ресурсы

- `themes.css` - CSS переменные для трёх тем
- `components.css` - Дополнительные компоненты (sidebar, topbar и т.д.)
- `layout.css` - Специфичные layout страниц
- `app.js` - JavaScript для интерактивности
- `theme-manager.js` - Переключение тем

---

**Создано**: 2025-12-12
**Версия**: 1.0
**Автор**: Tattoo Bot Team
