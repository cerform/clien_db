#!/usr/bin/env python3
"""
Скрипт для настройки OpenAI API ключа и Assistant ID
"""
import os
from pathlib import Path

def setup_openai():
    """Настройка OpenAI в .env файлах"""
    env_file = Path(__file__).parent / ".env"
    env_cloud_file = Path(__file__).parent / ".env.cloud"
    
    print("=== Настройка OpenAI для INKA ===\n")
    
    # Запрашиваем данные у пользователя
    api_key = input("Введите ваш OPENAI_API_KEY (начинается с sk-): ").strip()
    if not api_key.startswith("sk-"):
        print("⚠️  Предупреждение: API ключ обычно начинается с 'sk-'")
    
    assistant_id = input("Введите OPENAI_ASSISTANT_ID (по умолчанию: asst_LBGeLxauJ3nYbauR3pilbifN): ").strip()
    if not assistant_id:
        assistant_id = "asst_LBGeLxauJ3nYbauR3pilbifN"
    
    # Обновляем .env
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Удаляем старые строки, если есть
        lines = content.split('\n')
        new_lines = [line for line in lines 
                     if not line.startswith('OPENAI_API_KEY=') 
                     and not line.startswith('OPENAI_ASSISTANT_ID=')]
        
        # Добавляем новые
        new_lines.append(f'\n# OpenAI Configuration')
        new_lines.append(f'OPENAI_API_KEY={api_key}')
        new_lines.append(f'OPENAI_ASSISTANT_ID={assistant_id}')
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"\n✅ Файл {env_file} обновлён")
    else:
        print(f"\n⚠️  Файл {env_file} не найден")
    
    # Обновляем .env.cloud
    if env_cloud_file.exists():
        with open(env_cloud_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = [line for line in lines 
                     if not line.startswith('OPENAI_API_KEY=') 
                     and not line.startswith('OPENAI_ASSISTANT_ID=')]
        
        new_lines.append(f'\n# OpenAI Configuration')
        new_lines.append(f'OPENAI_API_KEY={api_key}')
        new_lines.append(f'OPENAI_ASSISTANT_ID={assistant_id}')
        
        with open(env_cloud_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Файл {env_cloud_file} обновлён")
    
    print("\n=== Настройка завершена ===")
    print("\nТеперь нужно обновить секреты в Google Cloud:")
    print(f"  gcloud secrets versions add openai-api-key --data-file=<(echo '{api_key}')")
    print(f"  gcloud secrets create openai-assistant-id --data-file=<(echo '{assistant_id}') --project=tattoo-480007")
    print("\nИли используйте Google Cloud Console для добавления секретов.")

if __name__ == "__main__":
    setup_openai()
