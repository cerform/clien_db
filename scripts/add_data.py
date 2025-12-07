#!/usr/bin/env python3
"""
Простой скрипт для добавления данных в Google Sheets
"""

import os
from urllib.parse import quote
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

load_dotenv()

def add_data():
    """Добавить данные в таблицу"""
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_JSON', 'credentials.json')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Credentials file: {credentials_file}")
    
    # Инициализируем сервис
    creds = Credentials.from_service_account_file(
        credentials_file,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)
    
    print("\n" + "="*60)
    print("➕ ДОБАВЛЕНИЕ ДАННЫХ В ТАБЛИЦУ")
    print("="*60)
    
    # Используем URL-кодирование для кириллицы
    masters_range = quote("Мастера!A2:J")
    procedures_range = quote("Услуги!A2:H")
    
    # Добавляем мастеров
    print("\n👨‍💼 Добавление мастеров...")
    masters_data = [
        ["1", "Иван Петров", "Татуировка", "7", "4.9", "+79001234567", "@ivan_petrov_tattoo", "2000", "Пн-Пт 10:00-18:00", "Специалист по реалистичным татуировкам"],
        ["2", "Александра Сидорова", "Пирсинг", "5", "4.8", "+79009876543", "@alex_piercing", "1500", "Пн-Сб 12:00-20:00", "Специалист по пирсингу всех типов"],
    ]
    
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=masters_range,
            valueInputOption="RAW",
            body={"values": masters_data}
        ).execute()
        print(f"✅ Добавлено {result.get('updates', {}).get('updatedRows', 0)} мастеров")
    except Exception as e:
        print(f"❌ Ошибка добавления мастеров: {str(e)}")
        # Пробуем без кодирования, с английским названием
        try:
            print("  Пробую альтернативный способ...")
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="A2:J",
                valueInputOption="RAW",
                body={"values": masters_data}
            ).execute()
            print(f"✅ Добавлено {result.get('updates', {}).get('updatedRows', 0)} мастеров (альтернативный способ)")
        except Exception as e2:
            print(f"❌ Ошибка: {str(e2)}")
    
    # Добавляем услуги
    print("\n💇 Добавление услуг...")
    procedures_data = [
        ["1", "Татуировка малая", "Татуировка размером до 5x5 см", "2000", "30", "Татуировка", "5", "ДА"],
        ["2", "Татуировка средняя", "Татуировка размером от 5x5 до 15x15 см", "5000", "120", "Татуировка", "5", "ДА"],
        ["3", "Пирсинг ушей", "Профессиональный пирсинг с использованием стерильного оборудования", "1500", "15", "Пирсинг", "4", "ДА"],
    ]
    
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=procedures_range,
            valueInputOption="RAW",
            body={"values": procedures_data}
        ).execute()
        print(f"✅ Добавлено {result.get('updates', {}).get('updatedRows', 0)} услуг")
    except Exception as e:
        print(f"❌ Ошибка добавления услуг: {str(e)}")
        # Пробуем без кодирования
        try:
            print("  Пробую альтернативный способ...")
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="A2:H",
                valueInputOption="RAW",
                body={"values": procedures_data}
            ).execute()
            print(f"✅ Добавлено {result.get('updates', {}).get('updatedRows', 0)} услуг (альтернативный способ)")
        except Exception as e2:
            print(f"❌ Ошибка: {str(e2)}")
    
    print("\n" + "="*60)
    print("✅ ОПЕРАЦИЯ ЗАВЕРШЕНА!")
    print("="*60)
    print(f"\n🔗 Откройте таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit\n")

if __name__ == '__main__':
    add_data()
