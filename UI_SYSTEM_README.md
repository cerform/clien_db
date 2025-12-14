# 🎨 Modern UI System - Tattoo Salon

## ✨ Что создано

### Три современные темы:

1. **Light** (Светлая) - Минималистичная светлая тема с мягкими тенями
2. **Dark** (Тёмная) - Современная тёмная тема для комфорта глаз
3. **Glow** (Neon) - Яркая неоновая тема с эффектами свечения

### 📁 Структура файлов

```
src/web/static/
├── css/
│   ├── themes.css        # Система тем (CSS переменные, цвета, режимы)
│   ├── components.css    # UI компоненты (кнопки, карточки, формы)
│   └── layout.css        # Layout система (grid, sidebar, navigation)
├── js/
│   ├── theme-manager.js  # Менеджер тем с localStorage
│   └── app.js           # Основная логика приложения
└── images/              # Иконки и изображения

src/web/templates/
└── base.html            # Базовый HTML шаблон с sidebar и topbar
```

## 🎯 Ключевые возможности

### 1. CSS Переменные для тем
```css
[data-theme="dark"] {
    --bg-primary: #1a1b1e;
    --text-primary: #c1c2c5;
    --accent-primary: #5c7cfa;
    /* ... и т.д. */
}

[data-theme="glow"] {
    --bg-primary: #0a0e27;
    --text-primary: #e0e7ff;
    --accent-primary: #818cf8;
    --glow-primary: 0 0 20px rgba(129, 140, 248, 0.4);
    /* ... эффекты свечения */
}
```

### 2. Компоненты UI

#### Кнопки
```html
<button class="button button-primary">Основная</button>
<button class="button button-secondary">Второстепенная</button>
<button class="button button-outline">С обводкой</button>
<button class="button button-ghost">Прозрачная</button>

<!-- Размеры -->
<button class="button button-sm">Маленькая</button>
<button class="button button-lg">Большая</button>
<button class="button button-icon">🔥</button>
<button class="button button-full">На всю ширину</button>
```

#### Карточки (Cards/Boxes)
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Заголовок</h3>
        <p class="card-subtitle">Подзаголовок</p>
    </div>
    <div class="card-body">
        Содержимое карточки
    </div>
    <div class="card-footer">
        <button class="button button-primary">Действие</button>
    </div>
</div>

<!-- Варианты -->
<div class="card card-elevated">С усиленной тенью</div>
<div class="card card-interactive">Интерактивная (кликабельная)</div>
```

#### Формы
```html
<div class="form-group">
    <label class="form-label">Имя клиента</label>
    <input type="text" class="input" placeholder="Введите имя">
    <span class="form-hint">Подсказка под полем</span>
</div>

<div class="form-group">
    <label class="form-label">Описание</label>
    <textarea class="textarea" placeholder="Опишите работу"></textarea>
</div>

<div class="form-group">
    <label class="form-label">Мастер</label>
    <select class="select">
        <option>Выберите мастера</option>
        <option>Владимир</option>
        <option>Анна</option>
    </select>
</div>
```

#### Badges (Значки)
```html
<span class="badge badge-primary">Новый</span>
<span class="badge badge-success">Подтверждён</span>
<span class="badge badge-warning">Ожидает</span>
<span class="badge badge-error">Отменён</span>
<span class="badge badge-info">Информация</span>
<span class="badge badge-outline">С обводкой</span>
```

#### Alerts (Уведомления)
```html
<div class="alert alert-success">
    <div class="alert-icon">✓</div>
    <div class="alert-content">
        <div class="alert-title">Успешно!</div>
        Запись создана
    </div>
</div>

<div class="alert alert-error">
    <div class="alert-icon">✕</div>
    <div class="alert-content">
        <div class="alert-title">Ошибка</div>
        Не удалось сохранить данные
    </div>
</div>
```

#### Модальные окна
```html
<div class="modal-overlay" id="myModal" style="display: none;">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Заголовок модалки</h3>
            <button class="modal-close" data-modal-close>×</button>
        </div>
        <div class="modal-body">
            Содержимое модального окна
        </div>
        <div class="modal-footer">
            <button class="button button-secondary" data-modal-close>Отмена</button>
            <button class="button button-primary">Сохранить</button>
        </div>
    </div>
</div>

<!-- Кнопка открытия -->
<button class="button" data-modal-open="myModal">Открыть модалку</button>
```

### 3. Layout система

#### Grid (Сетка)
```html
<div class="grid grid-cols-3 gap-lg">
    <div class="card">Колонка 1</div>
    <div class="card">Колонка 2</div>
    <div class="card">Колонка 3</div>
</div>

<!-- Адаптивность: на мобильном автоматически 1 колонка -->
```

#### Flex утилиты
```html
<div class="flex items-center justify-between gap-4">
    <div>Слева</div>
    <div>Справа</div>
</div>

<div class="flex flex-col gap-6">
    <div>Элемент 1</div>
    <div>Элемент 2</div>
    <div>Элемент 3</div>
