#!/bin/bash
# 🚀 Быстрая настройка унифицированной БД

echo "🗄️ UNIFIED DATABASE CREATOR - БЫСТРАЯ НАСТРОЙКА"
echo "=================================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Переходим в корень проекта
cd "$(dirname "$0")/.." || exit 1

# Активируем виртуальное окружение если есть
if [ -d "venv" ]; then
    echo -e "${BLUE}📦 Активация виртуального окружения...${NC}"
    source venv/bin/activate
fi

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python найден: $(python3 --version)${NC}"
echo ""

# Меню выбора
echo "Выберите действие:"
echo "1) 📋 Показать схему БД"
echo "2) 🆕 Создать новую БД (пустую структуру)"
echo "3) 🆕 Создать БД с тестовыми данными"
echo "4) 🔄 Миграция существующих данных (dry run)"
echo "5) 🔄 Миграция существующих данных (применить)"
echo "6) 🔍 Проверить данные (валидация)"
echo "7) 💾 Создать backup"
echo "8) 🔄 Полный цикл (backup → migrate → validate)"
echo "9) ❌ Выход"
echo ""
read -p "Введите номер (1-9): " choice

case $choice in
    1)
        echo -e "\n${BLUE}📋 Схема БД:${NC}"
        python3 scripts/unified_database_creator.py --schema
        ;;
    2)
        echo -e "\n${YELLOW}⚠️ Создание новой БД. Продолжить? (y/n)${NC}"
        read -p "> " confirm
        if [ "$confirm" = "y" ]; then
            python3 scripts/unified_database_creator.py --create
        else
            echo "Отменено"
        fi
        ;;
    3)
        echo -e "\n${YELLOW}⚠️ Создание БД с тестовыми данными. Продолжить? (y/n)${NC}"
        read -p "> " confirm
        if [ "$confirm" = "y" ]; then
            python3 scripts/unified_database_creator.py --create
            python3 scripts/unified_database_creator.py --test-data
            echo -e "\n${GREEN}✅ БД создана и заполнена тестовыми данными${NC}"
        else
            echo "Отменено"
        fi
        ;;
    4)
        echo -e "\n${BLUE}🔄 Миграция (dry run - без изменений):${NC}"
        python3 scripts/unified_database_creator.py --migrate
        ;;
    5)
        echo -e "\n${RED}⚠️ ВНИМАНИЕ! Это изменит данные в БД.${NC}"
        echo -e "${YELLOW}Рекомендуется сначала создать backup.${NC}"
        read -p "Создать backup перед миграцией? (y/n): " backup_choice
        if [ "$backup_choice" = "y" ]; then
            python3 scripts/unified_database_creator.py --backup
            echo ""
        fi
        read -p "Применить миграцию? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            python3 scripts/unified_database_creator.py --migrate --apply
            echo -e "\n${GREEN}✅ Миграция завершена${NC}"
        else
            echo "Отменено"
        fi
        ;;
    6)
        echo -e "\n${BLUE}🔍 Валидация данных:${NC}"
        python3 scripts/unified_database_creator.py --validate
        ;;
    7)
        echo -e "\n${BLUE}💾 Создание backup...${NC}"
        python3 scripts/unified_database_creator.py --backup
        echo -e "\n${GREEN}✅ Backup создан в директории backups/${NC}"
        ;;
    8)
        echo -e "\n${RED}⚠️ ПОЛНЫЙ ЦИКЛ: backup → migrate → validate${NC}"
        echo -e "${YELLOW}Это изменит данные в БД!${NC}"
        read -p "Продолжить? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            python3 scripts/unified_database_creator.py --full
            echo -e "\n${GREEN}✅ Полный цикл завершен${NC}"
        else
            echo "Отменено"
        fi
        ;;
    9)
        echo "Выход"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✨ Готово!${NC}"
