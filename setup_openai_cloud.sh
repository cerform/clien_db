#!/bin/bash
# Финальная настройка OpenAI для Cloud Run

echo "=== Настройка OpenAI секретов в Google Cloud ==="
echo ""
echo "Для завершения настройки выполните следующие команды:"
echo ""
echo "1. Создайте секрет с вашим OpenAI API ключом:"
echo "   gcloud secrets create openai-api-key \\"
echo "     --data-file=<(echo 'ваш-api-ключ-sk-...') \\"
echo "     --project=tattoo-480007"
echo ""
echo "2. Дайте Cloud Run доступ к секрету:"
echo "   gcloud secrets add-iam-policy-binding openai-api-key \\"
echo "     --member='serviceAccount:408800151466-compute@developer.gserviceaccount.com' \\"
echo "     --role='roles/secretmanager.secretAccessor' \\"
echo "     --project=tattoo-480007"
echo ""
echo "3. Обновите деплой с новым секретом:"
echo "   gcloud run deploy telegram-bot \\"
echo "     --source . \\"
echo "     --platform managed \\"
echo "     --region us-central1 \\"
echo "     --project tattoo-480007 \\"
echo "     --set-secrets=TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,\\"
echo "GOOGLE_SHEETS_ID=google-sheets-id:latest,\\"
echo "GOOGLE_CREDENTIALS=google-credentials:latest,\\"
echo "OPENAI_API_KEY=openai-api-key:latest \\"
echo "     --set-env-vars=OPENAI_ASSISTANT_ID=asst_LBGeLxauJ3nYbauR3pilbifN \\"
echo "     --memory 512Mi \\"
echo "     --min-instances 1 \\"
echo "     --max-instances 1"
echo ""
echo "=== Важно ==="
echo "Assistant ID уже настроен: asst_LBGeLxauJ3nYbauR3pilbifN"
echo "Осталось только добавить ваш OPENAI_API_KEY"
echo ""

# Интерактивный режим
read -p "Хотите добавить API ключ сейчас? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Введите ваш OpenAI API ключ (sk-...): " OPENAI_KEY
    
    if [[ $OPENAI_KEY == sk-* ]]; then
        echo "Создаю секрет..."
        echo "$OPENAI_KEY" | gcloud secrets create openai-api-key \
            --data-file=- \
            --project=tattoo-480007 2>/dev/null || \
        echo "$OPENAI_KEY" | gcloud secrets versions add openai-api-key \
            --data-file=- \
            --project=tattoo-480007
        
        echo "Добавляю права доступа..."
        gcloud secrets add-iam-policy-binding openai-api-key \
            --member='serviceAccount:408800151466-compute@developer.gserviceaccount.com' \
            --role='roles/secretmanager.secretAccessor' \
            --project=tattoo-480007
        
        echo ""
        echo "✅ Секрет создан! Теперь запустите деплой с командой выше."
    else
        echo "❌ API ключ должен начинаться с 'sk-'"
    fi
fi