</div>
```

#### Container
```html
<div class="container">
    <!-- Центрированный контейнер с max-width: 1280px -->
</div>

<div class="container container-sm">
    <!-- Узкий контейнер (max-width: 640px) -->
</div>
```

## 📱 Адаптивность

### Breakpoints:
- Mobile: `<= 640px`
- Tablet: `641px - 1024px`
- Desktop: `>= 1025px`

### На мобильных:
- ✅ Sidebar сворачивается в hamburger menu
- ✅ Grid автоматически становится 1-колоночным
- ✅ Карточки адаптируются под меньший размер
- ✅ Модальные окна растягиваются на весь экран
- ✅ Кнопки и инпуты увеличиваются для удобства тапа

## 🎨 Переключение тем

### JavaScript API:
```javascript
// Установить тему
window.themeManager.setTheme('dark');
window.themeManager.setTheme('light');
window.themeManager.setTheme('glow');

// Переключить на следующую тему
window.themeManager.toggle();

// Получить текущую тему
const current = window.themeManager.getTheme();

// Слушать изменения темы
window.addEventListener('themechange', (e) => {
    console.log('Новая тема:', e.detail.theme);
});
```

### HTML:
```html
<div class="theme-switcher">
    <button class="theme-button" data-theme-toggle="light">Light</button>
    <button class="theme-button active" data-theme-toggle="dark">Dark</button>
    <button class="theme-button" data-theme-toggle="glow">Glow</button>
</div>
```

## 🚀 Как использовать

### 1. Подключить стили и скрипты:
```html
<link rel="stylesheet" href="/static/css/themes.css">
<link rel="stylesheet" href="/static/css/components.css">
<link rel="stylesheet" href="/static/css/layout.css">

<script src="/static/js/theme-manager.js"></script>
<script src="/static/js/app.js"></script>
```

### 2. Использовать базовый шаблон:
```html
{% extends "base.html" %}

{% block title %}Мои клиенты{% endblock %}

{% block content %}
<div class="content-header">
    <h1 class="content-title">Клиенты</h1>
    <p class="content-subtitle">Управление базой клиентов</p>
    <div class="content-actions">
        <button class="button button-primary">Добавить клиента</button>
    </div>
</div>

<div class="grid grid-cols-3 gap-lg">
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Иван Иванов</h3>
            <span class="badge badge-success">Активен</span>
        </div>
        <div class="card-body">
            +972-50-123-4567<br>
            ivan@example.com
        </div>
        <div class="card-footer">
            <button class="button button-sm button-outline">Просмотр</button>
            <button class="button button-sm button-primary">Записать</button>
        </div>
    </div>
    <!-- Еще карточки... -->
</div>
{% endblock %}
```

## 🎯 Особенности Glow темы

В Glow теме автоматически применяются эффекты свечения:
- Карточки светятся при hover
- Кнопки имеют неоновый эффект
- Активные элементы подсвечиваются
- Границы и тени имеют свечение

```css
/* Автоматически в glow теме */
[data-theme="glow"] .card {
    box-shadow: 0 0 20px rgba(129, 140, 248, 0.15);
}

[data-theme="glow"] .button:hover {
    box-shadow: 0 0 10px rgba(196, 181, 253, 0.5);
}
```

## 📊 Loading States

### Skeleton loaders:
```html
<div class="skeleton" style="height: 100px; width: 100%;"></div>
```

### Spinner:
```html
<div class="spinner"></div>
```

### Pulse animation:
```html
<div class="animate-pulse">Загрузка...</div>
```

## 🔥 JavaScript утилиты

### Показать alert:
```javascript
window.app.showAlert('Данные сохранены!', 'success');
window.app.showAlert('Произошла ошибка', 'error');
window.app.showAlert('Внимание!', 'warning');
window.app.showAlert('Информация', 'info');
```

### Копировать в буфер:
```javascript
window.app.copyToClipboard('текст для копирования');
```

### Открыть/закрыть модалку:
```javascript
window.app.openModal('myModalId');
window.app.closeModal(modalElement);
```

## 🎨 Цветовая палитра

### Light Theme:
- Primary: `#4c6ef5` (синий)
- Success: `#51cf66` (зелёный)
- Warning: `#ffd43b` (жёлтый)
- Error: `#ff6b6b` (красный)
- Info: `#339af0` (голубой)

### Dark Theme:
- Primary: `#5c7cfa` (яркий синий)
- Остальные цвета аналогичны

### Glow Theme:
- Primary: `#818cf8` (неоновый фиолетовый)
- Secondary: `#c4b5fd` (светло-фиолетовый)
- Success: `#34d399` (неоновый зелёный)

## 📦 Что дальше?

1. Подключите темы в существующие страницы
2. Замените старые стили на новые компоненты
3. Используйте grid и flex утилиты для layout
4. Добавьте кастомные иконки в `/static/icons/`
5. Настройте цвета под свой бренд через CSS переменные

**✨ Современный, адаптивный, с тремя темами UI готов к использованию!**
